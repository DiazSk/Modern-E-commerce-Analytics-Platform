select 'funnel' as mart, cast(session_date as string) as d, category_l1, count(*) as n
from {{ ref('mart_funnel_daily') }}
group by session_date, category_l1
having count(*) > 1
union all
select 'abandonment', concat(price_band, '|', week_start), category_l1, count(*)
from {{ ref('mart_cart_abandonment') }}
group by category_l1, price_band, week_start
having count(*) > 1
