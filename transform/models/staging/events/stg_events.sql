{{
    config(
        materialized='view',
        tags=['staging', 'events', 'hourly']
    )
}}

-- ==============================================================================
-- Staging Model: Clickstream Events
-- ==============================================================================
-- Purpose: Clean and standardize clickstream event data from web application
--
-- Transformations:
--   - Standardize column names to snake_case
--   - Cast data types appropriately
--   - Extract date/time components for partitioning
--   - Add data quality flags
--
-- Grain: One row per event
-- ==============================================================================

with source as (

    select * from {{ source('postgres_ecommerce', 'clickstream_events') }}

),

renamed as (

    select
        -- Primary Key
        event_id,

        -- Session Information
        session_id,
        user_id,

        -- Event Details
        event_timestamp::timestamp as event_timestamp,
        event_type,
        product_id,
        page_url,
        device_type,
        browser,

        -- Date Components (for partitioning and analysis)
        event_timestamp::date as event_date,
        extract(year from event_timestamp)::integer as event_year,
        extract(month from event_timestamp)::integer as event_month,
        extract(day from event_timestamp)::integer as event_day,
        extract(hour from event_timestamp)::integer as event_hour,
        extract(dow from event_timestamp)::integer as event_day_of_week,
        to_char(event_timestamp, 'Day') as event_day_name,

        -- Metadata
        created_at::timestamp as created_at,

        -- Data Quality Flags
        case
            when event_type is null or event_type = '' then true
            else false
        end as is_missing_event_type,

        case
            when user_id is null then true
            else false
        end as is_anonymous_user,

        case
            when product_id is null and event_type in ('add_to_cart', 'remove_from_cart', 'purchase') then true
            else false
        end as is_missing_product_context

    from source

),

categorized as (

    select
        *,

        -- Event Category Classification
        case
            when event_type = 'page_view' then 'browsing'
            when event_type in ('add_to_cart', 'remove_from_cart') then 'cart_activity'
            when event_type = 'purchase' then 'conversion'
            when event_type = 'search' then 'search'
            else 'other'
        end as event_category,

        -- Device Category
        case
            when lower(device_type) like '%mobile%' or lower(device_type) like '%phone%' then 'mobile'
            when lower(device_type) like '%tablet%' then 'tablet'
            when lower(device_type) like '%desktop%' then 'desktop'
            else 'other'
        end as device_category,

        -- Business Day Flag
        case
            when extract(dow from event_timestamp) in (0, 6) then false
            else true
        end as is_business_day,

        -- Business Hours Flag (9 AM - 5 PM)
        case
            when extract(hour from event_timestamp) between 9 and 17 then true
            else false
        end as is_business_hours

    from renamed

)

select * from categorized

-- ==============================================================================
-- Model Documentation
-- ==============================================================================
--
-- **Update Frequency**: Hourly (via Airflow batch processing)
-- **Expected Row Count**: ~50,000 events (synthetic data)
-- **Materialization**: View (lightweight, always fresh)
--
-- **Data Quality Notes**:
-- - event_id is unique and not null (tested in sources.yml)
-- - event_timestamp is required for all events
-- - product_id should be present for cart/purchase events
--
-- **Event Categories**:
-- - browsing: page_view events
-- - cart_activity: add_to_cart, remove_from_cart
-- - conversion: purchase events
-- - search: search events
--
-- **Usage**:
-- This model is used as the base for:
-- - User behavior analysis
-- - Conversion funnel analysis
-- - Product engagement metrics
-- - Session analytics
--
-- ==============================================================================
