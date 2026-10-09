# Uphill AI landing audit and proposed direction

Phase 0 only. Prepared 9 October 2026. No application code, seeded data, pricing or comparison content changed. Implementation waits for approval.

## Scope and evidence

- Target: `claude/landing-page-redesign-codex-2d6105`, checkout `.claude/worktrees/landing-page-redesign-codex-2d6105`. The chat's initial cwd was on `codex/mobile-navigation-motion`; that checkout was left untouched.
- Authority: this checkout's `PRODUCT.md` and `DESIGN.md`, current landing source, current native screenshot fixtures, and the supplied brief. The context launcher initially ran from the chat cwd, where those documents were absent; the correct checkout's documents were subsequently read directly. No context files were created or rewritten.
- Method: independent Impeccable assessments A (design review) and B (detector/browser evidence), plus taste-skill's redesign audit. Persuade mode. Source findings and live observations are distinguished below.
- Live baseline: Next.js 16.2.7 at `http://127.0.0.1:18081`, EN at 1440 × 900 and 390 × 844, with a VI mobile spot-check. Existing locked packages were installed with `npm ci`; no dependency or lockfile additions. Read `frontend/AGENTS.md` and the installed Next static-export and server/client guides.
- Layout reference: [Kotcha](https://www.kotcha.com/en), consulted for device-family storytelling only. Its claims, photography, colors, copy and section layouts are not material for this build.
- No backend, simulator build, database seed, Gemini request or external lead submission was needed for Phase 0. Native fixtures are evidence of current visual direction, not approved final marketing assets.

### Baseline screenshots

| Surface | Desktop | Mobile |
|---|---|---|
| Hero | [1440](evidence/audit-b-desktop-hero-1440.png) | [390 EN](evidence/audit-b-mobile-hero-390.png), [390 VI](evidence/audit-b-mobile-hero-vi-390.png) |
| How it works | [1440](evidence/audit-b-desktop-steps-1440.png) | [390](evidence/audit-b-mobile-step-390.png) |
| Coach | [1440](evidence/audit-b-desktop-coach-1440.png) | [390](evidence/audit-b-mobile-coach-390.png) |
| Tools | [1440](evidence/audit-b-desktop-tools-1440.png) | [390](evidence/audit-b-mobile-tools-390.png) |
| Comparison | [1440](evidence/audit-b-desktop-comparison-1440.png) | [390](evidence/audit-b-mobile-comparison-390.png) |
| Closing | [1440](evidence/audit-b-desktop-closing-1440.png) | [390](evidence/audit-b-mobile-closing-390.png) |

These are the incumbent page, not redesign previews. Below-fold captures were scrolled into view so entrance effects settled; initial full-page captures with hidden reveal targets are not valid visual evidence.

## 1. What to keep

1. **The brand contract.** Emerald `#19ce8b`, forest ink, Plus Jakarta Sans, the mountain video and readable glass. Keep the logo and wordmark. Glass belongs on navigation, device staging and selected panels, with quieter opaque surfaces behind dense text.
2. **A runner's actual workflow.** Profile/thresholds → plan → train/log/adapt → review/next block is useful content. Preserve all four jobs and the weekly-planning emphasis; make current screens prove them.
3. **Science as support.** Keep the methodology/book acknowledgement and `/science` links with their existing deep links. Position them after visitors understand the product. Existing author acknowledgements are not endorsements of the app.
4. **Coach and race preparation.** Keep Coach Uphill, Pace Strategy, Goal Determiner, Gear Finder and Nutrition Lab. Emphasize a useful training decision rather than RAG terminology.
5. **Comparison exactly as approved.** Preserve `ComparisonSection`, factual content, source links, desktop table and mobile disclosures. No pricing change or new commercial claim.
6. **Honest integration status.** COROS is the available watch integration. Preserve explicit limits around unsupported integrations. The proposed watch represents a structured workout sent to COROS, never an Uphill watch app.
7. **Working behavior and accessibility wins.** Native-platform redirect and one-shot guard; `/app` authentication path; BetaDownloadModal; bilingual controls; semantic links/buttons; keyboard outlines; dialog Escape/focus restoration; visible-by-default reveal fallback and reduced-motion handling.
8. **No invented proof.** Keep `SHOW_PROOF_CONTENT = false`. Completion values from the preview athlete are example data, not testimonials, product usage or athlete achievements.

## 2. Critique: what to cut or merge

The strongest opportunity is to show one believable training plan moving across devices. The incumbent has mountain atmosphere and a clear training subject, but could still be mistaken for a general AI coaching site because the first viewport contains no product interface.

| Priority | Finding and evidence | Proposed response |
|---|---|---|
| P1 | **The hero does not show the product family.** At both widths it leads with a general headline, subtitle, three actions and two grounding statements. Native iOS and usable COROS workouts are invisible. | Stage a real web planner, real native Plan tab and a clearly captioned COROS workout illustration together. One download action and one web action. Keep science reachable through navigation and supporting sections. |
| P1 | **Product images are stale and shrink beyond usefulness on mobile.** The legacy planner depicts a DUT 100km mock-style layout; current native fixtures show a different forest/glass interface. At 390 the desktop screenshots become small, dense thumbnails. | Recapture all product visuals. Use native portrait screens and focused authentic web crops on mobile; device frames must never substitute for readable content. |
| P1 | **VI has meaning and length drift.** The mobile VI heading wraps to four lines; its subtitle is much longer than EN. TrustBanner adds “100%” in VI. Other source examples: EN process repeats per block while VI says per week; VI closing promises a 16-week plan absent from EN. | Rewrite only approved landing copy with exact EN/VI parity. Use the Vietnamese copy skill: plain club-runner register, retain AeT/AnT, Plan, Long Run, ME and other community terms. Remove added guarantees and superlatives. |
| P1 | **The primary action promises a plan but lands on Tools in the audited session.** Clicking “Start Training Plan” reached `/app` with the Tools heading; source initializes the active tab to `tools`. | Use the brief's honest “Open web app” label for that route and beta download as the primary action. Preserve authentication behavior. A direct Scheduler destination must use a supported existing entry point; do not invent a query parameter or change AppContext outside scope. |
| P1 | **Bright emerald display text falls below large-text AA on the pale hero.** `#19ce8b` measures 2.05:1 against white and 1.95:1 against the pale landing surface. | Keep bright emerald identity/button fills, but set display text in forest ink or readable dark emerald. Target at least 3:1 for large text and 4.5:1 for body/controls across footage states. |
| P2 | **The page explains its grounding repeatedly before showing the everyday benefit.** The source-authority section sits between the training process and Coach; the hero already has two science/trust statements. | Relocate methodology after the product features and integration story. Consolidate grounding explanation into supporting copy and source links. Keep acknowledgements and their content unless a specific cut is approved. |
| P2 | **The visual rhythm repeats.** Four consecutive process splits, numbered step labels, image rectangles and repeated science links make the product tour feel procedural. Desktop headings also separate large headlines from small right-column prose. | Use at least four composition families: multi-device hero, wide planner stage, native phone/detail pair, focused adapt panel, phone-led Coach, and one race-tool stage. Stack section headings and short descriptions; alternate devices without alternating the identical layout five times. |

### Proposed cuts and merges, subject to approval

- Retire the legacy product screenshot usages. Do not delete unrelated public assets in this phase or use generated UI replacements.
- Merge the hero's physiology label and TrustBanner message into one concise science statement lower down. Preserve the TrustBanner component/behavior where needed; do not retain absolute “never hallucinated” or VI-only “100%” claims as design decoration.
- Remove the hero's third Science action from that action cluster; retain `/science` in navigation, feature links, methodology and footer.
- Remove numbered “Step 01–04” ornamentation while preserving the four process jobs and deep links.
- Standardize download wording across header, hero and close. The existing beta flow is the verified destination; do not invent an App Store URL.
- Keep all landing sections in the conservative proposal below. No section deletion is needed. Shortening the book/author passage or removing roadmap badges is a separate approval, not assumed by approval of visual direction.

### Taste-skill audit

**Reading this as:** a consumer landing-page redesign for trail and ultra runners, using mountain imagery, emerald accents and readable glass, with authentic devices carrying the evidence.

**Mode:** redesign preserving brand/product/content while replacing the product presentation. Native CSS/CSS Modules and existing Phosphor icons; no new design system or motion package.

**Current dials (qualitative):** `DESIGN_VARIANCE 5`, `MOTION_INTENSITY 5`, `VISUAL_DENSITY 6`. The open hero is offset, but the long process and authority passages repeat and increase reading burden. **Proposed:** `7 / 3 / 4`: stronger device composition, subtle reveals/parallax only, shorter feature copy. The existing atmospheric video is retained; moving footage is still disabled under reduced motion.

Observed/source anti-template findings: four consecutive zigzag process rows; repetitive numbering and small metadata labels; duplicate grounding statements; too many hero actions; desktop split section headings; decorative floating book treatment; a dark closing panel interrupting the pale surface language; em-dash-heavy landing copy; stale product thumbnails. Brand exceptions are explicit: emerald and glass remain, Plus Jakarta Sans remains, CSS/SVG device frames are requested, and the watch illustration is the sole permitted illustrated product display.

Keep a coherent pale/forest page world. A dark watch display is device content, not a page-theme change. Use brand glass selectively rather than giving every section another frosted card. Scale the headline alongside the device stage instead of letting display type consume the hero.

### Independent Impeccable design assessment

Assessment A: `/root/design_critique`; completed without detector output. Assessment B: `/root/technical_audit`; findings withheld until A returned. Both used fresh browser tabs and the required widths.

| # | Nielsen heuristic | Score / 4 | Principal finding |
|---|---|---|---|
| 1 | Visibility of system status | 3 | Locale, integration status and disclosures are clear; beta submitting state exists in source. |
| 2 | Match with the real world | 2 | Runner language coexists with unexplained AeT/AnT, RAG, KB, ME and load terminology. |
| 3 | User control and freedom | 3 | Disclosure collapse and beta Escape/focus restoration verified. |
| 4 | Consistency and standards | 2 | Three labels describe the same beta destination; header and hero CTA treatment differ. |
| 5 | Error prevention | 2 | Required/email fields exist; broad integration wording and absolute claims create expectation risk. |
| 6 | Recognition rather than recall | 2 | Mobile header hides start/download actions during a long scroll. |
| 7 | Flexibility and efficiency | n/a | Expert accelerators are not relevant to this Persuade surface. |
| 8 | Aesthetic and minimalist design | 2 | Readable spacing with repeated reassurance and long reading passages. |
| 9 | Error recovery | 2 | Source validation exists; registration network failure advances to downloads without explaining that registration failed. No form submission was tested. |
| 10 | Help and documentation | 3 | Science links are useful, but immediate setup/download expectations are less clear. |
| | **Total** | **21 / 36** | Qualitative assessment of the incumbent landing and beta entry, not product reliability. |

**Cognitive load:** moderate, with three checklist failures: competing hero decisions, mixed product/AI-reliability/authority tasks, and partial progressive disclosure. **Emotional journey:** calm mountain opening → useful training-loop evidence → long authority reading valley → product features → demanding comparison → strong close → beta-form effort.

**Personas:** a first-time visitor must decode training and AI terms; a distracted mobile runner loses nearby start actions and cannot read miniature screenshots; a skeptical experienced runner sees lineage but insufficient current-product evidence for unconditional claims.

Assessment A measured a 13,702px mobile page, with the next start action near y=13,006 after the hero, and a roughly 1,967px default-open comparison alternative. These are the inspected EN state's values, not fixed layout constants. Mobile process imagery was about 324px wide. Preserve comparison content and its current disclosure defaults; any change to comparison behavior needs separate approval.

The beta modal asks for four required fields before showing download choices. This audit records the acquisition friction but does not propose changing requirements, form order or submission behavior within the visual rebuild. Improve path labels first and retain the existing flow.

### Source/technical baseline

- Page source references `/screenshots/*` for all legacy product visuals. The Step 2 alt text describes a next-block modal although its image is the planner. Coach and tool alts are currently hard-coded English.
- `layout.tsx` loads Plus Jakarta Sans through `--font-outfit`, while many landing display declarations request unresolved `--font-schibsted`. Scope the correct brand face in allowed landing CSS; no layout edit is required for that repair.
- Existing screenshots are roughly 96–200 KB each; `bg.mp4` is about 15 MB on disk. The new-image allowance does not remove video loading/decode cost. Retain the video and prioritize the product LCP asset; no measured CWV score is claimed from a dev-server audit.
- Global/root issues needing separate permission: `html lang="en"` regardless of locale, and viewport settings disabling user zoom in `layout.tsx`. They are not landing-only fixes and will not be silently edited.
- Preserve current routes and anchor IDs: `#how-it-works`, `#methodology`, `#coach`, `#tools`, `#comparison`, plus the current `/science#...` links. `/privacy` and `/support` flows must remain available; this audit does not rewrite those routes.
- SEO baseline: current title is “Uphill AI | Science-Backed Trail & Mountain Coaching”; existing metadata description stays. No search-ranking measurement, route migration, structured-data addition or OG change is proposed.

### Independent detector and browser findings

The detector ran once over `page.tsx` and `components/landing`: exit 2, **one warning** (`side-tab`, “Side-tab accent border”, `page.tsx:1033`, `borderLeft: "4px solid"`). Manual context identifies a conventional `blockquote` accent, not a generic card flourish; treat it as a contextual false positive, not a redesign priority. The scan did not identify the stale screenshots, claim drift or mobile legibility problems; a low finding count is not a visual pass.

- Settled document heights: 9,157px desktop EN, 13,702px mobile EN, 14,024px mobile VI. Mobile comparison occupied roughly 4,227px. Preserve its content and defaults unless separately approved.
- No horizontal document overflow: desktop client/scroll width 1434/1434; mobile 384/384. The requested viewport widths were 1440 and 390, with six pixels consumed by the scrollbar.
- All ten images loaded when reached. Process screenshots displayed around 324px from 1360px source on mobile; Coach around 302px. Tool images are eager-loaded despite being below the fold; change those to lazy loading during the approved rebuild.
- Primary CTA text/background pair measured 5.91:1; dark green links against white measured 5.65:1. Those pairs are strengths. Transparent surfaces over changing footage still need complete contrast review in Phase 5; these spot checks do not certify the whole page.
- Normal motion played a fixed continuous video with no local pause control. Observed first video transfer was 15,899,045 bytes. Reduced motion paused both videos and removed reveals, but sources were still assigned/decoded. Propose an accessible video pause control and a real static video-frame fallback for reduced motion; defer footage behind the product LCP asset. Do not modify `public/bg.mp4` outside the allowlist.
- Keyboard focus was visible on logo, locale controls and CTAs. Beta modal trap, Escape, focus restoration and scroll-lock cleanup worked. Science target IDs were checked in source; no complete authenticated plan-creation flow or beta submission was tested.
- Locale controls were 36px high and some science links 18–19px high; increase touch areas within landing styles while keeping visible hierarchy quiet.
- Local console showed analytics CORS failures against staging from port 18081. Treat this as a dev-environment limitation, not proof of a production defect. Do not change analytics configuration during the landing audit.

No live detector overlay is available. Mutable-injection preflight succeeded and was restored, but the overlay helper's durable state/HTML injection was skipped under the user's file allowlist. CLI results plus actual viewport captures are the fallback evidence. Target slug: `frontend-src-app-page-tsx`; no critique ignore list was present. No helper overlay server was started. The temporary frontend server was stopped and the root/design-review IAB tabs were closed after inspection. Standard `.impeccable/critique` persistence is outside the allowlist, so this document is the permitted critique archive; no separate snapshot/trend history was written. Installed Impeccable is v4.4.0; the launcher reported v4.5.1 available, and the skill was not updated during this audit.

The existing `.gitignore:61` rule `docs/*` ignores this audit and its evidence. They exist locally and are linked here; adding them to a later commit will require explicit staging despite that rule. No `.gitignore` edit, commit or push was performed.

## 3. Proposed section order and real-shot mapping

This is a proposal, not authority to remove sections or alter comparison content. Each visual row uses one focal screen; supporting screens only where they explain the same task.

| Order | Section/job | Real screenshot and composition |
|---|---|---|
| 1 | **Hero: understand the product and choose phone or web.** | `web-plan-week-1440` in a laptop; `ios-plan-week2` in an iPhone; watch illustration from the same seeded workout, explicitly “Syncs to COROS”. |
| 2a | **Build a plan around your race, thresholds and time.** Within `#how-it-works`. | `web-plan-builder-1440`: actual populated builder form, not a generated fake form; wide laptop stage, short copy above. |
| 2b | **See the week and the weeks ahead.** Preserve the current plan step's job. | `ios-plan-week2` + `ios-workout-long-run`; optional `web-calendar-month-1440` supporting crop. Phone-led close-up with readable Saturday Long Run. |
| 2c | **Adapt when the week changes.** | `web-adapt-week-1440` (390 crop when needed), actual feeling/constraints state; focused glass panel rather than another full laptop. |
| 2d | **Review and plan the next block.** Preserve the fourth process job. | `web-week1-review` or actual next-block controls. Show real seeded completion state; no fabricated evaluation grade, AI verdict or athlete result. If a real review is unavailable, retain explanatory content without inventing a screenshot. |
| 3 | **Ask Coach Uphill about the next climb.** `#coach`. | `ios-coach-vht` as the main portrait screen; `web-coach-vht-1440` available for a readable desktop crop. Actual answer to one real VHT training question. |
| 4 | **Prepare for the course.** `#tools`; retain all four tools. | `web-pace-vht-1440` as the main wide tool visual; actual `ios-goal-vht`, `ios-gear-result`, `ios-nutrition-result` close-ups as supporting tool rows. Each must be a current capture if rendered. No invented finish/result data. |
| 5 | **Carry the structured workout onto COROS.** Existing integration section, moved earlier. | `ios-coros-workout-detail`/`ios-coros-synced-workout` beside the same clearly identified watch illustration. Distinguish outbound workout sync from imported completed activity matching. |
| 6 | **Show the training foundation and authors.** `#methodology`. | Existing real book image and acknowledgements; no product screenshot required. Preserve the passage and source links unless a specific shortening is approved. |
| 7 | **Help the visitor compare options.** `#comparison`. | Existing `ComparisonSection`, unchanged content and native responsive table/disclosures; no screenshot needed. |
| 8 | **Choose an app surface and start.** Existing closing section. | Reuse hero phone asset if a product visual helps; same beta-download action and “Open web app” secondary intent. No new illustration or claim. |
| 9 | **Footer: science, account, legal and support paths.** | Existing wordmark and link behavior; no product visual. |

The hidden proof slot stays hidden and does not acquire a visual substitute. Calendar and review remain parts of the training story, not extra equal-sized feature-card grids.

## 4. Hero composition sketches

### Desktop, 1440 × 900

```text
┌────────────────────────────────────────────────────────────────────┐
│ Uphill.AI                         language     download / web       │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ Short, two-line headline         ┌──── LAPTOP: real web week ─────┐ │
│ One sentence about the plan      │ race header / calendar         │ │
│ across web, phone and COROS.     │ consistent example training    │ │
│                                 └────────────────────────────────┘ │
│ [Get beta app]  Open web app           ┌── iPHONE ──┐               │
│                                      │ native Plan │    ╭────────╮ │
│                                      │ Week 2      │    │ COROS  │ │
│                                      └─────────────┘    │workout │ │
│                 Mountain video + calm veil              ╰────────╯ │
│                             Example plan / watch illustration note │
└────────────────────────────────────────────────────────────────────┘
```

Use a text column around 40% and a device stage around 60%, not a symmetrical 50/50 card pair. Laptop behind, iPhone foreground, round sport-watch bezel beside it. Overlap bezels/empty margins only; never cover the race title, zone target or key workout. No stock frame artwork. Keep the download action visible within the first viewport and the composition useful at 1280 as well as 1440.

### Mobile, 390 × 844

```text
┌───────────────────────────┐
│ Uphill.AI          EN / VI │
│                           │
│ Concise headline          │
│ One short explanation     │
│ [Get beta app]            │
│ Open web app              │
│                           │
│       ┌── iPHONE ──┐      │
│       │real Plan   │      │
│       │week/race   │      │
│       │Long Run    │╭────╮│
│       │            ││zone││
│       └────────────┘╰────╯│
│ Example plan.             │
│ Syncs to COROS.           │
│ Watch display illustrated.│
└───────────────────────────┘
```

The laptop leaves the mobile hero; web remains visible in the following builder section. Phone first, watch overlapping its lower bezel, with no horizontal page scroll. At shorter heights allow the honest caption to follow the device stage; do not shrink product text or conceal the main CTA to force a fixed-height hero. Reserve all device aspect ratios before loading.

Draft CTA labels: EN “Get beta app” / VI “Tải app beta”; EN “Open web app” / VI “Vào app web”. Example label: EN “Example plan” / VI “Plan minh hoạ”. Watch label: EN “Syncs to COROS. Watch display illustrated.” / VI “Đồng bộ sang COROS. Màn hình đồng hồ minh hoạ.” Final headline/body wording will be reviewed for parity before implementation.

## 5. Screenshot shot list for Phase 2

All captures use the fictional `landing-preview@uphill.ai` athlete and the same VHT example. Web captures: 1440 × 900 CSS px at 2× (2880 × 1800 source), plus 390 × 844 at 2× where needed. iOS: iPhone 18 Pro simulator's native pixel size, recorded from the actual available simulator; light appearance, status bar 9:41/full battery. Exact simulator resolution must be verified, not guessed.

| Asset stem | Surface/device | Viewport | Required state and intended use |
|---|---|---|---|
| `web-plan-week-1440` | Web/laptop | 1440 × 900 @2× | Active 15-week VHT plan, Week 2, race header and useful weekday/weekend sessions. Hero. |
| `web-plan-builder-1440` | Web/laptop | 1440 × 900 @2× | Real plan builder prefilled with the preview athlete's thresholds, Saturday Long Run, time goal and race; no generation required for capture. |
| `web-plan-builder-390` | Web/mobile crop | 390 × 844 @2× | Same real builder in responsive form layout; crop only to the relevant inputs. |
| `web-calendar-month-1440` | Web/laptop | 1440 × 900 @2× | Actual month populated from seeded workouts, no empty demo grid or invented activity streak. |
| `web-coach-vht-1440` | Web/laptop | 1440 × 900 @2× | One submitted real VHT climb-preparation question and the actual response. Keep a useful excerpt with any source/context caveat; no rewritten screenshot reply. |
| `web-adapt-week-1440` | Web/panel | 1440 × 900 @2× | Adapt Week open for Week 2, real feeling and availability controls. Capture before committing changes unless an actual adapted result is requested. |
| `web-adapt-week-390` | Web/mobile panel | 390 × 844 @2× | Same state, controls readable on mobile; modal must be reached through the real UI. |
| `web-week1-review` | Web/panel | 1440 × 900 @2× | Week 1 mostly completed, actual review/next-block state. No synthetic letter grade or coach assessment. |
| `web-pace-vht-1440` | Web/laptop | 1440 × 900 @2× | Real Pace Strategy for the user-confirmed 56.4 km/2,946 m D+ course and the example time target; only genuine course checkpoints/profile or visibly identified model assumptions. |
| `ios-plan-week2` | Native iPhone | Actual iPhone 18 Pro | Plan tab, Week 2, race context and first workout(s). Hero and calendar story; avoid an expanded review pushing the workout off-screen. |
| `ios-workout-long-run` | Native iPhone | Same simulator | Saturday Long Run detail with target zone/HR, duration, D+, execution steps and fueling tip. |
| `ios-coach-vht` | Native iPhone | Same simulator | Actual Coach conversation with the seeded plan; capture an existing shared conversation if supported, otherwise submit a real question through the native app. |
| `ios-coros-workout-detail` | Native iPhone | Same simulator | Actual outbound structured-workout sync state where available; preserve labels and steps. Imported activity “Matched” alone is not proof of outbound sync. |
| `ios-coros-synced-workout` | Native iPhone | Same simulator | Native workout/card sync badge supported by local seeded integration data. Caption it as an example; no claim that a physical watch was connected or contacted. |
| `ios-goal-vht` | Native iPhone | Same simulator | Real Goal Determiner result using profile/plan inputs, no invented historical finish. |
| `ios-gear-result` | Native iPhone | Same simulator | Actual curated gear response if shown in the retained Gear Finder row; if KB is unavailable, do not invent a recommendation. |
| `ios-nutrition-result` | Native iPhone | Same simulator | Actual Nutrition Lab response for the preview race if shown in the retained nutrition row. |
| Watch display (no raster asset) | CSS/SVG sport watch | Responsive frame | Title, duration, target zone and steps read directly from one seeded structured workout. Caption “Watch display illustrated”; no recreated COROS firmware or Uphill watchOS interface. |

Shot states may be cropped from actual captures; cropping must not change UI, fabricate values, remove meaningful caveats or splice together different states. Keep fixture reference images separate from final capture assets. The existing `plan-redesign` fixtures guide shot selection; they currently show another example race and are not reused as Minh Trail's plan.

### Capture and delivery rules

- All final product rasters go to `frontend/public/landing/` as optimized WebP with PNG fallback. Keep raw audit/provenance evidence under `docs/codex/`; no screenshot tooling dependency additions.
- Reuse identical screens across placements. Treat **all new shipped images, including PNG fallbacks**, as part of the 1.5 MB budget. Proposed allocation: hero reused assets 300 KB; planning/adapt/review 400 KB; Coach 200 KB; tools/integration 450 KB; reserve 100 KB. These are targets, not measured outputs.
- Select focused native/detail crops for secondary tool visuals; don't ship every full 2× source capture. Preserve source captures as evidence. If legible real screens plus both formats cannot meet the budget with existing converters, report the conflict rather than silently dropping formats or raising the limit.
- Preload only the LCP product screen; lazy-load below-fold screens; set intrinsic dimensions/aspect ratios. Verify LCP/CLS after build. Video remains the existing asset, with readable static/reduced-motion treatment.
- Local-only seed guard, idempotence and user ownership must be verified twice in Phase 1. No Gemini calls in the seed. Never record its password in this document or screenshots.
- Keep personally identifying data/debug UI out of frames. “Minh Trail” is fictional and the completion/sync state is explicitly preview data. Do not overlay an example label inside the real product UI; caption outside the device.
- Final Phase 5 evidence matrix: 390/768/1440 × EN/VI × motion/reduced motion = 12 states. Verify actual page overflow, glass contrast, keyboard focus, download dialog, web/auth path and native redirect; do not treat screenshots alone as flow verification.

## Approval and open decisions

1. Approve or correct the device composition and conservative section reordering above. This preserves all current sections, tool coverage and comparison/pricing content.
2. **Race details confirmed by the user:** Elephant 50, **56.4 km**, **2,946 m D+**, **9 January 2027** (`2027-01-09`). These supersede the brief's original distance/elevation. With today (9 October 2026) in Week 2, a Monday start of 28 September 2026 puts race day on Saturday of Week 15. Use these values consistently in the local preview seed, tool inputs and screenshot captions. No seed has been run yet.
3. Use the existing beta-download destination until a verified native App Store listing is provided; an App Store label or URL will not be invented.
4. The existing VHT payload in `race_courses.json` records 55.4 km/3,200 m D+, which differs from the user's confirmed 56.4 km/2,946 m D+. Use the user's values for this showcase without modifying the KB outside the allowlist. Its `key_climbs` list is race-wide rather than proof of an Elephant 50 segment sequence. Phrase the actual Coach question about preparation for sustained climbs such as Langbiang; do not present an unverified segment map.
5. Existing E2E files under `frontend/tests/` pin legacy screenshot paths, hero exclusions and floating-book styling. Updating those tests is required if intended changes break them, but that directory is outside the edit allowlist. Ask before those edits; never delete tests to pass.
6. Root locale/zoom fixes are outside scope. Keep them recorded for separate permission rather than bundling them into the landing rebuild.

**Phase gate:** stop here. No seed, screenshot replacement, UI implementation, dependency addition, commit, push or PR until the user approves the next phase.
