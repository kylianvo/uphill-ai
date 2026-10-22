# A quieter Plan screen (iOS first)

Status: draft, 2026-10-23. Source: brainstorm `~/.claude/plans/help-me-inspect-my-wild-nova.md`, topic C. Follows `2026-10-21-plan-view-coach-design.md` ("one message at a time, no badges").

## Job

The Plan screen shows the same things two or three times and puts up to six pills on a day row. Make it show fewer, quieter things. Not a new visual style.

## Constraints that stay

- Emerald identity, existing typography.
- Web keeps its glass and mountain video (PRODUCT.md / DESIGN.md).
- Taste rules that apply: one border style, ≤ 12 pt corners, no gradients on content, colour only for meaning, generous spacing.
- No backend change.

## Changes (files under `ios-native/UphillAI/.../Plan`)

1. **Repeats**
   - Goal: header pill, race card and goal card → keep only the goal card (`GoalPathRow`/`GoalPlanCheckCard` stay; header Goal pill goes).
   - Race name, date, time to go: drop the race card; the header keeps "N weeks to go".
   - "Adapt Week N": carousel pill and separate pill → one action.
   - "Coach's pick": the knowledge card (`KnowledgeCard.swift`) becomes "Read this week"; the other two uses keep the name.
2. **Carousel** (`SummaryCarousel.swift`): 5 cards → 2 (This week, Goal progress). Week volume and phase go into the week header as one line: "Week 6 · Build · 7.5 h · 52 km".
3. **Day row** (`DayRow.swift`): at most 2 pills (type, status). Drop the gradient wash; keep the 4.5 pt zone stripe. "TODAY" once. Matched-run details move to the session sheet.
4. **Coach review card** (`CoachReviewCard.swift`): one message plus "Read the full review" (opens `WeekReviewSheet`).
5. **Session sheet** (`WorkoutDetailSheet.swift`, `WorkoutDetailContent.swift`): order numbers → steps → done; "Mark as done / Log how it felt" at the top; Why, Benefit, Caution merged into one "About this session" fold; fueling becomes a line inside the steps.
6. **Type and icons:** the 24 hard-coded font sizes and hand-made eyebrows → the 8 `UH.TextStyle` tokens. Cut decorative SF Symbols (53 in Plan today); keep those that carry meaning.

## Copy

New strings in EN and VI (`uphill-ai-vietnamese-copy` skill): "Read this week", "Read the full review", "About this session", the week header line.

## Proof

- Simulator screenshots before and after: Plan list, calendar, session sheet, coach card, in EN and VI (extend `PlanAuditScreenshots.swift`).
- Existing Plan unit/UI tests updated, not deleted, where content moved.

## Later

Same cuts on web, as its own spec.
