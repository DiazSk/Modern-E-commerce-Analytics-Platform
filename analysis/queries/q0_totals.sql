-- Q0b: headline scale figures for the dashboard and README.
select
    count(*) as events,
    count(distinct user_session) as sessions,
    sum(case when event_type = 'purchase' then 1 else 0 end) as purchases,
    count(distinct user_id) as users,
    min(event_date) as first_day,
    max(event_date) as last_day
from workspace.rees46.raw_events
