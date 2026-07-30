with versioned as (
    select
        *,
        row_number() over (partition by user_id order by dbt_valid_from) as version_number
    from {{ ref('users_snapshot') }}
)
select
    dbt_scd_id as user_key,
    user_id,
    email,
    role,
    provider,
    is_coach,
    goal_type,
    days_per_week,
    current_weekly_km,
    onboarding_complete,
    case when version_number = 1 then timestamp '1900-01-01' else dbt_valid_from end as valid_from,
    coalesce(dbt_valid_to, timestamp '2999-12-31') as valid_to,
    dbt_valid_to is null as is_current
from versioned
