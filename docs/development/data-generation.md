# Synthetic Data Generation Runbook

## Purpose

Generate the synthetic source dataset (customers, orders, order items, clickstream events) and load it into the PostgreSQL `ecommerce` database for local development and CI testing.

| Dataset | Records | Description |
|---------|---------|-------------|
| customers | 1,000 | Customer profiles with SCD Type 2 segment history |
| orders | 5,000 | E-commerce transactions |
| order_items | ~12,500 | Line items (avg. 2.5 per order) |
| clickstream_events | 50,000 | User-behaviour events |

---

## Prerequisites

### 1. Docker services

```bash
docker-compose up -d
docker ps
```

The `ecommerce-postgres` container must be reported `Healthy`. The Airflow services are not required for this runbook but typically come up in the same compose stack.

### 2. Python environment

```bash
# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Environment variables

`.env` must contain:

```env
POSTGRES_SOURCE_HOST=localhost
POSTGRES_SOURCE_PORT=5432
POSTGRES_SOURCE_USER=ecommerce_user
POSTGRES_SOURCE_PASSWORD=ecommerce_pass
POSTGRES_SOURCE_DB=ecommerce
```

> **Note:** `localhost:5432` reaches the consolidated `postgres` container's exposed port from the host. Inside the Docker network, services reach the database via host name `postgres`.

---

## Deployment Steps

### 1. Generate CSV files

```bash
python scripts/generate_data.py
```

Expected output (truncated):

```
Starting Data Generation Process
Generating 1000 customers...
Generated 1000 customers
   Segment distribution: {'bronze': 500, 'silver': 300, 'gold': 150, 'platinum': 50}
Generating 5000 orders...
Generated 5000 orders
Generating order items for 5000 orders...
Generated 12500 order items
Generating 50000 clickstream events...
Generated 50000 clickstream events
Saved: data/generated/customers.csv
Saved: data/generated/orders.csv
Saved: data/generated/order_items.csv
Saved: data/generated/clickstream_events.csv
DATA GENERATION SUMMARY
Customers:           1,000
Orders:              5,000
Order Items:         12,500
Clickstream Events:  50,000
Output Directory:    data/generated/
Status:              completed
```

Output files:

- `data/generated/customers.csv` (~150 KB)
- `data/generated/orders.csv` (~500 KB)
- `data/generated/order_items.csv` (~300 KB)
- `data/generated/clickstream_events.csv` (~8 MB)

### 2. Inspect generated CSVs (optional)

```bash
# macOS / Linux
head -n 5 data/generated/customers.csv

# Windows PowerShell
Get-Content data\generated\customers.csv | Select-Object -First 5
```

```python
import pandas as pd
df = pd.read_csv('data/generated/customers.csv')
print(df.head())
print(f"Shape: {df.shape}")
```

### 3. Load CSVs into PostgreSQL

```bash
python scripts/load_data.py
```

The script truncates the target tables and reloads via `psycopg2.execute_values`. Expected output (truncated):

```
Connected to PostgreSQL database
Loading customers from data/generated/customers.csv...
   Truncated existing customers table
Loaded 1,000 customers
Loading orders from data/generated/orders.csv...
   Truncated existing orders table
Loaded 5,000 orders
Loading order items from data/generated/order_items.csv...
   Truncated existing order_items table
Loaded 12,500 order items
DATA VALIDATION
Customers:                            1,000
Orders:                               5,000
Order Items:                          12,500
Orphan orders (must be 0):            0
Invalid order totals (must be 0):     0
Order date range:                     2023-10-28 to 2025-10-28
Status:                               completed
```

---

## Validation

### 4.1 Database queries

```bash
docker exec -it ecommerce-postgres \
    psql -U ecommerce_user -d ecommerce
```

```sql
-- Row counts
SELECT 'customers'   AS table_name, COUNT(*) FROM customers
UNION ALL
SELECT 'orders',     COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items;

-- Customer segment distribution
SELECT customer_segment, COUNT(*) AS count
FROM customers
WHERE is_current = TRUE
GROUP BY customer_segment
ORDER BY count DESC;

-- Order status distribution
SELECT order_status, COUNT(*) AS count
FROM orders
GROUP BY order_status
ORDER BY count DESC;

-- Sample order with line items
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
```

### 4.2 Programmatic checks (optional)

```python
import pandas as pd

customers = pd.read_csv('data/generated/customers.csv')
orders    = pd.read_csv('data/generated/orders.csv')
items     = pd.read_csv('data/generated/order_items.csv')
events    = pd.read_csv('data/generated/clickstream_events.csv')

print(f"Customers           : {len(customers)} (unique emails: {customers['email'].nunique()})")
print(f"Orders              : {len(orders)}")
print(f"Order date range    : {orders['order_date'].min()} → {orders['order_date'].max()}")
print(f"Avg order value     : ${orders['order_total'].mean():.2f}")
print(f"Order items         : {len(items)} (avg/order: {len(items)/len(orders):.2f})")
print(f"Clickstream events  : {len(events)}")
```

### 4.3 Success criteria

- All four CSV files exist in `data/generated/`
- PostgreSQL row counts match the dataset summary table above
- Orphan orders count is `0`
- Invalid order totals count is `0`
- Order date range spans `2023-10-28` to `2025-10-28`

---

## Built-in Data-Quality Checks

The `load_data.py` script enforces:

**Referential integrity**

- All `orders.customer_id` values resolve to a `customers.customer_id`
- All `order_items.order_id` values resolve to an `orders.order_id`

**Data validity**

- No negative `order_total`
- No zero-or-negative `quantity`
- All required fields populated

**Uniqueness**

- `customers.email` is globally unique
- No duplicate `order_id`

---

## Troubleshooting

### Symptom — `psycopg2.OperationalError: could not connect to server`

```bash
docker ps | grep postgres
docker-compose up -d postgres        # if not running
docker logs ecommerce-postgres
```

Confirm port `5432` is reachable from the host:

```bash
# macOS / Linux
nc -zv localhost 5432

# Windows
netstat -an | findstr 5432
```

### Symptom — `FileNotFoundError: data/generated/customers.csv`

```bash
mkdir -p data/generated
python scripts/generate_data.py
```

### Symptom — `psycopg2.errors.UniqueViolation`

`load_data.py` truncates target tables before insertion. If the `TRUNCATE` itself fails (e.g. due to active connections), force-truncate manually:

```bash
docker exec -it ecommerce-postgres \
    psql -U ecommerce_user -d ecommerce \
    -c "TRUNCATE TABLE order_items, orders, customers CASCADE;"
python scripts/load_data.py
```

### Symptom — `psycopg2.errors.InsufficientPrivilege`

Reapply privileges as the `postgres` superuser:

```bash
docker exec -it ecommerce-postgres psql -U postgres
```

```sql
GRANT ALL PRIVILEGES ON ALL TABLES   IN SCHEMA public TO ecommerce_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ecommerce_user;
\q
```

---

## Dataset Characteristics

### Customer data

**Segment distribution** (target hierarchy):

- Bronze: 50% (500)
- Silver: 30% (300)
- Gold: 15% (150)
- Platinum: 5% (50)

**SCD Type 2 support:**

- ~30% of customers have at least one historical segment row
- `is_current = TRUE` indicates the active row
- `segment_start_date` and `segment_end_date` bound each version

### Order data

**Temporal patterns:**

- Span: `2023-10-28` → `2025-10-28` (two years)
- Peak hours: 11:00–12:00 and 20:00–22:00
- Higher frequency on evenings and weekends

**Order values by segment:**

- Bronze: $20–$150
- Silver: $40–$200
- Gold: $80–$400
- Platinum: $150–$800

**Pareto distribution:** ~20% of customers generate ~80% of orders.

### Clickstream events

**Event distribution:**

- `page_view`: 60%
- `add_to_cart`: 15%
- `search`: 12%
- `purchase`: 8%
- `remove_from_cart`: 5%

**Device usage:**

- Mobile: 65%
- Desktop: 30%
- Tablet: 5%

---

## References

- Generation script: `scripts/generate_data.py`
- Loader script: `scripts/load_data.py`
- Source schema DDL: `scripts/init_db.sql`
- Multi-database bootstrap (consolidated container): `scripts/init_multi_db.sh`
