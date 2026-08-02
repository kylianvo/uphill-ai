"""Nightly Postgres -> DuckDB ELT: extract raw tables, then dbt snapshot -> run -> test.
See docs/superpowers/specs/2026-07-29-duckdb-dbt-warehouse-design.md for the full design."""

import os
import subprocess
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

DUCKDB_PATH = os.environ.get("DUCKDB_PATH", "/opt/airflow/warehouse/uphill_dw.duckdb")
DBT_PROJECT_DIR = os.environ.get("DBT_PROJECT_DIR", "/opt/airflow/warehouse")
DBT_PROFILES_DIR = os.environ.get("DBT_PROFILES_DIR", "/opt/airflow/warehouse")

default_args = {"owner": "uphill-ai", "retries": 1}


def _extract(**context):
    from config import settings
    from services.warehouse_extractor import extract_raw_tables

    counts = extract_raw_tables(DUCKDB_PATH, settings.DATABASE_URL)
    for table, count in counts.items():
        print(f"raw.{table}: {count} rows")
    return counts


def _run_dbt(subcommand: list[str]):
    # NOTE on the DuckDB single-writer lock conflict (see
    # backend/services/warehouse_extractor.py's module docstring and
    # docs/superpowers/specs/2026-08-02-warehouse-dashboards-design.md): unlike
    # `extract` and `record_run_metadata`, the three tasks that call this
    # (dbt_snapshot/dbt_run/dbt_test) are NOT covered by the bespoke
    # `_connect_with_retry` lock-conflict retry. Each `dbt` invocation opens
    # its own read-write DuckDB connection internally as a subprocess, and dbt
    # doesn't expose a lock-conflict-specific retry hook -- blindly retrying a
    # failed `subprocess.run` on any non-zero exit would mask real dbt
    # failures (a broken model, a failing test) as well as lock conflicts,
    # which is worse than not retrying. These three tasks rely solely on
    # Airflow's own `default_args={"retries": 1}` (a single retry after ~5
    # min) as their backstop against a Metabase-held lock. This is a known,
    # accepted scope boundary, not an oversight.
    env = dict(os.environ, DBT_DUCKDB_PATH=DUCKDB_PATH)
    result = subprocess.run(
        ["dbt", *subcommand, "--project-dir", DBT_PROJECT_DIR, "--profiles-dir", DBT_PROFILES_DIR],
        env=env,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(f"dbt {' '.join(subcommand)} failed with exit code {result.returncode}")


def _dbt_snapshot(**context):
    _run_dbt(["snapshot"])


def _dbt_run(**context):
    _run_dbt(["run"])


def _dbt_test(**context):
    _run_dbt(["test"])


def _upstream_tasks_ran(context) -> bool:
    """True if extract/dbt_snapshot/dbt_run all succeeded, meaning dbt_test
    actually got to run and target/run_results.json reflects THIS run rather
    than being a stale leftover from a previous successful run.

    Deliberately does NOT check dbt_test's own task state here: `dbt test`
    exits non-zero (Airflow-"failed") whenever any test fails, which is a
    legitimate, freshly-written result in run_results.json -- not a reason to
    distrust the file. Only a failure in an *earlier* task means dbt_test was
    skipped (default trigger_rule="all_success") and never wrote a fresh file.
    """
    dag_run = context["dag_run"]
    for task_id in ("extract", "dbt_snapshot", "dbt_run"):
        ti = dag_run.get_task_instance(task_id)
        if ti is None or ti.state != "success":
            return False
    return True


def _record_run_metadata(**context):
    from services.warehouse_pipeline_metadata import parse_dbt_run_results, record_pipeline_run

    ti = context["ti"]
    raw_row_counts = ti.xcom_pull(task_ids="extract") or {}

    if not _upstream_tasks_ran(context):
        # extract/dbt_snapshot/dbt_run didn't all succeed, so dbt_test was
        # skipped and run_results.json (if it exists at all) is stale --
        # recording anything derived from it as 'success' would be a lie.
        # The earlier task's own failure already fails this DAG run; nothing
        # further to raise here.
        record_pipeline_run(DUCKDB_PATH, raw_row_counts, dbt_test_counts=None, upstream_ok=False)
        return

    run_results_path = os.path.join(DBT_PROJECT_DIR, "target", "run_results.json")
    dbt_test_counts = parse_dbt_run_results(run_results_path)
    record_pipeline_run(DUCKDB_PATH, raw_row_counts, dbt_test_counts, upstream_ok=True)

    if dbt_test_counts["failed"] > 0 or dbt_test_counts["errored"] > 0:
        raise RuntimeError(
            f"dbt test had {dbt_test_counts['failed']} failure(s) and {dbt_test_counts['errored']} error(s) "
            "(recorded to meta.pipeline_runs before re-raising)"
        )


with DAG(
    dag_id="dw_elt",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=datetime(2026, 7, 29),
    catchup=False,
    tags=["warehouse", "uphill-ai"],
) as dag:
    extract_task = PythonOperator(task_id="extract", python_callable=_extract)
    snapshot_task = PythonOperator(task_id="dbt_snapshot", python_callable=_dbt_snapshot)
    run_task = PythonOperator(task_id="dbt_run", python_callable=_dbt_run)
    test_task = PythonOperator(task_id="dbt_test", python_callable=_dbt_test)
    # trigger_rule="all_done": must run even when dbt_test fails, so a real test
    # regression lands a status="failed" row instead of leaving meta.pipeline_runs
    # stale. If extract/dbt_snapshot/dbt_run fail instead of dbt_test,
    # _upstream_tasks_ran() detects that dbt_test never got to run and records
    # status="incomplete" instead of trusting a possibly-stale run_results.json --
    # see _upstream_tasks_ran's docstring.
    record_metadata_task = PythonOperator(
        task_id="record_run_metadata",
        python_callable=_record_run_metadata,
        trigger_rule="all_done",
    )

    extract_task >> snapshot_task >> run_task >> test_task >> record_metadata_task
