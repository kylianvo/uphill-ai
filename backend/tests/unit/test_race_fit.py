from services import race_fit

PLAN = {"race_name": "VHT 100K", "course_distance_km": 104.2, "course_elevation_gain_m": 5533, "cutoff_time_hours": 29}


def test_mountain_day_compares_its_climb_with_the_race():
    wo = {"type": "Easy", "duration_minutes": 180, "distance_km": 12, "elevation_gain_m": 700}
    assert (
        race_fit.line(PLAN, wo)
        == "VHT 100K climbs about 53 m per km. Today: 700 m over 12 km (58 m/km), as steep as the race."
    )
    assert race_fit.line(PLAN, wo, vi=True).startswith("VHT 100K leo khoảng 53 m mỗi km")


def test_long_run_is_measured_against_race_day():
    wo = {"type": "Long Run", "duration_minutes": 210, "distance_km": 20, "elevation_gain_m": 0}
    assert race_fit.line(PLAN, wo) == "3 h 30 on your feet, of the 29 h cutoff at VHT 100K."
    assert race_fit.line({**PLAN, "target_time_hours": 24}, wo) == (
        "3 h 30 on your feet, of the 24 h you're aiming for at VHT 100K."
    )


def test_no_line_where_there_is_nothing_true_to_say():
    assert race_fit.line(PLAN, {"type": "Easy", "duration_minutes": 40, "distance_km": 7}) is None
    assert race_fit.line({"race_name": "5K"}, {"type": "Long Run", "duration_minutes": 120}) is None
    assert race_fit.line(PLAN, {"type": "Race", "duration_minutes": 1500}) is None
