"""Round-trip tests for the kb_chunks data-access functions in db.py."""

from db import clear_kb_chunks, get_kb_chunk_count, get_kb_chunks, save_kb_chunks


def _sample_chunks():
    return [
        {
            "domain": "gear",
            "kind": "catalog_item",
            "title": "Speedgoat 7",
            "content": "Hoka Speedgoat 7 — cushioned trail shoe.",
            "payload": {"brand": "Hoka", "price": "$155", "pros": "Grippy, plush", "cons": "Heavy"},
        },
        {
            "domain": "scheduler",
            "kind": "principle",
            "title": "ME circuit design",
            "content": "ME sessions are circuits: one pass per exercise, 6-8 rounds, short rests.",
            "payload": None,
        },
    ]


def test_save_and_get_kb_chunks_roundtrip(_init_test_database):
    saved = save_kb_chunks(_sample_chunks())
    assert saved == 2

    gear = get_kb_chunks("gear")
    assert len(gear) == 1
    assert gear[0]["title"] == "Speedgoat 7"
    assert gear[0]["payload"]["brand"] == "Hoka"  # JSONB round-trips as dict
    assert gear[0]["content_hash"]  # auto-computed

    principles = get_kb_chunks("scheduler", kind="principle")
    assert len(principles) == 1
    assert principles[0]["payload"] is None


def test_clear_kb_chunks_is_domain_scoped(_init_test_database):
    save_kb_chunks(_sample_chunks())
    clear_kb_chunks("gear")
    assert get_kb_chunk_count("gear") == 0
    assert get_kb_chunk_count("scheduler") == 1
    assert get_kb_chunk_count() == 1


def test_replace_kb_chunks_is_atomic(_init_test_database):
    import pytest

    from db import replace_kb_chunks

    save_kb_chunks(_sample_chunks())
    assert get_kb_chunk_count("gear") == 1
    bad_batch = [
        {"domain": "gear", "kind": "catalog_item", "title": "New Shoe", "content": "c", "payload": None},
        # NOT NULL violation — must abort the whole replace, not just this row
        {"domain": None, "kind": "catalog_item", "title": "Broken", "content": "c", "payload": None},
    ]
    with pytest.raises(Exception):
        replace_kb_chunks("gear", bad_batch)
    # the failed replace must not have wiped the existing row
    assert get_kb_chunk_count("gear") == 1
    assert get_kb_chunks("gear")[0]["title"] == "Speedgoat 7"


def test_replace_kb_chunks_swaps_domain_content(_init_test_database):
    from db import replace_kb_chunks

    save_kb_chunks(_sample_chunks())
    replace_kb_chunks(
        "gear", [{"domain": "gear", "kind": "catalog_item", "title": "Tecton X 3", "content": "c", "payload": None}]
    )
    gear = get_kb_chunks("gear")
    assert [c["title"] for c in gear] == ["Tecton X 3"]
    assert get_kb_chunk_count("scheduler") == 1  # other domains untouched


def test_add_kb_chunks_skips_existing_titles_case_insensitively(_init_test_database):
    from db import add_kb_chunks

    save_kb_chunks(_sample_chunks())  # seeds "Speedgoat 7" under gear
    inserted = add_kb_chunks(
        "gear",
        [
            {"domain": "gear", "kind": "catalog_item", "title": "speedgoat 7", "content": "dup", "payload": None},
            {"domain": "gear", "kind": "catalog_item", "title": "Tecton X 3", "content": "new", "payload": None},
        ],
    )
    assert inserted == 1
    titles = sorted(c["title"] for c in get_kb_chunks("gear"))
    assert titles == ["Speedgoat 7", "Tecton X 3"]  # original row untouched, only the new one added


def test_add_kb_chunks_never_deletes_other_domains(_init_test_database):
    from db import add_kb_chunks

    save_kb_chunks(_sample_chunks())  # gear=1, scheduler=1
    add_kb_chunks(
        "gear", [{"domain": "gear", "kind": "catalog_item", "title": "New Row", "content": "c", "payload": None}]
    )
    assert get_kb_chunk_count("gear") == 2
    assert get_kb_chunk_count("scheduler") == 1


def test_replace_kb_chunks_by_kind_only_touches_that_kind(_init_test_database):
    from db import replace_kb_chunks_by_kind

    save_kb_chunks(
        [
            {"domain": "nutrition", "kind": "principle", "title": "Carb targets", "content": "c", "payload": None},
            {
                "domain": "nutrition",
                "kind": "catalog_item",
                "title": "GU Roctane",
                "content": "c",
                "payload": {"brand": "GU"},
            },
        ]
    )
    replace_kb_chunks_by_kind(
        "nutrition",
        "principle",
        [{"domain": "nutrition", "kind": "principle", "title": "Sodium strategy", "content": "c", "payload": None}],
    )
    principles = get_kb_chunks("nutrition", kind="principle")
    catalog = get_kb_chunks("nutrition", kind="catalog_item")
    assert [p["title"] for p in principles] == ["Sodium strategy"]  # old principle replaced
    assert [c["title"] for c in catalog] == ["GU Roctane"]  # catalog_item row untouched


def test_replace_kb_chunks_by_kind_is_atomic(_init_test_database):
    import pytest

    from db import replace_kb_chunks_by_kind

    save_kb_chunks(
        [{"domain": "nutrition", "kind": "principle", "title": "Carb targets", "content": "c", "payload": None}]
    )
    bad_batch = [
        {"domain": "nutrition", "kind": "principle", "title": "New Principle", "content": "c", "payload": None},
        {"domain": None, "kind": "principle", "title": "Broken", "content": "c", "payload": None},
    ]
    with pytest.raises(Exception):
        replace_kb_chunks_by_kind("nutrition", "principle", bad_batch)
    principles = get_kb_chunks("nutrition", kind="principle")
    assert [p["title"] for p in principles] == ["Carb targets"]  # failed replace left the original row intact
