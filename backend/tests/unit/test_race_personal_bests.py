from datetime import date


def prs(rows):
    from services.race_personal_bests import compute_road_prs

    return compute_road_prs(rows, date(2026, 10, 13))


def row(**changes):
    value = dict(
        id=1,
        race_date="2023-12-03",
        discipline="road",
        distance_km=42.195,
        selected=True,
        hidden=False,
        is_dnf=False,
        finish_time_sec=13154,
    )
    value.update(changes)
    return value


def test_pending_trail_dnf_and_hidden_have_correct_pb_semantics():
    results = prs(
        [
            row(hidden=True),
            row(id=2, selected=False, finish_time_sec=12000),
            row(id=3, discipline="trail", finish_time_sec=11000),
            row(id=4, is_dnf=True, finish_time_sec=None),
        ]
    )
    assert results["fm"] == {"result_id": 1, "time_sec": 13154, "date": "2023-12-03", "stale": True}
    assert all(results[k] is None for k in ["5k", "10k", "hm"])


def test_ties_use_latest_date_then_lowest_id():
    result = prs([row(), row(id=4, race_date="2026-09-01"), row(id=2, race_date="2026-09-01")])
    assert result["fm"]["result_id"] == 2 and result["fm"]["stale"] is False


def test_distance_tolerance_and_empty_records():
    result = prs(
        [
            row(distance_km=5.05, finish_time_sec=1200),
            row(id=2, distance_km=5.11, finish_time_sec=1100),
            row(id=3, distance_km=10.1, finish_time_sec=2500),
            row(id=4, distance_km=10.3, finish_time_sec=2400),
        ]
    )
    assert result["5k"]["time_sec"] == 1200 and result["10k"]["time_sec"] == 2500
    assert all(value is None for value in prs([]).values())


def test_confirmed_half_marathon_uses_recorded_time():
    result = prs([row(distance_km=21.0975, race_date="2023-11-19", finish_time_sec=6244)])
    assert result["hm"]["time_sec"] == 6244 and result["fm"] is None
