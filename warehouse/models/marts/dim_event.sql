select distinct
    event_name
from {{ ref('stg_analytics_events') }}
