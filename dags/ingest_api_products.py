"""
============================================
FakeStore API Products Ingestion DAG
============================================

This DAG fetches product catalog from FakeStore API
and loads it to S3 raw data bucket.

Features:
- REST API integration
- JSON data processing
- S3 storage with date partitioning
- Error handling with retries
- Data validation

Schedule: Daily at 3 AM UTC
Author: Zaid Shaikh
============================================
"""

import json
import logging
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.http.operators.http import SimpleHttpOperator

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

# API Configuration
FAKESTORE_API_URL = "https://fakestoreapi.com/products"

# ============================================
# HELPER FUNCTIONS
# ============================================


def get_execution_date(**context):
    """Get execution date for file naming"""
    execution_date = context["execution_date"]
    date_str = execution_date.strftime("%Y-%m-%d")

    context["ti"].xcom_push(key="execution_date_str", value=date_str)

    logging.info(f"Processing API data for date: {date_str}")
    return date_str


def fetch_products_from_api(**context):
    """
    Fetch products from FakeStore API

    Returns: JSON array of products
    """
    import requests

    logging.info(f"Fetching products from: {FAKESTORE_API_URL}")

    try:
        # Make API request
        response = requests.get(FAKESTORE_API_URL, timeout=30)
        response.raise_for_status()  # Raise error for bad status codes

        # Parse JSON
        products = response.json()

        logging.info(f"✅ Successfully fetched {len(products)} products from API")

        # Log sample product
        if len(products) > 0:
            logging.info(f"   Sample product: {products[0].get('title', 'N/A')}")
            logging.info(f"   Categories: {set([p.get('category') for p in products])}")

        # Push to XCom
        context["ti"].xcom_push(key="products_data", value=json.dumps(products))
        context["ti"].xcom_push(key="product_count", value=len(products))

        return len(products)

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ API request failed: {str(e)}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"❌ JSON parsing failed: {str(e)}")
        raise


def validate_product_data(**context):
    """
    Validate fetched product data

    Checks:
    - Data structure
    - Required fields
    - Data types
    - Business rules
    """
    # Get data from XCom
    products_json = context["ti"].xcom_pull(
        key="products_data", task_ids="fetch_products"
    )

    products = json.loads(products_json)

    logging.info("=" * 50)
    logging.info("DATA VALIDATION")
    logging.info("=" * 50)

    validation_passed = True

    # Check 1: Data is a list
    if not isinstance(products, list):
        logging.error(f"❌ Data is not a list: {type(products)}")
        validation_passed = False
    else:
        logging.info(f"✅ Data is a valid list with {len(products)} items")

    # Check 2: Required fields in each product
    required_fields = ["id", "title", "price", "category", "description", "image"]

    missing_fields_count = 0
    for i, product in enumerate(products[:5]):  # Check first 5
        missing = [f for f in required_fields if f not in product]
        if missing:
            logging.warning(f"⚠️ Product {i} missing fields: {missing}")
            missing_fields_count += 1

    if missing_fields_count == 0:
        logging.info(f"✅ All required fields present in sample products")
    else:
        logging.warning(f"⚠️ {missing_fields_count} products with missing fields")

    # Check 3: Price validation
    invalid_prices = [
        p
        for p in products
        if not isinstance(p.get("price"), (int, float)) or p.get("price", 0) <= 0
    ]

    if len(invalid_prices) > 0:
        logging.warning(f"⚠️ {len(invalid_prices)} products with invalid prices")
    else:
        logging.info(f"✅ All product prices are valid")

    # Check 4: Data statistics
    categories = set([p.get("category") for p in products])
    avg_price = (
        sum([p.get("price", 0) for p in products]) / len(products) if products else 0
    )

    logging.info(f"   Total products: {len(products)}")
    logging.info(f"   Categories: {categories}")
    logging.info(f"   Average price: ${avg_price:.2f}")

    logging.info("=" * 50)

    if not validation_passed:
        raise ValueError("Data validation failed! Check logs for details.")

    logging.info("🎉 Data validation passed!")
    return True


def enrich_product_data(**context):
    """
    Enrich product data with additional metadata

    Adds:
    - ingestion_timestamp
    - execution_date
    - data_source
    """
    products_json = context["ti"].xcom_pull(
        key="products_data", task_ids="fetch_products"
    )

    execution_date_str = context["ti"].xcom_pull(
        key="execution_date_str", task_ids="get_execution_date"
    )

    products = json.loads(products_json)

    # Add metadata to each product
    current_timestamp = datetime.utcnow().isoformat()

    enriched_products = []
    for product in products:
        enriched = product.copy()
        enriched["ingestion_timestamp"] = current_timestamp
        enriched["ingestion_date"] = execution_date_str
        enriched["data_source"] = "fakestoreapi"
        enriched_products.append(enriched)

    logging.info(f"✅ Enriched {len(enriched_products)} products with metadata")

    # Push enriched data to XCom
    context["ti"].xcom_push(
        key="enriched_products", value=json.dumps(enriched_products)
    )

    return len(enriched_products)


def load_to_s3(**context):
    """
    Load products data to S3 with date partitioning

    S3 Path: s3://bucket/raw/products/year=YYYY/month=MM/day=DD/products.json
    """
    # Get enriched data from XCom
    enriched_json = context["ti"].xcom_pull(
        key="enriched_products", task_ids="enrich_data"
    )

    execution_date_str = context["ti"].xcom_pull(
        key="execution_date_str", task_ids="get_execution_date"
    )

    products = json.loads(enriched_json)

    if len(products) == 0:
        logging.info("No data to upload. Skipping S3 load.")
        return 0

    # Convert to pretty JSON string
    json_content = json.dumps(products, indent=2)

    # Create S3 key with partitioning
    date_obj = datetime.strptime(execution_date_str, "%Y-%m-%d")
    year = date_obj.strftime("%Y")
    month = date_obj.strftime("%m")
    day = date_obj.strftime("%d")

    # S3 path with Hive-style partitioning
    s3_key = f"raw/products/year={year}/month={month}/day={day}/products.json"

    logging.info(f"Uploading to S3: s3://{S3_RAW_BUCKET}/{s3_key}")

    # Upload to S3 using Airflow S3Hook
    s3_hook = S3Hook(aws_conn_id="aws_default")

    s3_hook.load_string(
        string_data=json_content, key=s3_key, bucket_name=S3_RAW_BUCKET, replace=True
    )

    logging.info(f"✅ Successfully uploaded {len(products)} products to S3")
    logging.info(f"   S3 URI: s3://{S3_RAW_BUCKET}/{s3_key}")
    logging.info(f"   File size: {len(json_content)} bytes")

    # Push S3 location to XCom
    context["ti"].xcom_push(key="s3_key", value=s3_key)
    context["ti"].xcom_push(key="s3_uri", value=f"s3://{S3_RAW_BUCKET}/{s3_key}")

    return s3_key


def log_summary(**context):
    """
    Log summary of the ingestion process
    """
    execution_date_str = context["ti"].xcom_pull(
        key="execution_date_str", task_ids="get_execution_date"
    )

    product_count = context["ti"].xcom_pull(
        key="product_count", task_ids="fetch_products"
    )

    s3_uri = context["ti"].xcom_pull(key="s3_uri", task_ids="load_to_s3")

    logging.info("=" * 60)
    logging.info("API INGESTION SUMMARY")
    logging.info("=" * 60)
    logging.info(f"Execution Date: {execution_date_str}")
    logging.info(f"API Source: FakeStore API")
    logging.info(f"Products Fetched: {product_count}")
    logging.info(f"S3 Location: {s3_uri}")
    logging.info(f"Status: SUCCESS ✅")
    logging.info("=" * 60)

    return True


# ============================================
# DAG DEFINITION
# ============================================

with DAG(
    dag_id="ingest_api_products",
    default_args=default_args,
    description="Fetch products from FakeStore API and load to S3",
    schedule_interval="@daily",  # Run daily at 3 AM UTC
    start_date=datetime(2025, 10, 20),
    catchup=False,  # Don't backfill historical data
    max_active_runs=1,  # Only one run at a time
    tags=["ingestion", "api", "products", "rest"],
) as dag:
    # Task 1: Get execution date
    task_get_date = PythonOperator(
        task_id="get_execution_date",
        python_callable=get_execution_date,
        provide_context=True,
    )

    # Task 2: Fetch products from API
    task_fetch = PythonOperator(
        task_id="fetch_products",
        python_callable=fetch_products_from_api,
        provide_context=True,
    )

    # Task 3: Validate data
    task_validate = PythonOperator(
        task_id="validate_data",
        python_callable=validate_product_data,
        provide_context=True,
    )

    # Task 4: Enrich data with metadata
    task_enrich = PythonOperator(
        task_id="enrich_data",
        python_callable=enrich_product_data,
        provide_context=True,
    )

    # Task 5: Load to S3
    task_load = PythonOperator(
        task_id="load_to_s3",
        python_callable=load_to_s3,
        provide_context=True,
    )

    # Task 6: Log summary
    task_summary = PythonOperator(
        task_id="log_summary",
        python_callable=log_summary,
        provide_context=True,
    )

    # Define task dependencies
    (
        task_get_date
        >> task_fetch
        >> task_validate
        >> task_enrich
        >> task_load
        >> task_summary
    )


# ============================================
# DAG DOCUMENTATION
# ============================================

dag.doc_md = """
# FakeStore API Products Ingestion DAG

## Purpose
Fetch product catalog from FakeStore API and load to S3 raw data lake.

## Schedule
- **Frequency**: Daily at 3 AM UTC
- **Catchup**: Disabled (no historical backfill)
- **Max Active Runs**: 1 (prevents concurrent runs)

## Data Flow
1. **Fetch**: HTTP GET request to FakeStore API
2. **Validate**: Check data structure and required fields
3. **Enrich**: Add ingestion metadata (timestamp, date, source)
4. **Load**: Upload to S3 as JSON with Hive-style partitioning

## S3 Partitioning Strategy
```
s3://ecommerce-raw-data/raw/products/
  year=2025/
    month=10/
      day=28/
        products.json
```

## API Details
- **Endpoint**: https://fakestoreapi.com/products
- **Method**: GET
- **Response**: JSON array of products
- **Expected Count**: ~20 products

## Airflow Connections Required
- `aws_default`: AWS credentials for S3 access

## Data Schema
Each product contains:
- id: Product ID (integer)
- title: Product name (string)
- price: Product price (float)
- category: Product category (string)
- description: Product description (string)
- image: Product image URL (string)
- rating: Product rating object

Plus enriched fields:
- ingestion_timestamp: UTC timestamp
- ingestion_date: Execution date
- data_source: "fakestoreapi"

## Monitoring
- Check logs for API failures
- Monitor S3 bucket for daily files
- Review product counts (should be ~20)

## Troubleshooting
- API timeout: Normal, retries will handle
- Connection errors: Check internet connectivity
- S3 upload fails: Check AWS credentials
"""
