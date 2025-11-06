-- ==============================================================================
-- Custom Relationship Test: fact_orders -> dim_customers (current records only)
-- ==============================================================================
-- Purpose: Validates that all customer_keys in fact_orders reference current
--          customers in dim_customers (is_current = true)
--
-- This custom test is needed because dbt's built-in relationships test cannot
-- filter the parent table (dim_customers), only the child table (fact_orders).
--
-- Business Rule: Orders should only reference currently active customer records
-- ==============================================================================

{{ config(
    severity = 'error',
    tags = ['relationships', 'referential_integrity', 'fact_orders', 'dim_customers']
) }}

with fact_orders as (
    
    select distinct customer_key
    from {{ ref('fact_orders') }}
    where customer_key is not null

),

current_customers as (
    
    select distinct customer_key
    from {{ ref('dim_customers') }}
    where is_current = true

),

-- Find customer_keys in fact_orders that don't exist in current customers
orphaned_keys as (

    select 
        f.customer_key,
        count(*) as occurrence_count
    from fact_orders f
    left join current_customers c 
        on f.customer_key = c.customer_key
    where c.customer_key is null
    group by f.customer_key

)

-- Return rows if any orphaned keys exist (test fails if > 0 rows)
select 
    customer_key,
    occurrence_count,
    'customer_key exists in fact_orders but not in current dim_customers records' as failure_reason
from orphaned_keys

