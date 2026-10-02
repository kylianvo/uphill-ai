# iOS native, Phase 2b: parity gaps and a simpler onboarding

**Goal:** Phase 2's screens follow the Kotcha review instead of copying every backend field. An athlete can sign up in under 90 seconds, then fill in the rest from a "Sharpen your plan" checklist. Profile and zone settings, schedule changes when adapting a week, scheduling warnings and the goal's reasoning all work natively, as they do on the web.

**Stacked on:** PR #81 (`claude/ios-native-phase2`) → #80 → #79. Branch `claude/ios-native-phase2b` from `claude/ios-native-phase2`.

**Why this phase exists:** the Phase 2 plan named apple-design and Impeccable as its design sources but not the Kotcha review. It also listed every `OnboardingRequest` field for parity, so the flow became a long form. The parity matrix in `docs/superpowers/specs/2026-10-01-ios-native-app-design.md` (section "Capacitor parity matrix") also found features that no phase covered. This plan fixes both.

**Design sources, in priority order:**
1. **Kotcha review** (https://claude.ai/artifact/1mZMJuhqMYbEkKpfRBYd7M), summarised under "Kotcha rules" below. This decides **what** is on screen.
2. **The existing web app** (`frontend/src`) decides **behaviour, copy and which fields exist**. Read the component named in each task before writing Swift.
3. **The spec's design system** (tokens, SF Pro, light only) and `.claude/skills/apple-design/SKILL.md` decide **how it looks and moves**.
4. **Impeccable** (the `impeccable:impeccable` skill, now installed). Run it twice only, to save tokens: `onboard` + `clarify` on the Task 2 screenshots, and one `polish` + `harden` pass over all other changed screens in Task 8. Its browser detector and live mode target web DOM. For iOS, feed it Simulator screenshots and apply its findings in SwiftUI. Record the main findings and what you changed in those two commit bodies.

**What stays as it is (owner decision 2026-10-02):** the workout card and the week header are already right. Don't trim them with Kotcha's "three metrics" rule, and don't change their content in Task 8.
- **Workout card:** date and weekday; name and type (Easy, ME, Long, ...); duration, estimated km, suggested pace, heart rate and zone; mark done, and missed or cancel with a confirmation. Matching a run from the watch arrives in Phase 4.
- **Week header:** Coach Uphill's review of the week and the phase brief for this week.
Task 8 may adjust their spacing and alignment to the baseline only.

**Out of scope:**
- Adding or editing a single workout. On the web this is coach-only (`isCoachActingAsAthlete`), so it moves to Phase 6.
- A real generation `stage` field and a single "fitness anchor" input (e.g. a recent race time). Both need backend changes. This phase makes no backend, prompt or schema changes; if a task seems to need one, stop and ask.
- Race history (Phase 5), so the checklist doesn't link to it yet.

---

## Global constraints

- Everything in Phase 0, 1 and 2's Global Constraints still applies: Swift 6, `@Observable @MainActor` view models, Swift Testing, fixtures recorded from the local backend and never hand-edited, the local backend only, and copying strings exactly.
- **Never run `backend/tests/integration` against `uphill_ai`**: it truncates every table. To re-seed: `cd backend && DATABASE_URL=postgresql://uphill:uphill_secret@localhost:5433/uphill_ai python scripts/seed_ios_preview.py`.
- The code on the branch (#81) is the source of truth for names. Adapt this plan's names to it and list the adaptations in the PR.
- Keep #81's models, services, poller and generation center. This phase changes views, view models and the draft's required fields, not the job plumbing.
- Screenshots go in `ios-native/docs/screenshots/phase2b/`. Take one **after** shot per changed screen (no before shots: #81's are in `phase2/`) and a single extra-extra-extra-large Dynamic Type shot for the whole phase (`onboard-large-text.png`). Look at each image once; don't re-read screenshots you've already checked.
- **Token budget:** run `test.sh` once at the end of each task, not before it, and pipe it through `tail -40`. Run `e2e.sh` only in Task 9. Read only the web files a task names, never whole directories.

## Kotcha rules (apply to every screen in this phase)

1. **One question per screen.** A screen may group two fields only when they are answered together (days per week and weekly km).
2. **The coach asks.** Each onboarding screen opens with a Coach Uphill line that also says why it needs the answer (strings in Task 2).
3. **Only five things are required:** goal, race (if racing), race date (if racing), days per week with current weekly km, and the start date. Everything else is optional, has a default, and never blocks.
4. **No warning pop-ups for missing data.** Missing HR or pace data lowers accuracy. The checklist tells the athlete what it would improve.
5. **Choices over typing.** Use large option rows, steppers and pickers. Type only names and notes.
6. **Each screen does one job.** No toolbars of buttons. Secondary actions go into a menu or sheet.
7. **Trail units first.** Show time and vertical gain where the web shows them; keep km for weekly volume because the backend takes km.
8. **Keep every feature.** Fields that leave onboarding move to the checklist or to settings. Nothing is dropped.

---

## Task 1: Design baseline and side-by-side audit

**Files:** create `ios-native/docs/design-baseline.md` (no new screenshots).

- [ ] **Step 1:** Don't run the web app. Use #81's `ios-native/docs/screenshots/phase2/` shots and the web components named in Tasks 2–7. Write a table in `design-baseline.md`, one row per screen, with columns: web, iOS #81, rule from "Kotcha rules" it breaks (if any), decision (keep / change / move to checklist / move to settings).
- [ ] **Step 2:** Under "Visual baseline" in the same file, write down what the iOS screens must share with the web: accent and ink colours (spec tokens), card radius 12, row spacing 12, section spacing 24, title/body/caption font styles, how option rows and the primary button look. Every later task cites this file.
- [ ] **Step 3:** Commit: `docs(ios): Phase 2b design baseline and audit`.

The audit can add a change that the tasks below don't cover. If so, put it in the PR under "Found in the audit". Don't widen the scope of a task without asking.

## Task 2: Single-question onboarding

**Read first:** `frontend/src/views/OnboardingWizard.tsx`, #81's `PlanSetupDraft`, `PlanSetupViewModel`, `SetupSteps.swift`.

**Required-field change (in `PlanSetupDraft`):** only the fields in Kotcha rule 3 are validated. Everything else is sent with the web's defaults when not set: `days_per_week` 4, `current_weekly_km` 30, `terrain` "trail", `training_environment` "flat", `has_gym_access` false, `race_goal` "finish". Drop the validation messages for HR, pace, injury and double sessions. Update `PlanSetupDraftTests` first (TDD): a draft with only the required fields must produce a valid `OnboardingBody` and `PlanBody`.

**Screens, in order (`.onboarding` mode).** Each has a coach line (`callout` font, secondary colour, beside the app mark) above one question:

| # | Question (title) | Coach line | Input |
|---|---|---|---|
| 1 | "What are you training for?" | "This sets the shape of your whole plan." | Option rows: "A trail race", "A road race", "Getting started", "Coming back after a break", "Recovering from a race" (map to `race` / `race` + terrain "road" / `start_running` / `return` / `recovery`) |
| 2 | "Which race?" (race goals only) | "If I know the race, I know its distance and climbing." | #81's race search field; manual distance and elevation only when no match |
| 3 | "When is it?" (race goals only) | "I'll count the weeks back from race day." | Date picker; shows "That's \(n) weeks away" |
| 3a | #81's existing return / recovery questions (non-race goals) | "So I don't start you too hard." | Option rows only, one question per screen |
| 4 | "How much do you run now?" | "Your first week starts close to what you already do." | Days per week stepper (3–7) and weekly km stepper (step 5) |
| 5 | "When do you want to start?" | "Pick today or any day in the next two weeks." | Date picker, default today |
| 6 | Review: "Here's what I'll build from" | "You can add heart rate, paces and injuries after this. They make each new week more accurate." | #81's summary lines, then primary "Build my plan" |

`.newPlan` mode uses screens 1–6 without the coach lines' first-time wording; keep #81's titles there if they differ.

- The progress bar at the top shows screen n of the total for the chosen path.
- Profile questions from #81 (date of birth, sex, height, weight), HR, pace, injury, long-run day, preferred days, double sessions, gym and terrain leave onboarding. They appear in the Task 3 checklist and the Task 4 and 5 settings.
- Keep #81's direction-matched transitions, keyboard avoidance and the "About 2 minutes" Welcome line. Change it to "About 1 minute".
- Tests: update `PlanSetupViewModelTests` for the new step list per goal. A race path has 6 screens. A "Getting started" path skips 2 and 3.
- Screenshots: each screen, plus `onboard-large-text.png` for screen 4.
- Timing check: run the flow by hand from Welcome to "Build my plan" and report the time in the PR. The target is under 90 s.
- Commit: `feat(ios): single-question onboarding with coach prompts`.

## Task 3: "Sharpen your plan" checklist

A card on the Plan tab, below the summary carousel. It's shown while any item is incomplete, and the athlete can hide it with "Hide for now". Hiding lasts until a new plan, stored in `UserDefaults` under `UPHILL_SHARPEN_HIDDEN_<planId>`.

- Title "Sharpen your plan", subtitle "\(done) of \(total) done · each one makes your next week more accurate".
- Items, each a row with a check state, which opens the screen named:
  - "Add your heart rate zones" → Task 4 Heart rate. Done when `aet_hr` and `max_hr` are set.
  - "Add your easy pace" → Task 4 Paces. Done when `zone2_pace_min` or `threshold_pace` is set.
  - "Tell me about injuries" → Task 4 About you (athlete notes). Done when `athlete_notes` is non-empty.
  - "Set your long-run day" → Task 5 schedule sheet. Done when the active plan has a `long_run_day`. If the plan model doesn't carry it, omit the item and say so in the PR.
  - "Add your age and weight" → Task 4 About you. Done when age and `weight_kg` are set.
- Tests: a pure `SharpenChecklist.items(user:plan:)` function with tests for each done rule.
- Screenshots: `sharpen-empty.png` (new athlete), `sharpen-partial.png`.
- Commit: `feat(ios): sharpen-your-plan checklist on the Plan tab`.

## Task 4: Profile and training zones (Me tab)

**Read first:** `frontend/src/views/ProfileSettingsModal.tsx`, `frontend/src/hooks/usePaceZones.ts`, `frontend/src/components/WatchZonesGuideModal.tsx`.

**Endpoints:**
- `POST /api/auth/update-profile`, which returns the user. `age`, `max_hr`, `resting_hr`, `aet_hr` and `ant_hr` are **required**, so always send the current values for fields the screen doesn't change. Optional: `zone2_pace_min`, `zone2_pace_max`, `gender`, `height_cm`, `weight_kg`, `threshold_pace`, `pace_zone_model`, `custom_pace_zones`, `athlete_notes`. Never send `gemini_api_key`: the app doesn't use bring-your-own-key, so it has no Gemini key field.
- `GET /api/auth/pace-zones?model=5_zone|4_zone`.
- Password change: the endpoint `ProfileSettingsModal` calls (`/api/auth/update-password`). Read its request model in the backend first. Show it only for email accounts.
- Record fixtures `update_profile.json` and `pace_zones.json` with `record_fixtures.sh`.

**Screens:** Me tab gets a "Training" section with three rows, each a pushed screen. Don't build one long form (Kotcha rule 6).
- **About you:** age, sex, height, weight, then "Injuries and notes for Coach Uphill" (`athlete_notes`).
- **Heart rate:** max, resting, aerobic threshold (AeT), anaerobic threshold (AnT), each a number field with the unit "bpm". Add a footer link "How to find these" → a sheet with the watch-zones guide copy from `WatchZonesGuideModal`.
- **Paces:** zone model picker ("5 zones" / "4 zones"), threshold pace or easy-pace range, then a read-only zone table from `pace-zones`. Custom zones: match the web if it lets athletes edit them, otherwise read-only.
- **Account** (existing Me section): add "Change password" (email accounts).
- After saving: banner "Saved. Your next week will use these." and the Task 3 checklist updates.
- Tests: view-model tests for the required-field merge (changing one HR value sends all five), validation (AeT < AnT ≤ max; resting < AeT) with the web's messages, and the offline write message from Phase 1.
- Screenshots: each screen.
- Commit: `feat(ios): profile, heart rate and pace zone settings`.

## Task 5: Schedule changes when adapting a week

**Read first:** `frontend/src/components/ScheduleFieldsEditor.tsx` and its use in the adapt-week modal (`PlannerView.tsx` around line 2367).

`AdaptWeekRequest` already accepts `preferred_days`, `long_run_day`, `days_per_week`, `double_session_days`, `has_gym_access`, `use_treadmill`, `training_environment` and `max_continuous_jog_min`. #81's adapt sheet sends only fatigue, RPE and notes.

- Add a disclosure row "Change my schedule" to #81's adapt sheet, collapsed by default. Expanded, it shows the following, prefilled from the plan when known:
  - run days (weekday chips)
  - long-run day
  - double-session days
  - "I can use a gym", "I can use a treadmill"
  - terrain near me: "Mostly flat" / "Hilly" / "A mix" (`flat` / `hilly` / `mixed`)
- Only fields the athlete changed are sent, so the backend keeps its own values for the rest.
- If the long-run day sits next to another quality day, warn inline, matching the web's wording if it has one. Otherwise: "A hard day right before the long run makes both harder."
- For "Getting started" plans, add "Longest run without walking" (minutes stepper) → `max_continuous_jog_min`. Show it only for that goal, as the web does.
- The same editor opens from the Task 3 checklist item "Set your long-run day" and from the Manage sheet as "Schedule". From those two places it starts an adapt-week job for the current week with fatigue `.medium`, after a confirmation: "Rebuild this week around your new schedule?" with buttons "Rebuild week" and "Not now".
- Tests: body contains only the changed fields; the jog field only for that goal.
- Screenshots: `adapt-schedule.png`, `adapt-schedule-warning.png`.
- Commit: `feat(ios): schedule changes when adapting a week`.

## Task 6: Scheduling warnings and move errors

**Read first:** `frontend/src/lib/scheduleProposals.ts` (`describeGuard`, `describeWarning`) and `frontend/src/components/CalendarNoticeBanner.tsx`.

`POST /api/coach/calendar/move` returns `{workouts, warnings: [{code, params}]}`, or 422 with `detail: {code, params}`. Check what Phase 1's move does with both and fill the gap.

- `ScheduleMessages.swift` with a pure `guardText(code:params:)` and `warningText(_:)`, using the English strings from `frontend/src/app/translations.ts` exactly:
  - guards: `G1_not_owner`, `G2_history`, `G3_past_target`, `G4_window`, `G5_out_of_plan`, `G6_coach_linked`, `G7_no_dates`, `STALE_changed`, `NOTHING_to_move`, `INVALID_operation`, `unknown`
  - warnings: `W1_same_day`, `W1_before_long_run` (when `params.kind == "before_long_run"`), `W2_volume_shift` (`before_minutes` / `after_minutes`), `W3_pending_draft`
  - `{day}` renders as the full weekday name.
- Warnings show as a banner prefixed "Heads-up:" (`.warning` style, dismiss on tap, auto-dismiss after 7 s like the web). Guards show as an error banner.
- Move-target fix from Phase 1: `G4_window` means moves are limited to this week and next week. Restrict the "Move to…" targets to this week and next, and only to generated weeks. If #81 already limits it to generated weeks, add the window.
- Tests: every code maps to its string; an unknown code falls back to the `unknown` text; a 422 body decodes.
- Screenshots: `move-warning.png`, `move-error.png`.
- Commit: `feat(ios): scheduling warnings and move errors`.

## Task 7: What the goal is based on

**Read first:** `frontend/src/components/GoalContextView.tsx` and `GoalResult.tsx`.

- Check #81's recorded `plan_goal.json` for `context` and `anchors`. If they're missing, re-record against a seeded athlete; the reassess endpoint is limited to 3 per day. Decode only the fields `GoalContextView` displays.
- In the Goal sheet, below the reasoning, add a disclosure "What this is based on" with three groups:
  - Race: distance, D+, course profile ("GPX" or "Estimated"), Time Target.
  - Field: winner, 10%, half and 90% finished.
  - You: weight, threshold pace.
  - Then a list of anchors, each with its method label from `METHOD_LABELS` (English) and a finish time.
- Hide any row with no value, as the web's `present()` does.
- Tests: decoding the fixture; empty groups are hidden.
- Screenshot: `goal-context.png`.
- Commit: `feat(ios): goal sheet shows what the estimate is based on`.

## Task 8: Restyle pass on the remaining Phase 2 screens

Run Impeccable's `polish` + `harden` once over all of this phase's screenshots, then apply `design-baseline.md` to every Phase 2 screen that Tasks 2–7 didn't already rebuild: the generation progress screen, next-week confirmation, weekly review, Goal pill, empty states and Manage sheet. Change layout, spacing and hierarchy only, not behaviour or copy. Exception: copy that breaks a Kotcha rule, such as a toolbar of buttons.

- Screenshots: one after-shot for each.
- Commit: `style(ios): Phase 2 screens follow the design baseline`.

## Task 9: Tests, end-to-end and the parity matrix

- [ ] Update the Phase 2 XCUITest onboarding flow to the new screen order.
- [ ] `ios-native/scripts/test.sh` and `ios-native/scripts/e2e.sh` pass.
- [ ] Mark in the spec's parity matrix:
  - These rows done: `ScheduleFieldsEditor`, `ProfileSettingsModal`, `CalendarNoticeBanner`, `GoalContextView`.
  - The `WorkoutTypeSelect` row moved to Phase 6 (coach-only on the web).
- [ ] Commit: `test(ios): Phase 2b end-to-end and parity matrix`.

## PR

Title: "iOS native, Phase 2b: simpler onboarding and parity gaps". In the body:
- Stacked on #81 → #80 → #79.
- The audit table from `design-baseline.md`.
- Screenshots.
- Onboarding time measured by hand.
- Snippet adaptations.
- "Found in the audit" items.
- "No backend, prompt or schema changes".

Then the attribution line.
