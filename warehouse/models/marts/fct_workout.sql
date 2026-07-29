with workouts as (
    select * from {{ ref('stg_workouts') }}
),
plans as (
    select plan_id, user_id from {{ ref('stg_plans') }}
),
workout_events as (
    select
        w.workout_id,
        w.plan_id,
        p.user_id,
        w.workout_type_key,
        w.duration_minutes,
        w.distance_km,
        w.is_completed,
        w.rpe,
        coalesce(w.approved_at, current_timestamp) as event_timestamp
    from workouts w
    join plans p on p.plan_id = w.plan_id
)
select
    we.workout_id,
    cast(we.event_timestamp as date) as date_key,
    du.user_key,
    we.plan_id as plan_key,
    we.workout_type_key,
    we.duration_minutes,
    we.distance_km,
    true as is_planned,
    we.is_completed,
    we.rpe
from workout_events we
left join {{ ref('dim_user') }} du
    on du.user_id = we.user_id
    and we.event_timestamp >= du.valid_from
    and we.event_timestamp < du.valid_to
