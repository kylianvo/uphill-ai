"""Schema tests for the device-integration tables. Needs a live Postgres."""

from sqlalchemy import text

from db import engine

EXPECTED = ["activities", "athlete_connections", "daily_metrics"]


def _columns(table: str) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT column_name FROM information_schema.columns " "WHERE table_name = :t"),
            {"t": table},
        ).fetchall()
    return {r[0] for r in rows}


def test_all_integration_tables_exist():
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT table_name FROM information_schema.tables " "WHERE table_name = ANY(:names)"),
            {"names": EXPECTED},
        ).fetchall()
    assert sorted(r[0] for r in rows) == EXPECTED


def test_activities_carries_device_model_for_coros_attribution():
    # COROS Agreement 14.5 requires naming the source device model wherever
    # their data is displayed; failure is a material breach.
    assert "device_model" in _columns("activities")


def test_activities_external_ids_supports_cross_provider_dedup():
    assert "external_ids" in _columns("activities")


def test_athlete_connections_stores_tokens_encrypted_not_plaintext():
    cols = _columns("athlete_connections")
    assert "access_token_enc" in cols
    assert "refresh_token_enc" in cols
    assert "access_token" not in cols


def test_daily_metrics_is_unique_per_user_date_provider():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT indexdef FROM pg_indexes WHERE tablename = 'daily_metrics'")).fetchall()
    assert any("UNIQUE" in r[0] and "metric_date" in r[0] for r in rows)
