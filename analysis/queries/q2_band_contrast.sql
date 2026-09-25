-- Q2b: within each category, abandonment in the priciest quartile (band 4)
-- minus the cheapest (band 1), with a 95% CI. Comparing inside a category keeps
-- category mix from posing as a price effect. >= 1000 items per band.
-- Nov 14-17 excluded (tracking anomaly).
with sp as (
    -- One row per product carted in a session, dated by its first cart event.
    select
        user_session,
        product_id,
        min(case when event_type = 'cart' then event_date end) as cart_date,
        max(case when event_type = 'purchase' then 1 else 0 end) as purchased
    from workspace.rees46_dbt.stg_events
    where user_session is not null
    group by user_session, product_id
),

carted as (
    select p.category_l1, p.price_band, sp.cart_date, sp.purchased
    from sp
    join workspace.rees46_dbt.dim_products p on sp.product_id = p.product_id
    where sp.cart_date is not null
      and sp.cart_date not between '2019-11-14' and '2019-11-17'
),

bands as (
    select
        category_l1,
        sum(case when price_band = 4 then 1 else 0 end) as n4,
        sum(case when price_band = 4 then 1 - purchased else 0 end) as a4,
        sum(case when price_band = 1 then 1 else 0 end) as n1,
        sum(case when price_band = 1 then 1 - purchased else 0 end) as a1
    from carted
    group by category_l1
),

rates as (
    select category_l1, n4, n1, a4 / n4 as p4, a1 / n1 as p1
    from bands
    where n4 >= 1000 and n1 >= 1000
)

select
    category_l1,
    p4 as top_band_rate,
    p1 as bottom_band_rate,
    p4 - p1 as diff,
    p4 - p1 - 1.96 * sqrt(p4 * (1 - p4) / n4 + p1 * (1 - p1) / n1) as ci_low,
    p4 - p1 + 1.96 * sqrt(p4 * (1 - p4) / n4 + p1 * (1 - p1) / n1) as ci_high,
    n4 as top_band_items,
    n1 as bottom_band_items
from rates
order by diff desc
