"""Which Uphill Athlete philosophy chunks ground a Scheduler generation.

Gen plan, next block and adapt week all ground the plan prompt on top-k chunks from
the scheduler KB. The retrieval query used to be one fixed string per terrain, so
every athlete on the same terrain got the same six chunks whatever their tier, phase
or situation: a beginner got the 14-week weighted ME protocol and the elite
double-session chunks (the query literally asked for "muscular endurance circuit
design" and "double sessions"), and an injured athlete adapting a week got nothing
about returning from missed sessions.

The query is now built from the generation's context, and the hits are filtered by
audience so a chunk the tier's rules forbid never reaches the prompt. Filtering runs
on the chunk title, so unknown titles (e.g. a re-swept KB) pass through unchanged.
"""

from services.athlete_tier import TierProfile

# Chunks that only make sense for some athletes. Titles not listed are for everyone.
#   me          -- structured Muscular Endurance; needs tier.allows_me_blocks
#   doubles     -- two-a-day doctrine; needs double-session days and a non-beginner
#   high_volume -- sub-elite/elite doctrine
#   chat_only   -- useful to Coach Uphill chat but not to plan generation: fueling
#                  (the plan prompt carries its own tiered fueling spec) and race-day
#                  execution
CHUNK_AUDIENCE: dict[str, str] = {
    "Difference Between Muscular Endurance and Conventional Strength Training": "me",
    "Gym-Based ME Workout Design": "me",
    "Progressive 14-Week Gym ME Protocol": "me",
    "Execution Guidelines and Phase Integration": "me",
    "Hill Sprints, Hill Repeats, and Race-Specific Gradient Matching": "me",
    "Treadmill & Gym Machine Substitutions": "me",
    "When Double Sessions Make Sense": "doubles",
    "Session Sequencing: Morning vs. Afternoon": "doubles",
    "Recovery Spacing & Spacing Protocols": "doubles",
    "Double-Day Training: Warrant, Allocation and Spacing": "doubles",
    "Weeks Containing Two or More Quality Sessions": "high_volume",
    "Periodization Above 100 km per Week": "high_volume",
    "Readiness and Overreaching Markers in Highly Trained Athletes": "high_volume",
    "Carbohydrate and Fluid Intake Guidelines": "chat_only",
    "Advanced Fueling Strategies": "chat_only",
    "Structuring the Final Week: Fueling and Nutrition": "chat_only",
    "Race-Day Pacing Strategies": "chat_only",
}

HIGH_VOLUME_TIERS = ("sub_elite", "elite")

# How many hits to request before filtering, so filtering does not starve the prompt.
RETRIEVAL_OVERFETCH = 14


def phase_hint(goal_type: str | None, is_event_goal: bool, total_weeks: int, first_week: int) -> str:
    """Rough training period for the weeks being generated.

    The model decides each workout's phase itself; this only steers retrieval, so a
    coarse split (race week is total_weeks - 1, the week before it is the taper) is
    enough.
    """
    if not is_event_goal:
        return goal_type or "base"
    weeks_to_race = (total_weeks - 1) - first_week
    if weeks_to_race <= 0:
        return "race_week"
    if weeks_to_race == 1:
        return "taper"
    if weeks_to_race <= 4:
        return "peak"
    if first_week > total_weeks // 2:
        return "build"
    return "base"


_PHASE_TERMS = {
    "base": "Base period: Zone 1-2 aerobic base volume, general strength, hill sprints for neuromuscular power",
    "build": "Specific period: event-specific workouts, Zone 3 then Zone 4 intensity, terrain and gradient matching",
    "peak": "Specific period: course-specific preparation, terrain and gradient matching, overreaching blocks",
    "taper": "Tapering and peaking: reducing volume, neuromuscular strides, race week",
    "race_week": "Race week and post-race recovery, active recovery modalities",
    "start_running": "new runner starting to run",
    "return": "returning to running after a break: re-entry at reduced volume, detraining of the aerobic system",
    "recovery": "post-race recovery: active recovery modalities, recovery weeks",
}


def build_query(
    profile: TierProfile,
    terrain: str,
    phase: str,
    *,
    adapting_week: bool,
    has_block_feedback: bool,
    has_double_days: bool,
) -> str:
    parts = [f"{terrain} training plan for a {profile.label.lower()}", _PHASE_TERMS.get(phase, _PHASE_TERMS["base"])]
    if profile.uses_walk_run:
        parts.append(
            "walk-to-run progression, connective-tissue adaptation in new runners, "
            "regulating effort without pace or heart-rate data"
        )
    else:
        parts.append("weekly volume progression, long run share, recovery weeks")
    if profile.allows_me_blocks and phase in ("base", "build", "peak"):
        parts.append("muscular endurance progression")
    if has_double_days and not profile.uses_walk_run:
        parts.append("double sessions spacing")
    if adapting_week:
        parts.append("adjusting training after missed sessions, illness, injury or fatigue; signs of overtraining")
    elif has_block_feedback:
        parts.append("adjusting the next block to the athlete's response, recovery and consolidation weeks")
    return "; ".join(parts)


def chunk_allowed(title: str, profile: TierProfile, has_double_days: bool) -> bool:
    audience = CHUNK_AUDIENCE.get(title, "all")
    if audience == "chat_only":
        return False
    if audience == "me":
        return profile.allows_me_blocks
    if audience == "doubles":
        return has_double_days and not profile.uses_walk_run
    if audience == "high_volume":
        return profile.key in HIGH_VOLUME_TIERS
    return True
