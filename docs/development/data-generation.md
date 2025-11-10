# Week 2 - Data Generation Guide

## Overview

This guide covers the data generation and loading process for Week 2 of the Modern E-Commerce Analytics Platform project.

## Generated Data Summary

| Dataset | Records | Description |
|---------|---------|-------------|
| **Customers** | 1,000 | Customer profiles with SCD Type 2 segments |
| **Orders** | 5,000 | E-commerce transactions |
| **Order Items** | ~12,500 | Line items (avg 2.5 items/order) |
| **Clickstream Events** | 50,000 | User behavior tracking |

## Prerequisites

### 1. Docker Services Running

Ensure PostgreSQL source database is running:

```bash
# Start all services
docker-compose up -d

# Check services status
docker ps

# You should see:
# - ecommerce-postgres-source (port 5433)
# - ecommerce-postgres-airflow (port 5434)
# - ecommerce-redis
# - ecommerce-airflow-webserver
# - ecommerce-airflow-scheduler
# - ecommerce-airflow-worker
# - ecommerce-airflow-triggerer
```

### 2. Python Environment

Activate virtual environment:

```bash
# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### 3. Environment Variables

Ensure `.env` file has correct PostgreSQL credentials:

```env
POSTGRES_SOURCE_HOST=localhost
POSTGRES_SOURCE_PORT=5433
POSTGRES_SOURCE_USER=ecommerce_user
POSTGRES_SOURCE_PASSWORD=ecommerce_pass
POSTGRES_SOURCE_DB=ecommerce
```

## Step-by-Step Execution

### Step 1: Generate Data

Generate synthetic CSV files:

```bash
python scripts/generate_data.py
```

**Expected Output:**
```
==================================================
Starting Data Generation Process
==================================================
INFO - Generating 1000 customers...
INFO - ✅ Generated 1000 customers
INFO -    Segment distribution: {'bronze': 500, 'silver': 300, 'gold': 150, 'platinum': 50}
INFO - Generating 5000 orders...
INFO - ✅ Generated 5000 orders
INFO -    Status distribution: {'completed': 3750, 'pending': 500, ...}
INFO - Generating order items for 5000 orders...
INFO - ✅ Generated 12500 order items
INFO - Generating 50000 clickstream events...
INFO - ✅ Generated 50000 clickstream events
INFO - 💾 Saved: data/generated/customers.csv
INFO - 💾 Saved: data/generated/orders.csv
INFO - 💾 Saved: data/generated/order_items.csv
INFO - 💾 Saved: data/generated/clickstream_events.csv
==================================================
DATA GENERATION SUMMARY
==================================================
✅ Customers: 1,000
✅ Orders: 5,000
✅ Order Items: 12,500
✅ Clickstream Events: 50,000
📁 Output Directory: C:\...\data\generated
==================================================
🎉 Data generation completed successfully!
```

**Generated Files:**
- `data/generated/customers.csv` (~150 KB)
- `data/generated/orders.csv` (~500 KB)
- `data/generated/order_items.csv` (~300 KB)
- `data/generated/clickstream_events.csv` (~8 MB)

### Step 2: Verify CSV Files

Quick inspection:

```bash
# Windows PowerShell
Get-Content data\generated\customers.csv | Select-Object -First 5

# Mac/Linux
head -n 5 data/generated/customers.csv
```

Or use Python:

```python
import pandas as pd

# Load and preview
df = pd.read_csv('data/generated/customers.csv')
print(df.head())
print(f"\nShape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
```

### Step 3: Load Data into PostgreSQL

Load CSV data into source database:

```bash
python scripts/load_data.py
```

**Expected Output:**
```
==================================================
Starting Data Loading Process
==================================================
INFO - ✅ Connected to PostgreSQL database
INFO - Loading customers from data\generated\customers.csv...
INFO -   Truncated existing customers table
INFO - ✅ Loaded 1,000 customers
INFO - Loading orders from data\generated\orders.csv...
INFO -   Truncated existing orders table
INFO - ✅ Loaded 5,000 orders
INFO - Loading order items from data\generated\order_items.csv...
INFO -   Truncated existing order_items table
INFO - ✅ Loaded 12,500 order items
==================================================
DATA VALIDATION
==================================================
✓ Customers: 1,000
✓ Orders: 5,000
✓ Order Items: 12,500
✓ Orphan orders (should be 0): 0
✓ Invalid order totals (should be 0): 0
✓ Order date range: 2023-10-28 to 2025-10-28
Sample Order with Customer:
  Order #5000: John Smith - $156.78 - completed
  ...
==================================================
🎉 Data loading completed successfully!
```

### Step 4: Verify in PostgreSQL

Connect to database and verify:

```bash
# Using docker exec
docker exec -it ecommerce-postgres-source psql -U ecommerce_user -d ecommerce
```

Run validation queries:

```sql
-- Check record counts
SELECT 'customers' AS table_name, COUNT(*) FROM customers
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items;

-- Customer segment distribution
SELECT customer_segment, COUNT(*) as count
FROM customers
WHERE is_current = TRUE
GROUP BY customer_segment
ORDER BY count DESC;

-- Orders by status
SELECT order_status, COUNT(*) as count
FROM orders
GROUP BY order_status
ORDER BY count DESC;

-- Sample order with items
SELECT
    o.order_id,
    c.first_name || ' ' || c.last_name AS customer,
    o.order_date,
    o.order_total,
    COUNT(oi.order_item_id) AS num_items
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id, customer, o.order_date, o.order_total
ORDER BY o.order_date DESC
LIMIT 10;

-- Exit psql
\q
```

## Data Quality Checks

### Automated Checks (in load_data.py)

✅ **Referential Integrity:**
- All orders have valid customer_id references
- All order_items have valid order_id references

✅ **Data Validity:**
- No negative order totals
- No zero quantities in order items
- All required fields populated

✅ **Uniqueness:**
- Customer emails are unique
- No duplicate order IDs

### Manual Verification

```python
import pandas as pd

# Load data
customers = pd.read_csv('data/generated/customers.csv')
orders = pd.read_csv('data/generated/orders.csv')
items = pd.read_csv('data/generated/order_items.csv')
events = pd.read_csv('data/generated/clickstream_events.csv')

# Basic statistics
print("Customers:")
print(f"  Total: {len(customers)}")
print(f"  Unique emails: {customers['email'].nunique()}")
print(f"  Segment distribution:\n{customers['customer_segment'].value_counts()}")

print("\nOrders:")
print(f"  Total: {len(orders)}")
print(f"  Date range: {orders['order_date'].min()} to {orders['order_date'].max()}")
print(f"  Avg order value: ${orders['order_total'].mean():.2f}")
print(f"  Status distribution:\n{orders['order_status'].value_counts()}")

print("\nOrder Items:")
print(f"  Total: {len(items)}")
print(f"  Avg items per order: {len(items) / len(orders):.2f}")
print(f"  Unique products: {items['product_id'].nunique()}")

print("\nClickstream Events:")
print(f"  Total: {len(events)}")
print(f"  Event types:\n{events['event_type'].value_counts()}")
print(f"  Device distribution:\n{events['device_type'].value_counts()}")
```

## Troubleshooting

### Issue: Database Connection Failed

**Error:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
```bash
# Check if PostgreSQL container is running
docker ps | grep postgres-source

# If not running, start it
docker-compose up -d postgres-source

# Check logs
docker logs ecommerce-postgres-source

# Verify port 5433 is available
netstat -an | grep 5433
```

### Issue: CSV Files Not Found

**Error:** `FileNotFoundError: data/generated/customers.csv`

**Solution:**
```bash
# Create directory
mkdir -p data/generated

# Re-run generation
python scripts/generate_data.py
```

### Issue: Duplicate Key Error

**Error:** `psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint`

**Solution:**
```bash
# The load_data.py script uses TRUNCATE, but if that fails:

# Connect to database
docker exec -it ecommerce-postgres-source psql -U ecommerce_user -d ecommerce

# Manually truncate
TRUNCATE TABLE order_items, orders, customers CASCADE;

# Exit and retry
\q
python scripts/load_data.py
```

### Issue: Permission Denied

**Error:** `psycopg2.errors.InsufficientPrivilege`

**Solution:**
```sql
-- Connect as postgres superuser
docker exec -it ecommerce-postgres-source psql -U postgres

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ecommerce_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ecommerce_user;

-- Exit
\q
```

## Data Characteristics

### Customer Data

**Segment Distribution** (realistic hierarchy):
- Bronze: 50% (500 customers) - Entry-level
- Silver: 30% (300 customers) - Mid-tier
- Gold: 15% (150 customers) - Premium
- Platinum: 5% (50 customers) - VIP

**SCD Type 2 Support:**
- 30% of customers have segment history (changed tiers)
- `is_current = TRUE` for active segment records
- `segment_start_date` and `segment_end_date` track changes

### Order Data

**Temporal Patterns:**
- Orders span 2 years (2023-10-28 to 2025-10-28)
- Peak hours: 11AM-12PM, 8PM-10PM (realistic shopping times)
- Higher frequency on evenings and weekends

**Order Values by Segment:**
- Bronze: $20-$150
- Silver: $40-$200
- Gold: $80-$400
- Platinum: $150-$800

**Pareto Principle:**
- 20% of customers generate 80% of orders
- Reflects real-world customer behavior

### Clickstream Events

**Event Distribution:**
- Page views: 60% (most common)
- Add to cart: 15%
- Search: 12%
- Purchase: 8%
- Remove from cart: 5%

**Device Usage (2025 trends):**
- Mobile: 65% (mobile-first)
- Desktop: 30%
- Tablet: 5%

## Next Steps

After successful data generation and loading:

1. ✅ Commit changes to git
2. ✅ Create Airflow DAGs for ingestion (Week 2, Day 3-4)
3. ✅ Set up S3 ingestion pipeline
4. ✅ Test incremental loading

## Git Workflow

```bash
# Stage changes
git add scripts/generate_data.py
git add scripts/load_data.py
git add data/generated/*.csv
git add docs/week2/

# Commit
git commit -m "feat: implement synthetic data generation

- Generate 1K customers with SCD Type 2 segment tracking
- Generate 5K orders with realistic temporal patterns
- Generate 10K order items with proper foreign keys
- Generate 50K clickstream events (CSV export)
- Implement PostgreSQL bulk loading with execute_values
- Add environment validation script
- Include comprehensive documentation

Data Quality Verified:
- Perfect referential integrity (0 orphan records)
- Customer segments: 491/307/151/51 (bronze/silver/gold/platinum)
- Top products have 60-70 orders each
- Monthly orders: 180-230 consistent distribution
- Date range: Oct 2023 to Oct 2025 (2 years)

Performance:
- Data generation: 10-20 seconds
- PostgreSQL loading: ~4 seconds
- Bulk inserts using execute_values for efficiency"

# Push to feature branch
git push origin feature/data-generation
```

## Documentation

- **Script Documentation:** See docstrings in `scripts/generate_data.py`
- **Database Schema:** See `scripts/init_db.sql`
- **Data Model:** See `docs/dimensional_model.md`

---

**Last Updated:** Week 2, Day 1
**Status:** Data Generation Complete ✅
**Next:** Airflow DAG Development
