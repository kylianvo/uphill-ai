"""Pure mapping from Uphill workout rows to COROS MCP course JSON (COROS push, phase 1).

No I/O. Rules mirror the COROS MCP createTrainingPlan / updateTrainingPlan course
schema: integer seconds/meters, one intensity format per plain section, interval
groups with 1-20 repeats and no nesting, names <= 100 chars, and every name and
description is shown to the athlete verbatim, so no internal labels.

Guidance is heart rate (spec Q4): the workout's own target_hr_range in bpm, else
the COROS HR zone matching target_zone. Runs go out as sportType 1 (running):
the plan is time-based and COROS trail running forbids time targets.
"""

import re
from typing import Any, Literal

SPORT_RUNNING = 1
SPORT_REST = 4
SECTION_WARMUP, SECTION_TRAINING, SECTION_RECOVERY, SECTION_COOLDOWN = 1, 2, 3, 4
TARGET_DISTANCE, TARGET_TIME = 1, 2
INTENSITY_HR = 1
MAX_REPEATS = 20
MAX_NAME = 100
MAX_DESCRIPTION = 1000
HR_MIN, HR_MAX = 30, 240
WARMUP_SECONDS = 600
COOLDOWN_SECONDS = 300
STRUCTURED_MIN_MINUTES = 30
MIN_CLIMB_NOTE_M = 50

NON_RUN_TYPES = frozenset({"strength", "muscular endurance", "cross-training", "cross training", "mobility", "yoga"})
REST_TYPES = frozenset({"", "rest", "off", "rest day"})
UNIT_TARGET = {
    "s": (TARGET_TIME, 1),
    "min": (TARGET_TIME, 60),
    "m": (TARGET_DISTANCE, 1),
    "km": (TARGET_DISTANCE, 1000),
}
EASY = {"intensityType": INTENSITY_HR, "sectionIntensity": 1}

_TEXT = {
    "en": {
        "rest_name": "Rest",
        "rest_desc": "Recovery day. No structured training.",
        "hr": "Keep heart rate {lo}–{hi} bpm.",
        "climb": "About {m} m of climbing.",
    },
    "vi": {
        "rest_name": "Nghỉ",
        "rest_desc": "Ngày hồi phục. Không có buổi tập.",
        "hr": "Giữ nhịp tim {lo}–{hi} bpm.",
        "climb": "Khoảng {m} m leo dốc.",
    },
}

_RANGE = re.compile(r"(\d{2,3})\s*[-–]\s*(\d{2,3})")
_BELOW = re.compile(r"<\s*(\d{2,3})")
_ABOVE = re.compile(r">\s*(\d{2,3})")
_SINGLE = re.compile(r"(\d{2,3})")
_ZONE = re.compile(r"([1-5])")


def _t(lang: str) -> dict[str, str]:
    return _TEXT.get(lang, _TEXT["en"])


def _int(value: Any) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return 0


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def workout_kind(w: dict[str, Any]) -> Literal["run", "other", "rest"]:
    t = str(w.get("type") or "").strip().lower()
    if t in REST_TYPES:
        return "rest"
    if t in NON_RUN_TYPES:
        return "other"
    return "run"


def _clamp_hr(v: int) -> int:
    return max(HR_MIN, min(HR_MAX, v))


def parse_hr_range(text: str | None) -> tuple[int, int] | None:
    """'120-135 bpm' -> (120, 135); '< 115' -> (100, 115); '> 160' -> (160, 170); '145' -> (145, 145)."""
    if not text:
        return None
    s = str(text)
    if m := _RANGE.search(s):
        lo, hi = sorted((int(m[1]), int(m[2])))
    elif m := _BELOW.search(s):
        hi = int(m[1])
        lo = hi - 15
    elif m := _ABOVE.search(s):
        lo = int(m[1])
        hi = lo + 10
    elif m := _SINGLE.search(s):
        lo = hi = int(m[1])
    else:
        return None
    return _clamp_hr(lo), _clamp_hr(hi)


def _main_intensity(w: dict[str, Any]) -> dict[str, int]:
    hr = parse_hr_range(w.get("target_hr_range"))
    if hr:
        return {"intensityType": INTENSITY_HR, "intensityValueStart": hr[0], "intensityValueEnd": hr[1]}
    m = _ZONE.search(str(w.get("target_zone") or ""))
    if m:
        return {"intensityType": INTENSITY_HR, "sectionIntensity": int(m[1])}
    return {}


def _section(section_type: int, target_type: int, value: int, intensity: dict[str, int]) -> dict[str, Any]:
    return {"sectionType": section_type, "targetType": target_type, "targetValue": int(value), **intensity}


def course_name(w: dict[str, Any]) -> str:
    name = str(w.get("title") or "").strip() or str(w.get("type") or "").strip() or "Run"
    return name[:MAX_NAME]


def _description(w: dict[str, Any], lang: str) -> str:
    t = _t(lang)
    parts = []
    desc = str(w.get("description") or "").strip()
    if desc:
        parts.append(desc)
    hr = parse_hr_range(w.get("target_hr_range"))
    if hr:
        parts.append(t["hr"].format(lo=hr[0], hi=hr[1]))
    climb = _float(w.get("elevation_gain_m"))
    if climb >= MIN_CLIMB_NOTE_M:
        parts.append(t["climb"].format(m=int(round(climb))))
    tip = str(w.get("fueling_tip") or "").strip()
    if tip:
        parts.append(tip)
    return ("\n\n".join(parts) or course_name(w))[:MAX_DESCRIPTION]


def _interval_group(w: dict[str, Any], main: dict[str, int]) -> dict[str, Any] | None:
    reps = _int(w.get("interval_reps"))
    value = _float(w.get("interval_rep_value"))
    unit = w.get("interval_rep_unit")
    if reps <= 0 or value <= 0 or unit not in UNIT_TARGET:
        return None
    target_type, mult = UNIT_TARGET[unit]
    work = max(1, int(round(value * mult)))
    walk = _float(w.get("walk_interval_value"))
    recovery = max(1, int(round(walk * mult))) if walk > 0 else max(1, work // 2)
    return {
        "intervalGroup": True,
        "repeats": min(reps, MAX_REPEATS),
        "sets": [
            _section(SECTION_TRAINING, target_type, work, main),
            _section(SECTION_RECOVERY, target_type, recovery, EASY),
        ],
    }


def build_course(w: dict[str, Any], lang: str) -> dict[str, Any] | None:
    if workout_kind(w) != "run":
        return None
    minutes = _int(w.get("duration_minutes"))
    if minutes <= 0:
        return None
    total = minutes * 60
    main = _main_intensity(w)
    group = _interval_group(w, main)
    if group is not None:
        if str(w.get("type") or "").strip().lower() == "walk/run":
            sections = [group]
        else:
            work, rec = group["sets"]
            cooldown = COOLDOWN_SECONDS
            if work["targetType"] == TARGET_TIME:
                used = WARMUP_SECONDS + group["repeats"] * (work["targetValue"] + rec["targetValue"])
                cooldown = max(COOLDOWN_SECONDS, total - used)
            sections = [
                _section(SECTION_WARMUP, TARGET_TIME, WARMUP_SECONDS, EASY),
                group,
                _section(SECTION_COOLDOWN, TARGET_TIME, cooldown, EASY),
            ]
    elif minutes >= STRUCTURED_MIN_MINUTES:
        sections = [
            _section(SECTION_WARMUP, TARGET_TIME, WARMUP_SECONDS, EASY),
            _section(SECTION_TRAINING, TARGET_TIME, total - WARMUP_SECONDS - COOLDOWN_SECONDS, main),
            _section(SECTION_COOLDOWN, TARGET_TIME, COOLDOWN_SECONDS, EASY),
        ]
    else:
        sections = [_section(SECTION_TRAINING, TARGET_TIME, total, main)]
    return {
        "sportType": SPORT_RUNNING,
        "courseName": course_name(w),
        "courseDescription": _description(w, lang),
        "sections": sections,
    }


def rest_course(lang: str) -> dict[str, Any]:
    t = _t(lang)
    return {"sportType": SPORT_REST, "courseName": t["rest_name"], "courseDescription": t["rest_desc"], "sections": []}


def placeholder_course(w: dict[str, Any], lang: str) -> dict[str, Any]:
    """A non-run session (strength, gym ME) shown on COROS as a rest day carrying its name and notes."""
    name = course_name(w)
    desc = str(w.get("description") or "").strip() or name
    return {"sportType": SPORT_REST, "courseName": name, "courseDescription": desc[:MAX_DESCRIPTION], "sections": []}


def build_day(rows: list[dict[str, Any]], lang: str) -> tuple[list[dict[str, Any]], int]:
    """Courses for one day, plus how many sessions stay in Uphill only.

    Pending coach-review workouts are never pushed. Runs win the day; a
    strength-only day becomes one placeholder; anything else is rest.
    """
    pushable = [r for r in rows if r.get("approved_at") is not None]
    ordered = sorted(
        pushable, key=lambda r: (0 if (r.get("session_slot") or "main") == "main" else 1, r.get("id") or 0)
    )
    runs = [c for c in (build_course(r, lang) for r in ordered) if c]
    others = [r for r in ordered if workout_kind(r) == "other"]
    if runs:
        return runs, len(others)
    if others:
        return [placeholder_course(others[0], lang)], len(others) - 1
    return [rest_course(lang)], 0


_FORMAT_KEYS = ("sectionIntensity", "intensityPercentStart", "intensityValueStart")


def _section_errors(s: dict[str, Any]) -> list[str]:
    errs = []
    if s.get("sectionType") not in (1, 2, 3, 4):
        errs.append("section_type")
    if s.get("targetType") not in (TARGET_DISTANCE, TARGET_TIME):
        errs.append("target_type")
    value = s.get("targetValue")
    if not isinstance(value, int) or value <= 0:
        errs.append("target_value")
    formats = sum(1 for k in _FORMAT_KEYS if k in s)
    if "intensityType" in s:
        if formats != 1:
            errs.append("intensity_format")
        if "intensityValueStart" in s and not (
            HR_MIN <= s["intensityValueStart"] <= HR_MAX and HR_MIN <= s.get("intensityValueEnd", 0) <= HR_MAX
        ):
            errs.append("hr_bounds")
    elif formats:
        errs.append("intensity_without_type")
    return errs


def validate_course(course: dict[str, Any]) -> list[str]:
    """Local mirror of COROS's course rules; a non-empty result means don't send it."""
    errs = []
    name = course.get("courseName") or ""
    if not name or len(name) > MAX_NAME:
        errs.append("name")
    if not course.get("courseDescription"):
        errs.append("description")
    sections = course.get("sections")
    if course.get("sportType") == SPORT_REST:
        if sections:
            errs.append("rest_sections")
        return errs
    if course.get("sportType") != SPORT_RUNNING:
        errs.append("sport")
    if not sections:
        errs.append("empty_sections")
    for s in sections or []:
        if s.get("intervalGroup"):
            if not 1 <= int(s.get("repeats") or 0) <= MAX_REPEATS:
                errs.append("repeats")
            members = s.get("sets") or []
            if not members:
                errs.append("empty_group")
            for m in members:
                if m.get("intervalGroup"):
                    errs.append("nested_group")
                elif m.get("sectionType") not in (SECTION_TRAINING, SECTION_RECOVERY):
                    errs.append("member_type")
                else:
                    errs.extend(_section_errors(m))
        else:
            errs.extend(_section_errors(s))
    return errs
