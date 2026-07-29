"""Golden-style correctness check for the DuckDB warehouse: after extract + dbt run,
compare row counts and a couple of aggregate metrics in the warehouse against live
Postgres, catching silent extraction/transform breakage.

    python scripts/dw_golden_eval.py

Requires backend/.env (DATABASE_URL) and a warehouse DuckDB file already built by
running the dw_elt Airflow DAG (or the extract + dbt run/test commands by hand --
see docs/superpowers/specs/2026-07-29-duckdb-dbt-warehouse-design.md).
"""

import os
import sys

import duckdb
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import engine  # noqa: E402

DUCKDB_PATH = os.environ.get(
    "DUCKDB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "warehouse", "uphill_dw.duckdb"),
)

SOURCE_TABLES = ("users", "plans", "workouts", "analytics_events", "block_reviews")


def _pg_count(table: str) -> int:
    with engine.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()


def main() -> None:
    conn = duckdb.connect(DUCKDB_PATH, read_only=True)
    failures = []

    for table in SOURCE_TABLES:
        pg_count = _pg_count(table)
        raw_count = conn.execute(f"SELECT COUNT(*) FROM raw.{table}").fetchone()[0]
        if raw_count != pg_count:
            failures.append(f"raw.{table}: {raw_count} rows, Postgres has {pg_count}")

    fct_plan_count = conn.execute("SELECT COUNT(*) FROM marts.fct_plan_generation").fetchone()[0]
    pg_plan_count = _pg_count("plans")
    if fct_plan_count != pg_plan_count:
        failures.append(f"fct_plan_generation: {fct_plan_count} rows, Postgres plans has {pg_plan_count}")

    fct_workout_count = conn.execute("SELECT COUNT(*) FROM marts.fct_workout").fetchone()[0]
    pg_workout_count = _pg_count("workouts")
    if fct_workout_count != pg_workout_count:
        failures.append(f"fct_workout: {fct_workout_count} rows, Postgres workouts has {pg_workout_count}")

    # Note: this only catches non-null-but-unresolved user_key values (a dangling FK). It does NOT
    # catch a regression back to 100%-null user_key -- that's the exact bug fixed earlier in this
    # project, and it's covered instead by dbt's own not_null test on fct_workout.user_key, not here.
    orphan_users = conn.execute(
        "SELECT COUNT(*) FROM marts.fct_workout w "
        "LEFT JOIN marts.dim_user du ON du.user_key = w.user_key "
        "WHERE w.user_key IS NOT NULL AND du.user_key IS NULL"
    ).fetchone()[0]
    if orphan_users:
        failures.append(f"fct_workout: {orphan_users} rows failed to resolve to a dim_user row")

    conn.close()

    if failures:
        print("GOLDEN CHECK FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(
        f"Golden check passed: {len(SOURCE_TABLES)} raw tables + fct_plan_generation + "
        "fct_workout match Postgres, and no fct_workout rows have a non-null user_key that fails "
        "to resolve to dim_user (100%-null user_key is separately covered by dbt's not_null test)."
    )


if __name__ == "__main__":
    main()
