"""
Seed script for Demonbreun Goods SQLite database.

Creates and populates a SQLite database with products, regions, and sales data.
Run with: python data/seed_sql.py

Database will be created at: data/seed.db
"""

import sqlite3
from datetime import datetime, timedelta
import random

def create_database(db_path: str = "data/seed.db"):
    """Create and populate the Demonbreun Goods database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS regions (
            region_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit_price REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            region_id INTEGER NOT NULL,
            sale_date TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            revenue REAL NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (region_id) REFERENCES regions(region_id)
        )
    """)

    # Insert regions
    regions = [
        (1, "Northeast"),
        (2, "Southeast"),
        (3, "Midwest"),
        (4, "Southwest"),
        (5, "West Coast"),
    ]
    cursor.executemany("INSERT INTO regions (region_id, name) VALUES (?, ?)", regions)

    # Insert products
    products = [
        (1, "Wool Blanket - Charcoal", "Home & Garden", 89.99),
        (2, "Cotton T-Shirt - Navy", "Apparel", 24.99),
        (3, "Ceramic Mug - Blue", "Home & Garden", 16.99),
        (4, "Leather Wallet", "Accessories", 49.99),
        (5, "Fleece Jacket - Forest Green", "Apparel", 119.99),
        (6, "Desk Lamp - Brass", "Home & Garden", 74.99),
        (7, "Socks (Pack of 3) - Grey", "Apparel", 14.99),
        (8, "Bamboo Cutting Board", "Home & Garden", 39.99),
        (9, "Canvas Tote Bag", "Accessories", 29.99),
        (10, "Stainless Steel Water Bottle", "Accessories", 34.99),
    ]
    cursor.executemany(
        "INSERT INTO products (product_id, name, category, unit_price) VALUES (?, ?, ?, ?)",
        products
    )

    # Generate sales data for 18 months (Jan 2023 - Jun 2024)
    sales_data = []
    sale_id = 1
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 6, 30)

    current_date = start_date
    while current_date <= end_date:
        # Generate 5-15 sales per day across all regions and products
        num_sales = random.randint(5, 15)
        for _ in range(num_sales):
            product_id = random.randint(1, 10)
            region_id = random.randint(1, 5)
            quantity = random.randint(1, 5)
            unit_price = next(p[3] for p in products if p[0] == product_id)
            revenue = quantity * unit_price

            sales_data.append((
                sale_id,
                product_id,
                region_id,
                current_date.strftime("%Y-%m-%d"),
                quantity,
                revenue
            ))
            sale_id += 1

        current_date += timedelta(days=1)

    cursor.executemany(
        """
        INSERT INTO sales (sale_id, product_id, region_id, sale_date, quantity, revenue)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        sales_data
    )

    conn.commit()
    conn.close()
    print(f"✓ Database created and populated at {db_path}")
    print(f"  - {len(regions)} regions")
    print(f"  - {len(products)} products")
    print(f"  - {len(sales_data)} sales records")


if __name__ == "__main__":
    create_database()
