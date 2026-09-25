-- Nulls must become 'unknown', never the string 'None' (dbt-spark seeds write
-- 'None' for empty values; this guards against that class of bug).
select event_key
from {{ ref('stg_events') }}
where 'None' in (category_code, category_l1, category_l2, brand)
