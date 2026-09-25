-- Q2a: cart abandonment by category and price band (quartile of latest price
-- within category), Oct-Nov combined. Unit = product carted in a session.
select
    category_l1,
    price_band,
    sum(carted_items) as carted_items,
    sum(abandoned_items) as abandoned_items,
    sum(abandoned_items) / sum(carted_items) as abandonment_rate
from workspace.rees46_dbt.mart_cart_abandonment
group by category_l1, price_band
order by category_l1, price_band
