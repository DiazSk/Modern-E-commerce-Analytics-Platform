{{
    config(
        materialized='table',
        unique_key='date_key',
        tags=['dimension', 'core', 'date']
    )
}}

-- ==============================================================================
-- Dimension Model: Date
-- ==============================================================================
-- Purpose: Create a comprehensive date dimension for time-series analysis
--
-- Features:
--   - Date spine covering 4 years (2023-2026)
--   - Standard calendar attributes (year, quarter, month, day, week)
--   - Formatted text fields for display (month_name, day_name)
--   - Business flags (is_weekend, is_holiday)
--   - Integer surrogate key (YYYYMMDD format)
--
-- Grain: One row per calendar day
-- ==============================================================================

with date_spine as (

    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2023-01-01' as date)",
        end_date="cast('2026-12-31' as date)"
    ) }}

),

date_details as (

    select
        -- Surrogate Key (YYYYMMDD format as integer)
        to_char(date_day, 'YYYYMMDD')::integer as date_key,

        -- Natural Key
        date_day,

        -- Year Attributes
        extract(year from date_day)::integer as year,
        extract(quarter from date_day)::integer as quarter,

        -- Month Attributes
        extract(month from date_day)::integer as month,
        to_char(date_day, 'Month') as month_name,
        to_char(date_day, 'Mon') as month_name_short,

        -- Day Attributes
        extract(day from date_day)::integer as day,
        to_char(date_day, 'Day') as day_name,
        to_char(date_day, 'Dy') as day_name_short,
        extract(dow from date_day)::integer as day_of_week, -- 0=Sunday, 6=Saturday
        extract(doy from date_day)::integer as day_of_year,

        -- Week Attributes
        extract(week from date_day)::integer as week_of_year,
        date_trunc('week', date_day)::date as week_start_date,
        (date_trunc('week', date_day) + interval '6 days')::date as week_end_date,

        -- Business Flags
        case
            when extract(dow from date_day) in (0, 6) then true
            else false
        end as is_weekend,

        case
            when extract(dow from date_day) between 1 and 5 then true
            else false
        end as is_weekday,

        -- Quarter Dates
        date_trunc('quarter', date_day)::date as quarter_start_date,
        (date_trunc('quarter', date_day) + interval '3 months - 1 day')::date as quarter_end_date,

        -- Month Dates
        date_trunc('month', date_day)::date as month_start_date,
        (date_trunc('month', date_day) + interval '1 month - 1 day')::date as month_end_date,

        -- Year Dates
        date_trunc('year', date_day)::date as year_start_date,
        (date_trunc('year', date_day) + interval '1 year - 1 day')::date as year_end_date

    from date_spine

)

select * from date_details
