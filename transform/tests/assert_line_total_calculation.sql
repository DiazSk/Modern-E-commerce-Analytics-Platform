-- ==============================================================================
-- Custom Test: Assert Line Total Calculation Correctness
-- ==============================================================================
-- Purpose: Validate that line_total is correctly calculated as:
--          line_total = (quantity * unit_price) - discount_amount
-- 
-- Business Rule: 
--   Line total must equal gross amount (qty × price) minus any discounts
--   This is critical for revenue accuracy and financial reporting
--
-- How it works:
--   Calculates expected line_total and compares with actual
--   Allows 0.01 tolerance for floating point precision
--   Returns rows where calculation is INCORRECT
--
-- Usage:
--   dbt test --select assert_line_total_calculation
--
-- Expected Result: 0 rows (all calculations correct)
-- ==============================================================================

with calculation_check as (
    select
        order_id,
        order_item_id,
        order_item_key,
        quantity,
        unit_price,
        discount_amount,
        line_total as actual_line_total,
        
        -- Calculate expected line total
        (quantity * unit_price) - coalesce(discount_amount, 0) as expected_line_total,
        
        -- Calculate difference (absolute value)
        abs(
            line_total - ((quantity * unit_price) - coalesce(discount_amount, 0))
        ) as calculation_difference
        
    from {{ ref('fact_orders') }}
)

select
    order_id,
    order_item_id,
    order_item_key,
    quantity,
    unit_price,
    discount_amount,
    actual_line_total,
    expected_line_total,
    calculation_difference
from calculation_check
where calculation_difference > 0.01  -- Allow 1 cent tolerance for floating point

-- If this query returns rows, those line items have incorrect calculations
-- Business impact: Revenue misstatement, financial reporting errors