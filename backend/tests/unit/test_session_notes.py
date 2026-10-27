"""About this session: the AI's notes survive the guards, a guard explains its own change, every session has notes."""

import asyncio
import json
import re
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from config import settings
from services import plan_generator
from services.plan_generator import PlanGenerator, hm, join_notes, parse_notes, without_session_numbers

START = date(2026, 10, 19)  # a Monday
AI_NOTES = (
    " Overall: AI-OVERALL summary of the session. Reason: AI-REASON why it is scheduled now."
    " Benefit: AI-BENEFIT expected adaptation. Warning: AI-WARNING injury precautions."
)
LABELS = r" (?:Overall|Tổng quan):"


def test_notes_round_trip_and_vietnamese_labels_map_to_the_apps():
    notes = parse_notes(" Tổng quan: Nhẹ. Lý do: Tuần 3. Lợi ích: Nền aerobic. Lưu ý: Dừng nếu đau.")
    assert notes == {"Overall": "Nhẹ.", "Reason": "Tuần 3.", "Benefit": "Nền aerobic.", "Warning": "Dừng nếu đau."}
    assert join_notes({"Warning": "w.", "Overall": "o."}) == " Overall: o. Warning: w."


def test_stale_session_numbers_are_dropped_but_zones_stay():
    text = "A 90 min run in Zone 2. It builds your base. Climb 600 m D+ steady."
    assert without_session_numbers(text) == "It builds your base."
    assert hm(50) == "50 min" and hm(210) == "3 h 30" and hm(240, vi=True) == "4 h" and hm(45, vi=True) == "45 phút"


@pytest.fixture
def ai_plan(monkeypatch):
    """A 100 km mountain plan whose AI draft (the rules' own sessions, each with full notes) runs the guards."""
    monkeypatch.setattr(settings, "PLAN_DEMANDS_ENABLED", True)
    monkeypatch.setattr(settings, "PLAN_LINT_ENABLED", False)
    monkeypatch.setattr(settings, "PLAN_LLM_PROVIDER", "gemini")
    monkeypatch.setattr(plan_generator, "get_plan_workouts", lambda plan_id: [])

    def build(weeks, lang="en", edit=None):
        race_info = {
            "name": "VHT 100K",
            "date": (START + timedelta(weeks=weeks - 2, days=5)).isoformat(),
            "plan_start_date": START.isoformat(),
            "terrain": "trail",
            "course_distance_km": 104.2,
            "course_elevation_gain_m": 5533,
            "goal_type": "finish",
            "preferred_days": ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "long_run_day": "Saturday",
            "days_per_week": 6,
            "training_environment": "flat",
            "training_mountain": "nui_dinh",
            "mountain_days": json.dumps(["Saturday"]),
            "athlete_tier": "recreational",
            "lang": lang,
        }
        user = {"max_hr": 185, "resting_hr": 55, "zone2_pace_min": "6:30", "zone2_pace_max": "5:45",
                "current_weekly_km": 60.0, "aet_hr": 159, "ant_hr": 174, "threshold_source": "field", "lang": lang}  # fmt: skip
        kw = dict(plan_id=0, user_profile=user, race_info=race_info, total_weeks=weeks, cutoff_time_hours=29,
                  block_number=1, weeks_per_block=weeks)  # fmt: skip
        rules, _ = asyncio.run(PlanGenerator.generate_plan_workouts(api_key=None, **kw))
        draft = [
            {**w, "description": re.split(LABELS, w.get("description") or "")[0] + AI_NOTES}
            if w.get("type") != "Rest"
            else w
            for w in rules
        ]
        if edit:
            draft = edit(draft)
        resp = MagicMock(text=json.dumps(draft), candidates=[])
        client = MagicMock()
        client.models.generate_content.return_value = resp
        with (
            patch("google.genai.Client", return_value=client),
            patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
            patch("services.race_history.prompt_summary", return_value=""),
            patch("services.race_history.tier_distance", return_value=None),
        ):
            out, _ = asyncio.run(PlanGenerator.generate_plan_workouts(api_key="fake", **kw))
        assert client.models.generate_content.called
        return [w for w in out if w.get("type") != "Rest" and float(w.get("duration_minutes") or 0) > 0]

    return build


@pytest.mark.parametrize("lang", ["en", "vi"])
def test_ai_notes_survive_the_guards(ai_plan, lang):
    sessions = ai_plan(20, lang)
    kept = [w for w in sessions if "AI-BENEFIT" in w["description"] and "AI-WARNING" in w["description"]]
    assert len(kept) >= 0.9 * len(sessions)
    longs = [w for w in sessions if w["type"] == "Long Run"]
    assert all("AI-BENEFIT" in w["description"] for w in longs)  # the ladder resizes them; the notes stay
    assert "_why" not in {k for w in sessions for k in w}


def test_a_guard_explains_its_change_with_the_runners_numbers(ai_plan):
    sessions = ai_plan(20)
    ladder = [w for w in sessions if "of your long-run ladder:" in w["description"]]
    assert ladder and all("AI-REASON" not in w["description"] for w in ladder)  # one Reason: the guard's
    assert any(re.search(r"Week \d+ of your long-run ladder: \d+ h", w["description"]) for w in ladder)


def test_every_session_reaches_the_app_with_all_four_notes(ai_plan):
    for w in ai_plan(13):
        notes = parse_notes(w["description"])
        need = ("Overall", "Warning") if w["type"] == "Race" else plan_generator.NOTE_KEYS
        assert all(notes.get(k) for k in need), (w["week_number"], w["title"])


def test_a_lengthened_easy_run_keeps_its_zone_and_strides(ai_plan):
    # prod plan 138: a 40 min Zone 1 run with strides was raised to the weekday minimum and came back as
    # "steady Zone 2" with no strides, under notes that still described the strides
    def short_strides_run(draft):
        wo = next(w for w in draft if w["week_number"] == 1 and w["day_of_week"] == "Wednesday")
        wo.update(type="Easy", target_zone="Zone 1", duration_minutes=40, title="Easy Zone 1 Run with Strides",
                  description="Warm-up 10 min easy → 20 min very easy Zone 1 → 6 x 20s relaxed strides, 60s jog "
                  "→ Cool-down 5 min easy." + AI_NOTES)  # fmt: skip
        return draft

    wo = next(w for w in ai_plan(13, edit=short_strides_run) if w["title"] == "Easy Zone 1 Run with Strides")
    steps = wo["description"].split(" Overall:")[0]
    assert wo["duration_minutes"] > 40 and "Zone 1" in steps and "Zone 2" not in steps
    assert "6 x 20s relaxed strides" in steps and "fueling" not in steps
    assert "AI-BENEFIT" in wo["description"]


def test_a_note_sentence_with_an_invented_number_is_dropped():
    desc = "Warm-up 10 min → 40 min Zone 2. Reason: You ran 42 km last week. It lifts VO2 by 12%. Benefit: Zone 2 base."
    text, dropped = plan_generator.ground_notes(desc, {"10", "40", "42"})
    assert dropped == 1 and "12%" not in text and "42 km" in text and "Benefit: Zone 2 base." in text
