select
    type_key,
    display_name,
    zone,
    lang
from {{ source('raw', 'workout_types') }}
where lang = 'en'
