with session_product as (
    select
        user_session,
        product_id,
        min(case when event_type = 'cart' then event_date end) as cart_date,
        max(case when event_type = 'cart' then 1 else 0 end) as carted,
        max(case when event_type = 'purchase' then 1 else 0 end) as purchased
    from {{ ref('stg_events') }}
    where user_session is not null
    group by user_session, product_id
),

carted as (
    select
        p.category_l1,
        p.price_band,
        cast(date_trunc('WEEK', sp.cart_date) as date) as week_start,
        sp.purchased
    from session_product sp
    join {{ ref('dim_products') }} p
        on sp.product_id = p.product_id
    where sp.carted = 1
)

select
    category_l1,
    price_band,
    week_start,
    count(*) as carted_items,
    sum(purchased) as purchased_items,
    sum(1 - purchased) as abandoned_items,
    sum(1 - purchased) / count(*) as abandonment_rate,
    week_start = cast(date_trunc('WEEK', to_date('{{ var("black_friday_week_start") }}')) as date) as is_black_friday_week
from carted
group by category_l1, price_band, week_start
