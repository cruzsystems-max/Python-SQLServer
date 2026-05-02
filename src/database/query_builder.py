"""
SQL query builder with parameterization to prevent SQL injection.

Generates safe, parameterized queries for CRUD operations.
All queries use placeholders (?) to prevent SQL injection attacks.
"""

from typing import List, Dict, Any, Optional, Tuple


class QueryBuilder:
    """
    SQL query builder with parameterization.

    This class provides static methods to build safe SQL queries with
    parameter placeholders, preventing SQL injection attacks.

    All methods return a tuple of (query_string, parameters_tuple).

    Example:
        >>> query, params = QueryBuilder.build_select(
        ...     table="dbo.Customer",
        ...     where={'Country': 'USA'},
        ...     limit=10
        ... )
        >>> print(query)
        'SELECT * FROM dbo.Customer WHERE Country = ? ORDER BY ... OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY'
        >>> print(params)
        ('USA',)
    """

    @staticmethod
    def build_select(
        table: str,
        columns: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> Tuple[str, Tuple]:
        """
        Build a SELECT query with parameters.

        Args:
            table: Table name (can include schema, e.g., "dbo.Customer")
            columns: List of column names (None for SELECT *)
            where: Dictionary of column=value conditions (AND logic)
            order_by: Column name(s) for ORDER BY (e.g., "CustomerId DESC")
            limit: Maximum number of rows to return
            offset: Number of rows to skip (for pagination)

        Returns:
            Tuple of (query_string, parameters_tuple)

        Example:
            >>> query, params = QueryBuilder.build_select(
            ...     table="dbo.Customer",
            ...     columns=["CustomerId", "FirstName", "Email"],
            ...     where={'Country': 'USA', 'State': 'CA'},
            ...     order_by="CustomerId",
            ...     limit=10,
            ...     offset=0
            ... )
        """
        # SELECT clause
        if columns:
            columns_str = ', '.join(columns)
        else:
            columns_str = '*'

        query = f"SELECT {columns_str} FROM {table}"
        params: List[Any] = []

        # WHERE clause
        if where:
            where_clause, where_params = QueryBuilder._build_where_clause(where)
            query += f" {where_clause}"
            params.extend(where_params)

        # ORDER BY clause (required for OFFSET/FETCH in SQL Server)
        if limit is not None or offset > 0:
            if not order_by:
                # Default order by first column if not specified
                # (SQL Server requires ORDER BY for OFFSET/FETCH)
                order_by = "1"  # Order by first column

        if order_by:
            query += f" ORDER BY {order_by}"

        # OFFSET/FETCH (SQL Server pagination)
        if limit is not None or offset > 0:
            query += f" OFFSET {offset} ROWS"
            if limit is not None:
                query += f" FETCH NEXT {limit} ROWS ONLY"

        return query, tuple(params)

    @staticmethod
    def build_insert(
        table: str,
        data: Dict[str, Any],
        return_identity: bool = True
    ) -> Tuple[str, Tuple]:
        """
        Build an INSERT query with parameters.

        Args:
            table: Table name
            data: Dictionary of column=value pairs to insert
            return_identity: If True, adds OUTPUT INSERTED.* to return the inserted row

        Returns:
            Tuple of (query_string, parameters_tuple)

        Example:
            >>> query, params = QueryBuilder.build_insert(
            ...     table="dbo.Customer",
            ...     data={
            ...         'FirstName': 'John',
            ...         'LastName': 'Doe',
            ...         'Email': 'john@example.com'
            ...     }
            ... )
        """
        if not data:
            raise ValueError("Cannot build INSERT query with empty data")

        columns = list(data.keys())
        placeholders = ', '.join(['?' for _ in columns])
        column_list = ', '.join(columns)

        if return_identity:
            # SQL Server syntax to return inserted row
            query = (
                f"INSERT INTO {table} ({column_list}) "
                f"OUTPUT INSERTED.* "
                f"VALUES ({placeholders})"
            )
        else:
            query = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"

        params = tuple(data.values())

        return query, params

    @staticmethod
    def build_update(
        table: str,
        data: Dict[str, Any],
        where: Dict[str, Any],
        return_updated: bool = True
    ) -> Tuple[str, Tuple]:
        """
        Build an UPDATE query with parameters.

        Args:
            table: Table name
            data: Dictionary of column=value pairs to update
            where: Dictionary of column=value conditions for WHERE clause
            return_updated: If True, adds OUTPUT INSERTED.* to return the updated row

        Returns:
            Tuple of (query_string, parameters_tuple)

        Raises:
            ValueError: If data or where is empty

        Example:
            >>> query, params = QueryBuilder.build_update(
            ...     table="dbo.Customer",
            ...     data={'Email': 'newemail@example.com'},
            ...     where={'CustomerId': 123}
            ... )
        """
        if not data:
            raise ValueError("Cannot build UPDATE query with empty data")

        if not where:
            raise ValueError(
                "Cannot build UPDATE query without WHERE clause. "
                "This would update all rows. Use explicit where conditions."
            )

        # SET clause
        set_items = [f"{col} = ?" for col in data.keys()]
        set_clause = ', '.join(set_items)

        params: List[Any] = []
        params.extend(data.values())

        # WHERE clause
        where_clause, where_params = QueryBuilder._build_where_clause(where)
        params.extend(where_params)

        if return_updated:
            # SQL Server syntax to return updated row
            query = (
                f"UPDATE {table} "
                f"SET {set_clause} "
                f"OUTPUT INSERTED.* "
                f"{where_clause}"
            )
        else:
            query = f"UPDATE {table} SET {set_clause} {where_clause}"

        return query, tuple(params)

    @staticmethod
    def build_delete(
        table: str,
        where: Dict[str, Any]
    ) -> Tuple[str, Tuple]:
        """
        Build a DELETE query with parameters.

        Args:
            table: Table name
            where: Dictionary of column=value conditions for WHERE clause

        Returns:
            Tuple of (query_string, parameters_tuple)

        Raises:
            ValueError: If where is empty

        Example:
            >>> query, params = QueryBuilder.build_delete(
            ...     table="dbo.Customer",
            ...     where={'CustomerId': 123}
            ... )

        Warning:
            Always provide a WHERE clause. This method raises ValueError
            if where is empty to prevent accidental deletion of all rows.
        """
        if not where:
            raise ValueError(
                "Cannot build DELETE query without WHERE clause. "
                "This would delete all rows. Use explicit where conditions."
            )

        where_clause, where_params = QueryBuilder._build_where_clause(where)

        query = f"DELETE FROM {table} {where_clause}"

        return query, where_params

    @staticmethod
    def build_count(
        table: str,
        where: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Tuple]:
        """
        Build a COUNT query.

        Args:
            table: Table name
            where: Optional dictionary of conditions

        Returns:
            Tuple of (query_string, parameters_tuple)

        Example:
            >>> query, params = QueryBuilder.build_count(
            ...     table="dbo.Customer",
            ...     where={'Country': 'USA'}
            ... )
        """
        query = f"SELECT COUNT(*) FROM {table}"
        params: List[Any] = []

        if where:
            where_clause, where_params = QueryBuilder._build_where_clause(where)
            query += f" {where_clause}"
            params.extend(where_params)

        return query, tuple(params)

    @staticmethod
    def build_exists(
        table: str,
        where: Dict[str, Any]
    ) -> Tuple[str, Tuple]:
        """
        Build an EXISTS query.

        Args:
            table: Table name
            where: Dictionary of conditions

        Returns:
            Tuple of (query_string, parameters_tuple)

        Example:
            >>> query, params = QueryBuilder.build_exists(
            ...     table="dbo.Customer",
            ...     where={'Email': 'john@example.com'}
            ... )
        """
        where_clause, where_params = QueryBuilder._build_where_clause(where)

        query = f"SELECT CASE WHEN EXISTS (SELECT 1 FROM {table} {where_clause}) THEN 1 ELSE 0 END"

        return query, where_params

    @staticmethod
    def _build_where_clause(where: Dict[str, Any]) -> Tuple[str, Tuple]:
        """
        Build WHERE clause with parameters.

        Args:
            where: Dictionary of column=value conditions

        Returns:
            Tuple of (where_clause_string, parameters_tuple)

        Note:
            - Joins multiple conditions with AND
            - Uses = for equality
            - For None values, uses IS NULL instead of = ?
            - For lists/tuples, uses IN operator

        Example:
            >>> clause, params = QueryBuilder._build_where_clause({
            ...     'Country': 'USA',
            ...     'State': 'CA',
            ...     'Active': True
            ... })
            >>> print(clause)
            'WHERE Country = ? AND State = ? AND Active = ?'
            >>> print(params)
            ('USA', 'CA', True)
        """
        if not where:
            return "", ()

        conditions = []
        params: List[Any] = []

        for key, value in where.items():
            if value is None:
                # Use IS NULL for None values
                conditions.append(f"{key} IS NULL")
            elif isinstance(value, (list, tuple)):
                # Use IN for lists/tuples
                placeholders = ', '.join(['?' for _ in value])
                conditions.append(f"{key} IN ({placeholders})")
                params.extend(value)
            else:
                # Regular equality
                conditions.append(f"{key} = ?")
                params.append(value)

        where_clause = " AND ".join(conditions)

        return f"WHERE {where_clause}", tuple(params)
