from datetime import UTC, date, datetime

from services.beginner_milestones import (
    baseline_keys,
    default_weeks,
    evaluate,
    jog_credit_minutes,
    ladder_for,
    minimum_weeks,
    serialize,
)


def _w(wid, week, **over):
    w = {"id": wid, "week_number": week, "type": "Easy Run", "duration_minutes": 20, "walk_interval_value": None}
    w.update(over)
    return w


def _a(aid, start, km):
    return {"id": aid, "start_time": start, "distance_km": km, "duration_seconds": 1800.0}


START = date(2026, 10, 5)


def test_ladder_for_5k_ends_at_first_5k():
    assert [m.key for m in ladder_for("5k")][-1] == "first_5k" and len(ladder_for("5k")) == 6


def test_ladder_for_10k_has_nine_ending_first_10k():
    assert [m.key for m in ladder_for("10k")][-1] == "first_10k" and len(ladder_for("10k")) == 9


def test_baseline_keys_at_10_min():
    assert baseline_keys("5k", 10) == ["jog_5", "jog_10"]


def test_baseline_keys_none_or_zero():
    assert baseline_keys("5k", None) == [] and baseline_keys("5k", 0) == []


def test_jog_credit_run_walk_uses_rep_value():
    w = {
        "type": "Walk/Run",
        "duration_minutes": 30,
        "interval_rep_value": 4,
        "interval_rep_unit": "min",
        "walk_interval_value": 1,
    }
    assert jog_credit_minutes(w) == 4


def test_jog_credit_run_walk_seconds_converted():
    w = {
        "type": "Walk/Run",
        "duration_minutes": 30,
        "interval_rep_value": 90,
        "interval_rep_unit": "s",
        "walk_interval_value": 60,
    }
    assert jog_credit_minutes(w) == 1.5


def test_jog_credit_continuous_uses_duration():
    assert jog_credit_minutes({"type": "Easy Run", "duration_minutes": 20, "walk_interval_value": None}) == 20


def test_jog_credit_non_run_is_none():
    assert jog_credit_minutes({"type": "Strength", "duration_minutes": 30}) is None


def test_evaluate_continuous_20_ticks_jog_5_10_20_and_first_session():
    got = {a.key for a in evaluate("5k", START, [_w(1, 1, duration_minutes=20)], [], set())}
    assert got == {"first_session", "jog_5", "jog_10", "jog_20"}


def test_evaluate_ignores_activities_before_plan_start():
    old = _a(9, datetime(2026, 10, 1, 6, tzinfo=UTC), 6.0)
    assert evaluate("5k", START, [], [old], set()) == []


def test_evaluate_5_2km_activity_ticks_first_5k():
    act = _a(3, datetime(2026, 10, 12, 6, tzinfo=UTC), 5.2)
    (got,) = evaluate("5k", START, [], [act], set())
    assert got.key == "first_5k" and got.activity_id == 3


def test_evaluate_skips_revoked_rows():
    got = {a.key for a in evaluate("5k", START, [_w(1, 1, duration_minutes=10)], [], {"jog_10"})}
    assert "jog_10" not in got and "jog_5" in got


def test_evaluate_5k_target_never_emits_stage_b():
    act = _a(3, datetime(2026, 10, 12, 6, tzinfo=UTC), 11.0)
    got = {a.key for a in evaluate("5k", START, [_w(1, 1, duration_minutes=70)], [act], set())}
    assert not got & {"jog_45", "jog_60", "first_10k"}


def test_evaluate_10k_target_emits_stage_b():
    act = _a(3, datetime(2026, 10, 12, 6, tzinfo=UTC), 10.5)
    got = {a.key for a in evaluate("10k", START, [_w(1, 1, duration_minutes=60)], [act], set())}
    assert {"jog_45", "jog_60", "first_10k", "first_5k"} <= got


def test_minimum_weeks_10k_with_jog_30_baseline():
    assert minimum_weeks("10k", 30) == 9


def test_minimum_weeks_5k_no_baseline():
    assert minimum_weeks("5k", None) == 9


def test_default_weeks():
    assert (default_weeks("5k"), default_weeks("10k")) == (12, 22)


def test_serialize_next_key_skips_achieved_and_treats_revoked_as_open():
    rows = [
        {"milestone_key": "first_session", "achieved_at": datetime(2026, 10, 6, tzinfo=UTC), "source": "auto"},
        {"milestone_key": "jog_5", "achieved_at": None, "source": "revoked"},
    ]
    out = serialize("5k", False, rows)
    assert out["next_key"] == "jog_5" and out["target"] == "5k" and out["has_event"] is False
    items = {i["key"]: i for i in out["items"]}
    assert items["first_session"]["achieved_at"].startswith("2026-10-06")
    assert items["jog_5"]["achieved_at"] is None and items["jog_5"]["typical_weeks"] == [3, 5]


def test_serialize_all_done_next_key_none():
    rows = [
        {"milestone_key": m.key, "achieved_at": datetime(2026, 10, 6, tzinfo=UTC), "source": "auto"}
        for m in ladder_for("5k")
    ]
    assert serialize("5k", False, rows)["next_key"] is None


# --- plan shape and creation -------------------------------------------------

from datetime import timedelta  # noqa: E402

import pytest  # noqa: E402

from services import beginner_milestones as bm  # noqa: E402

MON = date(2026, 10, 5)


def test_shape_10k_no_event_is_22_weeks_named_first_10k():
    s = bm.plan_shape("10k", MON, MON, 0, None, None)
    assert (s.race_name, s.total_weeks, s.has_event) == ("First 10K", 22, False)
    assert s.race_date == (MON + timedelta(weeks=21)).isoformat() and s.warning is None


def test_shape_5k_no_event_is_12_weeks():
    assert bm.plan_shape("5k", MON, MON, None, None, None).total_weeks == 12


def test_shape_with_event_uses_event_date_and_flag():
    s = bm.plan_shape("5k", MON, MON, 0, "Parkrun", "2026-12-12")
    assert (s.race_name, s.race_date, s.has_event) == ("Parkrun", "2026-12-12", True)
    assert s.total_weeks == 10 and s.warning is None


def test_shape_event_too_soon_returns_warning_not_error():
    s = bm.plan_shape("5k", MON, MON, 0, None, "2026-11-02")
    assert s.warning == {"code": "event_too_soon", "minimum_weeks": 9} and s.race_name == "First 5K" and s.has_event


def test_shape_event_in_past_raises():
    with pytest.raises(ValueError):
        bm.plan_shape("5k", MON, MON, 0, None, "2026-10-01")


def test_apply_creation_seeds_baseline_and_jog_ceiling(monkeypatch):
    import db

    rows, jog = [], []
    monkeypatch.setattr(db, "set_max_continuous_jog_min", lambda uid, m: jog.append(m) or True)
    monkeypatch.setattr(db, "insert_milestone_if_absent", lambda pid, k, src, at, **kw: rows.append((k, src)) or True)
    bm.apply_creation(7, 5, "5k", 10)
    assert rows == [("jog_5", "baseline"), ("jog_10", "baseline")] and jog == [10]


def test_apply_creation_without_jog_does_nothing(monkeypatch):
    import db

    monkeypatch.setattr(db, "set_max_continuous_jog_min", lambda *a: pytest.fail("no jog given"))
    monkeypatch.setattr(db, "insert_milestone_if_absent", lambda *a, **k: pytest.fail("no baseline"))
    bm.apply_creation(7, 5, "5k", 0)
    bm.apply_creation(7, 5, "5k", None)


def test_jog_credit_walk_run_without_walk_value_is_not_full_duration():
    w = {
        "type": "Walk/Run",
        "duration_minutes": 30,
        "interval_rep_value": 3,
        "interval_rep_unit": "min",
        "walk_interval_value": None,
    }
    assert jog_credit_minutes(w) == 3
    assert jog_credit_minutes({"type": "Walk/Run", "duration_minutes": 30}) is None


def test_shape_event_before_start_raises():
    with pytest.raises(ValueError):
        bm.plan_shape("5k", date(2026, 12, 1), MON, 0, None, "2026-11-20")
