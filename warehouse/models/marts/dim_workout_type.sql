select
    type_key,
    display_name,
    zone
from {{ ref('stg_workout_types') }}
