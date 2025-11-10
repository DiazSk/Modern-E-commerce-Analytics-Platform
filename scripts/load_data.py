"""
============================================
Modern E-Commerce Analytics Platform
Data Loading Script - PostgreSQL
============================================

This script loads generated CSV data into PostgreSQL source database.

Prerequisites:
    - PostgreSQL source database running (docker-compose up)
    - Generated CSV files in data/generated/
    - .env file with database credentials

Usage:
    python scripts/load_data.py

Author: Zaid Shaikh
Date: October 2025
============================================
"""

import logging
import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

# Load environment variables
load_dotenv()

# ============================================
# CONFIGURATION
# ============================================

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_CONFIG = {
    "host": os.getenv("POSTGRES_SOURCE_HOST", "localhost"),
    "port": os.getenv("POSTGRES_SOURCE_PORT", "5433"),
    "database": os.getenv("POSTGRES_SOURCE_DB", "ecommerce"),
    "user": os.getenv("POSTGRES_SOURCE_USER", "ecommerce_user"),
    "password": os.getenv("POSTGRES_SOURCE_PASSWORD", "ecommerce_password"),
}

# Data directory
DATA_DIR = Path("data/generated")

# ============================================
# DATABASE CONNECTION
# ============================================


def get_db_connection():
    """Create and return PostgreSQL connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("✅ Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        raise


# ============================================
# DATA LOADING FUNCTIONS
# ============================================


def load_customers(conn, csv_path):
    """
    Load customer data into PostgreSQL

    Args:
        conn: Database connection
        csv_path: Path to customers.csv
    """
    logger.info(f"Loading customers from {csv_path}...")

    df = pd.read_csv(csv_path)

    # Create cursor
    cur = conn.cursor()

    # Clear existing data (for clean reload)
    cur.execute("TRUNCATE TABLE customers CASCADE;")
    logger.info("  Truncated existing customers table")

    # Prepare data for insertion
    columns = [
        "email",
        "first_name",
        "last_name",
        "phone",
        "registration_date",
        "customer_segment",
        "segment_start_date",
        "segment_end_date",
        "is_current",
    ]

    # Convert DataFrame to list of tuples
    values = []
    for _, row in df.iterrows():
        values.append(
            (
                row["email"],
                row["first_name"],
                row["last_name"],
                row["phone"],
                row["registration_date"],
                row["customer_segment"],
                row["segment_start_date"],
                (
                    None
                    if pd.isna(row.get("segment_end_date"))
                    else row["segment_end_date"]
                ),
                row["is_current"],
            )
        )

    # Bulk insert using execute_values (much faster)
    insert_query = """
        INSERT INTO customers (email, first_name, last_name, phone, registration_date,
                             customer_segment, segment_start_date, segment_end_date, is_current)
        VALUES %s
    """

    execute_values(cur, insert_query, values)
    conn.commit()

    # Get count
    cur.execute("SELECT COUNT(*) FROM customers;")
    count = cur.fetchone()[0]

    logger.info(f"✅ Loaded {count:,} customers")

    cur.close()
    return count


def load_orders(conn, csv_path):
    """
    Load order data into PostgreSQL

    Args:
        conn: Database connection
        csv_path: Path to orders.csv
    """
    logger.info(f"Loading orders from {csv_path}...")

    df = pd.read_csv(csv_path)

    cur = conn.cursor()

    # Clear existing data
    cur.execute("TRUNCATE TABLE orders CASCADE;")
    cur.execute("ALTER SEQUENCE orders_order_id_seq RESTART WITH 1;")
    logger.info("  Truncated existing orders table and reset sequence")

    # Map customer email to customer_id
    cur.execute("SELECT customer_id, email FROM customers;")
    email_to_id = {email: customer_id for customer_id, email in cur.fetchall()}

    # Prepare data
    values = []
    for _, row in df.iterrows():
        customer_id = email_to_id.get(row["customer_id"])  # customer_id in CSV is email
        if customer_id:
            values.append(
                (
                    customer_id,
                    row["order_date"],
                    row["order_total"],
                    row["payment_method"],
                    row["shipping_address"],
                    row["order_status"],
                )
            )

    # Bulk insert
    insert_query = """
        INSERT INTO orders (customer_id, order_date, order_total,
                          payment_method, shipping_address, order_status)
        VALUES %s
    """

    execute_values(cur, insert_query, values)
    conn.commit()

    # Get count
    cur.execute("SELECT COUNT(*) FROM orders;")
    count = cur.fetchone()[0]

    # Debug: check order_ids
    cur.execute("SELECT MIN(order_id), MAX(order_id) FROM orders;")
    min_id, max_id = cur.fetchone()
    logger.info(f"   Order IDs range: {min_id} to {max_id}")

    logger.info(f"✅ Loaded {count:,} orders")

    cur.close()
    return count


def load_order_items(conn, csv_path):
    """
    Load order items into PostgreSQL

    Args:
        conn: Database connection
        csv_path: Path to order_items.csv
    """
    logger.info(f"Loading order items from {csv_path}...")

    df = pd.read_csv(csv_path)

    cur = conn.cursor()

    # Clear existing data
    cur.execute("TRUNCATE TABLE order_items;")
    logger.info("  Truncated existing order_items table")

    # Prepare data - convert numpy types to Python native types
    values = []
    for _, row in df.iterrows():
        values.append(
            (
                int(row["order_id"]),
                int(row["product_id"]),
                int(row["quantity"]),
                float(row["unit_price"]),
                float(row["discount_amount"]),
            )
        )

    # Bulk insert
    insert_query = """
        INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_amount)
        VALUES %s
    """

    execute_values(cur, insert_query, values)
    conn.commit()

    # Get count
    cur.execute("SELECT COUNT(*) FROM order_items;")
    count = cur.fetchone()[0]

    logger.info(f"✅ Loaded {count:,} order items")

    cur.close()
    return count


# ============================================
# DATA VALIDATION
# ============================================


def validate_data(conn):
    """Run validation queries on loaded data"""
    logger.info("\n" + "=" * 50)
    logger.info("DATA VALIDATION")
    logger.info("=" * 50)

    cur = conn.cursor()

    # Check 1: Record counts
    cur.execute("SELECT COUNT(*) FROM customers;")
    customer_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders;")
    order_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM order_items;")
    item_count = cur.fetchone()[0]

    logger.info(f"✓ Customers: {customer_count:,}")
    logger.info(f"✓ Orders: {order_count:,}")
    logger.info(f"✓ Order Items: {item_count:,}")

    # Check 2: Referential integrity
    cur.execute(
        """
        SELECT COUNT(*) FROM orders o
        WHERE NOT EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id);
    """
    )
    orphan_orders = cur.fetchone()[0]
    logger.info(f"✓ Orphan orders (should be 0): {orphan_orders}")

    # Check 3: Data quality
    cur.execute("SELECT COUNT(*) FROM orders WHERE order_total <= 0;")
    invalid_totals = cur.fetchone()[0]
    logger.info(f"✓ Invalid order totals (should be 0): {invalid_totals}")

    # Check 4: Date ranges
    cur.execute("SELECT MIN(order_date), MAX(order_date) FROM orders;")
    min_date, max_date = cur.fetchone()
    logger.info(f"✓ Order date range: {min_date} to {max_date}")

    # Check 5: Sample data
    logger.info("\nSample Order with Customer:")
    cur.execute(
        """
        SELECT
            o.order_id,
            c.email,
            c.first_name || ' ' || c.last_name AS customer_name,
            o.order_date,
            o.order_total,
            o.order_status
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        ORDER BY o.order_date DESC
        LIMIT 5;
    """
    )

    for row in cur.fetchall():
        logger.info(f"  Order #{row[0]}: {row[2]} - ${row[4]} - {row[5]}")

    # Check 6: Customer segments
    cur.execute(
        """
        SELECT customer_segment, COUNT(*)
        FROM customers
        WHERE is_current = TRUE
        GROUP BY customer_segment
        ORDER BY COUNT(*) DESC;
    """
    )
    logger.info("\nCustomer Segment Distribution:")
    for segment, count in cur.fetchall():
        logger.info(f"  {segment}: {count:,}")

    logger.info("=" * 50)

    cur.close()


# ============================================
# MAIN EXECUTION
# ============================================


def main():
    """Main execution function"""
    logger.info("=" * 50)
    logger.info("Starting Data Loading Process")
    logger.info("=" * 50)

    # Check if data files exist
    customers_csv = DATA_DIR / "customers.csv"
    orders_csv = DATA_DIR / "orders.csv"
    order_items_csv = DATA_DIR / "order_items.csv"

    for csv_file in [customers_csv, orders_csv, order_items_csv]:
        if not csv_file.exists():
            logger.error(f"❌ Required file not found: {csv_file}")
            logger.error("   Please run generate_data.py first!")
            return False

    try:
        # Connect to database
        conn = get_db_connection()

        # Load data in order (respecting foreign keys)
        load_customers(conn, customers_csv)
        load_orders(conn, orders_csv)
        load_order_items(conn, order_items_csv)

        # Validate
        validate_data(conn)

        # Close connection
        conn.close()
        logger.info("\n🎉 Data loading completed successfully!")

        return True

    except Exception as e:
        logger.error(f"❌ Error during data loading: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
