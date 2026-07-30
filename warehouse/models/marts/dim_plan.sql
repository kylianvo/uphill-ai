select
    plan_id,
    user_id,
    race_name,
    goal_type,
    total_weeks,
    course_distance_km,
    plan_status,
    is_approved,
    (created_by_user_id is not null and created_by_user_id != user_id) as is_coach_assigned
from {{ ref('stg_plans') }}
