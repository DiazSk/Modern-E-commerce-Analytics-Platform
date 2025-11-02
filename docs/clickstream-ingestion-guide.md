# Clickstream Ingestion DAG - Setup & Testing Guide

## Overview

This DAG processes 50,000 clickstream events from CSV and uploads them to S3 with date partitioning.

---

## Prerequisites

### CSV File Must Be Accessible to Airflow

The DAG reads from: `/opt/airflow/data/generated/clickstream_events.csv`

**Copy file to Airflow container:**

```bash
# Create directory in container
docker exec -it ecommerce-airflow-webserver mkdir -p /opt/airflow/data/generated

# Copy CSV file
docker cp data/generated/clickstream_events.csv ecommerce-airflow-webserver:/opt/airflow/data/generated/

# Verify
docker exec -it ecommerce-airflow-webserver ls -lh /opt/airflow/data/generated/
```

---

## Quick Start

### Step 1: Copy CSV to Container

```bash
# From project root
docker exec -it ecommerce-airflow-webserver mkdir -p /opt/airflow/data/generated
docker cp data/generated/clickstream_events.csv ecommerce-airflow-webserver:/opt/airflow/data/generated/

# Verify file exists
docker exec -it ecommerce-airflow-webserver ls -lh /opt/airflow/data/generated/clickstream_events.csv
```

### Step 2: Verify DAG Loaded

1. Open Airflow UI: http://localhost:8081
2. Find: `ingest_clickstream_events`
3. Status: ⚪ (paused)

### Step 3: Manual Trigger

1. Click DAG name
2. Click ▶️ **Trigger DAG**
3. Wait ~1-2 minutes (processing 50K events)

### Step 4: Monitor Progress

**Expected Tasks:**
```
get_execution_date → read_events → validate_data → upload_to_s3 → log_summary
```

**Check Logs (upload_to_s3 task):**
```
INFO - Partitioning 50000 events into X date partitions
INFO -    Uploading XXX events to: s3://.../year=2023/month=10/day=29/events.csv
INFO -    Uploading XXX events to: s3://.../year=2023/month=11/day=15/events.csv
...
INFO - ✅ Successfully uploaded X partitions to S3
```

### Step 5: Verify S3 Upload

```bash
# List all clickstream partitions
aws s3 ls s3://ecommerce-raw-data-bnf5etbn/raw/clickstream/ --recursive

# Expected output: Multiple files across dates
# raw/clickstream/year=2023/month=10/day=29/events.csv
# raw/clickstream/year=2023/month=11/day=15/events.csv
# ...
# raw/clickstream/year=2025/month=10/day=28/events.csv
```

---

## Expected Results

### Event Distribution (50,000 total)

**By Event Type:**
- page_view: ~30,000 (60%)
- add_to_cart: ~7,500 (15%)
- search: ~6,000 (12%)
- purchase: ~4,000 (8%)
- remove_from_cart: ~2,500 (5%)

**By Device Type:**
- mobile: ~32,500 (65%)
- desktop: ~15,000 (30%)
- tablet: ~2,500 (5%)

**Date Range:**
- From: ~September 2025 (30 days before current)
- To: October 28, 2025

**Partitions Created:**
- Approximately 30-40 date partitions
- Events distributed across 2 months

---

## Verification Steps

### Check File Uploaded

```bash
# Count partitions
aws s3 ls s3://ecommerce-raw-data-bnf5etbn/raw/clickstream/ --recursive | wc -l

# Download sample file
aws s3 cp s3://ecommerce-raw-data-bnf5etbn/raw/clickstream/year=2025/month=10/day=28/events.csv test_clickstream.csv

# Check content
head -n 5 test_clickstream.csv
```

### Validate Data Quality

```python
import pandas as pd

# Load sample file
df = pd.read_csv('test_clickstream.csv')

print(f"Shape: {df.shape}")
print(f"\nColumns: {df.columns.tolist()}")
print(f"\nEvent types: {df['event_type'].value_counts()}")
print(f"Device types: {df['device_type'].value_counts()}")
print(f"\nSample events:")
print(df.head())
```

---

## S3 Data Lake - Complete Structure

After this DAG completes:

```
ecommerce-raw-data-bnf5etbn/
└── raw/
    ├── orders/              # PostgreSQL (10-15 orders/day)
    │   └── year=2025/
    │       └── month=10/
    │           ├── day=27/
    │           │   └── orders.csv
    │           └── day=28/
    │               └── orders.csv
    │
    ├── products/            # API (20 products/day)
    │   └── year=2025/
    │       └── month=10/
    │           ├── day=27/
    │           │   └── products.json
    │           └── day=28/
    │               └── products.json
    │
    └── clickstream/         # Events (1K-2K events/day)
        └── year=2023/
            └── month=10/
                └── day=29/
                    └── events.csv
        └── year=2024/
            ...
        └── year=2025/
            └── month=09/
                ├── day=28/
                │   └── events.csv
                └── day=29/
                    └── events.csv
            └── month=10/
                ├── day=01/
                │   └── events.csv
                ...
                └── day=28/
                    └── events.csv
```

---

## Troubleshooting

### Issue 1: File Not Found

**Error:** `FileNotFoundError: /opt/airflow/data/generated/clickstream_events.csv`

**Solution:**
```bash
# Copy file to container
docker cp data/generated/clickstream_events.csv ecommerce-airflow-webserver:/opt/airflow/data/generated/

# Verify
docker exec -it ecommerce-airflow-webserver ls /opt/airflow/data/generated/
```

### Issue 2: Memory Error (Large File)

**Error:** `MemoryError` when processing 50K events

**Solution:**
- Normal for large CSV files
- DAG processes in batches by date
- If issue persists, increase Docker memory limit

### Issue 3: S3 Upload Timeout

**Error:** Upload takes too long

**Solution:**
- Normal for 30-40 files being uploaded
- Each partition uploads separately
- Total time: 1-2 minutes expected

### Issue 4: Empty Partitions

**Error:** Some date partitions are empty

**Solution:**
- Normal - not all dates have events
- Data spans 60+ days but events distributed unevenly
- This is realistic data distribution

---

## Performance Metrics

**Execution Time:**
- read_events: 10-15 seconds (reading 50K rows)
- validate_data: 5-10 seconds
- upload_to_s3: 30-60 seconds (30-40 files)
- **Total: ~1-2 minutes**

**Data Volume:**
- Total events: 50,000
- Partitions: 30-40 date partitions
- Avg events per partition: ~1,200-1,700
- File sizes: 100-200 KB per partition

---

## Post-Ingestion Cleanup (Optional)

After successful S3 upload, you can optionally remove the CSV from container to save space:

```bash
# Remove file (after confirming S3 upload)
docker exec -it ecommerce-airflow-webserver rm /opt/airflow/data/generated/clickstream_events.csv

# Note: DAG will skip processing on future runs when file not found
```

---

## Week 2 Completion Checklist

After this DAG completes:

- [ ] CSV copied to Airflow container
- [ ] DAG visible in UI
- [ ] Manual trigger successful
- [ ] All 5 tasks completed (green)
- [ ] Logs show 50K events processed
- [ ] 30-40 S3 partitions created
- [ ] Sample file downloaded and verified
- [ ] Git committed and pushed

---

## Week 2 Tag

After all three ingestion DAGs are complete:

```bash
git checkout develop

git tag -a v0.2-week2-complete -m "Week 2 Complete: Data Generation & Ingestion

Accomplishments:
- Synthetic data generation (1K customers, 5K orders, 50K events)
- 3 Airflow DAGs (PostgreSQL, API, Clickstream)
- S3 data lake with Hive-style partitioning
- Comprehensive data validation
- Production-ready error handling

Data Pipeline:
- PostgreSQL → CSV (orders, incremental)
- FakeStore API → JSON (products, daily snapshot)
- CSV Batch → CSV (clickstream events, date partitioned)

S3 Structure:
- raw/orders/ (5K orders across 2 days)
- raw/products/ (20 products across 2 days)
- raw/clickstream/ (50K events across 30-40 days)

Next: Week 3 - dbt Transformation Layer"

git push origin v0.2-week2-complete
```

---

**Last Updated:** Week 2, Day 6-7  
**Status:** Clickstream Ingestion DAG Created  
**Next:** Test, Verify, Complete Week 2
