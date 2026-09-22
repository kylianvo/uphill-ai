"""kb_search tool: semantic search for scheduler/nutrition doctrine via
Qdrant, plain keyword lookup for race_courses (not embedded in Qdrant --
see docs/superpowers/specs/2026-09-22-coach-chat-read-tools-design.md §4.4)."""

from typing import Any, Literal

import db
from services import kb_retrieval
from services.coach_tools.base import ToolResult


def _citation_from_chunk(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "book": "Training for the Uphill Athlete",
        "chapter": item.get("chapter") or "",
        "section": item.get("title", ""),
        "quote": (item.get("content") or "")[:280],
        "relevance_score": item.get("score"),
    }


def _citation_from_race_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "book": "Uphill AI Race Course Library",
        "chapter": "",
        "section": chunk.get("title", ""),
        "quote": (chunk.get("content") or "")[:280],
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
        citations = [_citation_from_chunk(h) for h in hits]
    else:
        # "nutrition" and "all" both go through search_principles, which already
        # covers both the scheduler and nutrition_principles Qdrant collections.
        hits = kb_retrieval.search_principles(query=query, api_key=api_key)
        citations = [_citation_from_chunk(h) for h in hits]

    card_data = {"query": query, "citations": citations}
    return ToolResult(
        tool_call_id="", name="kb_search", status="success", card_type="knowledge_citations", card_data=card_data
    )
