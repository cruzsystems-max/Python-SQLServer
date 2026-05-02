"""
Singleton connection pool for managing database connections.

Implements a thread-safe connection pool using the Singleton pattern
to ensure efficient resource usage and prevent connection exhaustion.
"""

from typing import Optional, Dict, Any
import pyodbc
import threading
from queue import Queue, Empty
from contextlib import contextmanager
from .logger import get_logger
from .exceptions import ConnectionPoolError, ConnectionTimeoutError
from .connection_factory import ConnectionFactory


class ConnectionPool:
    """
    Singleton connection pool for managing database connections.

    This class implements a thread-safe connection pool using the Singleton
    pattern. It maintains a pool of reusable connections, creating new ones
    as needed up to a maximum limit.

    Features:
    - Thread-safe connection management
    - Automatic connection creation and reuse
    - Configurable pool size (min/max connections)
    - Connection timeout handling
    - Automatic connection health checks

    Example:
        >>> from config.settings import settings
        >>> pool = ConnectionPool()
        >>> pool.initialize(settings.get_db_config(), min_size=2, max_size=10)
        >>> with pool.get_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT 1")
        ...     result = cursor.fetchone()
    """

    _instance: Optional['ConnectionPool'] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> 'ConnectionPool':
        """
        Create or return the singleton instance.

        This method ensures only one instance of ConnectionPool exists,
        implementing the Singleton pattern in a thread-safe way.

        Returns:
            ConnectionPool: The singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking for thread safety
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize the connection pool.

        Note:
            This only runs once due to the Singleton pattern.
            Use initialize() to configure the pool.
        """
        # Only initialize once
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._pool: Queue = Queue()
            self._in_use: set = set()
            self._pool_lock = threading.Lock()
            self._config: Optional[Dict[str, Any]] = None
            self._min_size = 2
            self._max_size = 10
            self._current_size = 0
            self._timeout = 30.0
            self._logger = get_logger(__name__)
            self._closed = False

    def initialize(
        self,
        config: Dict[str, Any],
        min_size: int = 2,
        max_size: int = 10,
        timeout: float = 30.0
    ) -> None:
        """
        Initialize the connection pool with configuration.

        Args:
            config: Database configuration dictionary (driver, server, etc.)
            min_size: Minimum number of connections to maintain
            max_size: Maximum number of connections allowed
            timeout: Timeout in seconds when waiting for a connection

        Raises:
            ConnectionPoolError: If initialization fails
            ValueError: If min_size > max_size or invalid values

        Example:
            >>> config = {
            ...     'driver': 'ODBC Driver 17 for SQL Server',
            ...     'server': 'localhost',
            ...     'database': 'Chinook',
            ...     'username': 'user',
            ...     'password': 'password'
            ... }
            >>> pool = ConnectionPool()
            >>> pool.initialize(config, min_size=2, max_size=10)
        """
        if min_size < 0 or max_size < 1:
            raise ValueError("Invalid pool size: min_size >= 0, max_size >= 1")

        if min_size > max_size:
            raise ValueError("min_size cannot be greater than max_size")

        self._config = config.copy()
        self._min_size = min_size
        self._max_size = max_size
        self._timeout = timeout
        self._closed = False

        self._logger.info(
            f"Initializing connection pool with min_size={min_size}, "
            f"max_size={max_size}, timeout={timeout}"
        )

        try:
            # Create minimum number of connections
            for _ in range(min_size):
                conn = self._create_connection()
                self._pool.put(conn)
                self._current_size += 1

            self._logger.info(
                f"Connection pool initialized with {self._current_size} connections"
            )

        except Exception as e:
            self._logger.error(f"Failed to initialize connection pool: {e}")
            self.close_all()
            raise ConnectionPoolError(
                "Failed to initialize connection pool",
                original_error=e
            )

    @contextmanager
    def get_connection(self, timeout: Optional[float] = None):
        """
        Get a connection from the pool (context manager).

        This is a context manager that automatically returns the connection
        to the pool when done.

        Args:
            timeout: Timeout in seconds (uses pool default if None)

        Yields:
            pyodbc.Connection: Database connection from the pool

        Raises:
            ConnectionPoolError: If pool is not initialized or closed
            ConnectionTimeoutError: If timeout occurs waiting for connection

        Example:
            >>> pool = ConnectionPool()
            >>> with pool.get_connection() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT * FROM users")
            ...     results = cursor.fetchall()
            # Connection automatically returned to pool
        """
        if self._closed:
            raise ConnectionPoolError("Connection pool is closed")

        if self._config is None:
            raise ConnectionPoolError(
                "Connection pool not initialized. Call initialize() first."
            )

        timeout = timeout if timeout is not None else self._timeout
        connection = None

        try:
            # Try to get connection from pool
            connection = self._acquire_connection(timeout)

            # Verify connection is still valid
            if not self._is_connection_alive(connection):
                self._logger.warning("Connection is dead, creating new one")
                try:
                    connection.close()
                except:
                    pass
                connection = self._create_connection()

            with self._pool_lock:
                self._in_use.add(id(connection))

            yield connection

        except Empty:
            self._logger.error(f"Timeout waiting for connection ({timeout}s)")
            raise ConnectionTimeoutError(
                f"Timeout waiting for connection from pool",
                timeout=timeout
            )

        finally:
            # Return connection to pool
            if connection:
                with self._pool_lock:
                    self._in_use.discard(id(connection))

                # Only return to pool if it's still alive
                if self._is_connection_alive(connection):
                    self._pool.put(connection)
                else:
                    self._logger.warning("Not returning dead connection to pool")
                    self._current_size -= 1

    def _acquire_connection(self, timeout: float) -> pyodbc.Connection:
        """
        Acquire a connection from the pool or create a new one.

        Args:
            timeout: Maximum time to wait for a connection

        Returns:
            pyodbc.Connection: Database connection

        Raises:
            Empty: If timeout occurs
            ConnectionPoolError: If unable to create new connection
        """
        try:
            # Try to get existing connection from pool
            return self._pool.get(timeout=timeout)

        except Empty:
            # No connections available, try to create new one
            with self._pool_lock:
                if self._current_size < self._max_size:
                    self._logger.debug(
                        f"Creating new connection ({self._current_size + 1}/"
                        f"{self._max_size})"
                    )
                    conn = self._create_connection()
                    self._current_size += 1
                    return conn

            # Pool is at max size, wait for a connection
            raise

    def _create_connection(self) -> pyodbc.Connection:
        """
        Create a new database connection.

        Returns:
            pyodbc.Connection: New database connection

        Raises:
            ConnectionPoolError: If connection creation fails
        """
        try:
            return ConnectionFactory.create_from_config(self._config)

        except Exception as e:
            self._logger.error(f"Failed to create connection: {e}")
            raise ConnectionPoolError(
                "Failed to create database connection",
                original_error=e
            )

    def _is_connection_alive(self, connection: pyodbc.Connection) -> bool:
        """
        Check if a connection is still alive.

        Args:
            connection: Connection to check

        Returns:
            bool: True if connection is alive, False otherwise
        """
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except:
            return False

    def close_all(self) -> None:
        """
        Close all connections in the pool.

        This should be called when shutting down the application.

        Example:
            >>> pool = ConnectionPool()
            >>> # ... use pool ...
            >>> pool.close_all()  # Cleanup on shutdown
        """
        self._logger.info("Closing all connections in pool")
        self._closed = True

        with self._pool_lock:
            # Close all connections in the pool
            while not self._pool.empty():
                try:
                    conn = self._pool.get_nowait()
                    conn.close()
                except:
                    pass

            self._current_size = 0
            self._in_use.clear()

        self._logger.info("All connections closed")

    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get current pool statistics.

        Returns:
            Dictionary with pool statistics

        Example:
            >>> stats = pool.get_pool_stats()
            >>> print(f"Available: {stats['available']}")
            >>> print(f"In use: {stats['in_use']}")
        """
        with self._pool_lock:
            return {
                'total_connections': self._current_size,
                'available': self._pool.qsize(),
                'in_use': len(self._in_use),
                'max_size': self._max_size,
                'min_size': self._min_size,
                'closed': self._closed
            }

    def __repr__(self) -> str:
        """Return string representation of pool."""
        stats = self.get_pool_stats()
        return (
            f"ConnectionPool("
            f"total={stats['total_connections']}, "
            f"available={stats['available']}, "
            f"in_use={stats['in_use']}, "
            f"max={stats['max_size']})"
        )
