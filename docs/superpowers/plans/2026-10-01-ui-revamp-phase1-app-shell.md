# UI Revamp Phase 1: App Shell

**Goal:** A signed-in athlete opens the app and sees this week's plan, with today's workout visible without scrolling at 375 px.

**Source:** Kotcha review (https://claude.ai/artifact/1mZMJuhqMYbEkKpfRBYd7M), Phase 1 row.

**Decisions (2026-10-01):**
- Tabs: **Plan / Coach / Me**. Progress stays hidden until Phase 4. Human coaches (`user.is_coach`) also get **Athletes**, which is the existing `CoachDashboardView`.
- Tools and Knowledge Hub: Nutrition, Pace Strategy and Goal Determiner open from the race card. Gear, Knowledge Hub and About are listed under Me → More. No feature is removed.
- Rollout: behind a flag, on by default in staging. The old shell stays for one release so we can roll back.
- Desktop: the same tabs as a left sidebar, with the plan column capped at about 720 px.

**Out of scope:** changes to workout card content (Phase 2), onboarding (Phase 3), the Progress tab (Phase 4) and weekly auto-generation (Phase 5). Phase 1 is frontend only except Task 6a (the `is_priority` field).

**Global constraints:**
- All new UI copy is English in both `lang` modes (decision 2026-10-01: no Vietnamese strings for new V2 labels).
- V1 (flag off) must render exactly as before.
- Priority is explicit data set by the AI or a coach. The frontend never infers it.
- Inline styles and existing CSS variables, matching surrounding code. Phosphor icons.

---

## UX rules applied (ui-ux-pro-max)

| Rule | How it applies here |
|---|---|
| Bottom nav with 5 items or fewer, with labels | 3 tabs (4 for coaches), each with an icon and a text label |
| Touch targets at least 44×44 px, 8 px apart | Tabs, carousel dots, Manage plan items, the collapsed rest row |
| Keyboard navigation and visible focus | Tabs become `<button>` elements with `aria-current="page"` (today they are `<li onClick>`). The sheet traps focus and returns it to its trigger. |
| Fixed nav must not cover content | The content panel gets bottom padding equal to the nav height plus `env(safe-area-inset-bottom)` |
| Predictable back behavior and deep links | The active tab is mirrored to `?tab=plan\|coach\|me` with `replaceState`, and read on boot |
| Reserve space to avoid layout shift | The carousel has a fixed height (148 px) and shows a skeleton while the plan loads |
| Motion that respects reduced motion | Scroll-snap only. Smooth scroll and the sheet slide are turned off under `prefers-reduced-motion`. |
| Don't rely on color alone | Priority uses a text label and an outline. Rest rows use text, not only a lower opacity. |
| No horizontal page scroll | Only the carousel track scrolls sideways, with `overscroll-behavior-x: contain` |

Visual language is unchanged: existing CSS variables, light theme, Phosphor icons. This phase changes structure, not branding.

---

## Task 0: Feature flag

**Files:** new `frontend/src/utils/uiVersion.ts` and its test; `AppContext.tsx`

- `isShellV2()` returns true when `NEXT_PUBLIC_UI_V2 === "true"`, or when `?ui=v2` or `?ui=v1` has set localStorage key `UPHILL_UI_VERSION`. This follows the `?api=` override pattern in `utils/native.ts`. Wrap storage access in try/catch.
- Expose `shellV2` on `AppContext`.
- Staging build sets `NEXT_PUBLIC_UI_V2=true`. Production leaves it unset until sign-off.
- **Test:** vitest covers the env var, both query overrides, a localStorage failure, and the default (off).

## Task 1: Tab model and default tab

**Files:** `contexts/AppContext.tsx`, `app/app/page.tsx`

- Under V2, `activeTab` defaults to `"planner"` for signed-in users. It is `"tools"` today, and `"home"` on native.
- Signed-out users keep today's behavior: the auth modal opens on protected tabs.
- Add a `"me"` tab value. Keep `tools`, `knowledge` and `about` as reachable values so Me → More and the race card can open them. They are no longer in the nav.
- Nav list under V2: `["planner", "chat", "me", ...(is_coach ? ["coach"] : [])]`. Labels: **Plan / Coach / Me / Athletes**, in English for both languages.
- Sync `?tab=` to the URL both ways (`plan` maps to `planner`, `coach` to `chat`, `athletes` to `coach`).
- Sub-screens opened from Me (Gear, Knowledge, About) show a back button that returns to Me. Nav highlights **Me** while they are open.
- The native `HomeTab` is dropped from the V2 nav. Anything it shows that Plan doesn't goes to Me.
- **Tests:** extend `e2e/navigation.spec.ts` to check the default tab, that `?tab=me` deep-links, that back from Gear returns to Me, and that non-coaches don't see Athletes.

## Task 2: Accessible nav components

**Files:** `app/app/page.tsx`, with the nav render blocks at about lines 2421 (sidebar) and 3174 (bottom bar); `globals.css`

- Replace `<li onClick>` with `<button type="button" aria-current={active ? "page" : undefined}>` inside `<nav aria-label="Main">`. Do this in both the sidebar and the bottom bar.
- Update `--nav-count` for the 3–4 items. Check the sliding indicator (`native-nav-motion`) at both counts.
- Add `padding-bottom: calc(var(--bottom-nav-h) + env(safe-area-inset-bottom))` to `.content-panel` on mobile.
- Desktop sidebar: the same items. Keep the `.content-panel` width for Plan at `max-width: 720px`.

## Task 3: Me tab

**Files:** new `views/MeView.tsx` and its test

Sections, top to bottom, all reusing existing components:
1. **Profile row:** avatar, name, and an "Edit profile" button that opens the existing `ProfileSettingsModal` through `setProfileSettingsOpen(true)`.
2. **My paces:** Z2, threshold and VO2 from `usePaceZones`, shown read-only as three columns.
3. **Watches:** `ConnectedAccounts`.
4. **Race history:** `RaceHistoryPanel`.
5. **More:** a list with Gear Finder, Knowledge Hub, About Uphill, Language, and Sign out. Each row is at least 48 px tall with a chevron.

- **Tests:** vitest checks that the sections render for a user with a plan and without one, and that More rows call `handleTabSwitch` with the right tab.

## Task 4: Manage plan sheet

**Files:** new `components/BottomSheet.tsx`, new `components/ManagePlanSheet.tsx`, `views/PlannerView.tsx` (header, about lines 1469–1670)

- `BottomSheet`: a sheet that slides up on mobile and becomes a centered dialog at 768 px and wider. It uses `role="dialog"`, `aria-modal`, traps focus, closes on Esc and backdrop tap, returns focus to its trigger, and locks body scroll. There is no existing sheet component to reuse; `ConfirmActionModal` is the nearest reference.
- `ManagePlanSheet` rows move out of the header without any logic change:
  - **Sync watch** (`handleHeaderSync`, with the status message shown inside the sheet)
  - **Export calendar** (the existing `showExportOptions` flow)
  - **Load a recent plan**
  - **Plan settings**
  - **Start a new plan** (styled as destructive, goes through `ConfirmActionModal`)
- V2 header becomes: race name, distance and D+, date, and a trailing **Manage** button (a text label, not icon-only). `CoachNoteThread` moves below the carousel as a single row.
- The List/Calendar toggle becomes a two-icon segmented control on the week row. Each icon has an `aria-label`.
- Only the V2 branch changes. V1 renders the current header unchanged.

## Task 5: Plan summary carousel

**Files:** new `components/PlanSummaryCarousel.tsx` and its test; `PlannerView.tsx`

- CSS scroll-snap track (`scroll-snap-type: x mandatory`), with each card at 100% width and 148 px tall. Dots sit below and are real buttons (`aria-label="Show volume"` and so on), 24 px visible inside a 44 px hit area. The active dot is tracked by an `IntersectionObserver`. No carousel library.
- On desktop at 768 px and wider, the 4 cards sit in a 2×2 grid and nothing scrolls.
- Cards (all from data already on the client):

| Card | Content | Source |
|---|---|---|
| **Volume** | Bars of planned hours for every generated week, with the current week highlighted and weeks not yet generated as outlined placeholders. Header: "12.4 h · +2,150 m this block" | `workouts` grouped by `week_number`. Reuse the weekly volume math already in PlannerView (about line 1744). Extract it to a helper in `utils/`. |
| **Race & goal** | Race name, distance, D+, date, days to go, `GoalPill`. Tapping the card opens Race tools: Pace Strategy, Nutrition, Goal Determiner | `activePlan`, and the existing `setIsPaceStrategyOpen` / `setIsGoalDeterminerOpen` |
| **This week** | Mon–Sun dots (done, missed, planned, rest) and "3 of 5 done" | The same completion data the weekly review ring uses today |
| **Phase** | Phase name, "Week 2 of 4 in Base", and a one-line purpose | `workout.phase` plus the existing phase banner copy (about line 1931) |

- The existing Weekly Volume card and phase banner are hidden under V2 because the carousel replaces them. "Adapt Week N" moves into the This week card as a text button.
- **Tests:** vitest checks that the volume helper handles missing weeks, that "days to go" is 0 on race day and not negative afterwards, and that the dots have labels.

## Task 6a: Explicit priority field (backend)

**Files:** `backend/db.py` (`init_db` plus workout read/write helpers), a new Alembic migration, `backend/services/plan_generator.py`, `backend/main.py`, backend tests. Follow the `db-migration` skill and `.claude/skills/llm-change-process/SKILL.md`.

- Add column `workouts.is_priority BOOLEAN NOT NULL DEFAULT FALSE` in both `init_db()` (with the idempotent ALTER for existing dev DBs) and a hand-written Alembic migration.
- Include `is_priority` in every workout dict the API returns and in `save_workouts`.
- **AI marking:** add an `"is_priority": true|false` field to the per-workout JSON schema in the in-code `PLAN_GENERATION_PROMPT` fallback. Add one instruction line: mark the 1–2 sessions per week that matter most for the goal (usually the key quality session and the long run), and never a rest, recovery or easy run. Parse it with a default of `false`, and coerce non-bools to `false`. The same applies to the next-block and single-workout generation paths if they share the schema.
- **Server-side guard:** after parsing, clear `is_priority` on Rest-type workouts and cap it at 2 per week (keep the first two by day order). This is enforced in code, not left to the prompt.
- **Coach marking:** the existing `PUT /api/coaching/athletes/{athlete_id}/plans/{plan_id}/workouts/{workout_id}` accepts an optional `is_priority` bool. The 2-per-week cap does not apply to coach edits.
- **LLM change process:** the Langfuse `plan_generation` prompt version and the golden-eval run are manual follow-ups for the user, listed in the PR description checklist. The code must work with a Langfuse version that lacks the field (default `false`).
- **Tests (pytest):** parsing defaults and coercion, the rest-day and cap guards, the column being present after `init_db`, and the coach PUT toggling it.

## Task 6b: Collapsed rest days and the Priority marker (frontend)

**Files:** `PlannerView.tsx` (day rows, about line 2968), `WorkoutCard.tsx`, the coach workout editor if one exists (`ScheduleFieldsEditor` or similar), tests

- **Rest days (V2):** one 44 px row reading "Wed · Rest", with no card and no Swap button. The Swap handle stays reachable through the day header's drag handle.
- **Priority display (V2):** when `workout.is_priority` is true, show a "PRIORITY" text label plus a 1.5 px accent outline. There is no color-only signal and no frontend inference.
- **Coach toggle:** where coaches already edit an athlete's workout, add a "Priority" checkbox that sends `is_priority` in the existing PUT.
- Today's and tomorrow's cards get a small "TODAY" / "TOMORROW" eyebrow.
- On first load, scroll to today's card (auto-scroll only; no smooth scroll under reduced motion).
- **Tests:** vitest checks that the label renders only when `is_priority` is true, that rest rows render collapsed under V2, and that V1 is unchanged.

## Task 7: Verification

1. `npm run lint`, `npx tsc --noEmit`, `npm test`. Run the existing e2e navigation and onboarding specs with the flag both on and off.
2. **Screenshot evidence** (the `ui-screenshot-evidence` skill), using the local test athlete with a plan, at 375×812 and 1280×800:
   - Plan tab at rest. Today's workout must be visible without scrolling. This is the phase success check.
   - Each carousel card
   - A workout marked Priority
   - Manage plan sheet open
   - Me tab
   - A deep link `?tab=me`
   - V1 with the flag off, to prove rollback still works
3. **Keyboard pass:** tab through the nav, carousel dots and the sheet, then close the sheet with Esc and confirm focus returns to Manage.
4. Run the `code-reviewer` agent over the PlannerView, AppContext and page.tsx diffs.

## Suggested PR split

1. Tasks 0–2: flag, tab model, accessible nav. Low risk.
2. Task 3: Me tab.
3. Tasks 4–5: sheet and carousel.
4. Task 6a: backend priority field.
5. Task 6b: rest days and Priority display, plus the Task 7 evidence.

Each PR is independently shippable behind the flag.

## Risks

- **`PlannerView.tsx` is 3,261 lines.** Keep V2 changes inside new components with thin branches, and don't refactor V1 code paths in this phase.
- **Losing tool discoverability.** Phase 0 analytics should show tab usage before and after. If Tools usage drops sharply, add a "Race tools" chip row above the carousel.
- **Carousel data gaps on new plans** (only week 1 generated). The Volume card shows outlined placeholders and "More weeks unlock as you train".
