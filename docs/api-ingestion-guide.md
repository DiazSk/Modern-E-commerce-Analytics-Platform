# API Ingestion DAG - Testing Guide

## Overview

This DAG fetches product catalog from FakeStore API and stores it in S3.

---

## Quick Start

### Step 1: Verify DAG Loaded

1. Open Airflow UI: http://localhost:8081
2. Find DAG: `ingest_api_products`
3. Status: Should be ⚪ (paused)

---

### Step 2: Test the DAG

**Manual Trigger:**

1. Click on `ingest_api_products`
2. Click ▶️ **Trigger DAG**
3. Wait ~30 seconds

**Expected Tasks:**
```
get_execution_date → fetch_products → validate_data → enrich_data → load_to_s3 → log_summary
```

---

### Step 3: Check Logs

Click on **`fetch_products`** task → **Log**

**Expected Output:**
```
INFO - Fetching products from: https://fakestoreapi.com/products
INFO - ✅ Successfully fetched 20 products from API
INFO -    Sample product: Fjallraven - Foldsack No. 1 Backpack
INFO -    Categories: {'electronics', 'jewelery', 'men\'s clothing', 'women\'s clothing'}
```

---

### Step 4: Verify S3 Upload

```bash
# List files
aws s3 ls s3://ecommerce-raw-data-bnf5etbn/raw/products/ --recursive

# Expected output:
# raw/products/year=2025/month=10/day=28/products.json
```

---

### Step 5: Download and Inspect

```bash
# Download JSON file
aws s3 cp s3://ecommerce-raw-data-bnf5etbn/raw/products/year=2025/month=10/day=28/products.json test_products.json

# Pretty print JSON
python -m json.tool test_products.json | head -50
```

---

## Expected Data Structure

```json
[
  {
    "id": 1,
    "title": "Fjallraven - Foldsack No. 1 Backpack, Fits 15 Laptops",
    "price": 109.95,
    "description": "Your perfect pack for everyday use...",
    "category": "men's clothing",
    "image": "https://fakestoreapi.com/img/81fPKd-2AYL._AC_SL1500_.jpg",
    "rating": {
      "rate": 3.9,
      "count": 120
    },
    "ingestion_timestamp": "2025-10-28T15:30:45.123456",
    "ingestion_date": "2025-10-28",
    "data_source": "fakestoreapi"
  },
  ...
]
```

---

## Verification Checklist

- [ ] DAG visible in Airflow UI
- [ ] Manual trigger successful
- [ ] All 6 tasks completed (green)
- [ ] Logs show "✅ Successfully fetched 20 products"
- [ ] S3 file exists with correct partitioning
- [ ] JSON file downloadable and valid
- [ ] Contains ~20 products with all fields
- [ ] Enriched fields present (ingestion_timestamp, etc.)

---

## Troubleshooting

### Issue 1: API Request Failed

**Error:** `requests.exceptions.ConnectionError`

**Solution:**
- Check internet connectivity
- API might be temporarily down (wait and retry)
- Verify URL: https://fakestoreapi.com/products

### Issue 2: JSON Parsing Failed

**Error:** `json.JSONDecodeError`

**Solution:**
- API response might be malformed
- Check task logs for actual response
- Retry - usually transient issue

### Issue 3: S3 Upload Failed

**Error:** `Access Denied` or `NoSuchBucket`

**Solution:**
- Verify AWS connection in Airflow
- Check bucket name in .env file
- Verify IAM permissions

---

## Testing Different Scenarios

### Test 1: Full Product Catalog
```bash
# Trigger normally - gets all products
```

### Test 2: API Endpoint Variations
You can modify the DAG to test:
- Single product: `https://fakestoreapi.com/products/1`
- Limit products: `https://fakestoreapi.com/products?limit=5`
- By category: `https://fakestoreapi.com/products/category/electronics`

### Test 3: Error Handling
Temporarily change API URL to invalid one to test retry logic.

---

## Data Quality Checks

```python
import json
import pandas as pd

# Load JSON
with open('test_products.json') as f:
    products = json.load(f)

# Check count
print(f"Total products: {len(products)}")

# Check required fields
required = ['id', 'title', 'price', 'category', 'description', 'image']
for p in products:
    missing = [f for f in required if f not in p]
    if missing:
        print(f"Product {p['id']} missing: {missing}")

# Check enriched fields
enriched = ['ingestion_timestamp', 'ingestion_date', 'data_source']
for p in products:
    missing = [f for f in enriched if f not in p]
    if missing:
        print(f"Product {p['id']} missing enrichment: {missing}")

# Price statistics
df = pd.DataFrame(products)
print(f"\nPrice statistics:")
print(df['price'].describe())

# Categories
print(f"\nCategories: {df['category'].unique().tolist()}")
print(f"Products per category:\n{df['category'].value_counts()}")
```

---

## Performance Metrics

**Expected Execution Time:**
- get_execution_date: < 1 second
- fetch_products: 5-15 seconds (API call)
- validate_data: 1-2 seconds
- enrich_data: 1-2 seconds
- load_to_s3: 3-5 seconds
- log_summary: < 1 second

**Total: ~15-30 seconds**

**Data Volume:**
- Products: ~20
- JSON file size: ~20-30 KB

---

## Success Criteria ✅

API Ingestion DAG complete when:

- [x] DAG file created and valid
- [ ] DAG visible in Airflow UI
- [ ] Manual trigger successful
- [ ] All tasks completed (green)
- [ ] Products fetched from API
- [ ] Data validation passed
- [ ] JSON file in S3 with partitioning
- [ ] File contains ~20 products
- [ ] Enriched fields present
- [ ] Git committed and pushed

---

## Next Steps

After API ingestion is working:

1. **Enable Schedule** (optional)
   - Toggle DAG to active
   - Will run daily at 3 AM UTC

2. **Create Clickstream Ingestion DAG**
   - Last ingestion pipeline
   - CSV file processing
   - Batch upload to S3

3. **Week 2 Completion**
   - All 3 ingestion DAGs working
   - S3 data lake populated
   - Ready for Week 3 (dbt transformation)

---

**Last Updated:** Week 2, Day 5  
**Status:** API Ingestion DAG Created  
**Next:** Test and Verify
