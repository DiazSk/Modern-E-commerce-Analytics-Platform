-- fact_orders inner-joins every dimension, so a line item whose product,
-- customer version or date has no match is silently dropped. Fail if any
-- staged line item is missing from the fact table.
select
    (select count(*) from {{ ref('stg_order_items') }}) as staged_line_items,
    (select count(*) from {{ ref('fact_orders') }}) as fact_line_items
where
    (select count(*) from {{ ref('stg_order_items') }})
    != (select count(*) from {{ ref('fact_orders') }})
