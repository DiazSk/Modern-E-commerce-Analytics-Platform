# 📖 Data Dictionary - Modern E-Commerce Analytics Platform

**Complete reference for all tables, columns, and relationships**

**Last Updated:** November 6, 2025  
**Database:** PostgreSQL 14  
**Schema:** public

---

## 📑 Table of Contents

1. [Source Tables](#source-tables)
   - [customers](#customers-table)
   - [orders](#orders-table)
   - [order_items](#order-items-table)
   - [products](#products-table)
   - [events](#events-table)
2. [Dimensional Tables](#dimensional-tables)
   - [dim_customers](#dim_customers-table)
   - [dim_products](#dim_products-table)
   - [dim_date](#dim_date-table)
3. [Fact Tables](#fact-tables)
   - [fact_orders](#fact_orders-table)
4. [Relationships](#table-relationships)
5. [Business Logic](#business-logic-reference)

---

## 📊 SOURCE TABLES

### customers Table

**Purpose:** Core customer master data with SCD Type 2 tracking

| Column Name | Data Type | Nullable | Description | Business Rules | Example |
|-------------|-----------|----------|-------------|----------------|---------|
| `customer_id` | SERIAL | NO | Primary key, auto-increment | Unique identifier | 1 |
| `email` | VARCHAR(255) | NO | Customer email (unique) | Valid email format, used for login | `john.doe@example.com` |
| `first_name` | VARCHAR(100) | NO | Customer first name | - | `John` |
| `last_name` | VARCHAR(100) | NO | Customer last name | - | `Doe` |
| `phone` | VARCHAR(20) | YES | Contact phone number | Format varies by region | `555-0123` |
| `registration_date` | DATE | NO | Account creation date | Cannot be future date | `2024-03-15` |
| `customer_segment` | VARCHAR(20) | NO | Current loyalty tier | Values: bronze, silver, gold, platinum | `gold` |
| `segment_start_date` | DATE | NO | When current segment began | >= registration_date | `2024-06-01` |
| `segment_end_date` | DATE | YES | When segment ended (NULL if current) | > segment_start_date if not NULL | `NULL` |
| `is_current` | BOOLEAN | NO | Current record flag (SCD Type 2) | Only one TRUE per customer | `TRUE` |
| `created_at` | TIMESTAMP | NO | Record creation timestamp | Auto-generated | `2024-03-15 10:30:45` |
| `updated_at` | TIMESTAMP | NO | Last update timestamp | Auto-updated via trigger | `2024-06-01 14:22:10` |

**Primary Key:** `customer_id`  
**Unique Constraints:** `email`  
**Indexes:** `idx_customers_email`, `idx_customers_segment`, `idx_customers_is_current`

**Business Logic:**
- Customer segments upgrade/downgrade based on total spend
- SCD Type 2 tracks historical segments (segment_end_date set when changing)
- Only one record per customer has `is_current = TRUE`

**Row Count:** 1,000

---

### orders Table

**Purpose:** Transactional order records

| Column Name | Data Type | Nullable | Description | Business Rules | Example |
|-------------|-----------|----------|-------------|----------------|---------|
| `order_id` | SERIAL | NO | Primary key, auto-increment | Unique order identifier | 1234 |
| `customer_id` | INTEGER | NO | Foreign key to customers | Must exist in customers table | 567 |
| `order_date` | TIMESTAMP | NO | When order was placed | Cannot be future date | `2025-10-15 14:23:45` |
| `order_total` | DECIMAL(10,2) | NO | Total order amount | >= 0, sum of line items | `157.98` |
| `payment_method` | VARCHAR(50) | NO | Payment type used | credit_card, debit_card, paypal, apple_pay, google_pay | `credit_card` |
| `shipping_address` | TEXT | YES | Delivery address | - | `123 Main St, City` |
| `order_status` | VARCHAR(20) | NO | Current order status | pending, processing, completed, cancelled, returned | `completed` |
| `created_at` | TIMESTAMP | NO | Record creation | Auto-generated | `2025-10-15 14:23:45` |
| `updated_at` | TIMESTAMP | NO | Last update | Auto-updated via trigger | `2025-10-16 09:15:22` |

**Primary Key:** `order_id`  
**Foreign Keys:** `customer_id` → `customers(customer_id)`  
**Indexes:** `idx_orders_customer_id`, `idx_orders_order_date`, `idx_orders_status`, `idx_orders_date_customer` (composite)

**Business Logic:**
- Order total calculated from order_items sum
- Status workflow: pending → processing → completed
- Can be cancelled or returned post-completion

**Row Count:** 5,000

---

### order_items Table

**Purpose:** Order line items (one row per product in order)

| Column Name | Data Type | Nullable | Description | Business Rules | Example |
|-------------|-----------|----------|-------------|----------------|---------|
| `order_item_id` | SERIAL | NO | Primary key | Unique line item identifier | 9876 |
| `order_id` | INTEGER | NO | Foreign key to orders | Must exist in orders, CASCADE delete | 1234 |
| `product_id` | INTEGER | NO | Product identifier | References products catalog | 5 |
| `quantity` | INTEGER | NO | Quantity ordered | > 0 | 2 |
| `unit_price` | DECIMAL(10,2) | NO | Price per unit at order time | >= 0, captured at purchase | `29.99` |
| `discount_amount` | DECIMAL(10,2) | NO | Discount applied | >= 0, <= quantity * unit_price | `5.00` |
| `line_total` | DECIMAL(10,2) | NO | Calculated total | GENERATED: quantity * unit_price - discount | `54.98` |
| `created_at` | TIMESTAMP | NO | Record creation | Auto-generated | `2025-10-15 14:23:45` |

**Primary Key:** `order_item_id`  
**Foreign Keys:** 
- `order_id` → `orders(order_id)` ON DELETE CASCADE
- `product_id` → `products(product_id)` (logical, not enforced)

**Indexes:** `idx_order_items_order_id`, `idx_order_items_product_id`

**Business Logic:**
- line_total is GENERATED column (automatically calculated)
- unit_price captured at order time (historical pricing)
- One order can have multiple line items

**Row Count:** 9,994

---

### products Table

**Purpose:** Product catalog from external API

| Column Name | Data Type | Nullable | Description | Business Rules | Example |
|-------------|-----------|----------|-------------|----------------|---------|
| `product_id` | INTEGER | NO | Primary key | From FakeStore API | 1 |
| `title` | VARCHAR(500) | YES | Product name | Full descriptive title | `Fjallraven Backpack` |
| `price` | DECIMAL(10,2) | YES | Current price | >= 0 | `109.95` |
| `category` | VARCHAR(100) | YES | Product category | women's clothing, men's clothing, electronics, jewelery | `men's clothing` |
| `description` | TEXT | YES | Product description | Full marketing copy | `Perfect backpack for...` |
| `image` | VARCHAR(500) | YES | Image URL | FakeStore CDN link | `https://fakestoreapi.com/img/...` |
| `rating_rate` | DECIMAL(3,2) | YES | **Product rating (0-5)** | **NOT "rating"!** | `3.90` |
| `rating_count` | INTEGER | YES | **Number of reviews** | Count of ratings | `120` |
| `ingestion_timestamp` | TIMESTAMP | YES | When data was pulled | API extraction time | `2025-10-28 23:19:39` |
| `ingestion_date` | DATE | YES | Ingestion date partition | For data lake organization | `2025-10-27` |
| `data_source` | VARCHAR(50) | YES | Source system | Always 'fakestoreapi' | `fakestoreapi` |
| `created_at` | TIMESTAMP | YES | Record creation | First seen in database | `2025-11-02 23:42:41` |

**Primary Key:** `product_id`  
**Indexes:** `idx_products_category`, `idx_products_price`

**⚠️ CRITICAL NOTES:**
- Rating is stored as **TWO columns**: `rating_rate` and `rating_count`
- NOT a single `rating` column!
- Original API returns: `{"rating": {"rate": 3.9, "count": 120}}`
- We split into two columns for easier querying

**Common Query Pattern:**
```sql
-- Correct ✅
SELECT p.rating_rate AS product_rating, p.rating_count
FROM products p;

-- Wrong ❌
SELECT p.rating FROM products p;  -- Column doesn't exist!
```

**Row Count:** 20 (FakeStore API catalog size)

---

### events Table

**Purpose:** Clickstream/user behavior tracking

| Column Name | Data Type | Nullable | Description | Business Rules | Example |
|-------------|-----------|----------|-------------|----------------|---------|
| `event_id` | SERIAL | NO | Primary key | Unique event identifier | 12345 |
| `session_id` | VARCHAR(100) | YES | User session ID | Groups events in same session | `session_789` |
| `user_id` | INTEGER | YES | Customer identifier | May be NULL for anonymous | `567` |
| `event_type` | VARCHAR(50) | YES | Type of event | page_view, add_to_cart, purchase, search | `page_view` |
| `event_timestamp` | TIMESTAMP | YES | When event occurred | Should have 24-hour distribution | `2025-11-01 15:34:22` |
| `page_url` | VARCHAR(255) | YES | URL visited | Relative path | `/product/5` |
| `product_id` | INTEGER | YES | Product viewed/clicked | References products | 5 |
| `device_type` | VARCHAR(50) | YES | Device used | mobile, desktop, tablet | `mobile` |
| `browser` | VARCHAR(50) | YES | Browser used | Chrome, Safari, Firefox, Edge | `Chrome` |
| `country` | VARCHAR(50) | YES | User location | ISO country code | `USA` |

**Primary Key:** `event_id`  
**Foreign Keys:** `product_id` → `products(product_id)` (logical)  
**Indexes:** `idx_events_timestamp`, `idx_events_type`, `idx_events_session`

**Business Logic:**
- Events track user journey: view → cart → purchase
- Session groups related events (same browsing session)
- Timestamps should have realistic hourly distribution (not all midnight!)

**Row Count:** 50,000

**Event Type Distribution:**
- page_view: 33.37% (~16,686 events)
- add_to_cart: 33.02% (~16,510 events)
- purchase: 33.61% (~16,804 events)

---

## 🎯 DIMENSIONAL TABLES

### dim_customers Table (SCD Type 2)

**Purpose:** Customer dimension with historical tracking

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `customer_key` | INTEGER | Surrogate primary key | 1001 |
| `customer_id` | INTEGER | Natural key from source | 567 |
| `full_name` | VARCHAR(200) | First + Last name | `John Doe` |
| `email` | VARCHAR(255) | Customer email | `john.doe@example.com` |
| `customer_segment` | VARCHAR(20) | Segment at this time | `gold` |
| `valid_from` | DATE | Record valid start date | `2024-06-01` |
| `valid_to` | DATE | Record valid end date | `2024-12-31` or NULL |
| `is_current` | BOOLEAN | Current record flag | TRUE or FALSE |

**SCD Type 2 Design:**
- Multiple rows per customer (one per segment change)
- Only one row has `is_current = TRUE`
- Historical analysis possible: "What were gold customers buying in June?"

---

### dim_products Table

**Purpose:** Product dimension (slowly changing)

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `product_key` | INTEGER | Surrogate primary key |
| `product_id` | INTEGER | Natural key |
| `title` | VARCHAR(500) | Product name |
| `category` | VARCHAR(100) | Product category |
| `price` | DECIMAL(10,2) | Current price |
| `rating_rate` | DECIMAL(3,2) | Product rating |
| `rating_count` | INTEGER | Number of reviews |

---

### dim_date Table

**Purpose:** Date dimension for time-based analysis

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `date_key` | INTEGER | Primary key (YYYYMMDD) | 20251015 |
| `full_date` | DATE | Actual date | `2025-10-15` |
| `year` | INTEGER | Year | 2025 |
| `quarter` | INTEGER | Quarter (1-4) | 4 |
| `month` | INTEGER | Month (1-12) | 10 |
| `month_name` | VARCHAR(10) | Month name | `October` |
| `day` | INTEGER | Day of month | 15 |
| `day_of_week` | INTEGER | Day number (0-6) | 2 |
| `day_name` | VARCHAR(10) | Day name | `Tuesday` |
| `is_weekend` | BOOLEAN | Weekend flag | FALSE |

**Usage:** Join fact tables on order_date for time analysis

---

## 🔗 FACT TABLES

### fact_orders Table

**Purpose:** Fact table for order analytics (star schema)

| Column Name | Data Type | Description | Grain |
|-------------|-----------|-------------|-------|
| `order_key` | INTEGER | Surrogate PK | One row per order line item |
| `customer_key` | INTEGER | FK to dim_customers | - |
| `product_key` | INTEGER | FK to dim_products | - |
| `date_key` | INTEGER | FK to dim_date | - |
| `quantity` | INTEGER | Units ordered | Measure |
| `unit_price` | DECIMAL(10,2) | Price per unit | Measure |
| `discount_amount` | DECIMAL(10,2) | Discount applied | Measure |
| `line_total` | DECIMAL(10,2) | Total line amount | Calculated measure |

**Grain:** One row per product per order (order line item level)

**Measures:**
- Additive: quantity, discount_amount, line_total
- Semi-additive: unit_price (average, not sum)

---

## 🔗 TABLE RELATIONSHIPS

### Entity Relationship Diagram (Text)

```
customers (1) ──────< (M) orders
    │
    │ customer_id
    │
    └─────────────────────┐
                          │
orders (1) ──────< (M) order_items
    │
    │ order_id
    │
    └─────────────────────┐
                          │
products (1) ──────< (M) order_items
    │
    │ product_id
    │
    └─────────────────────┐
                          │
events (M) ───────> (1) products (optional)
    │
    │ product_id
```

**Relationship Types:**
- customers → orders: One-to-Many (one customer, many orders)
- orders → order_items: One-to-Many (one order, many line items)
- products → order_items: One-to-Many (one product, many order lines)
- products → events: One-to-Many (optional, events can exist without product)

**Referential Integrity:**
- ✅ Enforced: customers ← orders, orders ← order_items
- ⚠️ Logical only: products ← order_items (product_id is INTEGER, not FK)

---

## 💼 BUSINESS LOGIC REFERENCE

### Customer Segmentation Rules

**Segment Assignment (Based on Total Lifetime Spend):**
```
Bronze:   $0 - $499       (Default tier, 50% of customers)
Silver:   $500 - $999     (30% of customers)
Gold:     $1,000 - $4,999 (15% of customers)
Platinum: $5,000+         (5% of customers - VIP)
```

**Segment Benefits:**
- Bronze: Standard shipping, no discounts
- Silver: Free shipping over $50, 5% birthday discount
- Gold: Free shipping always, 10% birthday discount, early access
- Platinum: Free expedited shipping, 15% always, dedicated support

**Upgrade Logic:**
```sql
-- Customer upgrades when cumulative spend crosses threshold
UPDATE customers
SET customer_segment = 'gold',
    segment_start_date = CURRENT_DATE
WHERE total_lifetime_spend >= 1000 
  AND customer_segment != 'gold';
```

---

### Order Status Workflow

**Status Progression:**
```
pending → processing → completed
   ↓           ↓
cancelled   cancelled
   ↓
returned (only from completed)
```

**Business Rules:**
- Orders start as `pending` when created
- Move to `processing` when payment confirmed
- Move to `completed` when shipped
- Can be `cancelled` from pending/processing
- Can be `returned` only from completed (within 30 days)

**Status Distribution (Your Data):**
- completed: 75%
- pending: 10%
- processing: 8%
- cancelled: 5%
- returned: 2%

---

### Discount Logic

**Discount Rules:**
- 20% of orders have discounts
- Maximum discount: 30% of line item total
- Applied at order_item level, not order level
- Stored as `discount_amount` in dollars (not percentage)

**Calculation:**
```sql
line_total = (quantity * unit_price) - discount_amount
```

---

### Product Pricing

**Price Updates:**
- Prices from API are current at ingestion time
- Historical pricing NOT tracked (limitation)
- order_items.unit_price captures price at purchase time

**Price Ranges (Your Data):**
- Minimum: $7.95
- Maximum: $999.99
- Average: ~$70
- Median: ~$50

---

### Event Tracking

**Event Types:**
1. **page_view:** User views product page
2. **add_to_cart:** User adds product to cart
3. **purchase:** User completes purchase
4. **search:** User searches for products (not implemented yet)

**Session Logic:**
- Session ID groups events in same browsing session
- Session typically 30 minutes of activity
- Same user can have multiple sessions

**Conversion Funnel:**
```
page_view → add_to_cart → purchase

Expected conversion rates:
- View to Cart: 10-15%
- Cart to Purchase: 25-35%
- Overall: 3-6%
```

---

## 📊 Analytics Use Cases

### Customer Lifetime Value (CLV)
```sql
SELECT 
    customer_id,
    SUM(oi.quantity * oi.unit_price) AS lifetime_value
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY customer_id;
```

### Top Products by Revenue
```sql
SELECT 
    p.title,
    SUM(oi.quantity * oi.unit_price) AS total_revenue
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.title
ORDER BY total_revenue DESC
LIMIT 10;
```

### Customer Retention Rate
```sql
WITH first_orders AS (
    SELECT customer_id, MIN(order_date) AS first_order
    FROM orders GROUP BY customer_id
)
SELECT 
    DATE_TRUNC('month', first_order) AS cohort,
    COUNT(DISTINCT CASE WHEN o.order_date <= first_order + INTERVAL '30 days' THEN o.customer_id END) AS month_0,
    COUNT(DISTINCT CASE WHEN o.order_date <= first_order + INTERVAL '60 days' THEN o.customer_id END) AS month_1
FROM first_orders fo
JOIN orders o ON fo.customer_id = o.customer_id
GROUP BY cohort;
```

---

## 🔍 Data Quality Rules

### Schema Validation

**customers:**
- email must be unique
- customer_segment must be in ('bronze', 'silver', 'gold', 'platinum')
- segment_end_date must be > segment_start_date if not NULL
- Only one row per customer_id can have is_current = TRUE

**orders:**
- order_total must be >= 0
- payment_method must be valid enum
- order_status must be valid enum
- customer_id must exist in customers

**order_items:**
- quantity must be > 0
- unit_price must be >= 0
- discount_amount must be >= 0 and <= (quantity * unit_price)
- order_id must exist in orders

**products:**
- product_id must be unique
- rating_rate must be between 0.00 and 5.00
- rating_count must be >= 0

---

## 📈 Statistics Summary

### Table Statistics

| Table | Rows | Avg Row Size | Total Size |
|-------|------|--------------|------------|
| customers | 1,000 | ~500 bytes | ~500 KB |
| orders | 5,000 | ~300 bytes | ~1.5 MB |
| order_items | 9,994 | ~200 bytes | ~2 MB |
| products | 20 | ~1 KB | ~20 KB |
| events | 50,000 | ~250 bytes | ~12.5 MB |

**Total Database Size:** ~16.5 MB (small for development, scales linearly)

---

## 🔐 Access Control (Future)

**Planned Row-Level Security:**
- Sales reps: See only their assigned customers
- Regional managers: See only their region
- Executives: See all data
- External partners: Read-only on specific products

**Implementation:**
```sql
-- Example RLS policy
CREATE POLICY sales_rep_policy ON orders
    FOR SELECT
    USING (customer_id IN (
        SELECT customer_id FROM customer_assignments 
        WHERE sales_rep_id = current_user_id()
    ));
```

---

## 📝 Change Log

**Version 1.0 (Week 1):**
- Initial schema created
- customers, orders, order_items tables

**Version 1.1 (Week 2):**
- Added products table
- Added events table

**Version 1.2 (Week 6):**
- Verified rating_rate/rating_count columns
- Added indexes for performance
- Updated events with 24-hour distribution

---

**This data dictionary is your schema reference!**  
**Use it when writing queries to avoid "column does not exist" errors!** 🎯

*Last Updated: November 6, 2025 | Week 6 Complete*
