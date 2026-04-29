"""
============================================
Clickstream Events Ingestion DAG
============================================

Reads clickstream CSV data and streams it to S3 with date
partitioning using Python's built-in csv module — no Pandas.

The file is processed line-by-line via csv.DictReader.
Rows are bucketed into per-date StringIO buffers and uploaded
to S3 without loading the full dataset into a DataFrame.

Schedule: Hourly
============================================
"""

import csv
import io
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta

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

S3_RAW_BUCKET = os.getenv("S3_RAW_BUCKET", "ecommerce-raw-data-bnf5etbn")
DATA_PATH = "/opt/airflow/data/generated/clickstream_events.csv"

REQUIRED_FIELDS = [
    "event_id", "session_id", "user_id", "event_timestamp",
    "event_type", "product_id", "page_url", "device_type", "browser",
]
VALID_EVENT_TYPES = {
    "page_view", "add_to_cart", "remove_from_cart", "purchase", "search",
}

# ============================================
# HELPER FUNCTIONS
# ============================================


def get_execution_date(**context):
    """Push execution date string to XCom."""
    date_str = context["execution_date"].strftime("%Y-%m-%d")
    context["ti"].xcom_push(key="execution_date_str", value=date_str)
    logging.info(f"Processing clickstream data for date: {date_str}")
    return date_str


def stream_and_upload_to_s3(**context):
    """
    Stream the clickstream CSV line-by-line and upload per-date partitions to S3.

    Approach (no Pandas):
      - csv.DictReader iterates the file one row at a time
      - Rows are collected into per-date csv.writer buffers (StringIO)
      - Each date partition is uploaded to S3 when the streaming is done
      - Validation errors are logged as warnings; critical failures raise
    """
    if not os.path.exists(DATA_PATH):
        logging.warning(f"Clickstream file not found: {DATA_PATH} — skipping.")
        context["ti"].xcom_push(key="total_events", value=0)
        context["ti"].xcom_push(key="partition_count", value=0)
        return 0

    # per-date buffers: { "YYYY-MM-DD": {"buffer": StringIO, "writer": csv.writer, "count": int} }
    partitions: dict = {}
    fieldnames_written: set = set()

    total_rows = 0
    invalid_event_type_count = 0
    null_field_count = 0

    with open(DATA_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate that required columns exist in the file header
        missing = [col for col in REQUIRED_FIELDS if col not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Clickstream CSV is missing required columns: {missing}")

        for row in reader:
            # ---- Validation (row-level) ----
            critical_nulls = [
                field for field in ["event_id", "user_id", "event_timestamp", "event_type"]
                if not row.get(field)
            ]
            if critical_nulls:
                null_field_count += 1
                continue  # skip malformed rows

            event_type = row.get("event_type", "")
            if event_type not in VALID_EVENT_TYPES:
                invalid_event_type_count += 1

            # ---- Date partitioning ----
            raw_ts = row["event_timestamp"]
            try:
                # Support both "YYYY-MM-DD HH:MM:SS" and ISO "YYYY-MM-DDTHH:MM:SS" formats
                ts_clean = raw_ts.replace("T", " ").split(".")[0]
                event_date = ts_clean[:10]  # "YYYY-MM-DD"
                year, month, day = event_date.split("-")
            except Exception:
                logging.warning(f"Unparseable timestamp '{raw_ts}' — skipping row.")
                continue

            # Initialise buffer for this date if first time seen
            if event_date not in partitions:
                buf = io.StringIO()
                writer = csv.DictWriter(buf, fieldnames=reader.fieldnames)
                writer.writeheader()
                partitions[event_date] = {"buffer": buf, "writer": writer, "count": 0, "year": year, "month": month, "day": day}

            partitions[event_date]["writer"].writerow(row)
            partitions[event_date]["count"] += 1
            total_rows += 1

    if null_field_count > 0:
        logging.warning(f"Skipped {null_field_count} rows with null critical fields.")
    if invalid_event_type_count > 0:
        logging.warning(f"{invalid_event_type_count} rows had unrecognised event_type values.")

    if total_rows == 0:
        logging.info("No valid events to upload.")
        context["ti"].xcom_push(key="total_events", value=0)
        context["ti"].xcom_push(key="partition_count", value=0)
        return 0

    # ---- Upload each date partition to S3 ----
    s3_hook = S3Hook(aws_conn_id="aws_default")
    uploaded = []

    for event_date, info in partitions.items():
        s3_key = (
            f"raw/clickstream"
            f"/year={info['year']}"
            f"/month={info['month']}"
            f"/day={info['day']}"
            f"/events.csv"
        )
        s3_hook.load_string(
            string_data=info["buffer"].getvalue(),
            key=s3_key,
            bucket_name=S3_RAW_BUCKET,
            replace=True,
        )
        logging.info(f"Uploaded {info['count']} events → s3://{S3_RAW_BUCKET}/{s3_key}")
        uploaded.append({"date": event_date, "events": info["count"], "s3_key": s3_key})

    context["ti"].xcom_push(key="total_events", value=total_rows)
    context["ti"].xcom_push(key="partition_count", value=len(uploaded))
    context["ti"].xcom_push(key="uploaded_files", value=uploaded)
    return len(uploaded)


def log_summary(**context):
    """Log ingestion summary."""
    date_str = context["ti"].xcom_pull(
        key="execution_date_str", task_ids="get_execution_date"
    )
    total_events = context["ti"].xcom_pull(key="total_events", task_ids="stream_and_upload_to_s3") or 0
    partition_count = context["ti"].xcom_pull(key="partition_count", task_ids="stream_and_upload_to_s3") or 0
    uploaded_files = context["ti"].xcom_pull(key="uploaded_files", task_ids="stream_and_upload_to_s3") or []

    logging.info("=" * 60)
    logging.info("CLICKSTREAM INGESTION SUMMARY")
    logging.info("=" * 60)
    logging.info(f"Execution Date      : {date_str}")
    logging.info(f"Total Events        : {total_events:,}")
    logging.info(f"Date Partitions     : {partition_count}")
    for info in uploaded_files:
        logging.info(f"  {info['date']}: {info['events']:,} events")
    logging.info(f"S3 Prefix           : s3://{S3_RAW_BUCKET}/raw/clickstream/")
    logging.info(f"Status              : SUCCESS")
    logging.info("=" * 60)
    return True


# ============================================
# DAG DEFINITION
# ============================================

with DAG(
    dag_id="ingest_clickstream_events",
    default_args=default_args,
    description="Streaming clickstream CSV ingestion to S3 with date partitioning (no Pandas)",
    schedule_interval="@hourly",
    start_date=datetime(2025, 10, 20),
    catchup=False,
    max_active_runs=1,
    tags=["ingestion", "clickstream", "events", "batch"],
) as dag:

    task_get_date = PythonOperator(
        task_id="get_execution_date",
        python_callable=get_execution_date,
        provide_context=True,
    )

    task_stream_upload = PythonOperator(
        task_id="stream_and_upload_to_s3",
        python_callable=stream_and_upload_to_s3,
        provide_context=True,
    )

    task_summary = PythonOperator(
        task_id="log_summary",
        python_callable=log_summary,
        provide_context=True,
    )

    task_get_date >> task_stream_upload >> task_summary


dag.doc_md = """
# Clickstream Events Ingestion DAG

## Purpose
Stream clickstream CSV data to the S3 raw data lake with Hive-style date partitioning.

## Data Flow
1. **get_execution_date** — sets the run window
2. **stream_and_upload_to_s3** — reads CSV row-by-row via `csv.DictReader`,
   accumulates per-date buffers, uploads each partition to S3
3. **log_summary** — records event counts and partition paths

## S3 Partitioning
```
s3://ecommerce-raw-data/raw/clickstream/year=YYYY/month=MM/day=DD/events.csv
```

## Connection Required
- `aws_default` — AWS credentials for S3 access
"""
