"""The coaching rules block, assembled for one athlete tier.

Previously the plan prompt carried a single rules block written for a mountain
ultrarunner. Every athlete got it: the beginner who could jog two minutes was told to
keep an ME session 48 hours clear of her weekend long run, and the elite got the same
10% weekly progression cap as a novice. The three-sentence `start_running` exception
sat above ~6,000 characters that contradicted it, and nothing switched any of it off.

Rules are now assembled from the tier's profile, so a number that varies by tier is
written once and interpolated, rather than restated in prose that drifts.

PROVENANCE
    The performance rules below are the previously shipped text, preserved verbatim
    except where a hardcoded figure became a tier parameter. The beginner rules are
    NEW and are conservative general run/walk practice -- they are NOT drawn from the
    distilled Uphill Athlete knowledge base, which contains no beginner material at all
    (0 of 29 scheduler rows). They are marked here so they can be replaced with
    KB-grounded doctrine rather than silently mistaken for it.
"""

from services.athlete_tier import TierProfile


def _pct(fraction: float) -> str:
    """0.08 -> '8'. Progression caps read as percentages in the prompt."""
    return f"{fraction * 100:g}"


def _beginner_rules(profile: TierProfile, max_continuous_jog_min: int | None) -> str:
    """Walk-to-run rules for an athlete who cannot yet run continuously.

    The organising principle is that the limiter is tissue tolerance and habit, not
    fitness or willpower. Everything here follows from that: no intensity, generous
    rest, and progress measured by unbroken jogging time rather than distance -- the
    one number a new runner can feel and retell.
    """
    lo, hi = profile.weekday_minutes
    jog_line = (
        f"The athlete's current longest UNBROKEN jog is {max_continuous_jog_min} minutes."
        if max_continuous_jog_min
        else "The athlete's longest unbroken jog is not recorded yet; assume 1-2 minutes and start there."
    )
    return f"""
Rules:
YOU ARE WRITING FOR A NEW RUNNER. Ignore any instinct to make this look like a serious
training plan. The single measure of success is that the athlete finishes every session
feeling like she could have done more, and comes back next week.

1. Progress Metric — THE headline number: longest UNBROKEN jog, in minutes. {jog_line}
   Every week should move that number, or hold it deliberately. Name it in the workout
   descriptions so the athlete can see it moving ("last week 3 minutes, this week 4").
   Do NOT lead with distance: a new runner's pace is slow and variable, so distance
   flatters or punishes at random and measures the wrong thing.
2. Session Shape — run/walk intervals, NOT continuous running:
   - Every running session is: brisk-walk warm-up → N x (jog X min, walk Y min) → walk cool-down.
   - Set the jog interval from the athlete's current unbroken jog time. Do not exceed it
     early in a week; the repeats, not the single effort, build the volume.
   - The walk is a prescribed part of the session, never a failure. Say so explicitly.
   - Progress ONE variable at a time: either lengthen the jog interval, or add a repeat,
     or shorten the walk. NEVER two in the same week.
3. Intensity — there is none. Every session is conversational: the athlete must be able
   to speak a full sentence throughout. NO Zone 3, 4 or 5. NO tempo, threshold, interval,
   fartlek, hill sprint or Muscular Endurance sessions of any kind. If the athlete asks
   to go faster, give them more minutes at the same easy effort instead.
   The talk test is the ONLY effort cue that works here: a new runner has no reliable
   pace sense and their heart-rate zones are estimates, so do not lean on either.
4. Effort Cue and Zones: prescribe Zone 1-2 only. Frame the target as "you should be able
   to hold a conversation", with pace and heart rate as secondary information.
5. Volume Progression: weekly TIME increases by at most {_pct(profile.max_weekly_progression)}%.
   Hold a week flat, or repeat it, whenever the athlete reports difficulty, misses
   sessions, or reports any pain. Repeating a week is a normal, successful outcome for a
   new runner -- describe it that way, never as a setback.
6. Frequency and Recovery: 3 running days per week, NEVER on consecutive days unless the
   athlete has explicitly asked for more. New runners break down from doing too much too
   soon, and the rest day is where the adaptation happens. Prefer adding a rest day over
   adding a session.
7. Session Duration: {lo}-{hi} minutes INCLUDING warm-up and cool-down. A 20-minute
   session is a complete, correct session for this athlete -- do NOT stretch it toward
   any general-population weekday minimum.
8. Long Run: the longest session may take up to {_pct(profile.long_run_share_cap)}% of
   weekly time, and is still run/walk. It is "the longest one", not a different kind of
   session, and it carries no additional intensity.
9. Injury Guardrails: new runners' most common injuries come from load applied faster
   than bone and tendon adapt. In the Warning section name the specific early signals --
   shin pain, a sore spot on the top of the foot, knee pain that worsens during a run --
   and instruct the athlete to stop and take rest days rather than push through. Any
   mention of pain in the athlete's feedback: reduce volume and remove the affected
   movement entirely.
10. Fueling: sessions this short need water only. Do NOT prescribe gels, carbohydrate
    targets per hour, or electrolyte protocols -- they are irrelevant at this duration
    and make the plan intimidating.
11. Cross-training and Strength: bodyweight only, and framed as injury prevention rather
    than performance. Simple, low-rep, no jumping or plyometrics.
12. Tone: write to someone who may not think of themselves as a runner yet. Explain WHY
    a session is easy. Never imply the athlete is behind, and never compare them to a
    trained runner.
13. NEVER invent a physiological claim, exercise, or number. If unsure of an exact
    figure, give a sensible range instead of fabricating false precision.
14. Give the athlete profile and prior feedback below real weight — this plan MUST
    reflect their specific numbers, schedule, and history, not a generic template.
"""


def _performance_rules(profile: TierProfile) -> str:
    """Rules for athletes who run continuously. Previously the only rules block.

    Kept verbatim except that the progression cap, long-run share and weekday session
    band are now interpolated from the tier profile, and the ME/periodization sections
    are omitted for tiers that do not use them.
    """
    lo, hi = profile.weekday_minutes
    cap = _pct(profile.max_weekly_progression)
    long_share = _pct(profile.long_run_share_cap)

    me_periodization = (
        """4. Periodization Phases (Training for the Uphill Athlete):
   - Short Runway Override (<= 10 weeks total plan): Bypass general strength phases. Start a specific Muscular Endurance (ME) block in Week 1 or Week 2, concluding 10-14 days before race day.
   - Base Phase: Aerobic volume accumulation (Zone 1-2) + Maximum Strength (heavy compound bodyweight/gym lifts: squats, deadlifts, step-ups; 3-5 sets of 4-6 reps, 2-3 min rest between sets). For standard/long plans (>= 12 weeks), introduce high-repetition ME circuits in the Build phase.
   - Build Phase: Aerobic base expansion + Muscular Endurance (8-12 week ME block: gym circuits or uphill carries) + Zone 3/4 hill tempo repeats.
   - Peak Phase: Race-specific terrain simulation, high-vert weekend back-to-backs, weighted pack step-ups, and eccentric downhill repeats (quad conditioning).
   - Taper Phase: Reduce weekly volume by 40-60% while maintaining neuromuscular sharpness (stop heavy ME 10-14 days out).
   - Race Week: Minimal volume, rest days before race day, race execution, post-race recovery.
"""
        if profile.allows_me_blocks
        else """4. Periodization Phases:
   - Base Phase: Aerobic volume accumulation (Zone 1-2) plus simple bodyweight strength for injury resilience.
   - Build Phase: Continue aerobic base expansion and extend the long run. Introduce structured quality work only if the athlete is tolerating volume well.
   - Peak Phase: Race-specific terrain and the longest sessions of the plan.
   - Taper Phase: Reduce weekly volume by 40-60% while keeping frequency.
   - Race Week: Minimal volume, rest days before race day, race execution, post-race recovery.
   - This athlete is NOT yet at the tier where structured Muscular Endurance blocks apply — do not prescribe them.
"""
    )

    me_directives = (
        """12. Muscular Endurance (ME) Directives (Scott Johnston Framework):
   - Chassis vs. Engine Principle: Local muscular fatigue resistance of propelling fibers, not cardiac capacity, is the primary governor of sustainable race pace.
   - Terrain Routing:
     * Flat/Rolling Races (<25m vert/km or road): Prescribe Gym Leg Endurance Circuits, Short Steep Hill Strides (10-15% grade, 8-12s bounds), or Flat Tire Drags/Sled Pushes to adapt FTa frontier fibers and prevent late-race stride shortening, hip drop, and eccentric quad collapse.
     * Steep Mountain Races (>=25-35m vert/km or sustained single climbs >500m D+): Prescribe Outdoor Weighted Uphill Hikes (20-30%+ slope, 5-15% BW pack, Summit Water Dump protocol: dump water at top, descend unweighted) or Treadmill Incline Series (12-15% grade).
   - Treadmill Incline Hardware Realism: Standard commercial gym treadmills MAX OUT at 12-15% incline. For treadmill ME or hill repeats, ALWAYS prescribe 10-15% incline. NEVER prescribe >15% treadmill incline unless the athlete explicitly notes access to a specialized 25-40% Incline Trainer.
   - The 48-Hour Buffer: NEVER schedule an ME session within 48 hours of a weekend Long Run, Zone 3/4 interval run, or heavy gym workout.
   - Double Session Sequencing: On double-session days with ME, the high-power ME session is ALWAYS in the morning (fresh CNS); the easy Zone 1/2 aerobic run is in the afternoon.
   - Cardiac vs. Muscular Rule: Heart rate must remain in Zone 1-2 (conversational), while peripheral propelling muscles experience deep, continuous muscular burn.
   - Missed ME Session: If an athlete misses an ME session, drop progression back by 2 workouts to protect tendons and joints.
"""
        if profile.allows_me_blocks
        else """12. Strength: bodyweight strength for injury resilience only — squats, lunges, step-ups, calf raises, core. Structured Muscular Endurance blocks do NOT apply at this tier; do not prescribe circuits, weighted carries or incline ME series.
"""
    )

    intensity_rule = (
        f"2. 80/20 Low-Intensity Volume Polarization: At least 80-85% of total weekly running volume/time MUST be strictly in Zone 1 and Zone 2 (below AeT). High-intensity work (Zone 3/4/5, ME circuits) must NOT exceed 15-20% of weekly volume. PROGRESSION CEILING: Total weekly running volume MUST NOT increase by more than {cap}% week-over-week. Never produce abrupt spikes in weekly mileage.\n"
        if profile.allows_intensity
        else f"2. Aerobic Base Only: 100% of running volume is Zone 1-2, below AeT. This athlete is building an aerobic base and structural resilience — do NOT prescribe tempo, threshold or interval sessions yet. PROGRESSION CEILING: total weekly running volume MUST NOT increase by more than {cap}% week-over-week. Never produce abrupt spikes in weekly mileage.\n"
    )

    return f"""
Rules:
1. Block Scope & Schedule: Generate workouts for the specified block weeks only. Each week must have structured workouts (typically 4-6 workouts per week). ALWAYS honor the athlete's preferred training days and double-session days from their profile — place Rest workouts on non-preferred days, and produce two workout objects on each double-session day as described above.
{intensity_rule}3. Long Run Proportionality Cap: A single long run must NOT exceed {long_share}% of total weekly volume. For ultra distances where back-to-back weekend long runs (Saturday + Sunday) are scheduled, their combined total must NOT exceed 50% of the week's total volume to prevent excessive structural breakdown. WEEKDAY RUN DURATIONS: Weekday runs (Mon-Fri) are typically {lo}-{hi} minutes for this athlete — respect their daily work schedule, and never schedule an excessive 90-120+ minute run on a weekday unless explicitly requested.
{me_periodization}5. Deload Adaptation Cycles: Follow a 3:1 (or 2:1 for masters/fatigued runners) loading-to-recovery pattern. On recovery/deload weeks, reduce weekly volume by 20-30% to consolidate physiological adaptation and prevent overtraining.
6. Aerobic Deficiency Syndrome (ADS) Rule: If ADS is detected in the athlete profile, strictly enforce aerobic base building: NO Zone 4 or 5 intervals in Base/Build phases. Keep all aerobic runs strictly below AeT heart rate.
7. Make the plan highly customized. For example, scale long runs, map Sunday Muscular Endurance box steps/weighted step-ups based on the race elevation gain, or specify treadmill incline/speed settings for gym workouts.
8. NEVER invent a physiological claim, exercise, or number beyond what the Uphill Athlete training philosophy implies. If unsure of an exact figure, give a sensible range instead of fabricating false precision.
9. Give the athlete profile and prior feedback below real weight — this plan MUST reflect their specific numbers, schedule, and history, not a generic template.
10. Uphill Athlete & Trail Specificity: For mountain/trail races, incorporate progressive eccentric quad conditioning (eccentric box step-downs, downhill repeats, hill bounding) and back-to-back weekend long runs where appropriate for ultra distances (50K+). If the course profile notes high heat or altitude, integrate acclimation guidance.
11. Environmental & Routine Scheduling: If the athlete's notes indicate flat/urban living on weekdays with weekend trail travel, prescribe flat road/treadmill aerobic work or gym ME on weekdays, reserving high-vert trail long runs for Saturday/Sunday. Keep weekday runs accessible ({lo}-{hi} min).
{me_directives}"""


def build_rules_block(profile: TierProfile, max_continuous_jog_min: int | None = None) -> str:
    """The rules text for this tier, including the tier statement that precedes it.

    The tier statement is not decoration: without it the model infers the athlete's
    level from the race distance and quietly reverts to ultrarunner defaults.
    """
    header = (
        f"\nATHLETE TIER: {profile.label}\n"
        f"{profile.description}\n"
        f"Write for THIS athlete. Do not import assumptions from a different level of runner — "
        f"in particular, do not add intensity, volume or session types that the rules below omit.\n"
    )
    body = _beginner_rules(profile, max_continuous_jog_min) if profile.uses_walk_run else _performance_rules(profile)
    return header + body
