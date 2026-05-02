"""
Factory for creating database connections with different configurations.

Implements the Factory pattern to centralize connection creation logic
and support multiple connection types (SQL Server, Azure SQL, custom).
"""

from typing import Dict, Any
import pyodbc
from .logger import get_logger
from .exceptions import ConnectionError as DBConnectionError


class ConnectionFactory:
    """
    Factory for creating database connections.

    This class provides static methods to create database connections
    with different configurations, following the Factory design pattern.

    Supports:
    - Standard SQL Server connections
    - Azure SQL Database connections
    - Custom connection strings
    - Connection from configuration dictionary

    Example:
        >>> conn = ConnectionFactory.create_connection(
        ...     driver="ODBC Driver 17 for SQL Server",
        ...     server="localhost",
        ...     database="Chinook",
        ...     username="user",
        ...     password="password"
        ... )
    """

    _logger = get_logger(__name__)

    @staticmethod
    def create_connection(
        driver: str,
        server: str,
        database: str,
        username: str,
        password: str,
        **kwargs
    ) -> pyodbc.Connection:
        """
        Create a database connection with standard parameters.

        Args:
            driver: ODBC driver name (e.g., "ODBC Driver 17 for SQL Server")
            server: Server address (e.g., "localhost", "192.168.1.50,1433")
            database: Database name
            username: Database username
            password: Database password
            **kwargs: Additional connection parameters (e.g., trust_certificate,
                     encrypt, timeout, etc.)

        Returns:
            pyodbc.Connection: Active database connection

        Raises:
            ConnectionError: If connection fails

        Example:
            >>> conn = ConnectionFactory.create_connection(
            ...     driver="ODBC Driver 17 for SQL Server",
            ...     server="localhost",
            ...     database="Chinook",
            ...     username="sa",
            ...     password="password",
            ...     trust_certificate="yes"
            ... )
        """
        ConnectionFactory._logger.debug(
            f"Creating connection to {server}/{database} as {username}"
        )

        try:
            conn_str = ConnectionFactory._build_connection_string(
                driver=driver,
                server=server,
                database=database,
                username=username,
                password=password,
                **kwargs
            )

            # Don't log the full connection string (contains password)
            ConnectionFactory._logger.debug("Connecting to database...")

            connection = pyodbc.connect(conn_str)

            ConnectionFactory._logger.info(
                f"Successfully connected to {server}/{database}"
            )

            return connection

        except pyodbc.Error as e:
            ConnectionFactory._logger.error(
                f"Failed to connect to {server}/{database}: {str(e)}"
            )
            raise DBConnectionError(
                f"Failed to connect to {server}/{database}",
                original_error=e
            )

    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> pyodbc.Connection:
        """
        Create connection from configuration dictionary.

        Args:
            config: Dictionary containing connection parameters.
                   Must include: driver, server, database, username, password
                   Optional: Any other pyodbc connection parameters

        Returns:
            pyodbc.Connection: Active database connection

        Raises:
            ConnectionError: If connection fails
            ValueError: If required config keys are missing

        Example:
            >>> config = {
            ...     'driver': 'ODBC Driver 17 for SQL Server',
            ...     'server': 'localhost',
            ...     'database': 'Chinook',
            ...     'username': 'user',
            ...     'password': 'pass',
            ...     'trust_certificate': 'yes'
            ... }
            >>> conn = ConnectionFactory.create_from_config(config)
        """
        required_keys = ['driver', 'server', 'database', 'username', 'password']
        missing_keys = [key for key in required_keys if key not in config]

        if missing_keys:
            raise ValueError(
                f"Missing required configuration keys: {', '.join(missing_keys)}"
            )

        # Extract required parameters
        driver = config['driver']
        server = config['server']
        database = config['database']
        username = config['username']
        password = config['password']

        # Extract optional parameters (everything else is kwargs)
        optional_params = {k: v for k, v in config.items()
                          if k not in ['driver', 'server', 'database', 'username', 'password']}

        return ConnectionFactory.create_connection(
            driver=driver,
            server=server,
            database=database,
            username=username,
            password=password,
            **optional_params
        )

    @staticmethod
    def create_from_connection_string(conn_str: str) -> pyodbc.Connection:
        """
        Create connection from connection string.

        Args:
            conn_str: ODBC connection string

        Returns:
            pyodbc.Connection: Active database connection

        Raises:
            ConnectionError: If connection fails

        Example:
            >>> conn_str = (
            ...     "DRIVER={ODBC Driver 17 for SQL Server};"
            ...     "SERVER=localhost;"
            ...     "DATABASE=Chinook;"
            ...     "UID=user;"
            ...     "PWD=password;"
            ...     "TrustServerCertificate=yes;"
            ... )
            >>> conn = ConnectionFactory.create_from_connection_string(conn_str)

        Warning:
            Connection strings may contain passwords. Be careful when logging
            or displaying connection strings.
        """
        ConnectionFactory._logger.debug("Creating connection from connection string")

        try:
            connection = pyodbc.connect(conn_str)
            ConnectionFactory._logger.info("Successfully connected to database")
            return connection

        except pyodbc.Error as e:
            ConnectionFactory._logger.error(f"Failed to connect: {str(e)}")
            raise DBConnectionError(
                "Failed to connect to database",
                original_error=e
            )

    @staticmethod
    def create_azure_sql_connection(
        server: str,
        database: str,
        username: str,
        password: str,
        **kwargs
    ) -> pyodbc.Connection:
        """
        Create a connection to Azure SQL Database.

        This is a convenience method that sets Azure-specific defaults.

        Args:
            server: Azure SQL server name (e.g., "myserver.database.windows.net")
            database: Database name
            username: Username (often in format user@servername)
            password: Password
            **kwargs: Additional connection parameters

        Returns:
            pyodbc.Connection: Active database connection

        Raises:
            ConnectionError: If connection fails

        Example:
            >>> conn = ConnectionFactory.create_azure_sql_connection(
            ...     server="myserver.database.windows.net",
            ...     database="Chinook",
            ...     username="admin@myserver",
            ...     password="password"
            ... )
        """
        # Azure SQL defaults
        defaults = {
            'driver': 'ODBC Driver 17 for SQL Server',
            'encrypt': 'yes',
            'trust_certificate': 'no',
            'connection_timeout': '30'
        }

        # Merge defaults with kwargs (kwargs takes precedence)
        params = {**defaults, **kwargs}

        return ConnectionFactory.create_connection(
            driver=params.pop('driver'),
            server=server,
            database=database,
            username=username,
            password=password,
            **params
        )

    @staticmethod
    def _build_connection_string(
        driver: str,
        server: str,
        database: str,
        username: str,
        password: str,
        **kwargs
    ) -> str:
        """
        Build ODBC connection string from parameters.

        Args:
            driver: ODBC driver name
            server: Server address
            database: Database name
            username: Username
            password: Password
            **kwargs: Additional parameters (will be added to connection string)

        Returns:
            str: Formatted ODBC connection string

        Note:
            This is an internal method. Use create_connection() instead.
        """
        # Build base connection string
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
        )

        # Add additional parameters
        # Convert parameter names: trust_certificate -> TrustServerCertificate
        for key, value in kwargs.items():
            # Convert snake_case to PascalCase for ODBC parameters
            odbc_key = ''.join(word.capitalize() for word in key.split('_'))
            conn_str += f"{odbc_key}={value};"

        return conn_str
