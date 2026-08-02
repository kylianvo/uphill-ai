"""End-to-end demo: generate clickstream traffic, trigger the warehouse DAG on
demand, wait for it to finish, print a before/after summary and the Metabase
dashboard URLs. See docs/superpowers/specs/2026-08-02-warehouse-dashboards-design.md
for the full design.

Usage (from backend/, with the full Docker Compose stack up):
    python scripts/run_e2e_demo.py --events 200
"""

import argparse
import json
import os
import subprocess
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb

from config import settings  # noqa: E402
from scripts.simulate_clickstream import run as run_simulation  # noqa: E402

DUCKDB_PATH = os.environ.get(
    "DUCKDB_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "warehouse", "uphill_dw.duckdb")
)


def _row_counts() -> dict[str, int]:
    conn = duckdb.connect(DUCKDB_PATH, read_only=True)
    try:
        return {
            table: conn.execute(f"SELECT COUNT(*) FROM raw.{table}").fetchone()[0]
            for table in ("analytics_events", "block_reviews")
        }
    finally:
        conn.close()


def _trigger_dag_and_wait(dag_id: str = "dw_elt", timeout: float = 300.0) -> None:
    # A paused DAG accepts manual triggers but the scheduler never runs their tasks
    # (the run just sits in "queued" forever), so unpause first.
    subprocess.run(
        ["docker", "compose", "exec", "-T", "airflow-scheduler", "airflow", "dags", "unpause", dag_id],
        check=True,
    )

    run_id = f"e2e_demo_{int(time.time())}"
    subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "airflow-scheduler",
            "airflow",
            "dags",
            "trigger",
            dag_id,
            "--run-id",
            run_id,
        ],
        check=True,
    )

    # This Airflow version's `dags state` subcommand takes an execution_date, not a
    # run_id, so we poll `dags list-runs --output json` and filter by run_id instead.
    start = time.time()
    while time.time() - start < timeout:
        result = subprocess.run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "airflow-scheduler",
                "airflow",
                "dags",
                "list-runs",
                "-d",
                dag_id,
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        runs = json.loads(result.stdout)
        matching = [run for run in runs if run["run_id"] == run_id]
        state = matching[0]["state"] if matching else "unknown"
        print(f"  DAG state: {state}")
        if state == "success":
            return
        if state == "failed":
            raise RuntimeError(f"DAG run {run_id} failed")
        time.sleep(5)

    raise TimeoutError(f"DAG run {run_id} did not finish within {timeout}s")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=int, default=200)
    args = parser.parse_args()

    print("Step 1/4: recording pre-run row counts...")
    before = _row_counts()
    print(f"  before: {before}")

    print(f"Step 2/4: simulating {args.events} clickstream events through /api/analytics/track_batch...")
    run_simulation(rate=1000, duration=None, count=args.events, burst=True)

    print("Step 3/4: triggering dw_elt DAG and waiting for it to finish...")
    _trigger_dag_and_wait()

    print("Step 4/4: recording post-run row counts...")
    after = _row_counts()
    print(f"  after: {after}")

    print("\nSummary:")
    for table in before:
        print(f"  raw.{table}: {before[table]} -> {after[table]} (+{after[table] - before[table]})")

    print(f"\nOpen dashboards at {settings.METABASE_URL}")


if __name__ == "__main__":
    main()
