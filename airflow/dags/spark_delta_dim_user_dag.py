"""Standalone-cluster Spark + Delta Lake demo: rebuilds dim_user via native
Delta MERGE (Type 2 SCD). Independent of dw_elt/kb_distill -- a separate,
deliberately narrow demonstration, not part of the DuckDB warehouse. See
docs/superpowers/specs/2026-08-03-spark-delta-lake-design.md for the full design."""

import subprocess
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

SPARK_MASTER_URL = "spark://spark-master:7077"
JOB_PATH = "/opt/spark-jobs/dim_user_delta_merge.py"
SPARK_PACKAGES = "io.delta:delta-spark_2.12:3.2.0,org.postgresql:postgresql:42.7.3"

default_args = {"owner": "uphill-ai", "retries": 1}


def _submit_spark_job(**context):
    result = subprocess.run(
        [
            "spark-submit",
            "--master", SPARK_MASTER_URL,
            "--packages", SPARK_PACKAGES,
            "--conf", "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension",
            "--conf", "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog",
            JOB_PATH,
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(f"spark-submit failed with exit code {result.returncode}")


with DAG(
    dag_id="spark_delta_dim_user",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=datetime(2026, 8, 3),
    catchup=False,
    tags=["spark", "delta-lake", "uphill-ai"],
) as dag:
    submit_task = PythonOperator(task_id="submit_spark_job", python_callable=_submit_spark_job)
