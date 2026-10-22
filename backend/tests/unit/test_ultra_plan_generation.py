"""Ultras trained on a mountain day follow Quang's ladder (services/ultra_rules.py), on the rule-based path."""

import asyncio
import json
from datetime import date, timedelta

import pytest

from config import settings
from services import plan_generator, plan_lint, ultra_rules
from services.plan_generator import PlanGenerator

START = date(2026, 10, 19)  # a Monday


@pytest.fixture
def rule_based_plan(monkeypatch):
    monkeypatch.setattr(settings, "PLAN_DEMANDS_ENABLED", True)
    monkeypatch.setattr(settings, "PLAN_LINT_ENABLED", False)
    monkeypatch.setattr(plan_generator, "get_plan_workouts", lambda plan_id: [])

    def build(km, weeks, mountain_days, tier, weekly_km=65, race_weekday=5, **profile):
        race_info = {
            "name": "VHT 100K",
            "date": (START + timedelta(weeks=weeks - 2, days=race_weekday)).isoformat(),
            "plan_start_date": START.isoformat(),
            "terrain": "trail",
            "course_distance_km": km,
            "course_elevation_gain_m": 5533,
            "goal_type": "finish",
            "preferred_days": ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "long_run_day": "Saturday",
            "days_per_week": 6,
            "training_environment": "flat",
            "training_mountain": "nui_dinh" if mountain_days else None,
            "mountain_days": json.dumps(mountain_days) if mountain_days else None,
            "athlete_tier": tier,
        }
        user = {
            "max_hr": 185,
            "resting_hr": 55,
            "zone2_pace_min": "6:30",
            "zone2_pace_max": "5:45",
            "current_weekly_km": float(weekly_km),
            **profile,
        }
        workouts, _ = asyncio.run(
            PlanGenerator.generate_plan_workouts(
                plan_id=0,
                user_profile=user,
                race_info=race_info,
                total_weeks=weeks,
                api_key=None,
                cutoff_time_hours=29,
                block_number=1,
                weeks_per_block=weeks,
            )
        )
        return workouts

    return build


def _longs(wos):
    return {w["week_number"]: w["duration_minutes"] for w in wos if w["type"] == "Long Run"}


def test_100k_mountain_plan_follows_ladder(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=["Saturday"], tier="recreational")
    longs = _longs(wos)
    assert longs[1] == 180 and longs[4] == 240 and longs[16] == 420
    assert max(longs.values()) <= 420
    weekday = [
        w
        for w in wos
        if w["type"] == "Easy"
        and w["day_of_week"] not in ("Saturday", "Sunday")
        and w["phase"] in ("Base", "Build", "Peak")
        and not ultra_rules.is_deload(w["week_number"], 20)
    ]
    assert weekday and all(60 <= w["duration_minutes"] <= 90 for w in weekday)
    assert not [w for w in wos if "back-to-back" in (w.get("title") or "").lower()]


def test_other_weekend_day_shrinks_after_a_long_mountain_day(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=["Saturday"], tier="recreational")
    longs = _longs(wos)
    for w in wos:
        if (
            w["day_of_week"] == "Sunday"
            and w["type"] in ("Easy", "Aerobic Capacity", "Recovery")
            and 3 <= w["week_number"] <= 16  # weeks 1-2: the start-load cap trims it
        ):
            # a ceiling: the deload, start-load and weekly-growth trims may cut it further
            assert w["duration_minutes"] <= ultra_rules.other_day_minutes(longs[w["week_number"]])


def test_short_plan_never_jumps_more_than_an_hour(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=8, mountain_days=["Saturday"], tier="recreational")
    longs = _longs(wos)
    for wk, minutes in longs.items():  # the step cap is measured against the last two weeks (a deload is not the base)
        recent = max((longs.get(wk - 1, 0), longs.get(wk - 2, 0)))
        assert not recent or minutes - recent <= 60


def test_no_mountain_day_unchanged(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=[], tier="recreational")
    assert max(_longs(wos).values()) <= 300


def test_no_me_in_6h_weeks(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=["Saturday"], tier="recreational")
    big = {n for n, m in _longs(wos).items() if m >= 360}
    assert big and not [w for w in wos if w["week_number"] in big and w["type"] == "Muscular Endurance"]


def _quality(wos):
    return [
        w
        for w in wos
        if plan_lint.is_hard(w)
        and w["type"] != "Race"
        and not any(k in (w.get("title") or "").lower() for k in plan_lint.NEUROMUSCULAR_KEYWORDS)
    ]


def test_ultra_quality_only_in_the_window(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=["Saturday"], tier="sub_elite", weekly_km=100,
                          aet_hr=150, ant_hr=160, threshold_source="lab")  # fmt: skip
    window = ultra_rules.quality_weeks(20)
    hard = _quality(wos)
    assert hard and all(w["week_number"] in window for w in hard)
    assert all(w["target_zone"] == "Zone 3" for w in hard)
    per_week = {wk: sum(1 for w in hard if w["week_number"] == wk) for wk in window}
    assert max(per_week.values()) == 2 and all(n <= 2 for n in per_week.values())


def test_gated_runner_gets_one_zone3_in_the_window(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=["Saturday"], tier="sub_elite", weekly_km=100,
                          aet_hr=140, ant_hr=170, threshold_source="lab")  # 18% gap: ADS  # fmt: skip
    hard = _quality(wos)
    window = ultra_rules.quality_weeks(20)
    assert hard and all(w["week_number"] in window and w["target_zone"] == "Zone 3" for w in hard)
    assert max(sum(1 for w in hard if w["week_number"] == wk) for wk in window) == 1


def _row(week, day, kind, minutes):
    return {"week_number": week, "day_of_week": day, "type": kind, "duration_minutes": minutes}


def test_rows_after_a_saturday_race_are_returned_for_rest():
    week = [_row(11, "Thursday", "Easy", 30), _row(11, "Saturday", "Race", 900), _row(11, "Sunday", "Recovery", 30)]
    assert plan_generator.rows_after_race(week + [_row(12, "Sunday", "Easy", 30)]) == [week[2]]


def test_a_sunday_race_has_nothing_after_it():
    week = [_row(11, "Saturday", "Easy", 20), _row(11, "Sunday", "Race", 900)]
    assert plan_generator.rows_after_race(week) == []
    assert plan_generator.rows_after_race([_row(3, "Sunday", "Easy", 30)]) == []


def test_model_prompt_carries_the_ladder_block(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import MagicMock, patch

    monkeypatch.setattr(settings, "PLAN_DEMANDS_ENABLED", True)
    monkeypatch.setattr(settings, "PLAN_LINT_ENABLED", False)
    monkeypatch.setattr(plan_generator, "get_plan_workouts", lambda plan_id: [])
    monkeypatch.setattr("services.kb_retrieval._client", lambda: None)
    client = MagicMock()
    client.models.generate_content.side_effect = RuntimeError("no model in tests")
    client.models.embed_content.return_value = SimpleNamespace(embeddings=[SimpleNamespace(values=[0.1])])
    race_info = {
        "name": "VHT 100K",
        "date": (START + timedelta(weeks=18, days=5)).isoformat(),
        "plan_start_date": START.isoformat(),
        "terrain": "trail",
        "course_distance_km": 104.2,
        "course_elevation_gain_m": 5533,
        "goal_type": "finish",
        "long_run_day": "Saturday",
        "days_per_week": 6,
        "mountain_days": json.dumps(["Saturday"]),
        "training_mountain": "nui_dinh",
        "athlete_tier": "recreational",
    }
    with patch("google.genai.Client", return_value=client):
        asyncio.run(
            PlanGenerator.generate_plan_workouts(
                plan_id=0,
                user_profile={"max_hr": 185, "resting_hr": 55, "current_weekly_km": 65.0},
                race_info=race_info,
                total_weeks=20,
                api_key="test-key",
                cutoff_time_hours=29,
                block_number=1,
                weeks_per_block=4,
            )
        )
    prompt = str(client.models.generate_content.call_args_list[0])
    assert "MOUNTAIN-DAY ULTRA RULES" in prompt and "Week 3: Long Run 240 min" in prompt
