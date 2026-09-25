-- Data-quality guard: a day with substantial cart activity but zero purchases
-- almost certainly means purchase tracking failed, not that nobody bought.
-- REES46 has one such day (2019-11-15). Severity warn: surface it on every
-- build without blocking; analyses exclude Nov 14-17 explicitly.
{{ config(severity='warn') }}

select
    event_date,
    sum(case when event_type = 'cart' then 1 else 0 end) as carts,
    sum(case when event_type = 'purchase' then 1 else 0 end) as purchases
from {{ ref('stg_events') }}
group by event_date
having sum(case when event_type = 'cart' then 1 else 0 end) >= 1000
   and sum(case when event_type = 'purchase' then 1 else 0 end) = 0
