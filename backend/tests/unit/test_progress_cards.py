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


def test_summary_ignores_the_good_direction():
    better = [
        Card("sleep", 500, "min", note={"key": "sleep.above"}),
        Card("resting_hr", 44, "bpm", note={"key": "rhr.below"}),
        Card("hrv", 80, "ms", note={"key": "hrv.above"}),
    ]
    assert pc.health_summary(better).note == {"key": "health.all_usual", "contributors": []}
    tired = [
        Card("sleep", 300, "min", note={"key": "sleep.below"}),
        Card("resting_hr", 55, "bpm", note={"key": "rhr.above"}),
    ]
    assert pc.health_summary(tired).note["contributors"] == ["sleep", "resting_hr"]


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
        "next": {
            "title": "Tempo 3x10",
            "type": "Tempo",
            "date": "2026-10-23",
            "duration_minutes": 60,
            "target_pace": None,
        },
        "adjust": {"kind": "swap_easy", "minutes": 45},
        "tonight": None,
    }
    response = Card("response", None, None, note={"key": "response.load.loading"})
    assert pc.today_card(ws, monday, date(2026, 10, 22), summary, response).note["adjust"] == {"kind": "cap"}


def test_today_without_plan_or_health_is_absent():
    assert pc.today_card([], None, TODAY, None) is None


def test_today_with_health_only():
    summary = Card("coach_read", None, None, note={"key": "health.all_usual", "contributors": []})
    assert pc.today_card([], None, TODAY, summary).note == {
        "key": "today",
        "health": "health.all_usual",
        "contributors": [],
        "next": None,
        "adjust": None,
        "tonight": None,
    }


# ─── training response ───

R_MONDAY = date(2026, 9, 7)
R_TODAY = R_MONDAY + timedelta(days=7 * 5 + 2)  # Wednesday of week 6


def _phases(phase="Build", week=6):
    return [{"week_number": w, "phase": "Base" if w < week else phase} for w in range(1, week + 1)]


def _signals(base_hrv=60.0, base_rhr=48.0, now_hrv=None, now_rhr=None, days=35):
    """Baseline days alternate around the mid (spread 2 ms / 1 bpm); the last 7 days carry `now_*`."""
    rows = []
    for i in range(days):
        recent = i < 7
        wobble = 1 if i % 2 else -1
        hrv = now_hrv if recent and now_hrv is not None else base_hrv + 2 * wobble
        rhr = now_rhr if recent and now_rhr is not None else base_rhr + wobble
        rows.append(
            {"metric_date": R_TODAY - timedelta(days=i), "source_provider": "coros", "hrv_ms": hrv, "resting_hr": rhr}
        )
    return rows


def test_response_none_without_phase():
    assert pc.training_response([], _signals(), R_MONDAY, R_TODAY) is None


def test_response_pending_below_14_days():
    out = pc.training_response(_phases(), _signals(days=13), R_MONDAY, R_TODAY)
    assert out == Pending("response", needs=14, have=13)


def test_response_none_when_recent_days_missing():
    rows = [r for r in _signals() if (R_TODAY - r["metric_date"]).days >= 7]
    assert pc.training_response(_phases(), rows, R_MONDAY, R_TODAY) is None


def test_response_build_week_feeling_the_load_is_expected():
    # HRV baseline 60 ms with a 3 ms spread (the floor), so 58.5 ms is z=-0.5; resting HR stays at its usual.
    out = pc.training_response(_phases(), _signals(now_hrv=58.5), R_MONDAY, R_TODAY)
    assert isinstance(out, Card) and out.note["key"] == "response.load.loading"
    assert out.note["phase"] == "Build" and out.note["week"] == 6 and out.note["hrv_pct"] == -2


def test_response_both_well_outside_is_strained():
    out = pc.training_response(_phases(), _signals(now_hrv=55.5, now_rhr=49.5), R_MONDAY, R_TODAY)
    assert out.note["key"] == "response.load.strained" and out.note["rhr_delta"] == 2


def test_response_mild_both_down_is_still_loading():
    out = pc.training_response(_phases(), _signals(now_hrv=58.0, now_rhr=49.0), R_MONDAY, R_TODAY)
    assert out.note["key"] == "response.load.loading"


def test_response_adapting_and_mixed_signals():
    up = pc.training_response(_phases(), _signals(now_hrv=63.0, now_rhr=47.0), R_MONDAY, R_TODAY)
    assert up.note["key"] == "response.load.adapting"
    mixed = pc.training_response(_phases(), _signals(now_hrv=63.0, now_rhr=50.0), R_MONDAY, R_TODAY)
    assert mixed.note["key"] == "response.load.steady"


def test_response_taper_reads_as_down_phase():
    rebound = pc.training_response(_phases("Taper"), _signals(now_hrv=64.0), R_MONDAY, R_TODAY)
    assert rebound.note["key"] == "response.down.adapting"
    stuck = pc.training_response(_phases("Taper"), _signals(now_hrv=55.0, now_rhr=51.0), R_MONDAY, R_TODAY)
    assert stuck.note["key"] == "response.down.strained"


def test_response_series_carries_phase_per_day():
    out = pc.training_response(_phases(), _signals(), R_MONDAY, R_TODAY)
    assert out.series[-1] == {"date": R_TODAY.isoformat(), "phase": "Build", "hrv": 58.0, "rhr": 47.0}
    assert out.series[0]["phase"] == "Base" and out.band == (57.0, 63.0) and out.source == "coros"


# ─── today's targets ───

OFF = Card("coach_read", None, None, note={"key": "health.off", "contributors": ["hrv"]})
USUAL = Card("coach_read", None, None, note={"key": "health.all_usual", "contributors": []})
TEMPO = {"type": "Tempo", "duration_minutes": 60}


def test_adjustment_only_for_hard_sessions_today_or_tomorrow():
    assert pc.session_adjustment({"type": "Easy Run"}, TODAY, TODAY, OFF, None) is None
    assert pc.session_adjustment(TEMPO, TODAY + timedelta(days=2), TODAY, OFF, None) is None


def test_adjustment_keep_cap_or_swap():
    loading = Card("response", None, None, note={"key": "response.load.loading"})
    strained = Card("response", None, None, note={"key": "response.load.strained"})
    assert pc.session_adjustment(TEMPO, TODAY, TODAY, USUAL, None) == {"kind": "as_planned"}
    assert pc.session_adjustment(TEMPO, TODAY, TODAY, OFF, loading) == {"kind": "cap"}
    assert pc.session_adjustment(TEMPO, TODAY, TODAY, OFF, strained) == {"kind": "swap_easy", "minutes": 45}
    short = {"type": "Interval", "duration_minutes": 32}
    assert pc.session_adjustment(short, TODAY, TODAY, OFF, None) == {"kind": "swap_easy", "minutes": 30}


def _sleep_nights(usual=480, recent=None, n=28):
    return [
        {"metric_date": TODAY - timedelta(days=i), "sleep_minutes": recent if recent is not None and i < 7 else usual}
        for i in range(n)
    ]


def test_sleep_target_pays_back_a_share_of_the_week():
    assert pc.sleep_target(_sleep_nights(n=6), TODAY) is None
    assert pc.sleep_target(_sleep_nights(), TODAY) == {
        "target_min": 480,
        "usual_min": 480,
        "debt_min": 0,
        "long_run_tomorrow": False,
    }
    # 7 nights at 465 against a usual of 480: 105 min short, a third (35) paid back tonight.
    assert pc.sleep_target(_sleep_nights(recent=465), TODAY)["target_min"] == 520
    # 7 nights at 450: 210 min short, but tonight's payback stops at an hour.
    assert pc.sleep_target(_sleep_nights(recent=450), TODAY)["target_min"] == 540


def test_sleep_target_caps_payback_and_adds_long_run_bonus():
    monday = TODAY - timedelta(days=TODAY.weekday())
    tomorrow = (TODAY + timedelta(days=1)).strftime("%A")
    week = (TODAY + timedelta(days=1) - monday).days // 7 + 1
    long_run = {"type": "Long Run", "week_number": week, "day_of_week": tomorrow, "is_completed": 0}
    out = pc.sleep_target(_sleep_nights(recent=300), TODAY, [long_run], monday)
    assert out["long_run_tomorrow"] and out["target_min"] == 480 + 60 + 30


# ─── week review ───

W_MONDAY = date(2026, 9, 7)
W_TODAY = W_MONDAY + timedelta(days=14)  # Monday of week 3: week 2 just finished


def _session(day, type_="Easy Run", done=1, week=2, minutes=60):
    return {
        "week_number": week,
        "day_of_week": day,
        "type": type_,
        "is_completed": done,
        "duration_minutes": minutes,
    }


def _health(days_back, hrv=60.0, rhr=48.0, sleep=480):
    return {
        "metric_date": W_TODAY - timedelta(days=days_back),
        "hrv_ms": hrv,
        "resting_hr": rhr,
        "sleep_minutes": sleep,
    }


def test_week_review_none_in_week_one():
    assert pc.week_review([_session("Monday", week=1)], [], W_MONDAY, W_MONDAY + timedelta(days=3)) is None


def test_week_review_facts_in_priority_order():
    ws = [
        _session("Tuesday", "Tempo"),
        _session("Thursday", "Interval"),
        _session("Saturday", "Long Run", minutes=150),
        _session("Sunday", done=0),
    ]
    rows = [_health(d, hrv=60.0 + (d % 2), rhr=48.0) for d in range(8, 40)]  # baseline before week 2
    rows += [
        _health(6, hrv=61.0),  # Tuesday: good
        _health(4, hrv=50.0),  # Thursday: HRV well below
        _health(2, sleep=360),  # Saturday: short sleep before the long run
    ]
    out = pc.week_review(ws, rows, W_MONDAY, W_TODAY)
    assert out.note["week"] == 2
    assert out.note["facts"] == [
        {"kind": "short_sleep_long_run", "count": 1, "total": 1},
        {"kind": "hard_on_good_days", "count": 1, "total": 2},
        {"kind": "sessions", "count": 3, "total": 4},
    ]


def test_week_review_falls_back_to_sessions():
    out = pc.week_review([_session("Tuesday")], [], W_MONDAY, W_TODAY)
    assert out.note["facts"] == [{"kind": "sessions", "count": 1, "total": 1}]
