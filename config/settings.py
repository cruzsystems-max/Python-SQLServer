"""
Application settings loaded from environment variables.

Uses python-dotenv to load configuration from .env file,
providing a secure way to manage credentials and settings.
"""

from typing import Dict, Any
import os
from pathlib import Path
from dotenv import load_dotenv


class Settings:
    """
    Application settings loaded from environment variables.

    This class uses python-dotenv to load configuration from a .env file
    in the project root, providing secure credential management and
    environment-specific configuration.

    Example:
        >>> from config.settings import settings
        >>> config = settings.get_db_config()
        >>> print(config['server'])
        'localhost'

    Note:
        Create a .env file in the project root based on .env.example
        and fill in your actual credentials.
    """

    def __init__(self):
        """
        Initialize settings by loading environment variables from .env file.

        The .env file should be located in the project root directory.
        If the file doesn't exist, environment variables from the system
        will be used instead.
        """
        # Load .env file from project root (parent of config directory)
        env_path = Path(__file__).parent.parent / '.env'

        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
        else:
            # Try loading from current directory as fallback
            load_dotenv()

        # Database configuration
        self.DB_DRIVER = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
        self.DB_SERVER = os.getenv('DB_SERVER', 'localhost')
        self.DB_NAME = os.getenv('DB_NAME', 'master')
        self.DB_USERNAME = os.getenv('DB_USERNAME', '')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD', '')
        self.DB_TRUST_CERTIFICATE = os.getenv('DB_TRUST_CERTIFICATE', 'yes')

        # Connection pool settings
        self.POOL_MIN_SIZE = int(os.getenv('POOL_MIN_SIZE', '2'))
        self.POOL_MAX_SIZE = int(os.getenv('POOL_MAX_SIZE', '10'))
        self.POOL_TIMEOUT = float(os.getenv('POOL_TIMEOUT', '30.0'))

        # Logging configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.getenv('LOG_FILE', 'logs/database.log')

    def get_db_config(self) -> Dict[str, Any]:
        """
        Get database configuration as dictionary.

        Returns:
            Dictionary containing database connection parameters

        Example:
            >>> config = settings.get_db_config()
            >>> print(config)
            {
                'driver': 'ODBC Driver 17 for SQL Server',
                'server': 'localhost',
                'database': 'Chinook',
                'username': 'user',
                'password': '***',
                'trust_certificate': 'yes'
            }
        """
        return {
            'driver': self.DB_DRIVER,
            'server': self.DB_SERVER,
            'database': self.DB_NAME,
            'username': self.DB_USERNAME,
            'password': self.DB_PASSWORD,
            'trust_certificate': self.DB_TRUST_CERTIFICATE
        }

    def get_pool_config(self) -> Dict[str, Any]:
        """
        Get connection pool configuration as dictionary.

        Returns:
            Dictionary containing pool parameters

        Example:
            >>> pool_config = settings.get_pool_config()
            >>> print(pool_config['max_size'])
            10
        """
        return {
            'min_size': self.POOL_MIN_SIZE,
            'max_size': self.POOL_MAX_SIZE,
            'timeout': self.POOL_TIMEOUT
        }

    def validate(self) -> bool:
        """
        Validate required settings are present.

        Raises:
            ValueError: If required settings are missing

        Returns:
            True if all required settings are present

        Example:
            >>> settings.validate()
            True
        """
        required = {
            'DB_SERVER': self.DB_SERVER,
            'DB_NAME': self.DB_NAME,
            'DB_USERNAME': self.DB_USERNAME,
            'DB_PASSWORD': self.DB_PASSWORD
        }

        missing = [key for key, value in required.items() if not value]

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Please create a .env file based on .env.example"
            )

        return True

    def __repr__(self) -> str:
        """Return string representation of settings (without sensitive data)."""
        return (
            f"Settings("
            f"server={self.DB_SERVER}, "
            f"database={self.DB_NAME}, "
            f"username={self.DB_USERNAME}, "
            f"pool_size={self.POOL_MIN_SIZE}-{self.POOL_MAX_SIZE})"
        )


# Global settings instance
# Import this in other modules: from config.settings import settings
settings = Settings()
