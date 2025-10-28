# Week 2, Day 3-4: PostgreSQL Ingestion DAG

## Overview

This guide covers setting up and testing the PostgreSQL orders ingestion DAG that extracts data from PostgreSQL and loads it to S3 with date partitioning.

## What We Built

### 1. PostgreSQL Ingestion DAG (`dags/ingest_postgres_orders.py`)

**Features:**
- ✅ Incremental extraction by date
- ✅ S3 Hive-style partitioning (year/month/day)
- ✅ Data validation checks
- ✅ Error handling with exponential backoff
- ✅ Comprehensive logging
- ✅ XCom for task communication

**DAG Structure:**
```
get_execution_date → extract_orders → validate_data → load_to_s3 → log_summary
```

### 2. Airflow Connections Setup (`scripts/setup_airflow_connections.py`)

**Connections Created:**
- `postgres_source` - PostgreSQL source database
- `aws_default` - AWS S3 credentials

---

## Prerequisites

### 1. Docker Services Running

```bash
# Check status
docker ps

# Should see all 7 containers running:
# - ecommerce-postgres-source
# - ecommerce-postgres-airflow
# - ecommerce-redis
# - ecommerce-airflow-webserver
# - ecommerce-airflow-scheduler
# - ecommerce-airflow-worker
# - ecommerce-airflow-triggerer
```

### 2. Data Loaded in PostgreSQL

```bash
# Verify orders exist
docker exec -it ecommerce-postgres-source psql -U ecommerce_user -d ecommerce -c "SELECT COUNT(*) FROM orders;"

# Should show 5000 orders
```

### 3. AWS Credentials Configured

Check `.env` file has:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_RAW_BUCKET=ecommerce-raw-data-bnf5etbn
```

---

## Step-by-Step Setup

### Step 1: Verify Airflow is Running

```bash
# Check Airflow webserver
docker logs ecommerce-airflow-webserver | tail -20

# Access Airflow UI
# Open browser: http://localhost:8081
# Login: admin / admin123
```

### Step 2: Set Up Airflow Connections

```bash
# Run connection setup script
python scripts/setup_airflow_connections.py
```

**Expected Output:**
```
==================================================
Airflow Connections Setup
==================================================
INFO - Creating PostgreSQL source connection...
INFO -    Connection 'postgres_source' doesn't exist (this is fine)
INFO - ✅ PostgreSQL connection created successfully
INFO - Creating AWS S3 connection...
INFO -    Connection 'aws_default' doesn't exist (this is fine)
INFO - ✅ AWS connection created successfully

Verifying connections...
Current Airflow Connections:
conn_id                | conn_type | description
=======================+==========+=============
aws_default            | aws       |
postgres_source        | postgres  |

✅ All connections set up successfully!

Next steps:
1. Open Airflow UI: http://localhost:8081
2. Check Admin > Connections to verify
3. Enable and trigger the DAG
```

### Step 3: Verify Connections in Airflow UI

1. Open Airflow UI: http://localhost:8081
2. Go to **Admin** → **Connections**
3. Verify you see:
   - `aws_default` (AWS type)
   - `postgres_source` (Postgres type)

**Screenshot locations:**
- AWS connection should show region: us-east-1
- PostgreSQL connection should show: postgres-source:5432/ecommerce

### Step 4: Check DAG is Loaded

1. In Airflow UI, go to **DAGs** page
2. Look for: `ingest_postgres_orders`
3. DAG should show with tags: `ingestion`, `postgres`, `orders`, `incremental`

**If DAG not visible:**
```bash
# Check for syntax errors
docker exec ecommerce-airflow-scheduler python -m py_compile /opt/airflow/dags/ingest_postgres_orders.py

# Check scheduler logs
docker logs ecommerce-airflow-scheduler | grep -i error

# Restart scheduler if needed
docker restart ecommerce-airflow-scheduler
```

---

## Testing the DAG

### Option 1: Manual Trigger (Recommended for Testing)

1. In Airflow UI, find `ingest_postgres_orders`
2. Click the **Play** button (▶) on the right
3. Select **Trigger DAG**
4. Click **Trigger**

### Option 2: Using Airflow CLI

```bash
# Trigger DAG manually
docker exec ecommerce-airflow-scheduler airflow dags trigger ingest_postgres_orders

# Check DAG run status
docker exec ecommerce-airflow-scheduler airflow dags list-runs -d ingest_postgres_orders
```

### Option 3: Test with Specific Date

```bash
# Trigger with specific execution date
docker exec ecommerce-airflow-scheduler airflow dags trigger ingest_postgres_orders \
  --exec-date "2025-10-28"
```

---

## Monitoring DAG Execution

### 1. Airflow UI Monitoring

**Graph View:**
1. Click on DAG name: `ingest_postgres_orders`
2. Click **Graph** tab
3. Watch tasks turn green as they complete:
   - `get_execution_date` → Green
   - `extract_orders` → Green
   - `validate_data` → Green
   - `load_to_s3` → Green
   - `log_summary` → Green

**Task Logs:**
1. Click any task box
2. Click **Log** button
3. Review detailed execution logs

### 2. Command Line Monitoring

```bash
# Watch scheduler logs
docker logs -f ecommerce-airflow-scheduler

# Watch worker logs
docker logs -f ecommerce-airflow-worker

# Check specific task log
docker exec ecommerce-airflow-scheduler airflow tasks logs ingest_postgres_orders extract_orders 2025-10-28
```

---

## Verifying Success

### 1. Check Task Completion

In Airflow UI, all tasks should show **green** (success).

### 2. Check S3 for Output

```bash
# Using AWS CLI
aws s3 ls s3://ecommerce-raw-data-bnf5etbn/raw/orders/ --recursive

# Expected output:
# raw/orders/year=2025/month=10/day=28/orders.csv
```

**Via Python:**
```python
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name='us-east-1'
)

bucket = os.getenv('S3_RAW_BUCKET')

# List objects
response = s3.list_objects_v2(Bucket=bucket, Prefix='raw/orders/')

if 'Contents' in response:
    print("Files in S3:")
    for obj in response['Contents']:
        print(f"  - {obj['Key']} ({obj['Size']} bytes)")
else:
    print("No files found")
```

### 3. Download and Inspect CSV

```python
import pandas as pd
import boto3
from io import StringIO

# Download from S3
s3 = boto3.client('s3')
bucket = 'ecommerce-raw-data-bnf5etbn'
key = 'raw/orders/year=2025/month=10/day=28/orders.csv'

obj = s3.get_object(Bucket=bucket, Key=key)
df = pd.read_csv(StringIO(obj['Body'].read().decode('utf-8')))

print(f"Records: {len(df)}")
print(f"Columns: {df.columns.tolist()}")
print(df.head())
```

### 4. Verify Data Quality

**Check XCom Values:**
1. In Airflow UI, go to DAG run
2. Click **XCom** tab
3. Verify:
   - `execution_date_str`: '2025-10-28'
   - `order_count`: number of orders
   - `s3_uri`: S3 location

**Check Logs:**
Look for summary in `log_summary` task:
```
==================================================
INGESTION SUMMARY
==================================================
Execution Date: 2025-10-28
Orders Extracted: 194
S3 Location: s3://ecommerce-raw-data-bnf5etbn/raw/orders/year=2025/month=10/day=28/orders.csv
Status: SUCCESS ✅
==================================================
```

---

## Troubleshooting

### Issue 1: DAG Not Showing in UI

**Problem:** DAG doesn't appear in Airflow UI

**Solution:**
```bash
# Check for Python syntax errors
docker exec ecommerce-airflow-scheduler python -c "import sys; sys.path.insert(0, '/opt/airflow/dags'); import ingest_postgres_orders"

# Check scheduler logs
docker logs ecommerce-airflow-scheduler | grep -A 5 -B 5 "ingest_postgres"

# Restart scheduler
docker restart ecommerce-airflow-scheduler

# Wait 30 seconds, then refresh UI
```

### Issue 2: Connection Not Found

**Error:** `Connection 'postgres_source' doesn't exist`

**Solution:**
```bash
# Re-run connection setup
python scripts/setup_airflow_connections.py

# Manually verify in Airflow UI
# Admin > Connections

# Or add manually via UI:
# Conn Id: postgres_source
# Conn Type: Postgres
# Host: postgres-source
# Schema: ecommerce
# Login: ecommerce_user
# Password: ecommerce_pass
# Port: 5432
```

### Issue 3: No Orders Found

**Warning:** `No orders found for date: 2025-10-28`

**This is NORMAL if:**
- No orders exist for that specific date in PostgreSQL
- You're testing with future dates

**Solution:**
```bash
# Check what dates have orders
docker exec -it ecommerce-postgres-source psql -U ecommerce_user -d ecommerce

SELECT DATE(order_date) as order_day, COUNT(*) 
FROM orders 
GROUP BY order_day 
ORDER BY order_day DESC 
LIMIT 10;

# Trigger DAG with a date that has orders
docker exec ecommerce-airflow-scheduler airflow dags trigger ingest_postgres_orders \
  --exec-date "2024-10-15"  # Use actual date from query above
```

### Issue 4: S3 Access Denied

**Error:** `An error occurred (AccessDenied) when calling the PutObject operation`

**Solution:**
```bash
# Test AWS credentials
aws s3 ls s3://ecommerce-raw-data-bnf5etbn/

# If fails, check .env file:
# 1. AWS_ACCESS_KEY_ID is correct
# 2. AWS_SECRET_ACCESS_KEY is correct
# 3. S3 bucket name matches Terraform output

# Re-run connection setup
python scripts/setup_airflow_connections.py

# Verify in AWS Console:
# IAM > Users > Your User > Permissions
# Should have S3 write access
```

### Issue 5: Task Fails with Timeout

**Error:** Task times out after 5 minutes

**Solution:**
```bash
# Check PostgreSQL is responsive
docker exec -it ecommerce-postgres-source psql -U ecommerce_user -d ecommerce -c "SELECT COUNT(*) FROM orders;"

# Check network connectivity
docker exec ecommerce-airflow-worker ping postgres-source -c 3

# Increase retry delay in DAG if needed
# Edit dags/ingest_postgres_orders.py:
# 'retry_delay': timedelta(minutes=10),
```

---

## Understanding the Data Flow

### 1. Extraction Logic

```python
# Query extracts orders for specific date
WHERE DATE(o.order_date) = '2025-10-28'
```

**Why this works:**
- Incremental loading (daily batches)
- Prevents re-processing old data
- Allows backfilling specific dates

### 2. S3 Partitioning Strategy

**Path Format:**
```
s3://bucket/raw/orders/year=YYYY/month=MM/day=DD/orders.csv
```

**Example:**
```
s3://ecommerce-raw-data-bnf5etbn/
  raw/
    orders/
      year=2023/
        month=10/
          day=28/
            orders.csv
          day=29/
            orders.csv
      year=2024/
        month=01/
          day=15/
            orders.csv
```

**Benefits:**
- Hive-compatible partitioning
- Efficient query pruning
- Easy to navigate
- Supports time-travel queries

### 3. XCom for Task Communication

```python
# Task 1 pushes data
context['ti'].xcom_push(key='orders_data', value=df.to_json())

# Task 2 pulls data
orders_json = context['ti'].xcom_pull(key='orders_data', task_ids='extract_orders')
```

**Why XCom:**
- Pass data between tasks
- No need for temporary files
- Built into Airflow
- Works across workers

---

## Performance Metrics

### Expected Performance

| Metric | Value |
|--------|-------|
| Extraction Time | 1-3 seconds |
| Validation Time | <1 second |
| S3 Upload Time | 2-5 seconds |
| Total DAG Duration | 5-15 seconds |
| Records per Run | 0-500 (varies by date) |

### Monitoring Queries

```sql
-- Orders per day (in PostgreSQL)
SELECT 
    DATE(order_date) as date,
    COUNT(*) as order_count,
    ROUND(AVG(order_total), 2) as avg_value
FROM orders
WHERE DATE(order_date) >= '2024-10-01'
GROUP BY date
ORDER BY date DESC
LIMIT 30;
```

---

## Next Steps

After PostgreSQL ingestion is working:

1. ✅ **Test with multiple dates**
   ```bash
   # Trigger for different dates
   docker exec ecommerce-airflow-scheduler airflow dags trigger ingest_postgres_orders --exec-date "2024-10-15"
   docker exec ecommerce-airflow-scheduler airflow dags trigger ingest_postgres_orders --exec-date "2024-10-16"
   ```

2. ✅ **Enable scheduled runs**
   - In Airflow UI, toggle DAG to "On"
   - Will run daily at 2 AM UTC

3. ✅ **Build API Ingestion DAG**
   - Switch to `feature/api-ingestion` branch
   - Create FakeStore API ingestion DAG

4. ✅ **Build Clickstream Ingestion DAG**
   - Switch to `feature/clickstream-ingestion` branch
   - Process event CSV files to S3

---

## Git Workflow

```bash
# Check status
git status

# Stage files
git add dags/ingest_postgres_orders.py
git add scripts/setup_airflow_connections.py
git add docs/week2/postgres-ingestion-guide.md

# Commit
git commit -m "feat: implement PostgreSQL orders ingestion DAG

- Add incremental extraction by order_date
- Implement S3 Hive-style partitioning (year/month/day)
- Add comprehensive data validation checks
- Include error handling with exponential backoff
- Add Airflow connections setup script
- Include detailed testing and troubleshooting guide

Data Flow:
- Extract orders from PostgreSQL (incremental by date)
- Validate data quality (nulls, types, business rules)
- Load to S3 with date partitioning
- Log comprehensive execution summary

Performance:
- Expected duration: 5-15 seconds per run
- Handles 0-500 orders per day
- Exponential backoff retry strategy"

# Push
git push origin feature/postgres-ingestion
```

---

## Success Criteria ✅

- [x] DAG file created with 5 tasks
- [x] Airflow connections setup script created
- [x] Documentation complete
- [ ] DAG visible in Airflow UI
- [ ] Connections verified in Admin panel
- [ ] DAG runs successfully (manual trigger)
- [ ] Data appears in S3 with correct partitioning
- [ ] All validation checks pass
- [ ] Git commit and push

---

**Last Updated:** Week 2, Day 3  
**Status:** PostgreSQL Ingestion DAG Complete  
**Next:** API Ingestion DAG
