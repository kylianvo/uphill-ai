"""The scheduler KB must cover the tier range the planner generates for.

Before these rows existed, all 29 scheduler principles were pitched at one audience: a
trained mountain athlete. Retrieval therefore grounded a beginner's plan on gym ME
protocols and 14-week progressions -- grounding was actively making the plan worse.
Since the prompt's beginner rules quote figures from these rows, a sweep that dropped
them would leave the prompt asserting numbers with nothing behind them.
"""

import json
import os

import pytest

SEED_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "kb_seed",
    "scheduler.json",
)

ELITE_TITLES = (
    "Weeks Containing Two or More Quality Sessions",
    "Periodization Above 100 km per Week",
    "Double-Day Training: Warrant, Allocation and Spacing",
    "Readiness and Overreaching Markers in Highly Trained Athletes",
)

BEGINNER_TITLES = (
    "Walk-to-Run Progression for Complete Beginners",
    "Transitioning from Run/Walk Intervals to Continuous Running",
    "Connective-Tissue Adaptation and Injury Risk in New Runners",
    "Regulating Effort Without Pace or Heart-Rate Data",
)


@pytest.fixture(scope="module")
def chunks():
    with open(SEED_PATH, encoding="utf-8") as f:
        return json.load(f)["chunks"]


@pytest.mark.parametrize("title", BEGINNER_TITLES)
def test_the_beginner_principles_are_present(chunks, title):
    assert any(c["title"] == title for c in chunks), f"missing scheduler principle: {title}"


@pytest.mark.parametrize("title", ELITE_TITLES)
def test_the_high_volume_principles_are_present(chunks, title):
    assert any(c["title"] == title for c in chunks), f"missing scheduler principle: {title}"


def test_every_row_has_the_shape_load_seed_expects(chunks):
    for c in chunks:
        assert c["domain"] == "scheduler"
        assert c["kind"] == "principle"
        assert c["title"].strip()
        assert c["content"].strip()


def test_titles_are_unique(chunks):
    """replace_kb_chunks keys on the row set; duplicate titles make retrieval return
    near-identical neighbours and waste top-k slots."""
    titles = [c["title"] for c in chunks]
    assert len(titles) == len(set(titles))


def test_the_figures_the_prompt_quotes_are_actually_in_the_kb(chunks):
    """services/plan_rules.py states these numbers as doctrine. If a re-sweep drops
    them, the prompt is asserting figures the knowledge base no longer supports."""
    body = " ".join(c["content"] for c in chunks)
    for figure in (
        # beginner end
        "1 minute of running alternating with 1 minute of walking",
        "10 minute run / 3 minute walk",
        "one seventh",
        "3 sessions per week",
        "10-15%",
        "nasal breathing",
        # elite end
        "7% to 10% per week",
        "10% per year",
        "30 to 40 minutes",
        "2.5 to 3.5 mMol/L",
        "35% to 45%",
        "8 to 12 hour",
    ):
        assert figure in body, f"figure quoted by the prompt is absent from the KB: {figure}"


def test_no_row_is_too_thin_to_ground_anything(chunks):
    for c in chunks:
        assert len(c["content"]) >= 200, f"thin chunk: {c['title']} ({len(c['content'])} chars)"
