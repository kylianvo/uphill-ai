"""Device-integration endpoints (COROS today; Garmin when their developer
program reopens to new applicants).

Currently a STUB. It exists so that every URL declared on the COROS API
application form resolves before the application is reviewed -- see
docs/integrations/coros-api-application.md, form questions 13 and 14.

Two facts from the COROS API Reference V2.0.6 shape this file:

  * The workout-data receiving endpoint is documented as an "Https service
    interface that accepts workout data and allows duplicate data" -- COROS
    may deliver the same summary more than once, so the real handler must be
    idempotent. The stub is trivially idempotent because it persists nothing.
  * The service-status-check API is validated with a GET, and passes purely on
    "http status code is 200". `/api/health` already satisfies that and is what
    the form declares; the GET here is a convenience for probing this path.

TODO before go-live (needs COROS API Reference section 5.3, plus the clientId /
clientSecret issued on approval):
  - Confirm the acknowledgement body COROS expects; this stub returns 200 with a
    minimal JSON body on the assumption that the status code is what is checked.
  - Verify the push request's authenticity before trusting it.
  - Persist the payload to the durable `sync_events` queue rather than dropping
    it, and let the drain worker normalise and match it.
  - Link the pushed `planWorkoutId` back to the originating workouts row -- COROS
    echoes it for sessions started from a synced training plan, which removes the
    matching guesswork for those activities entirely.
"""

import secrets
import time
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import RedirectResponse

import db
from config import settings
from db import verify_session
from log_utils import get_logger
from services import coros_oauth, coros_sync, token_crypto
from services.providers.coros import PROVIDER

router = APIRouter(prefix="/integrations", tags=["integrations"])
logger = get_logger(__name__)


@router.get("/coros/webhook")
async def coros_webhook_probe() -> dict[str, str]:
    """Liveness probe for the push endpoint.

    COROS validates a partner interface with a GET expecting HTTP 200. The form
    declares `/api/health` for that check; this exists so the push path itself
    also answers a probe rather than 404ing.
    """
    return {"status": "ok"}


@router.post("/coros/webhook")
async def coros_webhook(request: Request) -> dict[str, str]:
    """Accept a COROS workout-summary push.

    Stub: acknowledges and discards. Always returns 200 -- including on a
    malformed body -- because a non-2xx would make COROS retry a payload we have
    no way to process yet, and a partner interface that errors under load is
    what their status check is designed to catch.

    Logs only the shape of the payload, never its content: these bodies carry
    real athlete training and health data (see log_utils).
    """
    raw = await request.body()
    keys: list[str] = []
    try:
        parsed: Any = await request.json()
        if isinstance(parsed, dict):
            keys = sorted(parsed.keys())
    except Exception:
        # Body may be form-encoded or malformed; the shape log is best-effort.
        pass

    logger.info(
        "coros webhook received",
        extra={
            "fields": {
                "service": "integrations",
                "provider": "coros",
                "event": "webhook_received",
                "status": "stubbed",
                "bytes": len(raw),
                "top_level_keys": keys,
            }
        },
    )
    return {"message": "ok"}


async def get_current_user(authorization: str | None = Header(None)) -> dict[str, Any]:
    """Local copy of main.py's dependency.

    Deliberately NOT imported from main: main.py imports this router, so
    importing back would be circular. routers/analytics.py solves the same
    problem the same way. Both call db.verify_session, so behaviour cannot drift.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication token missing or invalid.")
    user = verify_session(authorization.split(" ")[1])
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid.")
    return user


# state -> (user_id, pkce_verifier, created_at). In-process and short-lived: an
# unfinished authorization simply has to be restarted after a deploy, which is
# acceptable. created_at (time.monotonic()) backs _prune_pending_auth below --
# without it, a user who starts /coros/connect and never completes the redirect
# (closed tab, denied consent, anything) would leave an entry here forever, since
# nothing else ever removes one. Deployment today is a single uvicorn process
# with no --workers and no --reload (see backend/Dockerfile's CMD), so this dict
# is not split across processes in production; it would need to move to a shared
# store (e.g. the DB) before this could run behind multiple workers or replicas.
_PENDING_AUTH: dict[str, tuple[int, str, float]] = {}
_PENDING_AUTH_TTL_SECONDS = 600  # 10 minutes -- generous for a redirect round trip


def _prune_pending_auth() -> None:
    """Drops expired pending-authorization entries so the dict cannot grow
    without bound across abandoned connect attempts. Called opportunistically
    on every new connect rather than on a timer -- there is no background
    scheduler in this process."""
    cutoff = time.monotonic() - _PENDING_AUTH_TTL_SECONDS
    expired = [s for s, (_, _, created_at) in _PENDING_AUTH.items() if created_at < cutoff]
    for s in expired:
        _PENDING_AUTH.pop(s, None)


def _pop_pending_auth(state: str | None) -> tuple[int, str] | None:
    """Consumes a pending authorization exactly once. Returns None for a
    missing, unknown, replayed, or expired state -- an attacker-supplied code
    paired with a state that doesn't resolve to a live pending flow must not
    create a connection, and all of those cases have to look identical to the
    caller."""
    if not state:
        return None
    entry = _PENDING_AUTH.pop(state, None)
    if entry is None:
        return None
    user_id, verifier, created_at = entry
    if created_at < time.monotonic() - _PENDING_AUTH_TTL_SECONDS:
        return None
    return user_id, verifier


@router.get("/coros/connect")
async def coros_connect(user: dict[str, Any] = Depends(get_current_user)):
    if not settings.COROS_CLIENT_ID:
        raise HTTPException(status_code=503, detail="COROS integration is not configured.")
    _prune_pending_auth()
    verifier, challenge = coros_oauth.make_pkce_pair()
    state = secrets.token_urlsafe(32)
    _PENDING_AUTH[state] = (user["id"], verifier, time.monotonic())
    return {"authorize_url": coros_oauth.build_authorize_url(state, challenge)}


@router.get("/coros/callback")
async def coros_callback(code: str | None = None, state: str | None = None):
    pending = _pop_pending_auth(state)
    if not code or not pending:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/?coros=error")

    user_id, verifier = pending
    try:
        tokens = await coros_oauth.exchange_code(code, verifier)
    except coros_oauth.CorosAuthError:
        # Never let a rejected/expired code surface as a raw 500 to the athlete's
        # browser -- this endpoint is hit by a full-page redirect from COROS, not
        # an API call the frontend can catch, so an unhandled exception here would
        # otherwise strand them on a bare JSON error page outside the app shell.
        logger.warning(
            "coros token exchange failed",
            extra={
                "fields": {
                    "service": "integrations",
                    "provider": "coros",
                    "event": "exchange_failed",
                    "user_id": user_id,
                }
            },
        )
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/?coros=error")

    db.save_connection(
        user_id=user_id,
        provider=PROVIDER,
        access_token_enc=token_crypto.encrypt_token(tokens.access_token),
        refresh_token_enc=token_crypto.encrypt_token(tokens.refresh_token) if tokens.refresh_token else None,
        token_expires_at=tokens.expires_at,
        scopes=coros_oauth.SCOPES,
    )
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/?coros=connected")


@router.post("/coros/sync")
async def coros_sync_now(days: int = 30, user: dict[str, Any] = Depends(get_current_user)):
    try:
        return await coros_sync.sync_user(user["id"], days=days)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/coros")
async def coros_disconnect(user: dict[str, Any] = Depends(get_current_user)):
    # Agreement 9.5: delete within 24 hours of revocation. We do it immediately.
    db.delete_provider_data(user["id"], PROVIDER)
    return {"status": "disconnected"}


@router.get("/status")
async def integration_status(user: dict[str, Any] = Depends(get_current_user)):
    connection = db.get_connection(user["id"], PROVIDER)
    return {
        "coros": {
            "connected": bool(connection and connection.get("status") == "active"),
            "last_sync_at": connection.get("last_sync_at") if connection else None,
        }
    }
