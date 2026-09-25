with days as (
    select explode(sequence(
        to_date('{{ var("data_start") }}'),
        to_date('{{ var("data_end") }}'),
        interval 1 day
    )) as date_day
)

select
    date_day,
    year(date_day) as year,
    month(date_day) as month,
    dayofweek(date_day) as day_of_week,
    cast(date_trunc('WEEK', date_day) as date) as week_start,
    dayofweek(date_day) in (1, 7) as is_weekend,
    date_day between to_date('{{ var("black_friday_week_start") }}')
        and to_date('{{ var("black_friday_week_end") }}') as is_black_friday_week
from days
