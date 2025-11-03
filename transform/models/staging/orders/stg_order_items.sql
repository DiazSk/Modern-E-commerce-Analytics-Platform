{{
    config(
        materialized='view',
        tags=['staging', 'order_items', 'daily']
    )
}}

-- ==============================================================================
-- Staging Model: Order Items
-- ==============================================================================
-- Purpose: Clean and standardize order line item data from PostgreSQL source
-- 
-- Transformations:
--   - Standardize column names to snake_case
--   - Cast data types appropriately
--   - Calculate derived metrics (discount_percentage)
--   - Add data quality flags
--   - No aggregations (saved for intermediate layer)
-- 
-- Grain: One row per order line item (order_id + product_id combination)
-- ==============================================================================

with source as (
    
    select * from {{ source('postgres_ecommerce', 'order_items') }}

),

renamed as (

    select
        -- Primary Key
        order_item_id,
        
        -- Foreign Keys
        order_id,
        product_id,
        
        -- Line Item Details
        quantity::integer as quantity,
        unit_price::decimal(10,2) as unit_price,
        discount_amount::decimal(10,2) as discount_amount,
        line_total::decimal(10,2) as line_total,
        
        -- Metadata
        created_at::timestamp as created_at

    from source

),

calculated as (

    select
        *,
        
        -- Calculated Metrics
        (quantity * unit_price) as gross_line_total,
        
        case 
            when (quantity * unit_price) > 0 
            then (discount_amount / (quantity * unit_price)) * 100
            else 0
        end as discount_percentage,
        
        -- Data Quality Checks
        case
            when line_total != (quantity * unit_price - discount_amount) then true
            else false
        end as has_line_total_mismatch,
        
        case
            when quantity <= 0 then true
            else false
        end as is_invalid_quantity,
        
        case
            when unit_price <= 0 then true
            else false
        end as is_invalid_price,
        
        case
            when discount_amount < 0 then true
            else false
        end as is_negative_discount,
        
        case
            when discount_amount > (quantity * unit_price) then true
            else false
        end as is_excessive_discount

    from renamed

),

final as (

    select
        *,
        
        -- Discount Tier Classification
        case
            when discount_percentage = 0 then 'no_discount'
            when discount_percentage < 10 then 'low_discount'
            when discount_percentage < 25 then 'medium_discount'
            when discount_percentage < 50 then 'high_discount'
            else 'extreme_discount'
        end as discount_tier
        
    from calculated

)

select * from final