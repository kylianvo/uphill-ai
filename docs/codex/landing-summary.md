# Landing redesign status — 9 October 2026

## What changed

Landing branch rebased onto origin/main at 06d96cf. Existing local work preserved. No commit, push or PR.

The hero device composition is removed at the user's request. The native iOS Plan header now appears in “Your week, ready to run”. Mountain video and emerald/Plus Jakarta Sans brand remain. COROS integration uses the supplied activity-watch photograph, isolated from the adjacent phone with a contour matte derived from its original pixels. Full case and crown are visible; display values remain illustrative manufacturer content, not the fictional athlete's results. No native watch-app claim or logo beneath the watch.

Native app captures cover plan builder, Plan header, Adapt Week, Coach and the four race tools. Web monthly calendar remains the broad calendar overview. Tool panels now pair existing bilingual feature copy with native screens. Gear Vault shows real generated shoe recommendations from the committed catalog, including Salomon Genesis. The empty local gear knowledge base was populated from committed gear.json (105 chunks) in localhost:5543 only; no schema or non-local database edits.

Coach is a real native recording of “I am busy this Saturday, help me change my training plan”. Idle waiting was trimmed; the actual reply is unchanged. Animated WebP is rebuilt at 780 pixels wide directly from original recording frames, with a static PNG under reduced motion. The requested pause/replay control and recording/watch captions are removed. Other native WebP screenshots are rebuilt at 780 pixels wide from 1206-pixel originals. Mountain video continues behind lower content; the former mountain-video button and requested screenshot titles are removed.

All landing sections, comparison/pricing copy, AuthModal/BetaDownloadModal flows and native-platform redirect remain. SHOW_PROOF_CONTENT=false. The seed runner is fictional example data.

## Screenshot and media list

- ios-plan-week2: native Plan header, week 2, example Elephant 50 race on 9 January 2027.
- ios-plan-builder: native builder.
- ios-adapt-week: native Adapt Week.
- ios-coros-workout: native COROS-matched workout.
- ios-coach-saturday: real native Coach recording, shortened waiting time, still fallback.
- ios-goal-determiner: real native Goal settings with corrected race date.
- ios-pace-strategy: native Pace settings, 56.4 km, 2,946 m gain, example 11-hour target.
- ios-nutrition-lab: native Nutrition settings.
- ios-gear-vault: native recommendations showing actual shoes; source ios-gear-shoes-raw.png.
- web-calendar-month: real web monthly calendar.
- coros-activity: isolated supplied activity-watch photo with full case/crown.
- mountain-poster: frame from the existing background video.

WebP plus PNG assets total 1,417,493 bytes, below 1.5 MB; see final-asset-manifest.json. No new dependencies.

## Validation

- npx tsc --noEmit: passed.
- npm run lint: passed, 0 errors, 128 warnings (repository-wide warnings).
- npx vitest run: 63 files, 505 tests passed; previous timeout failures cleared after rebase and a standalone run.
- npm run build: static export passed.
- Native iPhone 18 Pro build/launch and actual shoe capture verified.

Latest checks saved in docs/codex/evidence/verification-revision-*.log: TypeScript, lint (0 errors, 128 warnings), 505 tests and static build all pass.

## Final polish and evidence

Phase 5 complete. Final captures are in docs/codex/evidence/landing-final-{en,vi}-{390,768,1440}-{motion,reduced}.jpg (12 full-page screenshots). Browser checks for each capture are in landing-final-checks.json: no horizontal overflow and no unloaded images in all 12 variants.

Verified the simplified hero, native Plan section, actual gear shoes, Coach recording and full COROS watch case/crown. Beta download modal opens and closes; keyboard focus has a visible 3px outline. Browser console has no errors. /science, /privacy and /support return 200.

Reduced motion pauses the mountain video and selects the Coach PNG still. The original macOS Reduce Motion setting (off) and default browser viewport were restored after verification.

Polish corrected the Vietnamese workflow subtitle to match the English training-block wording. Small green links now use #076442: 4.71:1 against #cdd2cf, the darkest possible composite of the #f5faf7d6 video overlay over black. Body copy is 5.42:1 or higher at that same worst-case background; emerald CTA text is 5.91:1. Brand emerald #19ce8b is unchanged.

Final checks: TypeScript passed; lint passed (0 errors, 128 repository-wide warnings); 63 test files / 505 tests passed; static export passed. Logs are verification-polish-*.log.

## Open questions / capture limits

No blockers remain. Goal, Pace and Nutrition captures show actual configuration states; Gear shows actual catalog shoe recommendations. Screens are in English on both language versions; surrounding copy and alt text are bilingual. Watch display values come from the supplied photograph and are illustrative, not the fictional athlete's results. No product UI or race results were invented.

The reviewed landing changes are prepared for commit and a pull request. Native Coach recording was captured on 06d96cf, before the later iOS proposal-card fix in e0fd721; it remains a real recording, but does not demonstrate that new Apply-card UI.
