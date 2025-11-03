{{
    config(
        materialized='table',
        tags=['analytics', 'customers', 'metrics']
    )
}}

-- ==============================================================================
-- Analytics Model: Customer Lifetime Value
-- ==============================================================================
-- Purpose: Calculate comprehensive customer lifetime value metrics
-- 
-- Features:
--   - Total revenue per customer
--   - Order frequency and recency
--   - Average order value
--   - Customer lifetime (in days and months)
--   - Estimated monthly revenue
--   - Customer value segmentation
--
-- Grain: One row per customer (current segment only)
-- ==============================================================================

with fact_orders as (
    
    select * from {{ ref('fact_orders') }}

),

dim_customers as (
    
    select * from {{ ref('dim_customers') }}
    where is_current = true

),

customer_orders as (

    select
        c.customer_id,
        c.customer_key,
        c.email,
        c.full_name,
        c.customer_segment,
        c.registration_date,
        
        -- Order Metrics
        count(distinct f.order_id) as total_orders,
        count(distinct f.order_item_key) as total_items_purchased,
        sum(f.line_total) as total_revenue,
        sum(f.quantity) as total_quantity,
        sum(f.discount_amount) as total_discounts,
        
        -- Time-based Metrics
        min(f.order_date) as first_order_date,
        max(f.order_date) as last_order_date,
        current_date - max(f.order_date) as days_since_last_order,
        max(f.order_date) - min(f.order_date) as customer_lifetime_days,
        
        -- Average Metrics
        avg(f.line_total) as avg_line_value,
        avg(f.order_total) as avg_order_value,
        avg(f.quantity) as avg_quantity_per_item

    from dim_customers c
    inner join fact_orders f 
        on c.customer_key = f.customer_key
    
    group by 
        c.customer_id,
        c.customer_key,
        c.email,
        c.full_name,
        c.customer_segment,
        c.registration_date

),

customer_metrics as (

    select
        *,
        
        -- Lifetime Value Calculations
        case 
            when customer_lifetime_days > 0 
            then total_revenue / (customer_lifetime_days / 30.0)
            else total_revenue
        end as estimated_monthly_revenue,
        
        case 
            when customer_lifetime_days > 0 
            then round(customer_lifetime_days / 30.0, 2)
            else 0
        end as customer_lifetime_months,
        
        -- Frequency Metrics
        case 
            when customer_lifetime_days > 0 
            then round(total_orders::numeric / (customer_lifetime_days / 30.0), 2)
            else total_orders
        end as orders_per_month,
        
        -- Customer Segmentation
        case 
            when total_orders >= 10 and total_revenue >= 1000 then 'VIP'
            when total_orders >= 5 and total_revenue >= 500 then 'High Value'
            when total_orders >= 3 and total_revenue >= 200 then 'Medium Value'
            when total_orders >= 1 and total_revenue >= 50 then 'Low Value'
            else 'At Risk'
        end as value_segment,
        
        case
            when days_since_last_order <= 30 then 'Active'
            when days_since_last_order <= 90 then 'At Risk'
            when days_since_last_order <= 180 then 'Churning'
            else 'Churned'
        end as recency_segment,
        
        case
            when total_orders = 1 then 'One-Time'
            when total_orders between 2 and 4 then 'Occasional'
            when total_orders between 5 and 9 then 'Regular'
            else 'Loyal'
        end as frequency_segment

    from customer_orders

),

final as (

    select
        -- Customer Identity
        customer_id,
        customer_key,
        email,
        full_name,
        customer_segment,
        registration_date,
        
        -- Order Metrics
        total_orders,
        total_items_purchased,
        total_quantity,
        
        -- Revenue Metrics
        round(total_revenue::numeric, 2) as total_revenue,
        round(total_discounts::numeric, 2) as total_discounts,
        round(avg_order_value::numeric, 2) as avg_order_value,
        round(avg_line_value::numeric, 2) as avg_line_value,
        round(avg_quantity_per_item::numeric, 2) as avg_quantity_per_item,
        
        -- Lifetime Metrics
        first_order_date,
        last_order_date,
        days_since_last_order,
        customer_lifetime_days,
        customer_lifetime_months,
        round(estimated_monthly_revenue::numeric, 2) as estimated_monthly_revenue,
        orders_per_month,
        
        -- Segmentation
        value_segment,
        recency_segment,
        frequency_segment

    from customer_metrics

)

select * from final