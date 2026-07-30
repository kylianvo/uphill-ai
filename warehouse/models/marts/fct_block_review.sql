with reviews as (
    select * from {{ ref('stg_block_reviews') }}
),
plans as (
    select plan_id, user_id from {{ ref('stg_plans') }}
)
select
    r.block_review_id,
    cast(r.created_at as date) as date_key,
    du.user_key,
    r.plan_id as plan_key,
    r.block_number,
    r.overall_rpe,
    r.has_notes,
    r.created_at
from reviews r
join plans p on p.plan_id = r.plan_id
left join {{ ref('dim_user') }} du
    on du.user_id = p.user_id
    and r.created_at >= du.valid_from
    and r.created_at < du.valid_to
