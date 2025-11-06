-- ==============================================================================
-- Custom Test: Assert Valid Discount Logic
-- ==============================================================================
-- Purpose: Validate that discounts do not exceed gross order amount
-- 
-- Business Rule: 
--   Discount amount cannot be greater than the gross line amount
--   (quantity × unit_price). This would result in negative revenue.
--
-- How it works:
--   Compares discount_amount with gross_amount
--   Returns rows where discount > gross_amount
--
-- Usage:
--   dbt test --select assert_valid_discount_logic
--
-- Expected Result: 0 rows (all discounts valid)
-- ==============================================================================

select
    order_id,
    order_item_id,
    order_item_key,
    quantity,
    unit_price,
    gross_amount,
    discount_amount,
    line_total,
    
    -- Show how much discount exceeds gross
    discount_amount - gross_amount as excess_discount,
    
    -- Discount percentage
    round((discount_amount / nullif(gross_amount, 0)) * 100, 2) as discount_percentage
    
from {{ ref('fact_orders') }}
where discount_amount > gross_amount

-- If this query returns rows, those orders have invalid discounts
-- Business Impact:
-- 1. Negative revenue (financial reporting error)
-- 2. Possible fraud or system manipulation
-- 3. Data integrity violation