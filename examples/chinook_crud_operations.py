"""
CRUD operations example - Read and Update operations.

This example demonstrates READ and UPDATE operations using the repository pattern.
Note: CREATE operations are commented out because the Chinook database Customer table
does not have IDENTITY/AUTO_INCREMENT on CustomerId.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.core import ConnectionPool
from src.database.connection import DatabaseConnection
from src.repositories.chinook_customer_repository import CustomerRepository
from src.models.chinook_customer import Customer
from src.core.exceptions import ValidationError, RepositoryError


def main():
    print("=== CRUD Operations Example ===\n")

    # Initialize connection pool
    pool = ConnectionPool()
    pool.initialize(
        config=settings.get_db_config(),
        min_size=settings.POOL_MIN_SIZE,
        max_size=settings.POOL_MAX_SIZE,
        timeout=settings.POOL_TIMEOUT
    )

    # Create repository
    db = DatabaseConnection()
    customer_repo = CustomerRepository(db, Customer)

    # ==================== READ ====================
    print("--- READ: Finding customer by ID ---")

    customer = customer_repo.find_by_id(1)
    if customer:
        print(f"[OK] Found customer: {customer.full_name}")
        print(f"     Email: {customer.Email}")
        print(f"     Address: {customer.full_address}")
    else:
        print("[ERROR] Customer not found")
        return

    # Read by email
    print("\n--- READ: Finding customer by email ---")
    customer_by_email = customer_repo.find_by_email(customer.Email)
    if customer_by_email:
        print(f"[OK] Found customer: {customer_by_email.full_name}")

    # Read multiple
    print("\n--- READ: Finding customers in Brazil ---")
    brazil_customers = customer_repo.find_by(Country="Brazil")
    print(f"[OK] Found {len(brazil_customers)} customers in Brazil")
    for c in brazil_customers[:3]:  # Show first 3
        print(f"     - {c.full_name} ({c.City})")

    # Count customers
    print("\n--- READ: Counting customers ---")
    total = customer_repo.count()
    print(f"[OK] Total customers: {total}")

    # Search by name
    print("\n--- READ: Searching for customers with 'Luis' in name ---")
    luis_customers = customer_repo.search_by_name("Luis")
    print(f"[OK] Found {len(luis_customers)} matches")
    for c in luis_customers:
        print(f"     - {c.full_name} ({c.Email})")

    # Find by country
    print("\n--- READ: Finding customers in USA ---")
    usa_customers = customer_repo.find_by_country("USA")
    print(f"[OK] Found {len(usa_customers)} customers in USA")
    for c in usa_customers[:3]:
        print(f"     - {c.full_name} from {c.City}, {c.State}")

    # Pagination
    print("\n--- READ: Pagination example ---")
    page1 = customer_repo.find_all(limit=5, offset=0)
    print(f"[OK] Page 1 (first 5 customers):")
    for c in page1:
        print(f"     {c.CustomerId}. {c.full_name}")

    page2 = customer_repo.find_all(limit=5, offset=5)
    print(f"[OK] Page 2 (next 5 customers):")
    for c in page2:
        print(f"     {c.CustomerId}. {c.full_name}")

    # Check if email exists
    print("\n--- READ: Checking if email exists ---")
    email_to_check = "luisg@embraer.com.br"
    exists = customer_repo.email_exists(email_to_check)
    if exists:
        print(f"[OK] Email '{email_to_check}' exists in database")
    else:
        print(f"[INFO] Email '{email_to_check}' not found")

    # ==================== UPDATE ====================
    print("\n--- UPDATE: Demonstrating update (will be rolled back) ---")
    print("[INFO] This demonstrates UPDATE but doesn't actually change the database")

    # Get a customer to update
    test_customer = customer_repo.find_by_id(1)
    if test_customer:
        original_phone = test_customer.Phone
        print(f"[INFO] Original phone: {original_phone}")

        # Note: Commented out actual update to preserve database
        # Uncomment these lines to actually test UPDATE:
        #
        # test_customer.Phone = "+1-555-TEST"
        # try:
        #     updated = customer_repo.update(test_customer)
        #     print(f"[OK] Updated phone to: {updated.Phone}")
        #
        #     # Restore original
        #     test_customer.Phone = original_phone
        #     customer_repo.update(test_customer)
        #     print(f"[OK] Restored phone to: {original_phone}")
        # except RepositoryError as e:
        #     print(f"[ERROR] Update failed: {e}")

        print("[INFO] To test UPDATE, uncomment the code in the example")

    # ==================== VALIDATION ====================
    print("\n--- VALIDATION: Testing model validation ---")

    try:
        invalid_customer = Customer(
            CustomerId=999,
            FirstName="",  # Invalid: empty name
            LastName="Test",
            Email="invalid-email"  # Invalid: bad format
        )
        invalid_customer.validate()
    except ValidationError as e:
        print(f"[OK] Validation correctly caught error: {e}")

    # ==================== STATISTICS ====================
    print("\n--- STATISTICS: Connection pool stats ---")
    stats = pool.get_pool_stats()
    print(f"[OK] Pool statistics:")
    print(f"     Total connections: {stats['total_connections']}")
    print(f"     Available: {stats['available']}")
    print(f"     In use: {stats['in_use']}")
    print(f"     Max size: {stats['max_size']}")

    print("\n=== Example Completed Successfully ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
