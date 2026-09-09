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


class TestNotCoveredHandling:
    """A sweep asks about topics the notebook may not cover. Scheduler principles
    REPLACE the domain wholesale on save, so a generalised answer to a topic with no
    source behind it would overwrite good rows with invented ones."""

    def test_the_query_forbids_generalising_beyond_the_documents(self):
        q = dp._sweep_query("walk-to-run progression", "Be specific with numbers.")
        assert "walk-to-run progression" in q
        assert dp.NOT_COVERED in q
        assert "Do NOT generalise" in q
        assert "outside these documents" in q

    def test_a_bare_marker_is_recognised(self):
        assert dp._is_not_covered("NOT COVERED")
        assert dp._is_not_covered("  not covered  ")

    def test_a_marker_wrapped_in_a_sentence_is_recognised(self):
        assert dp._is_not_covered("The provided documents do not address this. NOT COVERED.")

    def test_an_empty_answer_counts_as_not_covered(self):
        assert dp._is_not_covered("")
        assert dp._is_not_covered("   ")

    def test_a_real_summary_is_not_discarded_just_for_mentioning_the_phrase(self):
        """The check is deliberately scoped to short answers, so a genuine summary that
        happens to note a gap in passing still becomes chunks."""
        long_answer = (
            "Muscular endurance training develops local fatigue resistance in the propelling "
            "muscles. Gym-based circuits use 4-6 sets of 10 reps with 60s rest. " * 4
        ) + " Downhill running is NOT COVERED in detail by these sources."
        assert len(long_answer) >= 200
        assert not dp._is_not_covered(long_answer)


class TestTierGapTopics:
    def test_the_sweep_covers_both_ends_of_the_tier_range(self):
        topics = " ".join(dp.SCHEDULER_TOPICS).lower()
        assert "walk-to-run progression" in topics
        assert "continuous running" in topics
        assert "new runners" in topics
        assert "talk test" in topics
        assert "100 km per week" in topics
        assert "double-day" in topics
