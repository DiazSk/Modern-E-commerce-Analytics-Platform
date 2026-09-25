select
    user_session,
    min(user_id) as user_id,
    min(event_date) as session_date,
    min(event_time) as session_start,
    max(event_time) as session_end,
    count(*) as events,
    sum(case when event_type = 'view' then 1 else 0 end) as views,
    sum(case when event_type = 'cart' then 1 else 0 end) as carts,
    sum(case when event_type = 'purchase' then 1 else 0 end) as purchases,
    sum(case when event_type = 'purchase' then price else 0 end) as purchase_revenue,
    max(case when event_type in ('cart', 'purchase') then 1 else 0 end) = 1 as reached_cart,
    max(case when event_type = 'purchase' then 1 else 0 end) = 1 as reached_purchase
from {{ ref('stg_events') }}
where user_session is not null
group by user_session
