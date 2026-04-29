"""
============================================
PostgreSQL Orders Ingestion DAG
============================================

Extracts orders from PostgreSQL and loads them directly to S3
using the SqlToS3Operator — no Pandas DataFrames in memory.

Data validation runs via SQL COUNT/SUM queries before extraction
so no worker memory is consumed on DataFrame operations.

Schedule: Daily at 2 AM UTC
============================================
"""

import logging
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.transfers.sql_to_s3 import SqlToS3Operator
from airflow.providers.postgres.hooks.postgres import PostgresHook

# ============================================
# DAG CONFIGURATION
# ============================================

default_args = {
    "owner": "data_engineering",
    "depends_on_past": False,
    "start_date": datetime(2025, 10, 20),
    "email": ["zaid07sk@gmail.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}

S3_RAW_BUCKET = os.getenv("S3_RAW_BUCKET", "ecommerce-raw-data-bnf5etbn")

# ============================================
# HELPER FUNCTIONS
# ============================================


def get_execution_date(**context):
    """Push execution date string to XCom for downstream tasks."""
    date_str = context["execution_date"].strftime("%Y-%m-%d")
    context["ti"].xcom_push(key="execution_date_str", value=date_str)
    logging.info(f"Processing data for date: {date_str}")
    return date_str


def validate_source_data(**context):
    """
    SQL-based pre-flight validation against the source database.

    Uses PostgresHook.get_first() — zero DataFrame allocation.
    Checks:
      - Row count for the execution date
      - No negative order totals
      - All orders have a valid customer_id
    """
    date_str = context["ti"].xcom_pull(
        key="execution_date_str", task_ids="get_execution_date"
    )

    pg_hook = PostgresHook(postgres_conn_id="postgres_source")

    # Check 1: row count
    row_count = pg_hook.get_first(
        f"SELECT COUNT(*) FROM orders WHERE DATE(order_date) = '{date_str}'"
    )[0]
    logging.info(f"Orders for {date_str}: {row_count}")

    if row_count == 0:
        logging.warning(f"No orders found for {date_str} — this may be expected.")

    # Check 2: negative order totals
    neg_count = pg_hook.get_first(
        f"SELECT COUNT(*) FROM orders WHERE DATE(order_date) = '{date_str}' AND order_total < 0"
    )[0]
    if neg_count > 0:
        raise ValueError(f"Data quality failure: {neg_count} orders with negative totals on {date_str}")
    logging.info("No negative order totals found.")

    # Check 3: orphaned orders (customer_id missing from customers)
    orphan_count = pg_hook.get_first(
        f"""
        SELECT COUNT(*)
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.customer_id
        WHERE DATE(o.order_date) = '{date_str}'
          AND c.customer_id IS NULL
        """
    )[0]
    if orphan_count > 0:
        raise ValueError(f"Data quality failure: {orphan_count} orders with no matching customer on {date_str}")
    logging.info("All orders have valid customer references.")

    context["ti"].xcom_push(key="order_count", value=row_count)
    return row_count


def log_summary(**context):
    """Log ingestion summary after S3 upload completes."""
    date_str = context["ti"].xcom_pull(
        key="execution_date_str", task_ids="get_execution_date"
    )
    order_count = context["ti"].xcom_pull(key="order_count", task_ids="validate_source_data")

    execution_date = context["execution_date"]
    year = execution_date.strftime("%Y")
    month = execution_date.strftime("%m")
    day = execution_date.strftime("%d")
    s3_uri = f"s3://{S3_RAW_BUCKET}/raw/orders/year={year}/month={month}/day={day}/orders.csv"

    logging.info("=" * 60)
    logging.info("INGESTION SUMMARY")
    logging.info("=" * 60)
    logging.info(f"Execution Date : {date_str}")
    logging.info(f"Orders in Source: {order_count}")
    logging.info(f"S3 Location    : {s3_uri}")
    logging.info(f"Status         : SUCCESS")
    logging.info("=" * 60)
    return True


# ============================================
# DAG DEFINITION
# ============================================

with DAG(
    dag_id="ingest_postgres_orders",
    default_args=default_args,
    description="Incremental ingestion of orders from PostgreSQL to S3 via SqlToS3Operator",
    schedule_interval="@daily",
    start_date=datetime(2025, 10, 20),
    catchup=False,
    max_active_runs=1,
    tags=["ingestion", "postgres", "orders", "incremental"],
) as dag:

    task_get_date = PythonOperator(
        task_id="get_execution_date",
        python_callable=get_execution_date,
        provide_context=True,
    )

    task_validate = PythonOperator(
        task_id="validate_source_data",
        python_callable=validate_source_data,
        provide_context=True,
    )

    # SqlToS3Operator streams query results directly to S3 in chunks —
    # no DataFrame is held in worker memory or passed through XCom.
    task_extract_to_s3 = SqlToS3Operator(
        task_id="extract_to_s3",
        sql="""
            SELECT
                o.order_id,
                o.customer_id,
                c.email          AS customer_email,
                c.first_name,
                c.last_name,
                c.customer_segment,
                o.order_date,
                o.order_total,
                o.payment_method,
                o.shipping_address,
                o.order_status,
                o.created_at,
                o.updated_at
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE DATE(o.order_date) = '{{ ds }}'
            ORDER BY o.order_date, o.order_id
        """,
        s3_bucket=S3_RAW_BUCKET,
        s3_key=(
            "raw/orders"
            "/year={{ execution_date.strftime('%Y') }}"
            "/month={{ execution_date.strftime('%m') }}"
            "/day={{ execution_date.strftime('%d') }}"
            "/orders.csv"
        ),
        sql_conn_id="postgres_source",
        aws_conn_id="aws_default",
        file_format="csv",
        replace=True,
    )

    task_summary = PythonOperator(
        task_id="log_summary",
        python_callable=log_summary,
        provide_context=True,
    )

    task_get_date >> task_validate >> task_extract_to_s3 >> task_summary


dag.doc_md = """
# PostgreSQL Orders Ingestion DAG

## Purpose
Incrementally extract orders from PostgreSQL and load to the S3 raw data lake.

## Data Flow
1. **get_execution_date** — sets the incremental date window
2. **validate_source_data** — SQL-based row count, negative total, and orphan checks
3. **extract_to_s3** — `SqlToS3Operator` streams query results to S3 (no Pandas in-memory)
4. **log_summary** — records partition path and row count

## S3 Partitioning
```
s3://ecommerce-raw-data/raw/orders/year=YYYY/month=MM/day=DD/orders.csv
```

## Connections Required
- `postgres_source` — PostgreSQL source database
- `aws_default`     — AWS credentials for S3 access
"""
