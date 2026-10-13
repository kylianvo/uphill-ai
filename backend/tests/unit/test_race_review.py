import pytest


def module():
    from services import race_review

    return race_review


def course(cid=10, **changes):
    payload = {
        "race_name": "Mountain Trail",
        "aliases": ["MT"],
        "race_type": "trail",
        "distances": [{"label": "50 km", "distance_km": 50, "elevation_gain_m": 2200}],
        "location": "Mountain Town",
        "terrain": ["singletrack"],
        "key_climbs": ["Summit climb"],
        "climate": {"notes": "Cool mornings"},
        "runner_reviews": ["Curated observation"],
        "edition_year": 2026,
        "source_urls": ["https://example.org/course"],
        "verified_at": "2026-10-13",
        "results": [
            {"year": 2024, "distance_label": "50 km", "distance_km": 50, "winner_time": "4:00:00"},
            {"year": 2026, "distance_label": "50 km", "distance_km": 50, "winner_time": "3:30:00"},
        ],
    }
    payload.update(changes)
    return {"id": cid, "title": "Mountain Trail", "source_label": "Organizer", "payload": payload}


def result(**changes):
    row = dict(
        id=1,
        race_name="Mountain Trail",
        race_date="2024-06-01",
        distance_km=50,
        discipline="trail",
        selected=True,
        is_dnf=False,
        finish_time_sec=22000,
        hidden=False,
    )
    row.update(changes)
    return row


def test_newer_profile_is_labeled_and_benchmarks_use_exact_year(monkeypatch):
    review = module()
    chunk = course()
    monkeypatch.setattr(review, "score_race_course_chunks", lambda name, chunks: [(chunk, 100)])
    context = review.select_course_context(result(), [chunk])
    assert context["course"]["edition_status"] == "different"
    assert review.historical_field(chunk["payload"], "50 km", 50, 2024)["winner_time"] == "4:00:00"
    assert review.historical_field(chunk["payload"], "50 km", 50, 2025) is None
    assert review.historical_field(chunk["payload"], "100 km", 100, 2024) is None


def test_close_scores_require_choice_and_reject_unrelated_id(monkeypatch):
    review = module()
    a, b = course(), course(11, race_name="Mountain Trail North")
    monkeypatch.setattr(review, "score_race_course_chunks", lambda name, chunks: [(a, 96), (b, 93)])
    context = review.select_course_context(result(), [a, b])
    assert context["status"] == "ambiguous" and context["course"] is None
    assert len(context["candidates"]) == 2
    assert review.select_course_context(result(), [a, b], 11)["course"]["id"] == 11
    with pytest.raises(ValueError):
        review.select_course_context(result(), [a, b], 999)


@pytest.mark.parametrize("changes", [{"distance_km": 100}, {"discipline": "road"}])
def test_course_compatibility_is_required(changes):
    context = module().select_course_context(result(**changes), [course()])
    assert context["status"] == "missing"


def test_exact_name_reaches_real_matching_and_unknown_edition():
    review = module()
    assert review.select_course_context(result(), [course(edition_year=None)])["course"]["edition_status"] == "unknown"
    assert review.select_course_context(result(), [course(edition_year=2024)])["course"]["edition_status"] == "same"
    assert review.select_course_context(result(race_name="Unrelated Marathon"), [course()])["status"] == "missing"


def test_missing_context_and_duplicate_benchmarks_are_not_guessed():
    review = module()
    assert review.select_course_context(result(), [])["status"] == "missing"
    with pytest.raises(ValueError):
        review.select_course_context(result(), [], 10)
    payload = course()["payload"]
    payload["results"].append(dict(payload["results"][0]))
    assert review.historical_field(payload, "50 km", 50, 2024) is None


@pytest.mark.parametrize(
    "rank,total,dnf,expected",
    [
        (30, 100, False, 30.0),
        (1, 100, False, 1.0),
        (None, 100, False, None),
        (30, None, False, None),
        (101, 100, False, None),
        (0, 100, False, None),
        (30, 100, True, None),
    ],
)
def test_field_position_is_not_fabricated(rank, total, dnf, expected):
    assert module().top_position_pct(rank, total, dnf) == expected


def test_previous_finish_requires_safe_identity_and_comparable_distance():
    current = result(
        id=2,
        race_name="City Marathon",
        race_date="2025-01-01",
        discipline="road",
        distance_km=42.195,
        finish_time_sec=13154,
    )
    prior = {**current, "id": 1, "race_date": "2024-01-01", "finish_time_sec": 14000}
    assert module().previous_finish(current, [prior], {})["delta_sec"] == -846
    assert module().previous_finish(current, [{**prior, "race_name": "Other City Marathon"}], {}) is None
    assert module().previous_finish(current, [{**prior, "distance_km": 21.0975}], {}) is None
    assert module().previous_finish({**current, "is_dnf": True}, [prior], {}) is None
    assert module().previous_finish(current, [{**prior, "selected": False}], {}) is None
    assert (
        module().previous_finish(current, [{**prior, "race_name": "Other course"}], {2: 10, 1: 10})["delta_sec"] == -846
    )
