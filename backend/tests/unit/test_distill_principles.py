"""scripts/distill_principles.py -- the operator-run NotebookLM principle sweep.

The retry cases here moved from test_kb_distiller.py when _query_with_retries moved
out of the service module: NotebookLM is no longer on any request path, so its client
code lives with the one script that still calls it.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import distill_principles as dp  # noqa: E402


def test_query_with_retries_does_not_retry_stream_overflow():
    with (
        patch(
            "services.notebooklm_service.NotebookLmService.query_notebook",
            new_callable=AsyncMock,
            side_effect=Exception("RPC response exceeded 52428800 bytes"),
        ) as nlm,
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(Exception, match="RPC response exceeded"):
            asyncio.run(dp._query_with_retries("nb", '{"tok":1}', "q"))
    assert nlm.call_count == 1  # deterministic overflow — retrying is pure waste


def test_query_with_retries_recovers_from_transient_failure():
    with (
        patch(
            "services.notebooklm_service.NotebookLmService.query_notebook",
            new_callable=AsyncMock,
            side_effect=[Exception("Server disconnected"), "recovered answer"],
        ) as nlm,
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        answer = asyncio.run(dp._query_with_retries("nb", '{"tok":1}', "q"))
    assert answer == "recovered answer"
    assert nlm.call_count == 2


def test_query_with_retries_gives_up_after_attempts():
    with (
        patch(
            "services.notebooklm_service.NotebookLmService.query_notebook",
            new_callable=AsyncMock,
            side_effect=Exception("DNS down"),
        ) as nlm,
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(Exception, match="DNS down"):
            asyncio.run(dp._query_with_retries("nb", '{"tok":1}', "q", attempts=3))
    assert nlm.call_count == 3


def test_sweep_refuses_without_notebook_config(monkeypatch):
    """A misconfigured run must fail loudly before it can produce a thin sweep that
    validate_domain_rows would then be asked to judge."""
    from config import settings

    monkeypatch.setattr(settings, "NOTEBOOKLM_AUTH_JSON", "")
    with pytest.raises(RuntimeError, match="not configured"):
        asyncio.run(dp.sweep_principles("scheduler", "test-key"))


def test_gear_has_no_notebook():
    """Gear's catalog comes from web discovery -- it must not be sweepable here."""
    with pytest.raises(KeyError):
        dp._notebook_id("gear")


def test_principle_domains_excludes_gear():
    assert dp.PRINCIPLE_DOMAINS == ("scheduler", "nutrition")
