# Quieter Plan Screen (iOS) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The iOS Plan screen shows each fact once, with at most two pills per day, and reads the same in EN and VI.

**Architecture:** Pure presentation changes in `ios-native/UphillAI/Features/Plan`, with the logic that decides what to show (week line, day pills, session sheet order) moved into small pure functions in `Core/Plan` so it can be unit-tested. No backend, model or API change.

**Tech Stack:** SwiftUI, Swift Testing, `UH` design tokens (`DesignSystem/Tokens.swift`), `Localizable.xcstrings`.

**Spec:** `docs/superpowers/specs/2026-10-23-plan-view-distill-design.md`

## Design brief (shape, confirmed 2026-10-23)

- **Job:** a trail runner opens Plan to see the week they are in and today's session. Operate mode. Success: in one glance they know the week (phase, hours, km), today's session and whether the goal is on track, without reading the same fact twice.
- **Direction:** refinement of the incumbent world, not a redesign. Emerald for meaning only, forest ink, one 1 pt `UH.Palette.line` border, corners ≤ 12 pt, no gradients on content.
- **Order on screen:** header (race name, date, "N weeks to go") → week line ("Week 6 · Build · 7.5 h · 52 km") with a quiet "Adapt this week" text button under it → carousel (This week, Goal progress) → coach card (one message) → week switcher → day rows → "Read this week" knowledge card.
- **Decisions the user made:** the volume chart (days / every-week trend) moves inside the This week card behind its existing two-way toggle; the one Adapt action lives under the week line; Apple rules and the current tokens win over the taste skill's serif, Phosphor and monochrome rules.
- **Anti-goals:** no new colours, fonts or components; nothing deleted from the session sheet, only reordered or folded; web untouched.

## Global Constraints

- Fonts only from `UH.TextStyle` (`screenTitle`, `sectionTitle`, `body`, `label`, `caption`, `disclosure`, `eyebrow`, `metric`). No `.font(.system(size:))` left in the files this plan touches. These are Dynamic Type styles; nothing may clip at the largest accessibility size.
- Apple HIG: tap targets ≥ 44 × 44 pt; SF Symbols only where they carry meaning (status, source, priority, disclosure chevrons, toolbar actions); every icon-only control has an `accessibilityLabel`; colour is never the only signal (status pill has text); honour Reduce Motion (no new animation); light and dark mode both checked.
- Colours only from `UH.Palette`. Borders: `UH.Palette.line`, 1 pt. Corners: `UH.Radius` values ≤ 12 pt.
- Every new string in EN and VI in `Resources/Localizable.xcstrings`, following `.claude/skills/uphill-ai-vietnamese-copy/SKILL.md` (Build, Base, Taper, Long Run, Interval stay in English).
- Keep every existing `accessibilityIdentifier` that a test or UI test uses, unless the element is removed; then update the test in the same commit.
- Tests: `ios-native/scripts/test.sh` must pass after every task.

## Review Focus

1. A week with no planned km (strength-only or rest week): the week line must drop the km part, not show "0 km".
2. Race week and race day: header says "Race week" / "Race day" and the week line still shows; no "0 weeks to go".
3. A double day (two sessions) that is also today and has a matched run: still at most two pills per session row, "TODAY" once.
4. VI at the largest Dynamic Type size: the week line wraps to two lines instead of truncating; pills don't push the title off the row.
5. Athlete viewed by a coach (`actingAsAthlete != nil`): Adapt action hidden exactly where `canAdaptWeek` says, as today.

---

### Task 1: Week line and one Adapt action

**Files:**
- Modify: `UphillAI/Core/Plan/PlanSummary.swift`
- Modify: `UphillAI/Features/Plan/PlanView.swift` (`raceGoalHeader`, the standalone "Adapt week button" block at ~line 236)
- Modify: `UphillAI/Resources/Localizable.xcstrings`
- Test: `UphillAITests/Plan/PlanSummaryTests.swift`

**Interfaces:**
- Produces: `PlanSummary.weekLine(_ volume: WeekVolume) -> String` (`WeekVolume` already carries `week`, `phase`, `km`, `hours`)

- [ ] **Step 1: Write the failing tests** in `PlanSummaryTests`:

```swift
@Test func weekLineFull() {
    let v = WeekVolume(week: 6, km: 52, minutes: 450, gainM: 0, generated: true, actualKm: 0, phase: "Build")
    #expect(PlanSummary.weekLine(v) == "Week 6 · Build · 7.5 h · 52 km")
}
@Test func weekLineNoKm() {   // strength-only week: no "0 km", whole hours without ".0"
    let v = WeekVolume(week: 3, km: 0, minutes: 240, gainM: 0, generated: true, actualKm: 0, phase: "Base")
    #expect(PlanSummary.weekLine(v) == "Week 3 · Base · 4 h")
}
@Test func weekLineNoPhase() {
    let v = WeekVolume(week: 1, km: 40, minutes: 330, gainM: 0, generated: true, actualKm: 0, phase: nil)
    #expect(PlanSummary.weekLine(v) == "Week 1 · 5.5 h · 40 km")
}
```

- [ ] **Step 2: Run** `ios-native/scripts/test.sh -only-testing:UphillAITests/PlanSummaryTests`. Expected: FAIL, `weekLine` not found.
- [ ] **Step 3: Implement `weekLine`.** Phase goes through `L()` so VI keeps the English phase name per the copy skill; hours one decimal, trimmed when whole; km rounded to an integer; parts joined with " · ". Add the "Week %lld" key with VI "Tuần %lld".
- [ ] **Step 4: In `PlanView`:** remove the goal pill from `raceGoalHeader` (keep race name, date and weeks-to-go; replace its `.system(size: 19)` with `UH.TextStyle.sectionTitle`). Under it add `Text(weekLine)` in `UH.TextStyle.label`, `UH.Palette.secondary`, and when `model.canAdaptWeek(model.selectedWeek)` a plain text button "Adapt this week" (`UH.TextStyle.disclosure`, `UH.Palette.accentInk`, `frame(minHeight: 44)`, identifier `plan.adaptWeek`). Delete the standalone capsule Adapt block. Drop `accessibilityIdentifier("plan.goalpill")` users in tests (the goal card is the way into `GoalSheet`).
- [ ] **Step 5: Run** `ios-native/scripts/test.sh`. Expected: PASS (update `PlanFlowUITests` if it taps `plan.goalpill`; it should tap the goal progress card instead).
- [ ] **Step 6: Commit** `feat(ios): week line in the Plan header; one Adapt action`.

### Task 2: Carousel down to two cards

**Files:**
- Modify: `UphillAI/Features/Plan/SummaryCarousel.swift`
- Modify: `UphillAI/Features/Plan/PlanView.swift` (the `SummaryCarousel(...)` call)
- Test: `UphillAITests/Plan/PlanAuditScreenshots.swift` (render check only)

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: `SummaryCarousel(model:onReview:onGoal:initialVolumeMode:)` — `onAdapt` and `adapting` parameters removed.

- [ ] **Step 1:** `body` keeps `weekCard` then `goalProgressCard` (This week first: it is the week the user is planning). Delete `raceCard`, `phaseCard` and their helpers (`phaseWeekText`, `phasePurpose`) once nothing uses them.
- [ ] **Step 2:** Fold `volumeCard` into `weekCard`. The card's top row is the eyebrow "This week" plus the existing two-way `VolumeChartMode` toggle (`.weekDays` default, `.weekTrend`; identifiers `volume.mode.days|trend` kept); below it the chosen chart; below that one line "Planned 52 km · Done 31 km" from `PlanSummary.volumeComparison`. The big km/hours numbers go (the week line in Task 1 carries them). Remove the Adapt button from the card.
- [ ] **Step 3:** If both cards fit the width (≥ 2 × 315 + spacing), lay them out without horizontal scroll; otherwise keep the `ScrollView(.horizontal)` with `.scrollTargetBehavior(.viewAligned)` so a card snaps (Apple paging feel). Replace the 26 pt monospaced number with `UH.TextStyle.metric`.
- [ ] **Step 4: Run** `ios-native/scripts/test.sh`. Expected: PASS; fix any test that looked for `volume.mode.*` only if the identifier moved (keep the identifiers).
- [ ] **Step 5: Commit** `feat(ios): Plan carousel shows This week and Goal progress`.

### Task 3: Day row — two pills, no wash

**Files:**
- Modify: `UphillAI/Core/Plan/WorkoutPresentation.swift`
- Modify: `UphillAI/Features/Plan/DayRow.swift`
- Test: `UphillAITests/Plan/WorkoutRowTests.swift`

**Interfaces:**
- Produces: `enum RowStatus { case done, missed, matched, none }` and `WorkoutPresentation.rowStatus(for: Workout) -> RowStatus`

- [ ] **Step 1: Write the failing tests:** completed + matched → `.matched`; completed only → `.done`; missed → `.missed`; planned → `.none`.
- [ ] **Step 2: Run** `ios-native/scripts/test.sh -only-testing:UphillAITests/WorkoutRowTests`. Expected: FAIL, `rowStatus` not found.
- [ ] **Step 3: Implement `rowStatus`.**
- [ ] **Step 4: In `DayRow`:**
  - Pills per session row: the type chip (`chipLabel`) and, when `rowStatus != .none`, one status pill ("Done", "Missed", "Matched" with the watch or heart symbol as today). Nothing else is a capsule.
  - "TODAY": shown once, as the day label in `UH.Palette.accentInk` (`UH.TextStyle.eyebrow`), not a capsule. Remove the other two "TODAY" capsules (lines ~157 and ~247).
  - "PRIORITY" → a `star.fill` symbol before the title, `accessibilityLabel("Coach's pick")`. "2 SESSIONS" → plain text after the day label ("· 2 sessions"). "SWAP" stays reachable from the context menu and the session sheet; remove the capsule.
  - Background: `UH.Palette.card` (today: `UH.Palette.activeFill`), no `LinearGradient`. Border 1 pt always. Keep the 4.5 pt zone stripe.
  - Delete `matchedActivityBadge` and `matchedMetrics` from the row (they move to the sheet in Task 5; keep the identifier `workout.<id>.matched` on the status pill).
  - Replace the 19 `.system(size:)` fonts with `UH.TextStyle` tokens.
- [ ] **Step 5: Run** `ios-native/scripts/test.sh`. Expected: PASS.
- [ ] **Step 6: Commit** `feat(ios): day rows carry type and status only`.

### Task 4: Coach card one message; "Read this week"

**Files:**
- Modify: `UphillAI/Features/Plan/CoachReviewCard.swift`
- Modify: `UphillAI/Features/Plan/PlanView.swift` (knowledge card label at ~line 289)
- Modify: `UphillAI/Resources/Localizable.xcstrings`
- Test: `UphillAITests/Plan/CoachReviewCardTests.swift`

- [ ] **Step 1: Write the failing test** in `CoachReviewCardTests`: the card's content model exposes exactly one message line for a week with a brief, a welcome and a priority workout (the priority line wins over takeaways; welcome wins in week 1). If the card has no pure content function yet, extract `CoachReviewCard.message(for:) -> String?` first and test that.
- [ ] **Step 2: Run** the suite; expected FAIL.
- [ ] **Step 3: Implement:** the card shows that one message and a "Read the full review" text button (≥ 44 pt, opens `WeekReviewSheet` via `onOpenReview`). Remove the expand/collapse state and its chevron; `initialExpanded` goes (update callers, including `PlanAuditScreenshots`). Fonts → tokens.
- [ ] **Step 4:** In `PlanView` the knowledge-card eyebrow "COACH'S PICK THIS WEEK" becomes "Read this week" (VI "Đọc trong tuần này"), in `UH.TextStyle.eyebrow`. `CoachReviewCard`'s own "Coach's pick" wording stays (it names the workout).
- [ ] **Step 5: Run** `ios-native/scripts/test.sh`. Expected: PASS.
- [ ] **Step 6: Commit** `feat(ios): coach card says one thing; knowledge card reads "Read this week"`.

### Task 5: Session sheet order

**Files:**
- Modify: `UphillAI/Core/Plan/WorkoutDetailContent.swift`
- Modify: `UphillAI/Features/Plan/WorkoutDetailSheet.swift`
- Test: `UphillAITests/Plan/WorkoutDetailContentTests.swift`

**Interfaces:**
- Produces: `WorkoutDetailContent.about: String?` (Why + Benefit + Caution joined as short paragraphs, nil when all empty) and `WorkoutDetailContent.fuelingLine: String?`.

- [ ] **Step 1: Write the failing tests:** `about` joins reason, benefit and warning in that order and is nil when all are empty; `fuelingLine` is the trimmed tip or nil.
- [ ] **Step 2: Run** `-only-testing:UphillAITests/WorkoutDetailContentTests`; expected FAIL.
- [ ] **Step 3: Implement** both properties.
- [ ] **Step 4: Reorder the sheet:** header numbers (duration, distance, zone, pace) → the done action ("Mark as done", or "Log how it felt" once done, identifier `detail.markDone` kept) → steps, with `fuelingLine` as the last line inside the step timeline → matched-run details (moved from `DayRow`, same metrics line and source attribution) → COROS send → one "About this session" `DisclosureGroup`, collapsed, holding `about` and the coach quote. Delete `fuelingTipSection`, `cautionCalloutSection` as separate blocks (keep `detail.fuelingTip` and `detail.cautionCallout` identifiers on their new text if a test uses them). Replace the 48 `.system(size:)` fonts with tokens; drop decorative symbols in section headers.
- [ ] **Step 5: Run** `ios-native/scripts/test.sh`. Expected: PASS.
- [ ] **Step 6: Commit** `feat(ios): session sheet — numbers, done, steps, then the rest`.

### Task 6: Remaining type tokens and symbols; screenshots

**Files:**
- Modify: `UphillAI/Features/Plan/PlanView.swift`, `WeekSwitcher.swift`, `KnowledgeCard.swift` (the Plan-screen files not covered above). Sheets not on the Plan screen (`ManagePlanSheet`, `MoveSwapDaySheet`, `ExportCalendarSheet`, `NextWeekSheet`, `WeekReviewSheet`) stay out of scope.
- Modify: `UphillAITests/Plan/PlanAuditScreenshots.swift`

- [ ] **Step 1:** `grep -n "font(.system(size" ` over the files this plan touched returns nothing. Remove `comingSoonBadge` if unused after Task 1.
- [ ] **Step 2:** Every `Image(systemName:)` left on the Plan screen carries meaning (status, source, priority, chevron, toolbar). Decorative ones (section-header sparkles, card-corner icons) go.
- [ ] **Step 3:** Extend `PlanAuditScreenshots` with `plan-calendar-<lang>`, `session-sheet-<lang>` and `day-row-double-today-<lang>` (Review Focus 3), plus one run with `SCREENSHOT_DARK=1` and one at `.accessibility3` Dynamic Type for the first screen in VI (Review Focus 4).
- [ ] **Step 4: Capture before/after:** run the screenshot suite on `main` and on the branch with `SCREENSHOT_DIR=docs/evidence/plan-view-distill/{before,after}`; read every image; one fix round at most.
- [ ] **Step 5: Run** `ios-native/scripts/test.sh`. Expected: PASS.
- [ ] **Step 6: Commit** `chore(ios): Plan screen type tokens, meaningful symbols, before/after screenshots`.

## Out of scope

Web Plan screen (its own spec later); the five sheets listed in Task 6; any backend or copy change beyond the four new strings and the week line.
