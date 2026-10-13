# Race History: results, personal bests, and course review

Date: 13 October 2026
Status: Draft for user review; implementation has not started.

## Purpose and agreed scope

Help an athlete collect their actual race results, understand their personal bests, and revisit a race with context from the curated race KB. Native iOS is the primary experience because the production report came from that app; the existing web panel must expose equivalent result-management and detail behavior.

The user requested manual entry and result links, a tappable race detail with ranking/performance/location, and a race review showing KB context. COROS activity linking, COROS PB import, watch metrics, and watch-derived analysis are excluded from this expansion. Existing COROS integrations elsewhere in the product continue operating. The upstream request for COROS personal records is https://github.com/coroslab/COROS-MCP/issues/16.

Design assumption for review: the first Race Review is a deterministic presentation of recorded results, comparisons, athlete notes, and curated course facts. It makes no new LLM calls. A generated Coach debrief is a separate future feature, rather than a prerequisite for useful course context.

## Observed starting point

- Production has imported VBM FM/HM results with `selected=false`; the backend intentionally excludes these from its summary.
- The web panel has a pending-VBM selector; the Swift screen lists pending results as ordinary races and offers only deletion, although deletion is supported only for manual results.
- Native `DistanceBadge.deriveBadges` excludes `hidden` results, while the backend defines `hidden` as exclusion from Coach text only.
- Native badges currently pick the fastest finish within broad distance categories, mixing road and trail results under a PB heading.
- `race_results` already stores bib, source URL, overall/gender/age-group rank pairs, notes, country, and import provenance. Manual requests currently expose only a subset.
- The race KB contains terrain, location, typical climate, key climbs, runner observations, edition metadata on some courses, source information, and optional historical results/course profiles.
- The current matcher may select a benchmark from another distance if none matches. The new review must filter structured KB data directly and must not reuse that fallback.

## Repository and execution boundary

This document and its plans are saved in `/Users/vietvo/Documents/antigravity/uphill-ai`, inspected at `9ca0429` on `codex/mobile-navigation-motion`. This checkout does not contain `ios-native/`.

Native source was inspected read-only at `/Users/vietvo/.codex/worktrees/ios-native-phase2b/uphill-ai`, commit `3e44d24`, branch `ios/shoe-rotation-and-prod-fixes`. That checkout contains existing modified screenshots owned by other work. Backend code on that branch also differs from this checkout. During execution, use an isolated worktree based on the native-containing integration branch, bring these planning files into it, and preserve newer backend behavior there, including goal-outcome reconciliation hooks. Do not reset either inspected checkout or copy its unrelated uncommitted files. Task paths below are repository-relative to that integration worktree.

## Global constraints

- Native targets iOS 18.0 or newer, Swift 6.0, and complete strict concurrency; retain the existing SwiftUI design system and dependency set.
- Web uses Next.js 16.2.7 App Router with static export; read installed Next.js documentation before App Router changes and retain the existing dependency set.
- Backend uses FastAPI, Pydantic, SQLAlchemy Core, and parameterized SQL against PostgreSQL; add no runtime dependencies.
- Every schema change must appear in both `backend/db.py:init_db()` and a handwritten Alembic migration, including idempotent upgrades for existing dev databases.
- Preserve existing API response keys; new response fields are additive and optional when decoded by older clients.
- All result reads and writes are owner-scoped; coach reads require the existing athlete-access authorization and expose no write actions.
- English and Vietnamese web copy must follow the Uphill Vietnamese-copy skill; native uses the existing English copy convention without adding a localization subsystem.
- Screenshot evidence from a running web app and iOS simulator is required for rendered changes; unit tests or static renders alone are insufficient.
- COROS and new LLM calls are excluded from this feature scope; no automatic production data repair or deployment is part of implementation.

## Phase A: result management and PB correctness

### A1. Confirm imported VBM results

Show a separate **Confirm your VBM results** section above the selected-race list. Each pending result has an explicit **This is my result** action. Confirming sends the existing owner-scoped PATCH `{selected: true}`. A selected VBM result has **Not my result**, which sends `{selected: false}` and returns it to pending. Selection remains an athlete decision; neither `is_pr` nor matching bibs silently selects a result. Sync preserves the selection flag.

Selected-race counts and road/trail filters operate only on selected rows. Pending rows remain inspectable from their confirmation section. Imported records offer source links and VBM selection actions; **Delete result** is available only for manual records, with confirmation. UTMB unlink remains the supported way to remove that imported profile.

An in-flight mutation disables its controls. A failed write retains the prior state, displays an inline error, and permits retry. A failed subsequent refresh does not claim that displayed stats are current. Native refreshes Race History and the Me page after a successful mutation and when returning to Me. Profile syncing polls every 5 seconds only while the screen is visible and a claim is pending; navigation/disappearance cancels polling.

### A2. Manual create, edit, and attach a link

Use a single manual-result form in add and edit modes. Required fields: name, local calendar date, discipline, positive distance, and positive finish duration unless DNF. Optional fields: elevation, location, bib, result URL, overall/gender/age-group rank and field-size pairs, and notes. Empty optional numeric fields save `null`, including elevation; never prefill an invented 2,200 m climb or 6:30 finish.

Manual entries stay `source=manual`, selected by default. A URL is supporting evidence, not proof of identity or automatic verification. Saving a link does not fetch or scrape that URL. Imported timing, distances, ranks, bib, and source URLs remain read-only; athlete notes and Coach-text exclusion remain editable.

Limits: name 200 characters; location 200; bib 100; notes 2,000; URL 2,048. Trim strings; empty optional strings become null. URL must be an absolute HTTP(S) URL with a host and no embedded credentials. Unknown fields are rejected. Explicit null cannot clear required fields or selection/hidden booleans. Optional fields can be cleared during edit.

Distance is finite, greater than 0, and at most 1,000 km. Elevation is finite and nonnegative when present. Each rank/total is a positive integer; rank cannot exceed total when both exist. A rank without a total can be stored but has no percentile. DNF clears the stored finish time. Validate the fully merged manual result on every manual PATCH, including edits of rank, elevation, or optional metadata alone.

Persistence: add only `race_results.location TEXT NULL`. Existing columns hold every other field. Imported location can come from course context without overwriting the result. Preserve nullable legacy rows.

### A3. Road PBs and distance achievements

The backend is authoritative for **Road personal bests**. Add `summary.road_prs` with keys `5k`, `10k`, `hm`, `fm`, each null or the existing PR shape `{result_id, time_sec, date, stale}`. Keep `road_hm_pr` and `road_fm_pr` as aliases to the corresponding entries. Eligibility: selected, road, finished, positive time. `hidden` affects Coach text only. Use distance tolerance strictly less than 0.1 km for 5K, 0.2 km for 10K, and 0.5 km for HM/FM. Choose lowest time, then latest date, then lowest result ID for ties. Old PBs remain visible with their date; stale is informational, not exclusion.

Keep the seven existing distance achievement categories separately, with the current category distance ranges for compatibility. They show completed/locked and the latest eligible finish name/date, rather than a fastest-time PB across incomparable courses. Both road and trail finishes can unlock achievements; DNF and pending results cannot. Remove the native `hidden` eligibility check. Label the section **Distance achievements** and the four road cards **Road personal bests**.

The FM road card must show the confirmed road marathon time even when a trail marathon has a different time. Tapping an unlocked road card or achievement navigates to its underlying result once Phase B is available; Phase A continues opening Race History.

## Phase B: race detail and KB review

### B1. Race detail

Tap a selected race card to open a full detail screen (iOS navigation push; accessible web dialog). Pending VBM cards have a View details action but are clearly marked **Awaiting confirmation**. Show the full race name, race date, discipline, result distance/elevation, finish/DNF, bib, source, safe source link, notes, and available rank pairs.

Add owner route `GET /api/race-history/results/{result_id}/detail` and coach route `GET /api/coaching/athletes/{athlete_id}/race-history/results/{result_id}/detail`. Both return the detail contract below; missing/unowned results return 404. Coach route uses `require_athlete_access` and then scopes the result to `athlete_id`. Presentation is read-only for coaches.

Actual-result location takes precedence over matched-KB location. Label the fallback **Course location (KB)**. Unknown fields show a short unavailable state or are omitted; never display zero for missing ranks, elevation, or duration.

Field position is `100 * rank / total`, rounded to one decimal for display as **Top X% of finishers**. Only calculate for a finished result with `1 <= rank <= total` and a known total. This is a finish-position fraction, not a time percentile. Each gender/age-group fraction uses its own denominator. Invalid imported ranks are shown as unavailable rather than turning into a percentage.

Road average race pace can be calculated from recorded time/distance and labeled **Average race pace**. For trail, keep the recorded duration and course demands visible, without judging performance by raw pace. Do not infer pacing, fatigue, heart-rate behavior, actual weather, or nutrition from a finish time.

### B2. Course context

Resolve against `kb_chunks` domain `race_courses`, kind `race_profile`. Reuse existing name normalization/scoring thresholds through a small public matcher adapter; do not alter Scheduler/Goal matcher behavior. Automatic match requires score >= 86, a >= 10 score gap, same road/trail race type, and a distance entry within 15% of the recorded distance. A close name alone is insufficient. Ambiguous matches expose up to five compatible candidates; the athlete can select one for the current detail view using `?course_id=<chunk id>`. A supplied course ID must belong to those compatible candidates or be the automatic match; otherwise return 422. The choice is not persisted in this release.

Render structured KB fields: location, terrain, distance-specific elevation, key climbs, typical climate, and published runner observations. Name their provenance and display source links when `source_urls` exist; otherwise show `source_label`. Legacy runner observations without individual citations are labeled **Curated runner observations**, with the available KB attribution, never invented as direct athlete quotes.

Return course-edition status `same`, `different`, or `unknown`. `edition_year` equal to result year gives same; a different integer gives different; missing gives unknown. A different or unknown edition is visibly labeled. Keep result distance/elevation separate from KB profile distance/elevation. Typical climate is labeled as typical and never reported as the conditions on the athlete's day.

Missing/empty KB, incompatible distance/discipline, or insufficient matching confidence leaves the result usable and returns an unavailable course-context state. A KB query failure returns `unavailable` with a retryable message; do not turn it into a successful empty review. Never introduce a KB distillation run or seed edits as part of a detail read.

### B3. Race Review

Race Review is a section of detail containing:

1. **Your result:** completion/DNF, recorded rank position, road PB status when eligible, and the athlete's note.
2. **Previous finish:** compare to the most recent earlier selected finish with the same normalized name (or canonical KB race when confidently matched), same discipline, and distance within 1%. Show both dates, times, and signed duration difference (`current - previous`). A course-edition change is explicit; this is a time comparison, not a claim of improved fitness. Unknown course identity uses exact normalized names only. Hidden results count statistically, but hidden notes are omitted from the review narrative/context.
3. **Course demands:** curated terrain, climbing, and typical conditions from the matched KB.
4. **Historical field context:** only compatible distance-label statistics for the athlete's exact result year. No matching year means this section is unavailable; another year's winner or median must never appear as that athlete's field. Do not interpolate a missing athlete percentile from sparse historical time percentiles.

Unknown races still receive Your result and a comparison when safe. DNF has no PB, field-position fraction, or time-improvement claim. User notes remain distinguishable from recorded timing and curated facts.

### Detail response contract

```typescript
type RaceDetail = {
  result: RaceResult; // existing row shape plus nullable location
  performance: {
    overall_top_pct: number | null;
    gender_top_pct: number | null;
    age_group_top_pct: number | null;
    average_pace_sec_km: number | null;
    road_pb_key: "5k" | "10k" | "hm" | "fm" | null;
  };
  previous_finish: {
    result_id: number; race_date: string; finish_time_sec: number;
    delta_sec: number;
  } | null;
  course_context: {
    status: "matched" | "ambiguous" | "missing" | "unavailable";
    candidates: { id: number; race_name: string; distance_label: string }[];
    course: {
      id: number; race_name: string; distance_label: string;
      distance_km: number; elevation_gain_m: number | null;
      location: string | null; terrain: string[]; key_climbs: string[];
      climate: { avg_temp_c?: number; humidity_pct?: number | string;
                 season?: string; notes?: string };
      runner_reviews: string[]; source_label: string | null;
      source_urls: string[]; verified_at: string | null;
      edition_year: number | null;
      edition_status: "same" | "different" | "unknown";
    } | null;
    message: string | null;
  };
  historical_field: Record<string, unknown> | null;
};
```

`historical_field` preserves the curated exact-year row shape (year, distance_label, distance_km, winner_time, finishers, percentiles, and source fields where present); clients render only known numeric/time fields with safe attribution and treat absent fields as absent. No raw imported provider payload or unrelated account data is added to this response.

## Release acceptance

- A synthetic VBM FM at 3:39:14 and HM at 1:44:04 starts pending; confirming both produces those road PBs and updated Me cards; no production account is changed by tests.
- Rejecting a VBM result removes its statistical contribution and survives provider refresh.
- Manual create/edit/delete works with absent elevation, DNF, metadata clearing, ranking-only edits, and safe URL links.
- An imported result has no delete action and its recorded fields cannot be edited through the manual form.
- Hidden finished races still count in PBs and achievements; hidden notes are not inserted into the review context.
- Unauthorized owner/coach detail requests return the existing authorization outcome without leaking result metadata.
- A 2024 result matched to a 2026 course clearly labels the edition difference; no 2026 winner statistic is described as the 2024 field.
- Unknown/ambiguous races, failed KB reads, partial rankings, and malformed source links have useful, visible states.
- iOS simulator and web screenshots cover pending/confirmed results, manual editing, road PB plus trail achievement, matching/mismatched/missing KB detail, and errors.

## Delivery sequence

Phase A plan: `docs/superpowers/plans/2026-10-13-race-history-results.md`.

Phase B plan: `docs/superpowers/plans/2026-10-13-race-history-review.md`. It consumes Phase A's metadata and road-PB contract. No automatic deployment is requested; backend additive changes can ship before new clients after review.

User amendment (2026-10-13): show one confirmed race list without Trail/Road filters. Keep discipline labels and discipline-specific calculations; pending VBM confirmation stays separate. This supersedes earlier filter requirements.
