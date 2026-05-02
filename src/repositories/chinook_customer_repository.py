"""
Repository for Customer table with custom queries.

Demonstrates how to extend BaseRepository with custom query methods.
"""

from typing import List, Optional
from ..database.base_repository import BaseRepository
from ..models.chinook_customer import Customer


class CustomerRepository(BaseRepository[Customer]):
    """
    Repository for Customer table.

    Provides generic CRUD operations from BaseRepository plus custom queries
    specific to customers.

    Example:
        >>> from config.settings import settings
        >>> from src.core.connection_pool import ConnectionPool
        >>> from src.database.connection import DatabaseConnection
        >>> from src.repositories.customer_repository import CustomerRepository
        >>> from src.models.customer import Customer
        >>>
        >>> # Initialize connection pool
        >>> pool = ConnectionPool()
        >>> pool.initialize(settings.get_db_config())
        >>>
        >>> # Create repository
        >>> db = DatabaseConnection()
        >>> repo = CustomerRepository(db, Customer)
        >>>
        >>> # Use generic CRUD
        >>> customer = repo.find_by_id(1)
        >>> all_customers = repo.find_all(limit=10)
        >>>
        >>> # Use custom methods
        >>> customer = repo.find_by_email('john@example.com')
        >>> usa_customers = repo.find_by_country('USA')
    """

    @property
    def table_name(self) -> str:
        """Return the table name."""
        return "dbo.Customer"

    @property
    def primary_key(self) -> str:
        """Return the primary key column name."""
        return "CustomerId"

    # ==================== Custom Query Methods ====================

    def find_by_email(self, email: str) -> Optional[Customer]:
        """
        Find customer by email address.

        Args:
            email: Customer email

        Returns:
            Customer instance or None if not found

        Example:
            >>> customer = repo.find_by_email('john@example.com')
            >>> if customer:
            ...     print(customer.full_name)
        """
        return self.find_one_by(Email=email)

    def find_by_country(self, country: str) -> List[Customer]:
        """
        Find all customers in a country.

        Args:
            country: Country name

        Returns:
            List of customers in the specified country

        Example:
            >>> usa_customers = repo.find_by_country('USA')
            >>> print(f"Found {len(usa_customers)} customers in USA")
        """
        return self.find_by(Country=country)

    def find_by_city(self, city: str) -> List[Customer]:
        """
        Find all customers in a city.

        Args:
            city: City name

        Returns:
            List of customers in the specified city

        Example:
            >>> nyc_customers = repo.find_by_city('New York')
        """
        return self.find_by(City=city)

    def search_by_name(self, name: str) -> List[Customer]:
        """
        Search customers by name (uses LIKE for partial matches).

        Searches in both FirstName and LastName fields.

        Args:
            name: Name to search for (partial match)

        Returns:
            List of customers matching the name

        Example:
            >>> customers = repo.search_by_name('John')
            >>> # Finds customers with 'John' in first or last name
        """
        query = """
            SELECT * FROM dbo.Customer
            WHERE FirstName LIKE ? OR LastName LIKE ?
            ORDER BY FirstName, LastName
        """
        search_term = f"%{name}%"
        return self.execute_raw(query, (search_term, search_term))

    def find_customers_with_support_rep(self, support_rep_id: int) -> List[Customer]:
        """
        Find all customers assigned to a specific support representative.

        Args:
            support_rep_id: Support representative ID

        Returns:
            List of customers assigned to the rep

        Example:
            >>> customers = repo.find_customers_with_support_rep(3)
        """
        return self.find_by(SupportRepId=support_rep_id)

    def count_by_country(self) -> List[tuple]:
        """
        Get customer count grouped by country.

        Returns:
            List of tuples (Country, Count) ordered by count descending

        Example:
            >>> country_counts = repo.count_by_country()
            >>> for country, count in country_counts:
            ...     print(f"{country}: {count} customers")
        """
        query = """
            SELECT Country, COUNT(*) as CustomerCount
            FROM dbo.Customer
            GROUP BY Country
            ORDER BY CustomerCount DESC, Country
        """
        results = self._connection.execute_query(query, fetch='all')
        return [(row[0], row[1]) for row in results]

    def find_customers_without_company(self) -> List[Customer]:
        """
        Find customers who don't have a company.

        Returns:
            List of customers with NULL or empty company

        Example:
            >>> personal_customers = repo.find_customers_without_company()
        """
        query = """
            SELECT * FROM dbo.Customer
            WHERE Company IS NULL OR Company = ''
            ORDER BY LastName, FirstName
        """
        return self.execute_raw(query)

    def email_exists(self, email: str, exclude_customer_id: Optional[int] = None) -> bool:
        """
        Check if an email already exists (useful for validation).

        Args:
            email: Email to check
            exclude_customer_id: Optional customer ID to exclude from check
                                (useful when updating existing customer)

        Returns:
            True if email exists, False otherwise

        Example:
            >>> # Check if email exists
            >>> if repo.email_exists('test@example.com'):
            ...     print("Email already in use")
            >>>
            >>> # Check if email exists for other customers
            >>> if repo.email_exists('test@example.com', exclude_customer_id=5):
            ...     print("Email used by another customer")
        """
        if exclude_customer_id:
            query = """
                SELECT CASE WHEN EXISTS (
                    SELECT 1 FROM dbo.Customer
                    WHERE Email = ? AND CustomerId != ?
                ) THEN 1 ELSE 0 END
            """
            row = self._connection.execute_query(query, (email, exclude_customer_id), fetch='one')
        else:
            return self.exists(Email=email)

        return bool(row[0]) if row else False
