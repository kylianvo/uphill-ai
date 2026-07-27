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
    # db.get_kb_chunks does SELECT * — mock the raw row shape it actually returns (id/
    # content_hash/created_at plus source_label) so this test catches those leaking into
    # the exported seed file.
    raw_catalog_rows = [
        {
            "id": 42,
            "domain": "gear",
            "kind": "catalog_item",
            "title": "Hoka Speedgoat 7",
            "content": "c",
            "payload": None,
            "source_label": "web discovery",
            "content_hash": "abc123",
            "created_at": "2026-07-27T00:00:00",
        }
    ]
    with (
        patch("db.add_kb_chunks", return_value=1) as add_mock,
        patch("db.get_kb_chunks", return_value=raw_catalog_rows),  # export_seed reads full current catalog
    ):
        saved = asyncio.run(kb_distiller.save_domain("gear", rows, "test-key"))
    add_mock.assert_called_once_with("gear", rows)
    assert saved == 1

    with open(f"{tmp_path}/gear.json", encoding="utf-8") as f:
        exported = json.load(f)
    exported_row = exported["chunks"][0]
    assert set(exported_row) == {"domain", "kind", "title", "content", "payload", "source_label"}
    assert "id" not in exported_row and "content_hash" not in exported_row and "created_at" not in exported_row


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


def test_validate_domain_rows_raises_below_floor_for_nutrition_principles():
    principle_rows = [{"kind": "principle", "title": f"p{i}"} for i in range(2)]  # floor is 3
    with pytest.raises(RuntimeError, match="nutrition"):
        kb_distiller.validate_domain_rows("nutrition", principle_rows)


def test_validate_domain_rows_nutrition_passes_through_catalog_rows_regardless_of_count():
    # 0 new web-discovered products is a normal outcome -- only the principle floor can raise.
    principle_rows = [{"kind": "principle", "title": f"p{i}"} for i in range(3)]  # at floor
    catalog_rows = [{"kind": "catalog_item", "title": "GU Roctane"}]
    result = kb_distiller.validate_domain_rows("nutrition", principle_rows + catalog_rows)
    assert result == principle_rows + catalog_rows

    # Even zero catalog rows must not raise once the principle floor is met.
    result_no_products = kb_distiller.validate_domain_rows("nutrition", principle_rows)
    assert result_no_products == principle_rows


def test_validate_domain_rows_passes_at_or_above_floor_for_scheduler():
    rows = [{"title": f"p{i}"} for i in range(15)]  # floor is 15
    assert kb_distiller.validate_domain_rows("scheduler", rows) == rows


def test_discover_nutrition_web_skips_known_products_and_structures_new_ones(monkeypatch):
    monkeypatch.setattr(kb_distiller, "NUTRITION_BRANDS", ["GU"])
    existing_rows = [
        {
            "domain": "nutrition",
            "kind": "catalog_item",
            "title": "GU Roctane",
            "content": "c",
            "payload": {"brand": "GU", "name": "Roctane"},
        }
    ]
    tavily_response = {
        "results": [
            {"title": "GU Roctane Review", "url": "https://guenergy.com/roctane", "content": "old product"},
            {
                "title": "GU Announces New Gel",
                "url": "https://guenergy.com/new-gel",
                "content": "new product article text...",
            },
        ]
    }
    structured = {
        "products": [
            {
                "brand": "GU",
                "name": "Mini Gel",
                "format": "gel",
                "carbs_per_unit": 15.0,
                "sodium_per_unit": 50.0,
                "protein_per_unit": 0.0,
                "tech_notes": "Smaller single-serve packet.",
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
        rows = asyncio.run(kb_distiller.discover_nutrition_web("test-key", "tvly-test", {}))

    assert len(rows) == 1  # "Roctane" result skipped (already known), "Mini Gel" structured
    assert rows[0]["title"] == "GU Mini Gel"
    assert rows[0]["domain"] == "nutrition"
    assert rows[0]["kind"] == "catalog_item"
    assert rows[0]["payload"]["brand"] == "GU"
    assert rows[0]["source_label"] == "guenergy.com"
    search_kwargs = tavily_cls.return_value.search.call_args.kwargs
    assert "facebook.com" in search_kwargs["exclude_domains"]  # low-reliability UGC platforms excluded


def test_discover_nutrition_web_strips_repeated_brand_from_product_name(monkeypatch):
    monkeypatch.setattr(kb_distiller, "NUTRITION_BRANDS", ["Maurten"])
    tavily_response = {
        "results": [
            {"title": "Maurten Drink Mix Review", "url": "https://fleetfeet.com/maurten", "content": "text"},
        ]
    }
    structured = {
        "products": [
            {
                "brand": "Maurten",
                "name": "Maurten Drink Mix",  # brand repeated inside the product name
                "format": "drink mix",
                "carbs_per_unit": 80.0,
                "sodium_per_unit": 500.0,
                "protein_per_unit": 0.0,
                "tech_notes": "Hydrogel technology.",
            }
        ]
    }
    with (
        patch.object(kb_distiller, "TavilyClient") as tavily_cls,
        patch("db.get_kb_chunks", return_value=[]),
        patch.object(kb_distiller, "_gemini_structured", new_callable=AsyncMock, return_value=structured),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        tavily_cls.return_value.search.return_value = tavily_response
        rows = asyncio.run(kb_distiller.discover_nutrition_web("test-key", "tvly-test", {}))

    assert rows[0]["title"] == "Maurten Drink Mix"  # not "Maurten Maurten Drink Mix"
    assert rows[0]["payload"]["name"] == "Drink Mix"  # brand stripped from payload name too


def test_discover_nutrition_web_returns_empty_when_nothing_new(monkeypatch):
    monkeypatch.setattr(kb_distiller, "NUTRITION_BRANDS", ["GU"])
    with (
        patch.object(kb_distiller, "TavilyClient") as tavily_cls,
        patch("db.get_kb_chunks", return_value=[]),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        tavily_cls.return_value.search.return_value = {"results": []}
        rows = asyncio.run(kb_distiller.discover_nutrition_web("test-key", "tvly-test", {}))
    assert rows == []


def test_sweep_domain_nutrition_combines_principles_and_web_products(monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, "NOTEBOOKLM_NUTRITION_ID", "nb-nutrition")
    monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", '{"tok":1}')
    monkeypatch.setattr(settings, "TAVILY_API_KEY", "tvly-test")
    principle_rows = [{"domain": "nutrition", "kind": "principle", "title": "Carb targets", "content": "c"}]
    product_rows = [{"domain": "nutrition", "kind": "catalog_item", "title": "GU Mini Gel", "content": "c"}]
    with (
        patch.object(kb_distiller, "_distill_nutrition", new_callable=AsyncMock, return_value=principle_rows),
        patch.object(kb_distiller, "discover_nutrition_web", new_callable=AsyncMock, return_value=product_rows),
    ):
        rows = asyncio.run(kb_distiller.sweep_domain("nutrition", "test-key", {}))
    assert rows == principle_rows + product_rows


def test_sweep_domain_nutrition_skips_web_discovery_without_tavily_key(monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, "NOTEBOOKLM_NUTRITION_ID", "nb-nutrition")
    monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", '{"tok":1}')
    monkeypatch.setattr(settings, "TAVILY_API_KEY", "")
    principle_rows = [{"domain": "nutrition", "kind": "principle", "title": "Carb targets", "content": "c"}]
    with (
        patch.object(kb_distiller, "_distill_nutrition", new_callable=AsyncMock, return_value=principle_rows),
        patch.object(kb_distiller, "discover_nutrition_web", new_callable=AsyncMock) as web_mock,
    ):
        rows = asyncio.run(kb_distiller.sweep_domain("nutrition", "test-key", {}))
    assert rows == principle_rows
    web_mock.assert_not_called()


def test_save_domain_nutrition_replaces_principles_and_appends_products(tmp_path, monkeypatch):
    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))
    principle_rows = [{"domain": "nutrition", "kind": "principle", "title": "Carb targets", "content": "c"}]
    catalog_rows = [{"domain": "nutrition", "kind": "catalog_item", "title": "GU Mini Gel", "content": "c"}]
    full_catalog_after_save = [
        {
            "id": 1,
            "domain": "nutrition",
            "kind": "principle",
            "title": "Carb targets",
            "content": "c",
            "payload": None,
            "source_label": "NotebookLM distillation",
            "content_hash": "h1",
            "created_at": "2026-07-27T00:00:00",
        },
        {
            "id": 2,
            "domain": "nutrition",
            "kind": "catalog_item",
            "title": "GU Mini Gel",
            "content": "c",
            "payload": None,
            "source_label": "guenergy.com",
            "content_hash": "h2",
            "created_at": "2026-07-27T00:00:00",
        },
    ]
    with (
        patch("db.replace_kb_chunks_by_kind", return_value=1) as replace_mock,
        patch("db.add_kb_chunks", return_value=1) as add_mock,
        patch("db.get_kb_chunks", return_value=full_catalog_after_save),
    ):
        saved = asyncio.run(kb_distiller.save_domain("nutrition", principle_rows + catalog_rows, "test-key"))
    replace_mock.assert_called_once_with("nutrition", "principle", principle_rows)
    add_mock.assert_called_once_with("nutrition", catalog_rows)
    assert saved == 2

    with open(f"{tmp_path}/nutrition.json", encoding="utf-8") as f:
        exported = json.load(f)
    for row in exported["chunks"]:
        assert set(row) == {"domain", "kind", "title", "content", "payload", "source_label"}


def _race_chunk(title, race_name, results):
    return {
        "domain": "race_courses",
        "kind": "race_profile",
        "title": title,
        "content": f"{title} narrative",
        "payload": {"race_name": race_name, "results": results},
        "source_label": "curated",
    }


def test_race_titles_with_results_only_returns_tracked_races():
    chunks = [
        _race_chunk("Vietnam Mountain Marathon (VMM) — Sa Pa, Vietnam", "Vietnam Mountain Marathon", [{"year": 2025}]),
        _race_chunk("Some Untracked Race", "Some Untracked Race", []),  # no results yet -- not eligible
    ]
    with patch("db.get_kb_chunks", return_value=chunks):
        tracked = kb_distiller._race_titles_with_results()
    assert len(tracked) == 1
    assert tracked[0][0] == "Vietnam Mountain Marathon (VMM) — Sa Pa, Vietnam"
    assert tracked[0][1] == "Vietnam Mountain Marathon"


def test_discover_race_results_web_skips_known_year_distance_and_structures_new(monkeypatch):
    existing_results = [{"year": 2025, "distance_label": "70km", "winner_time": "9:10:58"}]
    tracked_chunk = _race_chunk("Vietnam Mountain Marathon", "Vietnam Mountain Marathon", existing_results)
    tavily_response = {
        "results": [
            {"title": "VMM 70km 2025", "url": "https://statistik.d-u-v.org/vmm-2025", "content": "2025 results page"},
        ]
    }
    structured = {
        "results": [
            {
                "year": 2025,
                "distance_label": "70km",  # already known -- must be skipped
                "winner_time": "9:10:58",
            },
            {
                "year": 2026,
                "distance_label": "70km",  # genuinely new
                "winner_time": "9:05:00",
                "distance_km": 69.5,
                "finishers": 300,
            },
        ]
    }
    with (
        patch("db.get_kb_chunks", return_value=[tracked_chunk]),
        patch.object(kb_distiller, "TavilyClient") as tavily_cls,
        patch.object(kb_distiller, "_gemini_structured", new_callable=AsyncMock, return_value=structured),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        tavily_cls.return_value.search.return_value = tavily_response
        updates = asyncio.run(kb_distiller.discover_race_results_web("test-key", "tvly-test", {}))

    assert list(updates.keys()) == ["Vietnam Mountain Marathon"]
    new_entries = updates["Vietnam Mountain Marathon"]
    assert len(new_entries) == 1  # the 2025/70km duplicate was dropped
    assert new_entries[0]["year"] == 2026
    assert new_entries[0]["winner_time"] == "9:05:00"
    assert new_entries[0]["source"] == "statistik.d-u-v.org"

    search_kwargs = tavily_cls.return_value.search.call_args.kwargs
    assert search_kwargs["include_domains"] == ["statistik.d-u-v.org"]


def test_discover_race_results_web_returns_empty_dict_when_nothing_new():
    existing_results = [{"year": 2025, "distance_label": "70km"}]
    tracked_chunk = _race_chunk("Vietnam Mountain Marathon", "Vietnam Mountain Marathon", existing_results)
    with (
        patch("db.get_kb_chunks", return_value=[tracked_chunk]),
        patch.object(kb_distiller, "TavilyClient") as tavily_cls,
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        tavily_cls.return_value.search.return_value = {"results": []}
        updates = asyncio.run(kb_distiller.discover_race_results_web("test-key", "tvly-test", {}))
    assert updates == {}


def test_discover_race_results_web_rejects_entries_without_a_real_winner_time():
    # Reproduces a real bug: a generic DUV events-calendar page structured into a
    # future, not-yet-run "result" with no winner time -- must be rejected outright.
    existing_results = [{"year": 2024, "distance_label": "70km", "winner_time": "9:15:00"}]
    tracked_chunk = _race_chunk("Vietnam Mountain Marathon", "Vietnam Mountain Marathon", existing_results)
    tavily_response = {
        "results": [{"title": "DUV events list", "url": "https://statistik.d-u-v.org/geteventlist.php", "content": "x"}]
    }
    structured = {
        "results": [
            {"year": 2099, "distance_label": "30h", "winner_time": ""},  # bogus future event, no winner time
            {"year": 2025, "distance_label": "70km", "winner_time": "9:10:58"},  # genuine result
        ]
    }
    with (
        patch("db.get_kb_chunks", return_value=[tracked_chunk]),
        patch.object(kb_distiller, "TavilyClient") as tavily_cls,
        patch.object(kb_distiller, "_gemini_structured", new_callable=AsyncMock, return_value=structured),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        tavily_cls.return_value.search.return_value = tavily_response
        updates = asyncio.run(kb_distiller.discover_race_results_web("test-key", "tvly-test", {}))
    new_entries = updates["Vietnam Mountain Marathon"]
    assert len(new_entries) == 1  # only the genuine result survives
    assert new_entries[0]["year"] == 2025


def test_save_race_results_merges_only_genuinely_new_entries_per_race(tmp_path, monkeypatch):
    monkeypatch.setattr(kb_distiller, "SEED_DIR", str(tmp_path))
    vmm_existing = [{"year": 2025, "distance_label": "70km", "winner_time": "9:10:58"}]
    dalat_existing = [{"year": 2025, "distance_label": "100km", "winner_time": "20:00:00"}]
    vmm_chunk = _race_chunk("VMM", "Vietnam Mountain Marathon", vmm_existing)
    dalat_chunk = _race_chunk("Dalat Ultra Trail", "Dalat Ultra Trail", dalat_existing)
    full_catalog = [vmm_chunk, dalat_chunk]

    updates = {
        "VMM": [
            {"year": 2025, "distance_label": "70km", "winner_time": "9:10:58"},  # dup -- must be dropped
            {"year": 2026, "distance_label": "70km", "winner_time": "9:05:00"},  # new
        ],
        "Dalat Ultra Trail": [],  # nothing new for this race
    }

    with (
        patch("db.get_kb_chunks", side_effect=lambda *a, **k: full_catalog),
        patch("db.update_kb_chunk_payload", return_value=True) as update_mock,
    ):
        total = kb_distiller.save_race_results(updates)

    assert total == 1  # only the 2026 entry was genuinely new
    update_mock.assert_called_once()
    called_domain, called_kind, called_title, called_payload = update_mock.call_args[0]
    assert called_title == "VMM"
    assert {"year": 2026, "distance_label": "70km", "winner_time": "9:05:00"} in called_payload["results"]
    assert len(called_payload["results"]) == 2  # existing entry kept alongside the new one

    with open(f"{tmp_path}/race_courses.json", encoding="utf-8") as f:
        exported = json.load(f)
    for row in exported["chunks"]:
        assert set(row) == {"domain", "kind", "title", "content", "payload", "source_label"}
