from datetime import datetime, timedelta
from typing import Any

from log_utils import get_logger
from services.athlete_tier import get_profile, resolve_tier
from services.plan_rules import build_rules_block
from services.training_rules import TrainingRules, default_zone2_pace, resolve_zone2_pace

_logger = get_logger(__name__)


class PlanGenerator:
    @staticmethod
    def parse_pace_to_decimal(pace_str: str) -> float:
        """Converts a pace string 'MM:SS' or decimal 'MM.SS' to decimal minutes."""
        if not pace_str:
            return 6.0
        try:
            pace_str = str(pace_str).strip()
            if ":" in pace_str:
                parts = pace_str.split(":")
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes + (seconds / 60.0)
            else:
                return float(pace_str)
        except Exception:
            return 6.0

    @staticmethod
    def decimal_to_pace_str(decimal_mins: float) -> str:
        """Converts decimal minutes to a pace string 'MM:SS'."""
        mins = int(decimal_mins)
        secs = int(round((decimal_mins - mins) * 60))
        if secs >= 60:
            mins += 1
            secs -= 60
        return f"{mins}:{secs:02d}"

    @staticmethod
    def calculate_pace_zones_from_threshold(
        threshold_pace_str: str,
        model: str = "5_zone",
    ) -> dict[str, Any]:
        """
        Calculates pace zones directly from a Threshold Pace (T-Pace / Zone 4).
        threshold_pace_str can be formatted as '4:34', '4:34 /km', or decimal minutes.

        5-Zone Model (Standard / COROS):
          - Zone 1 (Recovery): > T-Pace * 1.25
          - Zone 2 (Aerobic / Easy): T-Pace * 1.15 to 1.25
          - Zone 3 (Tempo): T-Pace * 1.05 to 1.15
          - Zone 4 (Threshold): T-Pace * 0.98 to 1.05
          - Zone 5 (Interval / VO2max): < T-Pace * 0.98

        4-Zone Model (Scott Johnston & Steve House - Training for the Uphill Athlete):
          - Zone 1 (Recovery): Below Aerobic Threshold (AeT) pace (> T-Pace * 1.22)
          - Zone 2 (Aerobic Capacity): AeT to AnT transition (T-Pace * 1.05 to 1.22)
          - Zone 3 (Threshold): Around Anaerobic Threshold (AnT) (T-Pace * 0.98 to 1.05)
          - Zone 4 (Max / Anaerobic): Above AnT (< T-Pace * 0.98)
        """
        clean_pace = threshold_pace_str.split("/")[0].strip()
        t_pace_dec = PlanGenerator.parse_pace_to_decimal(clean_pace)

        def _fmt(slow_d: float, fast_d: float) -> str:
            return f"{PlanGenerator.decimal_to_pace_str(slow_d)} - {PlanGenerator.decimal_to_pace_str(fast_d)}"

        if model == "4_zone":
            z4_fast = t_pace_dec * 0.88
            z4_slow = t_pace_dec * 0.98
            z3_fast = z4_slow
            z3_slow = t_pace_dec * 1.05
            z2_fast = z3_slow
            z2_slow = t_pace_dec * 1.22
            z1_fast = z2_slow
            z1_slow = t_pace_dec * 1.40

            return {
                "model": "4_zone",
                "threshold_pace": clean_pace,
                "zone1_pace": _fmt(z1_slow, z1_fast),
                "zone1_pace_mid": PlanGenerator.decimal_to_pace_str((z1_slow + z1_fast) / 2.0),
                "zone2_pace": _fmt(z2_slow, z2_fast),
                "zone2_pace_mid": PlanGenerator.decimal_to_pace_str((z2_slow + z2_fast) / 2.0),
                "zone3_pace": _fmt(z3_slow, z3_fast),
                "zone3_pace_mid": PlanGenerator.decimal_to_pace_str((z3_slow + z3_fast) / 2.0),
                "zone4_pace": _fmt(z4_slow, z4_fast),
                "zone4_pace_mid": PlanGenerator.decimal_to_pace_str((z4_slow + z4_fast) / 2.0),
                "zone_labels": {
                    "Zone 1": "Recovery (< AeT)",
                    "Zone 2": "Aerobic Capacity (AeT - AnT)",
                    "Zone 3": "Anaerobic Threshold (AnT)",
                    "Zone 4": "Max / Anaerobic (> AnT)",
                },
            }
        else:
            # 5-zone
            z5_fast = t_pace_dec * 0.88
            z5_slow = t_pace_dec * 0.98
            z4_fast = z5_slow
            z4_slow = t_pace_dec * 1.05
            z3_fast = z4_slow
            z3_slow = t_pace_dec * 1.15
            z2_fast = z3_slow
            z2_slow = t_pace_dec * 1.25
            z1_fast = z2_slow
            z1_slow = t_pace_dec * 1.40

            return {
                "model": "5_zone",
                "threshold_pace": clean_pace,
                "zone1_pace": _fmt(z1_slow, z1_fast),
                "zone1_pace_mid": PlanGenerator.decimal_to_pace_str((z1_slow + z1_fast) / 2.0),
                "zone2_pace": _fmt(z2_slow, z2_fast),
                "zone2_pace_mid": PlanGenerator.decimal_to_pace_str((z2_slow + z2_fast) / 2.0),
                "zone3_pace": _fmt(z3_slow, z3_fast),
                "zone3_pace_mid": PlanGenerator.decimal_to_pace_str((z3_slow + z3_fast) / 2.0),
                "zone4_pace": _fmt(z4_slow, z4_fast),
                "zone4_pace_mid": PlanGenerator.decimal_to_pace_str((z4_slow + z4_fast) / 2.0),
                "zone5_pace": _fmt(z5_slow, z5_fast),
                "zone5_pace_mid": PlanGenerator.decimal_to_pace_str((z5_slow + z5_fast) / 2.0),
                "zone_labels": {
                    "Zone 1": "Recovery",
                    "Zone 2": "Aerobic / Easy",
                    "Zone 3": "Tempo",
                    "Zone 4": "Threshold",
                    "Zone 5": "Interval / VO2max",
                },
            }

    @staticmethod
    def resolve_pace_zones(
        user_profile: dict[str, Any],
        goal_type: str | None = None,
        athlete_tier: str | None = None,
    ) -> dict[str, Any]:
        """An athlete's pace zones, resolved the SAME way everywhere.

        Precedence, strongest evidence first:
          1. A measured threshold pace, which produces zones anchored on a real test
             rather than chained outward from an estimate.
          2. Zone 2 bounds -- the athlete's own if stored, otherwise the tier default.

        This exists because the plan generator used to call estimate_pace_zones with
        only the Zone 2 bounds, silently dropping `threshold_pace` and `pace_zone_model`
        even though the function accepts both and GET /api/auth/pace-zones passes them.
        An athlete with a measured threshold therefore saw one set of zones in the app
        while their PLAN was built on a different, estimated set -- and every workout's
        target pace, distance_km and treadmill speed came from the plan's set.

        `custom_pace_zones` is deliberately NOT consulted here: that payload is shaped
        for display and is not guaranteed to carry the `*_pace_mid` values the distance
        maths needs. Honouring it needs a shape migration, not a lookup.
        """
        z2_min, z2_max = resolve_zone2_pace(
            user_profile.get("zone2_pace_min"),
            user_profile.get("zone2_pace_max"),
            goal_type,
            athlete_tier=athlete_tier,
        )
        return PlanGenerator.estimate_pace_zones(
            z2_min,
            z2_max,
            user_profile.get("aet_hr"),
            user_profile.get("ant_hr"),
            threshold_pace=user_profile.get("threshold_pace"),
            model=user_profile.get("pace_zone_model") or "5_zone",
        )

    @staticmethod
    def estimate_pace_zones(
        zone2_min_str: str | None = None,
        zone2_max_str: str | None = None,
        aet_hr: float | None = None,
        ant_hr: float | None = None,
        threshold_pace: str | None = None,
        model: str = "5_zone",
    ) -> dict[str, Any]:
        """
        Estimates pace zones. If threshold_pace is provided, uses calculate_pace_zones_from_threshold.
        Otherwise, estimates all 5 pace zones as contiguous, non-overlapping ranges,
        chained outward from the athlete's Zone 2 bounds.
        """
        if threshold_pace:
            return PlanGenerator.calculate_pace_zones_from_threshold(threshold_pace, model=model)

        # Last-resort guard only: every caller resolves the athlete's zones through
        # training_rules.resolve_zone2_pace first, which is where the tier default is
        # applied. This branch means a caller passed nothing at all -- fall back to the
        # general tier rather than crash, but it should not normally be reachable.
        _fallback_min, _fallback_max = default_zone2_pace()
        z2_min = PlanGenerator.parse_pace_to_decimal(zone2_min_str or _fallback_min)
        z2_max = PlanGenerator.parse_pace_to_decimal(zone2_max_str or _fallback_max)

        reference_gap = 1.15
        if aet_hr and ant_hr and aet_hr > 0:
            scale = (ant_hr / aet_hr) / reference_gap
        else:
            scale = 1.0
        scale = max(0.7, min(1.4, scale))

        # Baseline deviations from Zone 2 (unchanged from the original
        # single-point ratios: Z1=1.15x, Z3=0.90x, Z4=0.82x, Z5=0.73x).
        ratio_1 = 1.0 + 0.15 * scale
        ratio_3 = 1.0 - 0.10 * scale
        ratio_4 = 1.0 - 0.18 * scale
        ratio_5 = 1.0 - 0.27 * scale

        b0 = z2_min * ratio_1  # Zone 1's slow (outer) bound
        b3 = z2_max * ratio_3  # Zone 3/4 boundary
        b4 = z2_max * ratio_4  # Zone 4/5 boundary
        b5 = z2_max * ratio_5  # Zone 5's fast (outer) bound

        def _range_and_mid(slow_dec: float, fast_dec: float) -> tuple[str, str]:
            range_str = (
                f"{PlanGenerator.decimal_to_pace_str(slow_dec)} - " f"{PlanGenerator.decimal_to_pace_str(fast_dec)}"
            )
            mid_str = PlanGenerator.decimal_to_pace_str((slow_dec + fast_dec) / 2.0)
            return range_str, mid_str

        z1_range, z1_mid = _range_and_mid(b0, z2_min)
        z3_range, z3_mid = _range_and_mid(z2_max, b3)
        z4_range, z4_mid = _range_and_mid(b3, b4)
        z5_range, z5_mid = _range_and_mid(b4, b5)
        z2_mid_dec = (z2_min + z2_max) / 2.0

        return {
            "zone1_pace": z1_range,
            "zone1_pace_mid": z1_mid,
            # Same fallback as the numeric branch above -- these were separate literals,
            # so a missing bound produced a DISPLAY range of 6:30-5:45 while the distance
            # maths used the tier default. The athlete saw one pace and got another.
            "zone2_pace": f"{zone2_min_str or _fallback_min} - {zone2_max_str or _fallback_max}",
            "zone2_pace_mid": PlanGenerator.decimal_to_pace_str(z2_mid_dec),
            "zone3_pace": z3_range,
            "zone3_pace_mid": z3_mid,
            "zone4_pace": z4_range,
            "zone4_pace_mid": z4_mid,
            "zone5_pace": z5_range,
            "zone5_pace_mid": z5_mid,
        }

    @staticmethod
    def _warmup_cooldown_minutes(total_minutes: float) -> tuple[int, int]:
        """Proportional warm-up/cool-down minutes (20% of total each, clamped
        to 3-10 min) for a rule-based fallback session description. Used so
        the stated Process minutes always sum to the day's actual
        duration_minutes instead of a fixed value that ignores it."""
        wc = min(10, max(3, round(round(total_minutes) * 0.2)))
        return wc, wc

    @staticmethod
    def pace_and_distance_for_zone(zone: str, duration_minutes: float, est_zones: dict[str, str]) -> tuple[str, float]:
        """Maps a target_zone label to its display pace range and computed distance_km."""
        zone_lower = (zone or "").lower()
        if "zone 1" in zone_lower:
            pace_str, mid_key = est_zones["zone1_pace"], "zone1_pace_mid"
        elif "zone 3" in zone_lower:
            pace_str, mid_key = est_zones["zone3_pace"], "zone3_pace_mid"
        elif "zone 4" in zone_lower:
            pace_str, mid_key = est_zones["zone4_pace"], "zone4_pace_mid"
        elif "zone 5" in zone_lower:
            pace_str, mid_key = est_zones["zone5_pace"], "zone5_pace_mid"
        else:  # Zone 2 default
            pace_str, mid_key = est_zones["zone2_pace"], "zone2_pace_mid"

        pace_dec = PlanGenerator.parse_pace_to_decimal(est_zones[mid_key])
        distance_km = round(duration_minutes / pace_dec, 1) if pace_dec > 0 else 0.0
        return f"{pace_str} /km", distance_km

    ELEVATION_ELIGIBLE_TYPES = ("Easy", "Tempo", "Interval", "Long Run")

    @staticmethod
    def resolve_elevation_and_grade(
        wo: dict[str, Any],
        w_type: str,
        terrain: str,
        distance_km: float,
        course_elevation_gain_m: float | None,
        course_distance_km: float | None,
    ) -> tuple[float, float]:
        """Resolves (elevation_gain_m, grade_percent) for a single workout.

        Elevation and grade resolve independently and in order: elevation
        first (AI-supplied value if present and numeric, else a course-
        proportional formula, else 0.0), then grade (AI-supplied value if
        present and numeric, else derived from the now-resolved elevation
        and distance_km, else 0.0). Grade's fallback deliberately never reads
        course_elevation_gain_m directly, so an AI-supplied elevation_gain_m
        with no AI-supplied grade_percent still gets a grade consistent with
        that specific elevation value, not the race's average.

        Only applies to Easy/Tempo/Interval/Long Run on trail terrain; every
        other type or terrain always returns (0.0, 0.0).
        """
        if w_type not in PlanGenerator.ELEVATION_ELIGIBLE_TYPES or terrain != "trail":
            return 0.0, 0.0

        def _as_float(value: Any) -> float | None:
            try:
                return float(value) if value is not None else None
            except (TypeError, ValueError):
                return None

        elevation_gain_m = _as_float(wo.get("elevation_gain_m"))
        if elevation_gain_m is None:
            if course_elevation_gain_m and course_distance_km and float(course_distance_km) > 0:
                elevation_gain_m = distance_km * (float(course_elevation_gain_m) / float(course_distance_km))
            else:
                elevation_gain_m = 0.0

        grade_percent = _as_float(wo.get("grade_percent"))
        if grade_percent is None:
            if elevation_gain_m and distance_km > 0:
                grade_percent = elevation_gain_m / (distance_km * 10)
            else:
                grade_percent = 0.0

        return round(elevation_gain_m, 1), round(grade_percent, 1)

    INTERVAL_REP_UNITS = ("s", "m", "min", "km")

    @staticmethod
    def resolve_interval_summary(wo: dict[str, Any], w_type: str) -> tuple[int | None, float | None, str | None]:
        """Resolves (interval_reps, interval_rep_value, interval_rep_unit) for a
        single workout — a single primary rep block (e.g. 8 reps x 12 seconds,
        rendered as "8x12s"). Returns (None, None, None) whenever the workout
        isn't a clean single-block Interval: wrong type, a missing field, an
        unparseable/non-positive value, or an unrecognized unit. Callers fall
        back to the existing distance_km display in that case — multi-block or
        pyramid workouts are expected to leave these fields unset and keep
        relying on the free-text description, same as before this field existed.
        """
        # Walk/Run sessions are the whole reason a beginner's plan has rep structure at
        # all. Gating this on "Interval" alone meant their structure was silently dropped
        # and survived only as free text in the description, so the UI could never render
        # "5 x 2 min jog / 1 min walk" as a chip.
        if w_type not in ("Interval", "Walk/Run"):
            return None, None, None

        raw_reps = wo.get("interval_reps")
        raw_value = wo.get("interval_rep_value")
        unit = wo.get("interval_rep_unit")

        try:
            reps = int(raw_reps)
            value = float(raw_value)
        except (TypeError, ValueError):
            return None, None, None

        if reps <= 0 or value <= 0 or unit not in PlanGenerator.INTERVAL_REP_UNITS:
            return None, None, None

        return reps, value, unit

    # Title substrings (case-insensitive) that identify a true hill-sprint/hill-repeat
    # session — short, near-maximal efforts that require a steep grade by design,
    # regardless of the race's average grade or this workout's own grade_percent.
    HILL_SPRINT_TITLE_KEYWORDS = ("hill sprint", "hill repeat", "hill bound")
    HILL_SPRINT_INCLINE_MIN = 10.0
    HILL_SPRINT_INCLINE_MAX = 15.0

    @staticmethod
    def parse_pace_range(pace_str: str | None) -> tuple[float, float] | None:
        """Parses a pace string — single ("6:00 /km") or range ("6:30 - 5:45 /km")
        — into (slower, faster) decimal min/km. Returns None when there's nothing
        parseable."""
        if not pace_str:
            return None
        cleaned = str(pace_str).replace("/km", "").strip()
        parts = [p.strip() for p in cleaned.split("-") if p.strip()]
        if not parts:
            return None
        values = [PlanGenerator.parse_pace_to_decimal(p) for p in parts[:2]]
        if len(values) == 1:
            values.append(values[0])
        return max(values), min(values)

    @staticmethod
    def _format_range(low: float, high: float) -> str:
        """ "8.2-9.2" (or "8.2" when both ends coincide), with trailing .0 trimmed."""

        def fmt(v: float) -> str:
            return f"{round(v, 1):g}"

        low, high = min(low, high), max(low, high)
        return fmt(low) if fmt(low) == fmt(high) else f"{fmt(low)}-{fmt(high)}"

    @staticmethod
    def resolve_treadmill_settings(
        wo: dict[str, Any], target_pace: str | None, use_treadmill: bool = True
    ) -> tuple[str, str]:
        """Deterministic treadmill settings as range strings — the same backstop
        pattern as resolve_elevation_and_grade, applied to EVERY workout instead
        of trusting the AI's numbers (which drifted from the pace range in
        practice). Returns (incline_range, speed_range), e.g. ("7.3-9.3",
        "8.2-9.2"); ("0", "0") when the workout isn't treadmill-relevant.

        - `use_treadmill=False`: always ("0", "0") — the athlete has no
          treadmill, regardless of what the AI emitted, so a workout can never
          carry treadmill settings into the final plan.
        - Hill Sprint/Hill Repeat titles: incline "10-15"; speed derived from the
          workout's own target_pace range at the band midpoint (12.5%).
        - Other workouts the AI marked treadmill-relevant (incline or speed > 0):
          incline is a ±1% band around the resolved grade (AI incline when > 0,
          else this run's own grade_percent, floored at 1%); speed is derived
          from both ends of the target_pace range at the band midpoint, using
          the grade-adjusted effort model in TrainingRules.
        """
        if not use_treadmill:
            return "0", "0"

        def _as_float(value: Any) -> float:
            try:
                return float(value or 0.0)
            except (TypeError, ValueError):
                return 0.0

        ai_incline = _as_float(wo.get("treadmill_incline"))
        ai_speed = _as_float(wo.get("treadmill_speed"))
        title_lower = (wo.get("title") or "").lower()
        is_hill_sprint = any(kw in title_lower for kw in PlanGenerator.HILL_SPRINT_TITLE_KEYWORDS)

        if not is_hill_sprint and ai_incline <= 0 and ai_speed <= 0:
            return "0", "0"  # AI marked this workout as not treadmill-relevant

        if is_hill_sprint:
            incline_low = PlanGenerator.HILL_SPRINT_INCLINE_MIN
            incline_high = PlanGenerator.HILL_SPRINT_INCLINE_MAX
        else:
            grade = ai_incline if ai_incline > 0 else _as_float(wo.get("grade_percent"))
            if grade <= 0:
                grade = 1.0  # standard 1% treadmill rule when nothing else is known
            grade = min(15.0, grade)  # Commercial gym treadmills max out at 15.0%
            incline_low = max(1.0, grade - 1.0)
            incline_high = min(15.0, grade + 1.0)
        incline_mid = (incline_low + incline_high) / 2

        pace_range = PlanGenerator.parse_pace_range(target_pace)
        if pace_range is None:
            # No pace to derive from (shouldn't happen for run types) — keep the
            # AI's speed if it gave one, but never invent our own number.
            speed_str = PlanGenerator._format_range(ai_speed, ai_speed) if ai_speed > 0 else "0"
            return PlanGenerator._format_range(incline_low, incline_high), speed_str

        slow_pace, fast_pace = pace_range
        speed_low = TrainingRules.calculate_treadmill_settings(slow_pace, incline_mid)["speed_kph"]
        speed_high = TrainingRules.calculate_treadmill_settings(fast_pace, incline_mid)["speed_kph"]
        return (
            PlanGenerator._format_range(incline_low, incline_high),
            PlanGenerator._format_range(speed_low, speed_high),
        )

    @staticmethod
    def _wu_cd_minutes(main_minutes: float) -> int:
        """Warm-up/cool-down minutes on each end of a coach-specified MAIN SET
        duration -- proportional to the main set, clamped to a sane range.
        Mirrors the spirit of _warmup_cooldown_minutes but inverted: that one
        derives wu/cd from a known TOTAL; this derives them from a known
        MAIN SET, since the coach's duration input never includes wu/cd."""
        return max(3, min(10, round(main_minutes * 0.15)))

    @staticmethod
    async def generate_single_workout(
        user_profile: dict[str, Any],
        workout_type: str,
        duration_minutes: float,
        day_of_week: str,
        week_number: int,
        intent: str | None = None,
        api_key: str | None = None,
        target_zone: str | None = None,
        target_pace: str | None = None,
        interval_reps: int | None = None,
        interval_rep_value: float | None = None,
        interval_rep_unit: str | None = None,
        details: str | None = None,
    ) -> dict[str, Any]:
        """Coach co-creation: the coach supplies type/duration/day, and
        optionally overrides (zone, pace, interval structure, details/intent)
        -- this fills in whatever's left, grounded in the athlete's own
        profile (same zone/pace math as the full-plan generator, scoped to
        one workout). `duration_minutes` is the MAIN SET only -- warm-up and
        cool-down are added on top, never counted against it, matching how
        coaches think about session length. Falls back to a deterministic,
        un-narrated construction if Gemini is unavailable or fails, so the
        coach always gets a usable workout rather than an error."""
        age = int(user_profile.get("age", 30))
        max_hr = int(user_profile.get("max_hr", 220 - age))
        resting_hr = int(user_profile.get("resting_hr", 60))
        aet_hr = int(user_profile.get("aet_hr", resting_hr + int((max_hr - resting_hr) * 0.65)))
        ant_hr = int(user_profile.get("ant_hr", resting_hr + int((max_hr - resting_hr) * 0.85)))
        hr_zones = TrainingRules.calculate_heart_rate_zones(max_hr, resting_hr, aet_hr, ant_hr)

        est_zones = PlanGenerator.resolve_pace_zones(
            {**user_profile, "aet_hr": aet_hr, "ant_hr": ant_hr}, user_profile.get("goal_type")
        )

        is_rest_or_strength = workout_type in ("Rest", "Strength", "Muscular Endurance")
        is_interval = workout_type == "Interval"
        zone_locked = target_zone is not None  # coach chose a zone -- AI must not override it
        _DEFAULT_ZONE_BY_TYPE = {"Tempo": "Zone 3", "Threshold": "Zone 3", "Interval": "Zone 4"}
        default_zone = "Zone 1" if is_rest_or_strength else _DEFAULT_ZONE_BY_TYPE.get(workout_type, "Zone 2")
        resolved_zone = target_zone or default_zone

        title = workout_type
        description = details
        fueling_tip = None

        if api_key and not is_rest_or_strength and not details:
            try:
                import json as _json

                from google import genai as _genai
                from google.genai import types as _genai_types

                from config import settings

                zone_instruction = (
                    f"Use exactly this zone (the coach already chose it): {resolved_zone}."
                    if zone_locked
                    else "Choose the single most appropriate zone: Zone 1|Zone 2|Zone 3|Zone 4|Zone 5."
                )
                interval_instruction = (
                    f"This is an interval session: {interval_reps}x{interval_rep_value}{interval_rep_unit} "
                    "(already fixed by the coach -- describe the session around this structure, don't invent a different one)."
                    if is_interval and interval_reps
                    else ""
                )
                prompt = f"""You are Coach Uphill, an expert trail-running coach following Scott Johnston's
"Training for the Uphill Athlete" principles. A human coach is manually adding ONE workout to an
athlete's training week and wants you to fill in the remaining detail. Do not invent a whole
week -- just this one session.

Athlete zones: Zone 1 {est_zones["zone1_pace"]} /km, Zone 2 {est_zones["zone2_pace"]} /km,
Zone 3 {est_zones["zone3_pace"]} /km, Zone 4 {est_zones["zone4_pace"]} /km, Zone 5 {est_zones["zone5_pace"]} /km.
AeT {aet_hr} bpm, AnT {ant_hr} bpm, max HR {max_hr} bpm.

Workout type: {workout_type}
Main set duration: {int(duration_minutes)} minutes (warm-up/cool-down are separate, don't fold them into this number)
Day: {day_of_week}, week {week_number}
{zone_instruction}
{interval_instruction}
{f"Coach's intent: {intent}" if intent else ""}

Return ONLY a single JSON object (no markdown fences, no prose) with exactly these keys:
{{"title": "short session title", "target_zone": "Zone 1|Zone 2|Zone 3|Zone 4|Zone 5",
"description": "warm-up, main set (with any intervals), cool-down as one paragraph",
"fueling_tip": "one sentence, or null if not applicable"}}"""

                _client = _genai.Client(api_key=api_key)
                import asyncio

                _response = await asyncio.to_thread(
                    _client.models.generate_content,
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=_genai_types.GenerateContentConfig(
                        thinking_config=_genai_types.ThinkingConfig(thinking_level=settings.GEMINI_THINKING_LEVEL)
                    )
                    if hasattr(_genai_types, "ThinkingConfig")
                    else None,
                )
                _text = _response.text.strip()
                _start, _end = _text.find("{"), _text.rfind("}")
                if _start != -1 and _end != -1:
                    parsed = _json.loads(_text[_start : _end + 1])
                    title = parsed.get("title") or title
                    if not zone_locked:
                        resolved_zone = parsed.get("target_zone") or resolved_zone
                    description = parsed.get("description")
                    fueling_tip = parsed.get("fueling_tip")
            except Exception as ex:
                print(f"[PlanGen][SingleWorkout] Gemini FAILED: {ex}. Using deterministic fallback.")

        computed_pace, distance_km = (
            (None, None)
            if is_rest_or_strength
            else PlanGenerator.pace_and_distance_for_zone(resolved_zone, duration_minutes, est_zones)
        )
        resolved_pace = target_pace or computed_pace
        # A coach-supplied pace overrides the zone's default, but distance is
        # still estimated off it so "est. distance" stays consistent with pace.
        if target_pace and not is_rest_or_strength:
            pace_dec = PlanGenerator.parse_pace_to_decimal(target_pace.split("/")[0].split("-")[0].strip())
            if pace_dec > 0:
                distance_km = round(duration_minutes / pace_dec, 1)

        zone_key = resolved_zone if resolved_zone in hr_zones else "Zone 2"
        hr_range = None if is_rest_or_strength else f"{hr_zones[zone_key]['min']}-{hr_zones[zone_key]['max']} bpm"

        if is_rest_or_strength:
            total_duration = duration_minutes
        else:
            wu_cd = PlanGenerator._wu_cd_minutes(duration_minutes)
            total_duration = duration_minutes + wu_cd * 2

        return {
            "week_number": week_number,
            "day_of_week": day_of_week,
            "phase": "Training",
            "title": title,
            "type": workout_type,
            "duration_minutes": total_duration,
            "distance_km": distance_km,
            "target_zone": resolved_zone,
            "target_hr_range": hr_range,
            "target_pace": resolved_pace,
            "description": description,
            "fueling_tip": fueling_tip,
            "session_slot": "main",
            "interval_reps": interval_reps if is_interval else None,
            "interval_rep_value": interval_rep_value if is_interval else None,
            "interval_rep_unit": interval_rep_unit if is_interval else None,
        }

    @staticmethod
    async def generate_plan_workouts(
        plan_id: int,
        user_profile: dict[str, Any],
        race_info: dict[str, Any],
        total_weeks: int = 12,
        api_key: str = None,
        cutoff_time_hours: float = None,
        block_number: int = 1,
        weeks_per_block: int = 2,
        block_context: str | None = None,
        target_week: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Generates a structured running plan based on:
        - User profile (age, max_hr, resting_hr, aet_hr, ant_hr, treadmill_preference, pace zones)
        - Race parameters (name, date, terrain 'road'/'trail', course distance, elevation gain)
        - Scott Johnston's Uphill Athlete principles (ME blocks)
        - The 80/20 intensity threshold logic for road running.
        - Dynamic periodized schedule duration.
        """
        # Block window calculation
        if target_week is not None:
            block_start_week = target_week
            block_end_week = target_week
        else:
            block_start_week = (block_number - 1) * weeks_per_block + 1
            block_end_week = min(block_start_week + weeks_per_block - 1, total_weeks)

        # 1. Base Variables Extract
        lang = race_info.get("lang", "en").lower()
        age = int(user_profile.get("age", 30))
        max_hr = int(user_profile.get("max_hr", 220 - age))
        resting_hr = int(user_profile.get("resting_hr", 60))
        gender = user_profile.get("gender")
        height_cm = user_profile.get("height_cm")
        weight_kg = user_profile.get("weight_kg")

        # Parse scheduling preferences stored as JSON strings in the DB
        import json as _json

        def _parse_days(val) -> list[str]:
            if not val:
                return []
            if isinstance(val, list):
                return val
            try:
                return _json.loads(val) or []
            except Exception:
                return []

        # Scheduling prefs are plan-level (stored in plans table, passed via race_info)
        preferred_run_days = _parse_days(race_info.get("preferred_days"))
        double_session_days = _parse_days(
            race_info.get("double_session_days") or user_profile.get("double_session_days")
        )
        long_run_day = race_info.get("long_run_day") or user_profile.get("long_run_day")
        days_per_week = race_info.get("days_per_week") or user_profile.get("days_per_week") or 4
        injury_history = user_profile.get("injury_history")

        # Threshold Heart Rates (AeT = Aerobic, AnT = Anaerobic)
        aet_hr = int(user_profile.get("aet_hr", resting_hr + int((max_hr - resting_hr) * 0.65)))
        ant_hr = int(user_profile.get("ant_hr", resting_hr + int((max_hr - resting_hr) * 0.85)))

        # Aerobic Deficiency Syndrome (ADS) per Training for the Uphill Athlete:
        # ADS is present if AeT is > 30 bpm below AnT, or if AeT < 80% of AnT.
        is_ads = (ant_hr - aet_hr) > 30 or (ant_hr > 0 and aet_hr < (ant_hr * 0.80))

        # Calculate Heart Rate Zones
        hr_zones = TrainingRules.calculate_heart_rate_zones(max_hr, resting_hr, aet_hr, ant_hr)
        z1_range = f"{hr_zones['Zone 1']['min']}-{hr_zones['Zone 1']['max']} bpm"
        z2_range = f"{hr_zones['Zone 2']['min']}-{hr_zones['Zone 2']['max']} bpm"
        z3_range = f"{hr_zones['Zone 3']['min']}-{hr_zones['Zone 3']['max']} bpm"
        z4_range = f"{hr_zones['Zone 4']['min']}-{hr_zones['Zone 4']['max']} bpm"

        coach_notes = race_info.get("coach_notes")
        terrain = race_info.get("terrain", "trail").lower()
        has_gym_access = bool(race_info.get("has_gym_access", False))
        use_treadmill = bool(race_info.get("use_treadmill", False))
        training_environment = (race_info.get("training_environment") or "flat").lower()
        # Hill Sprint/Hill Repeat/Hill Bound sessions need either real hills
        # (training_environment) or a treadmill incline to substitute for them —
        # not required for gym access, since these are bodyweight/no-equipment.
        hill_sprint_eligible = training_environment in ("hilly", "mixed") or use_treadmill

        course_distance_km = race_info.get("course_distance_km")
        course_elevation_gain_m = race_info.get("course_elevation_gain_m")
        target_time_hours = race_info.get("target_time_hours")
        current_weekly_km = float(user_profile.get("current_weekly_km", 30.0))

        # Pre-compute goal race pace if we have both a target time and distance
        if target_time_hours and course_distance_km:
            race_pace_dec = (float(target_time_hours) * 60) / float(course_distance_km)
            goal_race_pace_str = PlanGenerator.decimal_to_pace_str(race_pace_dec)
        else:
            goal_race_pace_str = None  # fall back to Zone 4 (race effort)

        # Which kind of runner this plan is for. Resolved here, above the pace zones,
        # because the tier decides the pace default as well as the rules block -- see
        # services/athlete_tier.py for why the tier follows the plan, not the athlete.
        _historical_ceiling = race_info.get("historical_ceiling") or user_profile.get("historical_ceiling")
        _max_jog_min = user_profile.get("max_continuous_jog_min")
        athlete_tier = resolve_tier(
            explicit_tier=race_info.get("athlete_tier"),
            goal_type=race_info.get("goal_type") or user_profile.get("goal_type"),
            current_weekly_km=current_weekly_km,
            max_continuous_jog_min=_max_jog_min,
            historical_max_distance_km=(_historical_ceiling or {}).get("max_distance_km"),
            # RAW stored thresholds, deliberately not the derived aet_hr/ant_hr above.
            # Those are computed from fixed 65%/85%-of-reserve ratios, so they yield the
            # SAME ~17% spread for every athlete -- which exceeds both the sub-elite and
            # elite gap limits and would cap literally everyone at recreational. The gap
            # is only evidence when it was actually measured.
            aet_hr=user_profile.get("aet_hr"),
            ant_hr=user_profile.get("ant_hr"),
        )
        tier_profile = get_profile(athlete_tier)

        # Extract Zone 2 bounds and calculate personalized pacing zone ranges.
        # goal_type comes from the PLAN, not the user: the same athlete can hold a
        # start-running plan and a race plan, and the tier default must follow the plan.
        est_zones = PlanGenerator.resolve_pace_zones(
            {**user_profile, "aet_hr": aet_hr, "ant_hr": ant_hr},
            race_info.get("goal_type") or user_profile.get("goal_type"),
            athlete_tier=athlete_tier,
        )

        p_z1 = est_zones["zone1_pace"]  # Range representation for prompt, e.g. "6:53 - 6:04"
        p_z2 = est_zones["zone2_pace"]  # Range representation for prompt, e.g. "6:30 - 5:45"
        p_z3 = est_zones["zone3_pace"]
        p_z4 = est_zones["zone4_pace"]
        p_z5 = est_zones["zone5_pace"]

        # Helper function to post-process and estimate target pace and distance for all workouts
        def post_process_workouts(wos: list[dict[str, Any]]) -> list[dict[str, Any]]:
            # Safety net: strip any week-1 workouts that land before the plan start day
            if block_number == 1 and _excluded_days_w1:
                wos = [
                    wo
                    for wo in wos
                    if not (
                        int(wo.get("week_number") or block_start_week) == 1
                        and wo.get("day_of_week") in _excluded_days_w1
                    )
                ]

            for wo in wos:
                dur = float(wo.get("duration_minutes") or 0.0)
                wo["duration_minutes"] = dur
                w_type = wo.get("type") or "Rest"
                wo["type"] = w_type

                # Ensure target_zone is never None to satisfy database TEXT NOT NULL constraint
                zone = wo.get("target_zone") or (
                    "Zone 1" if w_type in ("Rest", "Strength", "Muscular Endurance") else "Zone 2"
                )
                wo["target_zone"] = zone

                # Default other non-nullable database columns
                wo["phase"] = wo.get("phase") or "Training"
                wo["title"] = wo.get("title") or ("Rest Day" if w_type == "Rest" else "Workout")
                wo["day_of_week"] = wo.get("day_of_week") or "Monday"

                # Ensure correct typing for optional numeric fields and week_number
                if "week_number" in wo and wo["week_number"] is not None:
                    try:
                        wn = int(wo["week_number"])
                        # Clamp to block range to catch AI hallucinating out-of-range week numbers
                        wo["week_number"] = max(block_start_week, min(block_end_week, wn))
                    except Exception:
                        wo["week_number"] = block_start_week
                else:
                    wo["week_number"] = block_start_week

                # Reset Rest/Strength/ME — always zero distance, never inherit AI value
                title_lower = wo.get("title", "").lower()

                # Backstop: no hills and no treadmill means Hill Sprint/Hill Repeat/Hill
                # Bound is physically impossible regardless of what the AI prescribed —
                # relabel to a flat-terrain equivalent (mirrors not trusting the AI's
                # raw treadmill numbers below).
                if not hill_sprint_eligible and any(
                    kw in title_lower for kw in PlanGenerator.HILL_SPRINT_TITLE_KEYWORDS
                ):
                    fallback_title = "Chạy Biến Tốc / Tăng Tốc" if lang == "vi" else "Fartlek / Surges"
                    wo["title"] = fallback_title
                    title_lower = fallback_title.lower()

                if w_type in ("Rest", "Strength", "Muscular Endurance") or dur <= 0.0:
                    wo["target_pace"] = ""
                    wo["distance_km"] = 0.0
                # Race / Target Race: use the known course distance and goal pace
                elif ("target race" in title_lower or w_type == "Race") and course_distance_km:
                    wo["distance_km"] = float(course_distance_km)
                    # Use goal race pace derived from target finish time; fall back to Zone 4
                    wo["target_pace"] = f"{goal_race_pace_str or p_z4} /km"
                else:
                    # Map zone to pace range + distance (always recalculate, discard AI distance)
                    wo["target_pace"], wo["distance_km"] = PlanGenerator.pace_and_distance_for_zone(
                        zone, dur, est_zones
                    )

                wo["elevation_gain_m"], wo["grade_percent"] = PlanGenerator.resolve_elevation_and_grade(
                    wo, w_type, terrain, wo["distance_km"], course_elevation_gain_m, course_distance_km
                )

                # Treadmill settings are never the AI's raw numbers: derive range
                # strings from this workout's own pace range and resolved grade
                # (Hill Sprints get the non-negotiable 10-15% band).
                wo["treadmill_incline"], wo["treadmill_speed"] = PlanGenerator.resolve_treadmill_settings(
                    wo, wo["target_pace"], use_treadmill
                )

                wo["interval_reps"], wo["interval_rep_value"], wo["interval_rep_unit"] = (
                    PlanGenerator.resolve_interval_summary(wo, w_type)
                )
            return wos

        # 2. AI Plan Generation (Gemini → reduced-prompt retry → Rule-Based)
        import re as _re

        def _extract_json_array(text: str) -> str:
            """Extract the first JSON array from text, tolerating prose preambles."""
            # Strip markdown fences first
            text = _re.sub(r"```(?:json)?|```", "", text).strip()
            # Find the first '[' and its matching ']'
            start = text.find("[")
            if start == -1:
                return text
            depth = 0
            for i, ch in enumerate(text[start:], start):
                if ch == "[":
                    depth += 1
                elif ch == "]":
                    depth -= 1
                    if depth == 0:
                        return text[start : i + 1]
            return text[start:]  # malformed but let json.loads produce a clear error

        from config import settings

        # Build the AI prompt (Gemini is the only engine; a reduced retry and the
        # rule-based schedule below are the fallbacks).
        _ai_prompt = None
        try:
            scheduling_notes = ""
            all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            if preferred_run_days:
                rest_days = [d for d in all_days if d not in preferred_run_days]
                scheduling_notes += (
                    f"\nScheduling Preferences:\n"
                    f"- Training days per week: {days_per_week}\n"
                    f"- Preferred training days: {', '.join(preferred_run_days)}\n"
                    f"- Rest/off days (assign Rest workouts): {', '.join(rest_days) if rest_days else 'none'}\n"
                )
                if long_run_day:
                    scheduling_notes += f"- Preferred long run day: {long_run_day}\n"
            elif days_per_week:
                scheduling_notes += f"\nScheduling Preferences:\n" f"- Training days per week: {days_per_week}\n"
                if long_run_day:
                    scheduling_notes += f"- Preferred long run day: {long_run_day}\n"
            if double_session_days:
                scheduling_notes += (
                    f"- Double-session days: {', '.join(double_session_days)}\n"
                    "  On these days produce TWO workout objects for the same day_of_week:\n"
                    "  one with session_slot='morning' (shorter, lower-intensity) and one with session_slot='afternoon' (the main session).\n"
                    "  Do NOT double-session a day already designated as Rest.\n"
                )
            if injury_history:
                scheduling_notes += f"- Injury history: {injury_history}\n"

            # Historical Ceiling & Athlete Notes
            ceiling_notes = ""
            historical_ceiling = race_info.get("historical_ceiling") or user_profile.get("historical_ceiling")
            if historical_ceiling:
                max_d = historical_ceiling.get("max_distance_km", 0)
                max_h = historical_ceiling.get("max_duration_hours", 0)
                max_v = historical_ceiling.get("max_elevation_gain_m", 0)
                total_c = historical_ceiling.get("total_activities_count", 0)
                if max_d > 0 or max_v > 0:
                    ceiling_notes = (
                        f"\nAthlete Historical Ceiling (from wearable activity records):\n"
                        f"- Longest recorded run: {max_d} km ({max_h} hrs)\n"
                        f"- Max single-run elevation gain: {max_v} m D+\n"
                        f"- Synced activities on record: {total_c}\n"
                        f"Rule: Respect the athlete's proven endurance ceiling. Single long runs must not exceed 15-20% above this ceiling without multi-block progression.\n"
                    )

            athlete_notes = race_info.get("athlete_notes") or user_profile.get("athlete_notes")
            constraints_notes = ""
            if athlete_notes:
                constraints_notes = (
                    f"\nAthlete Notes & Special Routine Constraints:\n"
                    f'"{athlete_notes}"\n'
                    f"Rules for Special Constraints:\n"
                    f"- Flat/Urban Weekdays vs Weekend Trails: If the runner lives in an urban/flat environment during the week but accesses trails on weekends, prescribe flat aerobic runs, treadmill incline sessions, or bodyweight ME on weekdays, and allocate the big-vert trail runs to Saturday/Sunday.\n"
                    f"- Training Camp: If the athlete specifies a training camp during certain dates or weeks, allocate higher volume, back-to-back long runs, and race-specific vert during those designated camp days.\n"
                )

            gender_str = f"Gender: {gender.capitalize()}" if gender else "Gender: Not specified"
            ht_wt_parts = []
            if height_cm:
                ht_wt_parts.append(f"Height: {height_cm} cm")
            if weight_kg:
                ht_wt_parts.append(f"Weight: {weight_kg} kg")
            ht_wt_str = (", " + ", ".join(ht_wt_parts)) if ht_wt_parts else ""

            female_note = ""
            if gender and str(gender).strip().lower() == "female":
                female_note = (
                    "\nFemale Athlete Physiology Considerations: Prioritize iron/ferritin status monitoring, "
                    "allow adequate recovery between high-intensity bouts, ensure adequate carbohydrate availability "
                    "to prevent Relative Energy Deficiency in Sport (RED-S), and emphasize progressive heavy strength "
                    "training to preserve bone mineral density and tendon stiffness for mountain trail durability.\n"
                )

            if is_ads:
                ads_status = (
                    f"\nAEROBIC DEFICIENCY SYNDROME (ADS) DETECTED:\n"
                    f"- AeT ({aet_hr} bpm) is {ant_hr - aet_hr} bpm below AnT ({ant_hr} bpm) — spread exceeds 30 bpm / 80% threshold.\n"
                    f"- Hard Coaching Constraint: The athlete's slow-twitch aerobic base is deficient. DO NOT prescribe Zone 4/5 "
                    f"speedwork, threshold intervals, or high-glycolytic sessions during Base/Build phases. Allocate 90%+ of running "
                    f"volume strictly to Zone 1-2 (conversational pace below {aet_hr} bpm) to build mitochondrial density and fat "
                    f"oxidation capacity before introducing speedwork.\n"
                )
            else:
                ads_spread = ant_hr - aet_hr
                ads_ratio_pct = round((aet_hr / ant_hr) * 100) if ant_hr > 0 else 0
                ads_status = (
                    f"\nAerobic Efficiency: Healthy AeT/AnT spread ({ads_spread} bpm gap, AeT at {ads_ratio_pct}% of AnT). "
                    f"Normal aerobic base. Progressive threshold and ME work permitted in appropriate phases.\n"
                )

            user_summary = (
                f"{gender_str}{ht_wt_str}, Age: {age}, Weekly volume base: {current_weekly_km} km, Max HR: {max_hr} bpm, "
                f"Resting HR: {resting_hr} bpm, AeT: {aet_hr} bpm, AnT: {ant_hr} bpm, "
                f"Gym Access: {has_gym_access}, Treadmill Access: {use_treadmill}, "
                f"Training Environment: {training_environment} (hills available: {training_environment in ('hilly', 'mixed')})\n"
                f"Custom Pace Zones (min/km):\n"
                f"- Zone 1 (Recovery): {p_z1}\n"
                f"- Zone 2 (Easy Range): {p_z2}\n"
                f"- Zone 3 (Tempo): {p_z3}\n"
                f"- Zone 4 (Threshold): {p_z4}\n"
                f"- Zone 5 (Interval): {p_z5}"
                f"{ads_status}"
                f"{female_note}"
                f"{scheduling_notes}"
                f"{ceiling_notes}"
                f"{constraints_notes}"
            )

            # Calculate week/date context for the AI prompt
            try:
                race_date_parsed = datetime.strptime(race_info.get("date"), "%Y-%m-%d").date()
            except (ValueError, TypeError):
                race_date_parsed = datetime.now().date() + timedelta(days=90)

            start_date_str = race_info.get("plan_start_date") or datetime.now().strftime("%Y-%m-%d")
            try:
                today = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except ValueError:
                today = datetime.now().date()
            race_week_num = total_weeks - 1
            race_weekday_name = race_date_parsed.strftime("%A")

            current_date_str = today.strftime("%Y-%m-%d")
            current_weekday = today.strftime("%A")

            # Days of the week before the start day that must be excluded from week 1
            _all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            _start_idx = _all_days.index(current_weekday) if current_weekday in _all_days else 0
            _excluded_days_w1 = _all_days[:_start_idx]  # e.g. if start=Wednesday → [Monday, Tuesday]

            is_event_goal = race_info.get("goal_type") not in ["start_running", "return", "recovery"]

            # Build goal description for AI context
            if race_info.get("goal_type") == "start_running":
                goal_description = (
                    "Goal: Start Running / Learn to run. Build a safe, injury-free aerobic base "
                    "starting with walk-to-run progressions. Do NOT assign high-intensity threshold "
                    "or anaerobic intervals. Volume must start low and increase very slowly."
                )
            elif race_info.get("goal_type") == "return":
                time_away = user_profile.get("time_away") or "some time"
                fitness_feel = user_profile.get("fitness_feel") or "rusty"
                goal_description = (
                    f"Goal: Return to running after a break of {time_away}. Currently feeling: {fitness_feel}. "
                    "Re-establish a safe baseline volume. Start at about 50% of the athlete's previous volume "
                    "and gradually condition the tendons/joints. No intense speedwork; keep workouts in Zone 1 and 2."
                )
            elif race_info.get("goal_type") == "recovery":
                race_dist = user_profile.get("race_distance_completed") or "a recent race"
                days_ago = user_profile.get("days_since_race") or "a few"
                rec_feel = user_profile.get("recovery_feel") or "fatigued"
                goal_description = (
                    f"Goal: Post-Race Recovery after completing a {race_dist} race {days_ago} days ago. "
                    f"Current recovery state: {rec_feel}. The first 1-2 weeks must be focused entirely "
                    "on active recovery, resting, and very light movement (mostly Zone 1 or Rest). "
                    "Gradually reintroduce short, easy Zone 2 runs in the remaining weeks. No workouts above Zone 2."
                )
            elif cutoff_time_hours:
                cutoff_h = int(cutoff_time_hours)
                cutoff_m = int(round((cutoff_time_hours - cutoff_h) * 60))
                safe_hours = cutoff_time_hours * 0.85
                safe_h = int(safe_hours)
                safe_m = int(round((safe_hours - safe_h) * 60))
                goal_description = (
                    f"Goal: Just to Finish safely. "
                    f"Cutoff Time: {cutoff_h}h{cutoff_m:02d}m. "
                    f"Target Safe Finish Time: {safe_h}h{safe_m:02d}m (85% of cutoff)."
                )
            elif race_info.get("goal_type") == "time" and race_info.get("target_time_hours"):
                t = race_info["target_time_hours"]
                th = int(t)
                tm = int(round((t - th) * 60))
                goal_description = f"Goal: Finish in {th}h{tm:02d}m."
            else:
                goal_description = "Goal: Optimal performance."

            steepness_ratio_str = ""
            if course_distance_km and course_elevation_gain_m and float(course_distance_km) > 0:
                steepness = round(float(course_elevation_gain_m) / float(course_distance_km), 1)
                if steepness < 25.0:
                    terrain_category = "Rolling / Runnable trail (< 25 m D+/km). Prioritize sustained running cadence, steady aerobic economy, and runnable tempo intervals."
                elif steepness <= 50.0:
                    terrain_category = "Steep mountain trail (25-50 m D+/km). Emphasize power-hiking transitions on sustained grades (>12%), uphill repeats, and quad-loading descents."
                else:
                    terrain_category = "Extreme technical mountain vert / Skyrunning (> 50 m D+/km). Emphasize sustained power-hiking with poles, heavy weighted box step-ups (15-20% bodyweight), and eccentric downhill resistance repeats."
                steepness_ratio_str = f"Course Steepness Ratio: {steepness} m D+/km — {terrain_category}\n"

            if is_event_goal:
                program_summary = (
                    f"Race Name: {race_info.get('name')}, Date: {race_info.get('date')}, Terrain: {terrain}, "
                    f"Distance: {course_distance_km} km, Elevation Gain: {course_elevation_gain_m} m.\n"
                    f"{steepness_ratio_str}"
                    f"{goal_description}"
                )
            else:
                program_summary = (
                    f"Training Plan Name: {race_info.get('name')}, Focus: {race_info.get('goal_type')}.\n"
                    f"{steepness_ratio_str}"
                    f"{goal_description}"
                )

            if is_event_goal:
                goal_intro = "You will design a complete, periodized training schedule from scratch for this athlete leading to their target race."
                program_details = f"Race Details:\n{program_summary}\n"
                target_date_details = f"Target Race Date: {race_info.get('date')} ({race_weekday_name})\n\n"
                week_schedule_constraints = (
                    f"- Week {race_week_num} is the Race Week. The target race event MUST be scheduled in Week {race_week_num} on {race_weekday_name} ({race_info.get('date')}).\n"
                    f"- Week {total_weeks} is the post-race Recovery week.\n"
                )
            else:
                goal_intro = f"You will design a complete, periodized {race_info.get('goal_type')} training program from scratch for this athlete."
                program_details = f"Program Focus:\n{program_summary}\n"
                target_date_details = ""
                week_schedule_constraints = ""

            course_context = race_info.get("course_context")
            if course_context:
                program_details += (
                    f"\nCOURSE INTELLIGENCE & ENVIRONMENTAL DEMANDS (Curated Race Profile):\n{course_context}\n"
                )

            if target_week is not None:
                block_scope_instruction = (
                    f"\nSINGLE-WEEK REGENERATION & ADAPTATION:\n"
                    f"This plan spans {total_weeks} weeks total. You are adapting and regenerating ONLY Week {target_week}.\n"
                    f"CRITICAL: Every workout `week_number` MUST be exactly {target_week}. Do NOT output any workouts for other weeks.\n"
                    f"Adapt the workouts according to the athlete's latest feedback, fatigue, and recovery while maintaining target progressive overload.\n"
                )
            else:
                total_blocks = (total_weeks + weeks_per_block - 1) // weeks_per_block
                block_scope_instruction = (
                    f"\nSEQUENTIAL BLOCK GENERATION:\n"
                    f"This plan spans {total_weeks} weeks total, generated in {total_blocks} blocks of {weeks_per_block} weeks each.\n"
                    f"Generate ONLY Block {block_number} of {total_blocks}: weeks {block_start_week} through {block_end_week}.\n"
                    f"CRITICAL: Every workout `week_number` MUST be between {block_start_week} and {block_end_week} (inclusive). Do NOT output week numbers outside this range.\n"
                )
            # Kept separate from block_scope_instruction and placed last in the final prompt
            # below: this is free-text athlete feedback of unbounded length, so the schema and
            # hard constraints stay ahead of it. Coach directives come first within this
            # trailing section, ahead of the auto-collected athlete feedback.
            feedback_instruction = ""
            if coach_notes:
                feedback_instruction += (
                    f"\nCOACH INSTRUCTIONS (from the athlete's human coach — give these real weight, "
                    f"and let them override the default heuristics below where they conflict):\n{coach_notes}\n"
                )

            # Wearable Readiness Summary (7-day HRV, ACWR load ratio, recovery)
            readiness_summary = race_info.get("readiness_summary") or user_profile.get("readiness_summary")
            if readiness_summary and readiness_summary.get("days_recorded", 0) > 0:
                hrv = readiness_summary.get("avg_hrv_ms")
                hrv_stat = readiness_summary.get("latest_hrv_status") or "normal"
                rhr = readiness_summary.get("avg_resting_hr")
                acwr = readiness_summary.get("avg_load_ratio")
                lat_acwr = readiness_summary.get("latest_load_ratio")
                recov = readiness_summary.get("avg_recovery_percent")
                flag = (readiness_summary.get("readiness_flag") or "optimal").upper()

                hrv_str = f"{hrv} ms" if hrv is not None else "N/A"
                rhr_str = f"{rhr} bpm" if rhr is not None else "N/A"
                acwr_str = f"{acwr}" if acwr is not None else (f"{lat_acwr}" if lat_acwr is not None else "N/A")
                lat_acwr_str = f"{lat_acwr}" if lat_acwr is not None else "N/A"
                recov_str = f"{recov}%" if recov is not None else "N/A"

                feedback_instruction += (
                    f"\n7-DAY WEARABLE BIOLOGICAL READINESS & LOAD RATIO:\n"
                    f"- Rolling HRV: {hrv_str} (Status: {hrv_stat}) | Resting HR: {rhr_str}\n"
                    f"- ACWR (Acute:Chronic Load Ratio): {acwr_str} (Latest: {lat_acwr_str})\n"
                    f"- Rolling Recovery: {recov_str} | Biological Readiness Flag: {flag}\n"
                    f"Wearable Load Guidance:\n"
                    f"  • OVERREACHING (ACWR > 1.4): Cap weekly volume increase at 0% or deload 10-15% to avoid high injury risk. Eliminate high-impact eccentric downhill pounding.\n"
                    f"  • FATIGUED (Low HRV / Recovery < 45%): Convert one scheduled tempo/interval workout to an easy Zone 1 recovery run or Rest.\n"
                    f"  • OPTIMAL / FRESH (ACWR 0.8-1.3): Athlete is adapting well; proceed with planned progressive overload.\n"
                )

            if block_context:
                feedback_instruction += (
                    f"\nATHLETE FEEDBACK FROM PREVIOUS BLOCKS & COACH EVALUATION:\n{block_context}\n"
                    "CRITICAL — adjust this block based on coach evaluation and feedback above:\n"
                    "  • Coach evaluation indicates high execution quality (Grade A/B) and good aerobic control: proceed with planned progression.\n"
                    "  • Coach evaluation notes broken Zone 2 discipline or excessive intensity drift: rein in paces, keep easy days strictly below AeT.\n"
                    "Athlete Feeling & Exertion Scale (5 Tiers):\n"
                    "  • Very Light (RPE ≤ 2): Effortless recovery / underloaded — increase stimulus by 5-10% weekly volume or progress a quality session.\n"
                    "  • Light (RPE 3-4): Fresh & easy — maintain progressive overload; keep key quality sessions intact; optional 5% base run volume.\n"
                    "  • Moderate (RPE 5-6): Manageable training fatigue — steady progression as planned with balanced volume.\n"
                    "  • Hard (RPE 7-8): Elevated fatigue / heavy legs — ease off high intensity (shift tempo to Zone 2, shorten intervals) and trim volume 10-15%.\n"
                    "  • Max Effort (RPE 9-10): High fatigue / overreaching / exhausted — prescribe active recovery / deload week, reduce volume 20-30% and eliminate high-intensity work.\n"
                    "  • Any mention of injury/pain: remove ALL high-intensity work for that body region and add Strength or active recovery.\n"
                )

            # Start-date constraint for the first week of the first block
            _start_date_constraint = ""
            if block_number == 1 and _excluded_days_w1:
                _start_date_constraint = (
                    f"\nSTART DATE CONSTRAINT:\n"
                    f"The plan starts on {current_date_str} ({current_weekday}). "
                    f"Week 1 is a partial week.\n"
                    f"CRITICAL: Do NOT generate any workouts in Week 1 on "
                    f"{', '.join(_excluded_days_w1)} — those days are BEFORE the start date.\n"
                    f"Week 1 workouts must only be assigned to: "
                    f"{', '.join(_all_days[_start_idx:])}.\n"
                )

            equipment_terrain_rule = (
                "\n5. Equipment/terrain constraints — hard requirements, not preferences:\n"
                f"   - Gym access: {'available' if has_gym_access else 'NOT available'}. "
                + (
                    ""
                    if has_gym_access
                    else "NEVER prescribe weighted or machine-based exercises for Strength or Muscular "
                    "Endurance sessions — bodyweight-only (step-ups, lunges, squats, bodyweight circuits). "
                )
                + f"\n   - Hill Sprint/Hill Repeat/Hill Bound availability: {'available' if hill_sprint_eligible else 'NOT available'}"
                + (
                    "."
                    if hill_sprint_eligible
                    else " (no hills and no treadmill). NEVER prescribe a Hill Sprint, Hill Repeat, or Hill "
                    "Bound session — substitute an equivalent flat-terrain intensity session (e.g. Fartlek or "
                    "Surges) covering the same training purpose.\n"
                )
            )

            lang_rule = (
                "\n6. CRITICAL LOCALIZATION (VIETNAMESE):"
                "\n   - All workout text fields ('title', 'description', 'fueling_tip') MUST be written in natural, idiomatic Vietnamese used by endurance runners."
                "\n   - KEEP specialized running and sports science terms in standard English (e.g. 'Easy Run', 'Long Run', 'Tempo', 'Threshold', 'Interval', 'Muscular Endurance', 'Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Pace', 'Carbs', 'Sodium', 'Electrolytes', 'Treadmill', 'Fartlek', 'Surges', 'Step-Ups', 'Hill Bounds', 'Foam Rolling', 'Fueling')."
                "\n   - NEVER use the word 'sinh lý'; use 'thể chất' or appropriate physical context instead."
                "\n   - Do NOT translate 'Pace' as 'tốc độ' (tốc độ is speed in km/h; Pace is min/km)."
                "\n   - Do NOT translate 'Fueling' as 'tiếp nhiên liệu' (use 'dinh dưỡng & fueling' or 'fueling')."
                if lang == "vi"
                else ""
            )

            rules_block = build_rules_block(tier_profile, _max_jog_min)

            # The SCHEMA has to be tier-aware too, not just the rules. Fixing only the
            # rules left a beginner's prompt stating "NO Muscular Endurance sessions of
            # any kind" a few hundred characters after the schema handed the model the
            # Summit Water Dump protocol and 8-10g/kg race-day carb loading. A prompt
            # that contradicts itself is worse than one that is uniformly wrong: the
            # model resolves the conflict however it likes, differently each run.
            me_format_spec = (
                "     * Muscular Endurance (ME): this develops peripheral muscular fatigue resistance without cardiac strain. Format by terrain: (a) Flat/Rolling or Gym: high-cadence, high-rep CIRCUIT training — NEVER straight sets. One → segment per exercise names ONE pass (e.g. '10 reps Split Jump Squats, 15s transition → 10 reps Squat Jumps, 15s transition → 10 reps/leg Box Step-Ups at 75% kneecap height, 15s transition → 10 reps/leg Front Lunges'), followed by total rounds (6-8 rounds) and rest between rounds (~60s tapering to 15s). (b) Outdoor Mountain Hikes: steep 30%+ off-trail grade with 5-15% bodyweight pack, 5-20 min climbing intervals with 1-3 min recovery, and mandatory Summit Water Dump protocol: 'Dump water weight at summit; descend unweighted to preserve orthopedic integrity'. (c) Incline Treadmill: 12-15% incline, 90% and 95% uphill climbing pace intervals (standard commercial gym treadmills max out at 15%). (d) Hill Bounding / Ski Striding: 6-8 reps of 8-12s max-effort bounds on 15-20% hill, 3-4 min full standing/walking rest, strictly terminate at first power drop.\n"
                if tier_profile.allows_me_blocks
                else ""
            )

            # Fueling advice scales to the sessions this athlete actually runs. A beginner
            # doing 25-minute run/walks never reaches the carbohydrate tiers, and listing
            # them makes the plan intimidating for no benefit.
            _fuel_head = "   - `fueling_tip` (string: hydration, carbohydrate, and electrolyte guides specific to duration and intensity. Strictly follow these quantitative targets: "
            _fuel_short = "* Sessions < 75 mins: Plain water and optional electrolytes (200-400mg sodium); no exogenous carbs needed. "
            _fuel_long = (
                "* Sessions 75-150 mins: 30-60g carbohydrates per hour + 300-500mg sodium/hr with 400-600ml water/hr. "
                "* Sessions > 150 mins (Long Runs & Ultra simulation): 60-90g carbohydrates per hour + 500-800mg sodium/hr with 500-750ml fluid/hr. Practice with race-day fuels (energy gels, chews, drink mix). "
            )
            _fuel_race = "* Race Day / Pre-race (Target Race): 8-10g carbohydrates per kg bodyweight per day for 36-48 hours prior; on race day take 60-90g CHO/hr + 600-900mg sodium/hr starting within the first 30-45 minutes."
            if tier_profile.uses_walk_run:
                fueling_spec = (
                    _fuel_head
                    + _fuel_short
                    + "Do NOT prescribe gels, per-hour carbohydrate targets or race-day loading — this athlete's sessions do not reach those durations.)\n"
                )
            elif is_event_goal:
                fueling_spec = _fuel_head + _fuel_short + _fuel_long + _fuel_race + ")\n"
            else:
                fueling_spec = _fuel_head + _fuel_short + _fuel_long + ")\n"

            # The steep hill-sprint incline is a prescription for a session type this
            # athlete may not be given at all.
            hill_incline_exception = (
                "EXCEPTION — for a Hill Sprint or Hill Repeat workout specifically (identifiable by 'Hill Sprint'/'Hill Repeat' in the `title`), `treadmill_incline` MUST be in the 10-15% range regardless of the race's average grade or this workout's own `grade_percent` — these are short, near-maximal efforts that require a steep grade by design, not a race-average one. "
                if tier_profile.allows_intensity
                else ""
            )

            _ai_prompt = (
                "You are a world-class running coach training athletes based on the 'Training for the Uphill Athlete' philosophy.\n"
                f"{goal_intro}\n\n"
                "OUTPUT CONTRACT — this is the most important instruction and applies no matter what follows:\n"
                "You MUST return ONLY a JSON array of workout objects. NEVER wrap it in markdown fences like ```json, "
                "NEVER add prose before or after it. Each workout object MUST follow this exact schema:\n"
                "   - `week_number` (integer: MUST be within the block range specified below)\n"
                "   - `day_of_week` (string: 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')\n"
                "   - `phase` (string: 'Base', 'Build', 'Peak', 'Taper', 'Race Week', 'Recovery'. IMPORTANT: Follow this exact progression — Base (early weeks) → Build (mid weeks) → Peak (highest intensity week, 1-2 weeks before taper) → Taper (the week immediately before Race Week, reduce volume to ~50%) → Race Week (the week containing the actual race event) → Recovery (final week after the race).)\n"
                "   - `title` (string: name of workout)\n"
                "   - `type` (string: 'Easy', 'Tempo', 'Interval', 'Long Run', 'Strength', 'Rest', "
                "'Race', 'Recovery', 'Muscular Endurance', 'Walk/Run'. Use 'Walk/Run' for ANY session "
                "built from alternating jog and walk intervals — never label such a session 'Interval', "
                "which means high-intensity repeats and is displayed to the athlete as hard, maximal work.)\n"
                "   - `duration_minutes` (number: duration of workout)\n"
                "   - `target_zone` (string: 'Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5')\n"
                "   - `target_hr_range` (string: heart rate bounds based on athlete's thresholds, e.g. '125-140 bpm')\n"
                "   - `target_pace` (string: recommended target pace, matching or referencing their custom pace zones, e.g. '6:00 /km')\n"
                "   - `distance_km` (number: estimated distance in kilometers. Calculate this as duration_minutes / (target_pace in decimal minutes), e.g. 60 mins at 6:00/km is 10.0 km)\n"
                "   - `walk_interval_value` (number, ONLY for `type` 'Walk/Run': the WALK recovery per "
                "rep, in the same unit as `interval_rep_unit`. Together with the three interval fields "
                "below this makes the session renderable as '5 x 2 min jog / 1 min walk' rather than a "
                "sentence the athlete has to parse.)\n"
                "   - `interval_reps`, `interval_rep_value`, `interval_rep_unit` (for `type` 'Interval' or "
                "'Walk/Run', AND ONLY when the session is a single clean rep block — e.g. 8 reps of 12-second hill sprints, or 5 reps of 400m repeats. `interval_reps` is the integer rep count, `interval_rep_value` is the number per rep, `interval_rep_unit` is one of 's'/'m'/'min'/'km' matching how that rep is measured. OMIT all three (do not guess) when the session has a warm-up/main/cool-down structure that doesn't reduce to one rep block, a pyramid, or mixed rep durations — the `description` Process section still carries the full detail for those.)\n"
                "   - `elevation_gain_m` and `grade_percent` (numbers, ONLY for `type` Easy/Tempo/Interval/Long Run AND only when the athlete's terrain is trail/mountain — omit or use 0 otherwise): give this specific run a plausible amount of climbing, using the race's overall course_elevation_gain_m/course_distance_km (given below in the athlete/race profile) as context for what's typical, and this run's own distance/phase/role to vary it — a Base-phase Easy run climbs less than a Peak-phase Long Run. `grade_percent` should be consistent with `elevation_gain_m` and this run's own `distance_km` (grade ≈ elevation_gain_m / (distance_km × 10)), not just the race's average. NEVER invent a figure wildly inconsistent with the race's overall elevation profile.\n"
                "   - `description` (string: highly detailed description containing specific sections, each introduced by its keyword — Process, Overall, Reason, Benefit, Warning — appearing in that order and each appearing EXACTLY ONCE: "
                "Process (step-by-step execution using → to separate segments — EVERY exercise or effort chunk MUST be its own → segment; NEVER chain multiple exercises together with semicolons or commas inside a single segment, and NEVER wrap them in a label like 'Main Circuit: ...'. The warm-up, main, and cool-down minutes stated MUST sum exactly to duration_minutes.\n"
                "     * Easy/Tempo/Interval/Long Run, e.g. 'Warm up 10 min easy → 4 x 6min @ Zone 4, 2min jog recovery → cool down 10 min'.\n"
                "     * Strength (general/max-strength): straight sets — one → segment per exercise, each naming the exercise plus sets x reps and a 60-180s rest interval BETWEEN SETS OF THAT SAME EXERCISE (appropriate for near-maximal loads), e.g. 'Warm up 5 min mobility → Bodyweight Squats: 3x10, 90s rest → Walking Lunges: 3x10 each leg, 90s rest → Cool down 5 min stretching'.\n"
                f"{me_format_spec}"
                "     * Interval: state exact rep count, distance or duration per rep, and recovery between reps.\n"
                "NEVER substitute a placeholder segment like 'Perform the bodyweight strength circuit for 20 minutes' for the actual named-exercise segments, and NEVER place the exercise breakdown anywhere outside this Process → chain (in particular, never append it after Warning or any other section) — every exercise MUST live inside Process and nowhere else), "
                "Overall (2-3 sentence summary of the session), Reason (why it is scheduled now), Benefit (expected physiological adaptation), and Warning (ONLY injury risks or execution precautions — NEVER exercise prescriptions, sets, or reps; those belong exclusively in Process). Provide extensive context.)\n"
                f"{fueling_spec}"
                f"   - `treadmill_incline` (number, optional: recommended incline percentage if using treadmill. Inform this from the route's actual grade instead of a flat generic default: for trail-terrain Easy/Tempo/Interval/Long Run workouts, set it consistent with this same workout's own `grade_percent` above (a flat 1% belt incline under-trains the specific climbing demand of a genuinely hilly race). {hill_incline_exception}Omit or use 0 when treadmill access isn't relevant.)\n"
                "   - `treadmill_speed` (number, optional: recommended speed in kph if using treadmill, reduced appropriately for the incline set above — a steeper incline needs a slower speed to hold the same target effort)\n"
                "   - `session_slot` (string, optional: ONLY set this on double-session days. Use 'morning' for the first/shorter session and 'afternoon' for the main/longer session. Omit entirely for single-session days.)\n\n"
                f"{block_scope_instruction}"
                f"{_start_date_constraint}"
                f"{week_schedule_constraints}"
                f"{rules_block}"
                f"{equipment_terrain_rule}"
                f"{lang_rule}\n\n"
                f"Athlete Profile:\n{user_summary}\n\n"
                f"{program_details}"
                f"Plan Start Date: {current_date_str} ({current_weekday})\n"
                f"{target_date_details}"
                f"Full Plan Length: {total_weeks} weeks.\n"
                f"- Week 1 starts on: {current_date_str} ({current_weekday}).\n"
                f"{feedback_instruction}"
            )

        except Exception as _prompt_ex:
            print(f"[PlanGen] Prompt building failed: {_prompt_ex}. Using rule-based fallback.")

        async def _try_gemini(reduced: bool = False) -> list[dict[str, Any]] | None:
            """One Gemini attempt. `reduced=True` is the retry tier: it drops the KB
            grounding context and asks for shorter descriptions, because the failure it
            exists to recover from — a truncated or unparseable response — is driven by
            output length. Telemetry labels it as a separate engine so the retry's own
            hit rate is visible rather than folded into the first attempt's."""
            if not (_ai_prompt and api_key):
                return None
            import asyncio

            _engine = "gemini_retry" if reduced else "gemini"

            _kb_context = ""
            # Ground the plan in distilled Uphill Athlete philosophy. Retrieval failure
            # is non-fatal — the prompt already carries the core rules inline.
            if not reduced:
                try:
                    from services.kb_context import render_principles_context
                    from services.kb_retrieval import search_scheduler_chunks

                    _retrieval_query = (
                        f"{race_info.get('terrain', 'trail')} race training plan: periodization "
                        f"phases, muscular endurance circuit design, taper and race week, long run "
                        f"and Zone 2 volume, double sessions"
                    )
                    _hits = await asyncio.to_thread(search_scheduler_chunks, _retrieval_query, api_key, 6)
                    _kb_context = render_principles_context(
                        _hits, heading="UPHILL ATHLETE PHILOSOPHY (grounding context)"
                    )
                    print(f"[PlanGen][KB] Retrieved {len(_hits)} philosophy chunks")
                except Exception as _kb_ex:
                    print(f"[PlanGen][KB] Retrieval failed (continuing without): {_kb_ex}")
            _gemini_prompt = _ai_prompt + ("\n\n" + _kb_context if _kb_context else "")
            if reduced:
                _gemini_prompt = (
                    "RETRY: the previous attempt did not return usable JSON. Return ONLY the JSON "
                    "array — no prose, no markdown fences — and keep each `description` under 600 "
                    "characters so the response completes. Every other rule below still applies.\n\n"
                ) + _gemini_prompt
            try:
                import time

                from google import genai as _genai
                from google.genai import types as _genai_types

                from telemetry import rag_attempts_total, rag_latency_seconds

                _client = _genai.Client(api_key=api_key)
                _logger.info(
                    "gemini prompt sent",
                    extra={
                        "fields": {
                            "service": "plan_generator",
                            "engine": _engine,
                            "event": "prompt_sent",
                            "chars_sent": len(_gemini_prompt),
                        }
                    },
                )

                rag_attempts_total.labels(service="plan_generator", engine=_engine, status="attempt").inc()
                _start = time.time()
                try:
                    _response = await asyncio.to_thread(
                        _client.models.generate_content,
                        model=settings.GEMINI_MODEL,
                        contents=_gemini_prompt,
                        config=_genai_types.GenerateContentConfig(
                            thinking_config=_genai_types.ThinkingConfig(thinking_level=settings.GEMINI_THINKING_LEVEL)
                        )
                        if hasattr(_genai_types, "ThinkingConfig")
                        else None,
                    )
                    _latency = time.time() - _start
                    rag_latency_seconds.labels(service="plan_generator", engine=_engine).observe(_latency)
                    rag_attempts_total.labels(service="plan_generator", engine=_engine, status="success").inc()
                    _logger.info(
                        "gemini response received",
                        extra={
                            "fields": {
                                "service": "plan_generator",
                                "engine": _engine,
                                "event": "response_received",
                                "chars_received": len(_response.text),
                                "latency_ms": round(_latency * 1000),
                            }
                        },
                    )
                except Exception as _gemini_ex:
                    rag_attempts_total.labels(service="plan_generator", engine=_engine, status="error").inc()
                    _logger.error(
                        "gemini request failed",
                        extra={
                            "fields": {
                                "service": "plan_generator",
                                "engine": _engine,
                                "event": "error",
                                "error": str(_gemini_ex),
                            }
                        },
                        exc_info=True,
                    )
                    raise
                clean_text = _extract_json_array(_response.text)
                try:
                    ai_workouts = _json.loads(clean_text)
                except _json.JSONDecodeError as json_err:
                    _logger.warning(
                        "gemini response failed JSON parsing",
                        extra={
                            "fields": {
                                "service": "plan_generator",
                                "engine": _engine,
                                "event": "parse_error",
                                "error": str(json_err),
                            }
                        },
                    )
                    ai_workouts = None
                if isinstance(ai_workouts, list) and len(ai_workouts) > 0:
                    cleaned_wos = [wo for wo in ai_workouts if isinstance(wo, dict)]
                    _logger.info(
                        "gemini workouts parsed",
                        extra={
                            "fields": {
                                "service": "plan_generator",
                                "engine": _engine,
                                "event": "parsed",
                                "workout_count": len(cleaned_wos),
                            }
                        },
                    )
                    _processed = post_process_workouts(cleaned_wos)
                    rag_attempts_total.labels(service="plan_generator", engine=_engine, status="used").inc()
                    return _processed
                else:
                    _logger.warning(
                        "gemini returned empty or invalid list, using rule-based fallback",
                        extra={
                            "fields": {
                                "service": "plan_generator",
                                "engine": _engine,
                                "event": "empty_result",
                            }
                        },
                    )
                    return None
            except Exception as ex:
                _logger.error(
                    "gemini attempt failed, using rule-based fallback schedule",
                    extra={
                        "fields": {
                            "service": "plan_generator",
                            "engine": _engine,
                            "event": "fallback",
                            "error": str(ex),
                        }
                    },
                    exc_info=True,
                )
                return None

        # Gemini is the only engine. One reduced-prompt retry covers the common transient
        # failure (a truncated or unparseable response) before falling through to the
        # deterministic rule-based schedule below.
        for _reduced in (False, True):
            _result = await _try_gemini(reduced=_reduced)
            if _result:
                return _result

        # --- Rule-Based Fallback Schedule ---

        base_weekly_minutes = current_weekly_km * 6.0
        if base_weekly_minutes < 120.0:
            base_weekly_minutes = 180.0

        workouts: list[dict[str, Any]] = []
        W = total_weeks - 1
        num_peak_weeks = 2 if W >= 6 else (1 if W >= 2 else 0)
        remaining_weeks = W - 1 - num_peak_weeks
        num_build_weeks = remaining_weeks // 2
        num_base_weeks = remaining_weeks - num_build_weeks

        def get_phase_for_week(w: int) -> str:
            if w == total_weeks:
                return "Recovery"
            elif w == W:
                return "Race Week"
            elif w == W - 1:
                return "Taper"
            elif w > num_base_weeks + num_build_weeks:
                return "Peak"
            elif w > num_base_weeks:
                return "Build"
            else:
                return "Base"

        for week in range(block_start_week, block_end_week + 1):
            phase = get_phase_for_week(week)
            if phase == "Base":
                volume_multiplier = 1.0 + (0.05 * (week - 1))
            elif phase == "Build":
                volume_multiplier = 1.2 + (0.05 * (week - num_base_weeks - 1))
            elif phase == "Peak":
                volume_multiplier = 1.4 - (0.05 * (week - num_base_weeks - num_build_weeks - 1))
            elif phase == "Taper":
                volume_multiplier = 0.5  # Reduced load — pre-race freshening
            elif phase == "Race Week":
                volume_multiplier = 0.6
            else:
                volume_multiplier = 0.4

            week_minutes = base_weekly_minutes * volume_multiplier
            easy_minutes = week_minutes * 0.8
            quality_minutes = week_minutes * 0.2

            # Day 1: Monday
            workouts.append(
                {
                    "week_number": week,
                    "day_of_week": "Monday",
                    "phase": phase,
                    "title": "Rest & Regeneration",
                    "type": "Rest",
                    "duration_minutes": 0.0,
                    "target_zone": "Zone 1",
                    "description": "Rest day. Prioritize sleep, light stretching, and muscular recovery.",
                    "fueling_tip": "Focus on standard hydration. Balanced baseline meals.",
                }
            )

            # Day 2: Tuesday
            tue_dur = easy_minutes * 0.25
            workouts.append(
                {
                    "week_number": week,
                    "day_of_week": "Tuesday",
                    "phase": phase,
                    "title": "Recovery Zone Run",
                    "type": "Recovery",
                    "duration_minutes": round(tue_dur),
                    "target_zone": "Zone 1",
                    "target_hr_range": z1_range,
                    "target_pace": f"{p_z1} /km",
                    "description": "Active recovery run. Keep effort extremely light and comfortable.",
                    "fueling_tip": "Hydrate with water. No additional intra-workout carbs required.",
                }
            )

            # Day 3: Wednesday
            wed_dur = quality_minutes if quality_minutes > 0 else easy_minutes * 0.2
            is_interval = week % 2 == 0

            if phase == "Recovery":
                title = "Restorative Mobility"
                w_type = "Rest"
                zone = "Zone 1"
                hr_range = z1_range
                pace = f"{p_z1} /km"
                desc = "No running. Focus on full-body mobility, gentle stretching, and hydration."
                fuel_tip = "Eat high-protein, nutrient-dense foods to rebuild muscle tissues."
                wed_dur = 0.0
            elif is_interval:
                title = "Aerobic Power Intervals"
                w_type = "Interval"
                zone = "Zone 4"
                hr_range = z4_range
                pace = f"{p_z4} /km"
                # Reps/recovery fixed; warmup+cooldown scale with the day's
                # actual duration, and cooldown absorbs any rounding
                # remainder so the stated minutes always sum to wed_dur.
                total_dur = round(wed_dur)
                warmup, cooldown = PlanGenerator._warmup_cooldown_minutes(total_dur)
                main_minutes = max(6, total_dur - warmup - cooldown)
                reps = 4
                recovery_per_gap = 2
                work_per_rep = max(1, round((main_minutes - (reps - 1) * recovery_per_gap) / reps))
                main_actual = reps * work_per_rep + (reps - 1) * recovery_per_gap
                cooldown = max(1, cooldown + (main_minutes - main_actual))
                desc = (
                    f"Warmup {warmup}m. Repeat {reps}x{work_per_rep} minutes at Zone 4 effort. "
                    f"Recover with {recovery_per_gap} minutes light jog between. Cooldown {cooldown}m."
                )
                fuel_tip = "High intensity workout: Consume a fast-absorbing energy gel 15 minutes before starting."
            else:
                title = "Aerobic Tempo Session"
                w_type = "Tempo"
                zone = "Zone 3"
                hr_range = z3_range
                pace = f"{p_z3} /km"
                # Warmup/cooldown scale with the day's actual duration; main
                # is the exact remainder, so the stated minutes always sum
                # to wed_dur.
                total_dur = round(wed_dur)
                warmup, cooldown = PlanGenerator._warmup_cooldown_minutes(total_dur)
                main_minutes = max(5, total_dur - warmup - cooldown)
                desc = f"Warmup {warmup}m. Run at moderate tempo pace (Zone 3) for {main_minutes} minutes. Cooldown {cooldown}m."
                fuel_tip = "Consume electrolytes during the workout. Take 1 gel mid-session."

            wo = {
                "week_number": week,
                "day_of_week": "Wednesday",
                "phase": phase,
                "title": title,
                "type": w_type,
                "duration_minutes": round(wed_dur),
                "target_zone": zone,
                "target_hr_range": hr_range,
                "target_pace": pace,
                "description": desc,
                "fueling_tip": fuel_tip,
            }
            if is_interval:
                wo["interval_reps"] = reps
                wo["interval_rep_value"] = float(work_per_rep)
                wo["interval_rep_unit"] = "min"
            workouts.append(wo)

            # Day 4: Thursday
            thu_dur = easy_minutes * 0.25
            if phase == "Recovery":
                title = "Easy Recovery Spin or Walk"
                w_type = "Recovery"
                zone = "Zone 1"
                hr_range = z1_range
                pace = f"{p_z1} /km"
                desc = "30-minute light walk, swim, or easy spin. Keep heart rate strictly in Zone 1."
                fuel_tip = "Drink plenty of water and electrolytes to rehydrate after target event."
                thu_dur = 30.0
            else:
                title = "Aerobic Capacity Run"
                w_type = "Aerobic Capacity"
                zone = "Zone 2"
                hr_range = z2_range
                pace = f"{p_z2} /km"
                desc = "Steady continuous run. Targets mitochondrial development and fat oxidation efficiency."
                fuel_tip = "Practice gut-training: take 30g carbs per hour if workout exceeds 60 minutes."

            workouts.append(
                {
                    "week_number": week,
                    "day_of_week": "Thursday",
                    "phase": phase,
                    "title": title,
                    "type": w_type,
                    "duration_minutes": round(thu_dur),
                    "target_zone": zone,
                    "target_hr_range": hr_range,
                    "target_pace": pace,
                    "description": desc,
                    "fueling_tip": fuel_tip,
                }
            )

            # Day 5: Friday
            workouts.append(
                {
                    "week_number": week,
                    "day_of_week": "Friday",
                    "phase": phase,
                    "title": "Rest & Mobilize",
                    "type": "Rest",
                    "duration_minutes": 0.0,
                    "target_zone": "Zone 1",
                    "description": "Rest day. Light yoga, mobility drills, or foam rolling.",
                    "fueling_tip": "Standard nutrition. Keep baseline hydration levels consistent.",
                }
            )

            # Day 6: Saturday
            sat_dur = easy_minutes * 0.50
            if course_distance_km and course_distance_km > 0:
                scale_factor = min(1.5, max(1.0, course_distance_km / 42.2))
                sat_dur = sat_dur * scale_factor
            sat_dur = min(300.0, sat_dur)

            if phase == "Recovery":
                workouts.append(
                    {
                        "week_number": week,
                        "day_of_week": "Saturday",
                        "phase": phase,
                        "title": "Post-Race Gentle Hike",
                        "type": "Recovery",
                        "duration_minutes": 30.0,
                        "target_zone": "Zone 1",
                        "target_hr_range": z1_range,
                        "target_pace": f"{p_z1} /km",
                        "description": "Short restorative walk or light hike on flat, soft terrain. Enjoy the fresh air.",
                        "fueling_tip": "Focus on clean foods. Hydrate normally.",
                    }
                )
            elif phase == "Race Week" and week == W:
                workouts.append(
                    {
                        "week_number": week,
                        "day_of_week": "Saturday",
                        "phase": phase,
                        "title": f"TARGET EVENT: {race_info.get('name', 'Race Day')}",
                        "type": "Race",
                        "duration_minutes": 240 if not course_distance_km else round(course_distance_km * 6.5),
                        "target_zone": "Zone 2",
                        "description": f"Race day! Execute pacing strategy for your {course_distance_km or ''}km event, maintain fueling targets, and enjoy the run.",
                        "fueling_tip": "RACE FUELING: Target 60-90g carbs/hr, and 500-700mg sodium/hr. Stick to tested products.",
                    }
                )
            else:
                desc = "Building aerobic endurance. Keep a steady conversational effort."
                if course_distance_km and course_distance_km > 0:
                    if phase == "Base":
                        desc = f"Building aerobic endurance for your {course_distance_km}km event. Keep a steady conversational effort. Target: cover around 30-40% of race distance."
                    elif phase == "Build":
                        desc = f"Steady long run. Keep effort conversational (Zone 2). Target: cover around 50-60% of your race distance ({round(course_distance_km * 0.5)}km-{round(course_distance_km * 0.6)}km) to build specific fatigue resistance."
                    elif phase == "Peak":
                        desc = f"Peak long run. Practice gear and race-day nutrition. Target: cover around 70-80% of your race distance ({round(course_distance_km * 0.7)}km) at conversational effort."

                workouts.append(
                    {
                        "week_number": week,
                        "day_of_week": "Saturday",
                        "phase": phase,
                        "title": "Endurance Long Run",
                        "type": "Long Run",
                        "duration_minutes": round(sat_dur),
                        "target_zone": "Zone 2",
                        "target_hr_range": z2_range,
                        "target_pace": f"{p_z2} /km",
                        "description": desc,
                        "fueling_tip": f"GUT TRAINING: Target {60 if sat_dur > 90 else 30}g carbs/hour using gels and drink mixes to prepare your stomach.",
                    }
                )

            # Day 7: Sunday
            sun_dur = 45.0
            treadmill_incl = 0.0
            treadmill_sp = 0.0

            if phase == "Recovery":
                workouts.append(
                    {
                        "week_number": week,
                        "day_of_week": "Sunday",
                        "phase": phase,
                        "title": "Rest & Recuperation",
                        "type": "Rest",
                        "duration_minutes": 0.0,
                        "target_zone": "Zone 1",
                        "description": "Complete rest day. Spend time with family, sleep well, and let your body fully restore.",
                        "fueling_tip": "Balanced recovery diet.",
                    }
                )
            else:
                if terrain == "trail":
                    if phase == "Base":
                        title = "General Base Strength"
                        w_type = "Strength"
                        desc = (
                            "Bodyweight routine: lunges, single-leg squats, and core stabilization. 3 sets of 12 reps."
                        )
                        if course_elevation_gain_m and course_elevation_gain_m > 0:
                            desc += f" Prepares muscles for the {course_elevation_gain_m}m climbing demands."
                        fuel_tip = "Drink amino acids post-workout for protein synthesis."
                    elif phase == "Build":
                        w_type = "Muscular Endurance"
                        steps = 400 + (100 * (week - num_base_weeks - 1))
                        if course_elevation_gain_m and course_elevation_gain_m > 0:
                            steps += int(course_elevation_gain_m / 10)
                        steps = min(1200, steps)
                        if has_gym_access:
                            title = "Muscular Endurance: Weighted Step-Ups"
                            weight_pct = 10 if week <= 6 else 15
                            desc = f"Execute {steps} step-ups holding {weight_pct}% of your body weight on a 30cm box. Simulates climbing demands for your event ({course_elevation_gain_m or ''}m total gain)."
                            fuel_tip = "Consume electrolytes. Keep hydration nearby during strength efforts."

                            incline_pct = 12.0
                            if course_elevation_gain_m and course_distance_km:
                                incline_pct = min(
                                    15.0,
                                    max(8.0, round((course_elevation_gain_m / (course_distance_km * 1000.0)) * 100, 1)),
                                )

                            if use_treadmill:
                                treadmill_incl = incline_pct
                                settings = TrainingRules.calculate_treadmill_settings(12.0, incline_pct)
                                treadmill_sp = settings["speed_kph"]
                        else:
                            title = "Muscular Endurance: Bodyweight Step-Ups"
                            desc = f"Execute {steps} bodyweight step-ups on a 30cm box, no added weight. Simulates climbing demands for your event ({course_elevation_gain_m or ''}m total gain)."
                            fuel_tip = "Consume electrolytes. Keep hydration nearby during strength efforts."
                    elif phase == "Peak":
                        w_type = "Muscular Endurance"
                        if hill_sprint_eligible:
                            title = "Muscular Endurance: Hill Bounds"
                            desc = "Find a steep 10-15% grade hill. 6-8x repeats of 30 seconds explosive hill bounds. Walk down recovery."
                            if course_elevation_gain_m and course_elevation_gain_m > 0:
                                desc = f"Find a steep 10-15% grade hill simulating your event. 8-10x repeats of 30 seconds explosive hill bounds to handle the {course_elevation_gain_m}m of race vertical. Walk down recovery."
                        else:
                            title = "Muscular Endurance: Explosive Bounding"
                            desc = "No hills or treadmill available: 6-8x sets of 8-10 explosive bounding strides on flat ground, focusing on power and stride length. Full recovery between sets."
                            if course_elevation_gain_m and course_elevation_gain_m > 0:
                                desc = f"No hills or treadmill available: 6-8x sets of 8-10 explosive bounding strides on flat ground to build the power needed for the {course_elevation_gain_m}m of race vertical. Full recovery between sets."
                        fuel_tip = "Intense muscle breakdown: Consume 25g protein within 30 minutes of finishing."
                    else:
                        title = "Active Recovery Walk"
                        w_type = "Recovery"
                        desc = f"Restorative {round(sun_dur)}-minute light walk or hike on soft trail."
                        fuel_tip = "Recovery focus. Drink water."
                else:
                    title = "Core & Hip Stability"
                    w_type = "Strength"
                    desc = "Focus on glute activation, hip bridges, side planks, and calf raises. Essential for road injury prevention."
                    fuel_tip = "Protein-focused recovery snack."

                if not (phase == "Race Week" and week == W):
                    workouts.append(
                        {
                            "week_number": week,
                            "day_of_week": "Sunday",
                            "phase": phase,
                            "title": title,
                            "type": w_type,
                            "duration_minutes": round(sun_dur),
                            "target_zone": "Zone 1",
                            "treadmill_incline": treadmill_incl,
                            "treadmill_speed": treadmill_sp,
                            "description": desc,
                            "fueling_tip": fuel_tip,
                        }
                    )

        # Localization dictionary for rule-based fallback
        if lang == "vi":
            vi_trans = {
                "Rest & Regeneration": "Nghỉ ngơi & Phục hồi",
                "Rest day. Prioritize sleep, light stretching, and muscular recovery.": "Ngày nghỉ. Ưu tiên giấc ngủ, giãn cơ nhẹ và phục hồi cơ bắp.",
                "Focus on standard hydration. Balanced baseline meals.": "Tập trung uống nước đầy đủ. Ăn các bữa ăn cân bằng dinh dưỡng.",
                "Recovery Zone Run": "Chạy phục hồi nhẹ nhàng (Recovery Run)",
                "Active recovery run. Keep effort extremely light and comfortable.": "Chạy phục hồi chủ động. Giữ nỗ lực cực kỳ nhẹ nhàng và thoải mái.",
                "Hydrate with water. No additional intra-workout carbs required.": "Uống nước lọc đầy đủ. Không cần nạp thêm carbs trong khi chạy.",
                "Restorative Mobility": "Di động khớp phục hồi",
                "No running. Focus on full-body mobility, gentle stretching, and hydration.": "Không chạy. Tập trung vào vận động khớp toàn thân, giãn cơ nhẹ nhàng và bổ sung nước.",
                "Eat high-protein, nutrient-dense foods to rebuild muscle tissues.": "Ăn thực phẩm giàu protein, giàu dinh dưỡng để tái tạo mô cơ.",
                "Aerobic Power Intervals": "Interval phát triển năng lực hiếu khí",
                # Note: the Interval/Tempo Process descriptions now embed
                # dynamic warmup/main/cooldown minutes (see t_str's regex
                # substitutions below) instead of a fixed exact string.
                "High intensity workout: Consume a fast-absorbing energy gel 15 minutes before starting.": "Bài tập cường độ cao: Nạp 1 gel năng lượng hấp thu nhanh 15 phút trước khi bắt đầu.",
                "Aerobic Tempo Session": "Chạy Aerobic Tempo",
                "Consume electrolytes during the workout. Take 1 gel mid-session.": "Bổ sung điện giải trong khi chạy. Nạp 1 gel năng lượng ở giữa buổi.",
                "Easy Recovery Spin or Walk": "Đạp xe nhẹ phục hồi hoặc đi bộ",
                "30-minute light walk, swim, or easy spin. Keep heart rate strictly in Zone 1.": "30 phút đi bộ nhẹ, bơi hoặc đạp xe nhẹ nhàng. Giữ nhịp tim nghiêm ngặt trong Zone 1.",
                "Drink plenty of water and electrolytes to rehydrate after target event.": "Uống nhiều nước và điện giải để bù nước sau sự kiện mục tiêu.",
                "Aerobic Capacity Run": "Chạy tích lũy sức bền hiếu khí (Aerobic Capacity)",
                "Steady continuous run. Targets mitochondrial development and fat oxidation efficiency.": "Chạy đều liên tục. Nhằm phát triển ti thể và tăng hiệu quả đốt chất béo làm năng lượng.",
                "Practice gut-training: take 30g carbs per hour if workout exceeds 60 minutes.": "Luyện tập hệ tiêu hóa (Gut Training): nạp 30g carbs mỗi giờ nếu buổi chạy kéo dài hơn 60 phút.",
                "Rest & Mobilize": "Nghỉ ngơi & Vận động nhẹ",
                "Rest day. Light yoga, mobility drills, or foam rolling.": "Ngày nghỉ. Tập yoga nhẹ nhàng, các bài tập linh hoạt khớp hoặc dùng con lăn giãn cơ (foam rolling).",
                "Standard nutrition. Keep baseline hydration levels consistent.": "Dinh dưỡng tiêu chuẩn. Giữ mức bổ sung nước cơ bản đều đặn.",
                "Post-Race Gentle Hike": "Đi bộ nhẹ phục hồi sau giải chạy",
                "Short restorative walk or light hike on flat, soft terrain. Enjoy the fresh air.": "Đi bộ ngắn phục hồi hoặc dạo bộ nhẹ nhàng trên địa hình phẳng, mềm. Tận hưởng không khí trong lành.",
                "Focus on clean foods. Hydrate normally.": "Tập trung vào thực phẩm lành mạnh. Bổ sung nước bình thường.",
                "TARGET EVENT: ": "SỰ KIỆN MỤC TIÊU: ",
                "Race day! Execute pacing strategy for your ": "Ngày chạy đua! Thực hiện chiến lược Pacing cho sự kiện ",
                "km event, maintain fueling targets, and enjoy the run.": "km của bạn, duy trì các mục tiêu nạp năng lượng & fueling và tận hưởng cuộc đua.",
                "RACE FUELING: Target 60-90g carbs/hr, and 500-700mg sodium/hr. Stick to tested products.": "DINH DƯỠNG NGÀY ĐUA: Mục tiêu nạp 60-90g carbs/giờ, và 500-700mg sodium/giờ. Chỉ dùng các sản phẩm đã thử nghiệm từ trước.",
                "Endurance Long Run": "Chạy dài phát triển sức bền (Long Run)",
                "Building aerobic endurance. Keep a steady conversational effort.": "Xây dựng sức bền hiếu khí. Giữ nỗ lực chạy đều đặn ở mức có thể trò chuyện.",
                "GUT TRAINING: Target 60g carbs/hour using gels and drink mixes to prepare your stomach.": "GUT TRAINING: Mục tiêu nạp 60g carbs/giờ sử dụng gel và drink mix để tập thích nghi cho dạ dày.",
                "GUT TRAINING: Target 30g carbs/hour using gels and drink mixes to prepare your stomach.": "GUT TRAINING: Mục tiêu nạp 30g carbs/giờ sử dụng gel và drink mix để tập thích nghi cho dạ dày.",
                "Rest & Recuperation": "Nghỉ ngơi & Phục hồi hoàn toàn",
                "Complete rest day. Spend time with family, sleep well, and let your body fully restore.": "Ngày nghỉ ngơi hoàn toàn. Dành thời gian cho gia đình, ngủ đủ giấc và để cơ thể phục hồi tối đa.",
                "Balanced recovery diet.": "Chế độ ăn phục hồi cân bằng.",
                "General Base Strength": "Bài tập Sức mạnh nền tảng (Base Strength)",
                "Bodyweight routine: lunges, single-leg squats, and core stabilization. 3 sets of 12 reps.": "Bài tập sức nặng cơ thể: chùng chân (lunges), ngồi xổm một chân (single-leg squats), và ổn định cơ core. 3 hiệp 12 lần lặp.",
                "Prepares muscles for the ": "Chuẩn bị cơ bắp cho nhu cầu leo dốc ",
                "m climbing demands.": "m của cuộc đua.",
                "Drink amino acids post-workout for protein synthesis.": "Uống axit amin sau khi tập để hỗ trợ tổng hợp protein cơ bắp.",
                "Muscular Endurance: Weighted Step-Ups": "Muscular Endurance: Bước lên bục với tạ",
                "Muscular Endurance: Bodyweight Step-Ups": "Muscular Endurance: Bước lên bục không tạ",
                "Simulates climbing demands for your event (": "Mô phỏng nhu cầu leo dốc cho sự kiện của bạn (",
                "m total gain).": "m tổng độ cao).",
                "Consume electrolytes. Keep hydration nearby during strength efforts.": "Bổ sung điện giải. Luôn để sẵn nước bên cạnh khi tập luyện sức mạnh.",
                "Muscular Endurance: Hill Bounds": "Muscular Endurance: Nhảy dốc bùng nổ (Hill Bounds)",
                "Muscular Endurance: Explosive Bounding": "Muscular Endurance: Nhảy bật bùng nổ (Explosive Bounding)",
                "Find a steep 10-15% grade hill. 6-8x repeats of 30 seconds explosive hill bounds. Walk down recovery.": "Tìm một ngọn dốc đứng 10-15%. Thực hiện 6-8 lần lặp lại nhảy dốc bùng nổ trong 30 giây. Đi bộ xuống dốc để phục hồi.",
                "No hills or treadmill available: 6-8x sets of 8-10 explosive bounding strides on flat ground, focusing on power and stride length. Full recovery between sets.": "Không có đồi hoặc máy chạy bộ (treadmill): Thực hiện 6-8 hiệp x 8-10 lần nhảy bật bùng nổ trên mặt đất phẳng, tập trung vào sức mạnh và độ dài bước chạy. Nghỉ hoàn toàn giữa các hiệp.",
                "Intense muscle breakdown: Consume 25g protein within 30 minutes of finishing.": "Cơ bắp hoạt động cường độ cao: Nạp 25g protein trong vòng 30 phút sau khi tập xong.",
                "Active Recovery Walk": "Đi bộ phục hồi chủ động",
                # Note: this description now embeds a dynamic minute count
                # (see t_str's regex substitutions below) instead of a fixed
                # exact string.
                "Recovery focus. Drink water.": "Tập trung phục hồi. Uống nước đầy đủ.",
                "Core & Hip Stability": "Bài tập Ổn định hông & Core",
                "Focus on glute activation, hip bridges, side planks, and calf raises. Essential for road injury prevention.": "Tập trung vào kích hoạt cơ mông, tư thế cây cầu (hip bridges), plank nghiêng (side planks), và nhón gót (calf raises). Cần thiết để phòng ngừa chấn thương khi chạy đường bằng.",
                "Protein-focused recovery snack.": "Bữa ăn nhẹ phục hồi tập trung vào protein.",
            }

            def t_str(s: str) -> str:
                if not s:
                    return s
                if s in vi_trans:
                    return vi_trans[s]
                # Partial match checks for dynamic string patterns
                for en_key, vi_val in vi_trans.items():
                    if en_key in s:
                        s = s.replace(en_key, vi_val)
                # Handle specific dynamic strings
                if "Building aerobic endurance for your" in s:
                    s = s.replace(
                        "Building aerobic endurance for your", "Xây dựng sức bền hiếu khí cho sự kiện"
                    ).replace(
                        "event. Keep a steady conversational effort. Target: cover around 30-40% of race distance.",
                        "của bạn. Giữ nỗ lực chạy đều đặn ở mức có thể trò chuyện. Mục tiêu: tích lũy khoảng 30-40% cự ly đua.",
                    )
                if (
                    "Steady long run. Keep effort conversational (Zone 2). Target: cover around 50-60% of your race distance"
                    in s
                ):
                    s = s.replace(
                        "Steady long run. Keep effort conversational (Zone 2). Target: cover around 50-60% of your race distance",
                        "Chạy dài ổn định. Giữ nỗ lực ở mức có thể trò chuyện (Zone 2). Mục tiêu: chạy khoảng 50-60% cự ly đua",
                    ).replace("to build specific fatigue resistance.", "để xây dựng sức bền chống mỏi cơ đặc thù.")
                if (
                    "Peak long run. Practice gear and race-day nutrition. Target: cover around 70-80% of your race distance"
                    in s
                ):
                    s = s.replace(
                        "Peak long run. Practice gear and race-day nutrition. Target: cover around 70-80% of your race distance",
                        "Bài chạy dài mô phỏng đỉnh cao. Tập dượt sử dụng trang thiết bị và dinh dưỡng & fueling ngày đua. Mục tiêu: chạy khoảng 70-80% cự ly đua",
                    )
                if "Execute" in s and "step-ups holding" in s:
                    s = (
                        s.replace("Execute", "Thực hiện")
                        .replace("step-ups holding", "lượt bước lên bục cao 30cm cầm theo")
                        .replace(
                            "of your body weight on a 30cm box. Simulates climbing demands for your event",
                            "trọng lượng cơ thể. Mô phỏng nhu cầu leo dốc cho sự kiện của bạn",
                        )
                    )
                if "Execute" in s and "bodyweight step-ups on a 30cm box, no added weight" in s:
                    s = s.replace("Execute", "Thực hiện").replace(
                        "bodyweight step-ups on a 30cm box, no added weight.",
                        "lượt bước lên bục cao 30cm, không cần tạ.",
                    )
                if (
                    "Find a steep 10-15% grade hill simulating your event. 8-10x repeats of 30 seconds explosive hill bounds to handle the"
                    in s
                ):
                    s = s.replace(
                        "Find a steep 10-15% grade hill simulating your event. 8-10x repeats of 30 seconds explosive hill bounds to handle the",
                        "Tìm một ngọn dốc đứng 10-15% mô phỏng sự kiện của bạn. Lặp lại 8-10 lần 30 giây nhảy dốc bùng nổ để thích nghi với",
                    ).replace("of race vertical. Walk down recovery.", "độ dốc của cuộc đua. Đi bộ xuống để phục hồi.")
                if (
                    "No hills or treadmill available: 6-8x sets of 8-10 explosive bounding strides on flat ground to build the power needed for the"
                    in s
                ):
                    s = s.replace(
                        "No hills or treadmill available: 6-8x sets of 8-10 explosive bounding strides on flat ground to build the power needed for the",
                        "Không có đồi hoặc máy chạy bộ (treadmill): Thực hiện 6-8 hiệp x 8-10 lần nhảy bật bùng nổ trên mặt đất phẳng để xây dựng sức mạnh cần thiết cho",
                    ).replace(
                        "of race vertical. Full recovery between sets.",
                        "độ dốc của cuộc đua. Nghỉ hoàn toàn giữa các hiệp.",
                    )
                # Dynamic Tempo/Interval/Taper-walk descriptions (see
                # _warmup_cooldown_minutes) embed minute counts that scale
                # with the day's duration -- translate around the numbers.
                s = _re.sub(
                    r"Warmup (\d+)m\. Run at moderate tempo pace \(Zone 3\) for (\d+) minutes\. Cooldown (\d+)m\.",
                    r"Khởi động \1 phút. Chạy ở tốc độ tempo vừa phải (Zone 3) trong \2 phút. Thả lỏng \3 phút.",
                    s,
                )
                s = _re.sub(
                    r"Warmup (\d+)m\. Repeat (\d+)x(\d+) minutes at Zone 4 effort\. "
                    r"Recover with (\d+) minutes light jog between\. Cooldown (\d+)m\.",
                    r"Khởi động \1 phút. Lặp lại \2 lần \3 phút ở mức nỗ lực Zone 4. "
                    r"Đi bộ hoặc chạy nhẹ phục hồi \4 phút giữa các tổ. Thả lỏng \5 phút.",
                    s,
                )
                s = _re.sub(
                    r"Restorative (\d+)-minute light walk or hike on soft trail\.",
                    r"Đi bộ phục hồi nhẹ nhàng \1 phút trên đường trail mềm.",
                    s,
                )
                return s

            for wo in workouts:
                wo["title"] = t_str(wo.get("title", ""))
                wo["description"] = t_str(wo.get("description", ""))
                wo["fueling_tip"] = t_str(wo.get("fueling_tip", ""))

        return post_process_workouts(workouts)
