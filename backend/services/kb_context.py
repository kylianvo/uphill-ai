"""Renders kb_chunks rows into compact prompt-context blocks for runtime Gemini calls.

Catalog domains (gear, nutrition) inject their ENTIRE distilled catalog — one JSON
object per line — so the model filters over the complete set (no retrieval-miss risk).
Principle chunks render as titled prose sections.
"""

import json
from typing import Any


def _payload_as_dict(payload: Any) -> dict[str, Any]:
    if payload is None:
        return {}
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except Exception:
            return {}
    return dict(payload)


def render_catalog_context(chunks: list[dict[str, Any]], domain_label: str) -> str:
    if not chunks:
        return ""
    lines = []
    for chunk in chunks:
        entry = {"name": chunk.get("title", "")}
        entry.update(_payload_as_dict(chunk.get("payload")))
        lines.append(json.dumps(entry, ensure_ascii=False))
    return (
        f"=== {domain_label.upper()} KNOWLEDGE BASE "
        "(this is the complete catalog — recommend ONLY from these entries) ===\n"
        + "\n".join(lines)
        + "\n=== END KNOWLEDGE BASE ===\n"
    )


def render_principles_context(chunks: list[dict[str, Any]], heading: str = "GROUNDING PRINCIPLES") -> str:
    if not chunks:
        return ""
    parts = [f"[{chunk.get('title', '')}]\n{chunk.get('content', '')}" for chunk in chunks]
    return f"=== {heading} ===\n" + "\n\n".join(parts) + f"\n=== END {heading} ===\n"
