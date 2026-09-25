"""Athlete trusted context assembler, token budget trimmer, and citation resolver."""

import re
import urllib.parse
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import db
from db import CoachChatError


def _is_valid_web_url(url: str | None) -> bool:
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urllib.parse.urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def build_chat_context(
    user_id: int,
    question: str,
    thread_id: int | None = None,
    retrieval_evidence: list[dict[str, Any]] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Assemble trusted server context for the authenticated athlete.

    Pulls physiology/preferences, active plan workouts (current & next week),
    recent activities (last 14 days, max 8), and thread history (retained 20 ok messages, <= 90 days).
    """
    current_time = now or datetime.now(UTC)
    retention_cutoff = current_time - timedelta(days=90)
    activity_cutoff = current_time - timedelta(days=14)

    # 1. Athlete profile & physiology
    athlete_row = db.get_user_by_id(user_id) or {}
    athlete_context = {
        "age": athlete_row.get("age"),
        "gender": athlete_row.get("gender"),
        "height_cm": athlete_row.get("height_cm"),
        "weight_kg": athlete_row.get("weight_kg"),
        "max_hr": athlete_row.get("max_hr"),
        "resting_hr": athlete_row.get("resting_hr"),
        "aet_hr": athlete_row.get("aet_hr"),
        "ant_hr": athlete_row.get("ant_hr"),
        "current_weekly_km": athlete_row.get("current_weekly_km"),
        "zone2_pace_min": athlete_row.get("zone2_pace_min"),
        "zone2_pace_max": athlete_row.get("zone2_pace_max"),
        "threshold_pace": athlete_row.get("threshold_pace"),
        "athlete_tier": athlete_row.get("athlete_tier"),
        "goal_type": athlete_row.get("goal_type"),
    }

    # 2. Plan and planned workouts
    plan = db.get_active_plan(user_id)
    plan_workouts: list[dict[str, Any]] = []
    if plan and plan.get("id"):
        all_workouts = db.get_plan_workouts(plan["id"]) or []
        # Keep current and upcoming workouts (e.g. within next 14 days)
        plan_workouts = all_workouts[:14]

    # 3. Recent completed activities (max 8, last 14 days)
    all_activities = db.get_activities_for_user(user_id, limit=20) or []
    recent_activities = []
    for act in all_activities:
        start_time = act.get("start_time")
        if start_time:
            if isinstance(start_time, str):
                try:
                    start_time = datetime.fromisoformat(start_time)
                except Exception:
                    continue
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=UTC)
            if start_time >= activity_cutoff:
                recent_activities.append(act)
        if len(recent_activities) >= 8:
            break

    # 4. Retained thread messages (status='ok' only, <= 90 days, max 20)
    raw_messages = db.get_chat_thread_messages(user_id=user_id, limit=30) or []
    valid_history: list[dict[str, Any]] = []
    for m in raw_messages:
        if m.get("status") != "ok":
            continue
        created_at = m.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at)
                except Exception:
                    continue
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=UTC)
            if created_at < retention_cutoff:
                continue
        valid_history.append(m)

    # Cap to most recent 20 messages
    valid_history = valid_history[-20:]

    # 5. Race record (claimed UTMB/VBM profiles + self-reported), <= 800 chars
    try:
        from services.race_history import prompt_summary

        race_history = prompt_summary(user_id)
    except Exception:
        race_history = ""

    return {
        "athlete": athlete_context,
        "plan": {"id": plan.get("id")} if plan else None,
        "workouts": plan_workouts,
        "recent_activities": recent_activities,
        "race_history": race_history,
        "history": valid_history,
        "evidence": list(retrieval_evidence or []),
        "question": question,
    }


def _default_token_counter(context: dict[str, Any]) -> int:
    """Fallback character-based token estimator (approx 4 chars/token)."""
    import json

    serialized = json.dumps(context, default=str)
    return len(serialized) // 4


def trim_context_to_budget(
    context: dict[str, Any],
    token_counter: Callable[[dict[str, Any]], int] | None = None,
    max_budget: int = 16000,
) -> dict[str, Any]:
    """Trim oldest history, then lowest-scoring evidence to stay within token budget.

    If essential context still exceeds budget after all history and evidence are removed,
    raises CoachChatError(code="chat_context_too_large").
    """
    counter = token_counter or _default_token_counter
    ctx = dict(context)
    history = list(ctx.get("history", []))
    evidence = list(ctx.get("evidence", []))

    # Sort evidence by score ascending so lowest scoring can be trimmed first
    evidence.sort(key=lambda x: x.get("score", 0.0))

    ctx["history"] = history
    ctx["evidence"] = evidence

    # Check essential baseline
    ctx_essential = dict(ctx)
    ctx_essential["history"] = []
    ctx_essential["evidence"] = []
    essential_tokens = counter(ctx_essential)
    if essential_tokens > max_budget:
        raise CoachChatError(code="chat_context_too_large", message="Essential athlete context exceeds token budget")

    # Step 1: Trim oldest history until under budget or empty
    while history and counter(ctx) > max_budget:
        history.pop(0)  # Drop oldest
        ctx["history"] = history

    # Step 2: If still over budget, trim lowest-scoring evidence
    while evidence and counter(ctx) > max_budget:
        evidence.pop(0)  # Drop lowest-scoring
        ctx["evidence"] = evidence

    return ctx


_REF_PATTERN = re.compile(r"\[ref:([a-zA-Z0-9_\-]+)\]|\[([0-9]{1,2})\]|\[([a-zA-Z0-9_\-]{8,32})\]")


def resolve_citations(reply_text: str, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolve citation markers in reply text against turn evidence.

    Supports numeric references (e.g. [1]), ref tags (e.g. [ref:1] or [ref:hash]),
    and raw chunk hashes (e.g. [7c9d28178ee9]).
    Attaches authoritative book provenance from Training for the Uphill Athlete.
    Validates URLs (only HTTP/HTTPS preserved, others set to None).
    """
    from services.doctrine_metadata import get_scheduler_chunk_metadata

    evidence_by_ref = {e.get("ref"): e for e in evidence if e.get("ref")}
    resolved: list[dict[str, Any]] = []
    seen_refs = set()

    for match in _REF_PATTERN.finditer(reply_text):
        ref_id = match.group(1) or match.group(2) or match.group(3)
        if not ref_id:
            continue

        ev = None
        # 1. Try matching by 1-based index if numeric
        if ref_id.isdigit():
            idx = int(ref_id) - 1
            if 0 <= idx < len(evidence):
                ev = evidence[idx]
        elif ref_id.startswith("ref:") and ref_id[4:].isdigit():
            idx = int(ref_id[4:]) - 1
            if 0 <= idx < len(evidence):
                ev = evidence[idx]

        # 2. Try matching by chunk ref hash
        if ev is None and ref_id in evidence_by_ref:
            ev = evidence_by_ref[ref_id]

        if ev is not None:
            canonical_ref = ev.get("ref") or ref_id
            if canonical_ref not in seen_refs:
                seen_refs.add(canonical_ref)
                raw_url = ev.get("url")
                safe_url = raw_url.strip() if _is_valid_web_url(raw_url) else None

                # Enrich with authoritative book metadata
                meta = get_scheduler_chunk_metadata(ev.get("title")) or {}
                book = meta.get("book") or ev.get("book") or ev.get("source_label", "Training for the Uphill Athlete")
                ch_str = meta.get("chapter") or ev.get("chapter")
                sec_str = meta.get("section") or ev.get("section")
                cit_label = meta.get("citation_label") or (f"{book} — {ch_str}" if ch_str else book)

                resolved.append(
                    {
                        "ref": canonical_ref,
                        "title": ev.get("title", ""),
                        "source_label": book,
                        "book": book,
                        "chapter": ch_str,
                        "chapter_num": meta.get("chapter_num"),
                        "chapter_title": meta.get("chapter_title"),
                        "section": sec_str,
                        "topic": meta.get("topic", ev.get("title", "")),
                        "citation_label": cit_label,
                        "url": safe_url,
                        "domain": ev.get("domain", "scheduler"),
                    }
                )

    return resolved
