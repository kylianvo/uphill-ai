---
name: Uphill AI
description: Mountain imagery, emerald identity and readable glass workspaces.
colors:
  workspace-accent: "#19ce8b"
  workspace-accent-ink: "#08764f"
  workspace-button-ink: "#063e2b"
  brand-emerald: "#19ce8b"
  brand-lime: "#a2d13c"
  workspace-ink: "#172b26"
  workspace-secondary: "#455c52"
  workspace-muted: "#5d7167"
  workspace-line: "#dce5df"
  workspace-active: "rgba(25,206,139,.16)"
  workspace-active-ink: "#08764f"
  workspace-hover: "#edf5f0"
  workspace-background: "rgba(243,246,244,.4)"
  workspace-glass: "rgba(255,255,255,.84)"
  science-glass: "rgba(255,255,255,.88)"
  landing-surface: "#f8faf8"
  landing-ink: "#111827"
  white: "#ffffff"
typography:
  body-family:
    fontFamily: "Plus Jakarta Sans, sans-serif"
  science-display:
    fontSize: "clamp(32px, 4vw, 52px)"
    lineHeight: 1.12
    letterSpacing: "-.03em"
  workspace-title:
    fontSize: "28px"
    lineHeight: 1.2
    letterSpacing: "-.025em"
  science-title:
    fontSize: "24px"
    lineHeight: 1.3
    letterSpacing: "-.025em"
  reading-body:
    fontSize: "16px"
    lineHeight: 1.85
  tool-description:
    fontSize: "14px"
    lineHeight: 1.7
  control-label:
    fontSize: "13px"
    fontWeight: 600
rounded:
  topic-link: "6px"
  control: "8px"
  workout-day: "10px"
  workspace-panel: "12px"
  landing-panel: "16px"
  pill: "9999px"
spacing:
  compact: "8px"
  small: "12px"
  regular: "16px"
  medium: "20px"
  section: "24px"
  panel: "28px"
  reading: "32px"
  column: "48px"
components:
  button-primary:
    backgroundColor: "{colors.workspace-accent}"
    textColor: "{colors.workspace-button-ink}"
    rounded: "{rounded.control}"
    padding: "10px 20px"
  button-secondary:
    backgroundColor: "rgba(0, 0, 0, 0.06)"
    textColor: "#111111"
    rounded: "{rounded.control}"
    padding: "10px 20px"
  calendar-scope:
    backgroundColor: "#f3f6f4"
    rounded: "{rounded.workout-day}"
    padding: "4px"
  calendar-scope-selected:
    backgroundColor: "{colors.workspace-glass}"
    textColor: "{colors.workspace-accent-ink}"
    rounded: "{rounded.topic-link}"
    padding: "8px 20px"
    typography: "{typography.control-label}"
  tool-card:
    backgroundColor: "{colors.workspace-glass}"
    textColor: "{colors.workspace-ink}"
    rounded: "{rounded.workspace-panel}"
    padding: "28px"
  chat-input:
    backgroundColor: "rgba(255, 255, 255, 0.85)"
    textColor: "#000000"
    rounded: "{rounded.pill}"
    padding: "10px 14px"
  road-pb-grid:
    backgroundColor: "rgba(255,255,255,.7)"
    rounded: "{rounded.workspace-panel}"
  road-pb-cell:
    padding: "18px 16px"
  race-detail-dialog:
    backgroundColor: "{colors.white}"
    rounded: "20px"
    padding: "24px"
    width: "min(720px, calc(100vw - 32px))"
  race-detail-action:
    rounded: "10px"
    padding: "10px 14px"
    height: "44px"
---

# Design System: Uphill AI

## Overview

**Creative North Star: "Readable training over the mountain"**

Uphill AI retains its mountain video, emerald identity and translucent white glass surfaces. The workspace places readable training information over that setting; science uses the same material for longer reading. The public landing page also contains opaque pale panels and open editorial rows, so glass is a shared material rather than a requirement for every container.

This is a source-backed record of the current implementation, not a new visual identity. The north-star wording describes the approved mountain, glass and readability commitments; it is not an additional user-selected brand metaphor. Scope: the app shell, training workspace, matched activities, science page and existing landing styles. Source authority is `Workspace.module.css`, `TrainingWorkspace.module.css`, `MatchedActivityCard.module.css`, `Science.module.css`, `LandingPage.module.css`, `ComparisonSection.module.css`, `globals.css` and `layout.tsx` under `frontend/src`.

**Key Characteristics:**
- Mountain video behind translucent, blurred working surfaces.
- Dark emerald controls and forest ink in the workspace; bright emerald remains in the global brand palette.
- Compact controls, distinct workout days and tabular metric numerals.
- Larger public-page typography and more measured science reading.

## Colors

### Primary

The original light green (#19ce8b) is restored for primary controls, selected weeks, icons and accents at the user’s request. Dark green remains for readable small labels and keyboard outlines.

### Secondary

Brand lime is the existing global secondary accent, including the avatar gradient. It does not replace emerald in the redesigned workspace controls.

### Neutral

Workspace ink, secondary and muted text are forest-toned neutrals. The workspace line token separates days and metrics. Workspace glass and science glass have different opacity; the science veil further calms the mountain background. Landing surface and landing ink describe public-page panels and the dark closing section.

## Typography

The body font actually installed by `layout.tsx` is Plus Jakarta Sans, exposed through the legacy `--font-outfit` variable, with Latin and Vietnamese subsets and weights 400, 500, 600 and 700. JetBrains Mono is installed under `--font-mono`; the sampled calendar and activity metrics use tabular numerals rather than requiring a mono face.

The frontmatter records observed science display, workspace title, science section title, reading body and control roles. Workspace titles range from 26px in the planner to 28px in tools; the planner falls to 22px below its mobile breakpoint. Tool titles use 19px and weight 650; activity values use 24px, falling to 22px in narrow containers. These intermediate weights are declarations, not evidence of separately loaded font files.

The public hero has a larger scale (clamp(44px, 6.6vw, 96px), line height 1.06) and changes to clamp(40px, 7.8vw, 60px) on mobile. Its declared `--font-schibsted` alias, like legacy `--font-inter`, is unresolved in the sampled source. This font drift is recorded, not made a normative display-family token. Fustat is requested in the document head, while the global `--font-fustat` alias currently points to the body font.

## Layout

The app content has a maximum width of 1240px with 32px interior padding, reducing to 16px at 800px. Working panels generally use 28px padding, dropping to 16px in the planner and 22px in tools. Tools use a single column of action rows at every width. Starter prompts use two columns and become one column at that breakpoint.

The scheduler's week navigation uses compact repeated controls; day surfaces have separate boundaries. Weekly calendar content can scroll horizontally on mobile and keeps a minimum board width of 770px. The scroll container is keyboard-focusable and includes a bilingual mobile scroll cue. This is a scheduler-specific behavior, not a global page-width rule.

Science has a 1200px container with a 230px sticky topic column and a flexible article column separated by 48px. At 800px it becomes one column with wrapping topics. Article paragraphs use a maximum of 72ch; About uses 70ch. Matched activity metrics use three columns and switch to two at a 480px container width.

The landing hero uses a 1092px inner width; the comparison section reaches 1120px. Public-page sections use more generous spacing and independent responsive composition. Their open rows should not be inferred to be glass cards.

Race history (web panel and native screen) stacks its blocks in one column: road personal bests, trail summary, linked profiles, the pending-confirmation block, then the race list. The web road-PB grid uses four columns and becomes two at 560px; native always uses two flexible columns. Pending rows put the result and its actions side by side and stack them at 560px. The web race detail dialog is at most 720px wide with a 16px viewport margin, scrolls internally within the dynamic viewport height, and reduces its 24px header and body padding to 20px at 480px. Native opens the same detail as a pushed screen with 16px padding.

## Elevation & Depth

Glass, background blur and fine borders provide most workspace depth. Planner, day, tool and About surfaces use 24px blur; app navigation uses 20px. Science combines 24px blur with a fixed mountain video and a pale translucent veil. The app navigation retains a soft shadow; many content cards explicitly remove shadows. Selected calendar controls carry a small shadow.

Public screenshots and comparison panels retain larger diffuse shadows. Exact shadow and motion values live in the sidecar. App control color feedback uses 160ms ease. The app's reduced-motion override reduces animation and transition duration and resets scrolling; landing reveal effects have their own reduced-motion handling. Public-page entrance motion is not a prescription for app controls.

## Shapes

Workspace panels commonly use the panel radius, with smaller day, control and topic-link radii inside. Existing chat containers retain a 16px radius and the top navigation retains a pill silhouette. Landing coach and closing panels use 16px corners; landing process and tool rows have square open edges. There is no single radius applied to every surface.

Fine borders define workspace containers; metric values are separated by bottom rules instead of additional nested tiles. Icons remain inline SVG in the actual component system.

## Components

Completed watch activities use a compact native disclosure, collapsed by default with distance, duration, heart rate, match status and source attribution visible. Suggested matches start expanded to keep confirmation discoverable. Full metrics and match actions remain inside the disclosure.

### Buttons

Workspace primary controls use light green and dark forest text; secondary controls retain the lightly tinted global treatment. Both inherit 10px by 20px padding and use 8px corners in the app shell, with a minimum height of 38px. App focus outlines use dark emerald with a 3px offset. Legacy hover translation remains in global button rules; it is not prescribed as the workspace motion language.

### Inputs / Fields

The existing chat field is white translucent glass with a fine dark border, pill corners and 12px blur. Its focus border uses the scoped accent. Coaching textareas enlarge the text to 16px with line height 1.6. Other forms are not normalized by this record.

### Navigation

Desktop navigation uses a translucent pill container. Workspace tabs have 8px corners, a minimum height of 42px and tinted emerald active states. Mobile navigation retains a blurred bottom surface. Science topics use compact links with a tinted hover/focus treatment; mobile topics wrap instead of remaining sticky.

### Chips / Segmented Controls

Calendar scope options use a grouped pale track, compact padding, 6px option corners and a glass selected option with emerald text. This represents a selection control, not a rule to style every label as a badge.

### Cards / Containers

Tool cards combine 28px padding, 12px corners, fine borders and glass. Hover changes the border to emerald and lightens the surface. Workout days use 10px corners, 16px padding and 12px separation. Science article sections use 12px corners and 32px padding, reducing to 24px by 20px on mobile.

### Matched Activity

Matched activities group the planned workout and recorded activity vertically. The recorded card uses a pale green glass surface and flat metric cells with tabular numerals, bottom borders and a responsive three-to-two-column grid. Supporting comparisons remain smaller than the measured values.

### Race History

Sources: `RaceHistoryPanel.tsx`, `RaceDetailDialog.tsx`, `RaceCourseContext.tsx`, `RaceHistory.module.css`, `RaceDetail.module.css` and `lib/raceHistory.ts` under `frontend/src`; `Features/RaceHistory` and `Core/RaceHistory/RaceDisplay.swift` under `ios-native/UphillAI`.

**Road personal bests.** Four fixed distances in order: 5 km, 10 km, HM, FM (native spells out Half marathon and Marathon). On web they sit in one bordered, pale-glass strip with 12px corners, divided by hairlines rather than separate tiles. Each cell has a 12px secondary label, a 24px semibold (650) tabular time and a 12px secondary date or status line. Native draws each distance as its own training card (panel radius, 16px padding) in a two-column grid, with a metric-style time and a filled medal symbol in the selected ink when a result exists. A cell with no result shows an em dash and "No confirmed result" and is disabled. A cell with a result opens that race's detail.

**The One List Rule.** Confirmed races appear in one reverse-chronological list. Road and Trail are shown as a small label on each row, not as a filter. Web rows use the existing collapsible result row with pill badges for source and discipline. Native rows are training cards showing name, tabular time, and a date · distance · discipline · source line.

**Pending confirmation.** Imported VBM results that are not yet confirmed appear only in a separate block ("Confirm your VBM results", with a count badge) above the list. They never appear in the race list or count toward personal bests. Each row has a quiet "View details" control and a primary "This is my result" action at least 44px tall. Native shows each pending result as a training card with a primary button and removes the date the race name repeats.

**Race detail.** On web this is a modal `<dialog>` that returns focus to the control that opened it. It has a white surface, a 20px radius, a dark forest backdrop at 55% opacity, and a header with a 24px title (22px on mobile) beside a 44px close control. The body starts with a date · discipline · source line and an "Awaiting confirmation" notice for unconfirmed results. Next comes a two-column definition list: finish time, recorded distance, recorded elevation gain, and overall, gender and age-group rank as "#rank / total" with a "Top n% of the field" note (left out for DNF). Then come location, bib, PB key, average pace, the source link, notes and source-specific actions: edit or delete for manual results, confirm or reject for VBM. A "Race Review" section, separated by a top rule, holds the comparison with the previous finish, the course context and the historical field. Action buttons are outlined, with 10px corners and a minimum height of 44px. Native shows the same content order on a pushed screen: a training card for the recorded result, then notes, actions and Race Review.

**Course context.** This is a fact list inside Race Review, not a card. It starts with the course name and distance label, followed by location and course elevation gain. When the course profile is from a different edition, a tinted notice states both years; when the edition is unknown, a line says so. Terrain, key climbs, typical conditions and runner reviews follow as short headed groups, and only when they have data. A footer gives the source label, verification date and source links (named by host). If the course is ambiguous, the block lists candidate courses as full-width buttons. If it is unavailable, it shows Retry. Both states say the race record stays the same.

**The Recorded-Result Rule.** Review content, course context and every error describe or explain the athlete's recorded result; they never alter it. Error copy names the failure, says the recorded result is unchanged and offers Retry when retrying helps (for example, "Couldn't load the race review. Your recorded result is unchanged."). On web each message is a `t(en, vi)` pair shown in an alert region. Errors are never shown as a raw HTTP status.

**The App-Language Number Rule.** Counts and metres use the app language, not the device region. Web uses `formatNumber` (en-US or vi-VN grouping), and native uses `RaceDisplay.number` (en_US or vi_VN, 0–1 decimal places). Distance is rounded to one decimal place and written as "n km". Pace is written as m:ss /km, rounding once before splitting so the seconds never show 60. Times are h:mm:ss, and DNF replaces the time.

## Do's and Don'ts

### Do:
- Do retain the mountain video, emerald identity and glass material confirmed in PRODUCT.md.
- Do distinguish workspace tokens from global and landing tokens when extending a surface.
- Do preserve visible keyboard focus and reduced-motion behavior.
- Do retain the weekly planning context when extending scheduler views.
- Do keep unconfirmed imports in their own confirmation block, outside the race list and personal bests.
- Do write race-history errors as bilingual sentences that say the recorded result is unchanged.

### Don't:
- Don't promote the workspace radius or compact type scale into a universal landing-page rule.
- Don't replace readable glass panels with unfiltered text over the video.
- Don't treat legacy font aliases as evidence that their named fonts are installed.
- Don't reintroduce a Trail/Road filter on the race list; discipline is a label.
