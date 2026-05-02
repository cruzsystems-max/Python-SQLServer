"""
Repository pattern example with custom queries.

This example demonstrates how to use custom query methods in repositories.
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


def main():
    print("=== Repository Pattern Example ===\n")

    # Initialize
    pool = ConnectionPool()
    pool.initialize(settings.get_db_config())

    db = DatabaseConnection()
    customer_repo = CustomerRepository(db, Customer)

    # ==================== Search by Name ====================
    print("--- Search customers by name ---")

    search_term = "Luis"
    customers = customer_repo.search_by_name(search_term)
    print(f"Customers with '{search_term}' in name:")
    for c in customers[:5]:  # Show first 5
        print(f"  - {c.full_name} ({c.Email})")

    # ==================== Count by Country ====================
    print("\n--- Customer count by country ---")

    country_counts = customer_repo.count_by_country()
    print("Top 10 countries by customer count:")
    for country, count in country_counts[:10]:
        country_name = country if country else "(No country)"
        print(f"  {country_name}: {count} customers")

    # ==================== Find by City ====================
    print("\n--- Customers in specific city ---")

    city = "São Paulo"
    city_customers = customer_repo.find_by_city(city)
    print(f"Customers in {city}: {len(city_customers)}")
    for c in city_customers:
        print(f"  - {c.full_name}")

    # ==================== Customers with Support Rep ====================
    print("\n--- Customers with support representative ---")

    support_rep_id = 3
    rep_customers = customer_repo.find_customers_with_support_rep(support_rep_id)
    print(f"Customers with support rep {support_rep_id}: {len(rep_customers)}")

    # ==================== Customers without Company ====================
    print("\n--- Personal customers (no company) ---")

    personal_customers = customer_repo.find_customers_without_company()
    print(f"Personal customers (no company): {len(personal_customers)}")
    for c in personal_customers[:5]:
        print(f"  - {c.full_name} from {c.City}, {c.Country}")

    # ==================== Using Generic CRUD ====================
    print("\n--- Using generic CRUD methods ---")

    # Find by multiple criteria
    print("\nCustomers in USA, California:")
    ca_customers = customer_repo.find_by(Country="USA", State="CA")
    for c in ca_customers:
        print(f"  - {c.full_name} from {c.City}")

    # Count with criteria
    usa_count = customer_repo.count(Country="USA")
    print(f"\nTotal USA customers: {usa_count}")

    # Check existence
    test_email = "fralston@gmail.com"
    exists = customer_repo.email_exists(test_email)
    print(f"\nEmail '{test_email}' exists: {exists}")

    # ==================== Pagination Example ====================
    print("\n--- Pagination example ---")

    page_size = 5
    page = 1  # First page

    offset = (page - 1) * page_size
    page_customers = customer_repo.find_all(
        limit=page_size,
        offset=offset,
        order_by="FirstName, LastName"
    )

    total = customer_repo.count()
    total_pages = (total + page_size - 1) // page_size

    print(f"Page {page} of {total_pages} (showing {len(page_customers)} customers):")
    for c in page_customers:
        print(f"  {c.CustomerId}. {c.full_name}")

    # ==================== Transaction Example ====================
    print("\n--- Transaction example ---")
    print("[INFO] Transaction example commented out (requires INSERT)")
    print("[INFO] To test transactions, uncomment the code below")

    # Note: Commented out because Chinook Customer table doesn't have AUTO_INCREMENT
    # Uncomment to test transactions:
    #
    # try:
    #     with db.transaction():
    #         # Create test customer
    #         test_customer = Customer(
    #             CustomerId=0,
    #             FirstName="Transaction",
    #             LastName="Test",
    #             Email="transaction@test.com",
    #             Country="TestCountry"
    #         )
    #
    #         saved = customer_repo.insert(test_customer)
    #         print(f"  Created customer {saved.CustomerId} in transaction")
    #
    #         # Update it
    #         saved.Email = "updated@test.com"
    #         updated = customer_repo.update(saved)
    #         print(f"  Updated customer email to {updated.Email}")
    #
    #         # Delete it
    #         customer_repo.delete(saved.CustomerId)
    #         print(f"  Deleted customer {saved.CustomerId}")
    #
    #         # All commits automatically if no exception
    #
    #     print("[OK] Transaction completed successfully")
    #
    # except Exception as e:
    #     print(f"[ERROR] Transaction failed (rolled back): {e}")

    print("\n=== Repository Pattern Example Completed ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
