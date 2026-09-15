"""Cost per call. Expected values are hand-computed from the price table in the spec:
gemini-3.8-flash through 2026-12-31: input 0.75, cached 0.075, output 3.75 (USD/1M);
from 2027-01-01: input 1.50, cached 0.15, output 7.50. Output price covers thinking."""

from datetime import date

from config import settings
from services import observability as obs

# 10k prompt tokens of which 2k cached, 1k output, 500 thinking.
USAGE = obs.Usage(input_tokens=10_000, output_tokens=1_000, thinking_tokens=500, cached_tokens=2_000)


def test_intro_pricing_subtracts_cached_tokens_and_bills_thinking_as_output():
    # 8000*0.75 + 2000*0.075 + 1500*3.75 = 6000 + 150 + 5625 = 11775 -> /1e6
    assert obs.cost_usd("gemini-3.8-flash", USAGE, on=date(2026, 9, 16)) == 0.011775


def test_last_day_of_intro_window_still_uses_intro_price():
    assert obs.cost_usd("gemini-3.8-flash", USAGE, on=date(2026, 12, 31)) == 0.011775


def test_standard_pricing_applies_from_2027():
    # 8000*1.50 + 2000*0.15 + 1500*7.50 = 12000 + 300 + 11250 = 23550 -> /1e6
    assert obs.cost_usd("gemini-3.8-flash", USAGE, on=date(2027, 1, 1)) == 0.02355


def test_unknown_model_is_unpriced_not_guessed():
    assert obs.cost_usd("some-other-model", USAGE, on=date(2026, 9, 16)) is None


def test_open_ended_window_from_an_overridden_table(monkeypatch):
    monkeypatch.setattr(
        settings, "LLM_PRICES_USD_PER_M", {"custom-model": [{"input": 1.0, "cached_input": 0.5, "output": 2.0}]}
    )
    usage = obs.Usage(input_tokens=1_000_000, output_tokens=250_000, thinking_tokens=250_000)

    # 1M*1.0 + 0 + 500k*2.0 = 2,000,000 -> /1e6
    assert obs.cost_usd("custom-model", usage, on=date(2030, 1, 1)) == 2.0
