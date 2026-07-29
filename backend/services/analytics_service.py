import json
from typing import Any

from sqlalchemy import text

from db import engine


class AnalyticsService:
    @staticmethod
    def track_events(events: list[dict[str, Any]], user_id: int | None = None, session_id: str | None = None):
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
                        "url": url,
                    },
                )

    @staticmethod
    def save_events_from_kafka(event: dict[str, Any]) -> None:
        """
        Write a single consumed Kafka clickstream message to Postgres, reusing
        the same insert path as the direct-write fallback.
        """
        AnalyticsService.track_events(
            [
                {
                    "event_name": event.get("event_name"),
                    "properties": event.get("properties", {}),
                    "url": event.get("url"),
                }
            ],
            user_id=event.get("user_id"),
            session_id=event.get("session_id"),
        )
