import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from services import kb_distiller


def test_distill_gear_sweeps_whitelisted_brands_and_builds_catalog_rows(monkeypatch):
    # Gear sweeps the operator whitelist directly — no brand-enumeration query
    monkeypatch.setattr(kb_distiller, "GEAR_BRANDS", ["Hoka", "Salomon"])
    nlm_answers = ["hoka shoes text...", "salomon shoes text..."]
    structured_answers = [
        {
            "shoes": [
                {
                    "model": "Speedgoat 7",
                    "brand": "HOKA ONE ONE",  # restyled name → coerced to the queried brand
                    "foam_material": "CMEVA (EVA)",
                    "outsole_compound": "Vibram Megagrip",
                    "lug_depth": "5mm",
                    "drop": "4mm",
                    "stack": "40mm/36mm",
                    "price": "$155",
                    "pros": "Grippy, plush, reliable on technical terrain.",
                    "cons": "Heavy for racing.",
                    "best_for": "Long technical trail days and ultras.",
                },
                {
                    "model": "Ultraventure 4",
                    "brand": "Topo Athletic",  # competitor mentioned in a review — must be dropped
                    "foam_material": "ZipFoam (EVA)",
                    "outsole_compound": "Vibram",
                    "lug_depth": "4mm",
                    "drop": "5mm",
                    "stack": "35mm/30mm",
                    "price": "$150",
                    "pros": "Roomy toe box.",
                    "cons": "Soft upper.",
                    "best_for": "Wide-footed runners.",
                },
            ]
        },
        {
            "shoes": [
                {
                    "model": "Salomon Genesis",  # brand repeated inside model → deduped in title
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
        ) as nlm,
        patch.object(kb_distiller, "_gemini_structured", new_callable=AsyncMock, side_effect=structured_answers),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        rows = asyncio.run(kb_distiller._distill_gear("nb-gear", '{"tok":1}', "test-key", {}))

    assert nlm.call_count == 2  # one query per whitelisted brand, no enumeration query
    assert len(rows) == 2  # Topo Athletic row filtered out
    assert rows[0]["domain"] == "gear"
    assert rows[0]["kind"] == "catalog_item"
    assert rows[0]["title"] == "Hoka Speedgoat 7"  # brand coerced from "HOKA ONE ONE"
    assert rows[0]["payload"]["brand"] == "Hoka"
    assert rows[0]["payload"]["cons"] == "Heavy for racing."  # qualitative fields captured
    assert rows[0]["payload"]["best_for"].startswith("Long technical")
    assert rows[1]["title"] == "Salomon Genesis"
    assert rows[1]["payload"]["model"] == "Genesis"  # brand stripped from payload model too


def _thin_shoe(model):
    return {
        "model": model,
        "brand": "Salomon",
        "foam_material": "",
        "outsole_compound": "",
        "lug_depth": "",
        "drop": "",
        "stack": "",
        "price": "",
        "pros": "",
        "cons": "",
        "best_for": "",
    }


def _rich_shoe(model):
    return {
        "model": model,
        "brand": "Salomon",
        "foam_material": "EnergyFoam (EVA)",
        "outsole_compound": "Contagrip",
        "lug_depth": "4mm",
        "drop": "8mm",
        "stack": "31mm/23mm",
        "price": "$140",
        "pros": "Secure fit.",
        "cons": "Firm.",
        "best_for": "Mountain running.",
    }


def test_thin_sweep_is_retried_and_richer_result_kept(monkeypatch):
    monkeypatch.setattr(kb_distiller, "GEAR_BRANDS", ["Salomon"])
    with (
        patch(
            "services.notebooklm_service.NotebookLmService.query_notebook",
            new_callable=AsyncMock,
            side_effect=["thin answer", "rich answer"],
        ) as nlm,
        patch.object(
            kb_distiller,
            "_gemini_structured",
            new_callable=AsyncMock,
            side_effect=[
                {"shoes": [_thin_shoe("Aero Glide series"), _thin_shoe("S/Lab racing line")]},
                {"shoes": [_rich_shoe("Genesis"), _rich_shoe("S/Lab Ultra Glide 2")]},
            ],
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        rows = asyncio.run(kb_distiller._distill_gear("nb-gear", '{"tok":1}', "test-key", {}))
    assert nlm.call_count == 2  # thin first sweep triggered exactly one re-sweep
    assert [r["title"] for r in rows] == ["Salomon Genesis", "Salomon S/Lab Ultra Glide 2"]
    assert rows[0]["payload"]["price"] == "$140"  # the rich result won


def test_overflowing_brand_answer_splits_into_trail_and_road(monkeypatch):
    calls = []

    async def fake_query(notebook_id, auth_json, query, attempts=3):
        calls.append(query)
        if len(calls) == 1:
            raise Exception("RPC response exceeded 52428800 bytes")
        return f"answer {len(calls)}"

    with (
        patch.object(kb_distiller, "_query_with_retries", side_effect=fake_query),
        patch.object(
            kb_distiller,
            "_gemini_structured",
            new_callable=AsyncMock,
            side_effect=[
                {"shoes": [_rich_shoe("Pegasus Trail 5"), _rich_shoe("Zegama 2")]},
                {"shoes": [_rich_shoe("Pegasus Trail 5"), _rich_shoe("Vaporfly 4")]},  # dup deduped
            ],
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        shoes = asyncio.run(kb_distiller._sweep_gear_brand("nb-gear", '{"tok":1}', "test-key", "Nike"))
    assert len(calls) == 3  # full sweep + trail + road
    assert "trail running" in calls[1] and "road running" in calls[2]
    assert sorted(s["model"] for s in shoes) == ["Pegasus Trail 5", "Vaporfly 4", "Zegama 2"]


def test_query_with_retries_does_not_retry_stream_overflow():
    with (
        patch(
            "services.notebooklm_service.NotebookLmService.query_notebook",
            new_callable=AsyncMock,
            side_effect=Exception("RPC response exceeded 52428800 bytes"),
        ) as nlm,
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(Exception, match="RPC response exceeded"):
            asyncio.run(kb_distiller._query_with_retries("nb", '{"tok":1}', "q"))
    assert nlm.call_count == 1  # deterministic overflow — retrying is pure waste


def test_query_with_retries_recovers_from_transient_failure():
    with (
        patch(
            "services.notebooklm_service.NotebookLmService.query_notebook",
            new_callable=AsyncMock,
            side_effect=[Exception("Server disconnected"), "recovered answer"],
        ) as nlm,
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        answer = asyncio.run(kb_distiller._query_with_retries("nb", '{"tok":1}', "q"))
    assert answer == "recovered answer"
    assert nlm.call_count == 2


def test_query_with_retries_gives_up_after_attempts():
    with (
        patch(
            "services.notebooklm_service.NotebookLmService.query_notebook",
            new_callable=AsyncMock,
            side_effect=Exception("DNS down"),
        ) as nlm,
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(Exception, match="DNS down"):
            asyncio.run(kb_distiller._query_with_retries("nb", '{"tok":1}', "q", attempts=3))
    assert nlm.call_count == 3


def test_whitelisted_brand_word_boundary():
    # "Salomon" contains "on" but must NOT be coerced to the "On" brand
    assert kb_distiller._whitelisted_brand("Salomon", "On") == "Salomon"  # exact whitelist hit wins
    assert kb_distiller._whitelisted_brand("Some Unknown Co", "On") is None
    assert kb_distiller._whitelisted_brand("On Running", "On") == "On"


def test_distill_domain_refuses_to_wipe_on_empty_sweep(monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, "NOTEBOOKLM_GEAR_ID", "nb-gear")
    monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", '{"tok":1}')
    with (
        patch.object(kb_distiller, "_distill_gear", new_callable=AsyncMock, return_value=[]),
        patch("db.replace_kb_chunks") as replace_mock,
    ):
        with pytest.raises(RuntimeError, match="empty"):
            asyncio.run(kb_distiller.distill_domain("gear", "test-key", {}))
    replace_mock.assert_not_called()  # existing KB must survive a failed sweep


def test_export_and_load_seed_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))
    rows = [{"domain": "gear", "kind": "catalog_item", "title": "X", "content": "c", "payload": {"a": 1}}]
    path = kb_distiller.export_seed("gear", rows)
    assert path.endswith("gear.json")
    assert json.loads(open(path, encoding="utf-8").read())["chunks"][0]["title"] == "X"

    with patch("db.replace_kb_chunks", return_value=1) as replace_mock:
        loaded = kb_distiller.load_seed("gear")
    replace_mock.assert_called_once()
    assert replace_mock.call_args[0][0] == "gear"
    assert loaded == 1


def test_load_seed_missing_file_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        kb_distiller.load_seed("nutrition")
