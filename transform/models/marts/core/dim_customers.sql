{{
    config(
        materialized='table',
        unique_key='customer_key',
        tags=['dimension', 'core', 'customers', 'scd_type_2']
    )
}}

-- ==============================================================================
-- Dimension Model: Customers (SCD Type 2)
-- ==============================================================================
-- Purpose: Slowly Changing Dimension Type 2 for customer tracking
-- 
-- Features:
--   - Tracks customer segment changes over time
--   - Maintains historical records with effective dates
--   - Surrogate key based on customer_id + segment_start_date
--   - is_current flag for latest record
--
-- SCD Type 2 Implementation:
--   - New row created when customer_segment changes
--   - segment_start_date: When this version became effective
--   - segment_end_date: When this version expired (NULL/9999-12-31 for current)
--   - is_current: TRUE for active record, FALSE for historical
--
-- Grain: One row per customer per segment change
-- ==============================================================================

with source_customers as (
    
    select * from {{ ref('stg_customers') }}

),

customers_with_history as (

    select
        -- Surrogate Key (unique per customer segment change)
        {{ dbt_utils.generate_surrogate_key(['customer_id', 'segment_start_date']) }} as customer_key,
        
        -- Natural Key
        customer_id,
        
        -- Customer Identity
        email,
        first_name,
        last_name,
        full_name,
        phone,
        
        -- Customer Segmentation (SCD Type 2 attribute)
        customer_segment,
        
        -- SCD Type 2 Tracking
        segment_start_date as effective_date,
        coalesce(segment_end_date, '9999-12-31'::date) as expiration_date,
        is_current,
        
        -- Registration Info
        registration_date,
        
        -- Metadata
        created_at,
        updated_at,
        
        -- Data Quality Flags
        is_missing_email,
        is_missing_phone

    from source_customers

),

final as (

    select
        customer_key,
        customer_id,
        email,
        first_name,
        last_name,
        full_name,
        phone,
        customer_segment,
        effective_date,
        expiration_date,
        is_current,
        registration_date,
        created_at,
        updated_at,
        is_missing_email,
        is_missing_phone

    from customers_with_history

)

select * from final