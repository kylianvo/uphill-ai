# Race History Detail and KB Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give each race a tappable result detail and a review containing trustworthy field position, prior-finish comparisons, and attributed course KB context.

**Architecture:** A single owner/coach-scoped backend detail response combines recorded results with a strict adapter over existing KB matching. Pure functions calculate performance and filter exact-year benchmarks. Native and web render the same contract; no new generation job, watch sync, or stored review is introduced.

**Tech Stack:** FastAPI, SQLAlchemy Core/PostgreSQL, existing RapidFuzz matcher, pytest; SwiftUI, Swift Testing, XCTest; React/TypeScript, Vitest, Playwright.

**Spec:** `docs/superpowers/specs/2026-10-13-race-history-expansion-design.md`, Phase B and Global constraints.

**Dependency:** Implement `docs/superpowers/plans/2026-10-13-race-history-results.md` first. Its optional metadata, `compute_road_prs`, native result-management callbacks, and web `safeResultUrl`/shared types are consumed here. Phase A remains usable if this phase is not released.

## Global Constraints

- Native targets iOS 18.0 or newer, Swift 6.0, and complete strict concurrency; retain the existing SwiftUI design system and dependency set.
- Web uses Next.js 16.2.7 App Router with static export; read installed Next.js documentation before App Router changes and retain the existing dependency set.
- Backend uses FastAPI, Pydantic, SQLAlchemy Core, and parameterized SQL against PostgreSQL; add no runtime dependencies.
- Every schema change must appear in both `backend/db.py:init_db()` and a handwritten Alembic migration, including idempotent upgrades for existing dev databases.
- Preserve existing API response keys; new response fields are additive and optional when decoded by older clients.
- All result reads and writes are owner-scoped; coach reads require the existing athlete-access authorization and expose no write actions.
- English and Vietnamese web copy must follow the Uphill Vietnamese-copy skill; native uses the existing English copy convention without adding a localization subsystem.
- Screenshot evidence from a running web app and iOS simulator is required for rendered changes; unit tests or static renders alone are insufficient.
- COROS and new LLM calls are excluded from this feature scope; no automatic production data repair or deployment is part of implementation.

## Review Focus

1. A known race from 2024 matches a 2026 profile: label edition mismatch and suppress other-year field statistics. Task 1 and native/web detail tests cover it.
2. Nearly identical races or incompatible course distances: expose ambiguity or missing context rather than attaching a plausible wrong course. Task 1 covers close scores, distance, and discipline.
3. Imported rank missing a denominator, invalid rank, or DNF: return null position and display no fabricated percentile. Task 2 covers all conditions.
4. Another user/unauthorized coach requests a guessed result ID or course ID: enforce result ownership before enrichment; no metadata leak. Task 2 integration tests cover owner/coach and invalid course selection.
5. Race navigation changes during a slow fetch, or KB is offline: prevent stale detail from replacing the new race and leave recorded result available. Tasks 2–4 cover response state, cancellation, and retry.

## File map

| File | Responsibility |
|---|---|
| `backend/services/race_matcher.py` | Add public scored-chunk adapter without changing current matcher callers |
| `backend/services/race_review.py` (new) | Strict course matching, field position, prior finish, and exact-year KB projection |
| `backend/main.py` | Thin owner/coach detail routes |
| `ios-native/UphillAI/Core/RaceHistory/RaceDetailModels.swift` (new) | Detail Codable contract and presentation values |
| `ios-native/UphillAI/Core/RaceHistory/RaceDetailViewModel.swift` (new) | Detail fetch, cancellation, and retry |
| `ios-native/UphillAI/Features/RaceHistory/RaceDetailScreen.swift` (new) | Result, actions, and review presentation |
| `ios-native/UphillAI/Features/RaceHistory/RaceCourseContextView.swift` (new) | KB facts and provenance |
| `frontend/src/components/RaceDetailDialog.tsx` (new) | Accessible web detail dialog and fetch lifecycle |
| `frontend/src/components/RaceCourseContext.tsx` (new) | Structured KB rendering |

Use the same isolated native-containing integration worktree as Phase A. No new schema is needed in Phase B. Keep all queries in existing SQLAlchemy/helper patterns.

### Task 1: Build a strict course-context adapter and benchmark filter

**Files:**
- Modify: `backend/services/race_matcher.py`
- Create: `backend/services/race_review.py`
- Create: `backend/tests/unit/test_race_review.py`

**Interfaces:**
- Consumes `db.get_kb_chunks("race_courses", kind="race_profile")` at the orchestration layer, existing matcher `_score_chunks` and `_payload_as_dict` internally.
- Produces `score_race_course_chunks(name: str, chunks: list[dict[str, Any]]) -> list[tuple[dict[str, Any], float]]` in race_matcher.
- Produces `select_course_context(result: dict[str, Any], chunks: list[dict[str, Any]], course_id: int | None = None) -> dict[str, Any]`, with the spec's course_context shape; invalid explicit course raises `ValueError`.
- Produces `historical_field(payload: dict[str, Any], distance_label: str, distance_km: float, year: int) -> dict[str, Any] | None`.

- [ ] **Step 1: Add complete synthetic course/result fixtures and red tests.**

```python
from services import race_review

def course(cid=10, **changes):
    payload = {
        "race_name": "Mountain Trail", "aliases": ["MT"], "race_type": "trail",
        "distances": [{"label": "50 km", "distance_km": 50, "elevation_gain_m": 2200}],
        "location": "Mountain Town", "terrain": ["technical singletrack"],
        "key_climbs": ["Summit climb"], "climate": {"notes": "Typical cool mornings"},
        "runner_reviews": ["Curated observation"], "edition_year": 2026,
        "source_urls": ["https://example.org/course"], "verified_at": "2026-10-13",
        "results": [
            {"year": 2024, "distance_label": "50 km", "distance_km": 50,
             "winner_time": "4:00:00", "finishers": 100},
            {"year": 2026, "distance_label": "50 km", "distance_km": 50,
             "winner_time": "3:30:00", "finishers": 150},
        ],
    }
    payload.update(changes)
    return {"id": cid, "title": "Mountain Trail", "source_label": "Organizer", "payload": payload}

def result(**changes):
    row = dict(id=1, race_name="Mountain Trail", race_date="2024-06-01",
               distance_km=50, discipline="trail", selected=True, is_dnf=False,
               finish_time_sec=22000, hidden=False)
    row.update(changes)
    return row

def test_newer_course_profile_is_labeled_and_benchmarks_use_result_year(monkeypatch):
    chunk = course()
    monkeypatch.setattr(race_review, "score_race_course_chunks", lambda name, chunks: [(chunk, 100)])
    context = race_review.select_course_context(result(), [chunk])
    assert context["course"]["edition_status"] == "different"
    field = race_review.historical_field(chunk["payload"], "50 km", 50, 2024)
    assert field["winner_time"] == "4:00:00" and field["year"] == 2024
    assert race_review.historical_field(chunk["payload"], "50 km", 50, 2025) is None

def test_close_scores_require_choice_and_reject_unrelated_id(monkeypatch):
    a, b = course(10), course(11, race_name="Mountain Trail North")
    monkeypatch.setattr(race_review, "score_race_course_chunks", lambda name, chunks: [(a, 96), (b, 93)])
    context = race_review.select_course_context(result(), [a, b])
    assert context["status"] == "ambiguous" and context["course"] is None
    assert len(context["candidates"]) == 2
    assert race_review.select_course_context(result(), [a, b], 11)["course"]["id"] == 11
    import pytest
    with pytest.raises(ValueError):
        race_review.select_course_context(result(), [a, b], 999)
```

Add cases: same edition; unknown edition; below-86 top score; wrong discipline; 100 km result against a sole 50 km course; matching course with mismatching benchmark label; empty chunks; absent source URLs; a duplicate exact-year/distance benchmark yields unavailable rather than arbitrary first-row selection.

- [ ] **Step 2: Run `python -m pytest tests/unit/test_race_review.py -q`; verify missing functions cause red.**

- [ ] **Step 3: Expose scoring and implement the strict adapter.**

Add this public wrapper to `race_matcher.py`:

```python
def score_race_course_chunks(name: str, chunks: list[dict[str, Any]]) -> list[tuple[dict[str, Any], float]]:
    if not name or len(name.strip()) < _MIN_NAME_LENGTH:
        return []
    return _score_chunks(name.strip().lower(), chunks)
```

In race_review, import that wrapper and existing `_payload_as_dict`. The adapter must never call `_to_matched_race` or `race_benchmarks` because their fallback can attach another distance's benchmark. Define course compatibility and benchmark filtering as:

```python
import math
from typing import Any
from services.race_matcher import _payload_as_dict, score_race_course_chunks

def compatible_distance(result_km: float, entry_km: Any) -> bool:
    return (isinstance(entry_km, (int, float)) and not isinstance(entry_km, bool)
            and math.isfinite(entry_km) and entry_km > 0 and result_km > 0
            and abs(entry_km - result_km) / result_km <= 0.15)

def historical_field(payload: dict[str, Any], distance_label: str,
                     distance_km: float, year: int) -> dict[str, Any] | None:
    label = distance_label.strip().casefold()
    matches = [row for row in payload.get("results", [])
               if row.get("year") == year
               and (row.get("distance_label") or "").strip().casefold() == label
               and compatible_distance(distance_km, row.get("distance_km"))]
    return dict(matches[0]) if len(matches) == 1 else None
```

`select_course_context` starts with `{status:'missing', candidates:[], course:None, message:None}`. Score all chunks using the wrapper. Keep only matching `race_type` and compatible distance entries; pick the closest compatible entry per chunk. Sort compatible chunks by score descending then chunk ID. Top <86 gives missing; a top >=86 and compatible runner-up gap <10 gives ambiguity and up to five score>=70 candidates. A supplied course ID must be one of these candidates (or the automatic winner), otherwise raise ValueError. For multiple equally close distance entries with different labels, return ambiguity between courses only if possible; otherwise missing with “Course distance is ambiguous” rather than choosing a label by array order.

On match project exactly the spec's course fields from the chosen chunk and distance entry. `edition_status` is same/different only for an integer edition_year; otherwise unknown. Coerce absent location/source labels to null, absent lists to empty arrays. Keep only string list values; do not stringify arbitrary dictionaries into runner observations. Source URLs are filtered to absolute HTTP(S), no credentials; reuse Task A1's URL-validation rule without fetching. Keep typical climate fields only if their values match the detail contract. No user result fields are overwritten.

- [ ] **Step 4: Run pure matcher and review regressions.**

Run `python -m pytest tests/unit/test_race_review.py tests/unit/test_race_matcher.py -q`; expect PASS including existing Scheduler matcher tests. Use a mocked score wrapper for ambiguity tests and one unmocked exact-name test so the adapter really reaches existing scoring. Confirm `_to_matched_race` and existing matcher behavior have no semantic edits.

- [ ] **Step 5: Commit the three listed files with `git commit -m "feat: resolve race review course context safely"`.**

### Task 2: Add owner/coach detail and deterministic result review

**Files:**
- Modify: `backend/services/race_review.py`, `backend/main.py`
- Modify: `backend/tests/unit/test_race_review.py`
- Create: `backend/tests/integration/test_race_review.py`

**Interfaces:**
- Consumes existing `race_history.get_result(result_id, user_id)`, `list_results(user_id, include_unselected=False)`, `_dedupe`, `normalize_name`, `db.get_kb_chunks`, Phase A `compute_road_prs`, and Task 1 functions.
- Produces `top_position_pct(rank: int | None, total: int | None, is_dnf: bool) -> float | None`, `previous_finish(result: dict[str, Any], rows: list[dict[str, Any]], canonical_ids: dict[int, int]) -> dict[str, Any] | None`, and `build_detail(user_id: int, result_id: int, course_id: int | None = None) -> dict[str, Any] | None`.
- Produces GET owner/coach routes from the spec, accepting optional `course_id`; responses conform to the spec's RaceDetail contract. No review writes or schema change.

- [ ] **Step 1: Write field-position, comparison, and owner-scope regressions.**

```python
import pytest
from services.race_review import top_position_pct, previous_finish

@pytest.mark.parametrize("rank,total,dnf,expected", [
    (30, 100, False, 30.0), (1, 100, False, 1.0),
    (None, 100, False, None), (30, None, False, None),
    (101, 100, False, None), (0, 100, False, None), (30, 100, True, None),
])
def test_field_position_is_not_fabricated(rank, total, dnf, expected):
    assert top_position_pct(rank, total, dnf) == expected

def test_previous_finish_requires_safe_identity_and_comparable_distance():
    current = dict(id=2, race_name="City Marathon", race_date="2025-01-01",
                   discipline="road", distance_km=42.195, finish_time_sec=13154,
                   selected=True, is_dnf=False)
    prior = {**current, "id": 1, "race_date": "2024-01-01", "finish_time_sec": 14000}
    assert previous_finish(current, [prior], {})["delta_sec"] == -846
    assert previous_finish(current, [{**prior, "race_name": "Other City Marathon"}], {}) is None
    assert previous_finish(current, [{**prior, "distance_km": 21.0975}], {}) is None
    assert previous_finish({**current, "is_dnf": True}, [prior], {}) is None
```

API test creates a manual result through existing POST, then GET detail as owner and a second mock-login user; expect 200 and 404 respectively. Monkeypatch `db.get_kb_chunks` to throw and assert result still returns with course_context.status unavailable. Patch it to synthetic course chunks and assert valid choice succeeds while arbitrary course_id yields 422. For coach access, follow `backend/tests/integration/test_coach_roster.py`: mock-login the coach, call `db.set_user_is_coach(coach_id, True)`, `link = db.create_coach_invite(coach_id, athlete_id)`, then `db.accept_coach_invite(link['id'], athlete_id)`. Authorize the linked coach and reject a different coach before inspecting result metadata.

- [ ] **Step 2: Run `python -m pytest tests/unit/test_race_review.py tests/integration/test_race_review.py -q`; confirm expected missing-route/helper failures.**

- [ ] **Step 3: Implement pure performance/comparison functions and orchestration.**

```python
from datetime import date
from services.race_history import normalize_name

def top_position_pct(rank: int | None, total: int | None, is_dnf: bool) -> float | None:
    if is_dnf or type(rank) is not int or type(total) is not int or not 1 <= rank <= total:
        return None
    return round(100 * rank / total, 1)

def previous_finish(result: dict[str, Any], rows: list[dict[str, Any]],
                    canonical_ids: dict[int, int]) -> dict[str, Any] | None:
    if not result.get("selected") or result.get("is_dnf") or not result.get("finish_time_sec"):
        return None
    candidates = []
    current_course = canonical_ids.get(result["id"])
    for row in rows:
        same_name = normalize_name(row["race_name"]) == normalize_name(result["race_name"])
        same_course = current_course is not None and canonical_ids.get(row["id"]) == current_course
        if (row["id"] != result["id"] and row.get("selected") and not row.get("is_dnf")
            and (row.get("finish_time_sec") or 0) > 0 and row["race_date"] < result["race_date"]
            and row["discipline"] == result["discipline"] and (same_name or same_course)
            and abs(row["distance_km"] - result["distance_km"]) / result["distance_km"] <= 0.01):
            candidates.append(row)
    if not candidates:
        return None
    prior = sorted(candidates, key=lambda row: (row["race_date"], row["id"]), reverse=True)[0]
    return {"result_id": prior["id"], "race_date": prior["race_date"],
            "finish_time_sec": prior["finish_time_sec"],
            "delta_sec": result["finish_time_sec"] - prior["finish_time_sec"]}
```

Implement `build_detail` in this order:

1. Owner-scoped `get_result`; return None before any KB lookup if absent.
2. Read selected rows once, dedupe them for PB/comparison, and compute PRs with `date.today()`. `road_pb_key` is the key whose result ID equals this result; pending/DNF yield null.
3. Fetch KB chunks once. On an exception log the error type without result/account payloads and set unavailable/message “Course context could not be loaded. Retry.”; do not swallow invalid explicit IDs.
4. Resolve context and validate explicit IDs. Build canonical IDs only for unambiguous compatible automatic matches; a user-selected compatible current course may identify that current row. Unknown/ambiguous prior rows use exact normalized names only.
5. Build performance rank fractions independently for each rank pair; road average pace is time/distance for a selected positive-time road finish, otherwise null. Compute previous_finish from the deduped selected rows.
6. When a course is matched, get its raw payload by ID from the already loaded chunks and use historical_field with result year, chosen label, and recorded distance. Do not consume course_intelligence.historical_results.
7. Return recorded result after removing `raw` and `user_id`, performance, previous_finish, course_context, and historical_field. Hidden notes are still editable/displayable in Your notes but excluded by clients from the Race Review narrative. Keep missing fields null.

Thin routes (import race_review alongside existing service imports):

```python
@app.get("/api/race-history/results/{result_id}/detail")
def get_race_detail(result_id: int, course_id: int | None = None,
                    user: dict[str, Any] = Depends(get_current_user)):
    try:
        detail = race_review.build_detail(user["id"], result_id, course_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    if detail is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return detail

@app.get("/api/coaching/athletes/{athlete_id}/race-history/results/{result_id}/detail")
def get_coach_race_detail(athlete_id: int, result_id: int, course_id: int | None = None,
                          acting_user: dict[str, Any] = Depends(require_athlete_access)):
    try:
        detail = race_review.build_detail(athlete_id, result_id, course_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    if detail is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return detail
```

- [ ] **Step 4: Exercise populated, ambiguous, missing, and unavailable response contracts.**

Run pure and integration tests, including the two owner/coach paths, pending result detail, hidden-note behavior, malformed imported ranks, multiple earlier editions, and manual metadata. Check JSON contains no raw provider data and no unrelated user ID. Run `python -m pytest tests/unit/test_race_review.py tests/unit/test_race_personal_bests.py tests/integration/test_race_review.py tests/integration/test_race_history.py -q`; expect PASS.

- [ ] **Step 5: Commit listed backend files with `git commit -m "feat: expose owner-scoped race details and review"`.**

### Task 3: Add native tappable detail and KB review

**Files:**
- Create: `ios-native/UphillAI/Core/RaceHistory/RaceDetailModels.swift`, `RaceDetailViewModel.swift`
- Modify: `ios-native/UphillAI/Core/RaceHistory/RaceHistoryService.swift`
- Create: `ios-native/UphillAI/Features/RaceHistory/RaceDetailScreen.swift`, `RaceCourseContextView.swift`
- Modify: `ios-native/UphillAI/Features/RaceHistory/RaceHistoryScreen.swift`, `ios-native/UphillAI/Features/Me/ProfileView.swift`
- Create: `ios-native/UphillAITests/RaceHistory/RaceDetailServiceTests.swift`, `RaceDetailViewModelTests.swift`
- Modify: `ios-native/UphillAIUITests/RaceHistoryFlowUITests.swift`
- Modify: `backend/scripts/seed_ios_preview.py` (extend local preview race and KB fixtures)
- Create: `ios-native/UphillAITests/Fixtures/race_detail.json`, `race_detail_ambiguous.json`, `race_detail_missing.json`

**Interfaces:** Consumes RaceDetail JSON, Phase A callbacks, `ManualRaceDraft`, and existing APIClient. Produces `RaceDetailResponse: Codable, Sendable` with nested `RacePerformance`, `PreviousRaceFinish`, `RaceCourseContext`, `RaceCourse`, and `RaceCourseCandidate` types. Historical field is decoded using `[String: JSONValue]?` and rendered through typed accessors for year, finishers, winner_time, and percentiles.overall.p50. Add `RaceHistoryServicing.detail(id: Int, courseId: Int?, athleteId: Int?) async throws -> RaceDetailResponse`; default nil arguments belong on the concrete service convenience or its call sites. Update every test fake conforming to the protocol in the same commit.

`RaceDetailViewModel` is MainActor Observable with `detail`, `isLoading`, `errorMessage`, and `load(id:courseId:athleteId:) async`. A monotonically increasing request revision prevents late responses from committing after newer requests; task cancellation is propagated. `RaceDetailScreen(result: RaceResult, service: any RaceHistoryServicing, athleteId: Int? = nil, onChanged: (() -> Void)? = nil)` can immediately show recorded fields while detail loads.

- [ ] **Step 1: Write service, decoding, and stale-response tests.**

Create fixture JSON covering same/different/unknown edition, no KB, ambiguous candidates, and nullable rankings. Test `.detail` owner path and course_id query; test athleteId uses the coach path. Return 404 in StubURLProtocol and assert failure without fabricated detail. For a delayed first response followed by a fast second one, assert the view model retains the second result ID.

```swift
@Test func detailUsesOwnerPathAndCourseChoice() async throws {
    let client = makeStubClient { request in
        #expect(request.url?.path == "/api/race-history/results/7/detail")
        #expect(URLComponents(url: request.url!, resolvingAgainstBaseURL: false)?
                .queryItems?.first(where: { $0.name == "course_id" })?.value == "10")
        return (200, try Fixture.data("race_detail.json"))
    }
    let detail = try await RaceHistoryService(client: client).detail(id: 7, courseId: 10, athleteId: nil)
    #expect(detail.result.id == 7)
}
```

The existing `Fixture.data` reads from `UphillAITests/Fixtures` in the source tree, so no bundle configuration is required. Each fixture is a complete spec-contract response: the primary result has id 7 and every required RaceResult field, the course has id 10, and the performance/previous_finish/course_context/historical_field keys are present with explicit nulls where absent. Add tests for time difference formatting: -846 -> “14:06 faster”, +846 -> “14:06 slower”, 0 -> “Same finish time”; no previous_finish means no comparison claim.

Use this exact primary fixture; the ambiguous and missing fixtures retain its result/performance and change course_context to the corresponding status with null course (and two explicit candidate entries for ambiguous):

```json
{
  "result": {
    "id": 7, "claim_id": null, "source": "manual", "race_name": "Mountain Trail",
    "race_date": "2024-06-01", "discipline": "trail", "distance_km": 50,
    "elevation_gain_m": 2200, "finish_time_sec": 22000, "is_dnf": false,
    "bib": "42", "selected": true, "hidden": false, "user_note": "Finished steadily",
    "verified": false, "verification_methods": [], "rank_overall": 30, "total_overall": 100,
    "rank_gender": null, "total_gender": null, "rank_age_group": null, "total_age_group": null,
    "location": null, "result_url": "https://example.org/result"
  },
  "performance": {
    "overall_top_pct": 30.0, "gender_top_pct": null, "age_group_top_pct": null,
    "average_pace_sec_km": null, "road_pb_key": null
  },
  "previous_finish": null,
  "course_context": {
    "status": "matched", "candidates": [], "message": null,
    "course": {
      "id": 10, "race_name": "Mountain Trail", "distance_label": "50 km", "distance_km": 50,
      "elevation_gain_m": 2200, "location": "Mountain Town", "terrain": ["singletrack"],
      "key_climbs": ["Summit climb"], "climate": {"notes": "Cool mornings"},
      "runner_reviews": [], "source_label": "Organizer", "source_urls": ["https://example.org/course"],
      "verified_at": "2026-10-13", "edition_year": 2026, "edition_status": "different"
    }
  },
  "historical_field": null
}
```

- [ ] **Step 2: Run `ios-native/scripts/test.sh -only-testing:UphillAITests/RaceDetailServiceTests -only-testing:UphillAITests/RaceDetailViewModelTests`; confirm intended red.**

- [ ] **Step 3: Implement service/model and detail views.**

```swift
func detail(id: Int, courseId: Int?, athleteId: Int?) async throws -> RaceDetailResponse {
    let prefix = athleteId.map { "/api/coaching/athletes/\($0)/race-history" } ?? "/api/race-history"
    let query = courseId.map { [URLQueryItem(name: "course_id", value: String($0))] } ?? []
    return try await client.send(.get("\(prefix)/results/\(id)/detail", query: query))
}
```

Detail screen layout: Result header; recorded distance/time/elevation; available rank pairs and fractions; source link; Your notes/actions; Race Review with previous finish and course context. Use ScrollView and the current training-card tokens, readable multiline names, accessibility headings, and semantic buttons. Label pending records “Awaiting confirmation”. Do not include completion/field-position narratives for DNF.

In `RaceCourseContextView`, branch on status: matched shows structured fields and attribution; ambiguous shows named candidate buttons that trigger `load` with course ID; missing shows “No course context available”; unavailable shows the agreed message and Retry. A different edition shows “Course profile: 2026; your result: 2024”; unknown shows “Course edition not recorded”. Typical climate uses “Typical conditions”. Render source links only after Foundation URLComponents verifies HTTP(S), a host, and no username/password, using Link. Missing metadata stays absent.

Manual Edit reuses AddRaceSheet in edit mode; confirmed manual Delete dismisses after success; VBM selection calls the Phase A model and parent callback; coach view suppresses all writes. Hidden notes appear in Your notes but are omitted from the review section. Historical field rendering includes its explicit year and distance label, and only known scalar values. No LLM-generated claims.

Replace the plain result card with a NavigationLink to RaceDetailScreen while preserving its source-aware context menu. Road PB/achievement taps locate the result by ID in the latest history and navigate to it; locked cards remain non-navigating. Add `.navigationDestination(for: RaceResult.self)` only if adopting result-valued navigation, which requires Hashable; otherwise use destination-based NavigationLink and a selected-result sheet/push binding to avoid modifying unrelated model conformance.

- [ ] **Step 4: Verify real app navigation and screenshot states.**

Run targeted native tests. Extend `_seed_race_history` from Phase A with result names prefixed `Preview Review` and minimal corresponding KB chunks whose source_label is `race-history-preview`, domain is race_courses, and kind is race_profile. Use `db.engine.begin()` and parameterized SQL to upsert those synthetic chunks; replace only rows with that preview source_label. Include one matching edition, a 2024 result against a 2026 profile, an unknown race with no chunk, and two compatible courses with equal aliases to exercise ambiguity. Leave all other local KB rows and committed seeds intact. Assert tap opens full name/ranks, course choice updates only current detail, back navigation preserves Race History, manual editing refreshes detail/PBs, and an imported row still has no Delete. Run the existing E2E scheme against the local preview user.

Capture running simulator screenshots for populated detail, edition warning, ambiguous choice, missing KB, DNF/partial ranking, long-name/Dynamic-Type, and loading/retry; save under `ios-native/docs/screenshots/race-history-review/`. Inspect each image. Do not use production data or only UIHostingController render snapshots as completion evidence.

- [ ] **Step 5: Commit native files, updated fakes, fixtures, E2E seed changes, and evidence with `git commit -m "feat: add native race detail and KB review"`.**

### Task 4: Add web detail with the same provenance and safety rules

**Files:**
- Modify: `frontend/src/lib/raceHistory.ts`, `frontend/src/components/RaceHistoryPanel.tsx`
- Create: `frontend/src/components/RaceDetailDialog.tsx`, `RaceCourseContext.tsx`, `RaceDetail.module.css`
- Create: `frontend/src/components/RaceDetailDialog.test.tsx`, `RaceCourseContext.test.tsx`
- Create: `frontend/tests/race-history-review.spec.ts`

**Interfaces:** Export RaceDetail and course types matching the spec from `lib/raceHistory.ts`. Produce `RaceDetailDialog({result, athleteId?, lang, onClose, onChanged})` and `RaceCourseContext({context, resultYear, lang, onChooseCourse, onRetry})`. `result` is Phase A RaceResult; lang is en/vi. `onChanged` reloads parent history after a successful mutation. Use existing session token and getApiBaseUrl conventions.

- [ ] **Step 1: Add rendering, cancellation, and safe-link tests.**

```tsx
import { render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import RaceCourseContext from "./RaceCourseContext";

it("labels another edition without claiming race-day weather", () => {
  render(<RaceCourseContext lang="en" resultYear={2024}
    onChooseCourse={vi.fn()} onRetry={vi.fn()}
    context={{ status: "matched", candidates: [], message: null, course: {
      id: 10, race_name: "Mountain Trail", distance_label: "50 km", distance_km: 50,
      elevation_gain_m: 2200, location: "Mountain Town", terrain: ["singletrack"],
      key_climbs: [], climate: { notes: "Cool mornings" }, runner_reviews: [],
      source_label: "Organizer", source_urls: [], verified_at: "2026-10-13",
      edition_year: 2026, edition_status: "different",
    } }} />);
  expect(screen.getByText(/Course profile: 2026/)).toBeInTheDocument();
  expect(screen.getByText("Typical conditions")).toBeInTheDocument();
  expect(screen.getByText("Organizer")).toBeInTheDocument();
});
```

Dialog tests return a synthetic detail with an absent rank denominator and assert no Top% appears. Test unsafe provider URL produces no link, DNF has no time comparison, unknown course leaves recorded result visible, and read-only athlete mode offers no Edit/Confirm/Delete. Simulate slow request A then fast request B and assert B remains visible. Assert Escape closes, focus returns to the opening button, and ambiguous choice sends the course_id query without modifying race_results.

- [ ] **Step 2: Run `npm test -- src/components/RaceDetailDialog.test.tsx src/components/RaceCourseContext.test.tsx`; confirm red.**

- [ ] **Step 3: Implement dialog fetch and KB presentation.**

Use native `<dialog>` (showModal/close) with the existing component styling conventions. Its accessible name is the race title; close on explicit Close or Escape, restore opener focus, and keep controls reachable by keyboard. Fetch is abortable and resets course choice when result ID changes:

```tsx
useEffect(() => {
  const controller = new AbortController();
  let active = true;
  const prefix = athleteId === undefined ? "/api/race-history" :
    `/api/coaching/athletes/${athleteId}/race-history`;
  const params = courseId === null ? "" : `?course_id=${courseId}`;
  setLoading(true); setError("");
  fetch(`${getApiBaseUrl()}${prefix}/results/${result.id}/detail${params}`, {
    signal: controller.signal,
    headers: { Authorization: `Bearer ${localStorage.getItem("uphill_session_token")}` },
  }).then(async (response) => {
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || `HTTP ${response.status}`);
    return body as RaceDetail;
  }).then((body) => { if (active) setDetail(body); })
    .catch((err: unknown) => {
      if (active && !(err instanceof DOMException && err.name === "AbortError")) setError(String(err));
    }).finally(() => { if (active) setLoading(false); });
  return () => { active = false; controller.abort(); };
}, [result.id, athleteId, courseId, retryCount]);
```

Keep the recorded `result` visible during loading/error. Initialize detail null/courseId null/retryCount zero; key the dialog by result.id in its parent so a changed race cannot keep prior detail. Define every state and import before using this effect.

RaceCourseContext renders the same status branches as native, safeResultUrl source links, source_label/verified_at, multiline terrain/climbs/observations, and labeled typical climate. Candidate buttons call onChooseCourse(id); do not PATCH or persist the choice. Detail shows rank/total and API fractions, explicit exact-year benchmarks, PB state and previous_finish, with no inferred watch metrics. Render KB/user notes as escaped text, never raw HTML. Reuse Phase A edit/delete/selection flows via callbacks; retain athleteId read-only behavior.

In RaceHistoryPanel add “View details” buttons to selected result summaries and pending VBM rows. Avoid nesting a button inside an interactive summary control; place the detail button inside the expanded detail region or replace the summary body with a separate title/button pair. Clicking a road PB card locates its result ID and opens the dialog. Keep visible names fully available in detail even if list rows truncate.

- [ ] **Step 4: Verify web and native/backend contract coverage, then capture web evidence.**

Run targeted Vitest, `npx tsc --noEmit`, and eslint on the touched TS/TSX files. Run `npx playwright test tests/race-history-review.spec.ts` against the actual local app. Use local synthetic results/course KB or explicit Playwright network fixtures; do not re-distill or modify committed KB seeds. Capture matched, edition mismatch, missing/ambiguous KB, DNF/partial ranking, read-only, error/retry, and VI detail states under `docs/screenshots/race-history-review/web/`. Inspect at mobile and desktop sizes, including keyboard focus and long names. Apply the Vietnamese-copy skill to all new VI labels.

- [ ] **Step 5: Commit listed web files and evidence with `git commit -m "feat: add web race detail and KB review"`.**

## Coverage and release verification

| Spec requirement | Owning task |
|---|---|
| Recorded fields, rankings, PB status, source links | B2 backend; B3/B4 presentation |
| Owner/coach scope and readonly | B2 integration; B3/B4 controls |
| Confident compatible matching, candidate choice | B1 adapter; B3/B4 choice UI |
| Edition/typical-climate attribution | B1 contract; B3/B4 rendering |
| Exact-year/distance historical statistics | B1 filter; B2 response; B3/B4 scalar presentation |
| Prior comparable finish, DNF/missing denominator | B2 pure tests; B3/B4 display |
| KB unavailable and stale request safety | B2 unavailable state; B3/B4 fetch tests |
| Hidden-note separation | B2 result contract; B3/B4 review rendering |
| Real screenshots and bilingual web copy | B3/B4 evidence |

After final edits run the targeted backend suites, native detail/model suites and race E2E, and web detail/component/E2E suites. Review branch changes against both Phase A and B contracts. New GET routes can deploy before clients, but deployment and native distribution require a separate user instruction. No automatic repair of the reported athlete account is included.

User amendment (2026-10-13): show one confirmed race list without Trail/Road filters. Keep discipline labels and discipline-specific calculations; pending VBM confirmation stays separate. This supersedes earlier filter requirements.
