"""Ultras trained on a mountain day follow Quang's ladder (services/ultra_rules.py), on the rule-based path."""

import asyncio
import json
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from config import settings
from services import plan_generator, plan_lint, ultra_rules
from services.athlete_tier import get_profile
from services.plan_generator import PlanGenerator

START = date(2026, 10, 19)  # a Monday


@pytest.fixture
def rule_based_plan(monkeypatch):
    monkeypatch.setattr(settings, "PLAN_DEMANDS_ENABLED", True)
    monkeypatch.setattr(settings, "PLAN_LINT_ENABLED", False)
    monkeypatch.setattr(plan_generator, "get_plan_workouts", lambda plan_id: [])

    def build(km, weeks, mountain_days, tier, weekly_km=65, race_weekday=5, race_extra=None, **profile):
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
            **(race_extra or {}),
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
    assert longs[1] == 180 and longs[4] == 180 and longs[16] == 420  # week 4: a rung below week 3
    assert max(longs.values()) <= 420
    weekday = [
        w
        for w in wos
        if w["type"] == "Easy"
        and not any(k in w["title"].lower() for k in plan_lint.NEUROMUSCULAR_KEYWORDS)  # sprints are short by design
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
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=["Saturday"], tier="elite", weekly_km=100,
                          aet_hr=150, ant_hr=160, threshold_source="lab")  # fmt: skip
    window = ultra_rules.quality_weeks(20)
    hard = [w for w in _quality(wos) if w["phase"] != "Taper"]  # the first taper week keeps a small dose
    assert hard and all(w["week_number"] in window for w in hard)
    assert all(w["target_zone"] == "Zone 3" for w in hard)
    per_week = {wk: sum(1 for w in hard if w["week_number"] == wk) for wk in window}
    assert max(per_week.values()) == 1  # elite tier, but ~100 km weeks: under 15 h, so the single dose


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
    assert "WEEKLY CLIMBING TARGET" in prompt and "- Week 1: about 600 m D+ (11% of race D+)" in prompt


def test_a_mid_plan_tune_up_race_does_not_rest_the_week():
    tune_up = [_row(6, "Wednesday", "Race", 120), _row(6, "Saturday", "Long Run", 180)]
    goal = [_row(12, "Saturday", "Race", 900), _row(12, "Sunday", "Recovery", 30)]
    assert plan_generator.rows_after_race(tune_up + goal) == [goal[1]]


def test_model_double_on_the_long_run_day_is_dropped(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import MagicMock, patch

    monkeypatch.setattr(settings, "PLAN_LINT_ENABLED", False)
    monkeypatch.setattr(plan_generator, "get_plan_workouts", lambda plan_id: [])
    monkeypatch.setattr("services.kb_retrieval._client", lambda: None)
    days = ["Tuesday", "Thursday", "Saturday", "Saturday", "Sunday"]
    kinds = ["Easy", "Tempo", "Easy", "Long Run", "Easy"]
    slots = [None, None, "morning", "afternoon", None]
    week = [
        {"week_number": 1, "day_of_week": d, "type": t, "title": t, "description": "Run", "duration_minutes": 45}
        | ({"session_slot": s} if s else {})
        for d, t, s in zip(days, kinds, slots)
    ]
    client = MagicMock()
    client.models.generate_content.return_value = SimpleNamespace(text=json.dumps(week))
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
        "days_per_week": 5,
        "mountain_days": json.dumps(["Saturday"]),
        "training_mountain": "nui_dinh",
        "athlete_tier": "recreational",
    }
    with patch("google.genai.Client", return_value=client):
        wos, _ = asyncio.run(
            PlanGenerator.generate_plan_workouts(
                plan_id=0,
                user_profile={"max_hr": 185, "resting_hr": 55, "current_weekly_km": 65.0},
                race_info=race_info,
                total_weeks=20,
                api_key="test-key",
                cutoff_time_hours=29,
                block_number=1,
                weeks_per_block=1,
            )
        )
    saturday = [w for w in wos if w["week_number"] == 1 and w["day_of_week"] == "Saturday"]
    assert [w["type"] for w in saturday] == ["Long Run"] and saturday[0]["session_slot"] == "main"


def test_flat_athlete_without_city_vertical_gets_flat_zone3_on_weekdays(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=["Saturday"], tier="sub_elite", weekly_km=100,
                          aet_hr=150, ant_hr=160, threshold_source="lab")  # fmt: skip
    weekday = [w for w in _quality(wos) if w["day_of_week"] != "Saturday"]
    assert weekday and all("treadmill" not in w["description"] and "stairs" not in w["description"] for w in weekday)
    assert not any("uphill" in w["title"].lower() for w in weekday)


def test_sub_elite_gets_one_zone3_and_the_window_is_labelled_build(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=13, mountain_days=["Saturday"], tier="sub_elite", weekly_km=50,
                          aet_hr=159, ant_hr=174, threshold_source="field")  # the 13-week plan from the bug  # fmt: skip
    window = ultra_rules.quality_weeks(13)
    hard = _quality(wos)
    assert hard and max(sum(1 for w in hard if w["week_number"] == wk) for wk in window) == 1
    assert all(w["phase"] != "Base" for w in wos if w["week_number"] in window)


def test_recovery_week_inside_the_window_keeps_the_build_label(rule_based_plan):
    """VHT 100K, 10 weeks: the week-4 recovery week sat between Build weeks labelled "Base" (persona run 2026-10-27)."""
    wos = rule_based_plan(km=104.2, weeks=11, mountain_days=["Saturday"], tier="sub_elite", weekly_km=100)
    window = ultra_rules.quality_weeks(11)
    assert ultra_rules.is_deload(4, 11) and 4 not in window and min(window) < 4 < max(window)
    assert {w["phase"] for w in wos if w["week_number"] == 4} == {"Build"}


def test_quality_dose_needs_elite_volume_and_keeps_zone3_under_9_percent():
    assert ultra_rules.quality_dose(True, False, 1200) == (2, 4, 12)  # 96 min of 1200 = 8%
    assert ultra_rules.quality_dose(True, False, 960) == (2, 3, 12)  # 4 reps would be 10%
    assert ultra_rules.quality_dose(True, False, 600) == (1, 3, 10)  # elite tier, 10 h week
    assert ultra_rules.quality_dose(False, False, 420) == (1, 3, 10)  # 30 min of 420 = 7%
    assert ultra_rules.quality_dose(False, True, 240) == (1, 2, 10)  # never below 20 min of work


def test_first_taper_week_keeps_a_small_zone3_dose(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=["Saturday"], tier="recreational", weekly_km=60,
                          aet_hr=159, ant_hr=174, threshold_source="field")  # fmt: skip
    taper = [w for w in wos if w["phase"] == "Taper"]
    first = min(w["week_number"] for w in taper)
    z3 = [w for w in taper if w.get("target_zone") == "Zone 3"]
    assert all(w["week_number"] == first for w in z3) and all(w["duration_minutes"] <= 45 for w in z3)


def test_short_plan_opens_with_me_weeks_then_zone3(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=13, mountain_days=["Saturday"], tier="recreational", weekly_km=50,
                          aet_hr=159, ant_hr=174, threshold_source="field")  # fmt: skip
    me_weeks = ultra_rules.me_first_weeks(13, legs_loaded=False)
    assert me_weeks == {1, 2, 3}
    for wk in me_weeks:
        rows = [w for w in wos if w["week_number"] == wk]
        assert sum(w["type"] == "Muscular Endurance" for w in rows) == 2
        assert not any(w.get("target_zone") == "Zone 3" for w in rows)
    z3_weeks = {w["week_number"] for w in _quality(wos) if w["phase"] != "Taper"}
    assert z3_weeks and z3_weeks <= {5, 6, 7, 9}
    assert not any(w["type"] == "Muscular Endurance" for w in wos if w["week_number"] in z3_weeks)  # Z3 replaces ME


def test_code_made_me_is_the_gym_progression_with_descents_as_a_step(rule_based_plan):
    """Plan 131: the ME day the ME-week rule adds read 3 x 12 rounds, and the descent work landed in About."""
    wos = rule_based_plan(km=104.2, weeks=13, mountain_days=["Saturday"], tier="recreational", weekly_km=50,
                          aet_hr=159, ant_hr=174, threshold_source="field")  # fmt: skip
    me = sorted((w for w in wos if w["type"] == "Muscular Endurance"), key=lambda w: w["week_number"])
    assert me and not any("Step-ups 3 x 12" in w["description"] for w in me)
    for w in me:
        steps = w["description"].split(" Overall:")[0]
        assert "3 x 10 slow step-downs per leg" in steps  # a step, not a note the app shows under About
        assert steps.rstrip(".").split(" → ")[-1].startswith("Cool-down")
    made = [w for w in me if w["title"] == "Muscular Endurance (ME)"]
    assert made and all(k in w["description"] for w in made for k in ("Reason:", "Benefit:", "Warning:"))
    assert "Split Jump Squats 4x10" in made[0]["description"]  # soft start


def test_me_first_weeks_rules():
    assert ultra_rules.me_first_weeks(8, legs_loaded=False) == {1, 2}  # never more than half the Zone 3 window
    assert ultra_rules.me_first_weeks(16, legs_loaded=False) == frozenset()  # long plans: ME block in Base
    assert ultra_rules.me_first_weeks(13, legs_loaded=True) == frozenset()  # climbing already loads the legs
    assert ultra_rules.legs_loaded(1600) and not ultra_rules.legs_loaded(None)


# Plan 131 (prod, 2026-10-26): 7 days a week, Tuesday doubles, a Saturday mountain day, 49 km/week. The model's
# week 2 had eight runs, seven of them at the 60-min weekday minimum: about 600 min against about 300 the athlete
# runs, which the start-load cap could not touch because it only shortens runs and never below that minimum.
PLAN_131_WEEK_1 = [
    ("Thursday", "Muscular Endurance", 55, "morning"),
    ("Thursday", "Easy", 45, "afternoon"),
    ("Friday", "Easy", 55, "main"),
    ("Saturday", "Easy", 80, "main"),
    ("Sunday", "Long Run", 119, "main"),
]
PLAN_131_WEEK_2 = [
    ("Monday", "Muscular Endurance", 70, "morning"),
    ("Monday", "Easy", 60, "afternoon"),
    ("Tuesday", "Easy", 60, "morning"),
    ("Tuesday", "Easy", 60, "afternoon"),
    ("Wednesday", "Muscular Endurance", 70, "morning"),
    ("Wednesday", "Easy", 60, "afternoon"),
    ("Thursday", "Easy", 60, "main"),
    ("Friday", "Easy", 60, "main"),
    ("Saturday", "Long Run", 179, "main"),
    ("Sunday", "Easy", 60, "main"),
]
ALL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _rows(week, spec):
    return [
        {"week_number": week, "day_of_week": d, "type": t, "title": f"{t} {d} {s}", "description": "Run",
         "duration_minutes": m, "session_slot": s, "phase": "Base"}
        for d, t, m, s in spec
    ]  # fmt: skip


def _plan_131_week_2(monkeypatch, week_no=2, prior=None):
    """Week 2 as Claude (the prod plan model) wrote it, run through the real post-processing; `week_no` and `prior`
    replay the same model week later in the plan."""
    from types import SimpleNamespace
    from unittest.mock import MagicMock, patch

    monkeypatch.setattr(settings, "PLAN_LINT_ENABLED", False)
    monkeypatch.setattr(settings, "PLAN_LLM_PROVIDER", "claude")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "anthropic-key")
    prior = prior if prior is not None else _rows(1, PLAN_131_WEEK_1)
    monkeypatch.setattr(plan_generator, "get_plan_workouts", lambda plan_id: prior)
    monkeypatch.setattr("services.kb_retrieval._client", lambda: None)
    reply = SimpleNamespace(
        content=[SimpleNamespace(type="text", text=json.dumps(_rows(week_no, PLAN_131_WEEK_2)))],
        stop_reason="end_turn",
        usage=SimpleNamespace(input_tokens=1000, output_tokens=200),
    )
    stream = MagicMock()
    stream.__enter__.return_value.get_final_message.return_value = reply
    client = MagicMock()
    client.messages.stream.return_value = stream
    race_info = {
        "name": "Vietnam Highlands Trail by UTMB",
        "date": "2027-01-09",
        "plan_start_date": "2026-10-22",
        "terrain": "trail",
        "course_distance_km": 104.2,
        "course_elevation_gain_m": 5533,
        "goal_type": "time",
        "target_time_hours": 15.75,
        "preferred_days": ALL_DAYS,
        "long_run_day": "Saturday",
        "days_per_week": 7,
        "double_session_days": json.dumps(["Tuesday"]),
        "mountain_days": json.dumps(["Saturday"]),
        "training_mountain": "chau_thoi",
        "mountain_min_minutes": 180,
        "athlete_tier": "recreational",
    }
    user = {"max_hr": 185, "resting_hr": 53, "zone2_pace_min": "6:23", "zone2_pace_max": "5:13",
            "current_weekly_km": 49.0}  # fmt: skip
    with patch("anthropic.Anthropic", return_value=client):
        wos, tier = asyncio.run(
            PlanGenerator.generate_plan_workouts(
                plan_id=131,
                user_profile=user,
                race_info=race_info,
                total_weeks=13,
                api_key="test-key",
                cutoff_time_hours=29,
                block_number=week_no,
                weeks_per_block=1,
            )
        )
    assert client.messages.stream.called  # the model's week, not the rule-based fallback
    recent = 49.0 * PlanGenerator.flat_zone2_pace(user, "time", tier)
    return [w for w in wos if w["week_number"] == week_no], recent


def test_week_2_held_at_current_load_by_dropping_extra_runs(monkeypatch):
    week, recent = _plan_131_week_2(monkeypatch)
    runs = [w for w in week if w["type"] not in ("Rest", "Muscular Endurance", "Strength")]
    run_days = {w["day_of_week"] for w in runs}
    # R-U2: the first two weeks at current load, down to four run days (the mountain long run stays whole)
    assert len(run_days) == 4 and len(runs) == 4
    assert plan_lint.week_minutes(week) <= 180 + 3 * 60  # was 600: eight runs, seven at the 60-min weekday minimum
    assert [w["duration_minutes"] >= 179 for w in week if w["type"] == "Long Run"] == [True]  # the mountain day stays
    assert sum(w["type"] == "Muscular Endurance" for w in week) == 2  # ME is not volume (R-G1)
    assert all(w["duration_minutes"] >= 60 for w in runs if w["day_of_week"] not in ("Saturday", "Sunday"))
    tuesday = [w for w in runs if w["day_of_week"] == "Tuesday"]
    assert len(tuesday) <= 1  # the double's second run goes first


def test_week_held_at_current_load_is_not_days_short(monkeypatch):
    from services.athlete_tier import get_profile

    week, recent = _plan_131_week_2(monkeypatch)
    rows = _rows(1, PLAN_131_WEEK_1) + week
    prefs = dict(long_run_day="Saturday", days_per_week=7, mountain_day=True, total_weeks=13)
    codes = {i.code for i in plan_lint.lint_weeks(rows, {2}, get_profile("recreational"), plan_lint.Prefs(**prefs))}
    assert "DAYS_SHORT" in codes  # without the athlete's load the lint can't tell why the week is short
    held = plan_lint.Prefs(**prefs, start_load_minutes=recent)
    assert "DAYS_SHORT" not in {i.code for i in plan_lint.lint_weeks(rows, {2}, get_profile("recreational"), held)}


def test_week_3_grows_by_the_tier_step_plus_the_ladder_step(monkeypatch):
    week_2, _ = _plan_131_week_2(monkeypatch)
    week_3, _ = _plan_131_week_2(monkeypatch, 3, _rows(1, PLAN_131_WEEK_1) + week_2)
    long_2, long_3 = (max(w["duration_minutes"] for w in wk if w["type"] == "Long Run") for wk in (week_2, week_3))
    # R-V2 on the week before, plus the long run's ladder step (R-U1: ladder steps are exempt)
    assert plan_lint.week_minutes(week_3) <= plan_lint.week_minutes(week_2) * 1.10 + (long_3 - long_2) + 1
    assert sum(w["type"] == "Muscular Endurance" for w in week_3) == 2


def test_deload_week_keeps_its_easy_runs_as_real_runs(rule_based_plan):
    # Plan 131's shape: a 49 km runner, 100K, 13 weeks. The 4 h recovery long run (R-U1) left 17-19 min for each
    # weekday run, which the clean-up then turned into rest: a deload week of the long run and one other run.
    wos = rule_based_plan(km=104.2, weeks=13, mountain_days=["Saturday"], tier="recreational", weekly_km=49)
    week_4 = [w for w in wos if w["week_number"] == 4]
    runs = [w for w in week_4 if w["type"] in ("Easy", "Aerobic Capacity", "Recovery", "Long Run")]
    assert ultra_rules.is_deload(4, 13) and len({w["day_of_week"] for w in runs}) >= 4
    assert all(w["duration_minutes"] >= 30 for w in runs)


def _week_min(wos, wk):
    return plan_lint.week_minutes([w for w in wos if w["week_number"] == wk])


def test_back_to_back_weekend_replaces_the_6_and_7_hour_days(rule_based_plan):
    """Owner 2026-10-27: an athlete who prefers a back-to-back holds the 6-7 h rung over two days, longer in all."""
    wos = rule_based_plan(
        km=104.2,
        weeks=20,
        mountain_days=["Saturday"],
        tier="recreational",
        race_extra={"long_day_format": "back_to_back"},
    )
    b2b = {w["week_number"]: w for w in wos if plan_lint.is_b2b_day(w)}
    longs = _longs(wos)
    assert set(b2b) == {14, 16}  # the 6 h and 7 h rungs; week 15 is the recovery week before the peak
    assert (longs[14], b2b[14]["duration_minutes"]) == (240, 150)
    assert (longs[16], b2b[16]["duration_minutes"]) == (300, 165)
    assert all(w["day_of_week"] == "Sunday" and w["target_zone"] == "Zone 2" for w in b2b.values())
    assert not any(w["type"] == "Muscular Endurance" for w in wos if w["week_number"] in (14, 16))


def test_single_long_day_stays_the_default(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=["Saturday"], tier="recreational")
    assert _longs(wos)[16] == 420 and not any(plan_lint.is_b2b_day(w) for w in wos)


def test_ladder_weeks_grow_by_the_ladder_step_and_10_percent_on_the_rest(rule_based_plan):
    """Quang's step on the long run, the tier's 10% on the rest of the week (measured from the week before a
    recovery week); no extra cap on the whole week, which would stop the weekday growth Quang asks for."""
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=["Saturday"], tier="recreational")
    for wk in range(3, 17):
        if ultra_rules.is_deload(wk, 20):
            continue
        ref = wk - 2 if ultra_rules.is_deload(wk - 1, 20) else wk - 1
        rows = [w for w in wos if w["week_number"] == wk]
        before = [w for w in wos if w["week_number"] == ref]
        rest = _week_min(wos, wk) - plan_lint.long_block_minutes(rows)
        rest_before = _week_min(wos, ref) - plan_lint.long_block_minutes(before)
        assert rest <= rest_before * 1.10 + 30, wk  # 30: an overshoot under half a run stays (R-V4)


def test_mid_week_start_gets_its_share_of_week_one(rule_based_plan):
    """Plan 131 started on a Thursday: week 1 held a full week of load in 4 days."""
    thursday = START + timedelta(days=3)
    wos = rule_based_plan(
        km=104.2,
        weeks=20,
        mountain_days=["Saturday"],
        tier="recreational",
        weekly_km=60,
        race_extra={"plan_start_date": thursday.isoformat()},
    )
    week1 = [w for w in wos if w["week_number"] == 1 and w["type"] != "Rest"]
    recent = 60 * PlanGenerator.flat_zone2_pace({"zone2_pace_min": "6:30", "zone2_pace_max": "5:45"}, "finish", None)
    # the 180 min mountain day plus at most one more run: the share of the load, or the mountain minimum
    assert plan_lint.week_minutes(week1) <= max(recent * 1.1 * 4 / 7, 180 + 60) + 1
    assert all(w["day_of_week"] in ("Thursday", "Friday", "Saturday", "Sunday") for w in week1)


def test_steep_race_gets_eccentric_me_descents_and_race_rehearsal(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=["Saturday"], tier="recreational")
    me = [w for w in wos if w["type"] == "Muscular Endurance"]
    # the step-text rules may fold it in as a step before the cool-down
    assert me and all("3 x 10 slow step-downs per leg" in w["description"] for w in me)
    longs = {w["week_number"]: w for w in wos if w["type"] == "Long Run"}
    assert plan_generator.DESCENT_EN in longs[16]["description"]
    assert plan_generator.DESCENT_EN not in longs[5]["description"]
    assert all(
        plan_generator.REHEARSAL_EN in (w.get("fueling_tip") or "")
        for w in longs.values()
        if w["duration_minutes"] >= 300 and w["phase"] in ("Build", "Peak")
    )


def test_flat_city_runner_gets_downhill_on_a_ramp_in_the_last_build_weeks(rule_based_plan):
    """No mountain day on a 53 m D+/km course: the last 6 build weeks end one easy run with ramp descents."""
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=[], tier="recreational")
    with_ramp = {w["week_number"] for w in wos if plan_generator.DESCENT_RAMP_EN in (w.get("description") or "")}
    assert with_ramp and min(with_ramp) > 16 - 6 and max(with_ramp) <= 16
    assert not any(ultra_rules.is_deload(wk, 20) for wk in with_ramp)


def test_gentle_mountain_long_runs_ask_for_repeats(rule_based_plan):
    """Châu Thới (28 m D+/km) for a 53 m D+/km course: Build/Peak mountain long runs repeat its steepest climb."""
    wos = rule_based_plan(
        km=104.2,
        weeks=20,
        mountain_days=["Saturday"],
        tier="recreational",
        race_extra={"training_mountain": "chau_thoi"},
    )
    build_longs = [
        w
        for w in wos
        if w["type"] == "Long Run"
        and w["phase"] in ("Build", "Peak")
        and w.get("mountain_mode")
        and not ultra_rules.is_deload(w["week_number"], 20)
    ]
    assert build_longs and all("repeats of its steepest climb" in w["description"] for w in build_longs)
    dinh = rule_based_plan(km=104.2, weeks=20, mountain_days=["Saturday"], tier="recreational")
    assert not any("repeats of its steepest climb" in (w.get("description") or "") for w in dinh)


def test_vert_targets_need_somewhere_to_climb():
    d_info = {"course_distance_km": 104.2, "course_elevation_gain_m": 5533, "goal_type": "finish"}
    from services import goal_demands

    d = goal_demands.compute(104.2, 5533, None, 29)
    assert PlanGenerator.vert_targets_for(d_info, d, 20) == {}  # flat, no stairs, no treadmill
    stairs = PlanGenerator.vert_targets_for({**d_info, "stair_access": True}, d, 20)
    assert max(stairs.values()) == round(0.25 * 5533, -1)  # indoor only
    dinh = {**d_info, "mountain_days": json.dumps(["Saturday"]), "training_mountain": "nui_dinh"}
    d_dinh = goal_demands.compute(104.2, 5533, None, 29, venue_climb_rate=60)
    assert max(PlanGenerator.vert_targets_for(dinh, d_dinh, 20).values()) == round(0.40 * 5533, -1)
    d_gentle = goal_demands.compute(104.2, 5533, None, 29, venue_climb_rate=28)
    assert PlanGenerator.vert_targets_for({**dinh, "training_mountain": "chau_thoi"}, d_gentle, 20) == {}


def test_a_100k_short_plan_peaks_three_weeks_out_with_a_two_week_taper(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=11, mountain_days=["Saturday"], tier="sub_elite", weekly_km=100)
    phase = {w["week_number"]: w["phase"] for w in wos}
    longest = {
        wk: max(w["duration_minutes"] for w in wos if w["week_number"] == wk and w["type"] == "Long Run")
        for wk in (7, 8)
    }
    assert phase[8] == phase[9] == "Taper" and phase[7] != "Taper"
    assert longest[7] == 420 and longest[8] < 420


@pytest.fixture
def seven_day_ai_plan(monkeypatch):
    """A mountain-day plan for a runner who picked all 7 days, built on the AI path: the draft is the rules' own
    week with an easy hour on every Monday, as a model fills a 7-day week."""
    monkeypatch.setattr(settings, "PLAN_DEMANDS_ENABLED", True)
    monkeypatch.setattr(settings, "PLAN_LINT_ENABLED", False)
    monkeypatch.setattr(settings, "PLAN_LLM_PROVIDER", "gemini")
    monkeypatch.setattr(plan_generator, "get_plan_workouts", lambda plan_id: [])

    def build(km, weeks, tier, weekly_km=60):
        race_info = {
            "name": "VHT",
            "date": (START + timedelta(weeks=weeks - 2, days=5)).isoformat(),
            "plan_start_date": START.isoformat(),
            "terrain": "trail",
            "course_distance_km": km,
            "course_elevation_gain_m": 5533 if km > 90 else 2946,
            "goal_type": "finish",
            "preferred_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "long_run_day": "Saturday",
            "days_per_week": 7,
            "training_environment": "flat",
            "training_mountain": "nui_dinh",
            "mountain_days": json.dumps(["Saturday"]),
            "athlete_tier": tier,
        }
        user = {
            "max_hr": 185,
            "resting_hr": 55,
            "zone2_pace_min": "6:30",
            "zone2_pace_max": "5:45",
            "current_weekly_km": float(weekly_km),
        }
        kw = dict(
            plan_id=0,
            user_profile=user,
            race_info=race_info,
            total_weeks=weeks,
            cutoff_time_hours=29,
            block_number=1,
            weeks_per_block=weeks,
        )
        rules, _ = asyncio.run(PlanGenerator.generate_plan_workouts(api_key=None, **kw))
        draft = [w for w in rules if not (w["day_of_week"] == "Monday" and w["type"] == "Rest")]
        draft += [
            {
                "week_number": wk,
                "day_of_week": "Monday",
                "phase": "Build",
                "title": "Easy Run",
                "type": "Easy",
                "duration_minutes": 60,
                "distance_km": 10,
                "target_zone": "Zone 1",
                "description": "Easy hour.",
            }
            for wk in range(1, weeks - 2)
        ]
        client = MagicMock()
        client.models.generate_content.return_value = MagicMock(text=json.dumps(draft), candidates=[])
        with (
            patch("google.genai.Client", return_value=client),
            patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
            patch("services.race_history.prompt_summary", return_value=""),
            patch("services.race_history.tier_distance", return_value=None),
        ):
            out, _ = asyncio.run(PlanGenerator.generate_plan_workouts(api_key="fake", **kw))
        assert client.models.generate_content.called
        return out

    return build


def _monday_runs(wos, week):
    return [
        w
        for w in wos
        if w["week_number"] == week
        and w["day_of_week"] == "Monday"
        and w["type"] not in ("Rest", "Muscular Endurance", "Strength")
        and w["duration_minutes"] > 0
    ]


def test_a_seven_day_runner_recovers_on_the_monday_after_the_weekend(seven_day_ai_plan):
    wos = seven_day_ai_plan(104.2, 20, "recreational")
    runs = _monday_runs(wos, 3)
    assert len(runs) == 1 and runs[0]["type"] == "Recovery" and runs[0]["target_zone"] == "Zone 1"
    assert 30 <= runs[0]["duration_minutes"] <= 40
    assert not any(
        i.code == "WEEKDAY_SHORT" and i.week == 3
        for i in plan_lint.lint_weeks(
            wos,
            {3},
            get_profile("recreational"),
            plan_lint.Prefs(total_weeks=20, race_km=104.2, mountain_day=True, days_per_week=7),
        )
    )


def test_the_monday_after_a_six_hour_mountain_day_is_rest(seven_day_ai_plan):
    wos = seven_day_ai_plan(104.2, 20, "recreational")
    six = next(wk for wk in range(1, 20) if _longs(wos).get(wk, 0) >= 360)
    assert not _monday_runs(wos, six + 1)


def test_a_novice_who_picks_seven_days_rests_on_monday(seven_day_ai_plan):
    wos = seven_day_ai_plan(56.4, 16, "novice", weekly_km=35)
    assert not any(_monday_runs(wos, wk) for wk in range(2, 12))


def test_week_one_monday_has_no_weekend_before_it(seven_day_ai_plan):
    wos = seven_day_ai_plan(104.2, 20, "recreational")
    assert [w["type"] for w in _monday_runs(wos, 1)] == ["Easy"]
