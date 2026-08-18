"""Nightly Postgres -> DuckDB ELT, run via cron instead of Airflow.

Prod's single-CPU/2GB box can't carry Airflow's always-on webserver+scheduler
(see deploy_dw.sh), so this mirrors airflow/dags/dw_elt_dag.py's task sequence
(extract -> dbt snapshot -> dbt run -> dbt test -> record_run_metadata) as one
plain script invoked by cron: `docker compose exec -T backend python scripts/run_dw_elt.py`.
Dev keeps the full Airflow DAG for orchestration work -- this script is prod-only.

dbt runs out of the isolated venv at DBT_BIN (default /warehouse/.venv/bin/dbt,
created by deploy_dw.sh) rather than the container's global site-packages:
dbt-core hard-requires protobuf>=6.0, which conflicts with (deprecated but
still in use) google-generativeai's protobuf<6.0 pin -- installing dbt-duckdb
globally would silently bump protobuf and risk breaking every Gemini call.
The venv keeps dbt's dependency tree fully separate from the app's.

Usage (from backend/): python scripts/run_dw_elt.py
"""

import os
import subprocess
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings  # noqa: E402
from services.warehouse_extractor import extract_raw_tables  # noqa: E402
from services.warehouse_pipeline_metadata import (  # noqa: E402
    parse_dbt_run_results,
    record_pipeline_run,
)

DUCKDB_PATH = os.environ.get("DUCKDB_PATH", "/warehouse/uphill_dw.duckdb")
DBT_PROJECT_DIR = os.environ.get("DBT_PROJECT_DIR", "/warehouse")
DBT_PROFILES_DIR = os.environ.get("DBT_PROFILES_DIR", "/warehouse")
DBT_BIN = os.environ.get("DBT_BIN", "/warehouse/.venv/bin/dbt")


def _run_dbt(subcommand: list[str]) -> None:
    env = dict(os.environ, DBT_DUCKDB_PATH=DUCKDB_PATH)
    result = subprocess.run(
        [DBT_BIN, *subcommand, "--project-dir", DBT_PROJECT_DIR, "--profiles-dir", DBT_PROFILES_DIR],
        env=env,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(f"dbt {' '.join(subcommand)} failed with exit code {result.returncode}")


def main() -> int:
    raw_row_counts: dict[str, int] = {}
    try:
        raw_row_counts = extract_raw_tables(DUCKDB_PATH, settings.DATABASE_URL)
        for table, count in raw_row_counts.items():
            print(f"raw.{table}: {count} rows")

        _run_dbt(["snapshot"])
        _run_dbt(["run"])
    except Exception as exc:
        print(f"dw_elt: upstream step failed before dbt test ran: {exc}")
        record_pipeline_run(DUCKDB_PATH, raw_row_counts, dbt_test_counts=None, upstream_ok=False)
        return 1

    # dbt test's own exit code is a legitimate result (some tests failing),
    # not a reason to skip recording -- record it either way, same as the
    # Airflow DAG's record_run_metadata does with trigger_rule="all_done".
    test_failed = False
    try:
        _run_dbt(["test"])
    except RuntimeError as exc:
        print(exc)
        test_failed = True

    run_results_path = os.path.join(DBT_PROJECT_DIR, "target", "run_results.json")
    dbt_test_counts = parse_dbt_run_results(run_results_path)
    record_pipeline_run(DUCKDB_PATH, raw_row_counts, dbt_test_counts, upstream_ok=True)

    if test_failed or dbt_test_counts["failed"] > 0 or dbt_test_counts["errored"] > 0:
        print(
            f"dw_elt: dbt test had {dbt_test_counts['failed']} failure(s) and "
            f"{dbt_test_counts['errored']} error(s) (recorded to meta.pipeline_runs)"
        )
        return 1

    print("dw_elt: completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
