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

import math
from dataclasses import dataclass, field
from typing import Any

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
    # Weekly running volume band in km. Upper bound is exclusive; None means unbounded.
    # Derivation now reads LOAD_ANCHORS (below), which must stay aligned with these
    # bands so load alone reproduces them; the prompt rules still read the bands.
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
    # Default Zone 2 bounds (slower, faster) in min/km, used ONLY when the athlete has no
    # zones of their own. KB-grounded, converted from the doctrine's min/mile figures.
    zone2_pace: tuple[str, str]
    # AeT-to-AnT spread this tier typically shows, as a fraction. Above 0.30 is Aerobic
    # Deficiency Syndrome. This is a stronger tier signal than weekly volume, because it
    # is measured rather than self-reported -- but only when the thresholds are real.
    aet_ant_gap_max: float


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
        zone2_pace=("9:19", "7:27"),
        aet_ant_gap_max=1.00,
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
        weekly_km_max=40.0,
        max_weekly_progression=0.10,
        max_annual_progression=0.20,
        low_intensity_share=1.00,
        zone4_weekly_cap_min=None,
        weekday_minutes=(25, 50),
        long_run_share_cap=0.35,
        allows_intensity=True,
        allows_me_blocks=False,
        uses_walk_run=False,
        zone2_pace=("7:27", "6:13"),
        aet_ant_gap_max=0.30,
    ),
    RECREATIONAL: TierProfile(
        key=RECREATIONAL,
        label="Recreational / trained runner",
        description=(
            "A consistently training runner with race experience, balancing training against "
            "work and family. Can absorb structured quality work and a genuine long run."
        ),
        weekly_km_min=40.0,
        weekly_km_max=80.0,
        max_weekly_progression=0.10,
        max_annual_progression=0.15,
        low_intensity_share=0.85,
        zone4_weekly_cap_min=40,
        weekday_minutes=(45, 75),
        long_run_share_cap=0.33,
        allows_intensity=True,
        allows_me_blocks=True,
        uses_walk_run=False,
        zone2_pace=("6:13", "4:58"),
        aet_ant_gap_max=0.30,
    ),
    SUB_ELITE: TierProfile(
        key=SUB_ELITE,
        label="Sub-elite runner",
        description=(
            "High training volume with a substantial racing history, competitive in their "
            "age group or locally. Tolerates two quality sessions a week and back-to-back "
            "long days, and recovers fast enough to progress on a shorter cycle."
        ),
        weekly_km_min=80.0,
        weekly_km_max=160.0,
        max_weekly_progression=0.10,
        max_annual_progression=0.10,
        low_intensity_share=0.90,
        zone4_weekly_cap_min=40,
        weekday_minutes=(60, 100),
        long_run_share_cap=0.30,
        allows_intensity=True,
        allows_me_blocks=True,
        uses_walk_run=False,
        zone2_pace=("4:21", "3:44"),
        aet_ant_gap_max=0.10,
    ),
    ELITE: TierProfile(
        key=ELITE,
        label="Elite runner",
        description=(
            "Training at or near a professional volume, where running is structured around "
            "recovery rather than fitted around a job. Double days are routine. Progression "
            "is cautious in percentage terms precisely because the absolute volume is large."
        ),
        weekly_km_min=160.0,
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
        zone2_pace=("3:06", "2:48"),
        aet_ant_gap_max=0.07,
    ),
}

# Goals that mean the athlete is starting from no running base, regardless of any
# stale weekly-volume number left on their profile.
BEGINNER_GOAL_TYPES = ("start_running",)

# Below this many minutes of unbroken jogging the athlete is a beginner whatever their
# other numbers say -- someone who cannot run 10 minutes continuously cannot execute a
# continuous-running plan, and that is the plainest possible evidence of it.
CONTINUOUS_JOG_BEGINNER_CEILING_MIN = 10

# --- Composite tier --------------------------------------------------------------
# The tier is a weighted mean of four dimensions, each mapped to a continuous level on
# the TIER_ORDER scale (0 beginner .. 4 elite). ALL ANCHORS AND WEIGHTS ARE CONVENTIONAL
# DEFAULTS, UNSOURCED, gathered here so a coach can correct them in one place.
# Spec: docs/superpowers/specs/2026-10-02-fitness-snapshot-design.md ("Tier rule").

WEIGHTS = {"load": 0.45, "performance": 0.30, "experience": 0.15, "physiology": 0.10}
MAX_LEVEL = 4.99
HYSTERESIS_LEVEL = 0.1
VERT_M_PER_EFFORT_KM = 100.0
FEMALE_PACE_FACTOR = 1.12
FEMALE_VO2_FACTOR = 0.9
# Threshold provenance that makes the AeT/AnT pair real evidence. "estimated" and
# "unknown" (the default for every existing athlete) never count.
MEASURED_THRESHOLD_SOURCES = ("lab", "field")

# Matches the old volume bands exactly, so load alone reproduces the old tiers.
LOAD_ANCHORS = [(0.0, 0.0), (15.0, 1.0), (40.0, 2.0), (80.0, 3.0), (160.0, 4.0), (320.0, 5.0)]
MARATHON_ANCHORS = [(25200.0, 0.0), (19800.0, 1.0), (15300.0, 2.0), (11400.0, 3.0), (9600.0, 4.0), (7800.0, 5.0)]
UTMB_ANCHORS = [(250.0, 1.0), (400.0, 2.0), (550.0, 3.0), (700.0, 4.0), (850.0, 5.0)]
VO2_ANCHORS = [(38.0, 1.0), (45.0, 2.0), (55.0, 3.0), (65.0, 4.0), (75.0, 5.0)]
THRESHOLD_PACE_ANCHORS = [(360.0, 1.0), (300.0, 2.0), (255.0, 3.0), (220.0, 4.0), (190.0, 5.0)]
EXPERIENCE_ANCHORS = [(0.0, 0.0), (10.0, 1.0), (21.0, 2.0), (42.0, 3.0), (80.0, 4.0), (160.0, 5.0)]
GAP_ANCHORS = [(0.50, 0.0), (0.35, 1.0), (0.30, 2.0), (0.10, 3.0), (0.07, 4.0), (0.04, 5.0)]
ANT_MAX_ANCHORS = [(0.80, 2.0), (0.87, 3.0), (0.91, 4.0), (0.94, 5.0)]


def effort_km(weekly_km: float | None, weekly_vert_m: float | None) -> float | None:
    """A kilometre plus 100 m of climbing counts as two."""
    if weekly_km is None:
        return None
    return round(weekly_km + (weekly_vert_m or 0.0) / VERT_M_PER_EFFORT_KM, 1)


def level_from(value: float | None, anchors: list[tuple[float, float]]) -> float | None:
    """Piecewise-linear level for `value`; works for rising (km) and falling (time,
    gap) anchors. Clamped to the end anchors and to [0, MAX_LEVEL]."""
    if value is None:
        return None
    pts = sorted(anchors)
    if value <= pts[0][0]:
        level = pts[0][1]
    elif value >= pts[-1][0]:
        level = pts[-1][1]
    else:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:], strict=False):
            if x0 <= value <= x1:
                level = y0 + (y1 - y0) * (value - x0) / (x1 - x0)
                break
    return round(min(max(level, 0.0), MAX_LEVEL), 3)


def _scaled(anchors: list[tuple[float, float]], factor: float) -> list[tuple[float, float]]:
    return [(x * factor, y) for x, y in anchors]


def performance_level(
    marathon_sec: float | None,
    utmb_index: float | None,
    vo2max: float | None,
    threshold_pace_sec: float | None,
    gender: str | None,
) -> tuple[float, str] | None:
    """Fallback chain. Race-derived signals first (best of the two); VO2max and threshold
    pace only when there is none, because COROS derives its predictor from them and
    counting both would weight one measurement twice."""
    female = (gender or "").lower() == "female"
    race = [
        (level_from(marathon_sec, _scaled(MARATHON_ANCHORS, FEMALE_PACE_FACTOR if female else 1.0)), "marathon"),
        (level_from(utmb_index, UTMB_ANCHORS), "utmb_index"),
    ]
    race = [(lv, src) for lv, src in race if lv is not None]
    if race:
        return max(race)
    if vo2max:
        return level_from(vo2max, _scaled(VO2_ANCHORS, FEMALE_VO2_FACTOR if female else 1.0)), "vo2max"
    if threshold_pace_sec:
        anchors = _scaled(THRESHOLD_PACE_ANCHORS, FEMALE_PACE_FACTOR if female else 1.0)
        return level_from(threshold_pace_sec, anchors), "threshold_pace"
    return None


def _tier_at(level: float) -> str:
    return TIER_ORDER[min(int(math.floor(level)), len(TIER_ORDER) - 1)]


@dataclass
class TierDecision:
    tier: str
    score: float | None = None
    levels: dict[str, float | None] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)


def get_profile(tier: str | None) -> TierProfile:
    """The profile for a tier, falling back to the default rather than raising: a plan
    built on slightly wrong assumptions still beats no plan, and the caller has nothing
    better to substitute."""
    return TIER_PROFILES.get((tier or "").strip().lower(), TIER_PROFILES[DEFAULT_TIER])


def aet_ant_gap(aet_hr: float | None, ant_hr: float | None) -> float | None:
    """Fractional spread between the aerobic and anaerobic thresholds, or None when the
    inputs are unusable. The doctrine reads this as the sharpest marker of training
    level: above 30% is Aerobic Deficiency Syndrome, 10-30% recreational, at or under
    10% competitive, 5-7% elite.

    CALLERS MUST PASS MEASURED THRESHOLDS ONLY. Elsewhere in this codebase aet_hr and
    ant_hr are derived from fixed 65%/85%-of-reserve ratios when absent, which produces
    the same ~17% spread for every athlete. Feeding those derived values in here would
    exceed both the sub-elite and elite limits for everyone and silently cap the whole
    user base at recreational. Pass the raw stored fields, and let None mean unknown."""
    if not aet_hr or not ant_hr or ant_hr <= 0 or aet_hr <= 0 or aet_hr >= ant_hr:
        return None
    return (ant_hr - aet_hr) / ant_hr


def explain_tier(
    *,
    goal_type: str | None = None,
    current_weekly_km: float | None = None,
    weekly_vert_m: float | None = None,
    max_continuous_jog_min: int | None = None,
    historical_max_distance_km: float | None = None,
    aet_hr: float | None = None,
    ant_hr: float | None = None,
    max_hr: float | None = None,
    threshold_source: str | None = None,
    marathon_prediction_sec: float | None = None,
    utmb_index: float | None = None,
    vo2max: float | None = None,
    threshold_pace_sec: float | None = None,
    gender: str | None = None,
    previous_tier: str | None = None,
) -> TierDecision:
    """Infer a tier, with per-dimension levels and reasons, from what is known.

    1. Beginner rules first. Choosing "start running" is an explicit statement that beats
       a weekly-volume number that may just be an onboarding default, and someone who
       cannot jog 10 minutes unbroken is a beginner whatever else their profile claims.
    2. Otherwise a weighted mean of four levels: load (effort-km), performance (race
       time, UTMB index, else VO2max, else threshold pace), physiology (AeT/AnT, ONLY
       when measured -- stored values of unknown provenance sit next to the DB defaults
       and once demoted a 130 km/week athlete to recreational) and experience (longest
       run, lift-only).
    3. floor(score), clamped to within one tier of what load alone gives: a fast runner
       on low volume cannot get elite caps, and a measured wide gap cannot drop a
       high-volume runner two tiers.
    4. Hysteresis on re-plans: within HYSTERESIS_LEVEL of the boundary with
       previous_tier, keep it, so a plan does not flip tiers block to block on noise.
    """
    if (goal_type or "").strip().lower() in BEGINNER_GOAL_TYPES:
        return TierDecision(BEGINNER, reasons=["start-running goal"])
    if max_continuous_jog_min is not None and max_continuous_jog_min < CONTINUOUS_JOG_BEGINNER_CEILING_MIN:
        return TierDecision(BEGINNER, reasons=[f"cannot jog {CONTINUOUS_JOG_BEGINNER_CEILING_MIN} min continuously"])

    reasons: list[str] = []
    levels: dict[str, float | None] = {}

    load = effort_km(current_weekly_km, weekly_vert_m)
    levels["load"] = level_from(load, LOAD_ANCHORS) if load and load > 0 else None
    if levels["load"] is not None:
        reasons.append(f"load {levels['load']:.1f} ({load:.0f} effort-km)")

    perf = performance_level(marathon_prediction_sec, utmb_index, vo2max, threshold_pace_sec, gender)
    levels["performance"] = perf[0] if perf else None
    if perf:
        reasons.append(f"performance {perf[0]:.1f} ({perf[1]})")

    gap = aet_ant_gap(aet_hr, ant_hr)
    measured = (threshold_source or "").lower() in MEASURED_THRESHOLD_SOURCES
    phys = []
    if measured and gap is not None:
        phys.append(level_from(gap, GAP_ANCHORS))
        if max_hr and ant_hr and ant_hr < max_hr:
            phys.append(level_from(ant_hr / max_hr, ANT_MAX_ANCHORS))
    levels["physiology"] = round(sum(phys) / len(phys), 3) if phys else None
    if levels["physiology"] is not None:
        reasons.append(f"physiology {levels['physiology']:.1f} (measured, {threshold_source})")
    elif gap is not None:
        reasons.append(f"physiology not used: AeT/AnT gap {gap:.0%}, source {threshold_source or 'unknown'}")

    def _mean(keys: list[str]) -> float | None:
        present = [(levels[k], WEIGHTS[k]) for k in keys if levels.get(k) is not None]
        if not present:
            return None
        return sum(v * w for v, w in present) / sum(w for _, w in present)

    base_keys = ["load", "performance", "physiology"]
    score = _mean(base_keys)
    # Experience lifts only: a short or missing long run in our data (30-day backfill,
    # no imported races) is not evidence of inexperience.
    exp = level_from(historical_max_distance_km, EXPERIENCE_ANCHORS) if historical_max_distance_km else None
    levels["experience"] = exp
    if exp is not None and (score is None or exp > score):
        score = _mean(base_keys + ["experience"])
        reasons.append(f"experience {exp:.1f} (longest {historical_max_distance_km:.0f} km)")
    elif exp is not None:
        reasons.append(f"experience {exp:.1f} not above the other dimensions, unused")

    if score is None:
        return TierDecision(DEFAULT_TIER, None, levels, ["no usable signal, default tier"])

    tier = _tier_at(score)
    load_tier = _tier_at(levels["load"]) if levels["load"] is not None else DEFAULT_TIER
    lo = max(TIER_ORDER.index(load_tier) - 1, 0)
    hi = min(TIER_ORDER.index(load_tier) + 1, len(TIER_ORDER) - 1)
    clamped = TIER_ORDER[min(max(TIER_ORDER.index(tier), lo), hi)]
    if clamped != tier:
        reasons.append(f"kept within one tier of load ({load_tier})")
        tier = clamped

    if previous_tier in TIER_PROFILES and previous_tier != tier:
        a, b = TIER_ORDER.index(tier), TIER_ORDER.index(previous_tier)
        if abs(a - b) == 1 and abs(score - max(a, b)) <= HYSTERESIS_LEVEL:
            reasons.append(f"within {HYSTERESIS_LEVEL} of the boundary, kept previous tier {previous_tier}")
            tier = previous_tier

    reasons.append(f"score {score:.2f} -> {tier}")
    return TierDecision(tier, round(score, 3), levels, reasons)


def derive_tier(**kwargs: Any) -> str:
    """Tier only; see explain_tier."""
    return explain_tier(**kwargs).tier


def resolve_tier_explained(explicit_tier: str | None = None, **kwargs: Any) -> TierDecision:
    """An explicit per-plan override when one is set, otherwise the composite.
    An unrecognised override is ignored rather than honoured, so a typo degrades to
    derivation instead of silently selecting the default profile."""
    if explicit_tier and explicit_tier.strip().lower() in TIER_PROFILES:
        return TierDecision(explicit_tier.strip().lower(), reasons=["explicit plan override"])
    return explain_tier(**kwargs)


def resolve_tier(explicit_tier: str | None = None, **kwargs: Any) -> str:
    return resolve_tier_explained(explicit_tier, **kwargs).tier
