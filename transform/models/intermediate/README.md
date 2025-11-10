# Intermediate Models

## Purpose
Business logic layer between staging and marts. Contains complex transformations, deduplication, and business rule application that would clutter staging or marts models.

## When to Use Intermediate Models
1. **Complex joins** across multiple staging models
2. **Deduplication logic** that's reused across marts
3. **Business calculations** used by multiple downstream models
4. **Window functions** for ranking, lead/lag operations
5. **Aggregations** that feed multiple marts

## Naming Convention
`int_<domain>_<description>.sql`

Examples:
- `int_orders_with_customers.sql`
- `int_products_enriched.sql`
- `int_user_sessions.sql`

## Models (To Be Created)
- `int_orders_enriched.sql` - Orders joined with customer and product info
- `int_customer_lifetime_metrics.sql` - Customer-level aggregations
- `int_product_performance.sql` - Product sales metrics
- `int_user_sessions.sql` - Sessionized clickstream events

## Materialization Strategy
- **Type:** Views (default) or tables if performance requires
- **Optimization:** Only create intermediate models if logic is reused

## Best Practices
1. Keep staging models simple (just cleaning)
2. Push complex logic to intermediate layer
3. Keep marts focused on final structure
4. Document business logic clearly
5. Use CTEs for readability

## Example Structure
```sql
-- int_orders_enriched.sql
with orders as (
    select * from {{ ref('stg_orders') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

order_items as (
    select * from {{ ref('stg_order_items') }}
)

select
    o.order_id,
    o.order_date,
    c.customer_name,
    c.customer_segment,
    oi.product_id,
    p.product_name,
    p.category,
    oi.quantity,
    oi.unit_price,
    oi.quantity * oi.unit_price as line_total
from orders o
left join customers c on o.customer_id = c.customer_id
left join order_items oi on o.order_id = oi.order_id
left join products p on oi.product_id = p.product_id
```

## Dependencies
- **Upstream:** Staging models
- **Downstream:** Marts models

## Testing
Apply data quality tests same as staging/marts:
- Relationship tests between joined entities
- Not null checks on key columns
- Accepted values for categorical fields
