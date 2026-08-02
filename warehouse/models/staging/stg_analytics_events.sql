select
    id as event_id,
    user_id,
    event_name,
    session_id,
    url,
    timestamp as event_timestamp
from {{ source('raw', 'analytics_events') }}
