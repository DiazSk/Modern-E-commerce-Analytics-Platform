with session_category as (
    select
        s.session_date,
        e.category_l1,
        e.user_session,
        max(case when e.event_type in ('cart', 'purchase') then 1 else 0 end) as reached_cart,
        max(case when e.event_type = 'purchase' then 1 else 0 end) as purchased
    from {{ ref('stg_events') }} e
    join {{ ref('fct_sessions') }} s
        on e.user_session = s.user_session
    group by s.session_date, e.category_l1, e.user_session
)

select
    sc.session_date as event_date,
    sc.category_l1,
    count(*) as sessions,
    sum(sc.reached_cart) as carted_sessions,
    sum(sc.purchased) as purchased_sessions,
    sum(sc.reached_cart) / count(*) as cart_rate,
    sum(sc.purchased) / count(*) as purchase_rate,
    d.is_black_friday_week
from session_category sc
join {{ ref('dim_date') }} d
    on sc.session_date = d.date_day
group by sc.session_date, sc.category_l1, d.is_black_friday_week
