"""
Customer model matching the dbo.Customer table from Chinook database.
"""

from dataclasses import dataclass
from typing import Optional
from .base_model import BaseModel
from ..core.exceptions import ValidationError


@dataclass
class Customer(BaseModel):
    """
    Customer model matching dbo.Customer table.

    This model represents a customer in the Chinook database with all fields
    matching the database schema.

    Example:
        >>> customer = Customer(
        ...     CustomerId=1,
        ...     FirstName="John",
        ...     LastName="Doe",
        ...     Email="john@example.com",
        ...     Country="USA"
        ... )
        >>> customer.validate()
        >>> print(customer.full_name)
        'John Doe'
    """

    CustomerId: int
    FirstName: str
    LastName: str
    Company: Optional[str] = None
    Address: Optional[str] = None
    City: Optional[str] = None
    State: Optional[str] = None
    Country: Optional[str] = None
    PostalCode: Optional[str] = None
    Phone: Optional[str] = None
    Fax: Optional[str] = None
    Email: str = ""
    SupportRepId: Optional[int] = None

    def validate(self) -> None:
        """
        Validate customer data.

        Raises:
            ValidationError: If validation fails

        Validation rules:
        - FirstName and LastName are required
        - Email must contain '@' if provided
        - CustomerId must be >= 0
        """
        # Required fields
        if not self.FirstName or not self.FirstName.strip():
            raise ValidationError(
                "First name is required",
                field="FirstName",
                value=self.FirstName
            )

        if not self.LastName or not self.LastName.strip():
            raise ValidationError(
                "Last name is required",
                field="LastName",
                value=self.LastName
            )

        # Email validation (if provided)
        if self.Email and '@' not in self.Email:
            raise ValidationError(
                "Invalid email format - must contain '@'",
                field="Email",
                value=self.Email
            )

        # CustomerId validation
        if self.CustomerId < 0:
            raise ValidationError(
                "CustomerId must be >= 0",
                field="CustomerId",
                value=self.CustomerId
            )

    @property
    def full_name(self) -> str:
        """
        Get customer's full name.

        Returns:
            str: FirstName + LastName

        Example:
            >>> customer = Customer(
            ...     CustomerId=1,
            ...     FirstName="John",
            ...     LastName="Doe",
            ...     Email="john@example.com"
            ... )
            >>> print(customer.full_name)
            'John Doe'
        """
        return f"{self.FirstName} {self.LastName}"

    @property
    def full_address(self) -> str:
        """
        Get customer's full address.

        Returns:
            str: Formatted address or "No address" if not available

        Example:
            >>> customer = Customer(
            ...     CustomerId=1,
            ...     FirstName="John",
            ...     LastName="Doe",
            ...     Email="john@example.com",
            ...     Address="123 Main St",
            ...     City="New York",
            ...     State="NY",
            ...     Country="USA",
            ...     PostalCode="10001"
            ... )
            >>> print(customer.full_address)
            '123 Main St, New York, NY 10001, USA'
        """
        parts = []

        if self.Address:
            parts.append(self.Address)

        if self.City:
            city_state = self.City
            if self.State:
                city_state += f", {self.State}"
            parts.append(city_state)

        if self.PostalCode:
            parts.append(self.PostalCode)

        if self.Country:
            parts.append(self.Country)

        return ", ".join(parts) if parts else "No address"

    def __str__(self) -> str:
        """Return string representation of customer."""
        return f"Customer({self.CustomerId}: {self.full_name} - {self.Email})"
