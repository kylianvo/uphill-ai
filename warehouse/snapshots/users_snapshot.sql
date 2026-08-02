{% snapshot users_snapshot %}

{{
    config(
        target_schema='snapshots',
        unique_key='user_id',
        strategy='check',
        check_cols=['role', 'is_coach', 'goal_type', 'days_per_week', 'current_weekly_km', 'onboarding_complete'],
    )
}}

-- NOTE: adding a new column to this SELECT that is NOT in check_cols (like
-- `created_at`/`provider`) only populates it for rows inserted from here on.
-- A check-strategy snapshot never re-evaluates/backfills existing unchanged
-- rows just because a new non-check column appeared -- `dbt snapshot` (there
-- is no `--full-refresh` for snapshots) will leave it NULL forever on rows
-- that predate the column addition. Fix is a one-time manual
-- `DROP TABLE snapshots.users_snapshot` (and the `marts.dim_user` built on
-- top of it) followed by a fresh `dbt snapshot` + `dbt run`, accepting the
-- loss of prior SCD2 version history -- fine for this dev/demo warehouse,
-- not something to do against real production history.

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
