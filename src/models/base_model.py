"""
Base model class for database entities.

Provides common functionality for all models including dictionary conversion,
database row mapping, and validation.
"""

from typing import Dict, Any, List, Type, TypeVar
from dataclasses import dataclass, asdict, fields
from datetime import datetime, date


T = TypeVar('T', bound='BaseModel')


@dataclass
class BaseModel:
    """
    Base class for all database models.

    This class provides common functionality for models including:
    - Conversion to/from dictionaries
    - Conversion from database rows
    - Base validation framework

    All model classes should inherit from this and be decorated with @dataclass.

    Example:
        >>> @dataclass
        ... class User(BaseModel):
        ...     id: int
        ...     name: str
        ...     email: str
        ...
        ...     def validate(self) -> None:
        ...         if '@' not in self.email:
        ...             raise ValidationError("Invalid email")
        >>>
        >>> user = User(id=1, name="John", email="john@example.com")
        >>> user.validate()
        >>> user_dict = user.to_dict()
    """

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.

        Returns:
            Dictionary representation of the model

        Example:
            >>> user = User(id=1, name="John", email="john@example.com")
            >>> user.to_dict()
            {'id': 1, 'name': 'John', 'email': 'john@example.com'}
        """
        return asdict(self)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create model instance from dictionary.

        Only includes fields that exist in the model definition,
        ignoring extra keys in the dictionary.

        Args:
            data: Dictionary with model data

        Returns:
            New instance of the model

        Example:
            >>> data = {'id': 1, 'name': 'John', 'email': 'john@example.com'}
            >>> user = User.from_dict(data)
        """
        # Get field names for this class
        field_names = {f.name for f in fields(cls)}

        # Filter data to only include valid fields
        filtered_data = {k: v for k, v in data.items() if k in field_names}

        return cls(**filtered_data)

    @classmethod
    def from_row(cls: Type[T], row: Any) -> T:
        """
        Create model instance from database row.

        Supports both pyodbc.Row objects and dictionaries.

        Args:
            row: Database row (pyodbc.Row or dict-like object)

        Returns:
            New instance of the model

        Example:
            >>> cursor.execute("SELECT * FROM users WHERE id = ?", (1,))
            >>> row = cursor.fetchone()
            >>> user = User.from_row(row)
        """
        if row is None:
            return None

        # Check if it's a pyodbc.Row
        if hasattr(row, 'cursor_description'):
            # Convert pyodbc.Row to dict
            data = {
                desc[0]: getattr(row, desc[0])
                for desc in row.cursor_description
            }
        else:
            # Assume it's already dict-like
            data = dict(row) if not isinstance(row, dict) else row

        return cls.from_dict(data)

    @classmethod
    def from_rows(cls: Type[T], rows: List[Any]) -> List[T]:
        """
        Create list of model instances from database rows.

        Args:
            rows: List of database rows

        Returns:
            List of model instances

        Example:
            >>> cursor.execute("SELECT * FROM users")
            >>> rows = cursor.fetchall()
            >>> users = User.from_rows(rows)
        """
        return [cls.from_row(row) for row in rows if row is not None]

    def validate(self) -> None:
        """
        Validate model data.

        Override this method in subclasses to implement custom validation logic.
        Should raise ValidationError if validation fails.

        Raises:
            ValidationError: If validation fails

        Example:
            >>> @dataclass
            ... class User(BaseModel):
            ...     email: str
            ...
            ...     def validate(self) -> None:
            ...         if '@' not in self.email:
            ...             from src.core.exceptions import ValidationError
            ...             raise ValidationError(
            ...                 "Invalid email format",
            ...                 field="email",
            ...                 value=self.email
            ...             )
        """
        pass

    def __str__(self) -> str:
        """
        Return string representation of the model.

        Returns:
            String representation with class name and fields
        """
        field_strs = [
            f"{f.name}={getattr(self, f.name)}"
            for f in fields(self)
        ]
        return f"{self.__class__.__name__}({', '.join(field_strs)})"

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return self.__str__()

    def copy(self: T) -> T:
        """
        Create a copy of this model instance.

        Returns:
            New instance with the same field values

        Example:
            >>> user = User(id=1, name="John", email="john@example.com")
            >>> user_copy = user.copy()
            >>> user_copy.name = "Jane"
            >>> print(user.name)  # Still "John"
        """
        return self.__class__(**self.to_dict())

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Update model fields from dictionary.

        Only updates fields that exist in the model definition.

        Args:
            data: Dictionary with new values

        Example:
            >>> user = User(id=1, name="John", email="john@example.com")
            >>> user.update_from_dict({'name': 'Jane', 'email': 'jane@example.com'})
            >>> print(user.name)  # "Jane"
        """
        field_names = {f.name for f in fields(self)}

        for key, value in data.items():
            if key in field_names:
                setattr(self, key, value)
