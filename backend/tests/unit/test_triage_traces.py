"""scripts/triage_traces: which scores flag a trace."""

import os
import sys
from datetime import UTC, datetime
from types import SimpleNamespace as NS

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts import triage_traces  # noqa: E402


class FakeScores:
    def __init__(self, by_name):
        self.by_name = by_name
        self.calls = []

    def get_many_v3(self, *, limit, cursor, name, **filters):
        self.calls.append((name, filters))
        return NS(data=self.by_name.get(name, []), meta=NS(cursor=None))


def _score(kind, id_):
    return NS(subject=NS(kind=kind, id=id_))


def test_flags_trace_scores_with_reasons_and_ignores_other_subjects():
    scores = FakeScores(
        {
            "thumbs": [_score("trace", "t1")],
            "judge_safe": [_score("trace", "t1"), _score("session", "s1")],
            "plan_engine": [_score("trace", "t2")],
        }
    )
    flagged = triage_traces.flagged_traces(NS(scores_v3=scores), datetime(2026, 9, 1, tzinfo=UTC))

    assert flagged == {
        "t1": ["thumbs down", "judge_safe < 0.75"],
        "t2": ["rule-based plan fallback"],
    }
    filters = dict(scores.calls)
    assert filters["plan_engine"]["value"] == "rules"
    assert filters["thumbs"]["data_type"] == "NUMERIC" and filters["thumbs"]["value_max"] < 0
