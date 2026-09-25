-- Q2a: cart abandonment by category and price band (quartile of latest price
-- within category), Oct-Nov. Unit = product carted in a session; abandoned if
-- that session never purchases it. Nov 14-17 excluded (tracking anomaly: carts
-- recorded without purchases), which would otherwise inflate abandonment.
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
)

select
    category_l1,
    price_band,
    count(*) as carted_items,
    sum(1 - purchased) as abandoned_items,
    sum(1 - purchased) / count(*) as abandonment_rate
from carted
group by category_l1, price_band
order by category_l1, price_band
