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
    fixture.write_text(json.dumps({"params": {"surface": "trail"}}))
    monkeypatch.setattr(golden_eval, "GOLDEN_DIR", str(tmp_path))

    with (
        patch("scripts.golden_eval._run_gear_nutrition", return_value={"recommendations": [{"name": "Speedcross"}]}),
        patch("db.get_kb_chunks", return_value=[{"title": "Speedcross"}]),
        patch.object(obs, "push_experiment", return_value=True) as mock_push,
    ):
        golden_eval.compare("gear", push_langfuse=True)
        assert mock_push.call_count == 1
        _, kwargs = mock_push.call_args
        assert kwargs["synthetic"] is True
        assert kwargs["dataset_name"] == "uphill_gear_golden"
        assert len(kwargs["items"]) == 1
        assert kwargs["items"][0]["provenance"] == "gear"
        assert kwargs["scores"][0]["catalog_membership_valid"] is True
        assert "latency_s" in kwargs["scores"][0]
        assert "engine_is_gemini" in kwargs["scores"][0]
