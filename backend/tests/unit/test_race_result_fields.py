import pytest


def record(**changes):
    value = dict(
        discipline="road",
        race_name="City Marathon",
        race_date="2023-12-03",
        distance_km=42.195,
        finish_time_sec=13154,
        is_dnf=False,
    )
    value.update(changes)
    return value


def normalize(value):
    from services.race_result_fields import normalize_manual_result

    return normalize_manual_result(value)


def test_optional_strings_and_dnf_are_normalized():
    value = normalize(record(location="  Can Tho  ", bib=" ", result_url="", is_dnf=True))
    assert value["location"] == "Can Tho"
    assert value["bib"] is None and value["result_url"] is None
    assert value["finish_time_sec"] is None


@pytest.mark.parametrize("url", ["javascript:alert(1)", "file:///tmp/result", "https://a:b@example.org/r", "https://"])
def test_unsafe_url_is_rejected(url):
    with pytest.raises(ValueError, match="Result URL"):
        normalize(record(result_url=url))


@pytest.mark.parametrize(
    "fields",
    [
        {"rank_overall": 3, "total_overall": 2},
        {"rank_gender": 0},
        {"rank_age_group": 12, "total_age_group": 10},
        {"elevation_gain_m": -1},
        {"location": "x" * 201},
        {"distance_km": float("nan")},
        {"elevation_gain_m": float("inf")},
        {"rank_overall": True},
        {"finish_time_sec": 0},
        {"race_name": " "},
    ],
)
def test_invalid_metadata_is_rejected(fields):
    with pytest.raises(ValueError):
        normalize(record(**fields))


def test_optional_numeric_zero_and_http_url_survive():
    value = normalize(
        record(elevation_gain_m=0, result_url="https://example.org/result", rank_gender=2, total_gender=5)
    )
    assert value["elevation_gain_m"] == 0
    assert value["rank_gender"] == 2 and value["result_url"] == "https://example.org/result"
