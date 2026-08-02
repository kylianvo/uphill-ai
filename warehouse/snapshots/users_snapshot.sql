{% snapshot users_snapshot %}

{{
    config(
        target_schema='snapshots',
        unique_key='user_id',
        strategy='check',
        check_cols=['role', 'is_coach', 'goal_type', 'days_per_week', 'current_weekly_km', 'onboarding_complete'],
    )
}}

select
    id as user_id,
    email,
    role,
    provider,
    is_coach,
    goal_type,
    days_per_week,
    current_weekly_km,
    onboarding_complete,
    created_at
from {{ source('raw', 'users') }}

{% endsnapshot %}
