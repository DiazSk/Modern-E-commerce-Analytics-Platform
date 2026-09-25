-- Q0: data profile for the memo's caveats. How long do REES46 "sessions" last?
select
    count(*) as sessions,
    avg(case when datediff(session_end, session_start) >= 1 then 1.0 else 0.0 end) as share_spanning_days,
    avg(case when datediff(session_end, session_start) >= 7 then 1.0 else 0.0 end) as share_spanning_week,
    max(datediff(session_end, session_start)) as max_span_days,
    percentile_approx(unix_timestamp(session_end) - unix_timestamp(session_start), 0.5) as median_seconds
from workspace.rees46_dbt.fct_sessions
