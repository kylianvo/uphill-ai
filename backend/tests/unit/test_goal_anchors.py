from datetime import date

import pytest

from services import goal_anchors

AS_OF = date(2026, 9, 26)
CURVE = [(5.0, 400.0), (10.0, 420.0), (25.0, 460.0), (50.0, 520.0), (75.0, 580.0), (90.0, 620.0)]


def _target(field=True):
    return {
        "race_name": "Target 70K",
        "distance_km": 70.0,
        "elevation_gain_m": 3000.0,
        "terrain": [],
        "checkpoints": None,
        "profile_source": "synthetic",
        "field": {"curve": CURVE, "winner_mins": 380.0, "fastest_winner_mins": 370.0} if field else None,
    }


def _result(rid, **kw):
    base = {
        "id": rid,
        "race_name": f"Race {rid}",
        "race_date": "2025-06-01",
        "distance_km": 50.0,
        "elevation_gain_m": 2000.0,
        "finish_time_sec": 7 * 3600,
        "is_dnf": False,
        "discipline": "trail",
        "source": "utmb",
        "rank_overall": None,
        "total_overall": None,
    }
    return {**base, **kw}


@pytest.fixture(autouse=True)
def _no_kb(monkeypatch):
    monkeypatch.setattr(
        goal_anchors,
        "resolve_course",
        lambda name, km, gain: {
            "terrain": [],
            "checkpoints": None,
            "profile_source": "synthetic",
            "field": None,
        },
    )


def test_one_physics_anchor_per_usable_result():
    anchors = goal_anchors.compute_anchors(_target(), [_result(1), _result(2, distance_km=60.0)], as_of=AS_OF)
    assert [a["id"] for a in anchors] == ["phys_r2", "phys_r1"]  # 60 km is closer to 70 km
    assert all(a["minutes"] > 0 for a in anchors)


def test_dnf_and_old_results_are_not_anchors():
    results = [_result(1, is_dnf=True, finish_time_sec=None), _result(2, race_date="2020-01-01")]
    assert goal_anchors.compute_anchors(_target(field=False), results, as_of=AS_OF) == []


def test_field_rank_anchor_uses_own_rank_on_target_curve():
    anchors = goal_anchors.compute_anchors(_target(), [_result(1, rank_overall=25, total_overall=100)], as_of=AS_OF)
    rank = next(a for a in anchors if a["method"] == "field_rank")
    assert rank["minutes"] == pytest.approx(460.0)
    assert "finished p25 of 100" in rank["notes"]


def test_percentile_transfer_when_reference_has_curve(monkeypatch):
    monkeypatch.setattr(
        goal_anchors,
        "resolve_course",
        lambda name, km, gain: {"terrain": [], "checkpoints": None, "profile_source": "gpx", "field": {"curve": CURVE}},
    )
    anchors = goal_anchors.compute_anchors(_target(), [_result(1, finish_time_sec=520 * 60)], as_of=AS_OF)
    pct = next(a for a in anchors if a["method"] == "percentile_transfer")
    assert pct["minutes"] == pytest.approx(520.0)


def test_road_and_long_ago_results_carry_quality_notes():
    anchors = goal_anchors.compute_anchors(
        _target(), [_result(1, discipline="road", distance_km=21.1, source="manual")], as_of=AS_OF
    )
    notes = anchors[0]["notes"]
    assert "road result" in notes
    assert "self-reported" in notes
    assert any(n.startswith("distance 21 km") for n in notes)


def test_trail_results_rank_before_road():
    picked = goal_anchors.select_anchor_results(
        [_result(1, discipline="road", distance_km=70.0), _result(2, distance_km=30.0)], 70.0, AS_OF
    )
    assert [r["id"] for r in picked] == [2, 1]


def test_field_prior_without_results():
    anchors = goal_anchors.compute_anchors(_target(), [], weekly_km=55.0, ultra_finishes=1, as_of=AS_OF)
    assert [a["id"] for a in anchors] == ["prior_field"]
    # 55 km/week -> p55, one ultra -> p45; between p25 (460) and p50 (520)
    assert 460.0 < anchors[0]["minutes"] < 520.0


def test_easy_pace_prior_when_no_field_curve():
    anchors = goal_anchors.compute_anchors(_target(field=False), [], weekly_km=40.0, easy_pace_min_km=6.5, as_of=AS_OF)
    assert [a["method"] for a in anchors] == ["easy_pace"]


def test_no_data_means_no_anchors():
    assert goal_anchors.compute_anchors(_target(field=False), [], as_of=AS_OF) == []
