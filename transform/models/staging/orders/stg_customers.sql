{{
    config(
        materialized='view',
        tags=['staging', 'customers', 'daily']
    )
}}

-- ==============================================================================
-- Staging Model: Customers
-- ==============================================================================
-- Purpose: Clean and standardize customer data from PostgreSQL source
--
-- Transformations:
--   - Standardize column names to snake_case
--   - Cast data types appropriately
--   - Create full_name for convenience
--   - Add data quality flags
--   - Include SCD Type 2 tracking fields
--   - No business logic (saved for intermediate layer)
--
-- Grain: One row per customer (with SCD Type 2 history)
-- ==============================================================================

with source as (

    select * from {{ source('postgres_ecommerce', 'customers') }}

),

renamed as (

    select
        -- Primary Key
        customer_id,

        -- Customer Identity
        email,
        first_name,
        last_name,
        concat(first_name, ' ', last_name) as full_name,
        phone,

        -- Customer Segmentation
        customer_segment,

        -- SCD Type 2 Tracking Fields
        segment_start_date::date as segment_start_date,
        segment_end_date::date as segment_end_date,
        is_current::boolean as is_current,

        -- Dates
        registration_date::date as registration_date,

        -- Metadata
        created_at::timestamp as created_at,
        updated_at::timestamp as updated_at,

        -- Data Quality Flags
        case
            when email is null or email = '' then true
            else false
        end as is_missing_email,

        case
            when phone is null or phone = '' then true
            else false
        end as is_missing_phone

    from source

)

select * from renamed
