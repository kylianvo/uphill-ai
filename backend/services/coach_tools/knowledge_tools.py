"""kb_search tool: semantic search for scheduler/nutrition doctrine via
Qdrant, plain keyword lookup for race_courses (not embedded in Qdrant --
see docs/superpowers/specs/2026-09-22-coach-chat-read-tools-design.md §4.4).

Citations take the Knowledge Hub card shape frontend/src/components/KnowledgeCard.tsx
renders (card.topic, card.chapter_title, card.summary, card.key_points, card.tags),
so the chat can reuse that component instead of a separate renderer."""

from typing import Any, Literal

import db
from services import kb_retrieval
from services.coach_tools.base import ToolResult

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


def _citation_from_race_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "topic": "Pacing",
        "chapter_title": chunk.get("title", ""),
        "summary": (chunk.get("content") or "")[:280],
        "key_points": [],
        "tags": ["Uphill AI Race Course Library"],
        "relevance_score": None,
    }


def kb_search_impl(
    user_id: int,
    query: str,
    domain: Literal["all", "scheduler", "nutrition", "race_courses"] = "all",
    *,
    api_key: str,
) -> ToolResult:
    if domain == "race_courses":
        chunks = db.get_kb_chunks("race_courses", kind="race_profile")
        q_lower = query.lower()
        matches = [c for c in chunks if q_lower in (c.get("title", "") + " " + (c.get("content") or "")).lower()]
        citations = [_citation_from_race_chunk(c) for c in matches[:6]]
    elif domain == "scheduler":
        hits = kb_retrieval.search_scheduler_chunks(query=query, api_key=api_key)
        citations = [_citation_from_chunk(h, domain) for h in hits]
    else:
        # "nutrition" and "all" both go through search_principles, which already
        # covers both the scheduler and nutrition_principles Qdrant collections.
        hits = kb_retrieval.search_principles(query=query, api_key=api_key)
        citations = [_citation_from_chunk(h, domain) for h in hits]

    card_data = {"query": query, "citations": citations}
    return ToolResult(
        tool_call_id="", name="kb_search", status="success", card_type="knowledge_citations", card_data=card_data
    )
