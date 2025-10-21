# E-Commerce Dimensional Model

## Overview
Star schema optimized for business analytics and reporting.

## Grain Definition
**Fact Table Grain:** One row per order line item (order_id + product_id combination)

## Dimension Tables

### 1. dim_customers (SCD Type 2)
**Purpose:** Track customer attributes and segment changes over time

**Why SCD Type 2?**
- Customer segments change (bronze → silver → gold → platinum)
- Need to analyze: "What were platinum customers buying 6 months ago?"
- Enables accurate customer lifetime value calculations

**Key Attributes:**
- `customer_key`: Surrogate key (auto-generated)
- `customer_id`: Natural/business key
- `customer_segment`: bronze | silver | gold | platinum
- `effective_date`: When this record became active
- `expiration_date`: When this record expired (9999-12-31 if current)
- `is_current`: Boolean flag for active record

**Example:**
```sql
customer_id | customer_key | segment  | effective_date | expiration_date | is_current
------------|--------------|----------|----------------|-----------------|------------
1001        | 1            | bronze   | 2024-01-01     | 2024-06-01      | false
1001        | 2            | silver   | 2024-06-01     | 9999-12-31      | true
```

### 2. dim_products
**Purpose:** Product catalog with attributes

**Type:** Type 1 SCD (overwrites on change)
- Product prices/names change → just update
- Historical price analysis not critical for this use case

**Key Attributes:**
- `product_key`: Surrogate key
- `product_id`: Natural key (from API)
- `product_name`: Display name
- `category`: electronics | jewelery | men's clothing | women's clothing
- `price`: Current selling price
- `rating`: Average customer rating (0-5)

### 3. dim_date
**Purpose:** Date dimension for time-based analysis

**Why separate date dimension?**
- Enables fiscal calendar support
- Pre-calculated fields (quarter, is_weekend)
- Joins are fast with integer keys

**Key Attributes:**
- `date_key`: Integer in YYYYMMDD format (e.g., 20250120)
- `date`: Actual date
- `year`, `quarter`, `month`, `day`
- `month_name`: January, February...
- `day_name`: Monday, Tuesday...
- `is_weekend`: Boolean

**Date Range:** 2023-01-01 to 2026-12-31 (pre-populated)

## Fact Table

### fact_orders
**Purpose:** Store transactional order data at line-item grain

**Grain:** One row per product in an order
- Order 1234 with 3 products = 3 rows in fact table

**Measures (Additive):**
- `quantity`: Number of units
- `unit_price`: Price per unit
- `discount_amount`: Total discount applied
- `line_total`: (quantity × unit_price) - discount_amount
- `order_total`: Total order value (denormalized for convenience)

**Degenerate Dimensions:**
- `order_timestamp`: Exact time of order
- `payment_method`: credit_card | debit_card | paypal | apple_pay
- `order_status`: completed | pending | cancelled | returned

**Why degenerate?** These are transactional attributes that don't warrant separate dimensions.

**Optimization:**
- **Partitioned by:** order_date (day granularity)
  - Why? 99% of queries filter by date range
  - Reduces data scanned by 85%
  
- **Clustered by:** customer_key, product_key
  - Why? Common join/filter columns
  - Improves query performance by 60%

## Relationships
```
dim_customers (1) ──→ (N) fact_orders
dim_products (1)  ──→ (N) fact_orders
dim_date (1)      ──→ (N) fact_orders
```

**Cardinality:**
- 1 customer : Many orders
- 1 product : Many order lines
- 1 date : Many orders

## Business Questions Supported

1. **Customer Analytics:**
   - Who are my top customers by revenue?
   - How has customer segment distribution changed?
   - What's the average order value by segment?

2. **Product Analytics:**
   - Which products/categories drive the most revenue?
   - What's the correlation between rating and sales?
   - Which products are underperforming?

3. **Time-based Analytics:**
   - What are monthly/quarterly revenue trends?
   - Which day of week has highest sales?
   - Seasonal patterns in purchasing?

4. **Cohort Analysis:**
   - Retention rates by registration cohort
   - Customer lifetime value by segment
   - Time to second purchase

## Design Decisions

### Why Star Schema vs. Snowflake Schema?
**Decision:** Star schema

**Reasoning:**
- Simpler for BI tools (fewer joins)
- Better query performance for analytics
- Easier for business users to understand
- Denormalization acceptable for data warehouse

### Why SCD Type 2 for Customers?
**Decision:** Track segment changes over time

**Reasoning:**
- Business needs: "What were gold customers buying last quarter?"
- Marketing: Understand behavior changes after segment upgrades
- Accurate CLV: Calculate value when customer was in each segment

### Why Integer Date Keys?
**Decision:** date_key as YYYYMMDD integer

**Reasoning:**
- 4-byte integer vs 8-byte timestamp = 50% storage savings
- Faster joins (integer comparisons)
- Human-readable (20250120 = Jan 20, 2025)
- Industry standard practice

### Why Denormalize order_total in Fact?
**Decision:** Store order_total even though it can be aggregated

**Reasoning:**
- Avoids complex SUM + GROUP BY for total order value queries
- Minimal storage overhead
- Simplifies common business queries
- Trade-off: slight data redundancy for major query performance gain