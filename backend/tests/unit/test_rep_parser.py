import pytest

from services.plan_generator import PlanGenerator
from services.rep_parser import parse_rep_block


@pytest.mark.parametrize(
    "text, expected",
    [
        ("8 x 12s hill sprints", (8, 12, "s")),
        ("6 reps of 10s maximum-effort", (6, 10, "s")),
        ("9 x 12-second maximum effort", (9, 12, "s")),
        ("3 x 10 min at threshold", (3, 10, "min")),
        ("5 x 400m", (5, 400, "m")),
        ("4 x 1.5 km", (4, 1.5, "km")),
        ("3 x 5 phút", (3, 5, "min")),
        ("8 x 10s Hill Sprints dốc >20%", (8, 10, "s")),
        ("8 × 10 giây", (8, 10, "s")),
        ("4x10 mỗi chân", None),
        ("3 x 5 min then 8 x 10s", None),
        ("8 x 10s, repeat the same 8 x 10s", (8, 10, "s")),
        ("0 x 10s", None),
        ("-3 x 5 min", None),
        ("easy running", None),
    ],
)
def test_rep_blocks(text, expected):
    assert parse_rep_block(text) == expected


def test_only_process_section_supplies_reps():
    text = (
        "Overall: build toward 5 x 400m. Process: Easy run → 8 x 10s Hill Sprints → Cool-down. Warning: avoid 4 x 1 km."
    )
    assert parse_rep_block(text) == (8, 10, "s")


@pytest.mark.parametrize("kind", ["Easy", "Long Run", "Tempo", "Recovery", "Interval", "Walk/Run"])
def test_any_run_can_get_missing_rep_fields_from_text(kind):
    assert PlanGenerator.resolve_interval_summary({"description": "Process: 8 x 10s Hill Sprints"}, kind) == (
        8,
        10,
        "s",
    )


@pytest.mark.parametrize("kind", ["Rest", "Strength", "Muscular Endurance", "ME"])
def test_non_runs_have_no_rep_summary(kind):
    assert PlanGenerator.resolve_interval_summary(
        {"description": "3 x 10 min", "interval_reps": 3, "interval_rep_value": 10, "interval_rep_unit": "min"}, kind
    ) == (None, None, None)


def test_invalid_explicit_rep_fields_fall_back_to_description():
    wo = {"interval_reps": "several", "interval_rep_unit": "laps", "description": "Process: 5 x 400m"}
    assert PlanGenerator.resolve_interval_summary(wo, "Interval") == (5, 400, "m")
