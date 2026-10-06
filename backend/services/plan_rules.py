"""The coaching rules block, assembled for one athlete tier.

Previously the plan prompt carried a single rules block written for a mountain
ultrarunner. Every athlete got it: the beginner who could jog two minutes was told to
keep an ME session 48 hours clear of her weekend long run, and the elite got the same
10% weekly progression cap as a novice. The three-sentence `start_running` exception
sat above ~6,000 characters that contradicted it, and nothing switched any of it off.

Rules are now assembled from the tier's profile, so a number that varies by tier is
written once and interpolated, rather than restated in prose that drifts.

PROVENANCE
    The performance rules are the previously shipped text, preserved verbatim except
    where a hardcoded figure became a tier parameter.

    The beginner rules ARE now KB-grounded. An earlier revision of this module warned
    that they were unsourced general practice, on the assumption that a mountain-athlete
    source would carry nothing for new runners. That assumption was wrong: the notebook
    covers walk-to-run progression, the transition to continuous running, connective-
    tissue adaptation, and effort regulation without device data. Those four principles
    are now rows in kb_seed/scheduler.json, and the numbers below are taken from them --
    the 1:1 starting ratio, the 10 min run / 3 min walk transition point, the sub-AeT
    heart-rate readiness criterion, the one-seventh connective-tissue adaptation rate,
    and the A-F session grading threshold.

    Several of the placeholders that revision shipped were simply wrong against the real
    doctrine and have been corrected: progression advances the RUN duration specifically
    rather than any one of three variables, and rest days call for non-impact
    cross-training rather than nothing at all.
"""

from services.athlete_tier import TierProfile


def _pct(fraction: float) -> str:
    """0.08 -> '8'. Progression caps read as percentages in the prompt."""
    return f"{fraction * 100:g}"


def _beginner_rules(profile: TierProfile, max_continuous_jog_min: int | None) -> str:
    """Walk-to-run rules for an athlete who cannot yet run continuously.

    Grounded in four kb_seed/scheduler.json principles: "Walk-to-Run Progression for
    Complete Beginners", "Transitioning from Run/Walk Intervals to Continuous Running",
    "Connective-Tissue Adaptation and Injury Risk in New Runners", and "Regulating
    Effort Without Pace or Heart-Rate Data".

    The organising principle is the connective-tissue one: tendons and fascia gain
    strength at roughly a seventh of the rate muscle gains fitness, so a new runner
    feels capable of far more than their tissues can absorb. Everything else follows --
    no intensity, non-consecutive running days, and progress measured in unbroken
    jogging minutes rather than distance.
    """
    lo, hi = profile.weekday_minutes
    jog_line = (
        f"The athlete's current longest UNBROKEN jog is {max_continuous_jog_min} minutes."
        if max_continuous_jog_min
        else "The athlete's longest unbroken jog is not recorded yet; start from a 1 min jog / 1 min walk ratio."
    )
    return f"""
Rules:
YOU ARE WRITING FOR A NEW RUNNER. Ignore any instinct to make this look like a serious
training plan. The limiter is connective-tissue tolerance, not fitness or willpower:
tendons, ligaments and fascia are poorly vascularized and gain strength at roughly ONE
SEVENTH the rate muscle gains fitness, so this athlete will feel capable of more than
their tissues can yet absorb. Every rule below follows from that.

1. Progress Metric — THE headline number: longest UNBROKEN jog, in minutes. {jog_line}
   Every week should move that number, or hold it deliberately. Name it in the workout
   descriptions so the athlete can see it moving ("last week 3 minutes, this week 4").
   Do NOT lead with distance: a new runner's pace is slow and variable, so distance
   flatters or punishes at random and measures the wrong thing.
2. Session Shape — run/walk intervals, NOT continuous running:
   - Every running session is: brisk-walk warm-up → N x (jog X min, walk Y min) → walk cool-down.
   - Standard starting ratio is 1 min jog / 1 min walk, or 2-3 min jog / 3-4 min walk.
   - Repeat the intervals to fill the session. Total session time starts at {lo}-{hi} min
     and builds toward 30-60 min as the athlete adapts.
   - The walk is a PRESCRIBED part of the session, never a failure. Say so explicitly.
3. Progression — advance the JOG duration, holding the walk steady or shortening it
   slightly. Never lengthen the jog and cut the walk in the same week. The ladder runs
   1 min jog / 1 min walk → 2 min jog / 1 min walk → and onward toward 10 min jog /
   3 min walk.
4. Readiness to Progress — subjective comfort at the current ratio, OR heart-rate
   stability. The concrete test: if the athlete can complete a jog segment (say 5 min)
   keeping heart rate strictly BELOW their Aerobic Threshold, and it settles during the
   walk break, they are ready to lengthen the jog. A heart rate that will not settle
   within the walk break means the current ratio is still correct — hold it.
5. Transition to Continuous Running — only once 10 min jog / 3 min walk is comfortable,
   or heart rate stays below AeT through the longer jog blocks. Then do NOT jump to
   uninterrupted running: shift to longer structured blocks such as 4 x 6 min jog with
   3 min walk recovery, extend from there, and drop the walk break only when it is no
   longer needed rather than on a schedule.
6. Intensity — there is none. NO Zone 3, 4 or 5. NO tempo, threshold, interval, fartlek,
   hill sprint or Muscular Endurance sessions of any kind. If the athlete asks to go
   faster, give them more minutes at the same easy effort instead.
7. Effort Cues — this athlete has no reliable pace sense and their heart-rate zones are
   estimates, so prescribe by feel and give the cue explicitly in every session:
   - Zone 2 / Aerobic Threshold: can speak smoothly in medium-length COMPLETE sentences
     without gasping; can hold strict NOSE breathing for several minutes at a time.
   - Zone 1 / recovery: "stumblingly slow" — should feel BETTER a few hours after the
     session than before it.
   Pace and heart rate are secondary information, never the instruction.
8. Volume Progression: weekly TIME increases by at most {_pct(profile.max_weekly_progression)}%.
   Hold a week flat, or repeat it, whenever the athlete reports difficulty, misses
   sessions, or reports any pain. Repeating a week is a normal, successful outcome for a
   new runner — describe it that way, never as a setback.
9. Frequency and Recovery: 3 running sessions per week. NEVER run on consecutive days,
   and never every day. On alternate days prescribe NON-IMPACT aerobic work — cycling,
   elliptical, stairmaster, steep treadmill hiking, or swimming — which builds aerobic
   volume without the joint pounding the tissues cannot yet absorb. Prefer adding a
   non-impact day over adding a run.
10. Session Duration: {lo}-{hi} minutes INCLUDING warm-up and cool-down. A 20-minute
    session is a complete, correct session for this athlete — do NOT stretch it toward
    any general-population weekday minimum.
11. Long Run: the longest session may take up to {_pct(profile.long_run_share_cap)}% of
    weekly time, and is still run/walk. It is "the longest one", not a different kind of
    session, and it carries no additional intensity.
12. Injury Guardrails — in the Warning section, name the specific early signals that
    mean back off, and instruct the athlete to take rest days rather than push through:
    - heavy, "dead" legs with no bounce or spring;
    - morning resting heart rate up 10-15% (roughly 10-15 bpm) over baseline;
    - loss of motivation, persistent grumpiness, waking with no desire to train;
    - morning stiffness — hobbling out of bed, or sharp joint twinges.
    Also tell the athlete to grade each session A-F: more than two "C" grades in a row,
    a "C" and a "D" in one week, or more than three "C"s in a week means an immediate
    easy day or total rest. Any mention of pain in their feedback: reduce volume and
    remove the affected movement entirely.
13. Fueling: sessions this short need water only. Do NOT prescribe gels, carbohydrate
    targets per hour, or electrolyte protocols — they are irrelevant at this duration
    and make the plan intimidating.
14. Cross-training and Strength: bodyweight only, framed as injury prevention rather
    than performance. Simple, low-rep, no jumping or plyometrics.
15. Tone: write to someone who may not think of themselves as a runner yet. Explain WHY
    a session is easy. Never imply the athlete is behind, and never compare them to a
    trained runner.
16. NEVER invent a physiological claim, exercise, or number. If unsure of an exact
    figure, give a sensible range instead of fabricating false precision.
17. Give the athlete profile and prior feedback below real weight — this plan MUST
    reflect their specific numbers, schedule, and history, not a generic template.
"""


def _performance_rules(profile: TierProfile, treadmill_max_incline: int = 15) -> str:
    """Rules for athletes who run continuously. Previously the only rules block.

    Kept verbatim except that the progression cap, long-run share and weekday session
    band are now interpolated from the tier profile, and the ME/periodization sections
    are omitted for tiers that do not use them.
    """
    lo, hi = profile.weekday_minutes
    cap = _pct(profile.max_weekly_progression)
    long_share = _pct(profile.long_run_share_cap)
    low_share = _pct(profile.low_intensity_share)
    high_share = _pct(1.0 - profile.low_intensity_share)
    annual = _pct(profile.max_annual_progression)

    me_periodization = (
        """4. Periodization Phases (Training for the Uphill Athlete):
   - Short Runway Override (<= 10 weeks total plan): Skip extended base building and go straight to event-specific work. Start the Muscular Endurance (ME) block in Week 1 or Week 2, concluding 10-14 days before race day.
   - Base Phase: Aerobic volume accumulation (Zone 1-2) + general strength (single-leg stability, hips, core) + weekly Hill Sprints and Strides for neuromuscular power (rule 14) + the Muscular Endurance (ME) block. For a MOUNTAIN RUNNER the ME block starts in the EARLY Base phase, as volume begins to build — 8-14 weeks, up to 16 when there is time, and at least 8 sessions to secure the benefit. Once a week when the rest of the training load is high; twice a week when it is otherwise low. ME is layered ON TOP of the Zone 1-2 volume, never in place of it. Heavy maximal-strength lifting first is the mountaineer/alpinist sequence, not the runner's: do NOT prescribe heavy low-rep max-strength blocks (e.g. 3-5 x 4-6) to this athlete.
   - Build (Specific) Phase: After the ME block, the final ~8 weeks before the taper shift to traditional UPHILL and ROLLING intervals (Zone 3 sub-threshold first, Zone 4 layered in later) on top of continued aerobic volume. Doing ME first makes these intervals more effective. ME is no longer the focus; heavy slow barbell lifting is removed.
   - Peak Phase: Race-specific terrain simulation and eccentric downhill repeats (quad conditioning). Back-to-back long days are an overreaching tool, not a weekly routine: at most 2-3 two-day blocks in the whole Specific period, each followed by several easy recovery days.
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
        f"""12. Muscular Endurance (ME) Directives (Scott Johnston Framework):
   - Chassis vs. Engine Principle: Local muscular fatigue resistance of propelling fibers, not cardiac capacity, is the primary governor of sustainable race pace.
   - Terrain Routing:
     * Flat/Rolling Races (<25m vert/km or road): Prescribe the Gym ME progression (straight sets, see the ME format above) or Flat Tire Drags/Sled Pushes to adapt FTa frontier fibers and prevent late-race stride shortening, hip drop, and eccentric quad collapse. Hill Sprints/strides are neuromuscular POWER work, not ME — never count them as the week's ME session.
     * Steep Mountain Races (>=25-35m vert/km or sustained single climbs >500m D+): Prescribe Outdoor Weighted Uphill Carries — water jugs in a backpack (5-15% BW) on a 30%+ grade (ordinary trails rarely exceed 10-12%). Summit Water Dump protocol: dump the water at the top and descend unweighted by default; stronger athletes may carry the weight back down for extra benefit. No suitable hill: fire stairs in a tall building (even six stories works), a Stairmaster, or a Treadmill Incline Series. Last resort: standing on a bike in a very high gear.
   - Dose: total weighted climbing time 30 minutes the first time, building to no more than 60 minutes. On short hills or stairs run it as laps of at least 5 minutes each.
   - Treadmill Incline Hardware Realism: ME on a treadmill is done at 25% grade, which needs an incline trainer. This athlete's treadmill tops out at {treadmill_max_incline}%: below 25%, set its maximum and add a weighted vest/pack (5-15% BW) so local leg burn, not breathing, is the limiter, or use stair laps or weighted box step-ups instead. NEVER prescribe a treadmill incline above {treadmill_max_incline}%.
   - The 48-Hour Buffer: NEVER schedule an ME session within 48 hours of a weekend Long Run, Zone 3/4 interval run, or heavy gym workout.
   - Double Session Sequencing: On double-session days with ME, the high-power ME session is ALWAYS in the morning (fresh CNS); the easy Zone 1/2 aerobic run is in the afternoon.
   - Load, Not Heart Rate: Disregard heart rate in ME sessions. The load must be heavy enough that local leg fatigue, not breathing, limits the athlete, with a distinct low-grade burn in the propelling muscles for the whole climb or set. Done correctly, heart rate stays below the athlete's unweighted AnT heart rate.
   - Recovery Over Volume: ME works quickly. If performance stops improving week to week, the athlete needs MORE RECOVERY, not more ME. Never replace easy Zone 1-2 or recovery volume with ME sessions: without the aerobic volume, gains of 10-20% in a few workouts are followed by a plateau and then a decline.
   - Missed ME Session: If an athlete misses an ME session, drop progression back by 2 workouts to protect tendons and joints.
"""
        if profile.allows_me_blocks
        else """12. Strength: bodyweight strength for injury resilience only — squats, lunges, step-ups, calf raises, core. Structured Muscular Endurance blocks do NOT apply at this tier; do not prescribe circuits, weighted carries or incline ME series.
"""
    )

    z4_cap = (
        f" ZONE 4 HARD CAP: total Zone 4 interval time must NOT exceed {profile.zone4_weekly_cap_min} minutes in a "
        f"single week — beyond that even well-conditioned athletes hit severe endocrine stress (elevated cortisol) "
        f"and risk overtraining. Controlled mid-Zone 3 held below AnT is different: a high-level runner tolerates 2+ "
        f"hours per week because global fatigue stays low."
        if profile.zone4_weekly_cap_min
        else ""
    )
    intensity_rule = (
        f"2. Intensity Distribution (measured by TIME IN ZONE, not by session count): at least {low_share}% of total "
        f"weekly volume MUST be in Zone 1-2 (at or below AeT), and high-intensity work no more than {high_share}%.{z4_cap} "
        f"PROGRESSION CEILING: weekly volume (distance, vertical or duration) MUST NOT increase by more than {cap}% "
        f"week-over-week, and this athlete's annual volume should not rise more than {annual}% per year. Never "
        f"produce abrupt spikes.\n"
        if profile.allows_intensity
        else f"2. Aerobic Base Only: 100% of running volume is Zone 1-2, below AeT. This athlete is building an "
        f"aerobic base and structural resilience — do NOT prescribe tempo, threshold or interval sessions yet. "
        f"PROGRESSION CEILING: weekly volume MUST NOT increase by more than {cap}% week-over-week, and annual volume "
        f"by no more than {annual}%. Never produce abrupt spikes.\n"
    )

    # Zone 3 session dose by tier (Evoke Endurance, "Training Fast Twitch and Slow Twitch
    # Endurance Athletes"): world-class ~60 min in 15-20 min reps, well-trained amateur
    # 30-45 min in 10-15 min reps, beginner/older/less-trained 15-30 min in 6-10 min reps.
    z3_dose = {
        "novice": "15-30 min of total work in 6-10 min reps",
        "recreational": "30-45 min of total work in 10-15 min reps",
        "sub_elite": "30-60 min of total work in 10-20 min reps",
        "elite": "up to 60 min of total work, typically 15-20 min reps",
    }.get(profile.key, "15-30 min of total work in 6-10 min reps")
    quality_rules = (
        f"""14. Speed and Quality Session Design (Evoke Endurance):
   - Priorities for multi-hour events, in order: (1) speed at the Aerobic Threshold — the best predictor of ultra performance, raised mainly by a lot of Zone 2 (Zone 1 for athletes whose AeT pace is very fast); (2) fatigue resistance of the main propelling muscles (ME, then controlled Zone 3).
   - Strides and Hill Sprints, year-round from the first block. They are neuromuscular power work: heart rate is irrelevant and they cost almost no fatigue. Strides: 4-8 x under 20 s inside or right after an easy Zone 1-2 run (often in its last 10-20 min) — take 5-10 s to ease up to a 'fun fast' pace with long-distance form and longer strides (no overstriding, not a full sprint), 1-2 min easy between. Hill Sprints: 8-12 s near-maximal on a 20%+ hill or steep stairs taken two at a time, 2-3+ min full standing/walking rest, starting with 6-8 reps; mark the high point of the first reps, double the rest once when the mark is missed, and stop when it is missed again. Together they stay under ~1% of training time.
   - Zone 3 (threshold) sessions: mid-Zone 3, a 'controlled, fun' hard with another gear in reserve — never pushed over AnT. Dose for this athlete: {z3_dose}, with 2-4 min rest between reps. If the athlete cannot repeat the pace in the next rep the session is over: it was too hard, or they need more ME first.
   - Zone 4 (VO2max) intervals: reps of 30 s to 4-5 min (no long 8-min reps); an elite tops out at 15-20 min of total work per session and less-trained athletes do less. If the athlete slows during a rep, double the next rest; stop when the speed can no longer be held.
   - Event length decides the mix: for events of 3+ hours the race-specific block is mostly controlled mid-Zone 3 (uphill and rolling), with only tiny amounts of Zone 4 — elite ultrarunners log about 35-45% of training time in Zone 1, 45-55% in Zone 2, 7-9% in Zone 3 and under 2% in Zone 4. For events under ~2 hours, a Zone 3 block is followed by Zone 4 as the final stage.
   - Utilization (race-like) work — high-intensity uphill intervals for a mountain runner; low-priority races count — must be added at least 6-8 weeks before the taper, whatever the athlete's aerobic capacity. Before that, capacity sessions train one quality at a time (an easy run stays easy, strides aside).
   - Anaerobic endurance work (20-60 s efforts to exhaustion) is not worth its fatigue cost for multi-hour events: do not prescribe it.
"""
        if profile.allows_intensity
        else ""
    )

    # Doctrine that only applies once volume is high enough for it to matter.
    high_volume_rules = (
        """13. High-Volume Directives (this athlete trains at a volume where these bind):
   - Diminishing Returns on Mileage: piling raw mileage onto an established high baseline yields diminishing returns and sharply raises overuse-injury risk. To keep adapting, add targeted LOW-GLOBAL-FATIGUE stimuli — Zone 3 sub-threshold work, or weighted Muscular Endurance — rather than more easy miles.
   - Zone 1 Substitution: when an athlete's AeT pace is exceptionally fast, Zone 2 running imposes a large neuromuscular load. Reduce Zone 2 volume and place 35-45% of total volume in Zone 1 'stumblingly slow' running to avoid structural injury.
   - Double-Threshold Days (Norwegian model): where two Zone 3 sessions share a day, the morning is controlled intervals (e.g. 10 x 1-mile sub-threshold, 1 min rest) and the afternoon a continuous sub-threshold tempo of 20-30 min. Hold lactate at 2.5-3.5 mMol/L.
   - Double-Day Spacing: easy aerobic doubles need 6-10 hours between sessions; double-threshold days need a strict 8-12 hours, ideally 10-12, for metabolic clearing.
   - Deload Weeks Are Consolidation Weeks: drop load so supercompensation can complete. Do NOT prescribe inactive rest — it leaves legs heavy and stiff. Use non-impact work: swimming, 20-30 min easy stationary cycling, walking.
   - Readiness Red Flags — instruct the athlete to act on these, and respond to them in their feedback:
     * resting HR up 10-15% (10-15 bpm) over baseline: immediate easy day or rest day;
     * an abnormally LOW resting HR plus inability to raise HR in exercise, severe fatigue and low mood: parasympathetic overtraining — stop training and seek guidance, this is months not days;
     * grade each session A-F; more than two 'C's in a row, a 'C' and a 'D' in one week, or more than three 'C's in a week: immediate easy day or rest;
     * the warm-up rule: if they do not start feeling better during the warm-up, stop and convert the session to recovery;
     * the daily repeatability test: if they cannot comfortably repeat yesterday's aerobic base session this morning, daily volume is exceeding work capacity — scale back.
"""
        if profile.key in ("sub_elite", "elite")
        else ""
    )

    return f"""
Rules:
1. Block Scope & Schedule: Generate workouts for the specified block weeks only. Each week must have structured workouts (typically 4-6 workouts per week). ALWAYS honor the athlete's preferred training days and double-session days from their profile — place Rest workouts on non-preferred days, and produce two workout objects on each double-session day as described above.
{intensity_rule}3. Long Run Proportionality Cap: In the Base phase the long run is about 25% of total weekly volume (the Uphill Athlete long aerobic run share). From the Build phase onward, as race-specific long efforts grow, a single long run may rise to but must NOT exceed {long_share}% of total weekly volume. Back-to-back weekend long runs (Saturday + Sunday) are NOT a weekly routine — they impose CNS and musculoskeletal overload that costs days of recovery and breaks weekly continuity. Use them only as short two-day overreaching blocks, at most 2-3 times in the Specific period before an ultra (50K+), each followed by several easy days, and their combined total must NOT exceed 50% of that week's volume. WEEKDAY RUN DURATIONS: Weekday runs (Mon-Fri) are typically {lo}-{hi} minutes for this athlete — respect their daily work schedule, and never schedule an excessive 90-120+ minute run on a weekday unless explicitly requested.
{me_periodization}5. Deload Adaptation Cycles: Follow a 3:1 (or 2:1 for masters/fatigued runners) loading-to-recovery pattern. On recovery/deload weeks, reduce weekly volume by 20-30% to consolidate physiological adaptation and prevent overtraining.
6. Aerobic Deficiency Syndrome (ADS) Rule: If ADS is detected in the athlete profile, strictly enforce aerobic base building: ALL running at or below AeT (Zone 1-2). NO Zone 3, 4 or 5 work — no tempo, threshold or intervals — while the AeT-AnT gap is above 10%: training above AeT signals the body to prioritise glycolytic capacity and delays the aerobic development ADS needs. Ideally the gap closes before the ME block begins. If it has not closed within 6-8 weeks of the taper, still add the ME and higher-intensity work the race demands — an under-prepared athlete is worse off — but keep it to the minimum and protect the Zone 1-2 volume. Strides and Hill Sprints STAY in the plan throughout: they are neuromuscular power work, not Zone 3-5 endurance intensity. Consistent Zone 2 training typically raises an aerobically deficient runner's AeT speed by 20-30% within 6-12 months.
7. Make the plan highly customized. For example, scale long runs, map Sunday Muscular Endurance box steps/weighted step-ups based on the race elevation gain, or specify treadmill incline/speed settings for gym workouts.
8. NEVER invent a physiological claim, exercise, or number beyond what the Uphill Athlete training philosophy implies. If unsure of an exact figure, give a sensible range instead of fabricating false precision.
9. Give the athlete profile and prior feedback below real weight — this plan MUST reflect their specific numbers, schedule, and history, not a generic template.
10. Uphill Athlete & Trail Specificity: For mountain/trail races, incorporate progressive eccentric quad conditioning (eccentric box step-downs, downhill repeats, hill bounding). For ultra distances (50K+), back-to-back long days follow the overreaching limits in rule 3. If the course profile notes high heat or altitude, integrate acclimation guidance.
11. Environmental & Routine Scheduling: Place every session where TRAINING VENUES (rule 5) says it can happen. When hills are only reachable on some days, those days carry the high-vert long runs, weighted carries and any back-to-back overreach, and the city weekdays carry gym ME, treadmill or stair work and flat aerobic running. If no hill days are recorded but the athlete's notes mention weekend trail trips, follow the notes the same way. Keep weekday runs accessible ({lo}-{hi} min).
{me_directives}{high_volume_rules}{quality_rules}"""


def build_rules_block(
    profile: TierProfile, max_continuous_jog_min: int | None = None, treadmill_max_incline: int = 15
) -> str:
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
    body = (
        _beginner_rules(profile, max_continuous_jog_min)
        if profile.uses_walk_run
        else _performance_rules(profile, treadmill_max_incline)
    )
    return header + body
