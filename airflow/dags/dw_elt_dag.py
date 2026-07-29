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

    extract_task >> snapshot_task >> run_task >> test_task
