"""
Input validation utilities.

Provides common validation functions for data integrity.
"""

import re
from typing import Any
from ..core.exceptions import ValidationError


def validate_email(email: str, field_name: str = "email") -> None:
    """
    Validate email format.

    Args:
        email: Email address to validate
        field_name: Name of the field (for error messages)

    Raises:
        ValidationError: If email is invalid

    Example:
        >>> validate_email("test@example.com")  # OK
        >>> validate_email("invalid")  # Raises ValidationError
    """
    if not email or '@' not in email:
        raise ValidationError(
            f"Invalid email format",
            field=field_name,
            value=email
        )

    # Simple email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError(
            f"Invalid email format",
            field=field_name,
            value=email
        )


def validate_not_empty(value: str, field_name: str) -> None:
    """
    Validate that string is not empty.

    Args:
        value: String to validate
        field_name: Name of the field

    Raises:
        ValidationError: If string is None or empty

    Example:
        >>> validate_not_empty("test", "name")  # OK
        >>> validate_not_empty("", "name")  # Raises ValidationError
    """
    if not value or not value.strip():
        raise ValidationError(
            f"{field_name} cannot be empty",
            field=field_name,
            value=value
        )


def validate_length(
    value: str,
    field_name: str,
    min_length: int = 0,
    max_length: int = None
) -> None:
    """
    Validate string length.

    Args:
        value: String to validate
        field_name: Name of the field
        min_length: Minimum length (default 0)
        max_length: Maximum length (optional)

    Raises:
        ValidationError: If length is invalid

    Example:
        >>> validate_length("test", "name", min_length=2, max_length=10)
    """
    if value is None:
        value = ""

    length = len(value)

    if length < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters",
            field=field_name,
            value=value
        )

    if max_length and length > max_length:
        raise ValidationError(
            f"{field_name} must be at most {max_length} characters",
            field=field_name,
            value=value
        )


def validate_positive(value: Any, field_name: str) -> None:
    """
    Validate that number is positive.

    Args:
        value: Number to validate
        field_name: Name of the field

    Raises:
        ValidationError: If number is not positive

    Example:
        >>> validate_positive(10, "age")  # OK
        >>> validate_positive(-5, "age")  # Raises ValidationError
    """
    try:
        num = float(value)
        if num <= 0:
            raise ValidationError(
                f"{field_name} must be positive",
                field=field_name,
                value=value
            )
    except (ValueError, TypeError):
        raise ValidationError(
            f"{field_name} must be a number",
            field=field_name,
            value=value
        )


def validate_range(
    value: Any,
    field_name: str,
    min_value: float = None,
    max_value: float = None
) -> None:
    """
    Validate that number is in range.

    Args:
        value: Number to validate
        field_name: Name of the field
        min_value: Minimum value (optional)
        max_value: Maximum value (optional)

    Raises:
        ValidationError: If number is out of range

    Example:
        >>> validate_range(5, "rating", min_value=1, max_value=10)
    """
    try:
        num = float(value)

        if min_value is not None and num < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}",
                field=field_name,
                value=value
            )

        if max_value is not None and num > max_value:
            raise ValidationError(
                f"{field_name} must be at most {max_value}",
                field=field_name,
                value=value
            )

    except (ValueError, TypeError):
        raise ValidationError(
            f"{field_name} must be a number",
            field=field_name,
            value=value
        )
