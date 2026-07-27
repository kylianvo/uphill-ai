import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from services import kb_distiller


def test_discover_gear_web_skips_known_shoes_and_structures_new_ones(monkeypatch):
    monkeypatch.setattr(kb_distiller, "GEAR_BRANDS", ["Hoka"])
    existing_rows = [
        {
            "domain": "gear",
            "kind": "catalog_item",
            "title": "Hoka Speedgoat 6",
            "content": "c",
            "payload": {"brand": "Hoka", "model": "Speedgoat 6"},
        }
    ]
    tavily_response = {
        "results": [
            {
                "title": "Hoka Speedgoat 6 Review",
                "url": "https://runrepeat.com/hoka-speedgoat-6",
                "content": "old shoe",
            },
            {
                "title": "Hoka Speedgoat 7 Review",
                "url": "https://believeintherun.com/hoka-speedgoat-7",
                "content": "new shoe article text...",
            },
        ]
    }
    structured = {
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
                "pros": "Grippy.",
                "cons": "Heavy.",
                "best_for": "Ultras.",
            }
        ]
    }
    with (
        patch.object(kb_distiller, "TavilyClient") as tavily_cls,
        patch("db.get_kb_chunks", return_value=existing_rows),
        patch.object(kb_distiller, "_gemini_structured", new_callable=AsyncMock, return_value=structured),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        tavily_cls.return_value.search.return_value = tavily_response
        rows = asyncio.run(kb_distiller.discover_gear_web("test-key", "tvly-test", {}))

    assert len(rows) == 1  # "Speedgoat 6" result skipped (already known), "Speedgoat 7" structured
    assert rows[0]["title"] == "Hoka Speedgoat 7"
    assert rows[0]["payload"]["brand"] == "Hoka"
    assert rows[0]["source_label"] == "believeintherun.com"


def test_discover_gear_web_returns_empty_when_nothing_new(monkeypatch):
    monkeypatch.setattr(kb_distiller, "GEAR_BRANDS", ["Hoka"])
    with (
        patch.object(kb_distiller, "TavilyClient") as tavily_cls,
        patch("db.get_kb_chunks", return_value=[]),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        tavily_cls.return_value.search.return_value = {"results": []}
        rows = asyncio.run(kb_distiller.discover_gear_web("test-key", "tvly-test", {}))
    assert rows == []


def test_validate_domain_rows_gear_drops_thin_rows_but_allows_empty():
    assert kb_distiller.validate_domain_rows("gear", []) == []  # 0 new shoes this week is valid
    thin = {
        "domain": "gear",
        "kind": "catalog_item",
        "title": "X",
        "content": "c",
        "payload": {
            "foam_material": "",
            "outsole_compound": "",
            "lug_depth": "",
            "drop": "",
            "stack": "",
            "price": "",
            "pros": "",
            "cons": "",
            "best_for": "",
            "cushioning": "",
            "foot_shape": "",
            "carbon_plate": "",
            "arch_support": "",
            "terrain": [],
            "intended_use": "",
            "overview": "",
            "highlights": "",
            "suitability": "",
        },
    }
    rich = {
        "domain": "gear",
        "kind": "catalog_item",
        "title": "Y",
        "content": "c",
        "payload": {
            "foam_material": "PEBA",
            "outsole_compound": "Vibram",
            "lug_depth": "5mm",
            "drop": "4mm",
            "stack": "40mm",
            "price": "$150",
            "pros": "Fast.",
            "cons": "Narrow.",
            "best_for": "Racing.",
            "cushioning": "max",
            "foot_shape": "standard",
            "carbon_plate": "no",
            "arch_support": "neutral",
            "terrain": ["road"],
            "intended_use": "race day",
            "overview": "Fast shoe.",
            "highlights": "Plate.",
            "suitability": "Racers.",
        },
    }
    result = kb_distiller.validate_domain_rows("gear", [thin, rich])
    assert result == [rich]


def test_save_domain_gear_uses_insert_only_append(tmp_path, monkeypatch):
    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))  # don't clobber the real committed seed file
    rows = [{"domain": "gear", "kind": "catalog_item", "title": "Hoka Speedgoat 7", "content": "c", "payload": None}]
    with (
        patch("db.add_kb_chunks", return_value=1) as add_mock,
        patch("db.get_kb_chunks", return_value=rows),  # export_seed reads full current catalog
    ):
        saved = asyncio.run(kb_distiller.save_domain("gear", rows, "test-key"))
    add_mock.assert_called_once_with("gear", rows)
    assert saved == 1


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


def test_distill_domain_composes_sweep_validate_save(monkeypatch, tmp_path):
    from config import settings

    monkeypatch.setattr(settings, "NOTEBOOKLM_NOTEBOOK_ID", "nb-sched")
    monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", '{"tok":1}')
    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))  # don't clobber the real committed seed file
    rows = [
        {"domain": "scheduler", "kind": "principle", "title": f"p{i}", "content": "c", "payload": None}
        for i in range(15)
    ]
    with (
        patch.object(kb_distiller, "_distill_scheduler", new_callable=AsyncMock, return_value=rows),
        patch("db.replace_kb_chunks", return_value=15) as replace_mock,
        patch("services.kb_retrieval.reindex_scheduler_chunks") as reindex_mock,
    ):
        saved = asyncio.run(kb_distiller.distill_domain("scheduler", "test-key", {}))
    assert saved == 15
    replace_mock.assert_called_once_with("scheduler", rows)
    reindex_mock.assert_called_once()


def test_distill_domain_still_refuses_to_wipe_on_below_floor_sweep(monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, "NOTEBOOKLM_NOTEBOOK_ID", "nb-sched")
    monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", '{"tok":1}')
    with (
        patch.object(kb_distiller, "_distill_scheduler", new_callable=AsyncMock, return_value=[]),
        patch("db.replace_kb_chunks") as replace_mock,
    ):
        with pytest.raises(RuntimeError, match="scheduler"):
            asyncio.run(kb_distiller.distill_domain("scheduler", "test-key", {}))
    replace_mock.assert_not_called()


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


def test_hand_curated_domains_excludes_race_courses_from_distillable_domains():
    assert "race_courses" in kb_distiller.HAND_CURATED_DOMAINS
    assert "race_courses" not in kb_distiller.DOMAINS


def test_validate_domain_rows_raises_below_floor_for_nutrition():
    with pytest.raises(RuntimeError, match="nutrition"):
        kb_distiller.validate_domain_rows("nutrition", [{"title": "x"}] * 4)  # floor is 5


def test_validate_domain_rows_passes_at_or_above_floor_for_scheduler():
    rows = [{"title": f"p{i}"} for i in range(15)]  # floor is 15
    assert kb_distiller.validate_domain_rows("scheduler", rows) == rows
