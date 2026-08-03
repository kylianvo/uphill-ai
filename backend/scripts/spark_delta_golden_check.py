"""Golden-style correctness check for the Spark/Delta dim_user_scd2 table --
compares its current-row count against live Postgres, using DuckDB's delta
extension (no JVM/Spark session needed just to verify). See
docs/superpowers/specs/2026-08-03-spark-delta-lake-design.md for the full design.

Usage (from backend/):  python scripts/spark_delta_golden_check.py
"""

import os
import sys

import duckdb
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import engine  # noqa: E402

DELTA_TABLE_PATH = os.environ.get(
    "DELTA_TABLE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "spark", "delta", "dim_user_scd2"),
)


def main() -> None:
    conn = duckdb.connect()
    conn.execute("INSTALL delta")
    conn.execute("LOAD delta")

    current_count = conn.execute(
        "SELECT COUNT(*) FROM delta_scan(?) WHERE is_current = true", [DELTA_TABLE_PATH]
    ).fetchone()[0]

    # SCD2 invariant check: no user_id should ever have more than one row with
    # is_current = true. A row-count match against Postgres alone can't catch
    # this -- e.g. one user stuck with 2 current rows and another with 0 would
    # still produce the same total count. Self-contained on the Delta table
    # alone, no live Postgres/Spark needed.
    duplicate_current_count = conn.execute(
        "SELECT COUNT(*) FROM "
        "(SELECT user_id FROM delta_scan(?) WHERE is_current = true GROUP BY user_id HAVING COUNT(*) > 1)",
        [DELTA_TABLE_PATH],
    ).fetchone()[0]
    conn.close()

    with engine.connect() as pg_conn:
        pg_count = pg_conn.execute(text("SELECT COUNT(*) FROM users")).scalar()

    failed = False

    if current_count != pg_count:
        print(f"GOLDEN CHECK FAILED: dim_user_scd2 has {current_count} current rows, Postgres users has {pg_count}")
        failed = True

    if duplicate_current_count > 0:
        print(
            "GOLDEN CHECK FAILED (SCD2 invariant violation): "
            f"{duplicate_current_count} user_id(s) have more than one row with is_current = true"
        )
        failed = True

    if failed:
        sys.exit(1)

    print(f"Golden check passed: dim_user_scd2 has {current_count} current rows, matching Postgres users.")
    print("Golden check passed: no user_id has more than one is_current = true row (SCD2 invariant holds).")


if __name__ == "__main__":
    main()
