import json
from pathlib import Path

from services.doctrine_metadata import (
    BOOK,
    BOOK_CLUB_PODCAST,
    BOOK_TITLE,
    CHAPTERS,
    SCHEDULER_CHUNK_PROVENANCE,
    get_scheduler_chunk_metadata,
)

SEED_PATH = Path(__file__).resolve().parents[2] / "kb_seed" / "scheduler.json"


def _chunks():
    with open(SEED_PATH) as f:
        return json.load(f).get("chunks", [])


def test_all_scheduler_seed_chunks_mapped():
    chunks = _chunks()
    assert len(chunks) == 38

    for chunk in chunks:
        title = chunk.get("title")
        assert title in SCHEDULER_CHUNK_PROVENANCE, f"Missing provenance for chunk: '{title}'"
        meta = get_scheduler_chunk_metadata(title)
        assert meta is not None
        assert meta["source"] in (BOOK, BOOK_CLUB_PODCAST)
        assert meta["citation_label"]
        if meta["source"] == BOOK:
            # A book citation must name a real chapter of the book.
            assert meta["book"] == BOOK_TITLE
            if meta["chapter_num"] is None:
                # Chapter unconfirmed: cite the book, never a guessed chapter.
                assert meta["citation_label"] == BOOK_TITLE
            else:
                assert meta["chapter_title"] == CHAPTERS[meta["chapter_num"]]
                assert meta["citation_label"] == (
                    f"{BOOK_TITLE} — Chapter {meta['chapter_num']}: {meta['chapter_title']}"
                )
        else:
            # Podcast material is never passed off as a book quotation.
            assert not meta["citation_label"].startswith(BOOK_TITLE)


def test_the_book_has_twelve_chapters_and_nothing_cites_beyond_them():
    assert sorted(CHAPTERS) == list(range(1, 13))
    for meta in SCHEDULER_CHUNK_PROVENANCE.values():
        assert meta["chapter_num"] is None or meta["chapter_num"] in CHAPTERS


def test_podcast_only_material_is_labelled_as_such():
    """The 2019 book cannot contain Tom Evans' UTMB prep or a 2022 paper."""
    for title in ("Race-Day Pacing Strategies", "Treadmill & Gym Machine Substitutions"):
        meta = get_scheduler_chunk_metadata(title)
        assert meta["source"] == BOOK_CLUB_PODCAST
        assert meta["chapter_num"] is None


def test_seed_payload_matches_the_provenance_map():
    for chunk in _chunks():
        meta = get_scheduler_chunk_metadata(chunk["title"])
        payload = chunk["payload"]
        for key in ("book", "source", "chapter_num", "chapter_title", "citation_label"):
            assert payload[key] == meta[key], (chunk["title"], key)
