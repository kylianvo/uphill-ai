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
