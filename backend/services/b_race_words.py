"""Coach Uphill's words for B-races: the opinion before and the debrief after.

The facts and the verdict come from services/b_race.py; the model only words them. Every number in the model's
text must appear in the facts (coach_nudge.grounded), otherwise the rule-written en/vi text is used.
"""

import asyncio
import hashlib
import json
from typing import Any

from config import settings
from log_utils import get_logger
from services import claude_llm, observability
from services.coach_nudge import grounded
from services.plan_generator import narrative_lang_instruction

_logger = get_logger(__name__)
MAX_CHARS = 600

OPINION_PROMPT = """You are Coach Uphill, a trail-running coach. A runner wants to add a tune-up race (a B-race)
before their goal race. The coach's rules already decided the verdict below; you only put it into words.

FACTS (JSON): {{facts}}

Write 2-4 short sentences to the runner:
- Open with the verdict in plain words: good test, OK with conditions, risky, or not recommended.
- Give the main reason. Use only numbers that appear in FACTS; never invent one.
- If FACTS has a suggestion, name it as your pick (distance and effort).
- Warm and direct. No lecturing: the runner decides.
{{lang_instruction}}
Return JSON only: {"text": "..."}"""

DEBRIEF_PROMPT = """You are Coach Uphill, a trail-running coach. Your runner just ran a tune-up race (a B-race)
before their goal race. Write the debrief from the facts below.

FACTS (JSON): {{facts}}

Write 3-5 short sentences:
- How the time compares with the predicted range, and what it says about the goal race.
- One lesson from each rehearsal answer (fuel, pacing, gear) that matters for race day.
- The recovery: how many easy days before hard sessions return.
Use only numbers that appear in FACTS. Warm, specific, no lecturing.
{{lang_instruction}}
Return JSON only: {"text": "..."}"""

_REASONS = {
    "longer_than_trained": (
        "{km} km is longer than your longest recent run{longest_en}.",
        "{km} km dài hơn buổi chạy dài nhất gần đây của bạn{longest_vi}.",
    ),
    "too_close": (
        "It is only {days} days before your goal race.",
        "Chỉ còn {days} ngày nữa là đến race mục tiêu.",
    ),
    "overlaps_taper": (
        "Recovering from it would run into your goal-race taper.",
        "Thời gian hồi phục sẽ lấn vào giai đoạn taper của race mục tiêu.",
    ),
    "overlaps_peak": ("It lands on your peak block.", "Race này rơi vào giai đoạn peak."),
    "stacked": ("Another race is too close to this one.", "Có một race khác quá gần race này."),
    "base_phase": ("It is a big race for this early in your plan.", "Race này khá lớn so với giai đoạn đầu của plan."),
}

_LEVELS = {
    "good": (
        "Good test. {km} km fits your training. Run it as a rehearsal: the same fuel, gear and pacing you will use "
        "on race day. Plan: {taper} easy days before, {rec} easy days after.",
        "Bài test tốt. {km} km phù hợp với mức tập của bạn. Hãy chạy như buổi tập dượt: cùng dinh dưỡng, trang bị "
        "và nhịp độ như ngày race chính. Kế hoạch: {taper} ngày nhẹ trước, {rec} ngày nhẹ sau.",
    ),
    "conditions": (
        "OK, with conditions. {reasons} My pick: {pick}.",
        "Được, nhưng có điều kiện. {reasons} Mình chọn: {pick}.",
    ),
    "risky": (
        "Risky for your goal race. {reasons} My pick: {pick}.",
        "Rủi ro cho race mục tiêu. {reasons} Mình chọn: {pick}.",
    ),
    "not_recommended": (
        "Not recommended. {reasons} If you go, run it easy as a training run; your taper stays as planned.",
        "Không nên. {reasons} Nếu vẫn chạy, hãy chạy nhẹ như một buổi tập; giai đoạn taper vẫn giữ nguyên.",
    ),
}


def _km(v: Any) -> str:
    return f"{float(v):g}"


def opinion_facts(verdict: dict[str, Any], race: dict[str, Any]) -> dict[str, Any]:
    return {
        "race": {k: race.get(k) for k in ("race_name", "race_date", "distance_km", "elevation_gain_m", "effort")},
        "level": verdict["level"],
        "reasons": list(verdict.get("reasons") or []),
        "numbers": verdict.get("numbers") or {},
        "taper_days": verdict.get("taper_days"),
        "recovery_days": verdict.get("recovery_days"),
        "suggestion": verdict.get("suggestion"),
    }


def _hash(facts: dict[str, Any], lang: str) -> str:
    return hashlib.sha256(json.dumps([facts, lang], sort_keys=True, default=str).encode()).hexdigest()[:16]


def fallback_opinion(verdict: dict[str, Any], race: dict[str, Any], lang: str) -> str:
    vi = lang == "vi"
    numbers = verdict.get("numbers") or {}
    longest = numbers.get("longest_recent_km")
    values = {
        "km": _km(race["distance_km"]),
        "days": numbers.get("days_before_a"),
        "longest_en": f" ({_km(longest)} km)" if longest else "",
        "longest_vi": f" ({_km(longest)} km)" if longest else "",
        "taper": verdict.get("taper_days"),
        "rec": verdict.get("recovery_days"),
    }
    reasons = " ".join(
        _REASONS[r][1 if vi else 0].format(**values) for r in verdict.get("reasons") or [] if r in _REASONS
    )
    s = verdict.get("suggestion")
    if s:
        pick = (
            _km(s["distance_km"])
            + " km"
            + (
                ("" if s["effort"] == "race" else " với cường độ chạy dài, không dốc hết sức")
                if vi
                else ("" if s["effort"] == "race" else " at long-run effort, not all-out")
            )
        )
    else:
        pick = "chạy nhẹ như một buổi tập" if vi else "run it easy as a training run"
    text = _LEVELS[verdict["level"]][1 if vi else 0].format(**values, reasons=reasons, pick=pick)
    return " ".join(text.split())


def grounded_opinion(text: str, verdict: dict[str, Any], race: dict[str, Any]) -> bool:
    return len(text) <= MAX_CHARS and grounded(text, opinion_facts(verdict, race))


async def _model_text(prompt_name: str, template: str, facts: dict[str, Any], lang: str, api_key: str) -> str | None:
    from google import genai as _genai

    provider = settings.COACH_NUDGE_LLM_PROVIDER
    tpl = observability.load_prompt(prompt_name, template, label=claude_llm.prompt_label(provider))
    prompt = observability.compile_prompt(
        tpl,
        {
            "facts": json.dumps(facts, ensure_ascii=False, default=str),
            "lang_instruction": narrative_lang_instruction({"lang": lang}, ""),
        },
    )
    with observability.generation(
        "generation", feature="b_race", model=claude_llm.model_for(provider), prompt=tpl
    ) as gen:
        if claude_llm.is_claude(provider):
            raw = await asyncio.to_thread(claude_llm.call, prompt, gen)
        else:
            client = _genai.Client(api_key=api_key)
            response = await asyncio.to_thread(
                client.models.generate_content, model=settings.GEMINI_MODEL, contents=prompt
            )
            gen.set_usage(observability.Usage.from_genai(response.usage_metadata))
            raw = response.text
    start, end = (raw or "").find("{"), (raw or "").rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return str(json.loads(raw[start : end + 1]).get("text") or "").strip() or None
    except (ValueError, AttributeError):
        return None


async def opinion_text(
    verdict: dict[str, Any],
    race: dict[str, Any],
    lang: str,
    api_key: str | None,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """{"text", "source": "model"|"rules", "hash"}. Reuses `previous` while the facts are unchanged. Never raises."""
    facts = opinion_facts(verdict, race)
    digest = _hash(facts, lang)
    if previous and previous.get("hash") == digest:
        return previous
    key = claude_llm.key_for(settings.COACH_NUDGE_LLM_PROVIDER, api_key)
    if key:
        try:
            with observability.trace("b_race_opinion", feature="b_race"):
                text = await _model_text("b_race_opinion", OPINION_PROMPT, facts, lang, key)
            if text and grounded_opinion(text, verdict, race):
                return {"text": text, "source": "model", "hash": digest}
        except Exception as ex:  # noqa: BLE001
            _logger.warning(f"[BRace] opinion model failed: {type(ex).__name__}: {ex}")
    return {"text": fallback_opinion(verdict, race, lang), "source": "rules", "hash": digest}


def current_text(stored: dict[str, Any] | None, verdict: dict[str, Any], race: dict[str, Any], lang: str) -> str:
    """The stored words while they still describe this verdict; the rule-written text once the facts moved."""
    if stored and stored.get("hash") == _hash(opinion_facts(verdict, race), lang):
        return stored["text"]
    return fallback_opinion(verdict, race, lang)


_VS = {
    "inside": ("Right inside the predicted range: your goal-race fitness is on track.",
               "Nằm đúng trong khoảng dự đoán: thể lực cho race mục tiêu đang đúng hướng."),
    "faster": ("Faster than predicted: a good sign for your goal race.",
               "Nhanh hơn dự đoán: dấu hiệu tốt cho race mục tiêu."),
    "slower": ("Slower than predicted. Treat it as information, not a verdict.",
               "Chậm hơn dự đoán. Hãy xem đây là thông tin, không phải kết luận."),
}  # fmt: skip
_ANSWERS = {
    ("fuel", "plan"): ("Your fuel worked: keep exactly that plan for race day.",
                       "Dinh dưỡng đã ổn: giữ nguyên kế hoạch đó cho ngày race."),
    ("fuel", "stomach"): ("Your stomach struggled: try smaller, more frequent doses or a different gel on your next long runs.",
                          "Bụng bị khó chịu: thử chia nhỏ liều, dùng thường xuyên hơn hoặc đổi loại gel ở các buổi chạy dài tới."),
    ("fuel", "skipped"): ("You skipped some fuel: set a timer so it happens on race day.",
                          "Bạn đã bỏ lỡ vài lần nạp: hãy đặt hẹn giờ để ngày race không bị sót."),
    ("pacing", "even"): ("Even pacing: keep that patience.", "Nhịp độ đều: hãy giữ sự kiên nhẫn đó."),
    ("pacing", "fast_start"): ("You went out too fast: on race day, hold back on the first climb.",
                               "Bạn xuất phát quá nhanh: ngày race, hãy kìm lại ở con dốc đầu tiên."),
    ("pacing", "held_back"): ("You held back: there may be more in the tank than you think.",
                              "Bạn đã chạy dè dặt: có thể bạn còn nhiều sức hơn mình nghĩ."),
    ("gear", "ok"): ("Gear is settled.", "Trang bị đã ổn."),
    ("gear", "change"): ("Sort out the gear you want to change before your next long run.",
                         "Hãy xử lý món trang bị cần đổi trước buổi chạy dài tới."),
}  # fmt: skip


def fallback_debrief(facts: dict[str, Any], lang: str) -> str:
    vi = lang == "vi"
    i = 1 if vi else 0
    parts = []
    if facts.get("result_time"):
        parts.append(f"{facts['race_name']}: {facts['result_time']}.")
    if facts.get("vs_prediction") in _VS:
        parts.append(_VS[facts["vs_prediction"]][i])
    for key in ("fuel", "pacing", "gear"):
        if (key, (facts.get("answers") or {}).get(key)) in _ANSWERS:
            parts.append(_ANSWERS[(key, facts["answers"][key])][i])
    rec = facts["recovery_days"]
    parts.append(
        f"Chạy nhẹ {rec} ngày trước khi các buổi nặng quay lại."
        if vi
        else f"Take {rec} easy days before hard sessions return."
    )
    return " ".join(parts)


def grounded_debrief(text: str, facts: dict[str, Any]) -> bool:
    return len(text) <= MAX_CHARS and grounded(text, facts)


async def debrief_text(facts: dict[str, Any], lang: str, api_key: str | None) -> dict[str, Any]:
    """{"text", "source"}. Never raises."""
    key = claude_llm.key_for(settings.COACH_NUDGE_LLM_PROVIDER, api_key)
    if key:
        try:
            with observability.trace("b_race_debrief", feature="b_race"):
                text = await _model_text("b_race_debrief", DEBRIEF_PROMPT, facts, lang, key)
            if text and grounded_debrief(text, facts):
                return {"text": text, "source": "model"}
        except Exception as ex:  # noqa: BLE001
            _logger.warning(f"[BRace] debrief model failed: {type(ex).__name__}: {ex}")
    return {"text": fallback_debrief(facts, lang), "source": "rules"}
