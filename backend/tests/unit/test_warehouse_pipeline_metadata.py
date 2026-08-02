"""Unit tests for warehouse_pipeline_metadata -- no live services needed, only a
temp DuckDB file and a JSON fixture."""

import json
import os
import tempfile

import duckdb

from services.warehouse_pipeline_metadata import parse_dbt_run_results, record_pipeline_run


def test_parse_dbt_run_results_counts_by_status():
    with tempfile.TemporaryDirectory() as tmp_dir:
        run_results_path = os.path.join(tmp_dir, "run_results.json")
        with open(run_results_path, "w") as f:
            json.dump(
                {
                    "results": [
                        {"status": "pass"},
                        {"status": "pass"},
                        {"status": "fail"},
                        {"status": "error"},
                    ]
                },
                f,
            )

        counts = parse_dbt_run_results(run_results_path)

    assert counts == {"passed": 2, "failed": 1, "errored": 1}


def test_record_pipeline_run_writes_a_row():
    with tempfile.TemporaryDirectory() as tmp_dir:
        duckdb_path = os.path.join(tmp_dir, "test.duckdb")

        record_pipeline_run(
            duckdb_path,
            raw_row_counts={"users": 10, "plans": 3},
            dbt_test_counts={"passed": 40, "failed": 0, "errored": 0},
        )

        conn = duckdb.connect(duckdb_path, read_only=True)
        row = conn.execute(
            "SELECT raw_row_counts, dbt_tests_passed, dbt_tests_failed, dbt_tests_errored, status "
            "FROM meta.pipeline_runs"
        ).fetchone()
        conn.close()

    assert json.loads(row[0]) == {"users": 10, "plans": 3}
    assert row[1:] == (40, 0, 0, "success")


def test_record_pipeline_run_marks_failed_status_on_test_failures():
    with tempfile.TemporaryDirectory() as tmp_dir:
        duckdb_path = os.path.join(tmp_dir, "test.duckdb")

        record_pipeline_run(
            duckdb_path,
            raw_row_counts={"users": 10},
            dbt_test_counts={"passed": 39, "failed": 1, "errored": 0},
        )

        conn = duckdb.connect(duckdb_path, read_only=True)
        status = conn.execute("SELECT status FROM meta.pipeline_runs").fetchone()[0]
        conn.close()

    assert status == "failed"
