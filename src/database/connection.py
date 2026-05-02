"""
Enhanced database connection with proper resource management.

Uses connection pooling and comprehensive error handling with type hints.
Fixes memory leaks from the original implementation by properly managing cursors.
"""

from typing import Optional, Any, List, Tuple, Literal
from contextlib import contextmanager
import pyodbc
from ..core.logger import get_logger
from ..core.exceptions import ConnectionError, QueryError, TransactionError
from ..core.connection_pool import ConnectionPool
from ..core.connection_factory import ConnectionFactory


class DatabaseConnection:
    """
    Enhanced database connection with proper resource management.

    This class provides a high-level interface for database operations
    with proper resource cleanup, connection pooling, and error handling.

    Features:
    - Connection pooling for efficiency
    - Context managers for automatic resource cleanup
    - Type hints for better IDE support
    - Comprehensive logging
    - Proper error handling with custom exceptions

    Example:
        >>> from config.settings import settings
        >>> from src.database.connection import DatabaseConnection
        >>>
        >>> # Using connection pool (recommended)
        >>> db = DatabaseConnection()
        >>>
        >>> # Execute query
        >>> results = db.execute_query(
        ...     "SELECT * FROM dbo.Customer WHERE Country = ?",
        ...     params=('USA',),
        ...     fetch='all'
        ... )
        >>>
        >>> # Using transactions
        >>> with db.transaction():
        ...     db.execute_query("INSERT INTO ...", params=(...))
        ...     db.execute_query("UPDATE ...", params=(...))
    """

    def __init__(self, use_pool: bool = True):
        """
        Initialize database connection.

        Args:
            use_pool: If True, uses connection pool (recommended).
                     If False, creates direct connections (for testing).

        Example:
            >>> # With connection pool (production)
            >>> db = DatabaseConnection()
            >>>
            >>> # Without pool (testing)
            >>> db = DatabaseConnection(use_pool=False)
        """
        self._use_pool = use_pool
        self._logger = get_logger(__name__)
        self._connection: Optional[pyodbc.Connection] = None
        self._in_transaction = False
        self._direct_config: Optional[dict] = None

    @contextmanager
    def get_connection(self):
        """
        Context manager for connection lifecycle.

        Automatically manages connection acquisition and release.

        Yields:
            pyodbc.Connection: Database connection

        Example:
            >>> db = DatabaseConnection()
            >>> with db.get_connection() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT 1")
        """
        if self._use_pool:
            # Use connection pool
            pool = ConnectionPool()
            with pool.get_connection() as conn:
                yield conn
        else:
            # Direct connection (for testing)
            if not self._connection:
                self._connection = self._create_direct_connection()
            try:
                yield self._connection
            except Exception as e:
                if self._connection:
                    try:
                        self._connection.rollback()
                    except:
                        pass
                raise
            finally:
                if self._connection and not self._in_transaction:
                    try:
                        self._connection.close()
                    except:
                        pass
                    self._connection = None

    @contextmanager
    def cursor(self):
        """
        Context manager for cursor lifecycle - prevents memory leaks.

        This automatically closes the cursor when done, fixing the memory leak
        issue from the original implementation.

        Yields:
            pyodbc.Cursor: Database cursor

        Example:
            >>> db = DatabaseConnection()
            >>> with db.cursor() as cur:
            ...     cur.execute("SELECT * FROM dbo.Customer")
            ...     results = cur.fetchall()
            # Cursor automatically closed here
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                try:
                    cursor.close()
                except:
                    pass

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch: Literal['none', 'one', 'all'] = 'none'
    ) -> Any:
        """
        Execute a query with proper resource management.

        Args:
            query: SQL query string
            params: Query parameters (uses placeholders to prevent SQL injection)
            fetch: Result fetching mode:
                  - 'none': Don't fetch results (for INSERT/UPDATE/DELETE)
                  - 'one': Fetch one row
                  - 'all': Fetch all rows

        Returns:
            - If fetch='none': Number of affected rows
            - If fetch='one': Single row or None
            - If fetch='all': List of rows

        Raises:
            QueryError: If query execution fails

        Example:
            >>> # SELECT query
            >>> results = db.execute_query(
            ...     "SELECT * FROM dbo.Customer WHERE Country = ?",
            ...     params=('USA',),
            ...     fetch='all'
            ... )
            >>>
            >>> # INSERT query
            >>> rows_affected = db.execute_query(
            ...     "INSERT INTO dbo.Customer (FirstName, LastName) VALUES (?, ?)",
            ...     params=('John', 'Doe'),
            ...     fetch='none'
            ... )
        """
        self._logger.debug(f"Executing query: {query[:100]}... with params: {params}")

        try:
            with self.cursor() as cur:
                cur.execute(query, params or ())

                if fetch == 'one':
                    result = cur.fetchone()
                    self._logger.debug(f"Fetched one row: {result}")
                    return result
                elif fetch == 'all':
                    results = cur.fetchall()
                    self._logger.debug(f"Fetched {len(results)} rows")
                    return results
                else:
                    # For INSERT/UPDATE/DELETE
                    affected = cur.rowcount
                    self._logger.debug(f"Query affected {affected} rows")

                    # Commit if not in manual transaction
                    if not self._in_transaction:
                        with self.get_connection() as conn:
                            conn.commit()

                    return affected

        except pyodbc.Error as e:
            self._logger.error(f"Query execution failed: {e}")
            raise QueryError(
                f"Failed to execute query: {str(e)}",
                query=query,
                params=params,
                original_error=e
            )

    def execute_many(
        self,
        query: str,
        params_list: List[Tuple]
    ) -> int:
        """
        Execute a query with multiple parameter sets (batch operation).

        Args:
            query: SQL query string with placeholders
            params_list: List of parameter tuples

        Returns:
            Number of affected rows

        Raises:
            QueryError: If execution fails

        Example:
            >>> db = DatabaseConnection()
            >>> customers = [
            ...     ('John', 'Doe', 'john@example.com'),
            ...     ('Jane', 'Smith', 'jane@example.com'),
            ...     ('Bob', 'Johnson', 'bob@example.com')
            ... ]
            >>> rows = db.execute_many(
            ...     "INSERT INTO dbo.Customer (FirstName, LastName, Email) VALUES (?, ?, ?)",
            ...     customers
            ... )
            >>> print(f"Inserted {rows} customers")
        """
        self._logger.debug(
            f"Executing batch query: {query[:100]}... with {len(params_list)} parameter sets"
        )

        try:
            with self.cursor() as cur:
                cur.executemany(query, params_list)
                affected = cur.rowcount

                # Commit if not in manual transaction
                if not self._in_transaction:
                    with self.get_connection() as conn:
                        conn.commit()

                self._logger.info(f"Batch query affected {affected} rows")
                return affected

        except pyodbc.Error as e:
            self._logger.error(f"Batch query execution failed: {e}")
            raise QueryError(
                f"Failed to execute batch query: {str(e)}",
                query=query,
                params=params_list[0] if params_list else None,
                original_error=e
            )

    @contextmanager
    def transaction(self):
        """
        Context manager for transaction management.

        Automatically commits on success, rolls back on exception.

        Yields:
            pyodbc.Connection: Database connection in transaction

        Raises:
            TransactionError: If transaction fails

        Example:
            >>> db = DatabaseConnection()
            >>> try:
            ...     with db.transaction():
            ...         db.execute_query("INSERT INTO ...", params=(...))
            ...         db.execute_query("UPDATE ...", params=(...))
            ...         # Commits automatically if no exception
            ... except Exception as e:
            ...     # Rolls back automatically on exception
            ...     print(f"Transaction failed: {e}")
        """
        self._logger.debug("Beginning transaction")
        self._in_transaction = True

        try:
            with self.get_connection() as conn:
                yield conn
                conn.commit()
                self._logger.debug("Transaction committed")
        except Exception as e:
            self._logger.error(f"Transaction failed, rolling back: {e}")
            with self.get_connection() as conn:
                try:
                    conn.rollback()
                    self._logger.debug("Transaction rolled back")
                except:
                    pass
            raise TransactionError(f"Transaction failed: {str(e)}", original_error=e)
        finally:
            self._in_transaction = False

    def _create_direct_connection(self) -> pyodbc.Connection:
        """
        Create a direct database connection (bypasses pool).

        Returns:
            pyodbc.Connection: New database connection

        Raises:
            ConnectionError: If connection creation fails

        Note:
            This is used internally when use_pool=False.
            For production, use connection pool instead.
        """
        if not self._direct_config:
            from config.settings import settings
            self._direct_config = settings.get_db_config()

        self._logger.debug("Creating direct database connection")

        try:
            return ConnectionFactory.create_from_config(self._direct_config)
        except Exception as e:
            self._logger.error(f"Failed to create direct connection: {e}")
            raise ConnectionError(
                "Failed to create database connection",
                original_error=e
            )

    def close(self) -> None:
        """
        Close the connection (if using direct connection).

        Note:
            When using connection pool, this does nothing (pool manages connections).
            When using direct connection, this closes the connection.

        Example:
            >>> db = DatabaseConnection(use_pool=False)
            >>> # ... use db ...
            >>> db.close()
        """
        if not self._use_pool and self._connection:
            try:
                self._connection.close()
                self._logger.debug("Direct connection closed")
            except Exception as e:
                self._logger.error(f"Error closing connection: {e}")
            finally:
                self._connection = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type:
            # Exception occurred
            if not self._use_pool and self._connection:
                try:
                    self._connection.rollback()
                except:
                    pass
        self.close()

    def __repr__(self) -> str:
        """Return string representation."""
        mode = "pooled" if self._use_pool else "direct"
        in_txn = " (in transaction)" if self._in_transaction else ""
        return f"DatabaseConnection(mode={mode}{in_txn})"
