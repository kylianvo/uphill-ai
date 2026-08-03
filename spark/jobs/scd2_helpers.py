"""Pure, dependency-free SCD2 helpers for dim_user_delta_merge.py -- no
pyspark/delta imports here, so these are unit-testable without a Spark
environment installed. See
docs/superpowers/specs/2026-08-03-spark-delta-lake-design.md for the full design.
"""

TRACKED_COLUMNS = ["role", "is_coach", "goal_type", "days_per_week", "current_weekly_km", "onboarding_complete"]
PASSTHROUGH_COLUMNS = ["email", "provider", "created_at"]
ALL_SOURCE_COLUMNS = ["user_id", *TRACKED_COLUMNS, *PASSTHROUGH_COLUMNS]


def build_change_condition(tracked_columns: list[str]) -> str:
    """SQL boolean expression (for a MERGE ... WHEN MATCHED AND ... clause),
    true when any tracked column differs between the merge source ('s') and
    target ('t') aliases. IS DISTINCT FROM is null-safe -- a column changing
    to/from NULL still counts as a change."""
    return " OR ".join(f"s.{col} IS DISTINCT FROM t.{col}" for col in tracked_columns)
