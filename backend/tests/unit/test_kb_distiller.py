import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from services import kb_distiller


def test_distill_gear_sweeps_brands_and_builds_catalog_rows(monkeypatch):
    # NotebookLM answers: first the brand list, then one enumeration per brand
    nlm_answers = ["Hoka\nSalomon", "hoka shoes text...", "salomon shoes text..."]
    structured_answers = [
        {"brands": ["Hoka", "Salomon"]},
        {
            "shoes": [
                {
                    "model": "Speedgoat 7",
                    "brand": "Hoka",
                    "foam_material": "CMEVA (EVA)",
                    "outsole_compound": "Vibram Megagrip",
                    "lug_depth": "5mm",
                    "drop": "4mm",
                    "stack": "40mm/36mm",
                    "price": "$155",
                    "pros": "Grippy, plush, reliable on technical terrain.",
                    "cons": "Heavy for racing.",
                    "best_for": "Long technical trail days and ultras.",
                }
            ]
        },
        {
            "shoes": [
                {
                    "model": "Genesis",
                    "brand": "Salomon",
                    "foam_material": "EnergyCell (EVA)",
                    "outsole_compound": "Contagrip",
                    "lug_depth": "4mm",
                    "drop": "8mm",
                    "stack": "31mm/23mm",
                    "price": "$140",
                    "pros": "Secure fit, versatile.",
                    "cons": "Firm ride.",
                    "best_for": "All-round mountain running.",
                }
            ]
        },
    ]
    with (
        patch(
            "services.notebooklm_service.NotebookLmService.query_notebook",
            new_callable=AsyncMock,
            side_effect=nlm_answers,
        ),
        patch.object(kb_distiller, "_gemini_structured", new_callable=AsyncMock, side_effect=structured_answers),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        rows = asyncio.run(kb_distiller._distill_gear("nb-gear", '{"tok":1}', "test-key", {}))

    assert len(rows) == 2
    assert rows[0]["domain"] == "gear"
    assert rows[0]["kind"] == "catalog_item"
    assert rows[0]["title"] == "Hoka Speedgoat 7"
    assert rows[0]["payload"]["cons"] == "Heavy for racing."  # qualitative fields captured
    assert rows[0]["payload"]["best_for"].startswith("Long technical")


def test_distill_domain_refuses_to_wipe_on_empty_sweep(monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, "NOTEBOOKLM_GEAR_ID", "nb-gear")
    monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", '{"tok":1}')
    with (
        patch.object(kb_distiller, "_distill_gear", new_callable=AsyncMock, return_value=[]),
        patch("db.clear_kb_chunks") as clear_mock,
    ):
        with pytest.raises(RuntimeError, match="empty"):
            asyncio.run(kb_distiller.distill_domain("gear", "test-key", {}))
    clear_mock.assert_not_called()  # existing KB must survive a failed sweep


def test_export_and_load_seed_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))
    rows = [{"domain": "gear", "kind": "catalog_item", "title": "X", "content": "c", "payload": {"a": 1}}]
    path = kb_distiller.export_seed("gear", rows)
    assert path.endswith("gear.json")
    assert json.loads(open(path, encoding="utf-8").read())["chunks"][0]["title"] == "X"

    with (
        patch("db.clear_kb_chunks") as clear_mock,
        patch("db.save_kb_chunks", return_value=1) as save_mock,
    ):
        loaded = kb_distiller.load_seed("gear")
    clear_mock.assert_called_once_with("gear")
    save_mock.assert_called_once()
    assert loaded == 1


def test_load_seed_missing_file_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        kb_distiller.load_seed("nutrition")
