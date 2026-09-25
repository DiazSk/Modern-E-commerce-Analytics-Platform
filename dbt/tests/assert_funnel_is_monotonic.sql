-- purchased <= carted <= sessions in every funnel row, and purchased <= carted
-- items in every abandonment row.
select 'funnel' as mart, cast(session_date as string) as grain
from {{ ref('mart_funnel_daily') }}
where purchased_sessions > carted_sessions or carted_sessions > sessions
union all
select 'abandonment', concat(category_l1, '|', price_band, '|', week_start)
from {{ ref('mart_cart_abandonment') }}
where purchased_items > carted_items
