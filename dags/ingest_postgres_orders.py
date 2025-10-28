"""
============================================
PostgreSQL Orders Ingestion DAG
============================================

This DAG extracts orders data from PostgreSQL source database
and loads it to S3 raw data bucket with date partitioning.

Features:
- Incremental extraction (daily batches)
- S3 partitioning: year/month/day
- Data validation
- Error handling with retries

Schedule: Daily at 2 AM UTC
Author: Zaid Shaikh
============================================
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from datetime import datetime, timedelta
import pandas as pd
from io import StringIO
import logging
import os

# ============================================
# DAG CONFIGURATION
# ============================================

default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 20),
    'email': ['zaid07sk@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30),
}

# S3 Configuration from environment
S3_RAW_BUCKET = os.getenv('S3_RAW_BUCKET', 'ecommerce-raw-data-bnf5etbn')

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_execution_date(**context):
    """Get execution date for incremental loading"""
    execution_date = context['execution_date']
    
    # Format as YYYY-MM-DD for SQL query
    date_str = execution_date.strftime('%Y-%m-%d')
    
    # Push to XCom for downstream tasks
    context['ti'].xcom_push(key='execution_date_str', value=date_str)
    
    logging.info(f"Processing data for date: {date_str}")
    return date_str


def extract_orders_from_postgres(**context):
    """
    Extract orders from PostgreSQL for specific date
    
    Uses incremental extraction based on order_date
    Returns: Number of orders extracted
    """
    # Get execution date from previous task
    execution_date_str = context['ti'].xcom_pull(
        key='execution_date_str',
        task_ids='get_execution_date'
    )
    
    logging.info(f"Extracting orders for date: {execution_date_str}")
    
    # Connect to PostgreSQL using Airflow Connection
    pg_hook = PostgresHook(postgres_conn_id='postgres_source')
    
    # Incremental extraction query
    # Extract orders where order_date matches execution_date
    query = f"""
        SELECT 
            o.order_id,
            o.customer_id,
            c.email AS customer_email,
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
        WHERE DATE(o.order_date) = '{execution_date_str}'
        ORDER BY o.order_date, o.order_id;
    """
    
    # Execute query and get DataFrame
    df = pg_hook.get_pandas_df(query)
    
    # Log extraction stats
    logging.info(f"✅ Extracted {len(df)} orders from PostgreSQL")
    
    if len(df) > 0:
        logging.info(f"   Order ID range: {df['order_id'].min()} to {df['order_id'].max()}")
        logging.info(f"   Order total sum: ${df['order_total'].sum():.2f}")
        logging.info(f"   Order statuses: {df['order_status'].value_counts().to_dict()}")
    else:
        logging.warning(f"⚠️ No orders found for date: {execution_date_str}")
    
    # Push DataFrame to XCom as JSON (more reliable than pickle)
    context['ti'].xcom_push(key='orders_data', value=df.to_json(orient='records'))
    context['ti'].xcom_push(key='order_count', value=len(df))
    
    return len(df)


def validate_data(**context):
    """
    Validate extracted data before loading to S3
    
    Checks:
    - Data completeness
    - Required fields
    - Data types
    - Business rules
    """
    # Get data from XCom
    orders_json = context['ti'].xcom_pull(
        key='orders_data',
        task_ids='extract_orders'
    )
    
    # Convert back to DataFrame
    df = pd.read_json(StringIO(orders_json), orient='records')
    
    logging.info("=" * 50)
    logging.info("DATA VALIDATION")
    logging.info("=" * 50)
    
    # Validation checks
    validation_passed = True
    
    # Check 1: Required fields exist
    required_fields = [
        'order_id', 'customer_id', 'customer_email', 
        'order_date', 'order_total', 'order_status'
    ]
    
    missing_fields = [field for field in required_fields if field not in df.columns]
    if missing_fields:
        logging.error(f"❌ Missing required fields: {missing_fields}")
        validation_passed = False
    else:
        logging.info(f"✅ All required fields present")
    
    # Check 2: No null values in critical fields
    critical_fields = ['order_id', 'customer_id', 'order_date', 'order_total']
    null_counts = df[critical_fields].isnull().sum()
    
    if null_counts.sum() > 0:
        logging.error(f"❌ Null values found: {null_counts.to_dict()}")
        validation_passed = False
    else:
        logging.info(f"✅ No null values in critical fields")
    
    # Check 3: Business rules
    if (df['order_total'] < 0).any():
        logging.error(f"❌ Negative order totals found")
        validation_passed = False
    else:
        logging.info(f"✅ All order totals are positive")
    
    # Check 4: Data types
    if df['order_id'].dtype not in ['int64', 'int32']:
        logging.warning(f"⚠️ order_id type is {df['order_id'].dtype}, expected int")
    
    logging.info("=" * 50)
    
    if not validation_passed:
        raise ValueError("Data validation failed! Check logs for details.")
    
    logging.info("🎉 Data validation passed!")
    return True


def load_to_s3(**context):
    """
    Load orders data to S3 with date partitioning
    
    S3 Path: s3://bucket/raw/orders/year=YYYY/month=MM/day=DD/orders.csv
    """
    # Get data from XCom
    orders_json = context['ti'].xcom_pull(
        key='orders_data',
        task_ids='extract_orders'
    )
    
    execution_date_str = context['ti'].xcom_pull(
        key='execution_date_str',
        task_ids='get_execution_date'
    )
    
    # Convert to DataFrame
    df = pd.read_json(StringIO(orders_json), orient='records')
    
    if len(df) == 0:
        logging.info("No data to upload. Skipping S3 load.")
        return 0
    
    # Convert to CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()
    
    # Create S3 key with partitioning
    # Parse execution date
    date_obj = datetime.strptime(execution_date_str, '%Y-%m-%d')
    year = date_obj.strftime('%Y')
    month = date_obj.strftime('%m')
    day = date_obj.strftime('%d')
    
    # S3 path with Hive-style partitioning
    s3_key = f"raw/orders/year={year}/month={month}/day={day}/orders.csv"
    
    logging.info(f"Uploading to S3: s3://{S3_RAW_BUCKET}/{s3_key}")
    
    # Upload to S3 using Airflow S3Hook
    s3_hook = S3Hook(aws_conn_id='aws_default')
    
    s3_hook.load_string(
        string_data=csv_content,
        key=s3_key,
        bucket_name=S3_RAW_BUCKET,
        replace=True
    )
    
    logging.info(f"✅ Successfully uploaded {len(df)} orders to S3")
    logging.info(f"   S3 URI: s3://{S3_RAW_BUCKET}/{s3_key}")
    logging.info(f"   File size: {len(csv_content)} bytes")
    
    # Push S3 location to XCom
    context['ti'].xcom_push(key='s3_key', value=s3_key)
    context['ti'].xcom_push(key='s3_uri', value=f"s3://{S3_RAW_BUCKET}/{s3_key}")
    
    return s3_key


def log_summary(**context):
    """
    Log summary of the ingestion process
    """
    execution_date_str = context['ti'].xcom_pull(
        key='execution_date_str',
        task_ids='get_execution_date'
    )
    
    order_count = context['ti'].xcom_pull(
        key='order_count',
        task_ids='extract_orders'
    )
    
    s3_uri = context['ti'].xcom_pull(
        key='s3_uri',
        task_ids='load_to_s3'
    )
    
    logging.info("=" * 60)
    logging.info("INGESTION SUMMARY")
    logging.info("=" * 60)
    logging.info(f"Execution Date: {execution_date_str}")
    logging.info(f"Orders Extracted: {order_count}")
    logging.info(f"S3 Location: {s3_uri}")
    logging.info(f"Status: SUCCESS ✅")
    logging.info("=" * 60)
    
    return True


# ============================================
# DAG DEFINITION
# ============================================

with DAG(
    dag_id='ingest_postgres_orders',
    default_args=default_args,
    description='Incremental ingestion of orders from PostgreSQL to S3',
    schedule_interval='@daily',  # Run daily at 2 AM UTC
    start_date=datetime(2025, 10, 20),
    catchup=False,  # Don't backfill historical data
    max_active_runs=1,  # Only one run at a time
    tags=['ingestion', 'postgres', 'orders', 'incremental'],
) as dag:
    
    # Task 1: Get execution date
    task_get_date = PythonOperator(
        task_id='get_execution_date',
        python_callable=get_execution_date,
        provide_context=True,
    )
    
    # Task 2: Extract orders from PostgreSQL
    task_extract = PythonOperator(
        task_id='extract_orders',
        python_callable=extract_orders_from_postgres,
        provide_context=True,
    )
    
    # Task 3: Validate data
    task_validate = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data,
        provide_context=True,
    )
    
    # Task 4: Load to S3
    task_load = PythonOperator(
        task_id='load_to_s3',
        python_callable=load_to_s3,
        provide_context=True,
    )
    
    # Task 5: Log summary
    task_summary = PythonOperator(
        task_id='log_summary',
        python_callable=log_summary,
        provide_context=True,
    )
    
    # Define task dependencies
    task_get_date >> task_extract >> task_validate >> task_load >> task_summary


# ============================================
# DAG DOCUMENTATION
# ============================================

dag.doc_md = """
# PostgreSQL Orders Ingestion DAG

## Purpose
Incrementally extract orders from PostgreSQL source database and load to S3 raw data lake.

## Schedule
- **Frequency**: Daily at 2 AM UTC
- **Catchup**: Disabled (no historical backfill)
- **Max Active Runs**: 1 (prevents concurrent runs)

## Data Flow
1. **Extract**: Query orders by order_date matching execution_date
2. **Validate**: Check data quality and business rules
3. **Load**: Upload to S3 with Hive-style partitioning

## S3 Partitioning Strategy
```
s3://ecommerce-raw-data/raw/orders/
  year=2025/
    month=10/
      day=28/
        orders.csv
```

## Airflow Connections Required
- `postgres_source`: PostgreSQL source database
- `aws_default`: AWS credentials for S3 access

## Monitoring
- Check logs for validation failures
- Monitor S3 bucket for daily files
- Review task duration for performance

## Troubleshooting
- If no orders found: Normal for dates with no transactions
- Connection errors: Verify Airflow connections
- S3 upload fails: Check AWS credentials and bucket permissions
"""
