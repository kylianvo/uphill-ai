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
