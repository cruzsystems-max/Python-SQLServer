from database.connection import DatabaseConnection

# Create a database connection object
db = DatabaseConnection()
db.connect()

# ---------------------------
# 1. List all existing tables
# ---------------------------
tables_query = """
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_SCHEMA, TABLE_NAME
"""
tables = db.fetch_all(tables_query)
print("\nExisting tables in the database:")
for schema, table in tables:
    print(f"{schema}.{table}")

# ---------------------------
# 2. Work with an existing table: dbo.Customer
# ---------------------------

cursor = db.execute("SELECT COUNT(*) FROM dbo.Customer")
count = cursor.fetchone()[0]
print(f"\nTotal number of customers: {count}")
#---------------------------


select_query = "SELECT CustomerId, FirstName, LastName, Email FROM dbo.Customer"
customers = db.fetch_all(select_query)
print("\nFirst 5 customers:")
for customer in customers[:5]:
    print(customer)

table = 'Customer'

# List columns with their data types
columns = db.fetch_all(
    "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=? ORDER BY ORDINAL_POSITION",
    (table,)
)

print(f"\nColumns of dbo.{table}:")
for col, dtype in columns:
    print(f"{col} ({dtype})")

# Close the connection
db.close()
