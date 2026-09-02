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

from typing import Any

from fastapi import APIRouter, Request

from log_utils import get_logger

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
