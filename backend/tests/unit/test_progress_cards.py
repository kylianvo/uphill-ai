from datetime import UTC, date, datetime, timedelta

from services import progress_cards as pc
from services.progress_cards import Card, Pending

MONDAY = date(2026, 9, 7)


def _wk(week, done=1, missed=0, reason=None, type_="Easy Run", km=10.0, climb=100.0, matched=None):
    return {
        "week_number": week,
        "type": type_,
        "is_completed": done,
        "is_missed": missed,
        "missed_reason": reason,
        "matched_activity_id": matched,
        "distance_km": km,
        "elevation_gain_m": climb,
    }


def _run(day: date, km=10.0, climb=50.0, minutes=60, drift=None, workout_type=None):
    return {
        "start_time": datetime.combine(day, datetime.min.time(), tzinfo=UTC),
        "distance_km": km,
        "elevation_gain_m": climb,
        "duration_seconds": minutes * 60,
        "hr_drift_pct": drift,
        "workout_type": workout_type,
    }


# ─── consistency ───


def test_consistency_pending_below_threshold():
    out = pc.consistency([_wk(1), _wk(2)], current_week=2)
    assert out == Pending("consistency", needs=2, have=1)


def test_consistency_card_at_threshold():
    ws = [_wk(1), _wk(1, done=0, missed=1, reason="busy"), _wk(2), _wk(2), _wk(1, type_="Rest", done=0)]
    out = pc.consistency(ws, current_week=3)
    assert isinstance(out, Card) and out.key == "consistency"
    assert out.value == 75.0
    assert out.note == {"key": "consistency", "pct": 75, "top_missed_reason": "busy"}
    assert out.series == [{"week": 1, "done": 1, "planned": 2}, {"week": 2, "done": 2, "planned": 2}]


def test_consistency_counts_watch_matched_as_done():
    ws = [_wk(1, done=0, matched=42), _wk(2)]
    assert pc.consistency(ws, current_week=3).value == 100.0


# ─── volume ───


def test_volume_pending_below_threshold():
    acts = [_run(MONDAY), _run(MONDAY + timedelta(days=7))]
    out = pc.volume([_wk(w, matched=w) for w in (1, 2, 3)], acts, MONDAY, current_week=4)
    assert out == Pending("volume", needs=3, have=2)


def test_volume_card_at_threshold():
    acts = [_run(MONDAY + timedelta(days=7 * i), km=12.0, climb=300.0) for i in range(3)]
    out = pc.volume([_wk(w, matched=w) for w in (1, 2, 3)], acts, MONDAY, current_week=4)
    assert isinstance(out, Card) and out.value == 12.0 and out.unit == "km"
    assert out.series[0] == {"week": 1, "km": 12.0, "km_planned": 10.0, "climb_m": 300.0, "climb_planned": 100.0}


# ─── durability ───


def test_durability_pending_below_threshold():
    acts = [_run(MONDAY, minutes=120, drift=2.0), _run(MONDAY, minutes=120, drift=3.0)]
    assert pc.durability(acts) == Pending("durability", needs=3, have=2)


def test_durability_card_at_threshold():
    acts = [_run(MONDAY + timedelta(days=i), minutes=120, drift=d) for i, d in enumerate([5.0, 1.6, 3.0])]
    out = pc.durability(acts)
    assert isinstance(out, Card) and out.value == 3.0 and out.note == {"key": "durability"}
    assert [p["pct"] for p in out.series] == [5.0, 1.6, 3.0]


def test_durability_excludes_hard_workouts_and_short_runs():
    acts = [_run(MONDAY, minutes=120, drift=1.0, workout_type="interval"), _run(MONDAY, minutes=60, drift=1.0)]
    acts += [_run(MONDAY, minutes=120, drift=2.0)] * 2
    assert pc.durability(acts) == Pending("durability", needs=3, have=2)


# ─── training load ───


def _load_days(n, short=100.0, long=100.0):
    today = date(2026, 10, 23)
    return [
        {
            "metric_date": today - timedelta(days=i),
            "training_load_short": short,
            "training_load_long": long,
            "load_ratio": short / long,
        }
        for i in range(n)
    ]


def test_load_pending_below_threshold():
    assert pc.training_load(_load_days(27)) == Pending("load", needs=28, have=27)


def test_load_card_at_threshold_and_wording():
    assert pc.training_load(_load_days(28)).note == {"key": "load.within"}
    assert pc.training_load(_load_days(28, short=140)).note == {"key": "load.above"}
    assert pc.training_load(_load_days(28, short=70)).note == {"key": "load.below"}


# ─── aerobic speed ───


def test_aerobic_speed_pending_without_path():
    assert pc.aerobic_speed_card([{"week_number": 1, "pace_min_km": 6.1}], None) == Pending("aerobic_speed", 3, 1)


def test_aerobic_speed_card_with_path():
    cps = [{"week_number": w, "pace_min_km": p} for w, p in [(1, 6.2), (2, 6.1), (4, 6.0)]]
    path = {"b": "on", "a": "behind", "measured_pct": 3.2, "expected_pct": 2.5, "weeks": 3, "confidence": "low"}
    out = pc.aerobic_speed_card(cps, path)
    assert out.value == 6.0 and out.unit == "min/km"
    assert out.note == {"key": "aerobic_speed", "b": "on", "a": "behind", "measured_pct": 3.2}
    assert out.series == [{"week": 1, "pace": 6.2}, {"week": 2, "pace": 6.1}, {"week": 4, "pace": 6.0}]


def test_volume_counts_logged_sessions_without_a_watch():
    ws = [_wk(w, done=1, km=8.0, climb=80.0) for w in (1, 2, 3)]
    out = pc.volume(ws, [], MONDAY, current_week=4)
    assert isinstance(out, Card) and out.value == 8.0


# ─── health ───

TODAY = date(2026, 10, 23)


def _nights(values, field, **extra):
    """values[0] is the oldest night; the last is today. None = no data that night."""
    n = len(values)
    return [
        {"metric_date": TODAY - timedelta(days=n - 1 - i), "source_provider": "coros", field: v, **extra}
        for i, v in enumerate(values)
    ]


def test_usual_range_floor_applies():
    assert pc.usual_range([50, 50, 50, 50], floor=2) == (48, 50, 52)


def test_sleep_pending_below_threshold():
    assert pc.sleep(_nights([420] * 6, "sleep_minutes"), TODAY) == Pending("sleep", 7, 6)


def test_sleep_ignores_missing_nights():
    assert pc.sleep(_nights([420] * 6 + [None] * 3, "sleep_minutes"), TODAY) == Pending("sleep", 7, 6)


def test_sleep_card_at_threshold():
    out = pc.sleep(_nights([420] * 7, "sleep_minutes"), TODAY)
    assert isinstance(out, Card) and out.value == 420 and out.unit == "min"
    assert out.band == (390, 450) and out.note == {"key": "sleep.within"}
    assert out.source == "coros" and out.as_of == TODAY and len(out.series) == 7


def test_sleep_short_week_reads_below():
    out = pc.sleep(_nights([480] * 21 + [300] * 7, "sleep_minutes"), TODAY)
    assert out.note == {"key": "sleep.below"}


def test_resting_hr_threshold_and_delta():
    assert pc.resting_hr(_nights([52] * 6, "resting_hr"), TODAY) == Pending("resting_hr", 7, 6)
    out = pc.resting_hr(_nights([55] * 21 + [50] * 7, "resting_hr"), TODAY)
    assert out.note == {"key": "rhr.below", "delta": -5}


def test_hrv_pending_below_threshold():
    assert pc.hrv(_nights([60.0] * 13, "hrv_ms"), TODAY) == Pending("hrv", 14, 13)


def test_hrv_prefers_coros_range():
    out = pc.hrv(_nights([60.0] * 14, "hrv_ms", hrv_range_low=51.0, hrv_range_high=75.0), TODAY)
    assert out.band == (51.0, 75.0) and out.note == {"key": "hrv.within"}


def test_hrv_apple_uses_usual_range():
    rows = _nights([60.0] * 14, "hrv_ms")
    for r in rows:
        r["source_provider"] = "apple_health"
    out = pc.hrv(rows, TODAY)
    assert out.band == (57.0, 63.0) and out.source == "apple_health"


def test_window_widens_series_only():
    rows = _nights([420] * 60, "sleep_minutes")
    assert len(pc.sleep(rows, TODAY).series) == 28
    assert len(pc.sleep(rows, TODAY, window_days=90).series) == 60


def test_summary_names_off_contributors():
    within = Card("sleep", 420, "min", note={"key": "sleep.within"})
    low = Card("hrv", 40, "ms", note={"key": "hrv.below"})
    assert pc.health_summary([within, low]).note == {"key": "health.off", "contributors": ["hrv"]}
    assert pc.health_summary([within]).note == {"key": "health.all_usual", "contributors": []}
    assert pc.health_summary([]) is None


# ─── today ───


def test_today_pairs_readiness_with_the_next_session():
    monday = date(2026, 10, 19)
    ws = [
        {
            "id": 1,
            "week_number": 1,
            "day_of_week": "Monday",
            "type": "Rest",
            "title": "Rest",
            "duration_minutes": 0,
            "is_completed": 0,
        },
        {
            "id": 2,
            "week_number": 1,
            "day_of_week": "Wednesday",
            "type": "Easy Run",
            "title": "Easy Run",
            "duration_minutes": 50,
            "is_completed": 1,
        },
        {
            "id": 3,
            "week_number": 1,
            "day_of_week": "Friday",
            "type": "Tempo",
            "title": "Tempo 3x10",
            "duration_minutes": 60,
            "is_completed": 0,
        },
    ]
    summary = Card("coach_read", None, None, note={"key": "health.off", "contributors": ["hrv"]})
    out = pc.today_card(ws, monday, date(2026, 10, 22), summary)
    assert out.key == "today"
    assert out.note == {
        "key": "today",
        "health": "health.off",
        "contributors": ["hrv"],
        "next": {"title": "Tempo 3x10", "type": "Tempo", "date": "2026-10-23", "duration_minutes": 60},
    }


def test_today_without_plan_or_health_is_absent():
    assert pc.today_card([], None, TODAY, None) is None


def test_today_with_health_only():
    summary = Card("coach_read", None, None, note={"key": "health.all_usual", "contributors": []})
    assert pc.today_card([], None, TODAY, summary).note == {
        "key": "today",
        "health": "health.all_usual",
        "contributors": [],
        "next": None,
    }
