"""Live quality signals for the Gear Finder and Nutrition Lab results.

- `catalog_valid`: every recommended product exists in the distilled catalog
  (the same check the golden set runs offline, now on live traffic).
- `brand_respected`: when preferred brands were requested, every pick is from them.
- A signed `feedback_token` returned with each fresh result lets the (possibly
  signed-out) athlete send thumbs for exactly that result's trace -- no table needed.
"""

import hashlib
import hmac
import re
from typing import Any

from config import settings
from services import observability
from services.kb_context import find_uncatalogued

FEATURES = ("gear_finder", "nutrition_lab")
_TOKEN_RE = re.compile(r"^([0-9a-f]{32})\.([a-z_]+)\.([0-9a-f]{32})$")


def _sign(trace_id: str, feature: str) -> str:
    key = settings.OBSERVABILITY_ID_SALT.encode()
    return hmac.new(key, f"feedback:{feature}:{trace_id}".encode(), hashlib.sha256).hexdigest()[:32]


def feedback_token(trace_id: str | None, feature: str) -> str | None:
    if not trace_id or feature not in FEATURES or not settings.OBSERVABILITY_ID_SALT:
        return None
    return f"{trace_id}.{feature}.{_sign(trace_id, feature)}"


def verify_feedback_token(token: str) -> tuple[str, str] | None:
    """(trace_id, feature) for a token this server issued, else None."""
    m = _TOKEN_RE.fullmatch(token or "")
    if not m or not settings.OBSERVABILITY_ID_SALT:
        return None
    trace_id, feature, sig = m.groups()
    if feature not in FEATURES or not hmac.compare_digest(sig, _sign(trace_id, feature)):
        return None
    return trace_id, feature


def _brands(preferred: str | None) -> list[str]:
    return [b.strip().lower() for b in (preferred or "").split(",") if b.strip()]


def brand_respected(recs: list[dict[str, Any]], preferred: str | None) -> bool | None:
    wanted = _brands(preferred)
    if not wanted or not recs:
        return None
    picked = [(r.get("brand") or "").strip().lower() for r in recs]
    return all(any(w in p or p in w for w in wanted) for p in picked if p)


def score_recommendations(
    trace_id: str | None, recs: list[dict[str, Any]], catalog_titles: list[str], preferred_brands: str | None
) -> None:
    if not trace_id or not recs:
        return
    observability.score(
        trace_id=trace_id, name="catalog_valid", value=0 if find_uncatalogued(recs, catalog_titles) else 1
    )
    respected = brand_respected(recs, preferred_brands)
    if respected is not None:
        observability.score(trace_id=trace_id, name="brand_respected", value=1 if respected else 0)
