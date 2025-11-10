# Week 4: Quick Start & Testing Guide

Bhau, ye raha quick reference Week 4 models ko run aur test karne ke liye!

---

## 🚀 Running Week 4 Models

### Prerequisites Check
```bash
# Navigate to transform directory
cd C:\Modern-E-commerce-Analytics-Platform\transform

# Activate virtual environment (if using one)
# Windows:
..\venv\Scripts\activate

# Verify dbt is installed
dbt --version

# Check dbt connection
dbt debug
```

### Step 1: Install/Update Dependencies
```bash
# Install required packages (dbt_utils, dbt_expectations, etc.)
dbt deps
```

### Step 2: Compile Models (Check for Errors)
```bash
# Compile all models without running
dbt compile

# Compile specific model
dbt compile --select dim_date
dbt compile --select dim_customers
dbt compile --select fact_orders
```

### Step 3: Run Dimension Tables First
```bash
# Run all dimension tables
dbt run --select dim_date dim_customers dim_products

# Or run them individually
dbt run --select dim_date
dbt run --select dim_customers
dbt run --select dim_products
```

**Expected Results**:
- ✅ `dim_date`: 1,460 rows created (4 years)
- ✅ `dim_customers`: ~1,200 rows with SCD Type 2 history
- ✅ `dim_products`: ~20 rows from FakeStore API

### Step 4: Run Fact Table
```bash
# Run fact table (will join with dimensions)
dbt run --select fact_orders

# Check row count
dbt run --select fact_orders --full-refresh  # Force full refresh if needed
```

**Expected Results**:
- ✅ `fact_orders`: 66,000+ rows (order line items)
- First run: Full load (~2-3 minutes)
- Subsequent runs: Incremental load (<1 minute)

### Step 5: Run Analytics Models
```bash
# Run customer lifetime value model
dbt run --select customer_lifetime_value
```

**Expected Results**:
- ✅ `customer_lifetime_value`: ~1,000 rows (unique customers)

### Step 6: Run All Week 4 Models Together
```bash
# Run entire marts layer
dbt run --select marts.core marts.analytics

# Or use tags
dbt run --select tag:dimension tag:fact tag:analytics
```

---

## 🧪 Testing Week 4 Models

### Run All Tests
```bash
# Run all tests in project
dbt test

# Run tests for specific models
dbt test --select dim_date
dbt test --select dim_customers
dbt test --select dim_products
dbt test --select fact_orders
dbt test --select customer_lifetime_value
```

### Run Specific Test Types

**Uniqueness Tests**:
```bash
dbt test --select test_type:unique
```

**Not Null Tests**:
```bash
dbt test --select test_type:not_null
```

**Referential Integrity Tests**:
```bash
dbt test --select test_type:relationships
```

**Custom Logic Tests**:
```bash
dbt test --select test_type:accepted_values
```

---

## 🔍 Validation Queries

Copy-paste these into PostgreSQL/pgAdmin to validate results:

### 1. Check dim_date
```sql
-- Verify date range
SELECT
    min(date_day) as first_date,
    max(date_day) as last_date,
    count(*) as total_rows
FROM analytics.dim_date;

-- Check weekend flag
SELECT
    is_weekend,
    count(*) as row_count
FROM analytics.dim_date
GROUP BY is_weekend;

-- Sample records
SELECT * FROM analytics.dim_date
WHERE year = 2024 AND month = 11
ORDER BY date_day
LIMIT 10;
```

### 2. Check dim_customers (SCD Type 2)
```sql
-- Verify SCD Type 2 structure
SELECT
    customer_id,
    customer_segment,
    effective_date,
    expiration_date,
    is_current,
    count(*) over (partition by customer_id) as version_count
FROM analytics.dim_customers
WHERE customer_id IN (
    SELECT customer_id
    FROM analytics.dim_customers
    GROUP BY customer_id
    HAVING count(*) > 1  -- Customers with history
)
ORDER BY customer_id, effective_date
LIMIT 20;

-- Check current vs historical records
SELECT
    is_current,
    count(*) as record_count
FROM analytics.dim_customers
GROUP BY is_current;
```

### 3. Check dim_products
```sql
-- Basic statistics
SELECT
    count(*) as total_products,
    count(distinct category) as categories,
    round(avg(price)::numeric, 2) as avg_price,
    min(price) as min_price,
    max(price) as max_price
FROM analytics.dim_products;

-- Price tier distribution
SELECT
    price_tier,
    count(*) as product_count
FROM analytics.dim_products
GROUP BY price_tier
ORDER BY price_tier;
```

### 4. Check fact_orders
```sql
-- Basic statistics
SELECT
    count(*) as total_rows,
    count(distinct order_id) as unique_orders,
    count(distinct customer_key) as unique_customers,
    count(distinct product_key) as unique_products,
    sum(line_total) as total_revenue
FROM analytics.fact_orders;

-- Orders by status
SELECT
    order_status,
    count(*) as order_count,
    sum(line_total) as revenue
FROM analytics.fact_orders
GROUP BY order_status
ORDER BY revenue DESC;

-- Top 10 customers by revenue
SELECT
    c.full_name,
    c.customer_segment,
    count(distinct f.order_id) as total_orders,
    sum(f.line_total) as total_revenue
FROM analytics.fact_orders f
JOIN analytics.dim_customers c ON f.customer_key = c.customer_key
WHERE c.is_current = true
GROUP BY c.full_name, c.customer_segment
ORDER BY total_revenue DESC
LIMIT 10;
```

### 5. Check customer_lifetime_value
```sql
-- Value segment distribution
SELECT
    value_segment,
    count(*) as customer_count,
    sum(total_revenue) as segment_revenue,
    round(avg(total_orders)::numeric, 2) as avg_orders,
    round(avg(total_revenue)::numeric, 2) as avg_revenue
FROM analytics.customer_lifetime_value
GROUP BY value_segment
ORDER BY segment_revenue DESC;

-- Recency segment distribution
SELECT
    recency_segment,
    count(*) as customer_count
FROM analytics.customer_lifetime_value
GROUP BY recency_segment
ORDER BY customer_count DESC;

-- Top VIP customers
SELECT
    full_name,
    email,
    customer_segment,
    total_orders,
    total_revenue,
    estimated_monthly_revenue,
    value_segment,
    recency_segment
FROM analytics.customer_lifetime_value
WHERE value_segment = 'VIP'
ORDER BY total_revenue DESC
LIMIT 10;
```

### 6. Star Schema Join Test
```sql
-- Full star schema query
SELECT
    d.year,
    d.month_name,
    c.customer_segment,
    p.category,
    count(distinct f.order_id) as total_orders,
    sum(f.quantity) as total_items,
    sum(f.line_total) as total_revenue,
    round(avg(f.line_total)::numeric, 2) as avg_line_value
FROM analytics.fact_orders f
JOIN analytics.dim_date d ON f.date_key = d.date_key
JOIN analytics.dim_customers c ON f.customer_key = c.customer_key
JOIN analytics.dim_products p ON f.product_key = p.product_key
WHERE d.year = 2024
  AND c.is_current = true
GROUP BY d.year, d.month_name, c.customer_segment, p.category
ORDER BY total_revenue DESC
LIMIT 20;
```

---

## 🐛 Troubleshooting

### Issue 1: "Relation does not exist"
```bash
# Solution: Run staging models first
dbt run --select staging
dbt run --select marts
```

### Issue 2: "Column does not exist in source"
```bash
# Solution: Check source freshness
dbt source freshness

# Verify staging models are up to date
dbt run --select staging --full-refresh
```

### Issue 3: Incremental model not loading new data
```bash
# Solution: Force full refresh
dbt run --select fact_orders --full-refresh
```

### Issue 4: Tests failing
```bash
# See detailed test results
dbt test --store-failures

# Check failed test details
SELECT * FROM analytics_dbt_test__audit.failed_test_name;
```

### Issue 5: Slow performance
```bash
# Run with threads for parallel execution
dbt run --threads 4

# Target specific models
dbt run --select +fact_orders  # Run fact_orders and all upstream deps
```

---

## 📊 Performance Benchmarks

Expected run times on local machine (Windows, PostgreSQL):

| Model | Materialization | Rows | First Run | Incremental Run |
|-------|----------------|------|-----------|-----------------|
| dim_date | table | 1,460 | ~2 sec | ~2 sec (full refresh) |
| dim_customers | table | ~1,200 | ~3 sec | ~3 sec (full refresh) |
| dim_products | table | ~20 | ~1 sec | ~1 sec (full refresh) |
| fact_orders | incremental | 66,000+ | ~45 sec | ~5 sec |
| customer_lifetime_value | table | ~1,000 | ~8 sec | ~8 sec (full refresh) |
| **TOTAL** | - | - | **~60 sec** | **~20 sec** |

---

## 🎯 Success Criteria

Week 4 is complete when:
- ✅ All 5 models compile without errors
- ✅ All 5 models run successfully
- ✅ All 50+ tests pass
- ✅ Row counts match expected ranges
- ✅ Star schema joins work correctly
- ✅ Analytics segmentation makes business sense
- ✅ Documentation is comprehensive
- ✅ Screenshots captured for portfolio

---

## 📝 Quick Commands Cheat Sheet

```bash
# Full workflow from scratch
dbt deps                                    # Install dependencies
dbt debug                                   # Verify connection
dbt run --select staging                    # Run staging first
dbt run --select marts.core                 # Run dimensions and fact
dbt run --select marts.analytics            # Run analytics
dbt test                                    # Run all tests
dbt docs generate                           # Generate documentation
dbt docs serve                              # View documentation

# Incremental updates (daily workflow)
dbt run --select staging                    # Refresh staging
dbt run --select fact_orders                # Incremental load fact
dbt run --select customer_lifetime_value    # Refresh analytics
dbt test --select fact_orders customer_lifetime_value

# Full refresh if needed
dbt run --full-refresh --select marts
```

---

**Bhau, bas itna karna hai Week 4 complete karne ke liye! Simple aur straightforward! 🚀**
