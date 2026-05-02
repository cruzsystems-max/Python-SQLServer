"""
Generic repository with automated CRUD operations.

Implements the Repository pattern with generic CRUD operations for any table.
Subclass this to create specific repositories for your tables.
"""

from typing import TypeVar, Generic, List, Optional, Dict, Any, Type
from abc import ABC, abstractmethod
from ..core.logger import get_logger
from ..core.exceptions import RepositoryError, ValidationError
from ..models.base_model import BaseModel
from .connection import DatabaseConnection
from .query_builder import QueryBuilder


T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T], ABC):
    """
    Generic repository with automated CRUD operations.

    This class provides generic CRUD operations for any table. Subclass it
    and specify the table name and primary key to get automatic CRUD functionality.

    Type parameter T should be a BaseModel subclass.

    Example:
        >>> from src.database.base_repository import BaseRepository
        >>> from src.models.customer import Customer
        >>>
        >>> class CustomerRepository(BaseRepository[Customer]):
        ...     @property
        ...     def table_name(self) -> str:
        ...         return "dbo.Customer"
        ...
        ...     @property
        ...     def primary_key(self) -> str:
        ...         return "CustomerId"
        >>>
        >>> repo = CustomerRepository(db_connection, Customer)
        >>> customer = repo.find_by_id(1)
        >>> all_customers = repo.find_all()
    """

    def __init__(self, connection: DatabaseConnection, model_class: Type[T]):
        """
        Initialize repository.

        Args:
            connection: Database connection instance
            model_class: The model class (must be a BaseModel subclass)

        Example:
            >>> db = DatabaseConnection()
            >>> repo = CustomerRepository(db, Customer)
        """
        self._connection = connection
        self._model_class = model_class
        self._logger = get_logger(self.__class__.__name__)

    @property
    @abstractmethod
    def table_name(self) -> str:
        """
        Return the table name for this repository.

        Must be implemented by subclasses.

        Returns:
            str: Table name (can include schema, e.g., "dbo.Customer")

        Example:
            >>> @property
            ... def table_name(self) -> str:
            ...     return "dbo.Customer"
        """
        pass

    @property
    @abstractmethod
    def primary_key(self) -> str:
        """
        Return the primary key column name.

        Must be implemented by subclasses.

        Returns:
            str: Primary key column name

        Example:
            >>> @property
            ... def primary_key(self) -> str:
            ...     return "CustomerId"
        """
        pass

    # ==================== CRUD Operations ====================

    def find_by_id(self, id_value: Any) -> Optional[T]:
        """
        Find a record by primary key.

        Args:
            id_value: Primary key value

        Returns:
            Model instance or None if not found

        Example:
            >>> customer = repo.find_by_id(123)
            >>> if customer:
            ...     print(customer.FirstName)
        """
        self._logger.debug(f"Finding {self._model_class.__name__} by id: {id_value}")

        try:
            query, params = QueryBuilder.build_select(
                table=self.table_name,
                where={self.primary_key: id_value}
            )

            row = self._connection.execute_query(query, params, fetch='one')

            if row:
                model = self._model_class.from_row(row)
                self._logger.debug(f"Found {self._model_class.__name__}: {model}")
                return model

            self._logger.debug(f"{self._model_class.__name__} not found")
            return None

        except Exception as e:
            self._logger.error(f"Error finding by id: {e}")
            raise RepositoryError(f"Failed to find by id: {id_value}", original_error=e)

    def find_all(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: Optional[str] = None
    ) -> List[T]:
        """
        Retrieve all records with optional pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: Column(s) to order by (e.g., "CustomerId DESC")

        Returns:
            List of model instances

        Example:
            >>> # Get first 10 customers
            >>> customers = repo.find_all(limit=10)
            >>>
            >>> # Get next 10 customers (page 2)
            >>> customers_page2 = repo.find_all(limit=10, offset=10)
            >>>
            >>> # Get customers ordered by name
            >>> customers = repo.find_all(order_by="FirstName, LastName")
        """
        self._logger.debug(
            f"Finding all {self._model_class.__name__}s (limit={limit}, offset={offset})"
        )

        try:
            query, params = QueryBuilder.build_select(
                table=self.table_name,
                limit=limit,
                offset=offset,
                order_by=order_by or self.primary_key
            )

            rows = self._connection.execute_query(query, params, fetch='all')
            models = self._model_class.from_rows(rows)

            self._logger.debug(f"Found {len(models)} {self._model_class.__name__}s")
            return models

        except Exception as e:
            self._logger.error(f"Error finding all: {e}")
            raise RepositoryError("Failed to find all records", original_error=e)

    def find_by(self, **criteria) -> List[T]:
        """
        Find records matching criteria.

        Args:
            **criteria: Column=value pairs for WHERE clause

        Returns:
            List of model instances matching criteria

        Example:
            >>> # Find customers in USA
            >>> usa_customers = repo.find_by(Country='USA')
            >>>
            >>> # Find customers in California, USA
            >>> ca_customers = repo.find_by(Country='USA', State='CA')
        """
        self._logger.debug(
            f"Finding {self._model_class.__name__}s by criteria: {criteria}"
        )

        try:
            query, params = QueryBuilder.build_select(
                table=self.table_name,
                where=criteria,
                order_by=self.primary_key
            )

            rows = self._connection.execute_query(query, params, fetch='all')
            models = self._model_class.from_rows(rows)

            self._logger.debug(
                f"Found {len(models)} {self._model_class.__name__}s matching criteria"
            )
            return models

        except Exception as e:
            self._logger.error(f"Error finding by criteria: {e}")
            raise RepositoryError(
                f"Failed to find by criteria: {criteria}",
                original_error=e
            )

    def find_one_by(self, **criteria) -> Optional[T]:
        """
        Find single record matching criteria.

        Args:
            **criteria: Column=value pairs for WHERE clause

        Returns:
            Model instance or None if not found

        Example:
            >>> # Find customer by email
            >>> customer = repo.find_one_by(Email='john@example.com')
        """
        results = self.find_by(**criteria)
        return results[0] if results else None

    def insert(self, model: T) -> T:
        """
        Insert a new record.

        Args:
            model: Model instance to insert

        Returns:
            Model instance with updated fields (e.g., auto-generated ID)

        Raises:
            ValidationError: If model validation fails
            RepositoryError: If insert fails

        Example:
            >>> new_customer = Customer(
            ...     CustomerId=0,  # Will be auto-generated
            ...     FirstName="John",
            ...     LastName="Doe",
            ...     Email="john@example.com"
            ... )
            >>> saved_customer = repo.insert(new_customer)
            >>> print(saved_customer.CustomerId)  # Auto-generated ID
        """
        self._logger.debug(f"Inserting {self._model_class.__name__}: {model}")

        try:
            # Validate model
            self._validate_model(model)

            # Prepare data (exclude primary key if it's 0 or None - will be auto-generated)
            data = model.to_dict()
            pk_value = data.get(self.primary_key)

            if pk_value is None or pk_value == 0:
                # Remove primary key, let database generate it
                data.pop(self.primary_key, None)

            # Build and execute insert query
            query, params = QueryBuilder.build_insert(
                table=self.table_name,
                data=data,
                return_identity=True
            )

            row = self._connection.execute_query(query, params, fetch='one')

            if row:
                # Return updated model with generated values
                inserted_model = self._model_class.from_row(row)
                self._logger.info(
                    f"Inserted {self._model_class.__name__} with "
                    f"{self.primary_key}={getattr(inserted_model, self.primary_key)}"
                )
                return inserted_model
            else:
                raise RepositoryError("Insert succeeded but no row returned")

        except ValidationError:
            raise
        except Exception as e:
            self._logger.error(f"Error inserting {self._model_class.__name__}: {e}")
            raise RepositoryError(
                f"Failed to insert {self._model_class.__name__}",
                original_error=e
            )

    def update(self, model: T) -> T:
        """
        Update an existing record.

        Args:
            model: Model instance with updated values

        Returns:
            Updated model instance

        Raises:
            ValidationError: If model validation fails
            RepositoryError: If update fails

        Example:
            >>> customer = repo.find_by_id(123)
            >>> customer.Email = "newemail@example.com"
            >>> updated_customer = repo.update(customer)
        """
        self._logger.debug(f"Updating {self._model_class.__name__}: {model}")

        try:
            # Validate model
            self._validate_model(model)

            # Prepare data
            data = model.to_dict()
            pk_value = data.pop(self.primary_key)

            if not pk_value:
                raise ValidationError(
                    f"Cannot update without {self.primary_key}",
                    field=self.primary_key
                )

            # Build and execute update query
            query, params = QueryBuilder.build_update(
                table=self.table_name,
                data=data,
                where={self.primary_key: pk_value},
                return_updated=True
            )

            row = self._connection.execute_query(query, params, fetch='one')

            if row:
                updated_model = self._model_class.from_row(row)
                self._logger.info(
                    f"Updated {self._model_class.__name__} with "
                    f"{self.primary_key}={pk_value}"
                )
                return updated_model
            else:
                raise RepositoryError(f"No record found with {self.primary_key}={pk_value}")

        except ValidationError:
            raise
        except Exception as e:
            self._logger.error(f"Error updating {self._model_class.__name__}: {e}")
            raise RepositoryError(
                f"Failed to update {self._model_class.__name__}",
                original_error=e
            )

    def delete(self, id_value: Any) -> bool:
        """
        Delete a record by primary key.

        Args:
            id_value: Primary key value

        Returns:
            True if deleted, False if not found

        Example:
            >>> success = repo.delete(123)
            >>> if success:
            ...     print("Customer deleted")
        """
        self._logger.debug(
            f"Deleting {self._model_class.__name__} with {self.primary_key}={id_value}"
        )

        try:
            query, params = QueryBuilder.build_delete(
                table=self.table_name,
                where={self.primary_key: id_value}
            )

            affected = self._connection.execute_query(query, params, fetch='none')

            if affected > 0:
                self._logger.info(
                    f"Deleted {self._model_class.__name__} with {self.primary_key}={id_value}"
                )
                return True

            self._logger.debug(f"No record found with {self.primary_key}={id_value}")
            return False

        except Exception as e:
            self._logger.error(f"Error deleting: {e}")
            raise RepositoryError(
                f"Failed to delete record with {self.primary_key}={id_value}",
                original_error=e
            )

    def delete_by(self, **criteria) -> int:
        """
        Delete records matching criteria.

        Args:
            **criteria: Column=value pairs for WHERE clause

        Returns:
            Number of deleted records

        Example:
            >>> # Delete all customers in a specific country
            >>> deleted = repo.delete_by(Country='TestCountry')
            >>> print(f"Deleted {deleted} customers")
        """
        self._logger.debug(
            f"Deleting {self._model_class.__name__}s by criteria: {criteria}"
        )

        try:
            query, params = QueryBuilder.build_delete(
                table=self.table_name,
                where=criteria
            )

            affected = self._connection.execute_query(query, params, fetch='none')

            self._logger.info(f"Deleted {affected} {self._model_class.__name__}s")
            return affected

        except Exception as e:
            self._logger.error(f"Error deleting by criteria: {e}")
            raise RepositoryError(
                f"Failed to delete by criteria: {criteria}",
                original_error=e
            )

    def count(self, **criteria) -> int:
        """
        Count records matching criteria.

        Args:
            **criteria: Optional column=value pairs for WHERE clause

        Returns:
            Number of matching records

        Example:
            >>> total_customers = repo.count()
            >>> usa_customers = repo.count(Country='USA')
        """
        try:
            query, params = QueryBuilder.build_count(
                table=self.table_name,
                where=criteria if criteria else None
            )

            row = self._connection.execute_query(query, params, fetch='one')
            count = row[0] if row else 0

            self._logger.debug(f"Count: {count}")
            return count

        except Exception as e:
            self._logger.error(f"Error counting: {e}")
            raise RepositoryError("Failed to count records", original_error=e)

    def exists(self, **criteria) -> bool:
        """
        Check if records exist matching criteria.

        Args:
            **criteria: Column=value pairs for WHERE clause

        Returns:
            True if at least one record exists, False otherwise

        Example:
            >>> if repo.exists(Email='john@example.com'):
            ...     print("Email already exists")
        """
        try:
            query, params = QueryBuilder.build_exists(
                table=self.table_name,
                where=criteria
            )

            row = self._connection.execute_query(query, params, fetch='one')
            exists = bool(row[0]) if row else False

            self._logger.debug(f"Exists: {exists}")
            return exists

        except Exception as e:
            self._logger.error(f"Error checking exists: {e}")
            raise RepositoryError("Failed to check existence", original_error=e)

    # ==================== Bulk Operations ====================

    def bulk_insert(self, models: List[T]) -> int:
        """
        Insert multiple records in a transaction.

        Args:
            models: List of model instances to insert

        Returns:
            Number of inserted records

        Example:
            >>> customers = [
            ...     Customer(CustomerId=0, FirstName="John", LastName="Doe"),
            ...     Customer(CustomerId=0, FirstName="Jane", LastName="Smith")
            ... ]
            >>> inserted = repo.bulk_insert(customers)
        """
        if not models:
            return 0

        self._logger.debug(f"Bulk inserting {len(models)} {self._model_class.__name__}s")

        try:
            # Validate all models first
            for model in models:
                self._validate_model(model)

            # Prepare data
            first_data = models[0].to_dict()
            pk_value = first_data.get(self.primary_key)

            if pk_value is None or pk_value == 0:
                first_data.pop(self.primary_key, None)

            # Build query (without OUTPUT clause for bulk insert)
            query, _ = QueryBuilder.build_insert(
                table=self.table_name,
                data=first_data,
                return_identity=False
            )

            # Prepare all parameter sets
            params_list = []
            for model in models:
                data = model.to_dict()
                data.pop(self.primary_key, None)
                params_list.append(tuple(data.values()))

            # Execute bulk insert
            with self._connection.transaction():
                affected = self._connection.execute_many(query, params_list)

            self._logger.info(f"Bulk inserted {affected} {self._model_class.__name__}s")
            return affected

        except ValidationError:
            raise
        except Exception as e:
            self._logger.error(f"Error bulk inserting: {e}")
            raise RepositoryError("Failed to bulk insert", original_error=e)

    # ==================== Raw SQL Support ====================

    def execute_raw(self, query: str, params: Optional[tuple] = None) -> List[T]:
        """
        Execute raw SQL query and return models.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of model instances

        Example:
            >>> query = '''
            ...     SELECT * FROM dbo.Customer
            ...     WHERE FirstName LIKE ? OR LastName LIKE ?
            ... '''
            >>> customers = repo.execute_raw(query, ('%John%', '%John%'))
        """
        self._logger.debug(f"Executing raw query: {query[:100]}...")

        try:
            rows = self._connection.execute_query(query, params, fetch='all')
            models = self._model_class.from_rows(rows)

            self._logger.debug(f"Raw query returned {len(models)} rows")
            return models

        except Exception as e:
            self._logger.error(f"Error executing raw query: {e}")
            raise RepositoryError("Failed to execute raw query", original_error=e)

    # ==================== Helper Methods ====================

    def _validate_model(self, model: T) -> None:
        """
        Validate model before database operation.

        Args:
            model: Model instance to validate

        Raises:
            ValidationError: If validation fails
        """
        try:
            model.validate()
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Model validation failed: {str(e)}")
