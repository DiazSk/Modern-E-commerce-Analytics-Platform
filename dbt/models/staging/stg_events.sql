select
    event_key,
    event_time,
    event_date,
    event_type,
    product_id,
    category_id,
    coalesce(category_code, 'unknown') as category_code,
    coalesce(try_element_at(split(category_code, '[.]'), 1), 'unknown') as category_l1,
    coalesce(try_element_at(split(category_code, '[.]'), 2), 'unknown') as category_l2,
    coalesce(brand, 'unknown') as brand,
    price,
    user_id,
    user_session
from {{ source('rees46', 'raw_events') }}
