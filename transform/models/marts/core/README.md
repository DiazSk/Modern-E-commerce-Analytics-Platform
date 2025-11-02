# Marts - Core (Fact Tables)

## Purpose
Analytics-ready fact tables containing business metrics and measures.

## Models
- `fact_orders.sql` - Order-level transactional data (grain: order line item)

## Materialization Strategy
- **Type:** Incremental table
- **Unique Key:** order_item_key (surrogate key)
- **Update Strategy:** Append-only for new orders, update for order modifications
- **Partitioning:** By order_date (daily partitions)
- **Clustering:** customer_key, product_key

## Grain
**One row per order line item** (order_id + product_id combination)

## Measures
- Quantity sold
- Gross revenue
- Discount amount
- Net revenue
- Tax amount
- Shipping cost
- Cost of goods sold (COGS)
- Profit margin

## Foreign Keys
- `customer_key` → dim_customers
- `product_key` → dim_products
- `order_date_key` → dim_date
- `ship_date_key` → dim_date

## Dependencies
- `stg_orders` (staging)
- `stg_order_items` (staging)
- `dim_customers` (dimension)
- `dim_products` (dimension)
- `dim_date` (dimension)

## Performance Optimization
- Daily incremental loads (only new/updated orders)
- Clustered on high-cardinality foreign keys
- Pre-aggregated metrics for common queries
- Indexes on date and customer keys

## Data Quality Checks
- [ ] order_item_key uniqueness
- [ ] All foreign keys exist in dimension tables
- [ ] Net revenue = gross revenue - discount
- [ ] Profit margin = (net revenue - COGS) / net revenue
- [ ] quantity > 0
- [ ] All monetary amounts >= 0
