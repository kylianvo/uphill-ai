import datetime as dt

from services.coros_workouts import (
    SPORT_REST,
    SPORT_RUNNING,
    build_course,
    build_day,
    parse_hr_range,
    placeholder_course,
    rest_course,
    validate_course,
    workout_kind,
)

APPROVED = dt.datetime(2027, 4, 1, tzinfo=dt.UTC)


def wo(**kw):
    base = {
        "id": 1,
        "title": "Easy Aerobic",
        "type": "Easy",
        "duration_minutes": 45,
        "target_zone": "Zone 2",
        "target_hr_range": "120-135 bpm",
        "description": "Conversational pace.",
        "approved_at": APPROVED,
        "session_slot": "main",
    }
    base.update(kw)
    return base


def test_workout_kind():
    assert workout_kind(wo(type="Easy")) == "run"
    assert workout_kind(wo(type="Long Run")) == "run"
    assert workout_kind(wo(type="Strength")) == "other"
    assert workout_kind(wo(type="Muscular Endurance")) == "other"
    assert workout_kind(wo(type="Rest")) == "rest"
    assert workout_kind(wo(type="")) == "rest"


def test_parse_hr_range_formats():
    assert parse_hr_range("120-135 bpm") == (120, 135)
    assert parse_hr_range("135 – 120") == (120, 135)
    assert parse_hr_range("< 115 bpm") == (100, 115)
    assert parse_hr_range("> 160 bpm") == (160, 170)
    assert parse_hr_range("145 bpm") == (145, 145)
    assert parse_hr_range("") is None
    assert parse_hr_range(None) is None
    assert parse_hr_range("easy") is None
    assert parse_hr_range("< 35") == (30, 35)


def test_easy_run_has_warmup_main_cooldown_with_hr_target():
    c = build_course(wo(), "en")
    assert c["sportType"] == SPORT_RUNNING
    assert c["courseName"] == "Easy Aerobic"
    assert [s["sectionType"] for s in c["sections"]] == [1, 2, 4]
    assert [s["targetValue"] for s in c["sections"]] == [600, 45 * 60 - 900, 300]
    main = c["sections"][1]
    assert main["targetType"] == 2
    assert (main["intensityType"], main["intensityValueStart"], main["intensityValueEnd"]) == (1, 120, 135)
    assert c["sections"][0]["sectionIntensity"] == 1
    assert "Keep heart rate 120–135 bpm." in c["courseDescription"]
    assert validate_course(c) == []


def test_short_run_is_single_section():
    c = build_course(wo(duration_minutes=20), "en")
    assert len(c["sections"]) == 1
    assert c["sections"][0]["targetValue"] == 1200
    assert validate_course(c) == []


def test_missing_hr_range_falls_back_to_zone():
    c = build_course(wo(target_hr_range=None, target_zone="Zone 3"), "en")
    main = c["sections"][1]
    assert main["intensityType"] == 1 and main["sectionIntensity"] == 3
    assert "intensityValueStart" not in main
    assert validate_course(c) == []


def test_interval_session_builds_group_with_recovery():
    c = build_course(
        wo(
            type="Interval",
            title="6x3min",
            duration_minutes=50,
            target_hr_range="160-172 bpm",
            interval_reps=6,
            interval_rep_value=3,
            interval_rep_unit="min",
        ),
        "en",
    )
    warm, group, cool = c["sections"]
    assert warm["sectionType"] == 1 and cool["sectionType"] == 4
    assert group["intervalGroup"] is True and group["repeats"] == 6
    work, rec = group["sets"]
    assert (work["sectionType"], work["targetType"], work["targetValue"]) == (2, 2, 180)
    assert (work["intensityValueStart"], work["intensityValueEnd"]) == (160, 172)
    assert (rec["sectionType"], rec["targetValue"], rec["sectionIntensity"]) == (3, 90, 1)
    # 50' total - 10' warmup - 6 x 4.5' = 13' cooldown
    assert cool["targetValue"] == 50 * 60 - 600 - 6 * 270
    assert "intensityType" not in group and "targetType" not in group
    assert validate_course(c) == []


def test_distance_intervals_and_repeat_cap():
    c = build_course(
        wo(type="Interval", interval_reps=25, interval_rep_value=400, interval_rep_unit="m", walk_interval_value=200),
        "en",
    )
    group = c["sections"][1]
    assert group["repeats"] == 20
    work, rec = group["sets"]
    assert (work["targetType"], work["targetValue"], rec["targetValue"]) == (1, 400, 200)
    assert c["sections"][2]["targetValue"] == 300
    assert validate_course(c) == []


def test_walk_run_is_just_the_group():
    c = build_course(
        wo(
            type="Walk/Run",
            duration_minutes=30,
            interval_reps=8,
            interval_rep_value=2,
            interval_rep_unit="min",
            walk_interval_value=1,
        ),
        "en",
    )
    assert len(c["sections"]) == 1
    work, walk = c["sections"][0]["sets"]
    assert (work["targetValue"], walk["targetValue"]) == (120, 60)
    assert validate_course(c) == []


def test_description_includes_climb_and_fueling_and_vi_text():
    c = build_course(wo(elevation_gain_m=450, fueling_tip="Take a gel at 45'."), "vi")
    assert "Khoảng 450 m leo dốc." in c["courseDescription"]
    assert "Giữ nhịp tim 120–135 bpm." in c["courseDescription"]
    assert "Take a gel at 45'." in c["courseDescription"]


def test_long_title_truncated_and_empty_title_falls_back():
    assert len(build_course(wo(title="x" * 150), "en")["courseName"]) == 100
    assert build_course(wo(title=""), "en")["courseName"] == "Easy"


def test_non_runs_and_zero_duration_return_none():
    assert build_course(wo(type="Strength"), "en") is None
    assert build_course(wo(type="Rest"), "en") is None
    assert build_course(wo(duration_minutes=0), "en") is None


def test_rest_and_placeholder_courses():
    r = rest_course("en")
    assert (r["sportType"], r["sections"], r["courseName"]) == (SPORT_REST, [], "Rest")
    assert r["courseDescription"]
    assert rest_course("vi")["courseName"] == "Nghỉ"
    p = placeholder_course(wo(type="Strength", title="Strength – Core & Legs", description="3x10 step-ups"), "en")
    assert (p["sportType"], p["courseName"], p["courseDescription"], p["sections"]) == (
        SPORT_REST,
        "Strength – Core & Legs",
        "3x10 step-ups",
        [],
    )
    assert validate_course(r) == [] and validate_course(p) == []


def test_build_day_rules():
    run = wo(id=1)
    gym = wo(id=2, type="Strength", title="Strength – Core", session_slot="secondary")
    pending = wo(id=3, approved_at=None)
    courses, left = build_day([gym, run], "en")
    assert [c["courseName"] for c in courses] == ["Easy Aerobic"] and left == 1
    courses, left = build_day([gym], "en")
    assert courses[0]["courseName"] == "Strength – Core" and courses[0]["sportType"] == SPORT_REST and left == 0
    courses, left = build_day([], "en")
    assert courses == [rest_course("en")] and left == 0
    courses, left = build_day([pending], "en")
    assert courses == [rest_course("en")] and left == 0
    courses, _ = build_day([wo(id=5, session_slot="secondary", title="Shakeout"), wo(id=6, title="Main")], "en")
    assert [c["courseName"] for c in courses] == ["Main", "Shakeout"]


def test_validate_course_catches_rule_breaks():
    bad = {
        "sportType": 1,
        "courseName": "",
        "courseDescription": "d",
        "sections": [
            {
                "sectionType": 2,
                "targetType": 2,
                "targetValue": 60,
                "intensityType": 1,
                "sectionIntensity": 2,
                "intensityValueStart": 120,
                "intensityValueEnd": 130,
            },
            {"intervalGroup": True, "repeats": 21, "sets": [{"intervalGroup": True}]},
            {
                "sectionType": 2,
                "targetType": 2,
                "targetValue": 60,
                "intensityType": 1,
                "intensityValueStart": 20,
                "intensityValueEnd": 300,
            },
        ],
    }
    errs = validate_course(bad)
    for code in ("name", "intensity_format", "repeats", "nested_group", "hr_bounds"):
        assert code in errs
    assert "empty_sections" in validate_course({**bad, "courseName": "x", "sections": []})
    assert "rest_sections" in validate_course(
        {"sportType": 4, "courseName": "R", "courseDescription": "d", "sections": [{"sectionType": 2}]}
    )
