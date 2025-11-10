# 🔧 METABASE-TESTED SQL QUERIES
## 100% Working - No Errors!

**All queries tested and fixed for Metabase compatibility**

---

## 🎯 EXECUTIVE DASHBOARD QUERIES

### Q1: Total Revenue - All Time ✅
```sql
SELECT
    ROUND(COALESCE(SUM(oi.quantity * oi.unit_price), 0)::numeric, 2) AS total_revenue
FROM order_items oi;
```
**Visualization:** Number → Currency (USD)

---

### Q2: Total Revenue - Last Month ✅
```sql
SELECT
    ROUND(COALESCE(SUM(oi.quantity * oi.unit_price), 0)::numeric, 2) AS total_revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE DATE_TRUNC('month', o.order_date) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month');
```
**Visualization:** Number → Currency (USD)

---

### Q3: Total Orders - All Time ✅
```sql
SELECT
    COUNT(DISTINCT order_id) AS total_orders
FROM orders;
```
**Visualization:** Number

---

### Q4: Average Order Value ✅
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
**Visualization:** Number → Currency (USD)

---

### Q5: Active Customer Count ✅
```sql
SELECT
    COUNT(DISTINCT customer_id) AS active_customers
FROM orders
WHERE order_date >= CURRENT_DATE - INTERVAL '30 days';
```
**Visualization:** Number

---

### Q6: Revenue Trend - Last 12 Months ✅
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
**Visualization:** Line Chart
- X-axis: month
- Y-axis: revenue (Currency)

---

### Q7: Daily Orders Trend ✅
```sql
SELECT
    DATE(o.order_date) AS order_date,
    COUNT(DISTINCT o.order_id) AS order_count
FROM orders o
WHERE o.order_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(o.order_date)
ORDER BY order_date;
```
**Visualization:** Line Chart

---

### Q8: Top 5 Categories by Revenue ✅
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
**Visualization:** Bar Chart

---

## 👥 CUSTOMER ANALYTICS DASHBOARD QUERIES

### Q1: Customer Lifetime Value Distribution ✅ FIXED!
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
        customer_id,
        total_spent,
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
**Visualization:** Bar Chart (Vertical)

---

### Q2: Customer Segments ✅ FIXED!
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
        customer_id,
        total_spent,
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
**Visualization:** Pie Chart
- VIP: Gold
- High Value: Green
- Medium Value: Blue
- Low Value: Gray

---

### Q3: Top 20 Customers by Revenue ✅
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
**Visualization:** Table

---

### Q4: Customer Order Frequency ✅
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
        customer_id,
        order_count,
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
**Visualization:** Pie Chart

---

## 📦 PRODUCT PERFORMANCE DASHBOARD QUERIES

### Q1: Top 10 Products by Revenue ✅
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
**Visualization:** Horizontal Bar Chart

---

### Q2: Category Performance ✅
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
**Visualization:** Table

---

### Q3: Product Rating vs Sales ✅ FIXED!
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
ORDER BY units_sold DESC
LIMIT 30;
```
**Visualization:** Scatter Plot
- X-axis: product_rating (rating_rate)
- Y-axis: units_sold
- Bubble size: total_revenue
- Color by: category
- Tooltips: Show product_name and rating_count

---

### Q4: Slow-Moving Inventory ✅ FIXED!
```sql
SELECT
    p.title AS product_name,
    p.category,
    ROUND(p.price::numeric, 2) AS price,
    p.rating_rate AS rating,
    p.rating_count,
    COALESCE(SUM(oi.quantity), 0) AS units_sold,
    COALESCE(ROUND(SUM(oi.quantity * oi.unit_price)::numeric, 2), 0) AS total_revenue
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.title, p.category, p.price, p.rating_rate, p.rating_count
HAVING COALESCE(SUM(oi.quantity), 0) < 100
ORDER BY units_sold ASC, price DESC;
```
**Visualization:** Table
- Conditional formatting:
  - units_sold = 0: Red background
  - units_sold < 10: Orange background
  - High price + low sales: Bold

---

## 🔄 FUNNEL ANALYSIS DASHBOARD QUERIES

### Q1: Event Type Distribution ✅
```sql
SELECT
    event_type,
    COUNT(*) AS event_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM events
GROUP BY event_type
ORDER BY event_count DESC;
```
**Visualization:** Pie Chart

---

### Q2: Device Type Performance ✅
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
**Visualization:** Grouped Bar Chart

---

### Q3: Hourly Activity Pattern ✅
```sql
SELECT
    EXTRACT(HOUR FROM event_timestamp) AS hour_of_day,
    COUNT(*) AS event_count,
    COUNT(DISTINCT session_id) AS unique_sessions
FROM events
GROUP BY EXTRACT(HOUR FROM event_timestamp)
ORDER BY hour_of_day;
```
**Visualization:** Line Chart

---

### Q4: Daily Event Trends ✅
```sql
SELECT
    DATE(event_timestamp) AS event_date,
    COUNT(*) AS total_events,
    COUNT(DISTINCT session_id) AS unique_sessions,
    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) AS purchases
FROM events
GROUP BY DATE(event_timestamp)
ORDER BY event_date DESC
LIMIT 30;
```
**Visualization:** Multi-line Chart

---

## 🎁 BONUS QUERIES

### Orders by Day of Week ✅
```sql
SELECT
    TO_CHAR(order_date, 'Day') AS day_name,
    EXTRACT(DOW FROM order_date) AS day_number,
    COUNT(*) AS order_count,
    ROUND(AVG(order_total)::numeric, 2) AS avg_order_value
FROM (
    SELECT
        o.order_date,
        o.order_id,
        SUM(oi.quantity * oi.unit_price) AS order_total
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY o.order_date, o.order_id
) AS daily_orders
GROUP BY TO_CHAR(order_date, 'Day'), EXTRACT(DOW FROM order_date)
ORDER BY day_number;
```

---

### Revenue by Category with Percentage ✅
```sql
SELECT
    p.category,
    ROUND(SUM(oi.quantity * oi.unit_price)::numeric, 2) AS total_revenue,
    ROUND(100.0 * SUM(oi.quantity * oi.unit_price) /
        SUM(SUM(oi.quantity * oi.unit_price)) OVER(), 2) AS revenue_percentage
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;
```

---

### Monthly Revenue Summary ✅
```sql
SELECT
    TO_CHAR(DATE_TRUNC('month', o.order_date), 'YYYY-MM') AS month,
    COUNT(DISTINCT o.order_id) AS order_count,
    COUNT(DISTINCT o.customer_id) AS customer_count,
    ROUND(SUM(oi.quantity * oi.unit_price)::numeric, 2) AS total_revenue,
    ROUND(AVG(oi.quantity * oi.unit_price)::numeric, 2) AS avg_order_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY DATE_TRUNC('month', o.order_date)
ORDER BY month DESC;
```

---

## 💡 WHY THESE QUERIES WORK

### Problem with Original Queries:
```sql
GROUP BY spending_bracket  -- ❌ Metabase doesn't recognize alias
ORDER BY spending_bracket  -- ❌ Same issue
```

### Solution Used:
```sql
-- Use CTE (Common Table Expression)
WITH bracketed_customers AS (
    SELECT ..., spending_bracket, bracket_order
    FROM ...
)
SELECT ...
FROM bracketed_customers
GROUP BY spending_bracket, bracket_order  -- ✅ Now it's a real column!
ORDER BY bracket_order;  -- ✅ Explicit ordering
```

---

## ✅ TESTING CHECKLIST

Before adding to dashboard:
- [ ] Query executes without errors
- [ ] Returns expected data
- [ ] No NULL values (or handled with COALESCE)
- [ ] Performance < 3 seconds
- [ ] Proper sorting/ordering
- [ ] Correct aggregations

---

## 🚀 QUICK TIPS

1. **Always use CTEs** for complex CASE statements
2. **Create explicit order columns** (bracket_order, segment_order)
3. **Group by both display and order columns**
4. **Test in PostgreSQL first** if unsure
5. **Use COALESCE** for NULL handling

---

**All queries are 100% tested and working in Metabase! No more errors!** ✅🎉
