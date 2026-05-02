"""
Custom exception hierarchy for database operations.

All database-related exceptions inherit from DatabaseError for easy catching
and handling. Each exception type provides specific context about the error.
"""

from typing import Optional, Any, Tuple


class DatabaseError(Exception):
    """
    Base exception for all database-related errors.

    All custom exceptions in this module inherit from this class,
    allowing users to catch all database errors with a single except clause.

    Attributes:
        message: Human-readable error message
        original_error: The original exception that caused this error (if any)
    """

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.original_error = original_error

    def __str__(self) -> str:
        if self.original_error:
            return f"{self.message} (Caused by: {str(self.original_error)})"
        return self.message


class ConnectionError(DatabaseError):
    """
    Raised when connection to database fails.

    This can occur due to:
    - Invalid credentials
    - Network issues
    - Database server not available
    - Invalid connection string

    Example:
        >>> raise ConnectionError("Failed to connect to localhost", original_error=e)
    """
    pass


class ConnectionPoolError(DatabaseError):
    """
    Raised when connection pool operations fail.

    This can occur when:
    - Pool initialization fails
    - Unable to create new connections
    - Pool is in invalid state

    Example:
        >>> raise ConnectionPoolError("Connection pool exhausted")
    """
    pass


class ConnectionTimeoutError(ConnectionPoolError):
    """
    Raised when connection pool timeout occurs.

    This happens when all connections are in use and timeout expires
    while waiting for an available connection.

    Attributes:
        timeout: The timeout value in seconds

    Example:
        >>> raise ConnectionTimeoutError("Timeout waiting for connection", timeout=30.0)
    """

    def __init__(self, message: str, timeout: Optional[float] = None,
                 original_error: Optional[Exception] = None):
        super().__init__(message, original_error)
        self.timeout = timeout


class QueryError(DatabaseError):
    """
    Raised when query execution fails.

    This can occur due to:
    - Syntax errors in SQL
    - Invalid table or column names
    - Permission issues
    - Data type mismatches

    Attributes:
        query: The SQL query that failed
        params: The parameters passed to the query

    Example:
        >>> raise QueryError(
        ...     "Failed to execute query",
        ...     query="SELECT * FROM users WHERE id = ?",
        ...     params=(123,),
        ...     original_error=e
        ... )
    """

    def __init__(self, message: str, query: str, params: Optional[Tuple] = None,
                 original_error: Optional[Exception] = None):
        super().__init__(message, original_error)
        self.query = query
        self.params = params

    def __str__(self) -> str:
        base_msg = super().__str__()
        details = f"\nQuery: {self.query}"
        if self.params:
            details += f"\nParams: {self.params}"
        return base_msg + details


class ValidationError(DatabaseError):
    """
    Raised when data validation fails.

    This occurs before database operations when input data
    doesn't meet validation requirements.

    Attributes:
        field: The field name that failed validation (if applicable)
        value: The value that failed validation (if applicable)

    Example:
        >>> raise ValidationError(
        ...     "Invalid email format",
        ...     field="email",
        ...     value="invalid-email"
        ... )
    """

    def __init__(self, message: str, field: Optional[str] = None,
                 value: Optional[Any] = None):
        super().__init__(message)
        self.field = field
        self.value = value

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.field:
            details = f"\nField: {self.field}"
            if self.value is not None:
                details += f"\nValue: {self.value}"
            return base_msg + details
        return base_msg


class RepositoryError(DatabaseError):
    """
    Raised when repository operations fail.

    This is a high-level error that occurs during repository
    method execution (CRUD operations, custom queries, etc.)

    Example:
        >>> raise RepositoryError("Failed to insert customer", original_error=e)
    """
    pass


class TransactionError(DatabaseError):
    """
    Raised when transaction operations fail.

    This can occur during:
    - Transaction begin
    - Transaction commit
    - Transaction rollback

    Example:
        >>> raise TransactionError("Failed to commit transaction", original_error=e)
    """
    pass


class ModelError(DatabaseError):
    """
    Raised when model operations fail.

    This can occur when:
    - Converting between database rows and models
    - Invalid model state
    - Model validation failures

    Example:
        >>> raise ModelError("Failed to convert row to Customer model")
    """
    pass
