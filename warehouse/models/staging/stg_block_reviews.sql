select
    id as block_review_id,
    plan_id,
    block_number,
    overall_rpe,
    (notes is not null and length(trim(notes)) > 0) as has_notes,
    created_at
from {{ source('raw', 'block_reviews') }}
