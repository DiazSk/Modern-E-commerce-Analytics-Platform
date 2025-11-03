{{
    config(
        materialized='table',
        unique_key='product_key',
        tags=['dimension', 'core', 'products']
    )
}}

-- ==============================================================================
-- Dimension Model: Products
-- ==============================================================================
-- Purpose: Product dimension for e-commerce analytics
-- 
-- Features:
--   - Surrogate key for product dimension
--   - Product attributes from FakeStore API
--   - Category for analysis and grouping
--   - Pricing and rating information
--
-- Grain: One row per product (Type 1 SCD - overwrites on change)
-- ==============================================================================

with source_products as (
    
    select * from {{ ref('stg_products') }}

),

products_final as (

    select
        -- Surrogate Key
        {{ dbt_utils.generate_surrogate_key(['product_id']) }} as product_key,
        
        -- Natural Key
        product_id,
        
        -- Product Attributes
        product_name,
        category,
        price,
        description,
        image_url,
        
        -- Rating Information
        rating,
        rating_count,
        
        -- Derived Fields
        case
            when price < 20 then 'Budget'
            when price between 20 and 100 then 'Mid-Range'
            else 'Premium'
        end as price_tier,
        
        case
            when rating >= 4.5 then 'Excellent'
            when rating >= 4.0 then 'Very Good'
            when rating >= 3.5 then 'Good'
            when rating >= 3.0 then 'Fair'
            else 'Poor'
        end as rating_category,
        
        -- Metadata
        created_at,
        ingestion_timestamp,
        ingestion_date,
        data_source

    from source_products

)

select * from products_final