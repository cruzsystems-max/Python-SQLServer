# Python-SQLServer Framework

Enterprise-level Object-Oriented Programming (OOP) framework for SQL Server automation with Python.

## Features

- **CRUD Automation**: Generic CRUD operations for any table without writing SQL manually
- **Connection Pooling**: Singleton pattern for efficient database connection management
- **Design Patterns**: Factory, Repository, and Singleton patterns implemented
- **Type Safety**: Full type hints throughout the codebase
- **Security**: Environment-based configuration, parameterized queries to prevent SQL injection
- **Professional Logging**: Structured logging with customizable levels
- **Transaction Management**: Context managers for automatic commit/rollback
- **Backward Compatible**: Legacy code continues to work

## Architecture

```
┌─────────────────────────────────────────┐
│       Application Layer                 │
│  (Your code, examples/)                 │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│      Repository Layer                   │
│  BaseRepository → CustomerRepository    │
│  (Generic CRUD + Custom Queries)        │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│      Database Layer                     │
│  DatabaseConnection + QueryBuilder      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│      Core Infrastructure                │
│  ConnectionPool + Factory + Exceptions  │
└─────────────────────────────────────────┘
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies:
- `pyodbc==5.3.0` - SQL Server connectivity
- `python-dotenv==1.0.0` - Environment variable management
- `numpy==2.2.6` - (existing dependency)
- `colorama==0.4.6` - Colored console output (Windows compatible)

### 2. Configure Environment

Copy the example environment file and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your database credentials:

```env
# Database Configuration
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_SERVER=localhost
DB_NAME=Chinook
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_TRUST_CERTIFICATE=yes

# Connection Pool Settings
POOL_MIN_SIZE=2
POOL_MAX_SIZE=10
POOL_TIMEOUT=30.0

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/database.log
```

### 3. Verify Setup

Run the basic example:

```bash
python examples/chinook_basic_usage.py
```

## Model/Repository Pattern

This framework uses the **Model/Repository Pattern** to organize data access:

- **Model**: A class representing one row from a database table (e.g., `Customer`, `Product`)
- **Repository**: A class with methods to access and manipulate data (e.g., `find_all()`, `find_by_id()`, `insert()`)

**Benefits:**
- Clean, readable code
- Centralized data access logic
- Easy to test and maintain
- Separation of concerns: data structure (Model) vs data access (Repository)

## Quick Start

### Basic Usage

```python
from config.settings import settings
from src.core import ConnectionPool
from src.database.connection import DatabaseConnection
from src.repositories.chinook_customer_repository import CustomerRepository
from src.models.chinook_customer import Customer

# Initialize connection pool (once at startup)
pool = ConnectionPool()
pool.initialize(settings.get_db_config())

# Create repository
db = DatabaseConnection()
customer_repo = CustomerRepository(db, Customer)

# Find customer by ID
customer = customer_repo.find_by_id(1)
print(f"Customer: {customer.full_name}")

# Find all customers (with pagination)
customers = customer_repo.find_all(limit=10)

# Find by criteria
usa_customers = customer_repo.find_by(Country='USA')
```

### CRUD Operations

```python
# CREATE
new_customer = Customer(
    CustomerId=0,  # Auto-generated
    FirstName="John",
    LastName="Doe",
    Email="john@example.com"
)
saved = customer_repo.insert(new_customer)

# READ
customer = customer_repo.find_by_id(saved.CustomerId)

# UPDATE
customer.Email = "newemail@example.com"
updated = customer_repo.update(customer)

# DELETE
customer_repo.delete(saved.CustomerId)
```

### Custom Queries

```python
# Use custom repository methods
customer = customer_repo.find_by_email('john@example.com')
usa_customers = customer_repo.find_by_country('USA')
results = customer_repo.search_by_name('John')

# Or raw SQL for complex queries
query = """
    SELECT * FROM dbo.Customer
    WHERE FirstName LIKE ? OR LastName LIKE ?
"""
customers = customer_repo.execute_raw(query, ('%John%', '%John%'))
```

### Transactions

```python
with db.transaction():
    customer1 = customer_repo.insert(new_customer1)
    customer2 = customer_repo.insert(new_customer2)
    # Automatically commits if no exception
    # Automatically rolls back on exception
```

### Creating Tables

```python
# Execute any SQL including DDL (CREATE, DROP, ALTER)
db = DatabaseConnection()

# Create table
db.execute_query("""
    CREATE TABLE dbo.Products (
        ProductID INT PRIMARY KEY IDENTITY(1,1),
        Name NVARCHAR(100) NOT NULL,
        Price DECIMAL(10,2)
    )
""")

# Drop table
db.execute_query("DROP TABLE dbo.Products")
```

## Creating Custom Repositories

### 1. Define Your Model

```python
from dataclasses import dataclass
from src.models.base_model import BaseModel
from src.core.exceptions import ValidationError

@dataclass
class YourModel(BaseModel):
    id: int
    name: str
    email: str

    def validate(self) -> None:
        if not self.name:
            raise ValidationError("Name is required")
        if '@' not in self.email:
            raise ValidationError("Invalid email")
```

### 2. Create Repository

```python
from src.database.base_repository import BaseRepository

class YourRepository(BaseRepository[YourModel]):
    @property
    def table_name(self) -> str:
        return "dbo.YourTable"

    @property
    def primary_key(self) -> str:
        return "id"

    # Add custom methods
    def find_by_name(self, name: str):
        return self.find_by(name=name)
```

### 3. Use It

```python
db = DatabaseConnection()
repo = YourRepository(db, YourModel)

# All generic CRUD methods available
item = repo.find_by_id(1)
all_items = repo.find_all()
repo.insert(new_item)
repo.update(item)
repo.delete(1)

# Plus your custom methods
items = repo.find_by_name("example")
```

## Examples

The `examples/` directory contains complete working examples using the Chinook database:

- **chinook_basic_usage.py**: Simple usage of the framework with Chinook database
- **chinook_crud_operations.py**: READ operations demonstration
- **chinook_repository_pattern.py**: Custom queries and repository pattern

Run any example:

```bash
python examples/chinook_basic_usage.py
python examples/chinook_crud_operations.py
python examples/chinook_repository_pattern.py
```

**Note:** These examples use the Chinook database as demonstration. The framework works with any SQL Server database.

## Project Structure

```
Python-SQLServer/
├── .env                    # Your credentials (gitignored)
├── .env.example            # Template for environment variables
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
├── README.md              # This file
│
├── config/                # Configuration
│   ├── __init__.py
│   └── settings.py        # Environment-based configuration
│
├── src/                   # Framework code
│   ├── __init__.py
│   │
│   ├── core/              # Core infrastructure
│   │   ├── __init__.py
│   │   ├── exceptions.py  # Custom exception hierarchy
│   │   ├── logger.py      # Colored logging system
│   │   ├── connection_pool.py  # Singleton pool
│   │   └── connection_factory.py  # Factory pattern
│   │
│   ├── database/          # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py       # Enhanced connection
│   │   ├── base_repository.py  # Generic CRUD
│   │   └── query_builder.py    # Safe query builder
│   │
│   ├── models/            # Domain models
│   │   ├── __init__.py
│   │   ├── base_model.py
│   │   └── chinook_customer.py    # Example model (Chinook DB)
│   │
│   ├── repositories/      # Data access layer
│   │   ├── __init__.py
│   │   └── chinook_customer_repository.py  # Example (Chinook DB)
│   │
│   └── utils/             # Utilities
│       ├── __init__.py
│       ├── validators.py
│       └── decorators.py
│
├── examples/              # Usage examples (Chinook database)
│   ├── __init__.py
│   ├── chinook_basic_usage.py
│   ├── chinook_crud_operations.py
│   └── chinook_repository_pattern.py
│
└── logs/                  # Log files (auto-created, gitignored)
```

## Key Improvements from v1.0

### Security
- ✅ Credentials in `.env` (not in code)
- ✅ Parameterized queries (SQL injection prevention)
- ✅ Input validation

### Performance
- ✅ Connection pooling (Singleton pattern)
- ✅ Efficient resource management
- ✅ No memory leaks (cursors properly closed)

### Code Quality
- ✅ Type hints throughout
- ✅ Custom exception hierarchy
- ✅ Professional logging (not print statements)
- ✅ Comprehensive docstrings
- ✅ Design patterns (Factory, Repository, Singleton)

### Developer Experience
- ✅ CRUD automation (no manual SQL for basic operations)
- ✅ Easy to extend (create custom repositories)
- ✅ Clear error messages
- ✅ Transaction support
- ✅ Full backward compatibility

## Migration from v1.0

Your existing code continues to work without changes:

```python
# Old code (still works)
from database.connection import DatabaseConnection

db = DatabaseConnection()
db.connect()
results = db.fetch_all("SELECT * FROM dbo.Customer")
db.close()
```

Migrate gradually to the new API:

```python
# New code (recommended)
from src.database.connection import DatabaseConnection
from src.repositories.chinook_customer_repository import CustomerRepository
from src.models.chinook_customer import Customer

db = DatabaseConnection()  # Uses connection pool automatically
repo = CustomerRepository(db, Customer)
customers = repo.find_all()  # No SQL needed!
```

## Design Patterns Used

### 1. Singleton Pattern
**Where**: `ConnectionPool`
**Why**: Ensure only one connection pool exists, managing resources efficiently.

### 2. Factory Pattern
**Where**: `ConnectionFactory`
**Why**: Centralize connection creation, support different connection types.

### 3. Repository Pattern
**Where**: `BaseRepository`, `CustomerRepository`
**Why**: Abstract data access, provide generic CRUD, separate business logic from database logic.

## Best Practices

### 1. Always Use Connection Pool

```python
# At application startup (once)
pool = ConnectionPool()
pool.initialize(settings.get_db_config())

# Then use DatabaseConnection (uses pool automatically)
db = DatabaseConnection()
```

### 2. Use Context Managers for Transactions

```python
with db.transaction():
    repo.insert(item1)
    repo.update(item2)
    # Auto-commit on success, auto-rollback on exception
```

### 3. Validate Models

```python
@dataclass
class Customer(BaseModel):
    name: str
    email: str

    def validate(self) -> None:
        if not self.name:
            raise ValidationError("Name required")
```

### 4. Use Type Hints

```python
def find_customer(customer_id: int) -> Optional[Customer]:
    return customer_repo.find_by_id(customer_id)
```

## Troubleshooting

### Connection Errors

```python
# Check your .env file
# Ensure SQL Server is running
# Verify ODBC driver is installed: odbcinst -q -d
```

### Import Errors

```python
# Ensure you're in the project root directory
# Check that __init__.py files exist in all packages
```

### Pool Exhausted

```python
# Increase pool size in .env
POOL_MAX_SIZE=20

# Or decrease timeout
POOL_TIMEOUT=60.0
```

## Contributing

This is a professional framework. To add features:

1. Follow existing patterns (Repository, Factory, etc.)
2. Add type hints
3. Include docstrings
4. Handle exceptions properly
5. Add logging
6. Write examples

## License

This project is for educational and professional use.

## Version History

### v2.0.0 (Current)
- Enterprise architecture with design patterns
- CRUD automation
- Connection pooling
- Security improvements (env variables, parameterized queries)
- Professional logging
- Type hints throughout
- Backward compatible with v1.0

### v1.0.0
- Basic DatabaseConnection class
- Manual SQL queries
- Hardcoded credentials
- Print-based logging

---

Built with professional OOP practices for SQL Server automation.
