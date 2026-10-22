"""Coach triage signal rules (services/coach_signals.py). Each rule gets a
trigger case and a just-below-threshold case. Today is fixed to Thursday
2026-10-22, week 4 of a plan whose week 1 starts Monday 2026-09-28."""

from datetime import UTC, date, datetime, timedelta

from services.coach_signals import AthleteFacts, signals_for, status_of, week_stats
from services.workout_calendar import workout_date

START = date(2026, 9, 28)
NOW = datetime(2026, 10, 22, 9, 0, tzinfo=UTC)
TODAY = NOW.date()
CURRENT_WEEK = 4


def wo(
    week, day, *, type="Easy", title=None, minutes=45, done=False, missed=False, reason=None, rpe=None, phase="build"
):
    return {
        "week_number": week,
        "day_of_week": day,
        "type": type,
        "title": title or type,
        "duration_minutes": minutes,
        "is_completed": 1 if done else 0,
        "is_missed": 1 if missed else 0,
        "missed_reason": reason,
        "rpe": rpe,
        "phase": phase,
        "target_zone": "Z4" if type == "Tempo" else "Z2",
        "date": workout_date(START, week, day),
    }


def plan(**kw):
    p = {
        "id": 1,
        "user_id": 7,
        "created_by_user_id": 99,  # coach-built unless a test says otherwise
        "race_name": "VMM 42K",
        "race_date": "2026-12-19",
        "start_date": START.isoformat(),
        "total_weeks": 12,
        "coach_reviewed_block": None,
        "created_at": NOW - timedelta(hours=31),
    }
    p.update(kw)
    return p


def facts(workouts=(), **kw):
    f = {
        "plan_type": "review",
        "plan": plan(),
        "draft_plan_id": None,
        "workouts": list(workouts),
        "current_week": CURRENT_WEEK,
        "pending_active_count": 0,
        "last_activity_at": NOW - timedelta(hours=5),
        "hrv_last3": [],
        "new_result": None,
        "now": NOW,
    }
    f.update(kw)
    return AthleteFacts(**f)


def codes(f):
    return [s.code for s in signals_for(f)]


def by_code(f, code):
    return next(s for s in signals_for(f) if s.code == code)


# --- act now ---------------------------------------------------------------


def test_pain_in_last_7_days_is_act_now():
    f = facts([wo(4, "Tuesday", missed=True, reason="pain")])
    s = by_code(f, "reported_pain")
    assert s.severity == "act_now"
    assert s.params == {"day": "Tuesday"}


def test_pain_8_days_ago_is_silent():
    f = facts([wo(3, "Tuesday", missed=True, reason="pain")])
    assert "reported_pain" not in codes(f)


def test_sick_is_act_now():
    assert "reported_sick" in codes(facts([wo(4, "Monday", missed=True, reason="sick")]))


def test_three_misses_in_7_days():
    ws = [wo(4, d, missed=True) for d in ("Monday", "Tuesday", "Wednesday")]
    assert by_code(facts(ws), "missed_many").params == {"count": 3}


def test_two_misses_is_not_many():
    ws = [wo(4, d, missed=True) for d in ("Monday", "Tuesday")]
    assert "missed_many" not in codes(facts(ws))


def test_overload_131_pct():
    ws = [wo(4, "Monday", minutes=100, done=True)]
    ws[0]["actual_minutes"] = 131  # summed from matched watch activities
    assert by_code(facts(ws), "overload").params == {"done_min": 131, "planned_min": 100}


def test_overload_130_pct_is_silent():
    ws = [wo(4, "Monday", minutes=100, done=True)]
    ws[0]["actual_minutes"] = 130
    assert "overload" not in codes(facts(ws))


def test_overload_ignored_when_planned_under_60_min():
    ws = [wo(4, "Monday", minutes=50, done=True)]
    ws[0]["actual_minutes"] = 100
    assert "overload" not in codes(facts(ws))


# --- review & build ---------------------------------------------------------


def test_new_athlete_plan_waiting_review():
    f = facts([wo(1, "Monday")], plan=plan(created_by_user_id=7), current_week=1)
    s = by_code(f, "plan_to_review")
    assert s.severity == "review_build"
    assert s.params == {"week": 1, "waiting_hours": 31}


def test_plan_to_review_week_2_after_week_1_reviewed():
    ws = [wo(1, "Monday"), wo(2, "Monday")]
    f = facts(ws, plan=plan(created_by_user_id=7, coach_reviewed_block=1), current_week=2)
    assert by_code(f, "plan_to_review").params == {"week": 2, "waiting_hours": None}


def test_reviewed_week_is_silent():
    ws = [wo(1, "Monday"), wo(2, "Monday")]
    f = facts(ws, plan=plan(created_by_user_id=7, coach_reviewed_block=2), current_week=2)
    assert "plan_to_review" not in codes(f)


def test_coach_created_plan_never_to_review():
    assert "plan_to_review" not in codes(facts([wo(1, "Monday")], current_week=1))


def test_coached_without_plan_needs_plan():
    f = facts(plan_type="coached", plan=None, last_activity_at=None)
    assert codes(f) == ["needs_plan"]
    assert status_of(signals_for(f)) == "review_build"


def test_review_without_plan_is_on_track():
    f = facts(plan=None, last_activity_at=None)
    assert signals_for(f) == []
    assert status_of([]) == "on_track"


def test_draft_unpublished():
    f = facts(plan_type="coached", plan=None, draft_plan_id=5, last_activity_at=None)
    assert codes(f) == ["draft_unpublished"]


def test_next_week_due_when_generated_weeks_end_within_7_days():
    f = facts([wo(4, "Sunday")], plan_type="coached")
    assert by_code(f, "next_block_due").params == {"days": 3}


def test_next_week_not_due_when_plan_fully_generated():
    f = facts([wo(4, "Sunday")], plan_type="coached", plan=plan(total_weeks=4))
    assert "next_block_due" not in codes(f)


def test_review_runner_generates_own_weeks_so_no_next_week_due():
    assert "next_block_due" not in codes(facts([wo(4, "Sunday")]))


def test_changes_to_approve():
    assert by_code(facts(pending_active_count=3), "changes_to_approve").params == {"count": 3}


# --- check in ---------------------------------------------------------------


def test_no_sync_for_6_days():
    f = facts(last_activity_at=NOW - timedelta(days=6))
    assert by_code(f, "no_sync").params == {"days": 6}


def test_sync_4_days_ago_is_silent():
    assert "no_sync" not in codes(facts(last_activity_at=NOW - timedelta(days=4)))


def test_no_sync_when_no_activity_since_plan_start():
    assert by_code(facts(last_activity_at=None), "no_sync").params == {"days": 24}


def test_no_watch_data_keeps_data_rules_silent():
    f = facts(
        [wo(4, "Monday", done=True)],
        last_activity_at=None,
        plan=plan(start_date=(TODAY - timedelta(days=2)).isoformat()),
    )
    assert [c for c in codes(f) if c in {"no_sync", "hrv_low", "hard_easy_days"}] == []


def test_missed_key_session():
    f = facts([wo(4, "Tuesday", type="Tempo", title="Tempo 3x10", missed=True)])
    assert by_code(f, "missed_key").params == {"title": "Tempo 3x10", "day": "Tuesday"}


def test_missed_easy_is_not_key():
    assert "missed_key" not in codes(facts([wo(4, "Tuesday", missed=True)]))


def test_adherence_below_60():
    ws = [wo(4, "Monday", done=True), wo(4, "Tuesday", missed=True), wo(3, "Friday", missed=True)]
    assert by_code(facts(ws), "adherence_drop").params == {"from_pct": None, "to_pct": 33}


def test_adherence_drop_20_points():
    prev = [wo(1, d, done=True) for d in ("Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")]
    cur = [wo(3, d, done=True) for d in ("Friday", "Saturday", "Sunday")] + [
        wo(4, "Monday", done=True),
        wo(4, "Tuesday", missed=True),
    ]
    s = by_code(facts(prev + cur), "adherence_drop")
    assert s.params == {"from_pct": 100, "to_pct": 80}


def test_adherence_steady_is_silent():
    ws = [wo(4, d, done=True) for d in ("Monday", "Tuesday", "Wednesday")]
    assert "adherence_drop" not in codes(facts(ws))


def test_hrv_low_two_of_three():
    assert by_code(facts(hrv_last3=["low", "normal", "low"]), "hrv_low").params == {"days": 2}


def test_hrv_low_once_is_silent():
    assert "hrv_low" not in codes(facts(hrv_last3=["low", "normal", "normal"]))


def test_hard_easy_days():
    ws = [wo(4, "Monday", done=True, rpe=7), wo(4, "Tuesday", done=True, rpe=8)]
    assert by_code(facts(ws), "hard_easy_days").params == {"count": 2}


def test_one_hard_easy_day_is_silent():
    ws = [wo(4, "Monday", done=True, rpe=8), wo(4, "Tuesday", done=True, rpe=4)]
    assert "hard_easy_days" not in codes(facts(ws))


# --- highlights -------------------------------------------------------------


def test_race_soon():
    f = facts(plan=plan(race_date=(TODAY + timedelta(days=9)).isoformat()))
    s = by_code(f, "race_soon")
    assert s.severity == "highlight"
    assert s.params == {"race": "VMM 42K", "days": 9}


def test_race_in_15_days_is_silent():
    assert "race_soon" not in codes(facts(plan=plan(race_date=(TODAY + timedelta(days=15)).isoformat())))


def test_phase_start_next_week():
    ws = [wo(4, "Monday", phase="build"), wo(5, "Monday", phase="peak")]
    assert by_code(facts(ws), "phase_start").params == {"phase": "peak", "when": "next_week"}


def test_longest_long_run():
    ws = [
        wo(2, "Saturday", type="Long Run", minutes=150, done=True),
        wo(4, "Monday", type="Long Run", minutes=250, done=True),
    ]
    assert by_code(facts(ws), "longest_long_run").params == {"minutes": 250}


def test_single_long_run_is_not_a_milestone():
    assert "longest_long_run" not in codes(facts([wo(4, "Monday", type="Long Run", minutes=250, done=True)]))


def test_block_done_on_phase_change():
    ws = [wo(3, "Monday", phase="base"), wo(4, "Monday", phase="build")]
    assert by_code(facts(ws), "block_done").params == {"phase": "base"}


def test_new_result():
    f = facts(new_result={"race_name": "Dalat 21K", "finish_time_sec": 10080})
    assert by_code(f, "new_result").params == {"race": "Dalat 21K", "finish_time_sec": 10080}


# --- ordering and stats ------------------------------------------------------


def test_status_prefers_act_now_over_highlight():
    ws = [wo(4, "Tuesday", missed=True, reason="pain")]
    f = facts(
        ws, plan=plan(race_date=(TODAY + timedelta(days=9)).isoformat()), last_activity_at=NOW - timedelta(days=6)
    )
    sig = signals_for(f)
    assert [s.severity for s in sig] == sorted(
        (s.severity for s in sig), key=["act_now", "review_build", "check_in", "highlight"].index
    )
    assert status_of(sig) == "act_now"


def test_highlights_alone_are_on_track():
    f = facts(plan=plan(race_date=(TODAY + timedelta(days=9)).isoformat()))
    assert status_of(signals_for(f)) == "on_track"


def test_week_stats_excludes_rest_and_counts_key():
    ws = [
        wo(4, "Monday", done=True, minutes=40),
        wo(4, "Tuesday", type="Tempo", minutes=60, done=True),
        wo(4, "Wednesday", type="Rest", minutes=0),
        wo(4, "Saturday", type="Long Run", minutes=120),
    ]
    assert week_stats(ws, 4) == {
        "sessions_planned": 3,
        "sessions_done": 2,
        "key_planned": 2,
        "key_done": 1,
        "minutes_planned": 220,
        "minutes_done": 100,
    }
