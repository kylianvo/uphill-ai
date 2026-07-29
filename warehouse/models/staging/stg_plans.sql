select
    id as plan_id,
    user_id,
    race_name,
    goal_type,
    total_weeks,
    course_distance_km,
    created_by_user_id,
    plan_status,
    approved_at is not null as is_approved,
    created_at
from {{ source('raw', 'plans') }}
