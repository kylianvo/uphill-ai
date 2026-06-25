from typing import List, Dict, Any, Optional
import json
from db import engine
from sqlalchemy import text

class AnalyticsService:
    @staticmethod
    def track_events(events: List[Dict[str, Any]], user_id: Optional[int] = None, session_id: Optional[str] = None):
        """
        Batch insert analytics events into PostgreSQL.
        """
        if not events:
            return

        with engine.begin() as conn:
            for event in events:
                event_name = event.get("event_name")
                properties = event.get("properties", {})
                url = event.get("url")
                
                if not event_name:
                    continue

                conn.execute(
                    text("""
                        INSERT INTO analytics_events (user_id, event_name, properties, session_id, url)
                        VALUES (:user_id, :event_name, :properties, :session_id, :url)
                    """),
                    {
                        "user_id": user_id,
                        "event_name": event_name,
                        "properties": json.dumps(properties),
                        "session_id": session_id,
                        "url": url
                    }
                )
