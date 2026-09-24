#!/usr/bin/env python3
"""
Quick check: Does fact_orders exist? If not, run dbt first!
"""

import sys

import psycopg2


def main():
    print("\n" + "=" * 80)
    print("CHECKING DATABASE FOR fact_orders TABLE")
    print("=" * 80 + "\n")

    try:
        # Connect to database
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="ecommerce",
            user="ecommerce_user",
            password="ecommerce_pass",
        )

        cur = conn.cursor()

        # Check if table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'fact_orders'
            );
        """)

        exists = cur.fetchone()[0]

        if exists:
            # Get row count
            cur.execute("SELECT COUNT(*) FROM public.fact_orders")
            count = cur.fetchone()[0]

            print("✅ fact_orders EXISTS!")
            print(f"✅ Row count: {count:,}")
            print("\n✅ Ready for Great Expectations!")

        else:
            print("❌ fact_orders DOES NOT EXIST")
            print("\n🔧 FIX: Run dbt to create the table:")
            print("   cd transform")
            print("   dbt run --select fact_orders")
            print("\nThen try again!")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        print("\n🔧 Make sure PostgreSQL is running:")
        print("   docker ps")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
