"""kb_search tool: semantic search for scheduler/nutrition doctrine via
Qdrant; the curated race library through the race matcher and the shoe
catalog by name (neither is embedded in Qdrant -- see
docs/superpowers/specs/2026-09-22-coach-chat-read-tools-design.md §4.4).

Citations take the Knowledge Hub card shape frontend/src/components/KnowledgeCard.tsx
renders (card.topic, card.chapter_title, card.summary, card.key_points, card.tags),
so the chat can reuse that component instead of a separate renderer."""

import json
from typing import Any, Literal

import db
from services import kb_retrieval, race_matcher
from services.coach_tools.base import ToolResult
from services.gear_catalog import _norm, _payload, filter_catalog, surface_of

Domain = Literal["all", "scheduler", "nutrition", "race_courses", "gear"]
_SHORTLIST = 15

_DOMAIN_TOPIC: dict[str, str] = {"scheduler": "Training", "nutrition": "Nutrition"}
_DOMAIN_SOURCE_LABEL: dict[str, str] = {
    "scheduler": "Training for the Uphill Athlete",
    "nutrition": "Evoke Endurance Nutrition",
}


def _citation_from_chunk(item: dict[str, Any], requested_domain: str) -> dict[str, Any]:
    item_domain = item.get("domain") or requested_domain
    topic = _DOMAIN_TOPIC.get(item_domain, "Training")
    source_label = item.get("source_label") or _DOMAIN_SOURCE_LABEL.get(item_domain, "Training for the Uphill Athlete")
    return {
        "topic": topic,
        "chapter_title": item.get("chapter") or item.get("title", ""),
        "summary": (item.get("content") or "")[:280],
        "key_points": [],
        "tags": [source_label],
        "relevance_score": item.get("score"),
    }


def _race_points(payload: dict[str, Any]) -> list[str]:
    """The course facts a coach answers from: each distance with its climb and cutoff, terrain, climate, climbs."""
    points = []
    for d in payload.get("distances") or []:
        line = f"{d.get('course_name') or d.get('label')}: {d.get('distance_km')} km, {d.get('elevation_gain_m')} m D+"
        points.append(line + (f", cutoff {d['cutoff_hours']} h" if d.get("cutoff_hours") else ""))
    if terrain := payload.get("terrain"):
        points.append("Terrain: " + (", ".join(terrain) if isinstance(terrain, list) else str(terrain)))
    climate = payload.get("climate")
    if isinstance(climate, dict) and (notes := climate.get("notes") or climate.get("season")):
        points.append(f"Climate: {notes}")
    for climb in (payload.get("key_climbs") or [])[:3]:
        points.append(f"Key climb: {climb.get('name', '') if isinstance(climb, dict) else climb}".strip())
    return points


def _citation_from_race_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "topic": "Pacing",
        "chapter_title": chunk.get("title", ""),
        "summary": (chunk.get("content") or "")[:280],
        "key_points": _race_points(_payload(chunk)),
        "tags": ["Uphill AI Race Course Library"],
        "relevance_score": None,
    }


def _race_citations(query: str, confident_only: bool = False) -> list[dict[str, Any]]:
    """Races the matcher finds in the runner's own words ("VHT by UTMB - 100k"); a plain substring hit otherwise."""
    chunks = db.get_kb_chunks("race_courses", kind="race_profile")
    found = race_matcher.match_race_candidates(query)
    names = [] if not found.matched else [found.top.race_name] if found.auto_apply else []
    if not confident_only and found.matched and not found.auto_apply:
        names = [r.race_name for r in found.candidates]
    by_name = {_payload(c).get("race_name"): c for c in chunks}
    hits = [by_name[n] for n in names if n in by_name]
    if not hits and not confident_only:
        q_lower = query.lower()
        hits = [c for c in chunks if q_lower in (c.get("title", "") + " " + (c.get("content") or "")).lower()]
    return [_citation_from_race_chunk(c) for c in hits[:6]]


_GEAR_FIELDS = (
    ("terrain", "Terrain"),
    ("lug_depth", "Lug depth"),
    ("drop", "Drop"),
    ("stack", "Stack"),
    ("weight", "Weight"),
    ("cushioning", "Cushioning"),
    ("best_for", "Best for"),
    ("pros", "Pros"),
    ("cons", "Cons"),
)


def _citation_from_gear_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    payload = _payload(chunk)
    points = [f"{label}: {str(payload[key])[:160]}" for key, label in _GEAR_FIELDS if payload.get(key)]
    return {
        "topic": "Gear",
        "chapter_title": chunk.get("title", ""),
        "summary": str(payload.get("overview") or chunk.get("content") or "")[:280],
        "key_points": points,
        "tags": ["Uphill AI Gear Catalog"],
        "relevance_score": None,
    }


def _named_shoes(query: str, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    q = _norm(query)
    hits = []
    for chunk in chunks:
        model = _norm(_payload(chunk).get("model"))
        if _norm(chunk.get("title")) in q or (len(model) >= 4 and model in q):
            hits.append(chunk)
    return hits


_SHOE_FIELDS = (
    "foam_material", "outsole_compound", "lug_depth", "drop", "stack", "weight", "price", "pros", "cons",
    "best_for", "terrain",
)  # fmt: skip


def _shoe(chunk: dict[str, Any]) -> dict[str, str]:
    """A catalog entry in the Gear Vault recommendation shape (the iOS shoe card decodes it); every field a string."""
    payload = _payload(chunk)
    shoe = {"brand": str(payload.get("brand") or ""), "model": str(payload.get("model") or chunk.get("title") or "")}
    for key in _SHOE_FIELDS:
        value = payload.get(key)
        shoe[key] = ", ".join(map(str, value)) if isinstance(value, list) else str(value or "")
    return shoe


def _gear_search(query: str) -> tuple[list[dict[str, Any]], bool]:
    """(catalog entries, exact_match): the shoes named in the query; else that brand's models; else a shortlist for
    the surface the query names, ranked by how many of its words the shoe's description shares."""
    chunks = db.get_kb_chunks("gear", kind="catalog_item")
    if named := _named_shoes(query, chunks):
        return named[:6], True
    q = _norm(query)
    if brand := [c for c in chunks if (b := _norm(_payload(c).get("brand"))) and b in q]:
        return brand[:_SHORTLIST], False
    words = {w for w in query.lower().split() if len(w) >= 4}
    surface = "road" if "road" in words else "trail"
    pool = [c for c in filter_catalog(chunks, surface, None) if surface_of(_payload(c)) != "unknown"] or chunks
    ranked = sorted(pool, key=lambda c: -sum(w in json.dumps(_payload(c)).lower() for w in words))
    return ranked[:_SHORTLIST], False


def kb_search_impl(
    user_id: int,
    query: str,
    domain: Domain = "all",
    *,
    api_key: str,
) -> ToolResult:
    card_data: dict[str, Any] = {"query": query}
    if domain == "race_courses":
        citations = _race_citations(query)
    elif domain == "gear":
        shoes, exact = _gear_search(query)
        card_data.update(exact_match=exact, recommendations=[_shoe(c) for c in shoes], tips=[])
        return ToolResult(
            tool_call_id="", name="kb_search", status="success", card_type="shoe_recommendations", card_data=card_data
        )
    elif domain == "scheduler":
        hits = kb_retrieval.search_scheduler_chunks(query=query, api_key=api_key)
        citations = [_citation_from_chunk(h, domain) for h in hits]
    else:
        # "nutrition" and "all" both go through search_principles, which already
        # covers both the scheduler and nutrition_principles Qdrant collections.
        hits = kb_retrieval.search_principles(query=query, api_key=api_key)
        citations = [_citation_from_chunk(h, domain) for h in hits]
        if domain == "all":  # a named race or shoe answers better than doctrine about one
            citations = (
                _race_citations(query, confident_only=True)
                + [
                    _citation_from_gear_chunk(c)
                    for c in _named_shoes(query, db.get_kb_chunks("gear", kind="catalog_item"))
                ]
                + citations
            )

    card_data["citations"] = citations
    return ToolResult(
        tool_call_id="", name="kb_search", status="success", card_type="knowledge_citations", card_data=card_data
    )
