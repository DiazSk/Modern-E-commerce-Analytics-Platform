with ranked as (
    select
        *,
        row_number() over (partition by product_id order by event_time desc, event_key) as recency
    from {{ ref('stg_events') }}
)

select
    product_id,
    category_id,
    category_code,
    category_l1,
    category_l2,
    brand,
    price,
    ntile(4) over (partition by category_l1 order by price, product_id) as price_band
from ranked
where recency = 1
