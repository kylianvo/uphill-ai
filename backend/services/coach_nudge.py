"""The coach message on the plan screen: one short, honest line, or silence.

What is true (adherence, missed reasons, milestones, readiness, goal state) is computed here and never left
to the model; the tone is chosen by rules; Gemini only words it, and its text is rejected unless every number
in it is in the facts. Without a key, or on any failure, a rule-based sentence says the same thing.
"""

import asyncio
import hashlib
import json
import re
from collections import Counter
from datetime import date, timedelta
from typing import Any

import telemetry
from config import settings
from log_utils import get_logger
from services import observability, plan_journey, vi_humanizer
from services.plan_generator import narrative_lang_instruction

_logger = get_logger(__name__)

SLIPPED_BELOW = 0.6  # a finished week under this share of planned sessions is a slip
SOLID_FROM = 0.8  # at or above this it was a solid week
MIN_SESSIONS = 2  # fewer planned sessions say nothing about consistency
MAX_TEXT_CHARS = 240
_FATIGUE = {"fatigued", "overreaching"}

NUDGE_PROMPT = """You are Coach Uphill, a calm, honest trail-running coach. Write ONE message of at most two short
sentences for the athlete's plan screen.

Tone: {{tone}}. encourage = recognise real consistency; push = a gentle nudge that offers a way forward and never
blames; heads_up = something the athlete should know, said plainly.

Use ONLY the facts below. Do not invent numbers, sessions or reasons. No medical advice, no guilt, no exclamation marks.
- push: say what happened in plain words, then offer ONE concrete way forward: the next session (next_session) kept
  easy, or adapting the week. Never blame, never repeat the days-to-race count.
- heads_up: name the specific reason from the facts (path.b = behind means aerobic speed is behind the path to the
  B goal; readiness_flag; feasibility_verdict; plan_supported = false means the plan does not yet back the goal
  times) and give ONE next step (keep Zone 2 sessions steady, adapt the week, or open Goal). Do not just restate adherence.
- encourage: name what was consistent (completed sessions, consistent_weeks, a milestone) in one sentence.

FACTS:
{{facts}}

Return ONLY a JSON object: {"text": "<the message>"}

{{lang_instruction}}"""

_REASON = {  # the missed-session reasons the athlete picks (workouts.missed_reason), in plain words
    "busy": ("busy", "bận"),
    "sick": ("sick", "ốm"),
    "pain": ("pain", "đau"),
    "tired": ("tired", "mệt"),
    "weather": ("weather", "thời tiết"),
    "other": ("other", "lý do khác"),
}

_MILESTONE = {
    "long_run_3h": ("your first 3-hour Long Run", "buổi Long Run 3 giờ đầu tiên"),
    "first_recovery_week": ("your first recovery week", "tuần recovery đầu tiên"),
    "peak_week": ("your peak week", "tuần peak"),
    "taper_start": ("the start of your taper", "tuần bắt đầu Taper"),
    "race_week": ("race week", "tuần Race"),
}


def _monday(iso: str) -> date:
    d = date.fromisoformat(str(iso)[:10])
    return d - timedelta(days=d.weekday())


def _week_stats(workouts: list[dict[str, Any]], week: int) -> dict[str, Any] | None:
    ws = [w for w in workouts if w.get("week_number") == week and w.get("type") != "Rest"]
    if not ws:
        return None
    done = sum(1 for w in ws if w.get("is_completed") == 1)
    missed = [w for w in ws if w.get("is_missed") == 1 and w.get("is_completed") != 1]
    return {
        "planned": len(ws),
        "completed": done,
        "missed": len(missed),
        "adherence": round(done / len(ws), 2),
        "missed_reasons": dict(Counter(w["missed_reason"] for w in missed if w.get("missed_reason"))),
    }


def facts_for(
    plan: dict[str, Any],
    workouts: list[dict[str, Any]],
    today: date,
    *,
    readiness_flag: str | None,
    feasibility_verdict: str | None,
    plan_supported: bool,
    path: dict[str, Any] | None = None,
) -> dict[str, Any]:
    total = int(plan.get("total_weeks") or 0)
    start = _monday(plan["start_date"]) if plan.get("start_date") else today - timedelta(days=today.weekday())
    week = max(1, min(total or 1, (today - start).days // 7 + 1))
    last = _week_stats(workouts, week - 1) if week > 1 else None
    consistent = 0
    for wk in range(week - 1, 0, -1):
        s = _week_stats(workouts, wk)
        if not s or s["planned"] < MIN_SESSIONS or s["adherence"] < SOLID_FROM:
            break
        consistent += 1
    order = {d: i for i, d in enumerate(plan_journey.plan_lint.DAYS)}
    upcoming = sorted(
        (
            w
            for w in workouts
            if w.get("week_number") == week
            and w.get("type") != "Rest"
            and w.get("is_completed") != 1
            and w.get("is_missed") != 1
            and order.get(w.get("day_of_week"), 9) >= today.weekday()
        ),
        key=lambda w: order.get(w.get("day_of_week"), 9),
    )
    nxt = upcoming[0] if upcoming else None
    done_now = [m for m in plan_journey.milestones(workouts, week) if m.done and m.week == week - 1]
    return {
        "current_week": week,
        "total_weeks": total,
        "phase": next((w.get("phase") for w in workouts if w.get("week_number") == week and w.get("phase")), None),
        "days_to_race": plan_journey.days_to_race(plan.get("race_date"), today),
        "last_week": last,
        "consistent_weeks": consistent,
        "milestones_just_done": [{"key": m.key, "week": m.week} for m in done_now],
        "next_session": {
            "day": nxt.get("day_of_week"),
            "title": nxt.get("title") or nxt.get("type"),
            "minutes": nxt.get("duration_minutes"),
        }
        if nxt
        else None,
        "readiness_flag": readiness_flag,
        "feasibility_verdict": feasibility_verdict,
        "plan_supported": plan_supported,
        "path": {k: path[k] for k in ("b", "a", "measured_pct", "weeks", "confidence")} if path else None,
    }


def tone_for(f: dict[str, Any]) -> str | None:
    if (
        f.get("readiness_flag") in _FATIGUE
        or f.get("feasibility_verdict") == "unsupported"
        or not f.get("plan_supported", True)
    ):
        return "heads_up"
    path = f.get("path")
    if path and path["confidence"] != "low" and path["b"] == "behind":
        return "heads_up"  # B is the promise: say so plainly when training is not on its path
    last = f.get("last_week")
    meaningful = bool(last) and last["planned"] >= MIN_SESSIONS
    if meaningful and last["adherence"] < SLIPPED_BELOW:
        return "push"
    ahead = bool(path) and path["confidence"] != "low" and "ahead" in (path["a"], path["b"])
    if f.get("milestones_just_done") or ahead or (meaningful and last["adherence"] >= SOLID_FROM):
        return "encourage"
    return None


def facts_hash(f: dict[str, Any], tone: str, lang: str) -> str:
    return hashlib.sha256(json.dumps([f, tone, lang], sort_keys=True, default=str).encode()).hexdigest()[:16]


def fallback_text(f: dict[str, Any], tone: str, lang: str) -> str:
    vi = lang == "vi"
    last = f.get("last_week") or {}
    ratio = f"{last.get('completed')}/{last.get('planned')}" if last else ""
    if tone == "encourage" and not f.get("milestones_just_done") and (f.get("path") or {}).get("a") == "ahead":
        return (
            "Tốc độ aerobic của bạn đang nhanh hơn lộ trình. Giữ nhịp này nhé."
            if vi
            else "Your aerobic speed is ahead of the path. Keep this rhythm."
        )
    if tone == "encourage":
        ms = (f.get("milestones_just_done") or [None])[0]
        if ms and ms["key"] in _MILESTONE:
            label = _MILESTONE[ms["key"]][1 if vi else 0]
            return f"Bạn vừa qua {label}. Giữ nhịp này nhé." if vi else f"You just passed {label}. Keep this rhythm."
        return (
            f"Tuần trước bạn hoàn thành {ratio} buổi. Giữ nhịp này nhé."
            if vi
            else f"You completed {ratio} sessions last week. Keep this rhythm."
        )
    if tone == "push":
        reasons = last.get("missed_reasons") or {}
        top = max(reasons, key=reasons.get) if reasons else None
        reason = f" ({_REASON.get(top, (top, top))[1 if vi else 0]})" if top else ""
        return (
            f"Tuần trước chỉ được {ratio} buổi{reason}. Không sao: chọn buổi kế tiếp và chạy nhẹ, hoặc điều chỉnh tuần này."
            if vi
            else f"Last week held {ratio} sessions{reason}. That happens: pick the next session and keep it easy, or adapt this week."
        )
    path = f.get("path")
    if path and path["b"] == "behind" and path["confidence"] != "low":
        return (
            "Tốc độ aerobic của bạn chưa theo kịp lộ trình mục tiêu B. Giữ đều các buổi Zone 2 và xem mục Goal."
            if vi
            else "Your aerobic speed is not yet on the path to your B goal. Keep the Zone 2 sessions steady and see Goal."
        )
    if f.get("readiness_flag") in _FATIGUE:
        return (
            "Chỉ số hồi phục của bạn đang thấp. Giữ tuần này nhẹ và cân nhắc điều chỉnh tuần."
            if vi
            else "Your recovery signals are low. Keep this week easy and consider adapting it."
        )
    if f.get("feasibility_verdict") == "unsupported":
        return (
            "Tuần tập hiện tại chưa đủ chỗ cho mục tiêu này. Xem mục Goal để biết cách điều chỉnh."
            if vi
            else "Your week does not have room for this goal yet. See Goal for options."
        )
    return (
        "Plan chưa đỡ hết mục tiêu nên thời gian mục tiêu đã lùi lại."
        if vi
        else "The plan does not fully back the goal yet, so the goal times moved later."
    )


def grounded(text: str, f: dict[str, Any]) -> bool:
    """Every number in the message must appear in the facts."""
    allowed = set(re.findall(r"\d+", json.dumps(f, default=str)))
    prose = re.sub(r"\b(?:zone|z)\s*\d\b", "", text, flags=re.IGNORECASE)  # "Zone 2" is a label, not a claim
    return all(n in allowed for n in re.findall(r"\d+", prose))


def _parse(text: str) -> str | None:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        value = str(json.loads(text[start : end + 1]).get("text") or "").strip()
    except (ValueError, AttributeError):
        return None
    return value or None


async def _worded(f: dict[str, Any], tone: str, lang: str, api_key: str) -> str | None:
    from google import genai as _genai

    tpl = observability.load_prompt("coach_nudge", NUDGE_PROMPT)
    prompt = observability.compile_prompt(
        tpl,
        {
            "tone": tone,
            "facts": json.dumps(f, ensure_ascii=False, default=str),
            "lang_instruction": narrative_lang_instruction({"lang": lang}, ""),
        },
    )
    client = _genai.Client(api_key=api_key)
    with observability.generation(
        "generation", feature="coach_nudge", model=settings.GEMINI_MODEL, metadata={"tier": "primary"}, prompt=tpl
    ) as generation:
        response = await asyncio.to_thread(client.models.generate_content, model=settings.GEMINI_MODEL, contents=prompt)
        generation.set_usage(observability.Usage.from_genai(response.usage_metadata))
    return _parse(response.text)


async def nudge(f: dict[str, Any], lang: str, api_key: str | None) -> dict[str, Any] | None:
    """{tone, text, source, facts_hash} or None when there is nothing to say. Never raises."""
    tone = tone_for(f)
    if tone is None:
        return None
    text, source = None, "rules"
    if api_key:
        try:
            with observability.trace("coach_nudge", feature="coach_nudge"):
                candidate = await _worded(f, tone, lang, api_key)
            if candidate and len(candidate) <= MAX_TEXT_CHARS and grounded(candidate, f):
                text, source = (await vi_humanizer.humanize(candidate) if lang == "vi" else candidate), "model"
        except Exception as ex:  # noqa: BLE001
            _logger.warning(f"[CoachNudge] Gemini FAILED: {type(ex).__name__}: {ex}")
    telemetry.coach_nudge_total.labels(tone=tone, source=source).inc()
    return {
        "tone": tone,
        "text": text or fallback_text(f, tone, lang),
        "source": source,
        "facts_hash": facts_hash(f, tone, lang),
    }
