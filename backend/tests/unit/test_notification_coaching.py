from datetime import UTC, datetime, timedelta

from services.notification_rules import candidates
from tests.unit.test_notification_rules import context


def test_checkin_distinguishes_athlete_skip():
    c = context()
    now = datetime(2026, 10, 16, 7, tzinfo=UTC)  # 18:00 Sydney, rest day
    c["workouts"] = [
        dict(c["workouts"][0], day_of_week=d, id=i, is_missed=1, missed_origin="matching")
        for i, d in enumerate(("Monday", "Tuesday"), 1)
    ]
    assert any(x["kind"] == "unlogged" for x in candidates(c, now))
    for w in c["workouts"]:
        w["missed_origin"] = "athlete"
    assert not any(x["kind"] == "unlogged" for x in candidates(c, now))


def test_taper_and_race_need_reviewed_content():
    c = context()
    now = datetime(2026, 10, 16, 7, tzinfo=UTC)  # 18:00 Sydney, the coaching slot
    c["plan"]["race_date"] = "2026-10-23"
    c["cards"] = [dict(id=4, topic="Race", tags='["race"]', lang="en", notification_reviewed=True)]
    assert any(x["kind"] == "race" for x in candidates(c, now))
    c["cards"] = []
    assert not any(x["kind"] == "race" for x in candidates(c, now))


def test_checklist_respects_snooze():
    c = context()
    c["workouts"] = []
    now = datetime(2026, 10, 16, 7, tzinfo=UTC)
    assert any(x["kind"] == "checklist" for x in candidates(c, now))
    c["preferences"]["checklist_snoozed_until"] = now + timedelta(days=14)
    assert not any(x["kind"] == "checklist" for x in candidates(c, now))


def test_estimated_profile_fields_stay_incomplete():
    from services.notification_rules import checklist_items

    c = context()
    c["user"].update(
        aet_hr=140, ant_hr=170, onboarding_complete=True, profile_field_sources={"aet_hr": {"source": "estimate"}}
    )
    assert dict(checklist_items(c))["hr"] is False


def test_new_taper_segment_after_build_phase():
    c = context()
    now = datetime(2026, 10, 16, 7, tzinfo=UTC)  # 18:00 Sydney, the coaching slot
    first = c["workouts"][0]
    c["workouts"] = [
        dict(first, id=1, day_of_week="Monday", phase="Taper"),
        dict(first, id=2, day_of_week="Wednesday", phase="Build"),
        dict(first, id=3, day_of_week="Friday", phase="Taper"),
    ]
    c["cards"] = [dict(id=4, topic="Taper", tags="[]", lang="en", notification_reviewed=True)]
    assert any(x["kind"] == "taper" and x["event_key"].endswith("2026-10-16") for x in candidates(c, now))


def test_claim_does_not_suppress_its_own_coaching_event():
    from services.notifications import still_eligible

    c = context()
    c["workouts"] = []
    now = datetime(2026, 10, 16, 7, tzinfo=UTC)
    event = next(x for x in candidates(c, now) if x["kind"] == "checklist")
    event.update(id="claimed", claimed_at=now, status="sending")
    c["history"] = [event]
    assert still_eligible(event, c, now)


def test_synthetic_race_date_does_not_trigger_race_advice():
    c = context()
    now = datetime(2026, 10, 15, 20, tzinfo=UTC)
    c["plan"].update(goal_type="start_running", race_date="2026-10-23")
    c["cards"] = [dict(id=4, topic="Race", tags="[]", lang="en", notification_reviewed=True)]
    assert not any(x["kind"] == "race" for x in candidates(c, now))


# --- v2 kinds ------------------------------------------------------------------------------------
MON_0731 = datetime(2026, 10, 11, 20, 31, tzinfo=UTC)  # Mon 12 Oct 07:31 Sydney, plan week 1


def kinds(c, now):
    return [x["kind"] for x in candidates(c, now)]


def test_week_brief_only_on_monday_with_workouts():
    c = context()
    brief = next(x for x in candidates(c, MON_0731) if x["kind"] == "week_brief")
    assert brief["destination"] == {"kind": "plan", "plan_id": 5, "week_number": 1, "intent": "week"}
    assert "week_brief" not in kinds(c, MON_0731 + timedelta(days=1))  # Tuesday
    c["workouts"] = []
    assert "week_brief" not in kinds(c, MON_0731)


def test_monday_brief_replaces_workout_reminder():
    c = context()
    c["workouts"].append(dict(c["workouts"][0], id=9, day_of_week="Monday"))
    found = kinds(c, MON_0731)
    assert "week_brief" in found and "workout" not in found


def priority_run(c):
    c["workouts"][0].update(is_priority=1, is_completed=1, type="Tempo")
    start = datetime(2026, 10, 15, 19, tzinfo=UTC)  # Fri 06:00 Sydney
    c["activities"] = [
        dict(id=70, start_time=start, duration_seconds=7200, distance_km=18, elevation_gain_m=820, matched_workout_id=1)
    ]
    return start + timedelta(hours=2)  # activity end


def test_recognition_requires_matched_activity():
    c = context()
    end = priority_run(c)
    assert "recognition" in kinds(c, end + timedelta(minutes=31))
    c["activities"] = []
    assert "recognition" not in kinds(c, end + timedelta(minutes=31))


def test_recognition_due_30_min_after_activity_end():
    c = context()
    end = priority_run(c)
    assert "recognition" not in kinds(c, end + timedelta(minutes=29))
    event = next(x for x in candidates(c, end + timedelta(minutes=31)) if x["kind"] == "recognition")
    assert event["due_at"] == end + timedelta(minutes=30)
    assert event["source"] == {"workout_id": 1, "activity_id": 70}


def test_recognition_expires_24h_after_activity_end():
    c = context()
    end = priority_run(c)
    assert "recognition" not in kinds(c, end + timedelta(hours=24, minutes=1))


def test_unlogged_names_the_priority_session_and_opens_adapt():
    c = context()
    now = datetime(2026, 10, 16, 7, tzinfo=UTC)  # Fri 18:00 Sydney
    c["workouts"] = [
        dict(c["workouts"][0], id=1, day_of_week="Monday", duration_minutes=45),
        dict(c["workouts"][0], id=2, day_of_week="Tuesday", duration_minutes=30, is_priority=1),
    ]
    event = next(x for x in candidates(c, now) if x["kind"] == "unlogged")
    assert event["destination"] == {"kind": "plan", "plan_id": 5, "week_number": 1, "intent": "adapt"}
    assert event["source"] == {"workout_id": 2}


def test_recovery_is_retired():
    c = context()
    end = priority_run(c)
    c["workouts"][0]["first_completed_at"] = end
    assert "recovery" not in kinds(c, end + timedelta(hours=10))


def test_checklist_waits_30_days():
    c = context()
    c["workouts"] = []
    now = datetime(2026, 10, 16, 7, tzinfo=UTC)
    c["history"] = [
        dict(id="c", kind="checklist", status="accepted", claimed_at=now - timedelta(days=20), opened_at=now)
    ]
    assert "checklist" not in kinds(c, now)
    c["history"][0]["claimed_at"] = now - timedelta(days=31)
    assert "checklist" in kinds(c, now)


def test_muted_brief_does_not_swallow_monday_workout_reminder():
    c = context()
    c["workouts"].append(dict(c["workouts"][0], id=9, day_of_week="Monday"))
    c["preferences"]["muted_kinds"] = ["week_brief"]
    assert kinds(c, datetime(2026, 10, 11, 20, 1, tzinfo=UTC)) == ["workout"]  # Mon 07:01
