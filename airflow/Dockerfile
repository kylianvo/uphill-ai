FROM apache/airflow:2.10.4-python3.12

USER root
# pyspark/delta-spark's spark-submit needs a JVM on PATH -- this image has
# none by default.
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jdk-headless \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    # arch-portable JAVA_HOME (arm64 vs amd64 differ in the openjdk package
    # path) -- symlink to whichever one apt actually installed.
    && ln -s "$(dirname "$(dirname "$(readlink -f "$(which java)")")")" /usr/lib/jvm/default-java
ENV JAVA_HOME=/usr/lib/jvm/default-java
COPY backend/requirements.txt /tmp/backend-requirements.txt
USER airflow
RUN pip install --no-cache-dir -r /tmp/backend-requirements.txt \
    # backend/requirements.txt pins sqlalchemy>=2.0.0, which upgrades the
    # image's SQLAlchemy past apache-airflow 2.10.4's own constraint
    # (sqlalchemy<2.0,>=1.4.36) and breaks `airflow db init`/webserver at
    # import time. Backend code only uses SQLAlchemy Core (engine/text()),
    # which is unaffected by the downgrade, so re-pin to Airflow's range.
    && pip install --no-cache-dir "sqlalchemy>=1.4.36,<2.0"
RUN pip install --no-cache-dir dbt-duckdb==1.9.4
# pyspark's version must match the cluster's Spark version exactly (see
# docker-compose.yml's spark-master/spark-worker, image bitnamilegacy/spark:3.5,
# which resolves to Spark 3.5.6 as of this writing -- confirmed via
# `docker compose exec spark-master spark-submit --version`), or job
# submission fails with a version-mismatch error.
RUN pip install --no-cache-dir pyspark==3.5.6 delta-spark==3.2.0
