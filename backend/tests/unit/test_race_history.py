from datetime import date

from services.race_history import _dedupe, normalize_name, normalize_utmb, normalize_vbm


def test_vietnamese_name_normalization_is_order_insensitive():
    assert normalize_name("Võ Văn Việt") == normalize_name("Viet Van Vo")
    assert normalize_name("Đặng An") == normalize_name("An Dang")


def test_vbm_qualifying_result_parses_dd_mm_yyyy_and_has_stable_key():
    parent = {"event": "FMM", "race_full_name": "CAN THO HERITAGE MARATHON 03/12/2023", "bib": "47107"}
    first = {"race": parent["race_full_name"], "time": "03:39:14", "bib": "47107", "rank": 30}
    later_rank = {**first, "rank": 31}
    a = normalize_vbm(parent, first)
    b = normalize_vbm(parent, later_rank)
    assert a and b
    assert a["race_date"] == "2023-12-03"
    assert a["distance_km"] == 42.195
    assert a["finish_time_sec"] == 13154
    assert a["source_key"] == b["source_key"]


def test_utmb_dnf_and_missing_time_are_distinct():
    base = {"dateIso": "2026-08-27", "raceYearId": 121330, "race": "OCC", "distance": "60.00"}
    assert normalize_utmb({**base, "isDnf": True})["finish_time_sec"] is None
    assert normalize_utmb({**base, "isDnf": False}) is None


def test_deduplication_requires_same_race_name_as_well_as_numbers():
    base = {
        "source": "utmb",
        "race_date": date(2025, 1, 1).isoformat(),
        "distance_km": 50,
        "finish_time_sec": 20000,
        "is_dnf": False,
        "race_name": "Vietnam Mountain Marathon",
        "elevation_gain_m": 2000,
    }
    rows = _dedupe([base, {**base, "source": "manual"}, {**base, "race_name": "Another Race"}])
    assert len(rows) == 2
