import re
from datetime import UTC, datetime

import pytest

from services import notification_copy as copy
from services.notification_copy import render_notification
from tests.unit.test_notification_rules import context

FRI_0700 = datetime(2026, 10, 15, 20, tzinfo=UTC)  # Fri 16 Oct, Sydney
MON_0730 = datetime(2026, 10, 11, 20, 30, tzinfo=UTC)  # Mon 12 Oct, Sydney


def ctx(lang="en", **plan):
    c = context()
    c["preferences"]["language"] = lang
    c["plan"].update(total_weeks=16, **plan)
    c["activities"] = []
    return c


def workout_event(c, **w):
    c["workouts"][0].update(w)
    return dict(kind="workout", source={"workout_id": 1}, due_at=FRI_0700)


def test_long_run_purpose_names_the_race():
    c = ctx(race_name="UTMB 100K")
    title, body = render_notification(workout_event(c, type="Long Run", title="Long run", duration_minutes=150), c)
    assert title == "Long run"
    assert body.endswith("Time on feet for UTMB 100K. Easy is the point.")


def test_missing_race_and_d_plus_fall_back_to_race_day():
    c = ctx(race_name=None, course_elevation_gain_m=None)
    _, body = render_notification(workout_event(c, type="Long Run"), c)
    assert body.endswith("Time on feet for race day. Easy is the point.")
    _, body = render_notification(workout_event(c, type="Hill Repeat"), c)
    assert body.endswith("Climbing strength for race day.")
    assert "None" not in body and " 0 m" not in body
    c = ctx("vi", race_name="UTMB 100K", course_elevation_gain_m=6100)
    _, body = render_notification(workout_event(c, type="Hill Repeat"), c)
    assert body.endswith("Sức leo cho 6100 m D+ của UTMB 100K.")


def test_taper_phase_overrides_session_purpose():
    c = ctx()
    _, body = render_notification(workout_event(c, type="Long Run", phase="Taper"), c)
    assert body.endswith("Taper week: less is more. Stay fresh.")


def test_week_brief_title_and_today_suffix_en_vi():
    c = ctx()
    c["workouts"] = [
        dict(c["workouts"][0], id=1, day_of_week="Monday", title="Easy Run", duration_minutes=45, phase="Build"),
        dict(
            c["workouts"][0],
            id=2,
            day_of_week="Saturday",
            title="Long climb",
            duration_minutes=150,
            phase="Build",
            is_priority=1,
        ),
    ]
    event = dict(kind="week_brief", source={"week_number": 1}, due_at=MON_0730)
    title, body = render_notification(event, c)
    assert title == "Week 1 of 16: Build"
    assert body == "2 sessions, 3.5 h. Key session: Long climb on Saturday. Today: Easy Run, 45 min."
    c["preferences"]["language"] = "vi"
    title, body = render_notification(event, c)
    assert title == "Tuần 1/16: Build"
    assert body == "2 buổi, 3.5 giờ. Buổi chính: Long climb (Thứ Bảy). Hôm nay: Easy Run, 45 phút."


def recognition(c, **activity):
    a = (
        dict(
            id=70,
            start_time=FRI_0700,
            duration_seconds=9660,
            distance_km=18,
            elevation_gain_m=820,
            matched_workout_id=1,
        )
        | activity
    )
    c["activities"] = [a]
    c["workouts"][0].update(title="Long run")
    return dict(kind="recognition", source={"workout_id": 1, "activity_id": 70})


def test_recognition_highlight_only_when_true():
    c = ctx()
    event = recognition(c)
    title, body = render_notification(event, c)
    assert title == "Nice work on Long run"
    assert body == "18 km and 820 m D+ in 2h41. Your biggest climb of this plan so far. Tap to log how it felt."
    c["activities"].append(dict(c["activities"][0], id=71, elevation_gain_m=1200, distance_km=10, matched_workout_id=1))
    assert "Your longest run of this plan so far." in render_notification(event, c)[1]
    c["activities"].append(dict(c["activities"][0], id=72, distance_km=30, matched_workout_id=1))
    assert "so far" not in render_notification(event, c)[1]


def test_unlogged_copy_names_the_session():
    c = ctx()
    c["workouts"][0].update(title="Tempo", day_of_week="Thursday")
    event = dict(kind="unlogged", source={"workout_id": 1})
    assert render_notification(event, c) == (
        "Missed Thursday's Tempo?",
        "No stress. Tap to adjust this week around it.",
    )
    c["preferences"]["language"] = "vi"
    assert render_notification(event, c) == ("Lỡ buổi Tempo hôm Thứ Năm?", "Không sao. Chạm để chỉnh lại tuần này.")


KINDS = ["workout", "week_brief", "recognition", "unlogged", "planning", "plan_ready", "checklist"]


@pytest.mark.parametrize("lang", ["en", "vi"])
@pytest.mark.parametrize("kind", KINDS)
def test_every_kind_renders_with_optional_values_missing(kind, lang):
    c = ctx(lang, race_name=None, course_elevation_gain_m=None)
    c["workouts"][0].update(title=None, target_zone=None, distance_km=None, phase=None, type=None)
    sources = dict(
        workout={"workout_id": 1},
        week_brief={"week_number": 1},
        unlogged={"workout_id": 1},
        recognition={"workout_id": 1, "activity_id": 70},
    )
    if kind == "recognition":
        recognition(c, elevation_gain_m=None)
        c["workouts"][0]["title"] = None
    title, body = render_notification(dict(kind=kind, source=sources.get(kind, {}), due_at=MON_0730), c)
    assert title and body and "None" not in title + body and "{" not in title + body


BANNED = "thể tích|sinh lý|kiến tạo|bảo chứng|tiếp nhiên liệu|kiểm toán|tuyệt vời|đồng hành|hành trình|bứt phá|giáo án"


def test_vi_copy_has_no_banned_words_or_exclamation_marks():
    vi = " ".join(v[1] for v in copy.PURPOSE.values()) + " ".join(v[1] for v in copy.TEMPLATES.values())
    assert not re.search(BANNED, vi) and "!" not in vi
