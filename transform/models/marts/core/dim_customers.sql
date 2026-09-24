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
-- Source: customers_snapshot (dbt snapshot, check strategy on customer_segment)
--
-- SCD Type 2 Implementation:
--   - A new version is created by `dbt snapshot` when customer_segment changes
--   - effective_date: When this version became valid (inclusive)
--   - expiration_date: When this version stopped being valid (exclusive,
--     9999-12-31 for the current version)
--   - is_current: TRUE for the active version
--   - The first version of each customer is backdated to 1900-01-01 so orders
--     placed before the first snapshot still resolve to a version
--
-- Fact tables join on customer_id AND order time within
-- [effective_date, expiration_date) to get the version valid at that time.
--
-- Grain: One row per customer per segment version
-- ==============================================================================

with snapshot as (

    select
        *,
        row_number() over (
            partition by customer_id
            order by dbt_valid_from
        ) as version_number

    from {{ ref('customers_snapshot') }}

),

final as (

    select
        -- Surrogate Key (unique per customer version)
        {{ dbt_utils.generate_surrogate_key(['customer_id', 'dbt_valid_from']) }} as customer_key,

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
        case
            when version_number = 1 then '1900-01-01'::timestamp
            else dbt_valid_from
        end as effective_date,
        coalesce(dbt_valid_to, '9999-12-31'::timestamp) as expiration_date,
        dbt_valid_to is null as is_current,
        version_number,

        -- Registration Info
        registration_date,

        -- Metadata
        created_at,
        updated_at,

        -- Data Quality Flags
        is_missing_email,
        is_missing_phone

    from snapshot

)

select * from final
