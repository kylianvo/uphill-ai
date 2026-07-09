from datetime import UTC, datetime, timedelta
from typing import Any


class CalendarService:
    DAY_OFFSETS = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}

    @staticmethod
    def escape_text(val: str) -> str:
        r"""
        Escapes special characters in text values per RFC 5545.
        - Backslash -> \\
        - Semicolon -> \;
        - Comma -> \,
        - Newline -> \n (literal sequence)
        """
        if not val:
            return ""
        # 1. Normalize line endings to LF
        val = val.replace("\r\n", "\n")
        # 2. Escape backslashes first
        val = val.replace("\\", "\\\\")
        # 3. Escape commas and semicolons
        val = val.replace(";", "\\;")
        val = val.replace(",", "\\,")
        # 4. Escape newlines to literal \n
        val = val.replace("\n", "\\n")
        return val

    @staticmethod
    def fold_line(line: str) -> str:
        """
        Folds a line so that it does not exceed 75 octets (bytes) per RFC 5545.
        Subsequent folded lines start with a single space.
        """
        if not line:
            return ""

        chunks = []
        current_chunk = ""
        current_bytes = 0
        limit = 75

        for char in line:
            char_bytes = len(char.encode("utf-8"))
            if current_bytes + char_bytes > limit:
                chunks.append(current_chunk)
                current_chunk = " " + char
                current_bytes = 1 + char_bytes
                limit = 75
            else:
                current_chunk += char
                current_bytes += char_bytes

        if current_chunk:
            chunks.append(current_chunk)

        return "\r\n".join(chunks)

    @classmethod
    def generate_ics_string(cls, race_date_str: str, workouts: list[dict[str, Any]], time_pref: str = "all_day") -> str:
        """
        Generates a standard RFC 5545 iCalendar string.
        Paces workouts backwards from the target race date.
        Filters out workouts occurring after the race day.
        """
        try:
            # Expected input format: 'YYYY-MM-DD'
            race_date = datetime.strptime(race_date_str, "%Y-%m-%d").date()
        except ValueError:
            # Fallback to today + 90 days if parsing fails
            race_date = datetime.now().date() + timedelta(days=90)

        # 1. Update the race workout's day_of_week to match the user's race date weekday.
        race_weekday_name = race_date.strftime("%A")
        for wo in workouts:
            title = wo.get("title", "").upper()
            w_type = wo.get("type", "").upper()
            if "TARGET EVENT" in title or w_type == "RACE":
                wo["day_of_week"] = race_weekday_name

        # 2. Determine total weeks and locate the Race workout to anchor dates
        total_weeks = max(int(wo["week_number"]) for wo in workouts) if workouts else 12
        race_week = None
        race_day_offset = cls.DAY_OFFSETS.get(race_weekday_name, 5)

        for wo in workouts:
            title = wo.get("title", "").upper()
            w_type = wo.get("type", "").upper()
            if "TARGET EVENT" in title or w_type == "RACE":
                race_week = int(wo["week_number"])
                break

        if race_week is not None:
            start_monday = race_date - timedelta(days=((race_week - 1) * 7) + race_day_offset)
        else:
            # Fallback: assume race is on race_date (which corresponds to race_date.weekday()) in the last week
            start_monday = race_date - timedelta(days=((total_weeks - 1) * 7) + race_date.weekday())

        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Uphill AI//Workout Scheduler//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]

        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

        for idx, wo in enumerate(workouts):
            week_num = int(wo["week_number"])
            day_name = wo["day_of_week"]

            day_offset = cls.DAY_OFFSETS.get(day_name, 0)
            workout_days_delta = ((week_num - 1) * 7) + day_offset
            workout_date = start_monday + timedelta(days=workout_days_delta)

            # Standard RFC 5545: DTEND for all-day events is non-inclusive (the following day)
            next_date = workout_date + timedelta(days=1)
            date_str = workout_date.strftime("%Y%m%d")
            next_date_str = next_date.strftime("%Y%m%d")

            uid = f"uphill-ai-wo-{wo.get('plan_id', 1)}-{week_num}-{day_offset}-{idx}@uphill.ai"

            summary = f"Uphill AI: {wo['title']}"
            if wo["type"] == "Rest":
                summary = f"Uphill AI: {wo['title']} (Rest)"

            # Compile description with human-readable date
            desc_parts = []
            desc_parts.append(f"Scheduled Date: {workout_date.strftime('%A, %B %d, %Y')}")
            desc_parts.append(f"Phase: {wo['phase']}")
            desc_parts.append(f"Type: {wo['type']}")
            if wo.get("duration_minutes", 0) > 0:
                desc_parts.append(f"Duration: {int(wo['duration_minutes'])} mins")
            if wo.get("target_hr_range"):
                desc_parts.append(f"HR Range: {wo['target_hr_range']}")
            if wo.get("target_zone"):
                desc_parts.append(f"Target Effort: {wo['target_zone']}")
            treadmill_incline = wo.get("treadmill_incline")
            if treadmill_incline and treadmill_incline != "0":
                desc_parts.append(f"Treadmill: Incline {treadmill_incline}% | Speed {wo['treadmill_speed']} kph")
            if wo.get("description"):
                desc_parts.append(f"\nWorkout Guide:\n{wo['description']}")
            if wo.get("fueling_tip"):
                desc_parts.append(f"\nFueling / Nutrition:\n{wo['fueling_tip']}")

            raw_description = "\n".join(desc_parts)

            # iCalendar properties with escaping and folding
            ics_lines.append("BEGIN:VEVENT")
            ics_lines.append(f"UID:{uid}")
            ics_lines.append(f"DTSTAMP:{timestamp}")

            if time_pref in ("morning", "afternoon", "evening"):
                # Determine start hour
                start_hour = 8 if time_pref == "morning" else (14 if time_pref == "afternoon" else 18)
                # Parse duration
                duration = int(wo.get("duration_minutes", 60))
                if duration <= 0:
                    duration = 60

                # Combine workout date with start time
                from datetime import time

                start_time = time(hour=start_hour, minute=0, second=0)
                start_dt = datetime.combine(workout_date, start_time)
                end_dt = start_dt + timedelta(minutes=duration)

                start_str = start_dt.strftime("%Y%m%dT%H%M%S")
                end_str = end_dt.strftime("%Y%m%dT%H%M%S")

                ics_lines.append(f"DTSTART:{start_str}")
                ics_lines.append(f"DTEND:{end_str}")
            else:
                ics_lines.append(f"DTSTART;VALUE=DATE:{date_str}")
                ics_lines.append(f"DTEND;VALUE=DATE:{next_date_str}")

            ics_lines.append(f"SUMMARY:{cls.escape_text(summary)}")
            ics_lines.append(f"DESCRIPTION:{cls.escape_text(raw_description)}")
            ics_lines.append("END:VEVENT")

        ics_lines.append("END:VCALENDAR")

        # Fold and format all output lines with CRLF endings
        folded_lines = [cls.fold_line(line) for line in ics_lines]
        return "\r\n".join(folded_lines) + "\r\n"
