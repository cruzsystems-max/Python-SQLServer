"""
Centralized logging configuration for the database framework.

Provides a standardized logging setup with file and console output,
configurable log levels, and structured formatting.
"""

import logging
import sys
from typing import Optional
from pathlib import Path

# Import colorama for Windows compatibility
try:
    from colorama import init, Fore, Style, Back
    init(autoreset=True)  # Initialize colorama for Windows
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to log output.

    Uses colorama for Windows compatibility.
    """

    # Color scheme for different log levels
    COLORS = {
        'DEBUG': Fore.CYAN if COLORS_AVAILABLE else '',
        'INFO': Fore.GREEN if COLORS_AVAILABLE else '',
        'WARNING': Fore.YELLOW if COLORS_AVAILABLE else '',
        'ERROR': Fore.RED if COLORS_AVAILABLE else '',
        'CRITICAL': Fore.RED + Back.WHITE if COLORS_AVAILABLE else '',
    } if COLORS_AVAILABLE else {}

    RESET = Style.RESET_ALL if COLORS_AVAILABLE else ''

    def format(self, record):
        """Format the log record with colors."""
        if COLORS_AVAILABLE and record.levelname in self.COLORS:
            # Save original levelname
            levelname = record.levelname

            # Add color to levelname
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"

            # Format the message
            formatted = super().format(record)

            # Restore original levelname
            record.levelname = levelname

            return formatted
        else:
            return super().format(record)


class DatabaseLogger:
    """
    Centralized logging configuration for the application.

    This class provides a singleton-like configuration for logging across
    the entire application. Once configured, all loggers will use the same
    settings.

    Example:
        >>> from src.core.logger import DatabaseLogger, get_logger
        >>> DatabaseLogger.configure(log_level="DEBUG", log_file="logs/app.log")
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """

    _configured = False

    @classmethod
    def configure(
        cls,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        format_string: Optional[str] = None
    ) -> None:
        """
        Configure application-wide logging.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file. If None, only console logging is enabled
            format_string: Custom format string for log messages

        Note:
            This method only configures logging once. Subsequent calls are ignored
            to prevent duplicate handlers.

        Example:
            >>> DatabaseLogger.configure(
            ...     log_level="DEBUG",
            ...     log_file="logs/database.log"
            ... )
        """
        if cls._configured:
            return

        if format_string is None:
            format_string = (
                '%(asctime)s - %(name)s - %(levelname)s - '
                '%(filename)s:%(lineno)d - %(message)s'
            )

        # Create formatters
        # Use colored formatter for console, regular for file
        colored_formatter = ColoredFormatter(format_string)
        file_formatter = logging.Formatter(format_string)

        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))

        # Clear any existing handlers
        root_logger.handlers.clear()

        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(colored_formatter)
        root_logger.addHandler(console_handler)

        # File handler (if log file specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(getattr(logging, log_level.upper()))
            file_handler.setFormatter(file_formatter)  # Use plain formatter for files
            root_logger.addHandler(file_handler)

        cls._configured = True

    @classmethod
    def reset(cls) -> None:
        """
        Reset logging configuration.

        This is primarily useful for testing where you need to reconfigure
        logging between tests.

        Warning:
            Use with caution in production code.
        """
        cls._configured = False
        logging.getLogger().handlers.clear()


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.

    This function ensures logging is configured before returning a logger.
    If not already configured, it uses default settings.

    Args:
        name: Name of the logger, typically __name__ from the calling module

    Returns:
        A configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing customer data")
        >>> logger.error("Failed to connect to database", exc_info=True)

    Note:
        The logger will use the module's full path as its name, which helps
        with filtering and debugging in logs.
    """
    # Ensure logging is configured with defaults if not already done
    DatabaseLogger.configure()
    return logging.getLogger(name)


class SensitiveDataFilter(logging.Filter):
    """
    Filter to prevent sensitive data from appearing in logs.

    This filter masks common sensitive fields like passwords, tokens,
    and API keys before they are written to logs.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.addFilter(SensitiveDataFilter())
        >>> logger.info("Config: password=secret123")  # Will be masked
    """

    SENSITIVE_KEYS = [
        'password', 'pwd', 'passwd', 'secret', 'token',
        'api_key', 'apikey', 'auth', 'credentials'
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record to mask sensitive data.

        Args:
            record: The log record to filter

        Returns:
            True (always allows the record, just modifies it)
        """
        message = record.getMessage().lower()

        for key in self.SENSITIVE_KEYS:
            if key in message:
                # Mask the sensitive data
                record.msg = str(record.msg).replace(
                    key,
                    f"{key}=***REDACTED***"
                )

        return True
