"""Postgres -> DuckDB raw-layer extraction via DuckDB's postgres_scanner extension.

Materializes a fixed list of OLTP tables into DuckDB's `raw` schema with a full
CREATE OR REPLACE TABLE ... AS SELECT each run (no incremental/CDC -- see
docs/superpowers/specs/2026-07-29-duckdb-dbt-warehouse-design.md, Non-goals).
"""

from urllib.parse import urlparse

import duckdb

SOURCE_TABLES = (
    "users",
    "plans",
    "workouts",
    "analytics_events",
    "block_reviews",
    "workout_types",
)


def _pg_conninfo(database_url: str) -> str:
    """Convert a SQLAlchemy-style postgresql:// URL into a libpq keyword/value conninfo string.

    Assumes a "simple" username/password (no spaces or single quotes) -- fine for this project's
    trusted, operator-controlled DATABASE_URL, but would need proper libpq escaping if ever used
    against untrusted credentials.
    """
    parsed = urlparse(database_url)
    parts = [
        f"host={parsed.hostname}",
        f"port={parsed.port or 5432}",
        f"dbname={parsed.path.lstrip('/')}",
        f"user={parsed.username}",
        f"password={parsed.password}",
    ]
    return " ".join(parts)


def extract_raw_tables(duckdb_path: str, database_url: str) -> dict[str, int]:
    """Attach Postgres and materialize each source table into DuckDB's raw schema.

    Returns table_name -> row_count, for the caller (Airflow task log / golden
    check) to report.
    """
    conn = duckdb.connect(duckdb_path)
    try:
        conn.execute("INSTALL postgres")
        conn.execute("LOAD postgres")
        conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
        conninfo = _pg_conninfo(database_url)
        conn.execute(f"ATTACH '{conninfo}' AS pg (TYPE POSTGRES, READ_ONLY)")
        counts: dict[str, int] = {}
        try:
            for table in SOURCE_TABLES:
                conn.execute(f"CREATE OR REPLACE TABLE raw.{table} AS SELECT * FROM pg.{table}")
                counts[table] = conn.execute(f"SELECT COUNT(*) FROM raw.{table}").fetchone()[0]
        finally:
            conn.execute("DETACH pg")
        return counts
    finally:
        conn.close()
