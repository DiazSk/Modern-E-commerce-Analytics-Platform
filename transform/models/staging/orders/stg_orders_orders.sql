{{
    config(
        materialized='view',
        tags=['staging', 'orders', 'daily']
    )
}}

-- ==============================================================================
-- Staging Model: Orders
-- ==============================================================================
-- Purpose: Clean and standardize order header data from PostgreSQL source
--
-- Transformations:
--   - Standardize column names to snake_case
--   - Cast data types appropriately
--   - Parse order_date into components
--   - Add data quality flags
--   - No aggregations (saved for intermediate layer)
--
-- Grain: One row per order
-- ==============================================================================

with source as (

    select * from {{ source('postgres_ecommerce', 'orders') }}

),

renamed as (

    select
        -- Primary Key
        order_id,

        -- Foreign Keys
        customer_id,

        -- Order Details
        order_date::timestamp as order_date,
        order_total::decimal(10,2) as order_total,
        payment_method,
        shipping_address,
        order_status,

        -- Date Components (for partitioning and filtering)
        order_date::date as order_date_only,
        extract(year from order_date)::integer as order_year,
        extract(month from order_date)::integer as order_month,
        extract(day from order_date)::integer as order_day,
        extract(dow from order_date)::integer as order_day_of_week,
        to_char(order_date, 'Day') as order_day_name,
        to_char(order_date, 'Month') as order_month_name,

        -- Order Classification
        case
            when order_total < 50 then 'small'
            when order_total < 200 then 'medium'
            when order_total < 500 then 'large'
            else 'enterprise'
        end as order_size_category,

        -- Metadata
        created_at::timestamp as created_at,
        updated_at::timestamp as updated_at,

        -- Data Quality Flags
        case
            when order_total < 0 then true
            else false
        end as is_negative_total,

        case
            when shipping_address is null or shipping_address = '' then true
            else false
        end as is_missing_shipping_address,

        case
            when order_status = 'cancelled' then true
            else false
        end as is_cancelled

    from source

),

final as (

    select
        *,
        -- Add business day flag (Monday = 1, Sunday = 0)
        case
            when order_day_of_week in (0, 6) then false  -- Saturday, Sunday
            else true
        end as is_business_day

    from renamed

)

select * from final

-- ==============================================================================
-- Model Documentation
-- ==============================================================================
--
-- **Update Frequency**: Daily (via Airflow)
-- **Expected Row Count**: ~5,000
-- **Materialization**: View (lightweight, always fresh)
--
-- **Data Quality Notes**:
-- - order_id is unique and not null (tested in sources.yml)
-- - customer_id is valid foreign key (tested in sources.yml)
-- - order_status values validated (tested in sources.yml)
-- - payment_method values validated (tested in sources.yml)
--
-- **Date Components**:
-- These are pre-calculated for easier filtering and grouping:
-- - order_year, order_month, order_day
-- - order_day_of_week (0=Sunday, 6=Saturday)
-- - order_day_name, order_month_name
--
-- **Order Size Categories**:
-- - small: < $50
-- - medium: $50 - $199
-- - large: $200 - $499
-- - enterprise: >= $500
--
-- **Usage**:
-- This model is used as the base for:
-- - fact_orders (fact table in marts)
-- - Order analytics and reporting
-- - Revenue analysis by date/customer/status
--
-- ==============================================================================
