# Progress tab: Training Progress and Health

Date: 2026-10-23 · Status: draft for approval · Research: `docs/research/2026-10-23-training-health-literature-review.md`

## Why

Athletes ask three things that Uphill answers today only in fragments, scattered across the plan view, the
goal pill and coach chat:

1. **Is my training working?** Am I doing the plan, and is my body adapting?
2. **Am I on track for my goal?**
3. **How am I recovering?** Sleep, HRV, resting heart rate.

Watch brands answer the third with their own opaque scores. None of them answers the second: progress
measured against *this* athlete's race goal. That is Uphill's edge. The tab should read like a coach's
summary, not a brand dashboard.

## Decisions taken

| Decision | Choice | By |
|---|---|---|
| Placement | One new **Progress** tab with two sections, Training and Health. iOS tab between Plan and Coach; web gets a matching nav item | user |
| Visual direction | **Apple-native**: solid calm cards, SF type, Swift Charts, system materials only, **emerald as the only accent**. No glass or video inside the tab; app shell untouched | user |
| Platform order | **iOS first**, web after | user |
| Empty data | **Never render an empty chart.** A card exists only once it has enough data to say something true | user |
| Athletes with no device | **Tab still shows.** Training works from plan data; Health becomes a single connect card | user (agreed with proposal) |
| Brand scores | Not imported or shown (no COROS Recovery %, sleep score or VO2max as headline numbers). We compute from raw signals so every brand gets the same tab | my call, from the research |
| Section switch | Segmented control (Training / Health) under the large title, remembered per device | my call |

## Goals

- One place that answers the three questions above in under ten seconds of looking.
- Works for every athlete: COROS, Apple Health (any brand that writes to it), or no device at all.
- Every number is explained in plain words: what it is, the athlete's own normal range, and what to do.
- Coach Uphill can explain any card and review the training, grounded in the same numbers.

## Non-goals (v1)

- Coach-role view of an athlete's Progress tab (the Athletes tab keeps `CoachChartsView`).
- Android / Health Connect, paid aggregators (Terra and similar).
- New brand integrations, FIT-file analysis.
- Changing how readiness influences plan generation or adapt-week.

## Anti-goals (a failure even if it works)

- An empty chart outline, a "0" placeholder or a chart with two dots.
- Claiming injury prediction from the load ratio. The research is clear this isn't valid.
- Judging sleep stages or sleep "quality". Wearables agree with the lab only about 50–65% of the time.
- Comparing HRV across devices or with other people.
- Medical language or diagnoses ("your heart…", "you may be ill").
- Showing a number the coach then words differently. Model text never invents numbers.

---

## What the athlete sees

### Training section (top to bottom)

| Card | Answers | Shows | Appears when | Source |
|---|---|---|---|---|
| **Coach's read** | the summary, in words | 2–3 sentences on this week + the one thing to do next | the athlete has an active plan and at least one completed week | `coach_nudge`-style generation (phase 4); until then a rule-based sentence |
| **Goal** | am I on track? | B/A path status (ahead / on / behind), goal time, feasibility label | active plan with a goal | `fitness_tracking.path_payload`, `goal_feasibility` |
| **Consistency** | am I doing the plan? | sessions done / planned per week, last 8 weeks (bars), plus the most common missed reason | ≥ 2 completed plan weeks | `workouts.is_completed / is_missed / missed_reason` (works with no device) |
| **Volume & climb** | is the load building as planned? | weekly km and vertical, actual vs planned | ≥ 3 weeks with logged or synced sessions | activities + plan workouts |
| **Training response** | is my body taking this phase as it should? | this week's HRV and resting HR against the 4 weeks before, on a map with the zone the plan's phase should land in shaded; one headline and a takeaway. Load phases (Base/Build/Peak) expect a mild dip; light phases (Recovery/Taper/Race Week) expect a rebound. States follow WHOOP's public HRV training guide | active plan with a phase this week, ≥ 14 days of both signals from one source, ≥ 3 in the last 7 | `progress_cards.training_response` |
| **Aerobic speed** | am I getting fitter? | pace at aerobic-threshold heart rate, weekly, against the B and A lines | the existing `aerobic_speed` rules (≥ 3 weeks, ≥ 3 qualifying runs) | `aerobic_speed`, `fitness_checkpoints` |
| **Durability** | do I hold up on long runs? | heart-rate drift % on each long run (≥ 90 min, steady), lower is better | ≥ 3 qualifying long runs | new: COROS lap data (phase 1). Apple Health runs carry no laps, so COROS only in v1 |
| **Training load** | too much or too little lately? | last 7 days vs last 6 weeks, as a band chart. Wording says "above / within / below your usual", never "risk" | ≥ 28 days of load | `daily_metrics.training_load_short/long` (COROS only in v1) |

### Health section

| Card | Shows | Appears when |
|---|---|---|
| **Coach's read** | today in one sentence, plus named contributors ("HRV below your normal, sleep short two nights") | at least one signal has a baseline |
| **Sleep** | hours asleep per night (28 days) against the athlete's own usual range; bedtime and wake time only when the source provides them (COROS after phase 1; Apple Health stores minutes only today) | ≥ 7 nights |
| **Resting heart rate** | 28-day line with a personal baseline band | ≥ 7 days |
| **HRV** | 28-day line with a normal-range band, from one source only, labelled with that source | ≥ 14 nights from one source |

The 28-day view is the default. Tapping a card opens a detail screen with a 4W / 3M range switch and a
short "what this means" text, drawn from the literature review.

### When a card doesn't qualify yet

- It isn't rendered: no frame, no title.
- At most **one** quiet line at the bottom of each section lists what's coming, for example "Durability
  appears after 3 long runs". It disappears when nothing is pending.
- **No device connected:** the Health section is a single card, "Connect COROS or Apple Health to see
  sleep, HRV and resting heart rate", with the connect action. Training shows whatever qualifies.
- **No plan at all:** the tab still opens. Health works if a device is connected; Training shows a single
  card that leads to creating a plan.
- **Brand-new athlete with nothing yet:** one welcome card per section explaining what will appear and when.

---

## Visual direction (Apple-native, emerald accent)

Reference: Apple Health's *Summary* and *Trends*, and Fitness's *Trends*. Apply the HIG directly in SwiftUI
rather than imitating it.

- **Structure:** `NavigationStack`, large title "Progress", segmented `Picker` (Training | Health), then a
  single-column `ScrollView` of cards. On iPad and wide web, two columns.
- **Card anatomy** (the Health app pattern): a top row with an SF Symbol and the metric name in emerald
  plus the "as of" date on the right; a large rounded-numeral value with its unit; a compact Swift Chart
  (no axes on the summary card); one plain-language line ("2 bpm below your usual").
- **Colour:** system grouped background, cards on the secondary grouped background. Emerald is the only
  accent: chart marks, symbols, the selected segment. Status uses system colours sparingly (orange for
  "below usual", never red unless something needs action). Normal-range bands are emerald at low opacity.
- **Type:** SF Pro, Dynamic Type everywhere, rounded numerals for values (`.fontDesign(.rounded)`),
  monospaced digits in charts.
- **Minimalism:** one idea per card, no decorative gradients, no shadows beyond the system card style,
  generous spacing. Copy is plain and specific.
- **Motion:** system defaults only (chart animation on first appearance, standard push transitions).
  Respect Reduce Motion.
- **Accessibility:** every chart gets an `AXChartDescriptor` and a spoken summary. Contrast is checked in
  light and dark. Values are never conveyed by colour alone.
- **Web (later):** same card anatomy and order on solid surfaces inside the existing shell, using the
  existing emerald tokens from `DESIGN.md`. No glass inside the tab content.

Existing pieces to reuse, not duplicate: `GoalPathRow`, `SummaryCarousel` (Plan tab), `TrainingZoneBar`,
`Tokens.swift`, `CardModifier`.
The Plan tab keeps its short summary; Progress holds the full picture. Overlap is acceptable for the goal
row only.

---

## Coach

- **Coach's read cards** follow the existing `coach_nudge` pattern: the code picks the facts and numbers,
  the model only words them, number-grounding is checked, and a rule-based sentence is the fallback. One
  generation per athlete per day per section, cached.
- **"Ask Coach about this"** on every detail screen opens Coach Uphill with the card's context
  pre-attached. Chat already receives 7-day readiness (`coach_context.py` section 6). Add sleep/HRV/RHR
  baselines and the Training cards' facts to that context.
- **Weekly training review:** extend the existing week review (`WeekReviewSheet`) with consistency,
  durability and health contributors rather than building a new flow.
- Any new or edited prompt goes through `.claude/skills/llm-change-process/SKILL.md` (Langfuse prompt,
  golden-set eval, staging → production label).

---

## Data and backend

### Phase 1: data we're missing (COROS)

Checked on a real account on 2026-10-23 (see the literature review, section 3).

1. **Sleep:** call `querySleepOverview` in `CorosAdapter.fetch_daily_metrics` and fill
   `daily_metrics.sleep_minutes` (main sleep asleep minutes plus naps, matching Apple Health's "asleep").
   Also store the sleep window (new columns `sleep_start`, `sleep_end`). The parser must handle older days
   with no `Daily Sleep` line, and nap-only days (score −1, no main sleep).
2. **History backfill on connect:** sleep and HRV accept explicit dates (HRV is 7 days per call). Backfill
   90 days once, paced. Resting HR takes `days` up to at least 120. Training load returns about 31 days
   at most. From then on the daily sync accumulates history (`daily_metrics` is one row per day).
3. **Durability:** for runs ≥ 90 min, call `queryActivityLapData`. From the 1 km laps, compute the
   first-half vs second-half change in grade-adjusted speed per heartbeat (`adjustedPace`, `avgHr`). Key on
   field `name`, not the Chinese `label`. Store on the activity (new column `hr_drift_pct`). Exclude
   structured hard workouts (same set as `aerobic_speed._HARD_WORKOUTS`) and runs with a big stop share.
4. Schema changes go in both `db.py:init_db()` and an Alembic migration (`db-migration` skill).

### Phase 2: one endpoint, server decides what qualifies

`GET /api/progress?section=training|health` returns only the cards that qualify, each with its series,
baseline/band, a one-line interpretation key, `as_of` and source, plus a `pending` list for the hint
line. The qualification rules live in one backend module (for example `services/progress_cards.py`), so
iOS and web can't drift apart and can't render an empty card. Pure functions, unit-tested per card at
just-below and just-at each threshold.

Baselines:
- Resting HR and sleep: 28-day median ± a band.
- HRV: COROS's own normal range when the source is COROS. For Apple Health, the existing
  `recovery_baseline` (28 days, ≥ 14 present).
- One source per metric, matching the readiness rule (newest provider wins, COROS on a tie). The card
  names its source.

### Phase 3: iOS Progress tab

New `Features/Progress/`: `ProgressView`, the per-card views, `ProgressViewModel`, and the tab entry in
`RootView.swift`. Coaches then have five tabs (Athletes, Plan, Progress, Coach, Me), which is the most
the iOS tab bar shows before "More". No sixth tab can be added later without regrouping. EN + VI copy (the `uphill-ai-vietnamese-copy` skill). Screenshot evidence for every
state: device data, Apple Health only, no device, no plan, brand-new athlete (`ui-screenshot-evidence`).

### Phase 4: Coach

Coach's read generation, chat context additions, week review extension (see Coach).

### Phase 5: web

A `ProgressTab` view on the same endpoint, `TabName` gains `progress`, and the same screenshot states.

---

## Open decisions (yours, not the builder's)

1. **HRV method.** Our Apple Health HRV status uses a 3-day mean vs 1 SD of 28 days. The sports-science
   guidance (AIS) is a 7-day rolling log value against a "smallest worthwhile change" band. Switching
   changes readiness everywhere (plans, adapt-week, coach). Proposal: keep it for v1 and revisit as its
   own change.
2. **Training load for Apple Health athletes.** v1 shows the Load card only for COROS. A heart-rate-based
   load (TRIMP or time in zone from AeT/AnT) would cover everyone. Proposal: a follow-up after v1.
3. **Tab name.** "Progress" (EN) / "Tiến độ" (VI)? Or "Trends" / "Xu hướng"?

## Builder's latitude

Exact thresholds within the ranges above, chart styling within the visual rules, endpoint field names,
backfill pacing, card detail copy (EN/VI, reviewed against the copy skill).

## Verification

- Backend: unit tests per card qualification rule and per parser edge case (the sleep formats, nap-only
  day, laps with Chinese labels). The `golden_eval` / Langfuse process for any prompt.
- iOS: screenshots of all five states in light and dark, Dynamic Type XL and VoiceOver chart summaries.
- A real-account check: your COROS account should show Sleep, RHR, HRV, Load, Durability and Aerobic
  speed, with no empty cards.
