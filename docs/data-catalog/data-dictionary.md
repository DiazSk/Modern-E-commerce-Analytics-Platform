# 📖 Data Dictionary

**Modern E-Commerce Analytics Platform**

**Version:** 1.0.0
**Last Updated:** November 10, 2025
**Author:** Zaid Shaikh

---

## 🎯 Overview

This data dictionary provides comprehensive documentation for all data tables, columns, relationships, and business rules in the Modern E-Commerce Analytics Platform. Use this as your reference guide when writing queries, building dashboards, or understanding the data model.

---

## 📊 Table of Contents

1. [Core Tables](#core-tables)
   - [dim_customers](#dim_customers)
   - [dim_products](#dim_products)
   - [fact_orders](#fact_orders)
   - [fact_order_items](#fact_order_items)
   - [fact_events](#fact_events)
2. [Data Relationships](#data-relationships)
3. [Business Rules](#business-rules)
4. [Common Queries](#common-queries)
5. [Common Mistakes](#common-mistakes)

---

## 📋 Core Tables

### `dim_customers`

**Purpose:** Slowly Changing Dimension (Type 2) tracking customer information and segment changes over time.

**Location:** `analytics.dim_customers`

**Grain:** One row per customer per segment period

**Total Records:** ~1,000 customers

| Column Name | Data Type | Nullable | Description | Example Value | Business Rules |
|-------------|-----------|----------|-------------|---------------|----------------|
| `customer_key` | INTEGER | NO | Surrogate key (auto-increment) | 1, 2, 3... | Primary key, unique |
| `customer_id` | INTEGER | NO | Natural key from source system | 1, 2, 3... | References source `customers.customer_id` |
| `email` | VARCHAR(255) | NO | Customer email address | `john.doe@example.com` | Unique per customer_id, used as business key |
| `first_name` | VARCHAR(100) | NO | Customer first name | `John` | Proper case preferred |
| `last_name` | VARCHAR(100) | NO | Customer last name | `Doe` | Proper case preferred |
| `phone` | VARCHAR(20) | YES | Customer phone number | `+1-555-123-4567` | Format varies by country |
| `registration_date` | DATE | NO | Date customer registered | `2024-01-15` | Cannot be in future |
| `customer_segment` | VARCHAR(20) | NO | Current segment classification | `gold`, `silver`, `bronze`, `platinum` | 4 possible values |
| `segment_start_date` | DATE | NO | When this segment assignment started | `2024-06-01` | Must be >= registration_date |
| `segment_end_date` | DATE | YES | When this segment assignment ended | `2024-12-31` or `NULL` | NULL = current/active record |
| `is_current` | BOOLEAN | NO | Flag indicating current/active record | `TRUE` or `FALSE` | Only 1 TRUE per customer_id |
| `created_at` | TIMESTAMP | NO | When record was created | `2024-01-15 10:30:00` | System-generated |
| `updated_at` | TIMESTAMP | NO | When record was last updated | `2024-06-01 14:22:15` | System-generated |

**Indexes:**
- Primary Key: `customer_key`
- Unique: `customer_id, segment_start_date`
- Index: `email`
- Index: `is_current, customer_segment`

**Sample Row:**
```sql
customer_key: 1
customer_id: 42
email: 'sarah.johnson@example.com'
first_name: 'Sarah'
last_name: 'Johnson'
phone: '+1-555-987-6543'
registration_date: '2023-03-15'
customer_segment: 'gold'
segment_start_date: '2024-01-01'
segment_end_date: NULL
is_current: TRUE
created_at: '2023-03-15 09:23:11'
updated_at: '2024-01-01 00:00:00'
```

---

### `dim_products`

**Purpose:** Product catalog dimension with complete product information.

**Location:** `analytics.dim_products`

**Grain:** One row per product

**Total Records:** 200 products

| Column Name | Data Type | Nullable | Description | Example Value | Business Rules |
|-------------|-----------|----------|-------------|---------------|----------------|
| `product_key` | INTEGER | NO | Surrogate key (auto-increment) | 1, 2, 3... | Primary key, unique |
| `product_id` | INTEGER | NO | Natural key from source (API) | 1, 2, 3... | Unique, references API product ID |
| `title` | VARCHAR(500) | NO | Product name/title | `Fjallraven Foldsack Backpack` | Display name |
| `price` | DECIMAL(10,2) | NO | Current product price | `109.95` | Must be > 0 |
| `description` | TEXT | YES | Detailed product description | `Your perfect pack for everyday...` | Can be lengthy |
| `category` | VARCHAR(100) | NO | Product category | `men's clothing`, `electronics` | 4 main categories |
| `image` | VARCHAR(500) | YES | Product image URL | `https://fakestoreapi.com/img/...` | Full URL to image |
| `rating_rate` | DECIMAL(3,2) | YES | Average customer rating (1-5) | `4.50` | Range: 1.0 to 5.0 |
| `rating_count` | INTEGER | YES | Number of ratings | `250` | Must be >= 0 |
| `ingestion_timestamp` | TIMESTAMP | NO | When product was ingested | `2025-10-28 23:19:49` | System-generated |
| `ingestion_date` | DATE | NO | Date of ingestion | `2025-10-28` | System-generated |
| `data_source` | VARCHAR(50) | NO | Source system name | `fakestoreapi` | Identifies origin |

**Indexes:**
- Primary Key: `product_key`
- Unique: `product_id`
- Index: `category`
- Index: `price`

**Sample Row:**
```sql
product_key: 1
product_id: 1
title: 'Fjallraven - Foldsack No. 1 Backpack, Fits 15 Laptops'
price: 109.95
description: 'Your perfect pack for everyday use...'
category: 'men''s clothing'
image: 'https://fakestoreapi.com/img/81fPKd-2AYL._AC_SL1500_t.png'
rating_rate: 3.90
rating_count: 120
ingestion_timestamp: '2025-10-28 23:19:49.129495'
ingestion_date: '2025-10-28'
data_source: 'fakestoreapi'
```

**⚠️ COMMON MISTAKE:** The rating columns are `rating_rate` and `rating_count`, NOT just `rating`. Many queries fail because developers write `SELECT rating` instead of `SELECT rating_rate`.

---

### `fact_orders`

**Purpose:** Fact table containing order header information.

**Location:** `analytics.fact_orders`

**Grain:** One row per order

**Total Records:** 5,000 orders

| Column Name | Data Type | Nullable | Description | Example Value | Business Rules |
|-------------|-----------|----------|-------------|---------------|----------------|
| `order_key` | INTEGER | NO | Surrogate key (auto-increment) | 1, 2, 3... | Primary key, unique |
| `order_id` | INTEGER | NO | Natural key from source system | 1, 2, 3... | Unique, references source orders |
| `customer_key` | INTEGER | NO | Foreign key to dim_customers | 42 | Must exist in dim_customers |
| `order_date` | TIMESTAMP | NO | When order was placed | `2025-10-28 14:30:22` | Cannot be in future |
| `order_total` | DECIMAL(10,2) | NO | Total order amount (USD) | `875.47` | Must be > 0 |
| `payment_method` | VARCHAR(50) | NO | Payment type | `credit_card`, `paypal`, `debit_card` | 5 possible values |
| `shipping_address` | TEXT | YES | Full shipping address | `123 Main St, New York, NY 10001` | Can contain newlines |
| `order_status` | VARCHAR(20) | NO | Current order status | `completed`, `pending`, `cancelled` | 5 possible values |
| `created_at` | TIMESTAMP | NO | Record creation timestamp | `2025-10-28 14:30:22` | System-generated |
| `updated_at` | TIMESTAMP | NO | Last update timestamp | `2025-10-28 15:45:10` | System-generated |

**Indexes:**
- Primary Key: `order_key`
- Unique: `order_id`
- Foreign Key: `customer_key` → `dim_customers(customer_key)`
- Index: `order_date`
- Index: `order_status`
- Index: `customer_key, order_date`

**Sample Row:**
```sql
order_key: 1
order_id: 4972
customer_key: 156
order_date: '2025-10-28 14:30:22.123456'
order_total: 127.48
payment_method: 'credit_card'
shipping_address: '742 Evergreen Terrace, Springfield, OR 97477'
order_status: 'completed'
created_at: '2025-10-28 14:30:22'
updated_at: '2025-10-28 15:45:10'
```

**Business Logic:**
- `order_total` should equal SUM of related `fact_order_items.line_total`
- Valid `order_status` values: `completed`, `pending`, `processing`, `cancelled`, `returned`
- Valid `payment_method` values: `credit_card`, `debit_card`, `paypal`, `apple_pay`, `google_pay`

---

### `fact_order_items`

**Purpose:** Fact table containing order line items (many-to-one with orders).

**Location:** `analytics.fact_order_items`

**Grain:** One row per product per order

**Total Records:** ~10,000 order items

| Column Name | Data Type | Nullable | Description | Example Value | Business Rules |
|-------------|-----------|----------|-------------|---------------|----------------|
| `order_item_key` | INTEGER | NO | Surrogate key (auto-increment) | 1, 2, 3... | Primary key, unique |
| `order_key` | INTEGER | NO | Foreign key to fact_orders | 1, 2, 3... | Must exist in fact_orders |
| `product_key` | INTEGER | NO | Foreign key to dim_products | 42 | Must exist in dim_products |
| `quantity` | INTEGER | NO | Quantity ordered | 2, 3, 5 | Must be > 0 |
| `unit_price` | DECIMAL(10,2) | NO | Price per unit at order time | `22.50` | Must be > 0 |
| `discount_amount` | DECIMAL(10,2) | NO | Total discount applied | `4.50` or `0.00` | Must be >= 0 |
| `line_total` | DECIMAL(10,2) | NO | (quantity × unit_price) - discount | `40.50` | Calculated field |

**Indexes:**
- Primary Key: `order_item_key`
- Foreign Key: `order_key` → `fact_orders(order_key)`
- Foreign Key: `product_key` → `dim_products(product_key)`
- Index: `order_key`
- Index: `product_key`

**Sample Row:**
```sql
order_item_key: 1
order_key: 1
product_key: 43
quantity: 2
unit_price: 22.50
discount_amount: 4.50
line_total: 40.50
```

**Calculation Formula:**
```sql
line_total = (quantity * unit_price) - discount_amount
```

**Business Logic:**
- Each order can have 1-5 line items (typically)
- `line_total` must be > 0
- `discount_amount` typically 0-30% of (quantity × unit_price)
- SUM of all `line_total` for an `order_key` should equal `fact_orders.order_total`

---

### `fact_events`

**Purpose:** Clickstream/behavioral events fact table (web analytics).

**Location:** `analytics.fact_events`

**Grain:** One row per user event

**Total Records:** 50,000+ events

| Column Name | Data Type | Nullable | Description | Example Value | Business Rules |
|-------------|-----------|----------|-------------|---------------|----------------|
| `event_key` | BIGINT | NO | Surrogate key (auto-increment) | 1, 2, 3... | Primary key, unique |
| `event_id` | UUID | NO | Unique event identifier | `550e8400-e29b-41d4...` | Universally unique |
| `session_id` | UUID | NO | User session identifier | `6ba7b810-9dad-11d1...` | Groups events by session |
| `customer_key` | INTEGER | YES | Foreign key to dim_customers | 42 or `NULL` | NULL = anonymous user |
| `event_timestamp` | TIMESTAMP | NO | When event occurred | `2025-10-31 20:15:33` | Microsecond precision |
| `event_type` | VARCHAR(50) | NO | Type of event | `page_view`, `add_to_cart`, `purchase` | 5 possible values |
| `product_key` | INTEGER | YES | Foreign key to dim_products | 15 or `NULL` | NULL if not product-related |
| `page_url` | VARCHAR(500) | YES | Page URL where event occurred | `/products/electronics` | Relative path |
| `device_type` | VARCHAR(20) | NO | Device category | `mobile`, `desktop`, `tablet` | 3 possible values |
| `browser` | VARCHAR(50) | NO | Browser type | `chrome`, `safari`, `firefox`, `edge` | 4 main browsers |

**Indexes:**
- Primary Key: `event_key`
- Unique: `event_id`
- Foreign Key: `customer_key` → `dim_customers(customer_key)`
- Foreign Key: `product_key` → `dim_products(product_key)`
- Index: `event_timestamp`
- Index: `event_type`
- Index: `session_id`
- Index: `customer_key, event_timestamp`

**Sample Row:**
```sql
event_key: 1
event_id: '550e8400-e29b-41d4-a716-446655440000'
session_id: '6ba7b810-9dad-11d1-80b4-00c04fd430c8'
customer_key: 42
event_timestamp: '2025-10-31 20:15:33.458912'
event_type: 'add_to_cart'
product_key: 15
page_url: '/products/electronics/laptop'
device_type: 'mobile'
browser: 'chrome'
```

**Business Logic:**
- Valid `event_type` values: `page_view`, `add_to_cart`, `remove_from_cart`, `purchase`, `search`
- Valid `device_type` values: `mobile`, `desktop`, `tablet`
- Valid `browser` values: `chrome`, `safari`, `firefox`, `edge`
- Most events (60%) are `page_view`
- `customer_key` can be NULL for anonymous/guest users
- `product_key` required for product-related events, NULL otherwise

---

## 🔗 Data Relationships

### Entity Relationship Diagram

```
┌─────────────────┐
│  dim_customers  │
│  (SCD Type 2)   │
└────────┬────────┘
         │ 1
         │
         │ N
┌────────┴────────┐
│  fact_orders    │◄──────┐
└────────┬────────┘       │
         │ 1              │
         │                │ N
         │ N         ┌────┴─────────┐
┌────────┴────────┐ │ fact_events  │
│fact_order_items │ │ (clickstream)│
└────────┬────────┘ └────┬─────────┘
         │ N             │ N
         │               │
         │ 1             │ 1
┌────────┴───────────────┴───┐
│      dim_products          │
└────────────────────────────┘
```

### Relationship Details

**1. dim_customers → fact_orders (1:N)**
- **Join:** `dim_customers.customer_key = fact_orders.customer_key`
- **Type:** Mandatory (every order must have a customer)
- **Note:** Join to customers WHERE `is_current = TRUE` for latest segment

**2. fact_orders → fact_order_items (1:N)**
- **Join:** `fact_orders.order_key = fact_order_items.order_key`
- **Type:** Mandatory (every order has 1+ line items)
- **Aggregation:** SUM(line_total) should equal order_total

**3. dim_products → fact_order_items (1:N)**
- **Join:** `dim_products.product_key = fact_order_items.product_key`
- **Type:** Mandatory (every line item has a product)

**4. dim_products → fact_events (1:N)**
- **Join:** `dim_products.product_key = fact_events.product_key`
- **Type:** Optional (some events don't reference products)

**5. dim_customers → fact_events (1:N)**
- **Join:** `dim_customers.customer_key = fact_events.customer_key`
- **Type:** Optional (anonymous users have NULL customer_key)

---

## 📜 Business Rules

### Customer Segmentation Logic

**Segments:** `platinum` > `gold` > `silver` > `bronze`

**Assignment Criteria:**
- **Platinum:** Top 5% by lifetime value (CLV > $1,500)
- **Gold:** Next 15% (CLV $800-$1,500)
- **Silver:** Next 30% (CLV $300-$800)
- **Bronze:** Remaining 50% (CLV < $300)

**SCD Type 2 Rules:**
- Only ONE record per customer has `is_current = TRUE`
- `segment_end_date = NULL` indicates current/active record
- Historical records have `segment_end_date` populated and `is_current = FALSE`
- When segment changes, old record is closed (end date + is_current set) and new record created

### Order Processing Rules

**Order Status Transitions:**
```
pending → processing → completed ✅
pending → cancelled ❌
completed → returned ⚠️
```

**Order Total Calculation:**
```sql
order_total = SUM(line_total) across all order items
line_total = (quantity × unit_price) - discount_amount
```

**Payment Methods (by popularity):**
1. Credit Card (40%)
2. Debit Card (25%)
3. PayPal (20%)
4. Apple Pay (10%)
5. Google Pay (5%)

### Product Catalog Rules

**Categories (4 total):**
- `men's clothing`
- `women's clothing`
- `electronics`
- `jewelery` (note: API spelling)

**Price Ranges:**
- **Budget:** $0-$50
- **Mid-Range:** $50-$200
- **Premium:** $200-$500
- **Luxury:** $500+

**Rating System:**
- Scale: 1.0 to 5.0
- Minimum ratings required: 10 (for statistical significance)
- Average across platform: ~3.8

### Clickstream Rules

**Event Funnel (typical session):**
1. `page_view` (multiple)
2. `search` (optional)
3. `page_view` (product pages)
4. `add_to_cart`
5. `purchase` (conversion!)

**Conversion Rates:**
- Page view → Add to cart: ~15%
- Add to cart → Purchase: ~8%
- Overall conversion: ~1.2%

**Device Distribution:**
- Mobile: 65%
- Desktop: 30%
- Tablet: 5%

---

## 🔍 Common Queries

### Query 1: Get Customer with Current Segment

```sql
-- Get customer info with their CURRENT segment
SELECT
    c.customer_id,
    c.email,
    c.first_name || ' ' || c.last_name AS full_name,
    c.customer_segment,
    c.segment_start_date
FROM analytics.dim_customers c
WHERE c.is_current = TRUE
    AND c.customer_id = 42;
```

### Query 2: Order with Line Items

```sql
-- Get order details with all line items
SELECT
    o.order_id,
    o.order_date,
    o.order_total,
    p.title AS product_name,
    oi.quantity,
    oi.unit_price,
    oi.discount_amount,
    oi.line_total
FROM analytics.fact_orders o
JOIN analytics.fact_order_items oi ON o.order_key = oi.order_key
JOIN analytics.dim_products p ON oi.product_key = p.product_key
WHERE o.order_id = 4972
ORDER BY oi.order_item_key;
```

### Query 3: Customer Lifetime Value (CLV)

```sql
-- Calculate Customer Lifetime Value
SELECT
    c.customer_id,
    c.email,
    c.customer_segment,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(o.order_total) AS lifetime_value,
    AVG(o.order_total) AS avg_order_value,
    MIN(o.order_date) AS first_order_date,
    MAX(o.order_date) AS last_order_date
FROM analytics.dim_customers c
JOIN analytics.fact_orders o ON c.customer_key = o.customer_key
WHERE c.is_current = TRUE
GROUP BY c.customer_id, c.email, c.customer_segment
ORDER BY lifetime_value DESC
LIMIT 20;
```

### Query 4: Product Performance

```sql
-- Product performance with ratings
SELECT
    p.product_id,
    p.title,
    p.category,
    p.price,
    p.rating_rate,  -- ⚠️ NOT just 'rating'!
    p.rating_count,
    COUNT(DISTINCT oi.order_key) AS times_ordered,
    SUM(oi.quantity) AS total_quantity_sold,
    SUM(oi.line_total) AS total_revenue
FROM analytics.dim_products p
LEFT JOIN analytics.fact_order_items oi ON p.product_key = oi.product_key
GROUP BY
    p.product_id, p.title, p.category,
    p.price, p.rating_rate, p.rating_count
ORDER BY total_revenue DESC NULLS LAST
LIMIT 10;
```

### Query 5: Daily Revenue Trend

```sql
-- Daily revenue with order counts
SELECT
    DATE(o.order_date) AS order_day,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(o.order_total) AS daily_revenue,
    AVG(o.order_total) AS avg_order_value,
    COUNT(DISTINCT o.customer_key) AS unique_customers
FROM analytics.fact_orders o
WHERE o.order_status = 'completed'
GROUP BY DATE(o.order_date)
ORDER BY order_day DESC;
```

### Query 6: Customer Segmentation Distribution

```sql
-- Current customer segment distribution
SELECT
    customer_segment,
    COUNT(*) AS customer_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS percentage
FROM analytics.dim_customers
WHERE is_current = TRUE
GROUP BY customer_segment
ORDER BY
    CASE customer_segment
        WHEN 'platinum' THEN 1
        WHEN 'gold' THEN 2
        WHEN 'silver' THEN 3
        WHEN 'bronze' THEN 4
    END;
```

### Query 7: Conversion Funnel Analysis

```sql
-- Clickstream conversion funnel
WITH event_counts AS (
    SELECT
        event_type,
        COUNT(*) AS event_count
    FROM analytics.fact_events
    WHERE event_timestamp >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY event_type
)
SELECT
    event_type,
    event_count,
    ROUND(100.0 * event_count /
        (SELECT event_count FROM event_counts WHERE event_type = 'page_view'), 2
    ) AS conversion_rate_percent
FROM event_counts
ORDER BY
    CASE event_type
        WHEN 'page_view' THEN 1
        WHEN 'search' THEN 2
        WHEN 'add_to_cart' THEN 3
        WHEN 'remove_from_cart' THEN 4
        WHEN 'purchase' THEN 5
    END;
```

---

## ⚠️ Common Mistakes

### Mistake 1: Wrong Rating Column Name

**❌ WRONG:**
```sql
SELECT product_id, title, rating
FROM dim_products;
-- ERROR: column "rating" does not exist
```

**✅ CORRECT:**
```sql
SELECT product_id, title, rating_rate, rating_count
FROM dim_products;
```

**Why?** The API returns a nested `rating` object with `rate` and `count` properties. We flatten this to `rating_rate` and `rating_count`.

---

### Mistake 2: Joining to Wrong Customer Record

**❌ WRONG:**
```sql
-- This can return MULTIPLE rows per customer!
SELECT o.order_id, c.customer_segment
FROM fact_orders o
JOIN dim_customers c ON o.customer_key = c.customer_key;
```

**✅ CORRECT:**
```sql
-- Use is_current = TRUE for latest segment
SELECT o.order_id, c.customer_segment
FROM fact_orders o
JOIN dim_customers c ON o.customer_key = c.customer_key
WHERE c.is_current = TRUE;
```

**Why?** SCD Type 2 creates multiple rows per customer. Always filter `is_current = TRUE` for latest state.

---

### Mistake 3: Forgetting NULL Handling

**❌ WRONG:**
```sql
-- This excludes orders with NULLs!
SELECT COUNT(*)
FROM fact_orders
WHERE order_status = 'completed' OR order_status = 'pending';
```

**✅ CORRECT:**
```sql
-- Use IN or COALESCE for NULL safety
SELECT COUNT(*)
FROM fact_orders
WHERE order_status IN ('completed', 'pending');

-- Or handle NULLs explicitly
SELECT COUNT(*)
FROM fact_orders
WHERE COALESCE(order_status, 'unknown') IN ('completed', 'pending');
```

---

### Mistake 4: Aggregating Before Joining

**❌ WRONG (Can cause cartesian products):**
```sql
SELECT
    c.customer_id,
    SUM(o.order_total)
FROM dim_customers c
LEFT JOIN fact_orders o ON c.customer_key = o.customer_key
LEFT JOIN fact_order_items oi ON o.order_key = oi.order_key
GROUP BY c.customer_id;
-- Results are INFLATED by number of line items!
```

**✅ CORRECT:**
```sql
-- Aggregate first, then join
SELECT
    c.customer_id,
    COALESCE(SUM(o.order_total), 0) AS total_revenue
FROM dim_customers c
LEFT JOIN fact_orders o ON c.customer_key = o.customer_key
WHERE c.is_current = TRUE
GROUP BY c.customer_id;
```

---

### Mistake 5: Incorrect Date Comparisons

**❌ WRONG:**
```sql
-- String comparison fails for dates!
SELECT * FROM fact_orders
WHERE order_date = '2025-10-28';
```

**✅ CORRECT:**
```sql
-- Cast to DATE or use DATE()
SELECT * FROM fact_orders
WHERE DATE(order_date) = '2025-10-28';

-- Or for ranges
SELECT * FROM fact_orders
WHERE order_date >= '2025-10-28 00:00:00'
  AND order_date < '2025-10-29 00:00:00';
```

---

## 📊 Data Quality Metrics

### Current Data Quality Status

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Test Pass Rate | > 95% | 96.3% | ✅ |
| NULL Values (Critical Fields) | 0% | 0% | ✅ |
| Duplicate Records | 0 | 0 | ✅ |
| Referential Integrity | 100% | 100% | ✅ |
| Data Freshness | < 24h | < 24h | ✅ |

### Known Data Limitations

1. **Product Catalog:** Limited to 200 products (API constraint)
2. **Date Range:** Orders span 2 years (2023-11-02 to 2025-10-31)
3. **Customer Scale:** 1,000 customers (synthetic data)
4. **Geographic Data:** Limited to US addresses
5. **Currency:** All values in USD (no multi-currency)

---

## 🔐 Data Security & Privacy

### Sensitive Data

**PII (Personally Identifiable Information):**
- `dim_customers.email`
- `dim_customers.phone`
- `fact_orders.shipping_address`

**Best Practices:**
- Mask PII in non-production environments
- Use `LEFT(email, 3) || '***@' || SPLIT_PART(email, '@', 2)` for partial masking
- Never log PII values
- Implement column-level security in production

---

## 📞 Support & Contact

### Questions or Issues?

- **Data Issues:** Check `logs/` directory for ingestion errors
- **Schema Questions:** Refer to dbt documentation in `transform/models/`
- **Performance Issues:** Review query execution plans with `EXPLAIN ANALYZE`

### Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-10 | 1.0.0 | Initial comprehensive data dictionary |
| 2025-10-28 | 0.2.0 | Added fact_events table |
| 2025-10-20 | 0.1.0 | Core tables documented |

---

## 🎯 Quick Reference Card

**Most Used Tables:**
1. `analytics.dim_customers` (with `is_current = TRUE`)
2. `analytics.fact_orders`
3. `analytics.dim_products`
4. `analytics.fact_order_items`

**Most Used Joins:**
```sql
-- Orders with current customer info
fact_orders o
JOIN dim_customers c ON o.customer_key = c.customer_key AND c.is_current = TRUE

-- Order items with products
fact_order_items oi
JOIN dim_products p ON oi.product_key = p.product_key
```

**Key Metrics:**
- **Total Revenue:** `SUM(order_total)` = $692,072.36
- **Average Order Value:** `AVG(order_total)` = $138.41
- **Customer Count:** `COUNT(DISTINCT customer_id WHERE is_current = TRUE)` = 1,000
- **Product Count:** `COUNT(DISTINCT product_id)` = 200

---

**End of Data Dictionary** | Version 1.0.0 | Modern E-Commerce Analytics Platform
