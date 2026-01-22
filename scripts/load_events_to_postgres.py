"""
Load Clickstream Events from S3 CSV to PostgreSQL
"""

import csv
import os
from io import StringIO

import boto3
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS Configuration
S3_BUCKET = os.getenv("S3_RAW_BUCKET", "ecommerce-raw-data-bnf5etbn")
S3_PREFIX = "raw/clickstream/"

# PostgreSQL Configuration
PG_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "ecommerce",
    "user": "ecommerce_user",
    "password": "ecommerce_pass",
}


def create_events_table():
    """Create clickstream_events table if not exists"""
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    # Drop table if exists (to recreate with correct schema)
    cur.execute("DROP TABLE IF EXISTS clickstream_events CASCADE;")

    create_table_sql = """
    CREATE TABLE clickstream_events (
        event_id VARCHAR(100) PRIMARY KEY,
        session_id VARCHAR(100),
        user_id VARCHAR(255),  -- Changed to VARCHAR to handle emails
        event_timestamp TIMESTAMP,
        event_type VARCHAR(50),
        product_id VARCHAR(100),  -- Changed to VARCHAR for flexibility
        page_url TEXT,
        device_type VARCHAR(50),
        browser VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_events_user_id ON clickstream_events(user_id);
    CREATE INDEX IF NOT EXISTS idx_events_event_type ON clickstream_events(event_type);
    CREATE INDEX IF NOT EXISTS idx_events_timestamp ON clickstream_events(event_timestamp);
    CREATE INDEX IF NOT EXISTS idx_events_product_id ON clickstream_events(product_id);
    """

    cur.execute(create_table_sql)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Clickstream events table created successfully")


def load_events_from_s3():
    """Load events from S3 CSV files to PostgreSQL"""
    s3 = boto3.client("s3")
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    # List all event files in S3
    response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=S3_PREFIX)

    if "Contents" not in response:
        print("❌ No events found in S3")
        return

    total_events = 0
    processed_files = 0

    for obj in response["Contents"]:
        if obj["Key"].endswith(".csv"):
            print(f"Processing: {obj['Key']}")

            # Download CSV from S3
            file_obj = s3.get_object(Bucket=S3_BUCKET, Key=obj["Key"])
            csv_content = file_obj["Body"].read().decode("utf-8")

            # Parse CSV
            csv_reader = csv.DictReader(StringIO(csv_content))

            batch_size = 0
            for row in csv_reader:
                insert_sql = """
                INSERT INTO clickstream_events (
                    event_id, session_id, user_id, event_timestamp,
                    event_type, product_id, page_url, device_type, browser
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO NOTHING;
                """

                # Handle user_id as string (could be email or ID)
                user_id = row.get("user_id", "")

                # Handle product_id as string
                product_id = row.get("product_id", "")

                cur.execute(
                    insert_sql,
                    (
                        row["event_id"],
                        row["session_id"],
                        user_id if user_id else None,
                        row["event_timestamp"],
                        row["event_type"],
                        product_id if product_id else None,
                        row["page_url"],
                        row["device_type"],
                        row["browser"],
                    ),
                )
                batch_size += 1
                total_events += 1

            # Commit after each file
            conn.commit()
            processed_files += 1
            print(f"  → Loaded {batch_size} events from this file")

    cur.close()
    conn.close()

    print(f"✅ Processed {processed_files} files")
    print(f"✅ Loaded {total_events} total events to PostgreSQL")

    # Get event statistics
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            event_type,
            COUNT(*) as count
        FROM clickstream_events
        GROUP BY event_type
        ORDER BY count DESC;
    """
    )

    print("\n📊 Event Type Distribution:")
    for row in cur.fetchall():
        print(f"   {row[0]}: {row[1]:,}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Starting clickstream events data load from S3 to PostgreSQL...")
    print("=" * 60)
    create_events_table()
    load_events_from_s3()
    print("=" * 60)
    print("Clickstream events load complete! 🎉")
    print("=" * 60)
