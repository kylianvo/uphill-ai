"""Source and chapter provenance for the scheduler philosophy chunks.

The chunks were swept from a NotebookLM notebook that holds the book AND the Evoke
Endurance Uphill Athlete Book Club lectures and podcasts. An earlier revision labelled
every chunk as a book chapter, using a made-up 15-chapter, five-section outline. The
real book has 12 chapters (CHAPTERS below) and no fueling, tapering or race-day
chapter, and many chunks carry podcast material the 2019 book cannot contain (Tom
Evans' and Ruth Croft's preparation, Jack Kuenzle, Ingebrigtsen, McKay et al. 2022).

So each chunk now records:
  - source: BOOK when the chunk restates the book's doctrine, BOOK_CLUB_PODCAST when
    it carries Book Club / podcast material (often alongside book doctrine);
  - chapter_num: the official chapter the topic belongs to, or None when the book has
    no chapter on it or the chapter could not be confirmed. The assignment is by topic
    -- the sweep did not keep page-level citations -- so treat it as "where to read
    more", not as a quotation reference. The tier rows added later (walk-to-run,
    high-volume, athlete level) carry no chapter until checked against the book.
"""

from typing import Any

BOOK_TITLE = "Training for the Uphill Athlete"
BOOK_AUTHORS = "Steve House, Scott Johnston, Kilian Jornet"
BOOK_CLUB_TITLE = "Evoke Endurance — Uphill Athlete Book Club & podcast"

BOOK = "book"
BOOK_CLUB_PODCAST = "book_club_podcast"

# The official chapter list of the book.
CHAPTERS: dict[int, str] = {
    1: "The Physiology of Endurance",
    2: "The Methodologies of Endurance Training",
    3: "Monitoring Your Training",
    4: "The Application Process: Where Theory Meets Reality",
    5: "Strength Training for the Uphill Athlete",
    6: "General Strength Assessment and Improvement",
    7: "Specific Strength-Training Methods",
    8: "Programming",
    9: "Transition Period Training",
    10: "Introduction to the Base Period (for Both Running and Ski Mountaineering)",
    11: "Special Considerations for Skimo and Ski Mountaineering",
    12: "Special Considerations for Mountain Running",
}


def _entry(chapter_num: int | None, source: str, topic: str) -> dict[str, Any]:
    return {
        "book": BOOK_TITLE if source == BOOK else BOOK_CLUB_TITLE,
        "source": source,
        "chapter_num": chapter_num,
        "chapter_title": CHAPTERS[chapter_num] if chapter_num else None,
        "topic": topic,
    }


# 38 scheduler philosophy chunks, keyed by kb_seed/scheduler.json title.
SCHEDULER_CHUNK_PROVENANCE: dict[str, dict[str, Any]] = {
    "Difference Between Muscular Endurance and Conventional Strength Training": _entry(
        7, BOOK, "Difference Between Muscular Endurance and Conventional Strength Training"
    ),
    "Gym-Based ME Workout Design": _entry(7, BOOK, "Gym-Based ME Workout Design"),
    "Progressive 14-Week Gym ME Protocol": _entry(7, BOOK, "Progressive 14-Week Gym ME Protocol"),
    "Execution Guidelines and Phase Integration": _entry(7, BOOK, "Execution Guidelines and Phase Integration"),
    "Transition Period: Foundational Preconditioning": _entry(9, BOOK, "Foundational Preconditioning"),
    "Base Period: Elevating Fundamental Qualities": _entry(10, BOOK, "Elevating Fundamental Qualities"),
    "Build and Peak Periods: Specificity and Competition Readiness": _entry(
        12, BOOK_CLUB_PODCAST, "Specificity and Competition Readiness"
    ),
    "Recovery and Core Training Principles": _entry(2, BOOK, "Recovery and Core Training Principles"),
    "Weekly Volume Share of Aerobic Base Training and Intensity Distribution": _entry(
        2, BOOK, "Aerobic Base Volume Share and Intensity Distribution (80/20 & 90/10)"
    ),
    "Aerobic Threshold (AeT) vs. Anaerobic Threshold (AnT)": _entry(
        1, BOOK, "Aerobic Threshold (AeT) vs. Anaerobic Threshold (AnT)"
    ),
    "Aerobic Deficiency Syndrome (ADS)": _entry(1, BOOK, "Aerobic Deficiency Syndrome (ADS)"),
    "Training Volume, Terrain Specificity, and Session Structure": _entry(
        12, BOOK, "Training Volume, Terrain Specificity, and Session Structure"
    ),
    "Carbohydrate and Fluid Intake Guidelines": _entry(
        None, BOOK_CLUB_PODCAST, "Carbohydrate and Fluid Intake Guidelines"
    ),
    "Advanced Fueling Strategies": _entry(
        None, BOOK_CLUB_PODCAST, "Advanced Fueling Strategies (Gut Training & Osmolality)"
    ),
    "Tapering and Neuromuscular Readiness": _entry(None, BOOK_CLUB_PODCAST, "Tapering and Neuromuscular Readiness"),
    "Structuring the Final Week: Fueling and Nutrition": _entry(
        None, BOOK_CLUB_PODCAST, "Structuring the Final Week: Carb Loading and Low-Residue Protocol"
    ),
    "Hill Sprints, Hill Repeats, and Race-Specific Gradient Matching": _entry(
        7, BOOK_CLUB_PODCAST, "Neuromuscular Speed, Hill Sprints, and Gradient Matching"
    ),
    "Treadmill & Gym Machine Substitutions": _entry(None, BOOK_CLUB_PODCAST, "Treadmill and Gym Machine Substitutions"),
    "When Double Sessions Make Sense": _entry(None, BOOK_CLUB_PODCAST, "When Double Sessions Make Sense"),
    "Core Philosophy and Lower Body Strength": _entry(6, BOOK, "Core Philosophy and Lower Body Strength"),
    "Upper Body and Core Strength Exercises": _entry(6, BOOK, "Upper Body and Core Strength Exercises"),
    "Training Protocols and Periodization": _entry(8, BOOK, "Training Protocols and Periodization"),
    "Recovery Weeks and Active Recovery Modalities": _entry(2, BOOK, "Recovery Weeks and Active Recovery Modalities"),
    "Signs and Stages of Overtraining": _entry(3, BOOK, "Signs and Stages of Overtraining"),
    "Adjusting Training After Missed Sessions, Illness, or Injury": _entry(
        3, BOOK, "Adjusting Training After Missed Sessions, Illness, or Injury"
    ),
    "Race-Day Pacing Strategies": _entry(None, BOOK_CLUB_PODCAST, "Race-Day Pacing Strategies"),
    "Course-Specific Preparation": _entry(12, BOOK_CLUB_PODCAST, "Course-Specific Preparation and Gradient Matching"),
    "Walk-to-Run Progression for Complete Beginners": _entry(
        None, BOOK, "Walk-to-Run Progression for Complete Beginners"
    ),
    "Transitioning from Run/Walk Intervals to Continuous Running": _entry(
        None, BOOK, "Transitioning from Run/Walk Intervals to Continuous Running"
    ),
    "Connective-Tissue Adaptation and Injury Risk in New Runners": _entry(
        None, BOOK, "Connective-Tissue Adaptation and Injury Risk in New Runners"
    ),
    "Regulating Effort Without Pace or Heart-Rate Data": _entry(
        3, BOOK, "Regulating Effort Without Pace or Heart-Rate Data"
    ),
    "Weeks Containing Two or More Quality Sessions": _entry(
        None, BOOK_CLUB_PODCAST, "Weeks Containing Two or More Quality Sessions"
    ),
    "Periodization Above 100 km per Week": _entry(None, BOOK, "Periodization Above 100 km per Week"),
    "Double-Day Training: Warrant, Allocation and Spacing": _entry(
        None, BOOK_CLUB_PODCAST, "Double-Day Training: Warrant, Allocation and Spacing"
    ),
    "Readiness and Overreaching Markers in Highly Trained Athletes": _entry(
        3, BOOK, "Readiness and Overreaching Markers in Highly Trained Athletes"
    ),
    "Classifying an Athlete's Training Level": _entry(
        None, BOOK_CLUB_PODCAST, "Classifying an Athlete's Training Level"
    ),
    "Zone 2 Pace Ranges by Training Level": _entry(None, BOOK, "Zone 2 Pace Ranges by Training Level"),
    "Establishing Aerobic Threshold Without Lab Testing": _entry(
        3, BOOK, "Establishing Aerobic Threshold Without Lab Testing"
    ),
}


def _with_labels(meta_raw: dict[str, Any]) -> dict[str, Any]:
    meta = dict(meta_raw)
    ch_str = f"Chapter {meta['chapter_num']}: {meta['chapter_title']}" if meta["chapter_num"] else None
    meta["chapter"] = ch_str
    if meta["source"] == BOOK:
        meta["citation_label"] = f"{BOOK_TITLE} — {ch_str}" if ch_str else BOOK_TITLE
    elif ch_str:
        meta["citation_label"] = f"{BOOK_CLUB_TITLE} (see {BOOK_TITLE}, {ch_str})"
    else:
        meta["citation_label"] = BOOK_CLUB_TITLE
    return meta


def get_scheduler_chunk_metadata(title: str | None) -> dict[str, Any] | None:
    """Return source provenance for a scheduler philosophy chunk title."""
    if not title:
        return None
    # Exact match
    if title in SCHEDULER_CHUNK_PROVENANCE:
        return _with_labels(SCHEDULER_CHUNK_PROVENANCE[title])

    # Partial / case-insensitive match
    title_lower = title.strip().lower()
    for prov_title, meta_raw in SCHEDULER_CHUNK_PROVENANCE.items():
        if title_lower == prov_title.lower() or title_lower in prov_title.lower() or prov_title.lower() in title_lower:
            return _with_labels(meta_raw)

    return None
