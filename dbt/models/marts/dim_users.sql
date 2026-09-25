select
    user_id,
    min(event_time) as first_seen_at,
    min(case when event_type = 'purchase' then event_time end) as first_purchase_at,
    cast(date_trunc('WEEK', min(event_date)) as date) as acquisition_week
from {{ ref('stg_events') }}
group by user_id
