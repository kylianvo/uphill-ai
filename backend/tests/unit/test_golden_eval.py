"""scripts/golden_eval.py's fixture discovery.

Regression cover for a real bug hit while building the tier fixtures: `_fixtures()`
globbed "fixture_*.json", which also matches its OWN saved output -- a captured
baseline is named "<fixture>.ref.json", and that name starts with "fixture_" and ends
in ".json" too. A second `capture` run over the same directory therefore tried to load
yesterday's baseline as a fixture, found none of the {"user_profile", "race_info", ...}
keys a real fixture has, and crashed with KeyError. Silent until the second run --
which is exactly the run that matters, since the whole point of the harness is
capture-then-compare across sessions.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import golden_eval  # noqa: E402


def test_a_ref_json_left_next_to_its_fixture_is_not_treated_as_a_fixture(tmp_path, monkeypatch):
    service_dir = tmp_path / "scheduler"
    service_dir.mkdir()

    fixture = service_dir / "fixture_beginner.json"
    fixture.write_text(json.dumps({"user_profile": {}, "race_info": {}, "total_weeks": 12}))

    # Exactly what `capture` produces next to a fixture on a prior run.
    ref = service_dir / "fixture_beginner.ref.json"
    ref.write_text(json.dumps({"latency_s": 1.2, "engine_used": "gemini", "output": []}))

    monkeypatch.setattr(golden_eval, "GOLDEN_DIR", str(tmp_path))

    found = golden_eval._fixtures("scheduler")

    assert found == [str(fixture)]
    assert str(ref) not in found


def test_multiple_real_fixtures_are_still_all_found(tmp_path, monkeypatch):
    service_dir = tmp_path / "scheduler"
    service_dir.mkdir()
    for name in ("fixture_a.json", "fixture_b.json", "fixture_c.json"):
        (service_dir / name).write_text("{}")
    (service_dir / "fixture_a.ref.json").write_text("{}")

    monkeypatch.setattr(golden_eval, "GOLDEN_DIR", str(tmp_path))

    found = golden_eval._fixtures("scheduler")

    assert len(found) == 3
    assert all(not p.endswith(".ref.json") for p in found)


def test_exits_with_a_clear_message_when_a_service_has_no_fixtures(tmp_path, monkeypatch, capsys):
    (tmp_path / "scheduler").mkdir()
    monkeypatch.setattr(golden_eval, "GOLDEN_DIR", str(tmp_path))

    try:
        golden_eval._fixtures("scheduler")
        raised = False
    except SystemExit:
        raised = True

    assert raised


def test_push_experiment_denies_export_when_synthetic_is_false():
    from services import observability as obs

    items = [{"id": "item1", "synthetic": True, "provenance": "gear"}]
    results = [{"recommendations": []}]
    scores = [{"latency_s": 1.0}]
    assert (
        obs.push_experiment(
            dataset_name="test_ds",
            run_name="run1",
            items=items,
            results=results,
            scores=scores,
            synthetic=False,
        )
        is False
    )


def test_push_experiment_denies_export_when_lengths_mismatch():
    from services import observability as obs

    items = [{"id": "item1", "synthetic": True, "provenance": "gear"}]
    results = [{"recommendations": []}]
    scores = []  # length mismatch
    assert (
        obs.push_experiment(
            dataset_name="test_ds",
            run_name="run1",
            items=items,
            results=results,
            scores=scores,
            synthetic=True,
        )
        is False
    )


def test_push_experiment_denies_export_on_empty_items():
    from services import observability as obs

    assert (
        obs.push_experiment(
            dataset_name="test_ds",
            run_name="run1",
            items=[],
            results=[],
            scores=[],
            synthetic=True,
        )
        is False
    )


def test_push_experiment_denies_export_for_unverified_or_private_items():
    from services import observability as obs

    results = [{}]
    scores = [{}]

    # Missing synthetic flag in item
    assert (
        obs.push_experiment(
            dataset_name="test_ds",
            run_name="run1",
            items=[{"id": "item1", "provenance": "gear"}],
            results=results,
            scores=scores,
            synthetic=True,
        )
        is False
    )

    # Private item marked
    assert (
        obs.push_experiment(
            dataset_name="test_ds",
            run_name="run1",
            items=[{"id": "item1", "synthetic": True, "provenance": "gear", "is_private": True}],
            results=results,
            scores=scores,
            synthetic=True,
        )
        is False
    )

    # Unsupported provenance (not gear/nutrition/scheduler)
    assert (
        obs.push_experiment(
            dataset_name="test_ds",
            run_name="run1",
            items=[{"id": "item1", "synthetic": True, "provenance": "private_db_user_123"}],
            results=results,
            scores=scores,
            synthetic=True,
        )
        is False
    )


def test_push_experiment_denies_export_on_duplicate_item_ids():
    from services import observability as obs

    items = [
        {"id": "item1", "synthetic": True, "provenance": "gear"},
        {"id": "item1", "synthetic": True, "provenance": "gear"},  # duplicate
    ]
    results = [{}, {}]
    scores = [{}, {}]
    assert (
        obs.push_experiment(
            dataset_name="test_ds",
            run_name="run1",
            items=items,
            results=results,
            scores=scores,
            synthetic=True,
        )
        is False
    )


def test_push_experiment_returns_false_when_client_is_none():
    from unittest.mock import patch

    from services import observability as obs

    items = [{"id": "item1", "synthetic": True, "provenance": "gear"}]
    results = [{}]
    scores = [{}]
    with patch.object(obs, "_client", None):
        assert (
            obs.push_experiment(
                dataset_name="test_ds",
                run_name="run1",
                items=items,
                results=results,
                scores=scores,
                synthetic=True,
            )
            is False
        )


def test_push_experiment_calls_langfuse_apis_on_valid_synthetic_data():
    from unittest.mock import MagicMock, patch

    from services import observability as obs

    items = [
        {"id": "gear_shoe_1", "synthetic": True, "provenance": "gear", "input": {"shoe": "Speedcross"}},
        {"id": "gear_shoe_2", "synthetic": True, "provenance": "gear", "input": {"shoe": "Sense Ride"}},
    ]
    results = [
        {"recommendations": [{"name": "Speedcross 6"}]},
        {"recommendations": [{"name": "Sense Ride 5"}]},
    ]
    scores = [
        {"latency_s": 1.2, "catalog_membership_valid": True, "engine_is_gemini": True},
        {"latency_s": 0.9, "catalog_membership_valid": True, "engine_is_gemini": True},
    ]

    mock_client = MagicMock()
    mock_run_item = MagicMock()
    mock_run_item.dataset_run_id = "run-item-uuid-1"
    mock_client.api.dataset_run_items.create.return_value = mock_run_item

    with patch.object(obs, "_client", mock_client):
        success = obs.push_experiment(
            dataset_name="uphill_gear_golden",
            run_name="eval_gear_commit123",
            items=items,
            results=results,
            scores=scores,
            synthetic=True,
            description="Synthetic golden eval run",
        )
        assert success is True
        assert mock_client.create_dataset.call_count == 1
        assert mock_client.create_dataset_item.call_count == 2
        assert mock_client.api.dataset_run_items.create.call_count == 2
        assert mock_client.create_score.call_count == 6  # 3 scores x 2 items
        assert mock_client.flush.call_count == 1


def test_push_experiment_handles_client_exception_without_raising():
    from unittest.mock import MagicMock, patch

    from services import observability as obs

    items = [{"id": "item1", "synthetic": True, "provenance": "gear"}]
    results = [{}]
    scores = [{"latency_s": 1.0}]

    mock_client = MagicMock()
    mock_client.create_dataset_item.side_effect = RuntimeError("network connection timeout")

    with patch.object(obs, "_client", mock_client):
        success = obs.push_experiment(
            dataset_name="uphill_gear_golden",
            run_name="eval_gear_1",
            items=items,
            results=results,
            scores=scores,
            synthetic=True,
        )
        assert success is False


def test_compare_without_push_langfuse_does_not_call_push_experiment(tmp_path, monkeypatch):
    from unittest.mock import patch

    from services import observability as obs

    service_dir = tmp_path / "gear"
    service_dir.mkdir()
    fixture = service_dir / "fixture_1.json"
    fixture.write_text(json.dumps({"params": {"surface": "trail"}}))
    monkeypatch.setattr(golden_eval, "GOLDEN_DIR", str(tmp_path))

    with (
        patch("scripts.golden_eval._run_gear_nutrition", return_value={"recommendations": []}),
        patch("db.get_kb_chunks", return_value=[]),
        patch.object(obs, "push_experiment") as mock_push,
    ):
        golden_eval.compare("gear", push_langfuse=False)
        assert mock_push.call_count == 0
        report_file = tmp_path / "report_gear.md"
        assert report_file.exists()
        content = report_file.read_text()
        assert "Catalog membership" in content or "catalog_membership" in content


def test_compare_with_push_langfuse_calls_push_experiment_with_precomputed_results(tmp_path, monkeypatch):
    from unittest.mock import patch

    from services import observability as obs

    service_dir = tmp_path / "gear"
    service_dir.mkdir()
    fixture = service_dir / "fixture_1.json"
    fixture.write_text(json.dumps({"synthetic": True, "provenance": "gear", "params": {"surface": "trail"}}))
    monkeypatch.setattr(golden_eval, "GOLDEN_DIR", str(tmp_path))

    with (
        patch("scripts.golden_eval._run_gear_nutrition", return_value={"recommendations": [{"name": "Speedcross"}]}),
        patch("db.get_kb_chunks", return_value=[{"title": "Speedcross"}]),
        patch.object(obs, "push_experiment", return_value=True) as mock_push,
    ):
        golden_eval.compare("gear", push_langfuse=True, synthetic_only=True)
        assert mock_push.call_count == 1
        _, kwargs = mock_push.call_args
        assert kwargs["synthetic"] is True
        assert kwargs["dataset_name"] == "uphill_gear_golden"
        assert len(kwargs["items"]) == 1
        assert kwargs["items"][0]["provenance"] == "gear"
        assert kwargs["scores"][0]["catalog_membership_valid"] is True
        assert "latency_s" in kwargs["scores"][0]
        assert "engine_is_gemini" in kwargs["scores"][0]


def test_push_experiment_accepts_synthetic_chat_items_up_to_the_client():
    from unittest.mock import patch

    from services import observability as obs

    with patch.object(obs, "_client", None):
        # Validation passes for chat provenance; only the missing client stops the push.
        assert (
            obs.push_experiment(
                dataset_name="test_ds",
                run_name="run1",
                items=[{"id": "chat_1", "synthetic": True, "provenance": "chat"}],
                results=[{}],
                scores=[{}],
                synthetic=True,
            )
            is False
        )
    assert "chat" in obs._SYNTHETIC_PROVENANCES


def test_compare_passes_file_level_synthetic_flag_down_to_chat_cases(tmp_path, monkeypatch):
    chat_dir = tmp_path / "chat"
    chat_dir.mkdir()
    (chat_dir / "fixture_bench.json").write_text(
        json.dumps({"synthetic": True, "provenance": "chat", "cases": [{"id": "c1", "lang": "en", "question": "q"}]})
    )
    monkeypatch.setattr(golden_eval, "GOLDEN_DIR", str(tmp_path))
    seen = []

    async def fake_run(service, fixture):
        seen.append(fixture)
        return {"id": fixture["id"], "reply_text": "", "status": "success"}, "gemini"

    monkeypatch.setattr(golden_eval, "_run", fake_run)
    monkeypatch.setitem(sys.modules, "db", type(sys)("db"))
    sys.modules["db"].get_kb_chunks = lambda *a, **k: []

    golden_eval.compare("chat", synthetic_only=True, judge_chat=False)

    assert seen == [{"synthetic": True, "provenance": "chat", "id": "c1", "lang": "en", "question": "q"}]


def test_gate_flags_fallbacks_catalog_misses_safety_and_low_acceptance():
    items = [
        {"id": "s1", "input": {}},
        {"id": "g1", "input": {}},
    ]
    assert golden_eval.gate_failures("scheduler", items[:1], [{"engine": "rules"}]) == [
        "s1: fell through to the rules tier"
    ]
    assert golden_eval.gate_failures("scheduler", items[:1], [{"engine": "gemini_retry"}]) == []
    assert golden_eval.gate_failures("gear", items[1:], [{"catalog_membership_valid": False}]) == [
        "g1: recommended something outside the catalog"
    ]
    chat_items = [{"id": f"c{i}", "input": {"lang": "en"}} for i in range(10)]
    chat_scores = [{"safe_outcome": True, "acceptable": i < 8, "judge_safe": 1.0} for i in range(10)]
    assert golden_eval.gate_failures("chat", chat_items, chat_scores) == ["chat en: acceptable rate below 90%"]
    chat_scores = [{"safe_outcome": True, "acceptable": True, "judge_safe": 0.5} for _ in range(10)]
    assert golden_eval.gate_failures("chat", chat_items, chat_scores) == ["chat: mean judge_safe below 0.9"]
    assert golden_eval.gate_failures("gear", items[1:], [{"catalog_membership_valid": True}]) == []


def test_goal_scores_check_ordering_and_anchor_range():
    fixture = {"anchors": [{"minutes": 400}, {"minutes": 420}]}
    assert golden_eval._goal_scores({"goals": {"a": 370, "b": 405, "c": 450}}, fixture) == {
        "ordered": True,
        "b_in_anchor_range": True,
    }
    assert golden_eval._goal_scores({"goals": {"a": 500, "b": 600, "c": 550}}, fixture) == {
        "ordered": False,
        "b_in_anchor_range": False,
    }


def test_fixture_selection_rejects_unknown_ids_before_running():
    import pytest

    items = [("/tmp/fixture_a.json", {"id": "case-a"})]
    with pytest.raises(ValueError, match="Unknown"):
        golden_eval._select_fixture_items("scheduler", items, ["absent"])
    assert golden_eval._select_fixture_items("scheduler", items, ["case-a"]) == items


def test_output_directory_never_overwrites_an_existing_run(tmp_path):
    import pytest

    target = tmp_path / "run"
    golden_eval._prepare_output_directory(str(target))
    (target / "results.json").write_text("original")
    with pytest.raises(FileExistsError):
        golden_eval._prepare_output_directory(str(target))
    assert (target / "results.json").read_text() == "original"


def test_scheduler_fixed_date_preserves_explicit_partial_start(monkeypatch):
    import asyncio

    from services.plan_generator import PlanGenerator

    captured = []

    async def generate(**kwargs):
        captured.append(kwargs["race_info"])
        return [], "recreational"

    monkeypatch.setattr(PlanGenerator, "generate_plan_workouts", generate)
    fixture = {"user_profile": {}, "race_info": {}, "_as_of": "2026-10-05"}
    asyncio.run(golden_eval._run_scheduler(fixture))
    asyncio.run(golden_eval._run_scheduler(fixture))
    assert captured[0]["plan_start_date"] == captured[1]["plan_start_date"] == "2026-10-05"
    fixture["race_info"]["plan_start_date"] = "2026-10-10"
    asyncio.run(golden_eval._run_scheduler(fixture))
    assert captured[2]["plan_start_date"] == "2026-10-10"


def test_push_requires_synthetic_only_before_any_fixture_is_run(tmp_path, monkeypatch):
    import pytest

    path = tmp_path / "fixture_synthetic.json"
    path.write_text(json.dumps({"synthetic": True, "user_profile": {}, "race_info": {}}))
    monkeypatch.setattr(golden_eval, "_fixtures", lambda service: [str(path)])

    async def fake_run(*args):
        return [], "gemini"

    monkeypatch.setattr(golden_eval, "_run", fake_run)
    monkeypatch.setattr(golden_eval, "GOLDEN_DIR", str(tmp_path))
    with pytest.raises(ValueError, match="synthetic-only"):
        golden_eval.compare("scheduler", push_langfuse=True)


def test_sequence_uses_real_next_block_context_without_database_writes(monkeypatch):
    import asyncio

    from services.plan_generator import PlanGenerator

    seen = []

    async def fake_generate(*args, **kwargs):
        seen.append(kwargs.get("block_context"))
        block = kwargs.get("block_number", 1)
        return [
            {
                "week_number": block,
                "day_of_week": "Tuesday",
                "type": "Easy",
                "title": "Easy Run",
                "duration_minutes": 48,
                "distance_km": 8,
            }
        ], "recreational"

    monkeypatch.setattr(PlanGenerator, "generate_plan_workouts", fake_generate)
    monkeypatch.setattr(golden_eval, "_scheduler_engine_used", lambda *a: "gemini")
    fixture = {
        "user_profile": {},
        "race_info": {"lang": "en"},
        "_as_of": "2026-10-05",
        "sequence": [{"block_number": 1}, {"block_number": 2, "previous_status": "unknown", "override_gate": True}],
    }
    result, engine = asyncio.run(golden_eval._run_scheduler(fixture))
    assert [w["week_number"] for w in result] == [1, 2]
    assert engine == "gemini"
    assert "Unknown sessions: 1" in seen[1]
    assert "not evidence of zero training" in seen[1]
    assert "override grants access" in seen[1]


def test_sequence_reports_worst_engine_not_first_success(monkeypatch):
    import asyncio

    from services.plan_generator import PlanGenerator

    async def fake_generate(*args, **kwargs):
        return [], "recreational"

    monkeypatch.setattr(PlanGenerator, "generate_plan_workouts", fake_generate)
    engines = iter(["gemini", "rule-based-or-unknown"])
    monkeypatch.setattr(golden_eval, "_scheduler_engine_used", lambda *a: next(engines))
    fixture = {
        "user_profile": {},
        "race_info": {},
        "_as_of": "2026-10-05",
        "sequence": [{"block_number": 1}, {"block_number": 2, "previous_status": "completed"}],
    }
    _, engine = asyncio.run(golden_eval._run_scheduler(fixture))
    assert engine == "rule-based-or-unknown"


def test_scheduler_error_is_recorded_and_other_cases_continue(tmp_path, monkeypatch):
    folder = tmp_path / "scheduler"
    folder.mkdir()
    for name in ("a", "b"):
        (folder / f"fixture_{name}.json").write_text(
            json.dumps({"synthetic": True, "provenance": "scheduler", "id": name, "user_profile": {}, "race_info": {}})
        )
    monkeypatch.setattr(golden_eval, "GOLDEN_DIR", str(tmp_path))

    async def fake_run(service, fixture):
        if fixture["id"] == "a":
            raise ValueError("Invalid synthetic prescription")
        return [], "gemini"

    monkeypatch.setattr(golden_eval, "_run", fake_run)
    failures = golden_eval.compare("scheduler", synthetic_only=True, output_dir=str(tmp_path / "run"))
    saved = json.loads((tmp_path / "run/results.json").read_text())
    assert [item["id"] for item in saved["items"]] == ["a", "b"]
    assert saved["scores"][0]["error_type"] == "ValueError"
    assert any("a" in failure for failure in failures)
