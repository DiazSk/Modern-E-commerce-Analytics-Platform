-- ==============================================================================
-- Custom Test: Assert No Orphaned Customer References
-- ==============================================================================
-- Purpose: Validate all customer_key values in fact_orders have corresponding
--          records in dim_customers
-- 
-- Business Rule: 
--   Every order must be linked to a valid customer. Orphaned records
--   indicate referential integrity violations.
--
-- Note: dbt's built-in relationships test handles this, but this custom
--       test provides more detailed information about orphaned records.
--
-- Usage:
--   dbt test --select assert_no_orphaned_customers
--
-- Expected Result: 0 rows (all customer_keys valid)
-- ==============================================================================

select
    f.order_id,
    f.order_item_key,
    f.customer_key,
    f.order_date,
    f.line_total,
    count(c.customer_key) as matching_customer_records
    
from {{ ref('fact_orders') }} f
left join {{ ref('dim_customers') }} c
    on f.customer_key = c.customer_key
    and c.is_current = true  -- Only check against current customer records
    
group by
    f.order_id,
    f.order_item_key,
    f.customer_key,
    f.order_date,
    f.line_total
    
having count(c.customer_key) = 0  -- No matching customer found

-- If this query returns rows, those are orphaned orders without valid customers
-- Business Impact:
-- 1. Cannot attribute revenue to customer
-- 2. Customer analytics will be incomplete
-- 3. SCD Type 2 dimension integrity issue