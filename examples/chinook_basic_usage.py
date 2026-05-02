"""
Basic usage example for Python-SQLServer framework.
This example demonstrates the simplest way to use the framework.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.core import ConnectionPool, get_logger
from src.database.connection import DatabaseConnection
from src.repositories.chinook_customer_repository import CustomerRepository
from src.models.chinook_customer import Customer


def main():
    # Configure logging
    from src.core.logger import DatabaseLogger
    DatabaseLogger.configure(log_level=settings.LOG_LEVEL, log_file=settings.LOG_FILE)

    logger = get_logger(__name__)
    logger.info("=== Basic Usage Example ===")

    # Step 1: Initialize connection pool (do this once at application startup)
    logger.info("Initializing connection pool...")
    pool = ConnectionPool()
    pool.initialize(
        config=settings.get_db_config(),
        min_size=settings.POOL_MIN_SIZE,
        max_size=settings.POOL_MAX_SIZE,
        timeout=settings.POOL_TIMEOUT
    )

    # Step 2: Create database connection
    db = DatabaseConnection()

    # Step 3: Create repository
    customer_repo = CustomerRepository(db, Customer)

    # Step 4: Find a customer by ID
    logger.info("\n--- Finding customer by ID [first 10] ---")

    for i in range(11): 

        customer = customer_repo.find_by_id(i)
        if customer:
            print(f"\nFound customer[{i}]:\t {customer.full_name}")
            print(f"Email [{i}]:\t\t {customer.Email}")
            print(f"Country[{i}]:\t\t {customer.Country}")
        else:
            print("Customer not found")

    # Step 5: Find all customers (with limit)
    print("\n")
    logger.info("\n--- Finding first 5 customers ---")
    customers = customer_repo.find_all(limit=5)
    print(f"\nFound {len(customers)} customers:")
    for c in customers:
        print(f"  - {c.CustomerId}: {c.full_name} ({c.Email})")

    # Step 6: Find customers by country
    print("\n")
    logger.info("\n--- Finding customers in USA ---")
    usa_customers = customer_repo.find_by_country('USA')
    print(f"\nFound {len(usa_customers)} customers in USA:")
    for c in usa_customers[:10]:  # Show first 3
        print(f"  - {c.full_name} from {c.City}, {c.State}")

    # Step 7: Count total customers
    print("\n")
    logger.info("\n--- Counting customers ---")
    total = customer_repo.count()
    print(f"\nTotal customers in database: {total}")

    # Step 8: Check if email exists
    print("\n")
    logger.info("\n--- Checking if email exists ---")
    test_email = "luisrojas@yahoo.cl"
    if customer_repo.email_exists(test_email):
        print(f"Email {test_email} exists in database")
    else:
        print(f"Email {test_email} not found")

    # Step 9: Show pool statistics
    print("\n")
    logger.info("\n--- Connection pool statistics ---")
    stats = pool.get_pool_stats()
    print(f"\nConnection Pool Stats:")
    print(f"  Total connections: {stats['total_connections']}")
    print(f"  Available: {stats['available']}")
    print(f"  In use: {stats['in_use']}")
    print(f"  Max size: {stats['max_size']}")

    # Cleanup
    logger.info("\n=== Example completed ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
