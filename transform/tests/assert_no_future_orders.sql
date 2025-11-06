-- ==============================================================================
-- Custom Test: Assert No Future Orders
-- ==============================================================================
-- Purpose: Validate that no orders have dates in the future
-- 
-- Business Rule: 
--   Orders cannot exist in the future - all order_date values must be
--   <= current_date. Future dates indicate data quality issues.
--
-- How it works:
--   Compares order_date with current_date
--   Returns rows where order_date is in the future
--
-- Usage:
--   dbt test --select assert_no_future_orders
--
-- Expected Result: 0 rows (no future orders)
-- ==============================================================================

select
    order_id,
    order_item_key,
    order_date,
    order_timestamp,
    current_date as today,
    order_date - current_date as days_in_future
from {{ ref('fact_orders') }}
where order_date > current_date

-- If this query returns rows, those orders have future dates
-- This indicates:
-- 1. Data entry errors
-- 2. System clock issues
-- 3. Data quality problems in source system