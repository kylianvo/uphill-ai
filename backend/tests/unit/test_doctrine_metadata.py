import json
from pathlib import Path

from services.doctrine_metadata import SCHEDULER_CHUNK_PROVENANCE, get_scheduler_chunk_metadata


def test_all_scheduler_seed_chunks_mapped():
    seed_path = Path(__file__).resolve().parents[2] / "kb_seed" / "scheduler.json"
    with open(seed_path) as f:
        data = json.load(f)

    chunks = data.get("chunks", [])
    assert len(chunks) == 40

    for chunk in chunks:
        title = chunk.get("title")
        assert title in SCHEDULER_CHUNK_PROVENANCE, f"Missing provenance for chunk: '{title}'"
        meta = get_scheduler_chunk_metadata(title)
        assert meta is not None
        assert meta["book"] == "Training for the Uphill Athlete"
        assert meta["chapter_num"] >= 1
        assert meta["chapter_title"]
        assert meta["section"].startswith("Section ")
        assert "Training for the Uphill Athlete — Chapter" in meta["citation_label"]
