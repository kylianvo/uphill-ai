with spine as (
    select unnest(generate_series(date '2020-01-01', current_date + interval '366 days', interval '1 day')) as date_day
)
select
    date_day as date_key,
    date_day,
    extract(year from date_day) as year,
    extract(quarter from date_day) as quarter,
    extract(month from date_day) as month,
    extract(week from date_day) as iso_week,
    extract(dayofweek from date_day) as day_of_week,
    strftime(date_day, '%A') as day_name,
    extract(dayofweek from date_day) in (0, 6) as is_weekend
from spine
