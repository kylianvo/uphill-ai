select
    id as workout_id,
    plan_id,
    week_number,
    type as workout_type_key,
    duration_minutes,
    distance_km,
    source,
    is_completed = 1 as is_completed,
    rpe,
    approved_at is not null as is_approved,
    approved_at
from {{ source('raw', 'workouts') }}
