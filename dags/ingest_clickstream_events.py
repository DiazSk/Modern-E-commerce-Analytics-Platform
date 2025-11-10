"""
============================================
Clickstream Events Ingestion DAG
============================================

This DAG processes clickstream event data from CSV files
and loads it to S3 raw data bucket with date partitioning.

Features:
- Batch CSV processing
- Event data validation
- S3 partitioning by event date
- Error handling with retries

Schedule: Hourly
Author: Zaid Shaikh
============================================
"""

import logging
import os
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

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

# S3 Configuration
S3_RAW_BUCKET = os.getenv("S3_RAW_BUCKET", "ecommerce-raw-data-bnf5etbn")

# Local data path (for initial load)
DATA_PATH = "/opt/airflow/data/generated/clickstream_events.csv"

# ============================================
# HELPER FUNCTIONS
# ============================================


def get_execution_date(**context):
    """Get execution date for processing"""
    execution_date = context["execution_date"]
    date_str = execution_date.strftime("%Y-%m-%d")

    context["ti"].xcom_push(key="execution_date_str", value=date_str)

    logging.info(f"Processing clickstream data for date: {date_str}")
    return date_str


def read_and_filter_events(**context):
    """
    Read clickstream events from CSV and filter by execution date

    For initial batch load, processes all historical events.
    For scheduled runs, would process new events only.

    Returns: Number of events processed
    """
    execution_date_str = context["ti"].xcom_pull(
        key="execution_date_str", task_ids="get_execution_date"
    )

    logging.info(f"Reading clickstream events from: {DATA_PATH}")

    # Check if file exists
    if not os.path.exists(DATA_PATH):
        logging.warning(f"⚠️ Clickstream file not found: {DATA_PATH}")
        logging.info("   This is normal for scheduled runs after initial load")
        context["ti"].xcom_push(key="events_data", value="[]")
        context["ti"].xcom_push(key="event_count", value=0)
        return 0

    # Read CSV
    df = pd.read_csv(DATA_PATH)

    logging.info(f"✅ Read {len(df)} total events from CSV")

    # Convert event_timestamp to datetime if it's not already
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"])

    # Extract date from timestamp for filtering
    df["event_date"] = df["event_timestamp"].dt.date

    # For batch processing: group events by date
    # We'll process all events, but organize them by date
    logging.info(f"   Date range: {df['event_date'].min()} to {df['event_date'].max()}")
    logging.info(f"   Event types: {df['event_type'].value_counts().to_dict()}")
    logging.info(f"   Unique users: {df['user_id'].nunique()}")

    # Push all events to XCom (we'll partition them in next task)
    context["ti"].xcom_push(
        key="events_data", value=df.to_json(orient="records", date_format="iso")
    )
    context["ti"].xcom_push(key="event_count", value=len(df))

    return len(df)


def validate_events(**context):
    """
    Validate clickstream event data

    Checks:
    - Required fields
    - Data types
    - Event type values
    - Timestamps
    """
    events_json = context["ti"].xcom_pull(key="events_data", task_ids="read_events")

    if events_json == "[]":
        logging.info("No events to validate. Skipping.")
        return True

    df = pd.read_json(StringIO(events_json), orient="records")

    logging.info("=" * 50)
    logging.info("DATA VALIDATION")
    logging.info("=" * 50)

    validation_passed = True

    # Check 1: Required fields
    required_fields = [
        "event_id",
        "session_id",
        "user_id",
        "event_timestamp",
        "event_type",
        "product_id",
        "page_url",
        "device_type",
        "browser",
    ]

    missing_fields = [field for field in required_fields if field not in df.columns]
    if missing_fields:
        logging.error(f"❌ Missing required fields: {missing_fields}")
        validation_passed = False
    else:
        logging.info(f"✅ All required fields present")

    # Check 2: No null values in critical fields
    critical_fields = ["event_id", "user_id", "event_timestamp", "event_type"]
    null_counts = df[critical_fields].isnull().sum()

    if null_counts.sum() > 0:
        logging.error(f"❌ Null values found: {null_counts.to_dict()}")
        validation_passed = False
    else:
        logging.info(f"✅ No null values in critical fields")

    # Check 3: Valid event types
    valid_event_types = [
        "page_view",
        "add_to_cart",
        "remove_from_cart",
        "purchase",
        "search",
    ]
    invalid_events = df[~df["event_type"].isin(valid_event_types)]

    if len(invalid_events) > 0:
        logging.warning(f"⚠️ {len(invalid_events)} events with invalid event_type")
    else:
        logging.info(f"✅ All event types are valid")

    # Check 4: Timestamp validation
    try:
        df["event_timestamp"] = pd.to_datetime(df["event_timestamp"])
        logging.info(f"✅ All timestamps are valid")
    except Exception as e:
        logging.error(f"❌ Timestamp parsing failed: {str(e)}")
        validation_passed = False

    # Statistics
    logging.info(f"\nEvent Statistics:")
    logging.info(f"   Total events: {len(df):,}")
    logging.info(f"   Unique users: {df['user_id'].nunique():,}")
    logging.info(f"   Unique sessions: {df['session_id'].nunique():,}")
    logging.info(f"   Event types: {df['event_type'].value_counts().to_dict()}")
    logging.info(f"   Device types: {df['device_type'].value_counts().to_dict()}")

    logging.info("=" * 50)

    if not validation_passed:
        raise ValueError("Data validation failed! Check logs for details.")

    logging.info("🎉 Data validation passed!")
    return True


def partition_and_upload_to_s3(**context):
    """
    Partition events by date and upload to S3

    Creates separate CSV files for each date with Hive-style partitioning:
    s3://bucket/raw/clickstream/year=YYYY/month=MM/day=DD/events.csv
    """
    events_json = context["ti"].xcom_pull(key="events_data", task_ids="read_events")

    if events_json == "[]":
        logging.info("No events to upload. Skipping S3 load.")
        return 0

    df = pd.read_json(StringIO(events_json), orient="records")

    # Ensure timestamp is datetime
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"])

    # Extract date components
    df["event_date"] = df["event_timestamp"].dt.date
    df["year"] = df["event_timestamp"].dt.year
    df["month"] = df["event_timestamp"].dt.strftime("%m")
    df["day"] = df["event_timestamp"].dt.strftime("%d")

    # Group by date
    date_groups = df.groupby(["year", "month", "day"])

    logging.info(
        f"Partitioning {len(df)} events into {len(date_groups)} date partitions"
    )

    s3_hook = S3Hook(aws_conn_id="aws_default")
    uploaded_files = []

    # Upload each date partition
    for (year, month, day), group_df in date_groups:
        # Drop helper columns
        upload_df = group_df.drop(columns=["event_date", "year", "month", "day"])

        # Convert to CSV
        csv_buffer = StringIO()
        upload_df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()

        # S3 key with Hive-style partitioning
        s3_key = f"raw/clickstream/year={year}/month={month}/day={day}/events.csv"

        logging.info(
            f"   Uploading {len(group_df)} events to: s3://{S3_RAW_BUCKET}/{s3_key}"
        )

        # Upload to S3
        s3_hook.load_string(
            string_data=csv_content, key=s3_key, bucket_name=S3_RAW_BUCKET, replace=True
        )

        uploaded_files.append(
            {"date": f"{year}-{month}-{day}", "events": len(group_df), "s3_key": s3_key}
        )

    logging.info(f"✅ Successfully uploaded {len(uploaded_files)} partitions to S3")

    # Push summary to XCom
    context["ti"].xcom_push(key="uploaded_files", value=uploaded_files)
    context["ti"].xcom_push(key="total_events", value=len(df))
    context["ti"].xcom_push(key="partition_count", value=len(uploaded_files))

    return len(uploaded_files)


def log_summary(**context):
    """
    Log summary of the ingestion process
    """
    execution_date_str = context["ti"].xcom_pull(
        key="execution_date_str", task_ids="get_execution_date"
    )

    total_events = (
        context["ti"].xcom_pull(key="total_events", task_ids="upload_to_s3") or 0
    )

    partition_count = (
        context["ti"].xcom_pull(key="partition_count", task_ids="upload_to_s3") or 0
    )

    uploaded_files = context["ti"].xcom_pull(
        key="uploaded_files", task_ids="upload_to_s3"
    )

    logging.info("=" * 60)
    logging.info("CLICKSTREAM INGESTION SUMMARY")
    logging.info("=" * 60)
    logging.info(f"Execution Date: {execution_date_str}")
    logging.info(f"Total Events Processed: {total_events:,}")
    logging.info(f"Date Partitions Created: {partition_count}")

    if uploaded_files and len(uploaded_files) > 0:
        logging.info(f"\nPartition Details:")
        for file_info in uploaded_files:
            logging.info(f"   {file_info['date']}: {file_info['events']:,} events")
    else:
        logging.info(f"\n⚠️ No events processed (CSV file not found or empty)")

    logging.info(f"\nS3 Location: s3://{S3_RAW_BUCKET}/raw/clickstream/")
    logging.info(f"Status: SUCCESS ✅")
    logging.info("=" * 60)

    return True


# ============================================
# DAG DEFINITION
# ============================================

with DAG(
    dag_id="ingest_clickstream_events",
    default_args=default_args,
    description="Batch ingestion of clickstream events to S3 with date partitioning",
    schedule_interval="@hourly",  # Hourly for real-time processing
    start_date=datetime(2025, 10, 20),
    catchup=False,  # Don't backfill historical data
    max_active_runs=1,  # Only one run at a time
    tags=["ingestion", "clickstream", "events", "batch"],
) as dag:
    # Task 1: Get execution date
    task_get_date = PythonOperator(
        task_id="get_execution_date",
        python_callable=get_execution_date,
        provide_context=True,
    )

    # Task 2: Read and filter events
    task_read = PythonOperator(
        task_id="read_events",
        python_callable=read_and_filter_events,
        provide_context=True,
    )

    # Task 3: Validate data
    task_validate = PythonOperator(
        task_id="validate_data",
        python_callable=validate_events,
        provide_context=True,
    )

    # Task 4: Partition and upload to S3
    task_upload = PythonOperator(
        task_id="upload_to_s3",
        python_callable=partition_and_upload_to_s3,
        provide_context=True,
    )

    # Task 5: Log summary
    task_summary = PythonOperator(
        task_id="log_summary",
        python_callable=log_summary,
        provide_context=True,
    )

    # Define task dependencies
    task_get_date >> task_read >> task_validate >> task_upload >> task_summary


# ============================================
# DAG DOCUMENTATION
# ============================================

dag.doc_md = """
# Clickstream Events Ingestion DAG

## Purpose
Process clickstream event data from CSV files and load to S3 with date partitioning.

## Schedule
- **Frequency**: Hourly (for near real-time processing)
- **Catchup**: Disabled
- **Max Active Runs**: 1

## Data Flow
1. **Read**: Load events from CSV file
2. **Validate**: Check data quality and structure
3. **Partition**: Group events by date (event_timestamp)
4. **Load**: Upload to S3 with Hive-style partitioning

## S3 Partitioning Strategy
```
s3://ecommerce-raw-data/raw/clickstream/
  year=2023/
    month=10/
      day=29/
        events.csv
  year=2024/
    ...
  year=2025/
    month=10/
      day=28/
        events.csv
```

## Data Schema
- event_id: Unique event identifier
- session_id: User session identifier
- user_id: User identifier
- event_timestamp: Event timestamp
- event_type: Type of event (page_view, add_to_cart, etc.)
- product_id: Associated product
- page_url: URL visited
- device_type: Device used (mobile, desktop, tablet)
- browser: Browser used

## Event Types
- page_view: User viewed a page
- add_to_cart: User added item to cart
- remove_from_cart: User removed item from cart
- purchase: User completed purchase
- search: User performed search

## Monitoring
- Check logs for file read errors
- Monitor partition counts
- Review event type distribution
- Track user and session counts

## Troubleshooting
- File not found: Normal after initial batch load
- Validation errors: Check CSV format
- S3 upload fails: Check AWS credentials
"""
