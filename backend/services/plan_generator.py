from datetime import datetime, timedelta
from typing import Any

from services.training_rules import TrainingRules


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
    def estimate_pace_zones(zone2_min_str: str, zone2_max_str: str) -> dict[str, str]:
        """
        Estimates all 5 pace zones based on Zone 2 min/max bounds using standard ratios.
        Ratios are anchored on the fast-end of Zone 2 (zone2_max).
        """
        z2_min = PlanGenerator.parse_pace_to_decimal(zone2_min_str or "6:30")
        z2_max = PlanGenerator.parse_pace_to_decimal(zone2_max_str or "5:45")

        # Calculate other zones based on z2_max (fast end)
        z1_dec = z2_max * 1.15
        z2_dec = (z2_min + z2_max) / 2.0
        z3_dec = z2_max * 0.90
        z4_dec = z2_max * 0.82
        z5_dec = z2_max * 0.73

        return {
            "zone1_pace": PlanGenerator.decimal_to_pace_str(z1_dec),
            "zone2_pace": f"{zone2_min_str or '6:30'} - {zone2_max_str or '5:45'}",
            "zone2_pace_mid": PlanGenerator.decimal_to_pace_str(z2_dec),
            "zone3_pace": PlanGenerator.decimal_to_pace_str(z3_dec),
            "zone4_pace": PlanGenerator.decimal_to_pace_str(z4_dec),
            "zone5_pace": PlanGenerator.decimal_to_pace_str(z5_dec),
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
        block_start_week = (block_number - 1) * weeks_per_block + 1
        block_end_week = min(block_start_week + weeks_per_block - 1, total_weeks)

        # 1. Base Variables Extract
        lang = race_info.get("lang", "en").lower()
        age = int(user_profile.get("age", 30))
        max_hr = int(user_profile.get("max_hr", 220 - age))
        resting_hr = int(user_profile.get("resting_hr", 60))

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

        # Calculate Heart Rate Zones
        hr_zones = TrainingRules.calculate_heart_rate_zones(max_hr, resting_hr)
        z1_range = f"{hr_zones['Zone 1']['min']}-{hr_zones['Zone 1']['max']} bpm"
        z2_range = f"{hr_zones['Zone 2']['min']}-{hr_zones['Zone 2']['max']} bpm"
        z3_range = f"{hr_zones['Zone 3']['min']}-{hr_zones['Zone 3']['max']} bpm"
        z4_range = f"{hr_zones['Zone 4']['min']}-{hr_zones['Zone 4']['max']} bpm"

        terrain = race_info.get("terrain", "trail").lower()
        use_treadmill = user_profile.get("use_treadmill", False)

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

        # Extract Zone 2 bounds and calculate estimated pacing zones
        z2_min = user_profile.get("zone2_pace_min") or "6:30"
        z2_max = user_profile.get("zone2_pace_max") or "5:45"
        est_zones = PlanGenerator.estimate_pace_zones(z2_min, z2_max)

        p_z1 = est_zones["zone1_pace"]
        p_z2 = est_zones["zone2_pace"]  # Range representation for prompt, e.g. "6:30 - 5:45"
        p_z2_mid = est_zones["zone2_pace_mid"]  # Midpoint representation, e.g. "6:08"
        p_z3 = est_zones["zone3_pace"]
        p_z4 = est_zones["zone4_pace"]
        p_z5 = est_zones["zone5_pace"]

        d_z1 = PlanGenerator.parse_pace_to_decimal(p_z1)
        d_z2 = PlanGenerator.parse_pace_to_decimal(p_z2_mid)
        d_z3 = PlanGenerator.parse_pace_to_decimal(p_z3)
        d_z4 = PlanGenerator.parse_pace_to_decimal(p_z4)
        d_z5 = PlanGenerator.parse_pace_to_decimal(p_z5)

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

                if "treadmill_incline" in wo and wo["treadmill_incline"] is not None:
                    try:
                        wo["treadmill_incline"] = float(wo["treadmill_incline"])
                    except Exception:
                        wo["treadmill_incline"] = 0.0
                if "treadmill_speed" in wo and wo["treadmill_speed"] is not None:
                    try:
                        wo["treadmill_speed"] = float(wo["treadmill_speed"])
                    except Exception:
                        wo["treadmill_speed"] = 0.0

                # Reset Rest/Strength/ME — always zero distance, never inherit AI value
                if w_type in ("Rest", "Strength", "Muscular Endurance") or dur <= 0.0:
                    wo["target_pace"] = ""
                    wo["distance_km"] = 0.0
                    continue

                # Race / Target Race: use the known course distance and goal pace
                title_lower = wo.get("title", "").lower()
                if ("target race" in title_lower or w_type == "Race") and course_distance_km:
                    wo["distance_km"] = float(course_distance_km)
                    # Use goal race pace derived from target finish time; fall back to Zone 4
                    wo["target_pace"] = f"{goal_race_pace_str or p_z4} /km"
                    continue

                # Map zone to decimal pace and label (always recalculate, discard AI distance)
                if "zone 1" in zone.lower():
                    pace_dec = d_z1
                    pace_str = p_z1
                elif "zone 3" in zone.lower():
                    pace_dec = d_z3
                    pace_str = p_z3
                elif "zone 4" in zone.lower():
                    pace_dec = d_z4
                    pace_str = p_z4
                elif "zone 5" in zone.lower():
                    pace_dec = d_z5
                    pace_str = p_z5
                else:  # Zone 2 default
                    pace_dec = d_z2
                    pace_str = p_z2_mid

                wo["target_pace"] = f"{pace_str} /km"
                # Always recalculate distance from duration + pace (never use AI's value)
                wo["distance_km"] = round(dur / pace_dec, 1) if pace_dec > 0 else 0.0
            return wos

        # 2. AI Plan Generation (NotebookLM → Gemini → Rule-Based)
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

        notebook_id = settings.NOTEBOOKLM_NOTEBOOK_ID
        auth_json = settings.NOTEBOOKLM_AUTH_JSON

        # Build shared AI prompt (used by both NotebookLM and Gemini paths)
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

            user_summary = (
                f"Age: {age}, Weekly volume base: {current_weekly_km} km, Max HR: {max_hr} bpm, "
                f"Resting HR: {resting_hr} bpm, AeT: {aet_hr} bpm, AnT: {ant_hr} bpm, Treadmill Access: {use_treadmill}\n"
                f"Custom Pace Zones (min/km):\n"
                f"- Zone 1 (Recovery): {p_z1}\n"
                f"- Zone 2 (Easy Range): {p_z2}\n"
                f"- Zone 3 (Tempo): {p_z3}\n"
                f"- Zone 4 (Threshold): {p_z4}\n"
                f"- Zone 5 (Interval): {p_z5}"
                f"{scheduling_notes}"
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

            if is_event_goal:
                program_summary = (
                    f"Race Name: {race_info.get('name')}, Date: {race_info.get('date')}, Terrain: {terrain}, "
                    f"Distance: {course_distance_km} km, Elevation Gain: {course_elevation_gain_m} m. "
                    f"{goal_description}"
                )
            else:
                program_summary = (
                    f"Training Plan Name: {race_info.get('name')}, Focus: {race_info.get('goal_type')}. "
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

            total_blocks = (total_weeks + weeks_per_block - 1) // weeks_per_block
            block_scope_instruction = (
                f"\nSEQUENTIAL BLOCK GENERATION:\n"
                f"This plan spans {total_weeks} weeks total, generated in {total_blocks} blocks of {weeks_per_block} weeks each.\n"
                f"Generate ONLY Block {block_number} of {total_blocks}: weeks {block_start_week} through {block_end_week}.\n"
                f"CRITICAL: Every workout `week_number` MUST be between {block_start_week} and {block_end_week} (inclusive). Do NOT output week numbers outside this range.\n"
            )
            # Kept separate from block_scope_instruction (and placed last in the final prompt below):
            # this is free-text athlete feedback of unbounded length, and NotebookLM truncates the
            # full prompt at ~3800 chars — the schema and hard constraints must survive truncation
            # even if this section gets cut off.
            feedback_instruction = ""
            if block_context:
                feedback_instruction = (
                    f"\nATHLETE FEEDBACK FROM PREVIOUS BLOCKS:\n{block_context}\n"
                    "CRITICAL — adjust this block based on feedback above:\n"
                    "  • RPE ≥ 8: reduce weekly volume by 10-15% AND drop one quality session to easy running.\n"
                    "  • RPE 6-7: reduce intensity slightly (shift a Tempo to Zone 2, or shorten intervals by 10%).\n"
                    "  • RPE 4-5: maintain current progression — athlete is adapting well.\n"
                    "  • RPE ≤ 3: athlete is underloaded — increase long run by 10-15% or add a quality session.\n"
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

            lang_rule = (
                "\n5. CRITICAL: All workout text fields, including 'title', 'description', and 'fueling_tip', MUST be written in Vietnamese."
                if lang == "vi"
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
                "   - `type` (string: 'Easy', 'Tempo', 'Interval', 'Long Run', 'Strength', 'Rest', 'Race', 'Recovery', 'Muscular Endurance')\n"
                "   - `duration_minutes` (number: duration of workout)\n"
                "   - `target_zone` (string: 'Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5')\n"
                "   - `target_hr_range` (string: heart rate bounds based on athlete's thresholds, e.g. '125-140 bpm')\n"
                "   - `target_pace` (string: recommended target pace, matching or referencing their custom pace zones, e.g. '6:00 /km')\n"
                "   - `distance_km` (number: estimated distance in kilometers. Calculate this as duration_minutes / (target_pace in decimal minutes), e.g. 60 mins at 6:00/km is 10.0 km)\n"
                "   - `description` (string: highly detailed description containing specific sections: Process (how to execute it step-by-step), Overall (summary of the session), Reason (why it is scheduled now), Benefit (expected physiological adaptation), and Warning (any injury risks or precautions). Provide extensive context.)\n"
                "   - `fueling_tip` (string: hydration, carbohydrate, and electrolyte guides specific to duration/intensity)\n"
                "   - `treadmill_incline` (number, optional: recommended incline percentage if using treadmill)\n"
                "   - `treadmill_speed` (number, optional: recommended speed in kph if using treadmill)\n"
                "   - `session_slot` (string, optional: ONLY set this on double-session days. Use 'morning' for the first/shorter session and 'afternoon' for the main/longer session. Omit entirely for single-session days.)\n\n"
                f"{block_scope_instruction}"
                f"{_start_date_constraint}"
                f"{week_schedule_constraints}"
                "\nRules:\n"
                "1. Generate workouts for the specified block weeks only. Each week must have structured workouts (typically 4-6 workouts per week). ALWAYS honor the athlete's preferred training days and double-session days from their profile — place Rest workouts on non-preferred days, and produce two workout objects on each double-session day as described above.\n"
                "2. Make the plan highly customized. For example, scale long runs, map Sunday Muscular Endurance box steps/weighted step-ups based on the race elevation gain, or specify treadmill incline/speed settings for gym workouts.\n"
                "3. NEVER invent a physiological claim, exercise, or number beyond what the Uphill Athlete training philosophy implies. If unsure of an exact figure, give a sensible range instead of fabricating false precision.\n"
                "4. Give the athlete profile and prior feedback below real weight — this plan MUST reflect their specific numbers, schedule, and history, not a generic template.\n"
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

        # NotebookLM has a strict query-size limit (~4000 chars). The full prompt is always sent
        # to Gemini, but for NotebookLM we cap it so block 2+ (which carry block_context) don't
        # silently return an empty streaming response.
        _NOTEBOOKLM_MAX_CHARS = 3800
        _nb_query = _ai_prompt[:_NOTEBOOKLM_MAX_CHARS] if _ai_prompt else None

        if _nb_query and notebook_id and auth_json:
            try:
                from services.notebooklm_service import NotebookLmService

                truncated = len(_ai_prompt) > _NOTEBOOKLM_MAX_CHARS
                print(
                    f"[PlanGen][NotebookLM] Sending prompt to notebook {notebook_id[:8]}... "
                    f"({len(_nb_query)} chars{', truncated from ' + str(len(_ai_prompt)) if truncated else ''})"
                )
                response_text = await NotebookLmService.query_notebook(
                    notebook_id=notebook_id, auth_json=auth_json, query=_nb_query, service="plan_generator"
                )
                print(f"[PlanGen][NotebookLM] Response received ({len(response_text)} chars)")
                clean_text = _extract_json_array(response_text)
                try:
                    ai_workouts = _json.loads(clean_text)
                except _json.JSONDecodeError as json_err:
                    print(f"[PlanGen][NotebookLM] JSON parsing failed: {json_err}. Raw snippet: {response_text[:200]}")
                    ai_workouts = None
                if isinstance(ai_workouts, list) and len(ai_workouts) > 0:
                    cleaned_wos = [wo for wo in ai_workouts if isinstance(wo, dict)]
                    print(f"[PlanGen][NotebookLM] Parsed {len(cleaned_wos)} workouts")
                    return post_process_workouts(cleaned_wos)
                else:
                    print("[PlanGen][NotebookLM] Empty or invalid list returned, trying Gemini fallback.")
            except Exception as ex:
                err_str = str(ex)
                if "No parseable chunks" in err_str or "empty" in err_str.lower():
                    print(
                        "[PlanGen][NotebookLM] Empty streaming response — prompt may still be too large, "
                        "or auth token expired (update NOTEBOOKLM_AUTH_JSON). Falling back to Gemini."
                    )
                else:
                    print(f"[PlanGen][NotebookLM] FAILED: {ex}. Trying Gemini fallback.")

        if _ai_prompt and api_key:
            try:
                import asyncio

                import google.generativeai as _genai

                _genai.configure(api_key=api_key)
                _model = _genai.GenerativeModel("gemini-2.5-flash")
                print(f"[PlanGen][Gemini] Sending prompt ({len(_ai_prompt)} chars)...")
                _response = await asyncio.to_thread(_model.generate_content, _ai_prompt)
                clean_text = _extract_json_array(_response.text)
                try:
                    ai_workouts = _json.loads(clean_text)
                except _json.JSONDecodeError as json_err:
                    print(f"[PlanGen][Gemini] JSON parsing failed: {json_err}. Raw snippet: {_response.text[:200]}")
                    ai_workouts = None
                if isinstance(ai_workouts, list) and len(ai_workouts) > 0:
                    cleaned_wos = [wo for wo in ai_workouts if isinstance(wo, dict)]
                    print(f"[PlanGen][Gemini] Parsed {len(cleaned_wos)} workouts")
                    return post_process_workouts(cleaned_wos)
                else:
                    print("[PlanGen][Gemini] Empty or invalid list returned, using rule-based fallback.")
            except Exception as ex:
                print(f"[PlanGen][Gemini] FAILED: {ex}. Using rule-based fallback schedule.")

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
                desc = "Warmup 10m. Repeat 4x3 minutes at Zone 4 effort. Recover with 2 minutes light jog between."
                fuel_tip = "High intensity workout: Consume a fast-absorbing energy gel 15 minutes before starting."
            else:
                title = "Aerobic Tempo Session"
                w_type = "Tempo"
                zone = "Zone 3"
                hr_range = z3_range
                pace = f"{p_z3} /km"
                desc = "Warmup 10m. Run at moderate tempo pace (Zone 3) for 20-30 minutes. Cooldown 10m."
                fuel_tip = "Consume electrolytes during the workout. Take 1 gel mid-session."

            workouts.append(
                {
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
            )

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
                        title = "Muscular Endurance: Weighted Step-Ups"
                        w_type = "Muscular Endurance"
                        weight_pct = 10 if week <= 6 else 15
                        steps = 400 + (100 * (week - num_base_weeks - 1))
                        if course_elevation_gain_m and course_elevation_gain_m > 0:
                            steps += int(course_elevation_gain_m / 10)
                        steps = min(1200, steps)
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
                    elif phase == "Peak":
                        title = "Muscular Endurance: Hill Bounds"
                        w_type = "Muscular Endurance"
                        desc = "Find a steep 10-15% grade hill. 6-8x repeats of 30 seconds explosive hill bounds. Walk down recovery."
                        if course_elevation_gain_m and course_elevation_gain_m > 0:
                            desc = f"Find a steep 10-15% grade hill simulating your event. 8-10x repeats of 30 seconds explosive hill bounds to handle the {course_elevation_gain_m}m of race vertical. Walk down recovery."
                        fuel_tip = "Intense muscle breakdown: Consume 25g protein within 30 minutes of finishing."
                    else:
                        title = "Active Recovery Walk"
                        w_type = "Recovery"
                        desc = "Restorative 30-minute light walk or hike on soft trail."
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
                "Recovery Zone Run": "Chạy phục hồi nhẹ nhàng",
                "Active recovery run. Keep effort extremely light and comfortable.": "Chạy phục hồi chủ động. Giữ nỗ lực cực kỳ nhẹ nhàng và thoải mái.",
                "Hydrate with water. No additional intra-workout carbs required.": "Bổ dung nước lọc. Không cần nạp thêm tinh bột trong khi chạy.",
                "Restorative Mobility": "Di động khớp phục hồi",
                "No running. Focus on full-body mobility, gentle stretching, and hydration.": "Không chạy. Tập trung vào vận động khớp toàn thân, giãn cơ nhẹ nhàng và bổ sung nước.",
                "Eat high-protein, nutrient-dense foods to rebuild muscle tissues.": "Ăn thực phẩm giàu protein, giàu dinh dưỡng để tái tạo mô cơ.",
                "Aerobic Power Intervals": "Bài tập Interval sức mạnh hiếu khí",
                "Warmup 10m. Repeat 4x3 minutes at Zone 4 effort. Recover with 2 minutes light jog between.": "Khởi động 10 phút. Lặp lại 4 lần 3 phút ở mức nỗ lực Zone 4. Đi bộ hoặc chạy nhẹ phục hồi 2 phút giữa các tổ.",
                "High intensity workout: Consume a fast-absorbing energy gel 15 minutes before starting.": "Bài tập cường độ cao: Nạp 1 gel năng lượng hấp thu nhanh 15 phút trước khi bắt đầu.",
                "Aerobic Tempo Session": "Bài chạy Aerobic Tempo",
                "Warmup 10m. Run at moderate tempo pace (Zone 3) for 20-30 minutes. Cooldown 10m.": "Khởi động 10 phút. Chạy ở tốc độ tempo vừa phải (Zone 3) trong 20-30 phút. Thả lỏng 10 phút.",
                "Consume electrolytes during the workout. Take 1 gel mid-session.": "Bổ sung điện giải trong khi chạy. Nạp 1 gel năng lượng ở giữa buổi.",
                "Easy Recovery Spin or Walk": "Đạp xe nhẹ phục hồi hoặc đi bộ",
                "30-minute light walk, swim, or easy spin. Keep heart rate strictly in Zone 1.": "30 phút đi bộ nhẹ, bơi hoặc đạp xe nhẹ nhàng. Giữ nhịp tim nghiêm ngặt trong Zone 1.",
                "Drink plenty of water and electrolytes to rehydrate after target event.": "Uống nhiều nước và điện giải để bổ sung nước sau sự kiện mục tiêu.",
                "Aerobic Capacity Run": "Bài chạy tích lũy hiếu khí",
                "Steady continuous run. Targets mitochondrial development and fat oxidation efficiency.": "Chạy đều liên tục. Nhằm phát triển ti thể và tăng hiệu quả đốt cháy chất béo.",
                "Practice gut-training: take 30g carbs per hour if workout exceeds 60 minutes.": "Luyện tập hệ tiêu hóa: nạp 30g tinh bột mỗi giờ nếu buổi chạy kéo dài hơn 60 phút.",
                "Rest & Mobilize": "Nghỉ ngơi & Vận động nhẹ",
                "Rest day. Light yoga, mobility drills, or foam rolling.": "Ngày nghỉ. Tập yoga nhẹ nhàng, các bài tập linh hoạt khớp hoặc dùng con lăn giãn cơ (foam roller).",
                "Standard nutrition. Keep baseline hydration levels consistent.": "Dinh dưỡng tiêu chuẩn. Giữ mức bổ sung nước cơ bản nhất quán.",
                "Post-Race Gentle Hike": "Đi bộ nhẹ phục hồi sau đua",
                "Short restorative walk or light hike on flat, soft terrain. Enjoy the fresh air.": "Đi bộ ngắn phục hồi hoặc đi bộ dã ngoại nhẹ nhàng trên địa hình phẳng, mềm. Tận hưởng không khí trong lành.",
                "Focus on clean foods. Hydrate normally.": "Tập trung vào thực phẩm sạch. Bổ sung nước bình thường.",
                "TARGET EVENT: ": "SỰ KIỆN MỤC TIÊU: ",
                "Race day! Execute pacing strategy for your ": "Ngày chạy đua! Thực hiện chiến lược phân phối tốc độ cho sự kiện ",
                "km event, maintain fueling targets, and enjoy the run.": "km của bạn, duy trì các mục tiêu nạp năng lượng và tận hưởng cuộc đua.",
                "RACE FUELING: Target 60-90g carbs/hr, and 500-700mg sodium/hr. Stick to tested products.": "DINH DƯỠNG NGÀY ĐUA: Mục tiêu nạp 60-90g tinh bột/giờ, và 500-700mg natri/giờ. Chỉ dùng các sản phẩm đã thử nghiệm.",
                "Endurance Long Run": "Chạy dài bền bỉ",
                "Building aerobic endurance. Keep a steady conversational effort.": "Xây dựng sức bền hiếu khí. Giữ nỗ lực chạy đều đặn ở mức có thể trò chuyện.",
                "GUT TRAINING: Target 60g carbs/hour using gels and drink mixes to prepare your stomach.": "LUYỆN HỆ TIÊU HÓA: Mục tiêu nạp 60g tinh bột/giờ sử dụng gel và nước uống năng lượng để chuẩn bị cho dạ dày.",
                "GUT TRAINING: Target 30g carbs/hour using gels and drink mixes to prepare your stomach.": "LUYỆN HỆ TIÊU HÓA: Mục tiêu nạp 30g tinh bột/giờ sử dụng gel và nước uống năng lượng để chuẩn bị cho dạ dày.",
                "Rest & Recuperation": "Nghỉ ngơi & Phục hồi hoàn toàn",
                "Complete rest day. Spend time with family, sleep well, and let your body fully restore.": "Ngày nghỉ ngơi hoàn toàn. Dành thời gian cho gia đình, ngủ đủ giấc và để cơ thể phục hồi tối đa.",
                "Balanced recovery diet.": "Chế độ ăn phục hồi cân bằng.",
                "General Base Strength": "Bài tập Sức mạnh nền tảng",
                "Bodyweight routine: lunges, single-leg squats, and core stabilization. 3 sets of 12 reps.": "Bài tập sức nặng cơ thể: chùng chân (lunges), ngồi xổm một chân (single-leg squats), và ổn định cơ trọng tâm. 3 hiệp 12 lần lặp.",
                "Prepares muscles for the ": "Chuẩn bị cơ bắp cho nhu cầu leo dốc ",
                "m climbing demands.": "m của cuộc đua.",
                "Drink amino acids post-workout for protein synthesis.": "Uống axit amin sau khi tập để hỗ trợ tổng hợp protein cơ bắp.",
                "Muscular Endurance: Weighted Step-Ups": "Sức bền cơ bắp: Bước lên bục với tạ",
                "Simulates climbing demands for your event (": "Mô phỏng nhu cầu leo dốc cho sự kiện của bạn (",
                "m total gain).": "m tổng độ cao).",
                "Consume electrolytes. Keep hydration nearby during strength efforts.": "Bổ sung điện giải. Luôn để sẵn nước bên cạnh khi tập luyện sức mạnh.",
                "Muscular Endurance: Hill Bounds": "Sức bền cơ bắp: Nhảy dốc",
                "Find a steep 10-15% grade hill. 6-8x repeats of 30 seconds explosive hill bounds. Walk down recovery.": "Tìm một ngọn dốc đứng 10-15%. Thực hiện 6-8 lần lặp lại nhảy dốc bùng nổ trong 30 giây. Đi bộ xuống dốc để phục hồi.",
                "Intense muscle breakdown: Consume 25g protein within 30 minutes of finishing.": "Cơ bắp hoạt động cường độ cao: Nạp 25g protein trong vòng 30 phút sau khi tập xong.",
                "Active Recovery Walk": "Đi bộ phục hồi chủ động",
                "Restorative 30-minute light walk or hike on soft trail.": "Đi bộ phục hồi nhẹ nhàng 30 phút trên đường trail mềm.",
                "Recovery focus. Drink water.": "Tập trung phục hồi. Uống nước.",
                "Core & Hip Stability": "Bài tập Ổn định hông & Cơ trọng tâm",
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
                        "của bạn. Giữ nỗ lực chạy đều đặn ở mức có thể trò chuyện. Mục tiêu: chạy khoảng 30-40% cự ly đua.",
                    )
                if (
                    "Steady long run. Keep effort conversational (Zone 2). Target: cover around 50-60% of your race distance"
                    in s
                ):
                    s = s.replace(
                        "Steady long run. Keep effort conversational (Zone 2). Target: cover around 50-60% of your race distance",
                        "Chạy dài ổn định. Giữ nỗ lực ở mức có thể nói chuyện (Zone 2). Mục tiêu: chạy khoảng 50-60% cự ly đua",
                    ).replace("to build specific fatigue resistance.", "để xây dựng khả năng chống mệt mỏi đặc thù.")
                if (
                    "Peak long run. Practice gear and race-day nutrition. Target: cover around 70-80% of your race distance"
                    in s
                ):
                    s = s.replace(
                        "Peak long run. Practice gear and race-day nutrition. Target: cover around 70-80% of your race distance",
                        "Bài chạy dài đỉnh cao. Tập dượt sử dụng trang thiết bị và dinh dưỡng ngày đua. Mục tiêu: chạy khoảng 70-80% cự ly đua",
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
                if (
                    "Find a steep 10-15% grade hill simulating your event. 8-10x repeats of 30 seconds explosive hill bounds to handle the"
                    in s
                ):
                    s = s.replace(
                        "Find a steep 10-15% grade hill simulating your event. 8-10x repeats of 30 seconds explosive hill bounds to handle the",
                        "Tìm một ngọn dốc đứng 10-15% mô phỏng sự kiện của bạn. Lặp lại 8-10 lần 30 giây nhảy dốc bùng nổ để chịu đựng",
                    ).replace("of race vertical. Walk down recovery.", "độ dốc của cuộc đua. Đi bộ xuống để phục hồi.")
                return s

            for wo in workouts:
                wo["title"] = t_str(wo.get("title", ""))
                wo["description"] = t_str(wo.get("description", ""))
                wo["fueling_tip"] = t_str(wo.get("fueling_tip", ""))

        return post_process_workouts(workouts)
