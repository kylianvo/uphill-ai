"""Unit tests for warehouse_extractor's _connect_with_retry -- no live DuckDB or
Metabase needed, duckdb.connect is mocked."""

from unittest.mock import MagicMock, patch

import duckdb
import pytest

from services import warehouse_extractor
from services.warehouse_extractor import _connect_with_retry

LOCK_CONFLICT_MESSAGE = 'IO Error: Could not set lock on file "uphill_dw.duckdb": Conflicting lock is held in PID 0.'
OTHER_IO_MESSAGE = "IO Error: Cannot open file, disk is full"


def test_retries_past_lock_conflict_then_succeeds(monkeypatch):
    monkeypatch.setattr(warehouse_extractor, "_CONNECT_RETRY_DELAY_SECONDS", 0.0)
    fake_conn = MagicMock()
    with patch(
        "services.warehouse_extractor.duckdb.connect",
        side_effect=[duckdb.IOException(LOCK_CONFLICT_MESSAGE), duckdb.IOException(LOCK_CONFLICT_MESSAGE), fake_conn],
    ) as mock_connect:
        result = _connect_with_retry("uphill_dw.duckdb")

    assert result is fake_conn
    assert mock_connect.call_count == 3


def test_exhausts_retry_budget_and_reraises(monkeypatch):
    monkeypatch.setattr(warehouse_extractor, "_CONNECT_RETRY_DELAY_SECONDS", 0.0)
    monkeypatch.setattr(warehouse_extractor, "_CONNECT_RETRY_ATTEMPTS", 3)
    with patch(
        "services.warehouse_extractor.duckdb.connect",
        side_effect=duckdb.IOException(LOCK_CONFLICT_MESSAGE),
    ) as mock_connect:
        with pytest.raises(duckdb.IOException, match="Conflicting lock is held"):
            _connect_with_retry("uphill_dw.duckdb")

    assert mock_connect.call_count == 3


def test_non_lock_conflict_error_reraises_immediately():
    with patch(
        "services.warehouse_extractor.duckdb.connect",
        side_effect=duckdb.IOException(OTHER_IO_MESSAGE),
    ) as mock_connect:
        with pytest.raises(duckdb.IOException, match="disk is full"):
            _connect_with_retry("uphill_dw.duckdb")

    assert mock_connect.call_count == 1
