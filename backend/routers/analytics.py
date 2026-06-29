from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import text

from db import engine
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


class AnalyticsEvent(BaseModel):
    event_name: str
    properties: dict[str, Any] | None = {}
    url: str | None = None


class AnalyticsBatch(BaseModel):
    events: list[AnalyticsEvent]
    session_id: str | None = None


# Custom dependency to extract user_id from token manually without throwing 401 if unauthenticated
def get_optional_user(request: Request) -> int | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT user_id, expires_at FROM sessions WHERE session_token = :t"), {"t": token}
        ).fetchone()
        if not result:
            return None

        import datetime

        user_id, expires_at = result
        # Check if tz-aware
        if expires_at.tzinfo is None:
            now = datetime.datetime.utcnow()
        else:
            now = datetime.datetime.now(datetime.UTC)

        if expires_at < now:
            return None

        return user_id


@router.post("/track_batch")
async def track_batch(batch: AnalyticsBatch, user_id: int | None = Depends(get_optional_user)):
    """
    Receive a batch of analytics events from the frontend and store them.
    """
    events_list = [{"event_name": e.event_name, "properties": e.properties, "url": e.url} for e in batch.events]
    AnalyticsService.track_events(events_list, user_id, batch.session_id)
    return {"status": "success", "recorded": len(events_list)}
