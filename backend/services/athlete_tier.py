"""Athlete tier: which kind of runner a plan is being written for.

The plan-generation prompt used to carry one rules block, written for a mountain
ultrarunner, and a three-sentence exception for `start_running`. Those three sentences
competed with ~6,000 characters of ME circuits, Peak-phase vert weekends and race-day
carb loading, and nothing switched any of it off -- so a beginner who could jog two
minutes was told to respect the 48-hour buffer before her weekend long run.

Special-casing beginners would only move that problem: the next athlete to be served
the wrong rules is the sub-elite reading a recreational runner's caps. So tier is a
dimension, not an exception, and the prompt assembles its rules from the tier's
profile.

WHERE THE NUMBERS COME FROM
    Mixed provenance, and worth knowing which is which.

    KB-GROUNDED: the beginner tier's session band (3 sessions per week of 20-30 min,
    building toward 30-60) and its no-intensity rule come from the distilled Uphill
    Athlete principles now in kb_seed/scheduler.json -- "Connective-Tissue Adaptation
    and Injury Risk in New Runners" and "Walk-to-Run Progression for Complete
    Beginners". An earlier revision assumed a mountain-athlete source would have
    nothing for new runners and shipped placeholders; that was wrong, and the beginner
    numbers here have been corrected against the real doctrine.

    STILL UNSOURCED: the weekly-volume BANDS that separate the five tiers, and the
    caps for novice/recreational/sub_elite/elite. These remain conventional coaching
    defaults. They are gathered here, in one table, precisely so a coach can correct
    them in one place rather than hunting through prompt prose.
"""

from dataclasses import dataclass

BEGINNER = "beginner"
NOVICE = "novice"
RECREATIONAL = "recreational"
SUB_ELITE = "sub_elite"
ELITE = "elite"

# Ordered easiest -> hardest. Order is load-bearing: it is how "at least this tier"
# comparisons are made, and how an unknown tier degrades to something safe.
TIER_ORDER = (BEGINNER, NOVICE, RECREATIONAL, SUB_ELITE, ELITE)

# The tier assumed when nothing better is known. Deliberately mid-range rather than
# the easiest tier: defaulting everyone to `beginner` would hand a walk-run plan to a
# trained runner who simply hasn't filled in their profile.
DEFAULT_TIER = RECREATIONAL


@dataclass(frozen=True)
class TierProfile:
    """Everything the prompt needs to know about a tier.

    Each field exists because the single-audience prompt got it wrong for someone:
    a beginner told her weekday runs must be 45-75 minutes, or an elite capped at the
    same 10% weekly progression as a novice.
    """

    key: str
    label: str
    # Human description injected into the prompt so the model knows who it is writing for.
    description: str
    # Weekly running volume band in km, used for derivation. Upper bound is exclusive;
    # None means unbounded.
    weekly_km_min: float
    weekly_km_max: float | None
    # Week-over-week volume progression cap, as a fraction (0.10 == 10%).
    # KB-grounded and deliberately the SAME across tiers: the doctrine limits weekly
    # increases to 7-10% for everyone. An earlier revision guessed that elites progress
    # more slowly week to week; they do not. What changes with training age is the
    # ANNUAL rate below.
    max_weekly_progression: float
    # Annual volume progression cap. This is the axis that actually separates a beginner
    # from a highly trained athlete: up to 25%/year for a beginner, 10%/year once trained.
    max_annual_progression: float
    # Share of weekly TIME that must sit in Zone 1-2 below AnT. 80% is the floor; highly
    # trained athletes run closer to 90/10.
    low_intensity_share: float
    # Ceiling on total weekly Zone 4 interval time, in minutes. None where intensity is
    # not prescribed at all. Beyond ~30-40 min even well-conditioned athletes hit severe
    # endocrine stress, so this is a hard cap rather than a target.
    zone4_weekly_cap_min: int | None
    # Typical weekday session length in minutes (low, high). A beginner's 20 minutes is
    # correct, not a session that failed to reach some floor.
    weekday_minutes: tuple[int, int]
    # Share of weekly volume a single long run may take.
    long_run_share_cap: float
    # Whether Zone 3+ work is permitted at all. Beginners get none: their limiter is
    # tissue tolerance and consistency, not the ability to run hard.
    allows_intensity: bool
    # Whether structured Muscular Endurance blocks apply.
    allows_me_blocks: bool
    # Whether running is continuous, or built from run/walk intervals.
    uses_walk_run: bool


TIER_PROFILES: dict[str, TierProfile] = {
    BEGINNER: TierProfile(
        key=BEGINNER,
        label="Beginner / new runner",
        description=(
            "A new runner who cannot yet run continuously for long. Sessions are built from "
            "run/walk intervals, on non-consecutive days with non-impact cross-training between "
            "them. The limiter is connective tissue, which gains strength at roughly a seventh "
            "the rate muscle gains fitness -- so this athlete will feel capable of more than "
            "their tendons can yet absorb. The goal is to finish every session feeling like "
            "more was possible."
        ),
        weekly_km_min=0.0,
        weekly_km_max=15.0,
        max_weekly_progression=0.10,
        max_annual_progression=0.25,
        low_intensity_share=1.00,
        zone4_weekly_cap_min=None,
        # KB-grounded: beginners start at 3 sessions per week of 20-30 minutes, and the
        # run/walk session builds toward 30-60 min as the ratio progresses. The upper
        # bound covers that progression; the rules text carries both figures explicitly.
        weekday_minutes=(20, 45),
        long_run_share_cap=0.40,
        allows_intensity=False,
        allows_me_blocks=False,
        uses_walk_run=True,
    ),
    NOVICE: TierProfile(
        key=NOVICE,
        label="Novice runner",
        description=(
            "Runs continuously but at low volume, and has little or no racing experience. "
            "Building the aerobic base and the weekly habit matters far more than any "
            "quality session."
        ),
        weekly_km_min=15.0,
        weekly_km_max=30.0,
        max_weekly_progression=0.10,
        max_annual_progression=0.20,
        low_intensity_share=1.00,
        zone4_weekly_cap_min=None,
        weekday_minutes=(25, 50),
        long_run_share_cap=0.35,
        allows_intensity=False,
        allows_me_blocks=False,
        uses_walk_run=False,
    ),
    RECREATIONAL: TierProfile(
        key=RECREATIONAL,
        label="Recreational / trained runner",
        description=(
            "A consistently training runner with race experience, balancing training against "
            "work and family. Can absorb structured quality work and a genuine long run."
        ),
        weekly_km_min=30.0,
        weekly_km_max=60.0,
        max_weekly_progression=0.10,
        max_annual_progression=0.15,
        low_intensity_share=0.85,
        zone4_weekly_cap_min=40,
        weekday_minutes=(45, 75),
        long_run_share_cap=0.33,
        allows_intensity=True,
        allows_me_blocks=True,
        uses_walk_run=False,
    ),
    SUB_ELITE: TierProfile(
        key=SUB_ELITE,
        label="Sub-elite runner",
        description=(
            "High training volume with a substantial racing history, competitive in their "
            "age group or locally. Tolerates two quality sessions a week and back-to-back "
            "long days, and recovers fast enough to progress on a shorter cycle."
        ),
        weekly_km_min=60.0,
        weekly_km_max=100.0,
        max_weekly_progression=0.10,
        max_annual_progression=0.10,
        low_intensity_share=0.90,
        zone4_weekly_cap_min=40,
        weekday_minutes=(60, 100),
        long_run_share_cap=0.30,
        allows_intensity=True,
        allows_me_blocks=True,
        uses_walk_run=False,
    ),
    ELITE: TierProfile(
        key=ELITE,
        label="Elite runner",
        description=(
            "Training at or near a professional volume, where running is structured around "
            "recovery rather than fitted around a job. Double days are routine. Progression "
            "is cautious in percentage terms precisely because the absolute volume is large."
        ),
        weekly_km_min=100.0,
        weekly_km_max=None,
        max_weekly_progression=0.10,
        max_annual_progression=0.10,
        low_intensity_share=0.90,
        zone4_weekly_cap_min=40,
        weekday_minutes=(60, 120),
        long_run_share_cap=0.28,
        allows_intensity=True,
        allows_me_blocks=True,
        uses_walk_run=False,
    ),
}

# Goals that mean the athlete is starting from no running base, regardless of any
# stale weekly-volume number left on their profile.
BEGINNER_GOAL_TYPES = ("start_running",)

# Below this many minutes of unbroken jogging the athlete is a beginner whatever their
# other numbers say -- someone who cannot run 10 minutes continuously cannot execute a
# continuous-running plan, and that is the plainest possible evidence of it.
CONTINUOUS_JOG_BEGINNER_CEILING_MIN = 10


def get_profile(tier: str | None) -> TierProfile:
    """The profile for a tier, falling back to the default rather than raising: a plan
    built on slightly wrong assumptions still beats no plan, and the caller has nothing
    better to substitute."""
    return TIER_PROFILES.get((tier or "").strip().lower(), TIER_PROFILES[DEFAULT_TIER])


def derive_tier(
    goal_type: str | None = None,
    current_weekly_km: float | None = None,
    max_continuous_jog_min: int | None = None,
    historical_max_distance_km: float | None = None,
) -> str:
    """Infer a tier from what is known about the athlete.

    Ordered by how much each signal can be trusted:

    1. The goal. Choosing "start running" is an explicit statement, and it beats a
       weekly-volume number that may just be an onboarding default (current_weekly_km
       defaults to 30.0, which would otherwise read as a recreational runner).
    2. Demonstrated continuous running. Someone who cannot jog 10 minutes unbroken is a
       beginner regardless of what else their profile claims.
    3. Weekly volume, the conventional axis.
    4. A proven long run, which can only raise the tier, never lower it -- one big day
       does not make someone elite, but it does rule out `beginner`.
    """
    if (goal_type or "").strip().lower() in BEGINNER_GOAL_TYPES:
        return BEGINNER

    if max_continuous_jog_min is not None and max_continuous_jog_min < CONTINUOUS_JOG_BEGINNER_CEILING_MIN:
        return BEGINNER

    if current_weekly_km is None or current_weekly_km <= 0:
        return DEFAULT_TIER

    tier = DEFAULT_TIER
    for key in TIER_ORDER:
        profile = TIER_PROFILES[key]
        if current_weekly_km >= profile.weekly_km_min and (
            profile.weekly_km_max is None or current_weekly_km < profile.weekly_km_max
        ):
            tier = key
            break

    # A proven long run can only promote. Someone whose weekly volume reads low but who
    # has completed a 30 km run is not a beginner -- more likely they are returning, or
    # their profile is stale.
    if historical_max_distance_km and historical_max_distance_km >= 25.0 and tier == BEGINNER:
        tier = NOVICE

    return tier


def resolve_tier(
    explicit_tier: str | None = None,
    goal_type: str | None = None,
    current_weekly_km: float | None = None,
    max_continuous_jog_min: int | None = None,
    historical_max_distance_km: float | None = None,
) -> str:
    """An explicit per-plan override when one is set, otherwise the derived tier.
    An unrecognised override is ignored rather than honoured, so a typo degrades to
    derivation instead of silently selecting the default profile."""
    if explicit_tier and explicit_tier.strip().lower() in TIER_PROFILES:
        return explicit_tier.strip().lower()
    return derive_tier(
        goal_type=goal_type,
        current_weekly_km=current_weekly_km,
        max_continuous_jog_min=max_continuous_jog_min,
        historical_max_distance_km=historical_max_distance_km,
    )
