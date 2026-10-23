import copy
import json
from pathlib import Path

import pytest

from services import coros_sync, hr_drift

LAPS = json.loads((Path(__file__).parent.parent / "fixtures" / "coros_laps_trail_25k.json").read_text())


def _with(mutate) -> str:
    doc = copy.deepcopy(LAPS)
    mutate(doc)
    return json.dumps(doc)


def test_drift_matches_real_trail_run():
    assert hr_drift.drift_pct(json.dumps(LAPS)) == 1.6


def test_drift_none_with_fewer_than_10_full_laps():
    def cut(doc):
        doc["lapGroups"][1]["laps"] = doc["lapGroups"][1]["laps"][:9]

    assert hr_drift.drift_pct(_with(cut)) is None


def test_drift_none_when_laps_missing_hr():
    def zero(doc):
        doc["lapGroups"][1]["laps"][4]["avgHr"] = 0

    assert hr_drift.drift_pct(_with(zero)) is None


def test_drift_keys_on_field_name_not_label():
    def english(doc):
        doc["columns"] = [{"name": "avgHr", "label": "Avg HR"}, {"name": "adjustedPace", "label": "GAP"}]

    assert hr_drift.drift_pct(_with(english)) == 1.6


def test_drift_none_for_invalid_json():
    assert hr_drift.drift_pct("not json") is None


class LapAdapter:
    def __init__(self):
        self.calls = []

    async def fetch_hr_drift(self, label_id, sport_type):
        self.calls.append((label_id, sport_type))
        return 1.6


@pytest.mark.asyncio
async def test_update_hr_drift_marks_checked_and_skips_hard_workouts(monkeypatch):
    rows = [
        {"id": 1, "external_id": "easy", "activity_type": "trail_run", "workout_type": "long_run"},
        {"id": 2, "external_id": "hard", "activity_type": "outdoor_run", "workout_type": "interval"},
        {"id": 3, "external_id": "hike", "activity_type": "hike", "workout_type": None},
    ]
    stored = {}
    monkeypatch.setattr(coros_sync.db, "get_activities_needing_drift", lambda *a, **k: rows)
    monkeypatch.setattr(coros_sync.db, "set_activity_hr_drift", lambda aid, pct: stored.__setitem__(aid, pct))
    adapter = LapAdapter()

    assert await coros_sync.update_hr_drift(7, adapter) == 3
    assert adapter.calls == [("easy", 102)]
    assert stored == {1: 1.6, 2: None, 3: None}
