-- ==============================================================================
-- Custom Test: Assert Positive Order Total
-- ==============================================================================
-- Purpose: Validate that all order totals are positive (no negative revenue)
-- 
-- Business Rule: 
--   Revenue cannot be negative. Refunds and returns are handled separately
--   in a different process, so line_total must always be >= 0
--
-- How it works:
--   This test returns rows where the condition FAILS (SQL anti-pattern)
--   If query returns 0 rows → Test PASSES ✓
--   If query returns rows → Test FAILS ✗
--
-- Usage:
--   dbt test --select assert_positive_order_total
--
-- Expected Result: 0 rows (all line_totals are positive)
-- ==============================================================================

select
    order_id,
    order_item_id,
    order_item_key,
    line_total,
    quantity,
    unit_price,
    discount_amount
from {{ ref('fact_orders') }}
where line_total < 0

-- If this query returns any rows, those are orders with negative totals
-- which violates our business rule