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
