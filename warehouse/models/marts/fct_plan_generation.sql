with plans as (
    select * from {{ ref('stg_plans') }}
),
users as (
    select * from {{ ref('stg_users') }}
),
first_plan as (
    select
        user_id,
        min(created_at) as first_plan_created_at
    from plans
    group by user_id
)
select
    p.plan_id,
    cast(p.created_at as date) as date_key,
    p.user_id,
    p.plan_status = 'active' as is_generation_success,
    case
        when fp.first_plan_created_at = p.created_at
            then date_diff('day', u.created_at, p.created_at)
    end as days_to_first_plan,
    p.created_at
from plans p
left join users u on u.user_id = p.user_id
left join first_plan fp on fp.user_id = p.user_id
