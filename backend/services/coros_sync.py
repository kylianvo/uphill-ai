"""Orchestrates a COROS sync: refresh the token, pull, normalise, persist.

Poll-driven by design. COROS gates webhook push notifications behind their
scale-onboarding programme, so there is nothing to subscribe to yet; the
webhook stub in routers/integrations.py is the landing point for when there is.
"""

from datetime import UTC, date, datetime, timedelta

import db
from config import settings
from log_utils import get_logger
from services import coros_oauth, token_crypto
from services.mcp_client import McpClient
from services.providers.coros import PROVIDER, CorosAdapter

logger = get_logger(__name__)


async def persist(user_id: int, adapter, days: int) -> dict[str, int]:
    """Pull and store. Isolated from transport so it can be unit-tested."""
    until = date.today()
    since = until - timedelta(days=days)

    activities = await adapter.fetch_activities(since, until)
    stored_activities = 0
    for activity in activities:
        try:
            db.upsert_activity(user_id, activity)
            stored_activities += 1
        except Exception:
            logger.exception(
                "activity persist failed",
                extra={
                    "fields": {
                        "service": "coros_sync",
                        "event": "activity_failed",
                        "external_id": activity.external_id,
                    }
                },
            )

    metrics = await adapter.fetch_daily_metrics(days=min(days, 30))
    stored_metrics = 0
    for metric in metrics:
        try:
            db.upsert_daily_metric(user_id, metric)
            stored_metrics += 1
        except Exception:
            logger.exception(
                "daily metric persist failed",
                extra={
                    "fields": {
                        "service": "coros_sync",
                        "event": "metric_failed",
                        "metric_date": str(metric.metric_date),
                    }
                },
            )

    db.mark_connection_synced(user_id, PROVIDER)
    return {"activities": stored_activities, "daily_metrics": stored_metrics}


async def _access_token(connection: dict) -> str:
    """Returns a usable access token, refreshing it first if it is near expiry."""
    expires_at = connection.get("token_expires_at")
    if expires_at and expires_at <= datetime.now(UTC) + timedelta(minutes=5):
        refreshed = await coros_oauth.refresh(token_crypto.decrypt_token(connection["refresh_token_enc"]))
        db.save_connection(
            user_id=connection["user_id"],
            provider=PROVIDER,
            access_token_enc=token_crypto.encrypt_token(refreshed.access_token),
            # A fresh refresh token isn't always issued -- save_connection COALESCEs
            # None to the stored ciphertext rather than clearing it, so passing None
            # when COROS didn't rotate it is correct, not an omission.
            refresh_token_enc=token_crypto.encrypt_token(refreshed.refresh_token) if refreshed.refresh_token else None,
            token_expires_at=refreshed.expires_at,
            scopes=connection.get("scopes", ""),
            provider_user_id=connection.get("provider_user_id"),
        )
        return refreshed.access_token
    return token_crypto.decrypt_token(connection["access_token_enc"])


async def sync_user(user_id: int, days: int = 30) -> dict[str, int]:
    connection = db.get_connection(user_id, PROVIDER)
    if not connection or connection.get("status") != "active":
        raise ValueError("No active COROS connection for this athlete.")

    token = await _access_token(connection)
    client = McpClient(settings.COROS_MCP_ENDPOINT, token)
    try:
        await client.initialize()
        return await persist(user_id, CorosAdapter(client), days)
    finally:
        await client.aclose()
