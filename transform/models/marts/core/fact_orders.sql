{{
    config(
        materialized='incremental',
        unique_key='order_item_key',
        tags=['fact', 'core', 'orders', 'incremental'],
        on_schema_change='fail',
        cluster_by=['customer_key', 'product_key'],
        partition_by={
            'field': 'order_date',
            'data_type': 'date',
            'granularity': 'day'
        }
    )
}}

-- ==============================================================================
-- Fact Model: Orders
-- ==============================================================================
-- Purpose: Transaction-level fact table for order analytics
--
-- Features:
--   - Incremental loading based on order_timestamp
--   - Foreign keys to all dimension tables
--   - Measures: quantity, unit_price, discount, line_total, order_total
--   - Grain: One row per order line item
--
-- Optimization:
--   - partition_by order_date: prunes full-table scans for date-range queries
--   - cluster_by customer_key, product_key: co-locates data for common joins
-- ==============================================================================

with orders as (

    select * from {{ ref('stg_orders') }}
    {% if is_incremental() %}
        where order_date > (
            select coalesce(max(order_timestamp), '1900-01-01'::timestamp)
            from {{ this }}
        )
    {% endif %}

),

order_items as (

    select * from {{ ref('stg_order_items') }}

),

customers as (

    select * from {{ ref('dim_customers') }}
    where is_current = true

),

products as (

    select * from {{ ref('dim_products') }}

),

dates as (

    select distinct date_key, date_day
    from {{ ref('dim_date') }}

),

joined as (

    select
        -- Unique Key for Fact Table
        {{ dbt_utils.generate_surrogate_key(['o.order_id', 'oi.product_id']) }} as order_item_key,

        -- Foreign Keys to Dimensions
        c.customer_key,
        p.product_key,
        d.date_key,

        -- Degenerate Dimensions (stored in fact)
        o.order_id,
        oi.order_item_id,

        -- Date/Time Attributes
        cast(o.order_date as date) as order_date,
        o.order_date as order_timestamp,
        extract(hour from o.order_date) as order_hour,
        extract(dow from o.order_date) as order_day_of_week,

        -- Order Attributes
        o.order_status,
        o.payment_method,

        -- Measures (Additive)
        oi.quantity,
        oi.unit_price,
        oi.discount_amount,
        oi.gross_line_total as gross_amount,
        (oi.gross_line_total - coalesce(oi.discount_amount, 0)) as line_total,
        o.order_total,

        -- Derived Measures
        case
            when oi.discount_amount > 0 then true
            else false
        end as has_discount,

        case
            when oi.discount_amount > 0
            then (oi.discount_amount / nullif(oi.quantity * oi.unit_price, 0)) * 100
            else 0
        end as discount_percentage,

        oi.gross_line_total - coalesce(oi.discount_amount, 0) as net_revenue

    from orders o
    inner join order_items oi
        on o.order_id = oi.order_id
    inner join customers c
        on o.customer_id = c.customer_id
    inner join products p
        on oi.product_id = p.product_id
    inner join dates d
        on cast(o.order_date as date) = d.date_day

)

select * from joined
