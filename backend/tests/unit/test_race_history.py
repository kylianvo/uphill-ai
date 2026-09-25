from datetime import date

from services.race_history import _dedupe, _name_filter, normalize_name, normalize_utmb, normalize_vbm


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


def test_vbm_ultra_distance_only_for_the_pr_race():
    # jp_bxh_athlete: other_results_full carries no distance, only the parent
    # (PR) row does -- other ultras must not inherit it.
    parent = {
        "event": "ULTRA_TRAIL",
        "distance_km": 250,
        "mark_sec": 200219,
        "bib": "25140",
        "race_full_name": "PRENN TRAIL SUMMIT 25/01/2026",
        "result_url": "https://5bib.com/x",
    }
    pr = {"race": "PRENN TRAIL SUMMIT 25/01/2026", "time": "55:36:59", "total_sec": 200219, "bib": "25140"}
    other = {"race": "BRAH YANG TRAIL SUMMIT 2026 03/03/2026", "time": "28:58:29", "total_sec": 104309, "bib": "100147"}
    own = normalize_vbm(parent, pr)
    assert own and own["distance_km"] == 250 and own["result_url"] == "https://5bib.com/x"
    assert normalize_vbm(parent, other) is None


def test_vbm_marathon_link_stays_on_its_own_race():
    parent = {
        "event": "FMM",
        "mark_sec": 13154,
        "bib": "47107",
        "result_url": "https://sportstats.one/results/1",
        "race_full_name": "CAN THO HERITAGE MARATHON 03/12/2023",
    }
    other = normalize_vbm(parent, {"race": "OTHER MARATHON 04/12/2022", "time": "03:42:00", "bib": "99999"})
    assert other and other["distance_km"] == 42.195 and other["result_url"] is None


def test_name_filter_matches_each_word_as_a_prefix_in_any_order():
    where, order, params = _name_filter("Trần Hoa")
    assert where.count("LIKE") == 2
    assert sorted(params[k] for k in ("t0", "t1")) == ["% HOA%", "% TRAN%"]
    assert sorted(params[k] for k in ("w0", "w1")) == ["% HOA %", "% TRAN %"]
    assert order.startswith("(")
    assert _name_filter("  ") is None
