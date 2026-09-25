-- Q2c: overall cart abandonment, Black Friday week vs the four weeks before
-- (Nov 14-17 excluded from the baseline: tracking anomaly). 95% Wald CI.
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

rates as (
    select
        sum(case when cart_date between '2019-11-25' and '2019-11-30' then 1 else 0 end) as n1,
        sum(case when cart_date between '2019-11-25' and '2019-11-30' then 1 - purchased else 0 end)
            / sum(case when cart_date between '2019-11-25' and '2019-11-30' then 1 else 0 end) as p1,
        sum(case when cart_date between '2019-10-28' and '2019-11-24' then 1 else 0 end) as n0,
        sum(case when cart_date between '2019-10-28' and '2019-11-24' then 1 - purchased else 0 end)
            / sum(case when cart_date between '2019-10-28' and '2019-11-24' then 1 else 0 end) as p0
    from carted
)

select
    p1 as black_friday_rate,
    p0 as baseline_rate,
    p1 - p0 as diff,
    p1 - p0 - 1.96 * sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0) as ci_low,
    p1 - p0 + 1.96 * sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0) as ci_high,
    n1 as black_friday_items,
    n0 as baseline_items
from rates
