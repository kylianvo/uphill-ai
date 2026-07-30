"""Integration test for warehouse_extractor -- requires live Postgres (uphill_ai_test),
see tests/integration/conftest.py for the DATABASE_URL/truncation fixtures this relies on."""

import os
import tempfile

import pytest
from sqlalchemy import text

from config import settings
from db import engine
from services.warehouse_extractor import SOURCE_TABLES, extract_raw_tables


@pytest.mark.integration
def test_extract_raw_tables_matches_postgres_counts(_init_test_database, _truncate_tables):
    with engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO users (email, name, role) VALUES "
                "('warehouse-test-1@uphill.ai', 'WH Test 1', 'user'), "
                "('warehouse-test-2@uphill.ai', 'WH Test 2', 'user')"
            )
        )
        conn.commit()

    with tempfile.TemporaryDirectory() as tmp_dir:
        duckdb_path = os.path.join(tmp_dir, "test_warehouse.duckdb")
        counts = extract_raw_tables(duckdb_path, settings.DATABASE_URL)

        assert set(counts.keys()) == set(SOURCE_TABLES)
        assert counts["users"] == 2
        assert counts["plans"] == 0

        import duckdb as duckdb_module

        conn = duckdb_module.connect(duckdb_path, read_only=True)
        emails = {row[0] for row in conn.execute("SELECT email FROM raw.users ORDER BY email").fetchall()}
        conn.close()
        assert emails == {"warehouse-test-1@uphill.ai", "warehouse-test-2@uphill.ai"}


@pytest.mark.integration
def test_extract_raw_tables_incrementally_appends_new_analytics_events(_init_test_database, _truncate_tables):
    with engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO analytics_events (event_name, timestamp) VALUES "
                "('first_batch_a', '2026-01-01 00:00:00+00'), "
                "('first_batch_b', '2026-01-01 00:00:01+00')"
            )
        )
        conn.commit()

    import duckdb as duckdb_module

    with tempfile.TemporaryDirectory() as tmp_dir:
        duckdb_path = os.path.join(tmp_dir, "test_warehouse.duckdb")

        counts = extract_raw_tables(duckdb_path, settings.DATABASE_URL)
        assert counts["analytics_events"] == 2

        # No new rows since the last extraction: a rerun must not duplicate the existing 2.
        counts = extract_raw_tables(duckdb_path, settings.DATABASE_URL)
        assert counts["analytics_events"] == 2

        with engine.connect() as conn:
            conn.execute(
                text(
                    "INSERT INTO analytics_events (event_name, timestamp) VALUES "
                    "('second_batch_a', '2026-01-02 00:00:00+00'), "
                    "('second_batch_b', '2026-01-02 00:00:01+00'), "
                    "('second_batch_c', '2026-01-02 00:00:02+00')"
                )
            )
            conn.commit()

        counts = extract_raw_tables(duckdb_path, settings.DATABASE_URL)
        assert counts["analytics_events"] == 5

        conn = duckdb_module.connect(duckdb_path, read_only=True)
        event_names = {row[0] for row in conn.execute("SELECT event_name FROM raw.analytics_events").fetchall()}
        conn.close()
        assert event_names == {
            "first_batch_a",
            "first_batch_b",
            "second_batch_a",
            "second_batch_b",
            "second_batch_c",
        }
