"""The coach's weekly review on the plan screen: three short messages and the session to nail.

What is true (adherence, missed reasons, milestones, readiness, goal state) is computed here and never left
to the model; the tone is chosen by rules; Gemini only words it, and its text is rejected unless every number
in it is in the facts. Without a key, or on any failure, a rule-based sentence says the same thing.
"""

import asyncio
import hashlib
import json
import re
from collections import Counter
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

import telemetry
from config import settings
from log_utils import get_logger
from services import beginner_milestones, claude_llm, observability, plan_journey
from services.plan_generator import narrative_lang_instruction

_logger = get_logger(__name__)

SLIPPED_BELOW = 0.6  # a finished week under this share of planned sessions is a slip
SOLID_FROM = 0.8  # at or above this it was a solid week
MIN_SESSIONS = 2  # fewer planned sessions say nothing about consistency
MAX_TEXT_CHARS = 200  # per message
_FATIGUE = {"fatigued", "overreaching"}

REVIEW_PROMPT = """You are Coach Uphill, a warm, honest trail-running coach texting your athlete on Monday morning.
Write the weekly review as exactly THREE short chat messages (each at most 200 characters) and one "nail" line.

1. Last week: what the athlete actually did (last_week, consistent_weeks, milestones_just_done). Week 1 (no last_week):
   a short welcome to the plan instead.
2. This week: the focus in plain words (this_week.focus: leg_strength = two ME sessions build the legs for the climbs;
   first_zone3 / zone3 = controlled Zone 3 intervals; deload = an easier week to absorb the work; taper / race_week /
   recovery; aerobic_base = easy volume) with the key sessions by day, and what it builds for THIS race (race).
3. Watch out: ONE simple rule the athlete can check themselves this week.
nail: the one session to nail (this_week.nail): day, title, minutes, one cue.

Tone: {{tone}}. encourage = proud of real consistency; push = understanding, never blames, offers a way forward;
heads_up = says the concern plainly (readiness_flag, feasibility_verdict, path, plan_supported) with one next step;
steady = calm and motivating.
Use ONLY the facts. Every number you write must appear in the facts; no invented sessions, reasons or climbs. No medical
advice, no guilt, at most one emoji in all, no exclamation marks. Speak to the athlete ("you"), never about "the plan"
or what "we incorporated".

FACTS:
{{facts}}

Return ONLY a JSON object: {"messages": ["<1>", "<2>", "<3>"], "nail": "<nail line>"}

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
    "first_session": ("your first run/walk session", "buổi chạy/đi bộ đầu tiên"),
    "jog_5": ("5 minutes of unbroken jogging", "5 phút chạy liên tục"),
    "jog_10": ("10 minutes of unbroken jogging", "10 phút chạy liên tục"),
    "jog_20": ("20 minutes of unbroken jogging", "20 phút chạy liên tục"),
    "jog_30": ("30 minutes of non-stop running", "30 phút chạy không nghỉ"),
    "first_5k": ("your first 5 km", "5 km đầu tiên"),
    "jog_45": ("45 minutes of non-stop running", "45 phút chạy không nghỉ"),
    "jog_60": ("60 minutes of non-stop running", "60 phút chạy không nghỉ"),
    "first_10k": ("your first 10 km", "10 km đầu tiên"),
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


def _minutes(w: dict[str, Any]) -> int:
    return int(round(float(w.get("duration_minutes") or 0)))


def _focus(rows: list[dict[str, Any]], earlier: list[dict[str, Any]], week: int, total: int, km: float | None) -> str:
    """What this week is for, in one word the messages are built around."""
    from services.plan_generator import PlanGenerator

    phase = next((w.get("phase") for w in rows if w.get("phase")), "")
    if phase in ("Taper", "Race Week", "Recovery"):
        return {"Taper": "taper", "Race Week": "race_week", "Recovery": "recovery"}[phase]
    if PlanGenerator.is_deload_week(week, total, km):
        return "deload"
    if sum(w.get("type") == "Muscular Endurance" for w in rows) >= 2:
        return "leg_strength"
    if any(w.get("target_zone") == "Zone 3" for w in rows):
        return "zone3" if any(w.get("target_zone") == "Zone 3" for w in earlier) else "first_zone3"
    return "aerobic_base"


def _this_week(workouts: list[dict[str, Any]], week: int, total: int, km: float | None) -> dict[str, Any] | None:
    order = {d: i for i, d in enumerate(plan_journey.plan_lint.DAYS)}
    rows = sorted(
        (w for w in workouts if w.get("week_number") == week and w.get("type") != "Rest"),
        key=lambda w: order.get(w.get("day_of_week"), 9),
    )
    if not rows:
        return None
    key = [w for w in rows if w.get("type") in ("Long Run", "Muscular Endurance") or w.get("target_zone") == "Zone 3"]
    nail = next((w for w in rows if w.get("is_priority")), None) or next(
        (w for w in rows if w.get("type") == "Long Run"), None
    )
    earlier = [w for w in workouts if (w.get("week_number") or 0) < week]

    def brief(w: dict[str, Any]) -> dict[str, Any]:
        return {"day": w.get("day_of_week"), "title": w.get("title") or w.get("type"), "minutes": _minutes(w)}

    return {
        "focus": _focus(rows, earlier, week, total, km),
        "sessions": len(rows),
        "total_minutes": sum(_minutes(w) for w in rows),
        "key_sessions": [brief(w) for w in key],
        "nail": brief(nail) if nail else None,
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
    beginner_rows: list[dict[str, Any]] | None = None,
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
    reached_now = beginner_milestones.just_reached(beginner_rows or [], datetime.combine(today, time.max, UTC))
    return {
        "current_week": week,
        "total_weeks": total,
        "phase": next((w.get("phase") for w in workouts if w.get("week_number") == week and w.get("phase")), None),
        "days_to_race": plan_journey.days_to_race(plan.get("race_date"), today),
        "last_week": last,
        "consistent_weeks": consistent,
        "milestones_just_done": [{"key": m.key, "week": m.week} for m in done_now]
        + [{"key": k, "week": week - 1} for k in reached_now],
        "next_session": {
            "day": nxt.get("day_of_week"),
            "title": nxt.get("title") or nxt.get("type"),
            "minutes": nxt.get("duration_minutes"),
        }
        if nxt
        else None,
        "race": {
            "name": plan.get("race_name"),
            "distance_km": plan.get("course_distance_km"),
            "elevation_gain_m": plan.get("course_elevation_gain_m"),
        },
        "this_week": _this_week(workouts, week, total, plan.get("course_distance_km")),
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
    return "steady" if f.get("this_week") else None


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


_FOCUS = {  # (this week, what it builds, watch out) per focus, EN then VI
    "leg_strength": (
        ("This week is legs: {sessions}.", "Strong legs now are what keep you climbing when others walk."),
        "Keep the day after ME easy. Heavy legs on the long run mean ME was too hard.",
        ("Tuần này tập chân: {sessions}.", "Chân khỏe bây giờ giúp bạn vẫn leo tốt khi người khác phải đi bộ."),
        "Giữ ngày sau buổi ME thật nhẹ. Chân nặng trong Long Run nghĩa là buổi ME quá sức.",
    ),
    "first_zone3": (
        ("Your first Zone 3 week: {sessions}.", "It teaches your legs to hold a strong climbing effort for longer."),
        "Zone 3 is hard but controlled: if you cannot say a few words, ease off.",
        ("Tuần Zone 3 đầu tiên: {sessions}.", "Nó dạy chân giữ được cường độ leo mạnh lâu hơn."),
        "Zone 3 là nặng nhưng kiểm soát được: nếu không nói được vài từ, hãy chậm lại.",
    ),
    "zone3": (
        ("Zone 3 week: {sessions}.", "Each one makes race-day climbing effort feel easier."),
        "Zone 3 is hard but controlled: if you cannot say a few words, ease off.",
        ("Tuần Zone 3: {sessions}.", "Mỗi buổi giúp cường độ leo ngày race nhẹ nhàng hơn."),
        "Zone 3 là nặng nhưng kiểm soát được: nếu không nói được vài từ, hãy chậm lại.",
    ),
    "deload": (
        ("Easier week: {sessions}.", "This is where the last weeks of work turn into fitness."),
        "Less is the point this week: do not add extra sessions.",
        ("Tuần nhẹ: {sessions}.", "Đây là lúc công sức các tuần trước biến thành thể lực."),
        "Ít hơn chính là mục tiêu tuần này: đừng tập thêm.",
    ),
    "taper": (
        ("Taper week: {sessions}.", "You arrive at the start line fresh, with the fitness already built."),
        "Feeling restless is normal. Do not add sessions to calm the nerves.",
        ("Tuần Taper: {sessions}.", "Bạn đến vạch xuất phát tươi mới, thể lực đã có sẵn."),
        "Bồn chồn là bình thường. Đừng tập thêm để trấn an bản thân.",
    ),
    "race_week": (
        ("Race week: {sessions}.", "Short and easy keeps your legs sharp for race day."),
        "Sleep, eat and stay off your feet. Nothing new this week.",
        ("Tuần Race: {sessions}.", "Ngắn và nhẹ giữ chân sắc bén cho ngày race."),
        "Ngủ đủ, ăn đủ và nghỉ chân. Không thử gì mới tuần này.",
    ),
    "recovery": (
        ("Recovery week: {sessions}.", "Your body rebuilds after the race; let it."),
        "Only easy movement. Pain or heavy legs mean rest another day.",
        ("Tuần hồi phục: {sessions}.", "Cơ thể đang phục hồi sau race; hãy để nó nghỉ."),
        "Chỉ vận động nhẹ. Đau hoặc chân nặng thì nghỉ thêm một ngày.",
    ),
    "aerobic_base": (
        ("This week is easy volume: {sessions}.", "Easy miles build the engine you will race on."),
        "Keep easy runs truly easy: you should be able to talk the whole time.",
        ("Tuần này chạy nhẹ tích lũy: {sessions}.", "Những km nhẹ xây động cơ cho ngày race."),
        "Giữ các buổi nhẹ thật nhẹ: bạn phải nói chuyện được suốt buổi.",
    ),
}


def fallback_review(f: dict[str, Any], tone: str, lang: str) -> dict[str, Any]:
    """The same three messages and nail, written by rules: used without a key or when the model's text fails a check."""
    vi = lang == "vi"
    week = f.get("this_week") or {}
    en_week, en_watch, vi_week, vi_watch = _FOCUS.get(week.get("focus") or "aerobic_base", _FOCUS["aerobic_base"])
    (this, builds), watch = (vi_week, vi_watch) if vi else (en_week, en_watch)
    sessions = ", ".join(f"{(s['day'] or '')[:3]} {s['title']}" for s in week.get("key_sessions") or []) or (
        f"{week.get('sessions')} buổi" if vi else f"{week.get('sessions')} sessions"
    )
    if f.get("last_week"):
        first = (
            fallback_text(f, tone, lang)
            if tone in ("encourage", "push", "heads_up")
            else (
                f"Tuần trước bạn hoàn thành {f['last_week']['completed']}/{f['last_week']['planned']} buổi."
                if vi
                else f"Last week you completed {f['last_week']['completed']}/{f['last_week']['planned']} sessions."
            )
        )
    else:
        first = (
            "Chào mừng bạn đến với plan. Mọi thứ bắt đầu từ đây."
            if vi
            else "Welcome to your plan. This is where it starts."
        )
    nail = week.get("nail")
    return {
        "messages": [first, f"{this.format(sessions=sessions)} {builds}", watch],
        "nail": f"{nail['day']}: {nail['title']}, {nail['minutes']} {'phút' if vi else 'min'}." if nail else None,
    }


def grounded(text: str, f: dict[str, Any]) -> bool:
    """Every number in the message must appear in the facts."""
    allowed = set(re.findall(r"\d+", json.dumps(f, default=str)))
    prose = re.sub(r"\b(?:zone|z)\s*\d\b", "", text, flags=re.IGNORECASE)  # "Zone 2" is a label, not a claim
    return all(n in allowed for n in re.findall(r"\d+", prose))


def _parse(text: str) -> dict[str, Any] | None:
    """{messages: [3 strings], nail} or None when the shape is wrong."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        data = json.loads(text[start : end + 1])
        messages = [str(m).strip() for m in data.get("messages") or []]
        nail = str(data.get("nail") or "").strip() or None
    except (ValueError, AttributeError, TypeError):
        return None
    if len(messages) != 3 or not all(messages):
        return None
    return {"messages": messages, "nail": nail}


def acceptable(review: dict[str, Any], f: dict[str, Any]) -> bool:
    parts = [*review["messages"], review.get("nail") or ""]
    return all(len(p) <= MAX_TEXT_CHARS for p in parts) and all(grounded(p, f) for p in parts)


async def _worded(f: dict[str, Any], tone: str, lang: str, api_key: str) -> dict[str, Any] | None:
    from google import genai as _genai

    provider = settings.COACH_NUDGE_LLM_PROVIDER
    tpl = observability.load_prompt("coach_review", REVIEW_PROMPT, label=claude_llm.prompt_label(provider))
    prompt = observability.compile_prompt(
        tpl,
        {
            "tone": tone,
            "facts": json.dumps(f, ensure_ascii=False, default=str),
            "lang_instruction": narrative_lang_instruction({"lang": lang}, ""),
        },
    )
    with observability.generation(
        "generation",
        feature="coach_nudge",
        model=claude_llm.model_for(provider),
        metadata={"tier": "primary"},
        prompt=tpl,
    ) as generation:
        if claude_llm.is_claude(provider):
            return _parse(await asyncio.to_thread(claude_llm.call, prompt, generation))
        client = _genai.Client(api_key=api_key)
        response = await asyncio.to_thread(client.models.generate_content, model=settings.GEMINI_MODEL, contents=prompt)
        generation.set_usage(observability.Usage.from_genai(response.usage_metadata))
    return _parse(response.text)


async def nudge(f: dict[str, Any], lang: str, api_key: str | None) -> dict[str, Any] | None:
    """{tone, text, messages, nail, source, facts_hash} or None when there is no current week. Never raises.
    `text` joins the messages for app builds that only read one line."""
    tone = tone_for(f)
    if tone is None:
        return None
    review, source = None, "rules"
    api_key = claude_llm.key_for(settings.COACH_NUDGE_LLM_PROVIDER, api_key)
    if api_key:
        try:
            with observability.trace("coach_nudge", feature="coach_nudge"):
                candidate = await _worded(f, tone, lang, api_key)
            if candidate and acceptable(candidate, f):
                review, source = candidate, "model"
        except Exception as ex:  # noqa: BLE001
            _logger.warning(f"[CoachNudge] model FAILED: {type(ex).__name__}: {ex}")
    review = review or fallback_review(f, tone, lang)
    telemetry.coach_nudge_total.labels(tone=tone, source=source).inc()
    return {
        "tone": tone,
        "text": " ".join(review["messages"]),
        "messages": review["messages"],
        "nail": review.get("nail"),
        "source": source,
        "facts_hash": facts_hash(f, tone, lang),
    }
