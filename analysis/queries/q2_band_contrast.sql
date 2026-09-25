-- Q2b: within each category, abandonment in the priciest quartile (band 4)
-- minus the cheapest (band 1), with a 95% CI. Comparing inside a category
-- keeps category mix from posing as a price effect. >= 1000 items per band.
with bands as (
    select
        category_l1,
        sum(case when price_band = 4 then carted_items else 0 end) as n4,
        sum(case when price_band = 4 then abandoned_items else 0 end) as a4,
        sum(case when price_band = 1 then carted_items else 0 end) as n1,
        sum(case when price_band = 1 then abandoned_items else 0 end) as a1
    from workspace.rees46_dbt.mart_cart_abandonment
    group by category_l1
),

rates as (
    select category_l1, n4, n1, a4 / n4 as p4, a1 / n1 as p1
    from bands
    where n4 >= 1000 and n1 >= 1000
)

select
    category_l1,
    p4 as top_band_rate,
    p1 as bottom_band_rate,
    p4 - p1 as diff,
    p4 - p1 - 1.96 * sqrt(p4 * (1 - p4) / n4 + p1 * (1 - p1) / n1) as ci_low,
    p4 - p1 + 1.96 * sqrt(p4 * (1 - p4) / n4 + p1 * (1 - p1) / n1) as ci_high,
    n4 as top_band_items,
    n1 as bottom_band_items
from rates
order by diff desc
