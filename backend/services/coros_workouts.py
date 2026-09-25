"""Pure mapping from Uphill workout rows to COROS MCP course JSON (COROS push, phase 1).

No I/O. Rules mirror the COROS MCP createTrainingPlan / updateTrainingPlan course
schema: integer seconds/meters, one intensity format per plain section, interval
groups with 1-20 repeats and no nesting, names <= 100 chars, and every name and
description is shown to the athlete verbatim, so no internal labels.

Guidance is heart rate (spec Q4): the workout's own target_hr_range in bpm, else
the COROS HR zone matching target_zone. Runs go out as sportType 1 (running):
the plan is time-based and COROS trail running forbids time targets.

Structure comes from the description's Process chain ("Warm up 15 min ... in
Zone 2 -> 10 min tempo ... in Zone 3 -> ..."), which the generator guarantees
sums to duration_minutes. Each step gets its own zone's heart rate; repeated
effort/recovery pairs become an interval group. When the chain can't be read,
a quality session goes out with no heart-rate target rather than holding the
whole session at its effort zone.
"""

import re
from dataclasses import dataclass
from typing import Any, Literal

SPORT_RUNNING = 1
SPORT_REST = 4
SECTION_WARMUP, SECTION_TRAINING, SECTION_RECOVERY, SECTION_COOLDOWN = 1, 2, 3, 4
TARGET_DISTANCE, TARGET_TIME, TARGET_FREE = 1, 2, 4
INTENSITY_HR = 1
MAX_REPEATS = 20
MAX_NAME = 100
MAX_DESCRIPTION = 1000
HR_MIN, HR_MAX = 30, 240
WARMUP_SECONDS = 600
COOLDOWN_SECONDS = 300
STRUCTURED_MIN_MINUTES = 30
MIN_CLIMB_NOTE_M = 50

PROCESS_TOLERANCE_MINUTES = 1

NON_RUN_TYPES = frozenset({"strength", "muscular endurance", "cross-training", "cross training", "mobility", "yoga"})
# Sessions where one effort zone over the whole run would be wrong (and hard).
QUALITY_MARKERS = ("tempo", "interval", "threshold", "hill", "fartlek", "vo2", "speed", "surge", "race pace")
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
        "race_name": "Race day: {race}",
        "race_desc": "Race day. Uphill AI adds your race-day plan here once it's generated.",
    },
    "vi": {
        "rest_name": "Nghỉ",
        "rest_desc": "Ngày hồi phục. Không có buổi tập.",
        "hr": "Giữ nhịp tim {lo}–{hi} bpm.",
        "climb": "Khoảng {m} m leo dốc.",
        "race_name": "Ngày đua: {race}",
        "race_desc": "Ngày đua. Uphill AI sẽ thêm plan cho ngày đua vào đây khi đã tạo xong.",
    },
}

_RANGE = re.compile(r"(\d{2,3})\s*[-–]\s*(\d{2,3})")
_BELOW = re.compile(r"<\s*(\d{2,3})")
_ABOVE = re.compile(r">\s*(\d{2,3})")
_SINGLE = re.compile(r"(\d{2,3})")
_ZONE = re.compile(r"([1-5])")
_PROCESS = re.compile(r"Process\s*[:\-]\s*(.*?)(?=\b(?:Overall|Reason|Benefit|Warning)\s*[:\-]|$)", re.I | re.S)
_STEP_SPLIT = re.compile(r"\s*(?:→|->)\s*")
_STEP_MINUTES = re.compile(r"(\d+(?:\.\d+)?)\s*(?:min|mins|minutes)\b", re.I)
_STEP_SECONDS = re.compile(r"(\d+)\s*(?:s|sec|secs|seconds)\b", re.I)
_STEP_ZONE = re.compile(r"\bZone\s*([1-5])\b", re.I)
_WARM = re.compile(r"\bwarm", re.I)
_COOL = re.compile(r"\bcool", re.I)
_EASY_STEP = re.compile(r"recover|jog|walk|rest|easy", re.I)


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
    return clip_text("\n\n".join(parts) or course_name(w))


def clip_text(text: str, limit: int = MAX_DESCRIPTION) -> str:
    """Fit COROS's description limit, cutting at a word boundary with an ellipsis."""
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,.;:-–—") + "…"


@dataclass(frozen=True)
class ProcessStep:
    minutes: float
    zone: int | None
    role: Literal["warmup", "training", "recovery", "cooldown"]


def parse_process_steps(description: str | None) -> list[ProcessStep] | None:
    """The description's Process chain as timed steps, or None when it has no
    Process section or any step lacks a duration."""
    m = _PROCESS.search(description or "")
    if not m:
        return None
    raw = [s.strip(" .") for s in _STEP_SPLIT.split(m[1].strip()) if s.strip(" .")]
    if len(raw) < 2:
        return None
    parsed: list[tuple[str, float, int | None]] = []
    for text in raw:
        mins = _STEP_MINUTES.search(text)
        secs = _STEP_SECONDS.search(text)
        if mins:
            minutes = float(mins[1])
        elif secs:
            minutes = int(secs[1]) / 60
        else:
            return None
        zone = _STEP_ZONE.search(text)
        parsed.append((text, minutes, int(zone[1]) if zone else None))
    middle_zones = [z for _, _, z in parsed[1:-1] if z is not None]
    hardest = max(middle_zones) if middle_zones else None
    steps = []
    for i, (text, minutes, zone) in enumerate(parsed):
        if i == 0 and _WARM.search(text):
            role = "warmup"
        elif i == len(parsed) - 1 and _COOL.search(text):
            role = "cooldown"
        elif _EASY_STEP.search(text) and zone is not None and hardest is not None and zone < hardest:
            role = "recovery"
        else:
            role = "training"
        steps.append(ProcessStep(minutes, zone, role))
    return steps


_ROLE_SECTION = {
    "warmup": SECTION_WARMUP,
    "training": SECTION_TRAINING,
    "recovery": SECTION_RECOVERY,
    "cooldown": SECTION_COOLDOWN,
}


def _zone_number(text: Any) -> int | None:
    m = _ZONE.search(str(text or ""))
    return int(m[1]) if m else None


def _step_intensity(
    step: ProcessStep, main_zone: int | None, main: dict[str, int], hr_zones: dict[str, dict[str, int]] | None
) -> dict[str, int]:
    """The workout's own range for steps in its zone; the athlete's zone table
    (in bpm) for the rest; COROS's zone number when no table is available."""
    if step.zone is None:
        return main if step.role == "training" else EASY
    if step.zone == main_zone and main:
        return main
    band = (hr_zones or {}).get(f"Zone {step.zone}")
    if band:
        return {
            "intensityType": INTENSITY_HR,
            "intensityValueStart": _clamp_hr(int(band["min"])),
            "intensityValueEnd": _clamp_hr(int(band["max"])),
        }
    return {"intensityType": INTENSITY_HR, "sectionIntensity": step.zone}


def _process_sections(
    w: dict[str, Any], main: dict[str, int], hr_zones: dict[str, dict[str, int]] | None
) -> list[dict[str, Any]] | None:
    """Sections from the Process chain; None unless its minutes add up to the workout."""
    steps = parse_process_steps(w.get("description"))
    if not steps:
        return None
    if abs(sum(s.minutes for s in steps) - _float(w.get("duration_minutes"))) > PROCESS_TOLERANCE_MINUTES:
        return None
    main_zone = _zone_number(w.get("target_zone"))
    if main_zone is None:
        main_zone = max((s.zone for s in steps if s.role == "training" and s.zone), default=None)
    plain = [
        _section(
            _ROLE_SECTION[s.role],
            TARGET_TIME,
            max(1, round(s.minutes * 60)),
            _step_intensity(s, main_zone, main, hr_zones),
        )
        for s in steps
    ]
    return _group_repeats(plain)


def _group_repeats(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Consecutive identical (effort, recovery) pairs -> one interval group."""
    out: list[dict[str, Any]] = []
    i = 0
    while i < len(sections):
        pair = sections[i : i + 2]
        is_pair = len(pair) == 2 and [s["sectionType"] for s in pair] == [SECTION_TRAINING, SECTION_RECOVERY]
        reps = 1
        while is_pair and sections[i + 2 * reps : i + 2 * reps + 2] == pair:
            reps += 1
        if is_pair and reps >= 2:
            out.append({"intervalGroup": True, "repeats": min(reps, MAX_REPEATS), "sets": pair})
            i += 2 * reps
        else:
            out.append(sections[i])
            i += 1
    return out


def is_quality(w: dict[str, Any]) -> bool:
    t = f"{w.get('type') or ''} {w.get('title') or ''}".lower()
    return any(marker in t for marker in QUALITY_MARKERS)


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


def race_day_course(race_name: str | None, distance_km: Any, lang: str) -> dict[str, Any]:
    """Race-day placeholder until Uphill generates the real race-day workout: the
    race distance as a distance target (free mode when unknown) and deliberately
    no heart-rate target -- a placeholder shouldn't guess race effort."""
    t = _t(lang)
    meters = int(round(_float(distance_km) * 1000))
    section: dict[str, Any] = {"sectionType": SECTION_TRAINING, "targetType": TARGET_FREE}
    if meters > 0:
        section = _section(SECTION_TRAINING, TARGET_DISTANCE, meters, {})
    return {
        "sportType": SPORT_RUNNING,
        "courseName": t["race_name"].format(race=race_name or "Race")[:MAX_NAME],
        "courseDescription": t["race_desc"],
        "sections": [section],
    }


def build_course(
    w: dict[str, Any], lang: str, hr_zones: dict[str, dict[str, int]] | None = None
) -> dict[str, Any] | None:
    if w.get("race_placeholder"):
        return race_day_course(w.get("race_name"), w.get("course_distance_km"), lang)
    if workout_kind(w) != "run":
        return None
    minutes = _int(w.get("duration_minutes"))
    if minutes <= 0:
        return None
    main = _main_intensity(w)
    return {
        "sportType": SPORT_RUNNING,
        "courseName": course_name(w),
        "courseDescription": _description(w, lang),
        "sections": _process_sections(w, main, hr_zones) or _fallback_sections(w, main, minutes),
    }


def _fallback_sections(w: dict[str, Any], main: dict[str, int], minutes: int) -> list[dict[str, Any]]:
    """Shapes for a workout whose Process chain can't be read."""
    total = minutes * 60
    group = _interval_group(w, main)
    if group is not None:
        if str(w.get("type") or "").strip().lower() == "walk/run":
            return [group]
        work, rec = group["sets"]
        cooldown = COOLDOWN_SECONDS
        if work["targetType"] == TARGET_TIME:
            used = WARMUP_SECONDS + group["repeats"] * (work["targetValue"] + rec["targetValue"])
            cooldown = max(COOLDOWN_SECONDS, total - used)
        return [
            _section(SECTION_WARMUP, TARGET_TIME, WARMUP_SECONDS, EASY),
            group,
            _section(SECTION_COOLDOWN, TARGET_TIME, cooldown, EASY),
        ]
    if is_quality(w):
        # Structure unknown: one timed block with no heart-rate target (the
        # description says what to do) beats a whole session at effort HR.
        return [_section(SECTION_TRAINING, TARGET_TIME, total, {})]
    if minutes >= STRUCTURED_MIN_MINUTES:
        return [
            _section(SECTION_WARMUP, TARGET_TIME, WARMUP_SECONDS, EASY),
            _section(SECTION_TRAINING, TARGET_TIME, total - WARMUP_SECONDS - COOLDOWN_SECONDS, main),
            _section(SECTION_COOLDOWN, TARGET_TIME, COOLDOWN_SECONDS, EASY),
        ]
    return [_section(SECTION_TRAINING, TARGET_TIME, total, main)]


def rest_course(lang: str) -> dict[str, Any]:
    t = _t(lang)
    return {"sportType": SPORT_REST, "courseName": t["rest_name"], "courseDescription": t["rest_desc"], "sections": []}


def placeholder_course(w: dict[str, Any], lang: str) -> dict[str, Any]:
    """A non-run session (strength, gym ME) shown on COROS as a rest day carrying its name and notes."""
    name = course_name(w)
    desc = str(w.get("description") or "").strip() or name
    return {"sportType": SPORT_REST, "courseName": name, "courseDescription": clip_text(desc), "sections": []}


def build_day(
    rows: list[dict[str, Any]], lang: str, hr_zones: dict[str, dict[str, int]] | None = None
) -> tuple[list[dict[str, Any]], int]:
    """Courses for one day, plus how many sessions stay in Uphill only.

    Pending coach-review workouts are never pushed. Runs win the day; a
    strength-only day becomes one placeholder; anything else is rest.
    """
    pushable = [r for r in rows if r.get("approved_at") is not None]
    ordered = sorted(
        pushable, key=lambda r: (0 if (r.get("session_slot") or "main") == "main" else 1, r.get("id") or 0)
    )
    runs = [c for c in (build_course(r, lang, hr_zones) for r in ordered) if c]
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
    value = s.get("targetValue")
    if s.get("targetType") == TARGET_FREE:
        if value not in (None, 0):
            errs.append("target_value")
    elif s.get("targetType") not in (TARGET_DISTANCE, TARGET_TIME):
        errs.append("target_type")
    elif not isinstance(value, int) or value <= 0:
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
