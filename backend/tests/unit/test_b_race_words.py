import asyncio

from services import b_race_words as words

RACE = {"race_name": "Ta Xua Trail", "race_date": "2026-11-01", "distance_km": 42, "elevation_gain_m": 2400,
        "effort": "race"}  # fmt: skip
RISKY = {"level": "risky", "reasons": ["longer_than_trained"], "taper_days": 3, "recovery_days": 7,
         "numbers": {"effort_km": 66, "days_before_a": 42, "load_ratio": 1.94, "longest_recent_km": 34},
         "suggestion": {"distance_km": 25, "effort": "race"}, "cost": None}  # fmt: skip
GOOD = {**RISKY, "level": "good", "reasons": [], "suggestion": None}


def run(coro):
    return asyncio.run(coro)


def test_fallback_names_level_and_suggestion_en_vi():
    en = words.fallback_opinion(RISKY, RACE, "en")
    vi = words.fallback_opinion(RISKY, RACE, "vi")
    assert "Risky" in en and "25 km" in en and "34 km" in en
    assert "Rủi ro" in vi and "25 km" in vi
    for level in ("good", "conditions", "not_recommended"):
        for lang in ("en", "vi"):
            assert words.fallback_opinion({**RISKY, "level": level}, RACE, lang)


def test_every_fallback_is_grounded():
    for level in ("good", "conditions", "risky", "not_recommended"):
        v = {**RISKY, "level": level}
        for lang in ("en", "vi"):
            assert words.grounded_opinion(words.fallback_opinion(v, RACE, lang), v, RACE)


def test_model_text_with_invented_number_rejected(monkeypatch):
    async def model(*a, **k):
        return "Risky: this will cost you 9 days of peak training."

    monkeypatch.setattr(words, "_model_text", model)
    out = run(words.opinion_text(RISKY, RACE, "en", api_key="k"))
    assert out["source"] == "rules" and out["text"] == words.fallback_opinion(RISKY, RACE, "en")


def test_model_text_used_when_grounded(monkeypatch):
    async def model(*a, **k):
        return "Risky. 42 km is far past your longest recent run of 34 km. Take the 25 km instead."

    monkeypatch.setattr(words, "_model_text", model)
    assert run(words.opinion_text(RISKY, RACE, "en", api_key="k"))["source"] == "model"


def test_model_failure_uses_fallback(monkeypatch):
    async def model(*a, **k):
        raise TimeoutError

    monkeypatch.setattr(words, "_model_text", model)
    assert run(words.opinion_text(GOOD, RACE, "en", api_key="k"))["source"] == "rules"


def test_text_reused_when_verdict_unchanged(monkeypatch):
    async def model(*a, **k):
        raise AssertionError("no model call when the verdict is unchanged")

    first = run(words.opinion_text(GOOD, RACE, "en", api_key=None))
    monkeypatch.setattr(words, "_model_text", model)
    assert run(words.opinion_text(GOOD, RACE, "en", api_key="k", previous=first)) == first


def test_stored_text_only_shown_while_its_verdict_holds():
    stored = run(words.opinion_text(GOOD, RACE, "en", api_key=None))
    assert words.current_text(stored, GOOD, RACE, "en") == stored["text"]
    assert words.current_text(stored, RISKY, RACE, "en") == words.fallback_opinion(RISKY, RACE, "en")
