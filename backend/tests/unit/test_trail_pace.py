from services.trail_pace import trail_minutes, trail_pace_range, trail_session


def test_quang_example_flat_5_00_at_50_m_per_km_is_8_00():
    assert trail_pace_range("5:00 /km", 50) == "8:00 /km"


def test_nui_dinh_3_5h_for_quang():
    pace, km, dplus = trail_session("4:54 - 4:30 /km", 210, 60)
    assert pace == "8:26 - 7:44 /km"
    assert 25.0 <= km <= 26.5
    assert dplus == round(km * 60)


def test_zero_climb_is_flat():
    assert trail_session("5:00 - 4:30 /km", 60, 0)[0] == "5:00 - 4:30 /km"


def test_minutes_round_trips_session():
    _, km, dplus = trail_session("4:54 - 4:30 /km", 210, 60)
    assert abs(trail_minutes("4:54 - 4:30 /km", km, dplus) - 210) < 2
