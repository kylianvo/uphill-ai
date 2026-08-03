"""Spark + Delta Lake demonstration: rebuilds dim_user via native Delta MERGE
(Type 2 SCD), reading users directly from Postgres. Deliberately narrow scope --
one table, not the whole star schema -- see
docs/superpowers/specs/2026-08-03-spark-delta-lake-design.md for the full design.

Run via (from a container with pyspark/delta-spark installed, matching the
cluster's Spark version -- e.g. this project's airflow-scheduler container):
    spark-submit --master spark://spark-master:7077 \
        --packages io.delta:delta-spark_2.12:3.2.0,org.postgresql:postgresql:42.7.3 \
        --conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension \
        --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog \
        /opt/spark-jobs/dim_user_delta_merge.py
"""

import os
import sys
from datetime import UTC, datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scd2_helpers import ALL_SOURCE_COLUMNS, TRACKED_COLUMNS, build_change_condition  # noqa: E402

from delta.tables import DeltaTable  # noqa: E402
from pyspark.sql import SparkSession, functions as F  # noqa: E402

POSTGRES_URL = os.environ.get("POSTGRES_JDBC_URL", "jdbc:postgresql://db:5432/uphill_ai")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "uphill")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "uphill_secret")
DELTA_TABLE_PATH = os.environ.get("DELTA_TABLE_PATH", "/opt/spark-jobs/delta/dim_user_scd2")


def read_users(spark: SparkSession):
    return (
        spark.read.format("jdbc")
        .option("url", POSTGRES_URL)
        .option("dbtable", "users")
        .option("user", POSTGRES_USER)
        .option("password", POSTGRES_PASSWORD)
        .option("driver", "org.postgresql.Driver")
        .load()
        .withColumnRenamed("id", "user_id")
        .select(*ALL_SOURCE_COLUMNS)
    )


def ensure_delta_table(spark: SparkSession, source_df) -> None:
    if DeltaTable.isDeltaTable(spark, DELTA_TABLE_PATH):
        return
    empty = spark.createDataFrame([], source_df.schema)
    (
        empty.withColumn("valid_from", F.lit(None).cast("timestamp"))
        .withColumn("valid_to", F.lit(None).cast("timestamp"))
        .withColumn("is_current", F.lit(None).cast("boolean"))
        .write.format("delta")
        .save(DELTA_TABLE_PATH)
    )


def merge_scd2(spark: SparkSession, source_df, run_ts: datetime) -> None:
    ensure_delta_table(spark, source_df)
    target = DeltaTable.forPath(spark, DELTA_TABLE_PATH)
    change_condition = build_change_condition(TRACKED_COLUMNS)

    # Step 1: close out current rows whose tracked columns changed.
    target.alias("t").merge(
        source_df.alias("s"),
        "s.user_id = t.user_id AND t.is_current = true",
    ).whenMatchedUpdate(
        condition=change_condition,
        set={"is_current": "false", "valid_to": f"TIMESTAMP'{run_ts.isoformat()}'"},
    ).execute()

    # Step 2: insert a fresh current row for brand-new users AND for users
    # whose previous version was just closed out in step 1 (their old row no
    # longer has is_current = true, so this insert-only merge treats them as
    # "not matched" this time and gives them a new current version).
    insert_df = (
        source_df.withColumn("valid_from", F.lit(run_ts))
        .withColumn("valid_to", F.lit(None).cast("timestamp"))
        .withColumn("is_current", F.lit(True))
    )
    target.alias("t").merge(
        insert_df.alias("s"),
        "s.user_id = t.user_id AND t.is_current = true",
    ).whenNotMatchedInsertAll().execute()


def main():
    spark = (
        SparkSession.builder.appName("dim_user_delta_merge")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .getOrCreate()
    )
    try:
        run_ts = datetime.now(UTC)
        source_df = read_users(spark)
        merge_scd2(spark, source_df, run_ts)
        current_count = spark.read.format("delta").load(DELTA_TABLE_PATH).filter("is_current = true").count()
        print(f"dim_user_scd2: {current_count} current rows as of {run_ts.isoformat()}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
