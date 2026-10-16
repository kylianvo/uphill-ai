import pytest

from services.training_mountains import MOUNTAINS, default_min_minutes, long_run_climb_rate


@pytest.mark.parametrize(
    "key, rate", [("nui_dinh", 60), ("chau_thoi", 28), ("ba_den", 60), ("ham_lon", 45), (None, None), ("unknown", None)]
)
def test_long_run_climb_rate(key, rate):
    assert long_run_climb_rate(key) == rate


@pytest.mark.parametrize("key, minutes", [("chau_thoi", 180), ("ham_lon", 180), ("sapa", None), (None, None)])
def test_default_min_minutes(key, minutes):
    assert default_min_minutes(key) == minutes


def test_curated_mountain_values():
    assert {key: m.climb_rate for key, m in MOUNTAINS.items()} == {
        "nui_dinh": 60,
        "chau_thoi": 28,
        "chua_chan": 85,
        "ba_den": 176,
        "ham_lon": 45,
        "dalat": 47,
        "sapa": 56,
    }
    assert MOUNTAINS["ba_den"].repeats_only


def test_chau_thoi_is_hcmc_long_run_mountain():
    mountain = MOUNTAINS["chau_thoi"]
    assert mountain.area == "hcmc"
    assert mountain.name_en == mountain.name_vi == "Núi Châu Thới"
    assert not mountain.repeats_only
