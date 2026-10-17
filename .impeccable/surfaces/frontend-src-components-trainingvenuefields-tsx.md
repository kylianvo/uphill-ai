---
version: 1
slug: "frontend-src-components-trainingvenuefields-tsx"
primary_target: "frontend/src/components/TrainingVenueFields.tsx"
related_targets: []
---

# Trail preferences

Scope: shared web and native iOS Trail preferences in setup and schedule editing. Operate mode. Runners specify practical Trail access without understanding training configuration. Keep home terrain, saved API fields and all scheduler rules unchanged.

## Direction contract

THESIS: Ask access, place and days in order, revealing relevant answers instead of presenting a configuration block.

OWN-WORLD: Inherit Uphill's emerald selection, forest text, fine rules and existing web glass/native form controls. One column, no nested cards or new visual identity.

STORY: Answer Trail access. Yes reveals the place picker; choosing a catalog place or Other reveals weekdays. No clears Trail place, days and minimum in the draft. Existing answers reopen visibly. Stairs and available Treadmill settings form a separate alternatives section.

FIRST VIEWPORT: A compact Trail heading, numbered functional question and two choices. Place and weekdays follow vertically. Coach sets duration by default; a quiet disclosure exposes the optional minimum override and a reset to the location default. Saved minima are summarized even while collapsed. Controls fit mobile with 44px targets.

FORM: User-selected progressive form, code-led, local extension of the established workspace. Seed key: not applicable; narrow user-specified sequence.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Built state and evidence

This ordinary UI extension retains the incumbent system. Web uses the existing emerald selection, inherited typography, 8px control corners, fine borders and translucent fields; native uses `UH.Palette`, `UH.TextStyle`, `UH.Space` and `UH.Radius` with standard SwiftUI controls. The form remains one column: access → place → days, Coach duration with a collapsed optional minimum override, then stairs and treadmill alternatives. Interactive targets are at least 44px. Selecting no access clears the existing Trail draft fields.

Source checked: `TrainingVenueFields.tsx` and its module stylesheet, `TrainingVenueSection.swift`, and their callers `AdaptWeekModal`, `ScheduleFieldsEditor`, native `ScheduleEditor` and `SetupSteps`. This records a local form composition; it adds no reusable system rule or API, schema or scheduler change.

Visual evidence checked: `.impeccable/review/{desktop,mobile,duration-mobile,no-access-mobile,focused-mobile,focused-desktop}.png`; `docs/evidence/trail-session-content/ios-trail-{guided,duration,no-access}-vi.png` and their `-dark-large-vi.png` counterparts. These are local screenshots of synthetic UI data, not new shipping image assets. The focused desktop/mobile captures show the numeric field retaining its pale surface and visible emerald outline. The fresh finish review's follow-up disposition was ship at that resolved focus-fix scope.

`PRODUCT.md`, `DESIGN.md` and `.impeccable/design.json` remain unchanged. Pre-existing documentation drift remains: DESIGN's key-characteristics line calls controls dark emerald while its primary-color section and the sidecar describe restored light green; sidecar narrative rules are paraphrases of DESIGN rather than verbatim. Neither discrepancy is adopted as a new rule or repaired by this surface extension.
