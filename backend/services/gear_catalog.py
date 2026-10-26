"""Choose which gear catalog entries go into the Gear Finder prompt.

The whole catalog used to be sent on every request (~35k tokens). A road request
never needs trail-only shoes and vice versa; entries we can't classify are always
kept, and any filter that leaves too little falls back to the full catalog.
"""

import json
from typing import Any, Literal

MIN_ENTRIES = 12
MIN_BRAND_ENTRIES = 5

_TRAIL_WORDS = ("trail", "singletrack", "mountain", "technical", "mud", "gravel", "rock", "fell", "sky")
_ROAD_WORDS = ("road", "treadmill", "pavement")


def _payload(chunk: dict[str, Any]) -> dict[str, Any]:
    payload = chunk.get("payload") or {}
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except ValueError:
            return {}
    return payload if isinstance(payload, dict) else {}


def surface_of(payload: dict[str, Any]) -> Literal["road", "trail", "both", "unknown"]:
    terrain = payload.get("terrain")
    text = " ".join(terrain) if isinstance(terrain, list) else str(terrain or "")
    text = text.lower()
    road = any(w in text for w in _ROAD_WORDS)
    trail = any(w in text for w in _TRAIL_WORDS)
    if road and trail:
        return "both"
    if road:
        return "road"
    if trail:
        return "trail"
    return "unknown"


def filter_catalog(
    chunks: list[dict[str, Any]], surface: str | None, preferred_brands: str | None
) -> list[dict[str, Any]]:
    wanted = (surface or "").strip().lower()
    if wanted in ("road", "trail"):
        excluded = "trail" if wanted == "road" else "road"
        by_surface = [c for c in chunks if surface_of(_payload(c)) != excluded]
        if len(by_surface) < MIN_ENTRIES:
            by_surface = chunks
    else:
        by_surface = chunks

    brands = [b.strip().lower() for b in (preferred_brands or "").split(",") if b.strip()]
    if brands:
        by_brand = [c for c in by_surface if str(_payload(c).get("brand", "")).strip().lower() in brands]
        if len(by_brand) >= MIN_BRAND_ENTRIES:
            return by_brand
    return by_surface


def _norm(text: Any) -> str:
    return "".join(ch for ch in str(text or "").lower() if ch.isalnum())


def _as_text(value: Any) -> str:
    return ", ".join(map(str, value)) if isinstance(value, list) else str(value or "")


def ground_recommendations(recs: list[dict[str, Any]], chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Tie each recommendation to the catalog entry it names. The brand always comes from the catalog and empty
    fields are filled from it (Claude once returned brand "X" with every spec blank); a shoe matching no entry
    is dropped, since the engine never recommends outside the KB."""
    entries = []
    for chunk in chunks:
        payload = _payload(chunk)
        names = {
            _norm(payload.get("model")),
            _norm(chunk.get("title")),
            _norm(f"{payload.get('brand', '')}{payload.get('model', '')}"),
        } - {""}
        entries.append((payload, names))

    grounded = []
    for rec in recs:
        name = _norm(rec.get("model"))
        if len(name) < 3:
            continue
        hits = [p for p, names in entries if name in names] or [
            p for p, names in entries if any(name in n or (len(n) >= 3 and n in name) for n in names)
        ]
        if not hits:
            continue
        brand = _norm(rec.get("brand"))
        payload = next((p for p in hits if _norm(p.get("brand")) == brand), hits[0])
        out = dict(rec)
        if payload.get("brand"):
            out["brand"] = str(payload["brand"])
        for field, value in rec.items():
            if not str(value or "").strip() and payload.get(field):
                out[field] = _as_text(payload[field])
        grounded.append(out)
    return grounded
