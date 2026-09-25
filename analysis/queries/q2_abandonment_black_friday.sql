-- Q2c: overall cart abandonment, Black Friday week vs the four weeks before.
with rates as (
    select
        sum(case when week_start = '2019-11-25' then carted_items else 0 end) as n1,
        sum(case when week_start = '2019-11-25' then abandoned_items else 0 end) / sum(case when week_start = '2019-11-25' then carted_items else 0 end) as p1,
        sum(case when week_start between '2019-10-28' and '2019-11-18' then carted_items else 0 end) as n0,
        sum(case when week_start between '2019-10-28' and '2019-11-18' then abandoned_items else 0 end) / sum(case when week_start between '2019-10-28' and '2019-11-18' then carted_items else 0 end) as p0
    from workspace.rees46_dbt.mart_cart_abandonment
)

select
    p1 as black_friday_rate,
    p0 as baseline_rate,
    p1 - p0 as diff,
    p1 - p0 - 1.96 * sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0) as ci_low,
    p1 - p0 + 1.96 * sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0) as ci_high,
    n1 as black_friday_items,
    n0 as baseline_items
from rates
