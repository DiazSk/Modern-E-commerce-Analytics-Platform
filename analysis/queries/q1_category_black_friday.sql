-- Q1b: purchase rate by top-level category, Black Friday week vs baseline.
-- Unit = session x category (a session can count in several categories).
-- Only categories with >= 1000 session-categories in both periods.
with by_period as (
    select
        category_l1,
        sum(case when session_date between '2019-11-25' and '2019-11-30' then sessions else 0 end) as n1,
        sum(case when session_date between '2019-11-25' and '2019-11-30' then purchased_sessions else 0 end) as k1,
        sum(case when session_date between '2019-10-28' and '2019-11-24' then sessions else 0 end) as n0,
        sum(case when session_date between '2019-10-28' and '2019-11-24' then purchased_sessions else 0 end) as k0
    from workspace.rees46_dbt.mart_funnel_daily
    group by category_l1
),

rates as (
    select category_l1, n1, n0, k1 / n1 as p1, k0 / n0 as p0
    from by_period
    where n1 >= 1000 and n0 >= 1000
)

select
    category_l1,
    p1 as black_friday_rate,
    p0 as baseline_rate,
    p1 - p0 as diff,
    p1 - p0 - 1.96 * sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0) as ci_low,
    p1 - p0 + 1.96 * sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0) as ci_high,
    n1 as black_friday_n,
    n0 as baseline_n
from rates
order by diff desc
