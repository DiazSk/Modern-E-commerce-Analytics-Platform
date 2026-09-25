-- Q0c: evidence for the Nov 14-17 tracking anomaly. Daily event mix, Nov 8-22:
-- Nov 15 records hundreds of thousands of carts and zero purchases, and Nov 17
-- records ~8x the normal purchase count.
select
    event_date,
    count(*) as events,
    sum(case when event_type = 'view' then 1 else 0 end) as views,
    sum(case when event_type = 'cart' then 1 else 0 end) as carts,
    sum(case when event_type = 'purchase' then 1 else 0 end) as purchases
from workspace.rees46.raw_events
where event_date between '2019-11-08' and '2019-11-22'
group by event_date
order by event_date
