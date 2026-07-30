"""Postgres -> DuckDB raw-layer extraction via DuckDB's postgres_scanner extension.

Materializes a fixed list of OLTP tables into DuckDB's `raw` schema. Most tables
are mutable (rows get updated in place -- onboarding fields, plan_status,
workout completion/rpe) so they get a full CREATE OR REPLACE TABLE each run.
analytics_events and block_reviews are append-only in practice (rows are never
updated after insert), so they're extracted incrementally instead: on first run
they're bootstrapped with a full copy, and every run after that only inserts
rows newer than the max timestamp already present in the raw table -- no
separate watermark-tracking table needed, the watermark lives in the data
itself. Known limitation: if a row were ever deleted upstream in one of these
two tables, the raw copy would drift (deletes never propagate). Acceptable here
since neither table is ever deleted from in practice.
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

# table -> column used both as the incremental watermark and as the strictly
# increasing ordering that makes "> watermark" safe to re-run without duplicating rows.
INCREMENTAL_WATERMARK_COLUMNS = {
    "analytics_events": "timestamp",
    "block_reviews": "created_at",
}


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


def _raw_table_exists(conn: duckdb.DuckDBPyConnection, table: str) -> bool:
    row = conn.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'raw' AND table_name = ?",
        [table],
    ).fetchone()
    return row[0] > 0


def _extract_table(conn: duckdb.DuckDBPyConnection, table: str) -> None:
    watermark_col = INCREMENTAL_WATERMARK_COLUMNS.get(table)

    if watermark_col is None or not _raw_table_exists(conn, table):
        conn.execute(f"CREATE OR REPLACE TABLE raw.{table} AS SELECT * FROM pg.{table}")
        return

    watermark = conn.execute(f"SELECT MAX({watermark_col}) FROM raw.{table}").fetchone()[0]
    if watermark is None:
        conn.execute(f"INSERT INTO raw.{table} SELECT * FROM pg.{table}")
    else:
        conn.execute(
            f"INSERT INTO raw.{table} SELECT * FROM pg.{table} WHERE {watermark_col} > ?",
            [watermark],
        )


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
                _extract_table(conn, table)
                counts[table] = conn.execute(f"SELECT COUNT(*) FROM raw.{table}").fetchone()[0]
        finally:
            conn.execute("DETACH pg")
        return counts
    finally:
        conn.close()
