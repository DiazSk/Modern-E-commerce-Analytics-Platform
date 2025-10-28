# Airflow Setup Guide - Week 2

## Overview

This guide covers setting up Airflow connections and testing the PostgreSQL ingestion DAG.

## Prerequisites

✅ Docker services running  
✅ Data loaded in PostgreSQL  
✅ AWS S3 buckets created  
✅ .env file configured  

---

## Step 1: Access Airflow Web UI

### Start Airflow Services

```bash
# Start all services
docker-compose up -d

# Wait 30 seconds for services to initialize
# Check if all services are healthy
docker ps
```

### Access UI

1. Open browser: **http://localhost:8081**
2. Login credentials:
   - Username: `admin`
   - Password: `admin123`

---

## Step 2: Create Airflow Connections

### Connection 1: PostgreSQL Source Database

**Via UI:**

1. Go to **Admin → Connections**
2. Click **+** (Add Connection)
3. Fill in details:

```
Connection Id: postgres_source
Connection Type: Postgres
Host: postgres-source
Schema: ecommerce
Login: ecommerce_user
Password: ecommerce_pass
Port: 5432
```

**Important Notes:**
- Use `postgres-source` as host (Docker service name)
- Port is `5432` (internal Docker network port, not 5433)
- Test connection before saving

**Via CLI (Alternative):**

```bash
docker exec -it ecommerce-airflow-webserver bash

airflow connections add 'postgres_source' \
    --conn-type 'postgres' \
    --conn-host 'postgres-source' \
    --conn-schema 'ecommerce' \
    --conn-login 'ecommerce_user' \
    --conn-password 'ecommerce_pass' \
    --conn-port 5432

exit
```

### Connection 2: AWS S3

**Via UI:**

1. Go to **Admin → Connections**
2. Click **+** (Add Connection)
3. Fill in details:

```
Connection Id: aws_default
Connection Type: Amazon Web Services
AWS Access Key ID: [Your AWS Access Key]
AWS Secret Access Key: [Your AWS Secret Key]
Region Name: us-east-1
```

**Get AWS Credentials:**
1. AWS Console → IAM → Users → Your User
2. Security Credentials → Create Access Key
3. Copy both Access Key ID and Secret Access Key

**Via CLI (Alternative):**

```bash
docker exec -it ecommerce-airflow-webserver bash

airflow connections add 'aws_default' \
    --conn-type 'aws' \
    --conn-login 'YOUR_AWS_ACCESS_KEY_ID' \
    --conn-password 'YOUR_AWS_SECRET_KEY' \
    --conn-extra '{"region_name": "us-east-1"}'

exit
```

---

## Step 3: Verify DAG Loaded

### Check DAGs List

1. Go to **DAGs** page in Airflow UI
2. Look for: `ingest_postgres_orders`
3. Status should show: ⚪ (paused)

**If DAG not visible:**

```bash
# Check logs
docker logs ecommerce-airflow-scheduler

# Verify DAG file syntax
docker exec -it ecommerce-airflow-webserver bash
python /opt/airflow/dags/ingest_postgres_orders.py
exit
```

### Check DAG Details

1. Click on `ingest_postgres_orders`
2. View:
   - **Graph**: Task dependencies
   - **Code**: DAG source code
   - **Details**: Schedule and configuration

---

## Step 4: Test the DAG

### Manual Trigger (Recommended for First Run)

1. Navigate to `ingest_postgres_orders` DAG
2. Click **▶️ Trigger DAG**
3. Optionally customize execution date (use date with orders)
4. Click **Trigger**

### Monitor Execution

1. Click on the running DAG instance
2. View **Graph** to see task progress:
   - 🟢 Green: Success
   - 🔴 Red: Failed
   - 🟡 Yellow: Running
   - ⚪ Gray: Not started

3. Click individual tasks to view logs:
   - Click task box → **Log**
   - Review extraction stats
   - Check validation results
   - Verify S3 upload

### Expected Log Output

**Task: extract_orders**
```
INFO - Extracting orders for date: 2025-10-28
INFO - ✅ Extracted 194 orders from PostgreSQL
INFO -    Order ID range: 4807 to 5000
INFO -    Order total sum: $25911.04
INFO -    Order statuses: {'completed': 146, 'pending': 19, ...}
```

**Task: validate_data**
```
INFO - ==================================================
INFO - DATA VALIDATION
INFO - ==================================================
INFO - ✅ All required fields present
INFO - ✅ No null values in critical fields
INFO - ✅ All order totals are positive
INFO - 🎉 Data validation passed!
```

**Task: load_to_s3**
```
INFO - Uploading to S3: s3://ecommerce-raw-data-xxx/raw/orders/year=2025/month=10/day=28/orders.csv
INFO - ✅ Successfully uploaded 194 orders to S3
INFO -    S3 URI: s3://ecommerce-raw-data-xxx/raw/orders/year=2025/month=10/day=28/orders.csv
```

---

## Step 5: Verify S3 Upload

### Via AWS Console

1. Go to **S3** service
2. Open bucket: `ecommerce-raw-data-xxx`
3. Navigate to: `raw/orders/year=2025/month=10/day=28/`
4. Verify `orders.csv` exists

### Via AWS CLI

```bash
# List files
aws s3 ls s3://ecommerce-raw-data-xxx/raw/orders/ --recursive

# Download and preview
aws s3 cp s3://ecommerce-raw-data-xxx/raw/orders/year=2025/month=10/day=28/orders.csv - | head -n 10
```

### Verify CSV Content

```bash
# Download file
aws s3 cp s3://ecommerce-raw-data-xxx/raw/orders/year=2025/month=10/day=28/orders.csv orders_test.csv

# Check in Python
python
>>> import pandas as pd
>>> df = pd.read_csv('orders_test.csv')
>>> print(df.head())
>>> print(f"Shape: {df.shape}")
>>> print(f"Columns: {df.columns.tolist()}")
```

---

## Step 6: Enable Scheduled Runs

### Unpause DAG

1. In Airflow UI, find `ingest_postgres_orders`
2. Toggle switch from ⚪ (paused) to 🟢 (active)
3. DAG will now run daily at 2 AM UTC

### Monitor Schedule

- **Next Run**: Check "Next Run" column
- **Last Run**: Check "Last Run" column
- **Recent Runs**: Click DAG → "Recent Runs"

---

## Troubleshooting

### Issue 1: Connection Test Failed (PostgreSQL)

**Error:** `could not connect to server: Connection refused`

**Solutions:**

1. Verify Docker network:
```bash
docker network inspect ecommerce-network
```

2. Check PostgreSQL service:
```bash
docker logs ecommerce-postgres-source
```

3. Use correct host: `postgres-source` (not `localhost`)
4. Use internal port: `5432` (not `5433`)

### Issue 2: AWS Connection Failed

**Error:** `Unable to locate credentials`

**Solutions:**

1. Verify AWS credentials in connection
2. Test credentials locally:
```bash
aws s3 ls --profile default
```

3. Check IAM permissions (need `s3:PutObject`, `s3:GetObject`)

### Issue 3: DAG Not Appearing

**Error:** DAG not visible in UI

**Solutions:**

1. Check syntax:
```bash
docker exec -it ecommerce-airflow-webserver python /opt/airflow/dags/ingest_postgres_orders.py
```

2. Check scheduler logs:
```bash
docker logs ecommerce-airflow-scheduler | tail -50
```

3. Refresh DAGs:
   - Wait 30 seconds (default parsing interval)
   - Or restart scheduler: `docker restart ecommerce-airflow-scheduler`

### Issue 4: Task Failed - No Orders Found

**Error:** `No orders found for date: YYYY-MM-DD`

**Not an Error!** This is normal if:
- Testing with future dates
- Testing with dates outside data range (Oct 2023 - Oct 2025)

**Solution:** Trigger with execution date that has orders:
- Use dates from: **2023-10-29** to **2025-10-28**
- Check order count first:
```sql
SELECT DATE(order_date), COUNT(*) 
FROM orders 
GROUP BY DATE(order_date) 
ORDER BY DATE(order_date) DESC 
LIMIT 10;
```

### Issue 5: S3 Permission Denied

**Error:** `Access Denied`

**Solutions:**

1. Verify S3 bucket name matches in:
   - `.env` file
   - DAG configuration
   - AWS connection

2. Check IAM policy includes:
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:PutObject",
    "s3:GetObject",
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::ecommerce-raw-data-xxx",
    "arn:aws:s3:::ecommerce-raw-data-xxx/*"
  ]
}
```

---

## Best Practices

### 1. Connection Security

✅ **DO:**
- Store credentials in Airflow Connections (encrypted)
- Use IAM roles in production (not access keys)
- Rotate AWS keys regularly

❌ **DON'T:**
- Hardcode credentials in DAG code
- Commit credentials to Git
- Share access keys in plain text

### 2. Testing Strategy

✅ **DO:**
- Test manually before enabling schedule
- Verify data in S3 after each run
- Monitor first few scheduled runs
- Test with different execution dates

❌ **DON'T:**
- Enable schedule without testing
- Ignore failed tasks
- Let errors accumulate

### 3. Monitoring

✅ **DO:**
- Check Airflow UI daily for failures
- Set up email alerts (already configured in DAG)
- Review logs for data quality issues
- Monitor S3 storage costs

❌ **DON'T:**
- Assume everything works without checking
- Ignore warnings in logs
- Let failed DAGs remain unresolved

---

## Quick Reference Commands

### Airflow CLI Commands

```bash
# List all connections
docker exec -it ecommerce-airflow-webserver airflow connections list

# Test DAG syntax
docker exec -it ecommerce-airflow-webserver python /opt/airflow/dags/ingest_postgres_orders.py

# List DAGs
docker exec -it ecommerce-airflow-webserver airflow dags list

# Trigger DAG manually
docker exec -it ecommerce-airflow-webserver airflow dags trigger ingest_postgres_orders

# View DAG runs
docker exec -it ecommerce-airflow-webserver airflow dags list-runs -d ingest_postgres_orders

# View task logs
docker exec -it ecommerce-airflow-webserver airflow tasks logs ingest_postgres_orders extract_orders 2025-10-28
```

### Docker Commands

```bash
# View all services
docker ps

# Restart Airflow scheduler
docker restart ecommerce-airflow-scheduler

# View scheduler logs
docker logs ecommerce-airflow-scheduler --tail 100 --follow

# View webserver logs
docker logs ecommerce-airflow-webserver --tail 100 --follow

# Access Airflow container
docker exec -it ecommerce-airflow-webserver bash
```

### AWS CLI Commands

```bash
# List S3 buckets
aws s3 ls

# List files in orders partition
aws s3 ls s3://ecommerce-raw-data-xxx/raw/orders/ --recursive --human-readable

# Download specific file
aws s3 cp s3://ecommerce-raw-data-xxx/raw/orders/year=2025/month=10/day=28/orders.csv ./

# Check file size
aws s3 ls s3://ecommerce-raw-data-xxx/raw/orders/year=2025/month=10/day=28/ --summarize
```

---

## Success Criteria ✅

After completing this guide, you should have:

- [x] Airflow UI accessible
- [x] PostgreSQL connection working
- [x] AWS connection configured
- [x] DAG visible in UI
- [x] Manual trigger successful
- [x] All 5 tasks completed (green)
- [x] Data validated successfully
- [x] CSV file in S3 with correct partitioning
- [x] Log output showing order counts
- [x] DAG schedule enabled (optional)

---

## Next Steps

After PostgreSQL ingestion is working:

1. **Create API Ingestion DAG** (`feature/api-ingestion`)
   - Fetch products from FakeStore API
   - Save JSON to S3

2. **Create Clickstream Ingestion DAG** (`feature/clickstream-ingestion`)
   - Read event CSV files
   - Batch upload to S3

3. **S3 Testing & Validation** (`feature/s3-testing`)
   - Verify partitioning strategy
   - Data quality checks
   - Performance testing

---

**Last Updated:** Week 2, Day 3  
**Status:** PostgreSQL Ingestion Setup  
**Next:** Test DAG and Verify S3 Upload
