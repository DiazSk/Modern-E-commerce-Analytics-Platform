select
    event_key,
    event_time,
    event_date,
    user_session,
    user_id,
    product_id,
    category_l1,
    category_l2,
    brand,
    price
from {{ ref('stg_events') }}
where event_type = 'purchase'
