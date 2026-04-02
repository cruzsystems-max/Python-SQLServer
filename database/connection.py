import pyodbc
from config.db_config import DB_CONFIG

class DatabaseConnection:
    def __init__(self):
        self.conn = None
        self.cursor = None

    # Create a connection to the database
    def connect(self):
        try:
            conn_str = (
                f"DRIVER={{{DB_CONFIG['driver']}}};"
                f"SERVER={DB_CONFIG['server']};"
                f"DATABASE={DB_CONFIG['database']};"
                f"UID={DB_CONFIG['username']};"
                f"PWD={DB_CONFIG['password']};"
                "TrustServerCertificate=yes;"
            )
            self.conn = pyodbc.connect(conn_str)
            print("Successfully connected to the database")
            return self.conn
        except Exception as e:
            print("Failed to connect to the database")
            raise Exception(f"Error connecting to the database: {e}")

    # Get a cursor for executing queries
    def get_cursor(self):
        if not self.conn:
            self.connect()
        self.cursor = self.conn.cursor()
        return self.cursor

    # Execute a query (INSERT, UPDATE, DELETE, SELECT)
    def execute(self, query, params=None):
        try:
            cursor = self.get_cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor
        except Exception as e:
            self.rollback()
            raise Exception(f"Error executing query: {e}")

    # Fetch multiple records
    def fetch_all(self, query, params=None):
        cursor = self.execute(query, params)
        return cursor.fetchall()

    # Fetch a single record
    def fetch_one(self, query, params=None):
        cursor = self.execute(query, params)
        return cursor.fetchone()

    # Insert / Update / Delete with automatic commit
    def execute_commit(self, query, params=None):
        try:
            cursor = self.execute(query, params)
            self.conn.commit()
            return cursor.rowcount
        except Exception as e:
            self.rollback()
            raise e

    # Manual transactions
    def begin(self):
        if self.conn:
            self.conn.autocommit = False

    def commit(self):
        if self.conn:
            self.conn.commit()

    def rollback(self):
        if self.conn:
            self.conn.rollback()

    # Close cursor
    def close_cursor(self):
        if self.cursor:
            self.cursor.close()

    # Close connection
    def close(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            print("the connection is closed")
        except Exception as e:
            print(f"Error closing the connection: {e}")

    # Context manager support (use with "with")
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()