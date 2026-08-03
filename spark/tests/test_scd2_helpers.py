"""Unit tests for the pure, dependency-free SCD2 helper functions -- no
pyspark/delta-spark installation needed to run these."""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "jobs"))

from scd2_helpers import build_change_condition  # noqa: E402


def test_build_change_condition_joins_with_or():
    condition = build_change_condition(["role", "is_coach"])
    assert condition == "s.role IS DISTINCT FROM t.role OR s.is_coach IS DISTINCT FROM t.is_coach"


def test_build_change_condition_single_column():
    condition = build_change_condition(["role"])
    assert condition == "s.role IS DISTINCT FROM t.role"


def test_build_change_condition_uses_null_safe_comparison():
    condition = build_change_condition(["role"])
    assert "IS DISTINCT FROM" in condition
