# Staging - Orders

## Purpose
Clean and standardize raw order data from PostgreSQL source database.

## Models
- `stg_orders.sql` - Order header data with cleaned columns
- `stg_order_items.sql` - Order line items with product references

## Source
- **Database:** PostgreSQL
- **Schema:** public
- **Table:** orders
- **Ingestion:** Daily incremental via Airflow DAG

## Transformations Applied
1. Column renaming to snake_case convention
2. Data type casting (dates, decimals, integers)
3. Null handling for optional fields
4. Timezone standardization to UTC
5. Status code mapping to descriptive values

## Dependencies
- Source: `raw_orders` (S3 parquet files)
- Next Layer: `intermediate` or `marts/core`

## Data Quality Checks
- [ ] order_id uniqueness
- [ ] customer_id not null
- [ ] order_date within valid range
- [ ] total_amount >= 0
- [ ] status in accepted values
