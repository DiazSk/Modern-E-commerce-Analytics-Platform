# Marts - Dimensions

## Purpose
Dimension tables providing descriptive attributes for fact table analysis.

## Models
- `dim_customers.sql` - Customer master with SCD Type 2 tracking
- `dim_products.sql` - Product catalog with current attributes
- `dim_date.sql` - Date dimension with fiscal calendar support

## Materialization Strategy
- **Type:** Full refresh tables (except dim_customers which uses SCD Type 2)
- **Update Frequency:** Daily
- **Surrogate Keys:** Auto-generated integer keys

## Slowly Changing Dimensions (SCD)

### dim_customers (Type 2)
Tracks historical changes in customer attributes over time.

**Columns:**
- `customer_key` - Surrogate key (PK)
- `customer_id` - Natural key (business key)
- `customer_segment` - Segmentation (e.g., VIP, Regular, New)
- `valid_from` - Record effective start date
- `valid_to` - Record effective end date (NULL for current)
- `is_current` - Boolean flag for active record

**Example:**
```
customer_key | customer_id | segment | valid_from | valid_to   | is_current
-------------|-------------|---------|------------|------------|------------
1            | C001        | New     | 2023-01-01 | 2023-06-01 | False
2            | C001        | Regular | 2023-06-01 | 2024-01-01 | False  
3            | C001        | VIP     | 2024-01-01 | NULL       | True
```

### dim_products (Type 1)
Current state only - overwrites on change.

**Columns:**
- `product_key` - Surrogate key (PK)
- `product_id` - Natural key
- `product_name`
- `category`
- `price`
- `rating`
- `stock_status`

### dim_date
Pre-populated calendar dimension (2023-2030).

**Columns:**
- `date_key` - YYYYMMDD integer (PK)
- `date` - Actual date
- `year`, `quarter`, `month`, `week`
- `day_of_week`, `day_name`
- `is_weekend`, `is_holiday`
- `fiscal_year`, `fiscal_quarter`

## Dependencies
- `stg_orders` → dim_customers (for customer attributes)
- `stg_products` → dim_products
- None → dim_date (static seed or generated)

## Data Quality Checks
- [ ] Surrogate keys uniqueness
- [ ] Natural keys not null
- [ ] SCD Type 2 validity: valid_from < valid_to
- [ ] Only one is_current = True per natural key
- [ ] Date dimension covers required date range
- [ ] Product prices > 0
- [ ] Customer segments in predefined list
