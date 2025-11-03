{{
    config(
        materialized='view',
        tags=['staging', 'products', 'daily']
    )
}}

-- ==============================================================================
-- Staging Model: Products
-- ==============================================================================
-- Purpose: Clean and standardize product catalog data from API source
-- 
-- Transformations:
--   - Standardize column names to snake_case
--   - Cast data types appropriately
--   - Handle rating fields from nested JSON
--   - Add data quality flags
-- 
-- Grain: One row per product
-- ==============================================================================

with source as (
    
    select * from {{ source('postgres_ecommerce', 'products') }}

),

renamed as (

    select
        -- Primary Key
        product_id,
        
        -- Product Details
        title as product_name,
        category,
        price::decimal(10,2) as price,
        description,
        image as image_url,
        
        -- Rating Information
        rating_rate::decimal(3,2) as rating,
        rating_count::integer as rating_count,
        
        -- Metadata
        ingestion_timestamp::timestamp as ingestion_timestamp,
        ingestion_date::date as ingestion_date,
        data_source,
        created_at::timestamp as created_at,
        
        -- Data Quality Flags
        case 
            when price <= 0 then true
            else false
        end as is_invalid_price,
        
        case
            when rating_rate < 0 or rating_rate > 5 then true
            else false
        end as is_invalid_rating,
        
        case
            when category is null or category = '' then true
            else false
        end as is_missing_category

    from source

)

select * from renamed

-- ==============================================================================
-- Model Documentation
-- ==============================================================================
-- 
-- **Update Frequency**: Daily (via Airflow API ingestion)
-- **Expected Row Count**: ~20 products (FakeStore API)
-- **Materialization**: View (lightweight, always fresh)
-- 
-- **Data Quality Notes**:
-- - product_id is unique and not null (tested in sources.yml)
-- - price should be positive (flagged with is_invalid_price)
-- - rating should be 0-5 (flagged with is_invalid_rating)
-- 
-- **Usage**:
-- This model is used as the base for:
-- - dim_products (dimension table in marts)
-- - Product performance analysis
-- - Price analytics
-- 
-- ==============================================================================
