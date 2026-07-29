select
    e.event_id,
    cast(e.event_timestamp as date) as date_key,
    du.user_key,
    e.event_name,
    e.session_id,
    e.event_timestamp
from {{ ref('stg_analytics_events') }} e
left join {{ ref('dim_user') }} du
    on du.user_id = e.user_id
    and e.event_timestamp >= du.valid_from
    and e.event_timestamp < du.valid_to
