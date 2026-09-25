-- Q3: how much the Nov 14-17 tracking anomaly changes the Black Friday
-- comparison. Each metric is computed twice: with those four days in the
-- baseline (naive) and without them (corrected, used everywhere else).
with sp as (
    select
        user_session,
        product_id,
        min(case when event_type = 'cart' then event_date end) as cart_date,
        max(case when event_type = 'purchase' then 1 else 0 end) as purchased
    from workspace.rees46_dbt.stg_events
    where user_session is not null
    group by user_session, product_id
),
-- Same carted-item unit as q2 (join included), so the corrected row matches it.
carted as (
    select sp.* from sp join workspace.rees46_dbt.dim_products p on sp.product_id = p.product_id
),

units as (
    select 'cart_abandonment' as metric, cart_date as d, 1 - purchased as hit from carted where cart_date is not null
    union all
    select 'cart_rate', session_date, cast(reached_cart as int) from workspace.rees46_dbt.fct_sessions
    union all
    select 'purchase_rate', session_date, cast(reached_purchase as int) from workspace.rees46_dbt.fct_sessions
),

periods as (
    select
        metric,
        sum(case when d between '2019-11-25' and '2019-11-30' then 1 else 0 end) as n1,
        sum(case when d between '2019-11-25' and '2019-11-30' then hit else 0 end) as k1,
        sum(case when d between '2019-10-28' and '2019-11-24' then 1 else 0 end) as n_naive,
        sum(case when d between '2019-10-28' and '2019-11-24' then hit else 0 end) as k_naive,
        sum(case when d between '2019-10-28' and '2019-11-24' and d not between '2019-11-14' and '2019-11-17' then 1 else 0 end) as n_clean,
        sum(case when d between '2019-10-28' and '2019-11-24' and d not between '2019-11-14' and '2019-11-17' then hit else 0 end) as k_clean
    from units
    group by metric
),

versions as (
    select metric, 'naive_includes_nov14_17' as baseline, k1 / n1 as p1, k_naive / n_naive as p0, n1, n_naive as n0 from periods
    union all
    select metric, 'corrected_excludes_nov14_17', k1 / n1, k_clean / n_clean, n1, n_clean from periods
)

select
    metric,
    baseline,
    p1 as black_friday,
    p0 as baseline_rate,
    p1 - p0 as diff,
    p1 - p0 - 1.96 * sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0) as ci_low,
    p1 - p0 + 1.96 * sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0) as ci_high,
    n1 as black_friday_n,
    n0 as baseline_n
from versions
order by metric, baseline
