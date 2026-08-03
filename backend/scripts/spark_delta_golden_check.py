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
        f"SELECT COUNT(*) FROM delta_scan('{DELTA_TABLE_PATH}') WHERE is_current = true"
    ).fetchone()[0]
    conn.close()

    with engine.connect() as pg_conn:
        pg_count = pg_conn.execute(text("SELECT COUNT(*) FROM users")).scalar()

    if current_count != pg_count:
        print(f"GOLDEN CHECK FAILED: dim_user_scd2 has {current_count} current rows, Postgres users has {pg_count}")
        sys.exit(1)

    print(f"Golden check passed: dim_user_scd2 has {current_count} current rows, matching Postgres users.")


if __name__ == "__main__":
    main()
