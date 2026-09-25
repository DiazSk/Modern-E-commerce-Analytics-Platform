-- Q1a: session-level funnel, Black Friday week vs the four weeks before it.
-- Sessions are dated by their start. 95% Wald CI on the difference.
-- Baseline excludes Nov 14-17: a tracking anomaly in the source (Nov 15 has
-- 468k cart events and zero purchases; Nov 17 ~8x normal purchases). See
-- q0_anomaly_daily.sql and q3_anomaly_impact.sql.
with periods as (
    select
        case
            when session_date between '2019-11-25' and '2019-11-30' then 'black_friday_week'
            when session_date between '2019-10-28' and '2019-11-24'
                 and session_date not between '2019-11-14' and '2019-11-17' then 'baseline_4_weeks'
        end as period,
        cast(reached_cart as int) as carted,
        cast(reached_purchase as int) as purchased
    from workspace.rees46_dbt.fct_sessions
),

rates as (
    select
        count(case when period = 'black_friday_week' then 1 end) as n1,
        avg(case when period = 'black_friday_week' then carted end) as cart1,
        avg(case when period = 'black_friday_week' then purchased end) as buy1,
        count(case when period = 'baseline_4_weeks' then 1 end) as n0,
        avg(case when period = 'baseline_4_weeks' then carted end) as cart0,
        avg(case when period = 'baseline_4_weeks' then purchased end) as buy0
    from periods
    where period is not null
)

select 'cart_rate' as metric, cart1 as black_friday, cart0 as baseline, cart1 - cart0 as diff,
       cart1 - cart0 - 1.96 * sqrt(cart1 * (1 - cart1) / n1 + cart0 * (1 - cart0) / n0) as ci_low,
       cart1 - cart0 + 1.96 * sqrt(cart1 * (1 - cart1) / n1 + cart0 * (1 - cart0) / n0) as ci_high,
       n1 as black_friday_sessions, n0 as baseline_sessions
from rates
union all
select 'purchase_rate', buy1, buy0, buy1 - buy0,
       buy1 - buy0 - 1.96 * sqrt(buy1 * (1 - buy1) / n1 + buy0 * (1 - buy0) / n0),
       buy1 - buy0 + 1.96 * sqrt(buy1 * (1 - buy1) / n1 + buy0 * (1 - buy0) / n0),
       n1, n0
from rates
