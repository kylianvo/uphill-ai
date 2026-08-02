"""Records one row per dw_elt DAG run into DuckDB's meta.pipeline_runs table --
per-table row counts, dbt test pass/fail/error counts, and overall status. This
is the data source for the Pipeline Health dashboard. See
docs/superpowers/specs/2026-08-02-warehouse-dashboards-design.md for the full design.
"""

import json
from datetime import UTC, datetime

from services.warehouse_extractor import _connect_with_retry


def parse_dbt_run_results(run_results_path: str) -> dict[str, int]:
    """Parse dbt's target/run_results.json (written by the most recent dbt
    invocation -- here, dbt test) into pass/fail/error counts."""
    with open(run_results_path) as f:
        run_results = json.load(f)

    passed = failed = errored = 0
    for result in run_results.get("results", []):
        status = result.get("status")
        if status == "pass":
            passed += 1
        elif status == "fail":
            failed += 1
        elif status == "error":
            errored += 1
    return {"passed": passed, "failed": failed, "errored": errored}


def record_pipeline_run(
    duckdb_path: str,
    raw_row_counts: dict[str, int],
    dbt_test_counts: dict[str, int] | None,
    upstream_ok: bool = True,
) -> None:
    """Write one row to meta.pipeline_runs summarizing this DAG run.

    `upstream_ok=False` means an earlier task (extract/dbt_snapshot/dbt_run)
    failed before dbt_test ever ran, so `target/run_results.json` -- if present
    at all -- is stale (left over from a prior successful run), not this run's
    result. In that case `dbt_test_counts` is ignored/may be None and the row
    is recorded with status='incomplete' rather than deriving a (possibly
    false) 'success' from stale file contents. See dw_elt_dag.py's
    `_upstream_tasks_ran` for how the caller determines this.
    """
    if not upstream_ok:
        status = "incomplete"
        dbt_test_counts = {"passed": 0, "failed": 0, "errored": 0}
    else:
        status = "success" if dbt_test_counts["failed"] == 0 and dbt_test_counts["errored"] == 0 else "failed"

    # Same DuckDB single-writer lock conflict as extract_raw_tables (see
    # warehouse_extractor.py's module docstring) -- reuse its retry helper
    # rather than duplicating the retry loop here.
    conn = _connect_with_retry(duckdb_path)
    try:
        conn.execute("CREATE SCHEMA IF NOT EXISTS meta")
        conn.execute("CREATE SEQUENCE IF NOT EXISTS meta.pipeline_runs_run_id_seq")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meta.pipeline_runs (
                run_id INTEGER PRIMARY KEY DEFAULT nextval('meta.pipeline_runs_run_id_seq'),
                run_timestamp TIMESTAMP NOT NULL,
                raw_row_counts JSON NOT NULL,
                dbt_tests_passed INTEGER NOT NULL,
                dbt_tests_failed INTEGER NOT NULL,
                dbt_tests_errored INTEGER NOT NULL,
                status VARCHAR NOT NULL
            )
        """)
        conn.execute(
            "INSERT INTO meta.pipeline_runs "
            "(run_timestamp, raw_row_counts, dbt_tests_passed, dbt_tests_failed, dbt_tests_errored, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                datetime.now(UTC),
                json.dumps(raw_row_counts),
                dbt_test_counts["passed"],
                dbt_test_counts["failed"],
                dbt_test_counts["errored"],
                status,
            ],
        )
    finally:
        conn.close()
