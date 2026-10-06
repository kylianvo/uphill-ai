"""Scheduler retrieval must follow the athlete and the situation, not one fixed query."""

import json
from pathlib import Path

import pytest

from services import scheduler_grounding as sg
from services.athlete_tier import TIER_PROFILES

BEGINNER = TIER_PROFILES["beginner"]
NOVICE = TIER_PROFILES["novice"]
RECREATIONAL = TIER_PROFILES["recreational"]
ELITE = TIER_PROFILES["elite"]

SEED = Path(__file__).resolve().parents[2] / "kb_seed" / "scheduler.json"


def _query(profile, phase="base", **kw):
    args = {"adapting_week": False, "has_block_feedback": False, "has_double_days": False, **kw}
    return sg.build_query(profile, "trail", phase, **args)


def test_every_audience_title_exists_in_the_seed():
    """A renamed chunk would silently escape its audience filter."""
    titles = {c["title"] for c in json.loads(SEED.read_text())["chunks"]}
    assert set(sg.CHUNK_AUDIENCE) <= titles


@pytest.mark.parametrize(
    ("weeks", "first_week", "expected"),
    [(16, 1, "base"), (16, 10, "build"), (16, 12, "peak"), (16, 14, "taper"), (16, 15, "race_week")],
)
def test_phase_hint_for_event_goals(weeks, first_week, expected):
    assert sg.phase_hint("time", True, weeks, first_week) == expected


def test_phase_hint_for_non_event_goals_is_the_goal():
    assert sg.phase_hint("return", False, 8, 1) == "return"


def test_beginner_query_never_asks_for_me_or_doubles():
    q = _query(BEGINNER, has_double_days=True)
    assert "walk-to-run" in q
    assert "muscular endurance" not in q.lower()
    assert "double" not in q.lower()


def test_me_tier_query_asks_for_me_only_outside_the_taper():
    assert "muscular endurance" in _query(RECREATIONAL, "base")
    assert "muscular endurance" not in _query(RECREATIONAL, "taper")


def test_adapt_week_query_asks_for_missed_sessions_and_overtraining():
    q = _query(RECREATIONAL, adapting_week=True, has_block_feedback=True)
    assert "missed sessions" in q
    assert "overtraining" in q


def test_query_differs_by_situation():
    assert len({_query(BEGINNER), _query(ELITE), _query(ELITE, "taper"), _query(ELITE, adapting_week=True)}) == 4


def test_beginner_never_receives_me_doubles_elite_or_fueling_chunks():
    titles = [*sg.CHUNK_AUDIENCE, "Walk-to-Run Progression for Complete Beginners"]
    kept = [t for t in titles if sg.chunk_allowed(t, BEGINNER, has_double_days=True)]
    assert kept == ["Walk-to-Run Progression for Complete Beginners"]


def test_novice_gets_no_me_chunks():
    assert not sg.chunk_allowed("Progressive 14-Week Gym ME Protocol", NOVICE, False)


def test_doubles_need_double_days():
    assert not sg.chunk_allowed("When Double Sessions Make Sense", ELITE, False)
    assert sg.chunk_allowed("When Double Sessions Make Sense", ELITE, True)


def test_high_volume_chunks_are_for_sub_elite_and_elite_only():
    title = "Periodization Above 100 km per Week"
    assert not sg.chunk_allowed(title, RECREATIONAL, False)
    assert sg.chunk_allowed(title, ELITE, False)


def test_unknown_titles_pass():
    assert sg.chunk_allowed("A re-swept chunk", BEGINNER, False)
