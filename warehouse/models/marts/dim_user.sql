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
    dbt_valid_from as valid_from,
    coalesce(dbt_valid_to, timestamp '2999-12-31') as valid_to,
    dbt_valid_to is null as is_current
from {{ ref('users_snapshot') }}
