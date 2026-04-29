# Metabase Operations Runbook

Operational reference for the Metabase BI deployment serving the e-commerce analytics platform.

| Field | Value |
|-------|-------|
| Service | Metabase |
| Backing database | PostgreSQL (`ecommerce` logical DB) |
| Container name | `ecommerce-metabase` |
| External URL | `http://localhost:3001` |
| Dashboards in scope | Executive, Product Performance, Customer Analytics, Funnel Analysis |
| Visualizations | 16 |
| Source data volume | 1,000 customers · 5,000 orders · 9,994 order items · 20 products · 50,000 events |

---

## Contents

1. [Service Bootstrap](#1-service-bootstrap)
2. [Connection Reference](#2-connection-reference)
3. [Schema Reference](#3-schema-reference)
4. [Initial Configuration](#4-initial-configuration)
5. [Dashboard Catalogue](#5-dashboard-catalogue)
6. [SQL Query Reference](#6-sql-query-reference)
7. [Troubleshooting](#7-troubleshooting)
8. [Performance Tuning](#8-performance-tuning)
9. [UI Reference](#9-ui-reference)

---

## 1. Service Bootstrap

```bash
cd /path/to/Modern-E-commerce-Analytics-Platform
docker-compose up -d
docker-compose logs -f metabase   # Wait for "Initialization COMPLETE"
```

Open `http://localhost:3001` once the log line above appears (typically 2–3 minutes after first start).

---

## 2. Connection Reference

### Metabase Web Console

| Setting | Value |
|---------|-------|
| URL | `http://localhost:3001` |
| Admin email | `admin@ecommerce.com` |
| Admin password | Set at first login |

### PostgreSQL Source Connection (configured inside Metabase)

| Setting | Value |
|---------|-------|
| Display name | `E-Commerce Analytics` |
| Database type | PostgreSQL |
| Host | `postgres` *(internal Docker network name)* |
| Port | `5432` |
| Database name | `ecommerce` |
| Username | `ecommerce_user` |
| Password | `ecommerce_pass` |
| SSL | Disabled |
| SSH tunnel | Disabled |

> **Note:** Use the Docker service name `postgres`, not `localhost`. The default internal port is `5432`.

---

## 3. Schema Reference

The connected database exposes the following tables. Column names are authoritative; query authors must match these exactly.

### `products`

```sql
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    title VARCHAR(500),
    price DECIMAL(10,2),
    category VARCHAR(100),
    description TEXT,
    image VARCHAR(500),
    rating_rate DECIMAL(3,2),     -- product rating (0.00–5.00)
    rating_count INTEGER,          -- number of reviews
    ingestion_timestamp TIMESTAMP,
    ingestion_date DATE,
    data_source VARCHAR(50),
    created_at TIMESTAMP
);
```

> **Column naming caveat:** the rating column is `rating_rate`, not `rating`. Reference `p.rating_rate` and `p.rating_count` in all queries.

### `customers`

```sql
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    registration_date DATE,
    customer_segment VARCHAR(20),       -- bronze | silver | gold | platinum
    segment_start_date DATE,
    segment_end_date DATE,
    is_current BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### `orders`

```sql
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date TIMESTAMP,
    order_total DECIMAL(10,2),
    payment_method VARCHAR(50),
    shipping_address TEXT,
    order_status VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### `order_items`

```sql
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER,
    quantity INTEGER,
    unit_price DECIMAL(10,2),
    discount_amount DECIMAL(10,2),
    line_total DECIMAL(10,2),       -- quantity * unit_price - discount
    created_at TIMESTAMP
);
```

### `events`

```sql
CREATE TABLE events (
    event_id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    user_id INTEGER,
    event_type VARCHAR(50),
    event_timestamp TIMESTAMP,
    page_url VARCHAR(255),
    product_id INTEGER,
    device_type VARCHAR(50),
    browser VARCHAR(50),
    country VARCHAR(50)
);
```

---

## 4. Initial Configuration

First-time setup of the Metabase admin account and source database connection.

1. Open `http://localhost:3001`.
2. Create the admin account:
   - First name: `Admin`
   - Last name: `User`
   - Email: `admin@ecommerce.com`
   - Password: set per organisational policy
3. Add the database connection using the values from [section 2](#2-connection-reference). Confirm the success banner reads "Successfully connected to your database!"
4. Skip usage preferences and accept defaults.
5. The home page will list `E-Commerce Analytics` as an available data source.

---

## 5. Dashboard Catalogue

Three production dashboards plus an optional funnel analysis dashboard. Each entry below documents purpose, audience, refresh cadence, and the underlying queries.

### 5.1 Executive Dashboard

| Field | Value |
|-------|-------|
| Purpose | High-level business metrics for leadership |
| Audience | CEO, CFO, executive team |
| Refresh interval | 5 minutes |
| Visualizations | 8 |

#### Construction

1. From the Metabase home page, click `+ New` → `Dashboard`.
2. Name: `Executive Dashboard`. Description: `High-level business metrics for leadership`.
3. Add each visualization below as a Native Query, save it, and pin it to this dashboard.

#### Metric 1 — Total Revenue (All Time)

```sql
SELECT
    ROUND(COALESCE(SUM(oi.quantity * oi.unit_price), 0)::numeric, 2) AS total_revenue
FROM order_items oi;
```

- Visualization: Number → Currency (USD), 2 decimal places
- Sample result: `$692,072.36`

#### Metric 2 — Total Revenue (Last Month)

```sql
SELECT
    ROUND(COALESCE(SUM(oi.quantity * oi.unit_price), 0)::numeric, 2) AS total_revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE DATE_TRUNC('month', o.order_date) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month');
```

- Visualization: Number → Currency (USD)
- Sample result: `$30,099.38`

#### Metric 3 — Total Orders (All Time)

```sql
SELECT COUNT(DISTINCT order_id) AS total_orders FROM orders;
```

- Visualization: Number
- Sample result: `5,000`

#### Metric 4 — Average Order Value

```sql
SELECT
    ROUND(AVG(order_total)::numeric, 2) AS avg_order_value
FROM (
    SELECT
        o.order_id,
        SUM(oi.quantity * oi.unit_price) AS order_total
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY o.order_id
) AS order_totals;
```

- Visualization: Number → Currency (USD)
- Sample result: `$138.41`

#### Metric 5 — Active Customer Count (Last 30 Days)

```sql
SELECT
    COUNT(DISTINCT customer_id) AS active_customers
FROM orders
WHERE order_date >= CURRENT_DATE - INTERVAL '30 days';
```

- Visualization: Number
- Sample result: `126`

#### Metric 6 — Revenue Trend (Last 12 Months)

```sql
SELECT
    DATE_TRUNC('month', o.order_date) AS month,
    ROUND(SUM(oi.quantity * oi.unit_price)::numeric, 2) AS revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', o.order_date)
ORDER BY month;
```

- Visualization: Line Chart with X-axis `month` (MMM YYYY) and Y-axis `revenue` (Currency)

#### Metric 7 — Daily Orders Trend

```sql
SELECT
    DATE(o.order_date) AS order_date,
    COUNT(DISTINCT o.order_id) AS order_count
FROM orders o
WHERE o.order_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(o.order_date)
ORDER BY order_date;
```

- Visualization: Line Chart

#### Metric 8 — Top 5 Categories by Revenue

```sql
SELECT
    p.category,
    ROUND(SUM(oi.quantity * oi.unit_price)::numeric, 2) AS total_revenue
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY total_revenue DESC
LIMIT 5;
```

- Visualization: Bar Chart (Vertical)

---

### 5.2 Product Performance Dashboard

| Field | Value |
|-------|-------|
| Purpose | Product-level analytics and inventory optimisation |
| Audience | Product team, inventory management, operations |
| Refresh interval | 10 minutes |
| Visualizations | 4 |

#### Metric 1 — Top 10 Products by Revenue

```sql
SELECT
    p.title AS product_name,
    p.category,
    COUNT(DISTINCT oi.order_id) AS order_count,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price)::numeric, 2) AS total_revenue
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.title, p.category
ORDER BY total_revenue DESC
LIMIT 10;
```

- Visualization: Horizontal Bar Chart, Y-axis `product_name`, X-axis `total_revenue` (Currency)

#### Metric 2 — Category Performance (Multi-Metric)

```sql
SELECT
    p.category,
    COUNT(DISTINCT oi.order_id) AS order_count,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price)::numeric, 2) AS total_revenue,
    ROUND(AVG(oi.quantity * oi.unit_price)::numeric, 2) AS avg_item_value
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;
```

- Visualization: Grouped Bar Chart, X-axis `category`, four metric series

#### Metric 3 — Product Rating vs Sales

```sql
SELECT
    p.title AS product_name,
    p.category,
    p.rating_rate AS product_rating,
    p.rating_count,
    COALESCE(SUM(oi.quantity), 0) AS units_sold,
    COALESCE(ROUND(SUM(oi.quantity * oi.unit_price)::numeric, 2), 0) AS total_revenue
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.title, p.category, p.rating_rate, p.rating_count
HAVING COALESCE(SUM(oi.quantity), 0) > 0
ORDER BY total_revenue DESC
LIMIT 30;
```

- Visualization: Scatter Plot (Bubble), X-axis `product_rating`, Y-axis `units_sold`, bubble size `total_revenue`, colour by `category`

#### Metric 4 — Slow-Moving Inventory (Status-Coded)

```sql
SELECT
    p.title AS product_name,
    p.category,
    ROUND(p.price, 2) AS price,
    p.rating_rate AS rating,
    COALESCE(SUM(oi.quantity), 0) AS units_sold,
    CASE
        WHEN COALESCE(SUM(oi.quantity), 0) = 0 THEN 'No Sales'
        WHEN COALESCE(SUM(oi.quantity), 0) < 60 THEN 'Critical'
        WHEN COALESCE(SUM(oi.quantity), 0) < 80 THEN 'Slow'
        ELSE 'Normal'
    END AS inventory_status
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.title, p.category, p.price, p.rating_rate
ORDER BY units_sold ASC
LIMIT 15;
```

- Visualization: Horizontal Bar Chart coloured by `inventory_status` (red=Critical, orange=Slow, green=Normal)

---

### 5.3 Customer Analytics Dashboard

| Field | Value |
|-------|-------|
| Purpose | Customer behaviour, segmentation, and retention analysis |
| Audience | Marketing, customer success, sales |
| Refresh interval | 15 minutes |
| Visualizations | 4 |

#### Metric 1 — Customer Lifetime Value Distribution

```sql
WITH customer_totals AS (
    SELECT
        c.customer_id,
        COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total_spent
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY c.customer_id
),
bracketed_customers AS (
    SELECT
        CASE
            WHEN total_spent = 0 THEN 0
            WHEN total_spent < 100 THEN 1
            WHEN total_spent < 500 THEN 2
            WHEN total_spent < 1000 THEN 3
            WHEN total_spent < 5000 THEN 4
            ELSE 5
        END AS bracket_order,
        CASE
            WHEN total_spent = 0 THEN 'No Orders'
            WHEN total_spent < 100 THEN '< $100'
            WHEN total_spent < 500 THEN '$100-$500'
            WHEN total_spent < 1000 THEN '$500-$1K'
            WHEN total_spent < 5000 THEN '$1K-$5K'
            ELSE '> $5K'
        END AS spending_bracket
    FROM customer_totals
)
SELECT
    spending_bracket,
    COUNT(*) AS customer_count
FROM bracketed_customers
GROUP BY spending_bracket, bracket_order
ORDER BY bracket_order;
```

- Visualization: Bar Chart (Vertical)
- Note: the CTE pattern is required because Metabase does not resolve aliases in `GROUP BY`/`ORDER BY` (see [section 7](#7-troubleshooting)).

#### Metric 2 — Customer Segments

```sql
WITH customer_totals AS (
    SELECT
        c.customer_id,
        COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total_spent
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY c.customer_id
),
segmented_customers AS (
    SELECT
        CASE
            WHEN total_spent >= 5000 THEN 1
            WHEN total_spent >= 1000 THEN 2
            WHEN total_spent >= 500 THEN 3
            ELSE 4
        END AS segment_order,
        CASE
            WHEN total_spent >= 5000 THEN 'VIP'
            WHEN total_spent >= 1000 THEN 'High Value'
            WHEN total_spent >= 500 THEN 'Medium Value'
            ELSE 'Low Value'
        END AS customer_segment
    FROM customer_totals
)
SELECT
    customer_segment,
    COUNT(*) AS customer_count
FROM segmented_customers
GROUP BY customer_segment, segment_order
ORDER BY segment_order;
```

- Visualization: Donut Chart with percentages

#### Metric 3 — Top 20 Customers by Revenue

```sql
SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.email,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.quantity * oi.unit_price)::numeric, 2) AS total_revenue
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email
ORDER BY total_revenue DESC
LIMIT 20;
```

- Visualization: Table; conditional formatting on `total_revenue > 10000`

#### Metric 4 — Customer Order Frequency

```sql
WITH customer_orders AS (
    SELECT
        c.customer_id,
        COUNT(DISTINCT o.order_id) AS order_count
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id
),
frequency_groups AS (
    SELECT
        CASE
            WHEN order_count = 0 THEN 0
            WHEN order_count = 1 THEN 1
            WHEN order_count <= 3 THEN 2
            WHEN order_count <= 5 THEN 3
            WHEN order_count <= 10 THEN 4
            ELSE 5
        END AS frequency_order,
        CASE
            WHEN order_count = 0 THEN 'No Orders'
            WHEN order_count = 1 THEN '1 Order'
            WHEN order_count <= 3 THEN '2-3 Orders'
            WHEN order_count <= 5 THEN '4-5 Orders'
            WHEN order_count <= 10 THEN '6-10 Orders'
            ELSE '10+ Orders'
        END AS order_frequency
    FROM customer_orders
)
SELECT
    order_frequency,
    COUNT(*) AS customer_count
FROM frequency_groups
GROUP BY order_frequency, frequency_order
ORDER BY frequency_order;
```

- Visualization: Donut Chart

---

### 5.4 Funnel Analysis Dashboard (Optional)

| Field | Value |
|-------|-------|
| Purpose | Event-stream funnel and traffic-pattern analysis |
| Audience | Growth, marketing, product analytics |
| Visualizations | 4 |

#### Metric 1 — Event Type Distribution

```sql
SELECT
    event_type,
    COUNT(*) AS event_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM events
GROUP BY event_type
ORDER BY event_count DESC;
```

- Visualization: Pie Chart

#### Metric 2 — Device Type Performance

```sql
SELECT
    device_type,
    COUNT(*) AS total_events,
    COUNT(DISTINCT session_id) AS unique_sessions,
    COUNT(CASE WHEN event_type = 'page_view' THEN 1 END) AS page_views,
    COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END) AS add_to_cart,
    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) AS purchases
FROM events
GROUP BY device_type
ORDER BY total_events DESC;
```

- Visualization: Grouped Bar Chart or Table

#### Metric 3 — Hourly Activity Pattern

```sql
SELECT
    EXTRACT(HOUR FROM event_timestamp) AS hour_of_day,
    COUNT(*) AS event_count,
    COUNT(DISTINCT session_id) AS unique_sessions
FROM events
GROUP BY EXTRACT(HOUR FROM event_timestamp)
ORDER BY hour_of_day;
```

- Visualization: Line Chart

#### Metric 4 — Daily Event Trends

```sql
SELECT
    DATE(event_timestamp) AS event_date,
    COUNT(*) AS total_events,
    COUNT(DISTINCT session_id) AS unique_sessions
FROM events
WHERE event_timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(event_timestamp)
ORDER BY event_date DESC
LIMIT 30;
```

- Visualization: Multi-line Chart

---

## 6. SQL Query Reference

This section consolidates utility queries used for ad-hoc analysis and validation.

### 6.1 Utility Queries

#### Orders by Day of Week

```sql
SELECT
    TO_CHAR(order_date, 'Day') AS day_name,
    EXTRACT(DOW FROM order_date) AS day_number,
    COUNT(*) AS order_count,
    ROUND(AVG(order_total)::numeric, 2) AS avg_order_value
FROM orders
GROUP BY day_name, day_number
ORDER BY day_number;
```

#### Revenue by Payment Method

```sql
SELECT
    payment_method,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(SUM(order_total)::numeric, 2) AS total_revenue
FROM orders
GROUP BY payment_method
ORDER BY total_revenue DESC;
```

#### New vs Returning Customers

```sql
WITH first_orders AS (
    SELECT customer_id, MIN(order_date) AS first_date FROM orders GROUP BY customer_id
)
SELECT
    CASE WHEN o.order_date = fo.first_date THEN 'New' ELSE 'Returning' END AS customer_type,
    COUNT(DISTINCT o.customer_id) AS customers
FROM orders o JOIN first_orders fo ON o.customer_id = fo.customer_id
GROUP BY customer_type;
```

### 6.2 Data Verification Queries

#### Row Count Validation

```sql
SELECT 'Customers' AS table_name, COUNT(*) AS count FROM customers
UNION ALL SELECT 'Orders', COUNT(*) FROM orders
UNION ALL SELECT 'Order Items', COUNT(*) FROM order_items
UNION ALL SELECT 'Products', COUNT(*) FROM products
UNION ALL SELECT 'Events', COUNT(*) FROM events;
```

Expected output:

| table_name  | count  |
|-------------|--------|
| Customers   | 1,000  |
| Orders      | 5,000  |
| Order Items | 9,994  |
| Products    | 20     |
| Events      | 50,000 |

#### Orphaned Record Check

```sql
-- Orders without a matching customer (must return 0)
SELECT COUNT(*) FROM orders o LEFT JOIN customers c
  ON o.customer_id = c.customer_id WHERE c.customer_id IS NULL;

-- Order items without a parent order (must return 0)
SELECT COUNT(*) FROM order_items oi LEFT JOIN orders o
  ON oi.order_id = o.order_id WHERE o.order_id IS NULL;
```

---

## 7. Troubleshooting

### Symptom — `ERROR: column "<alias>" does not exist`

**Cause.** Metabase's SQL parser does not resolve column aliases inside `GROUP BY`/`ORDER BY` clauses.

**Resolution.** Use a CTE to materialise the alias as a real column before grouping.

Incorrect:

```sql
SELECT CASE ... END AS my_alias
FROM source
GROUP BY my_alias;            -- Error
```

Correct:

```sql
WITH temp AS (
    SELECT
        CASE ... END AS my_alias,
        CASE ... END AS sort_col
    FROM source
)
SELECT my_alias, COUNT(*) FROM temp
GROUP BY my_alias, sort_col
ORDER BY sort_col;
```

### Symptom — Query returns no rows

**Possible causes.**

1. Date range filter excludes all data (e.g. dates fall outside the source data window).
2. Column reference does not exist (e.g. `p.rating` instead of `p.rating_rate`).
3. `INNER JOIN` filters out all matching records — switch to `LEFT JOIN` if appropriate.

**Diagnostic queries.**

```sql
-- Confirm date coverage
SELECT MIN(order_date), MAX(order_date) FROM orders;

-- Confirm rows exist
SELECT COUNT(*) FROM products;

-- Confirm column nullability
SELECT COUNT(*) FROM products WHERE rating_rate IS NULL;

-- Validate base query before applying joins
SELECT * FROM orders LIMIT 5;
```

### Symptom — Query runs longer than 10 seconds

**Resolution sequence.**

1. Apply the indexes documented in [section 8](#8-performance-tuning).
2. Inspect the query plan with `EXPLAIN ANALYZE`.
3. Reduce CTE depth, eliminate `SELECT *`, push filters before joins.

---

## 8. Performance Tuning

### Required Indexes

```sql
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
```

### Performance Targets

| Query type | Target latency |
|------------|----------------|
| Simple metrics (count/sum) | <500 ms |
| Medium queries (5-table joins) | <2 s |
| Complex dashboards (CTEs) | <5 s |

### Optimisation Checklist

- Indexed columns in `WHERE` and `JOIN` predicates
- `COALESCE` for NULL handling in aggregates
- `ROUND` for decimal output
- `LIMIT` for preview/inspection queries
- `DATE_TRUNC` for date grouping

---

## 9. UI Reference

### Create a Native Question

1. Click `+ New` → `Question`.
2. Select `Native query` (SQL).
3. Paste SQL.
4. Click `▶ Execute` (or `Ctrl+Enter`).
5. Verify results.
6. Click `Save`.

### Create a Dashboard

1. Click `+ New` → `Dashboard`.
2. Enter name and description.
3. Click `Create`.
4. Click `+ Add a question` and select saved questions or create new ones inline.

### Number Formatting

- Currency: Settings → Number → Currency → USD
- Percentages: Settings → Number → Percent
- Dates: Settings → Date → Format (e.g. `MMM YYYY`)

### Visualization Selector Reference

| Use case | Visualization |
|----------|---------------|
| Single metric | Number |
| Categorical comparison | Bar Chart |
| Time series | Line Chart |
| Correlation between two measures | Scatter Plot |
| Segment proportions | Donut Chart |
| Detailed records | Table |
