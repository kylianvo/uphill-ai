# Race History Results and Personal Bests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let athletes confirm imports, maintain manual results and supporting links, and see correct road PBs separately from distance achievements on native and web.

**Architecture:** Extend the existing race-result API with optional metadata and an additive authoritative road-PB summary. Keep provider imports and selection rules intact. Native gains explicit pending-result management and shared refresh state; web extends its existing management flow.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy Core/PostgreSQL, Alembic, pytest; SwiftUI/Swift Testing/XCTest; Next.js/React/TypeScript, Vitest, Playwright.

**Spec:** `docs/superpowers/specs/2026-10-13-race-history-expansion-design.md`, Phase A and Global constraints.

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

1. A save succeeds but its following GET fails: show “Saved, but refresh failed. Retry.” without displaying a claimed fresh PB. Task 3 tests this in the native model; Task 4 tests the web flow.
2. A manual edit clears URL/location/elevation or changes only a rank: persist explicit null and validate the merged result. Task 1 API tests cover this.
3. A selected result is hidden from Coach text: it still contributes to PBs and achievements. Tasks 2 and 3 test this.
4. Long names and pending imports on a small screen: confirmation, source, and errors remain visible and accessible. Tasks 3 and 4 require running-app screenshots.
5. Provider refresh reimports a rejected VBM result: it remains unselected; imported records have no delete action. Existing integration selection tests are extended in Task 2; native/web UI tests are in Tasks 3 and 4.

## Execution workspace and file map

Before code, invoke using-git-worktrees and create a fresh managed worktree from the current native-containing branch `ios/shoe-rotation-and-prod-fixes` (inspected at `3e44d24`). Do not execute against the unrelated screenshot-dirty checkout. Copy only the three new spec/plan documents from this chat's checkout into that isolated worktree. Check its own AGENTS instructions and live signatures before editing. `backend/main.py` there has newer goal-outcome hooks: preserve them. Run `git status --short`, `git rev-parse HEAD`, and `git ls-files ios-native/project.yml` to establish the execution base. Paths in all tasks are relative to that worktree.

| File | Responsibility |
|---|---|
| `backend/services/race_result_fields.py` (new) | Manual-result normalization and validation |
| `backend/services/race_personal_bests.py` (new) | Pure, deterministic road PB calculation |
| `backend/services/race_history.py` | Existing owner-scoped persistence and summary integration |
| `backend/db.py`, Alembic migration | Nullable location column |
| `backend/main.py` | Additive request fields and validation wiring |
| `ios-native/UphillAI/Core/RaceHistory/ManualRaceDraft.swift` (new) | Add/edit form state and validated payload construction |
| `ios-native/UphillAI/Core/RaceHistory/RaceHistoryViewModel.swift` (new) | History fetch, mutation, and error state |
| Native models, RaceHistory screen, AddRaceSheet, ProfileView | Result management and statistics presentation |
| `frontend/src/lib/raceHistory.ts` (new) | Shared frontend result types, manual payload, and safe external-link helper |
| Existing `RaceHistoryPanel.tsx` / CSS | Web entry/editing, confirmation, and PB cards |

### Task 1: Persist and validate manual result metadata

**Files:**
- Create: `backend/services/race_result_fields.py`
- Modify: `backend/main.py` (`RaceResultInput`, `RaceResultPatch`, `_validate_race_result`, `patch_race_result`)
- Modify: `backend/services/race_history.py` (`create_manual`, `_EDITABLE_MANUAL`)
- Modify: `backend/db.py:init_db()` (`race_results` DDL and idempotent ALTER)
- Create: `backend/alembic/versions/a713c9e6f024_race_result_location.py`
- Create: `backend/tests/unit/test_race_result_fields.py`
- Modify: `backend/tests/integration/test_race_history.py`

**Interfaces:** Consumes existing `get_result(id, user_id)` and `update_result(id, user_id, changes)`. Produces `normalize_manual_result(data: dict[str, Any]) -> dict[str, Any]` raising `ValueError`; nullable location/result_url/bib/user_note and gender/age rank fields in create/patch responses. Imported editable fields remain selected/hidden/user_note.

- [ ] **Step 1: Add failing validation and round-trip tests.**

```python
import pytest
from services.race_result_fields import normalize_manual_result

def record(**changes):
    return dict(discipline="road", race_name="City Marathon", race_date="2023-12-03",
                distance_km=42.195, finish_time_sec=13154, is_dnf=False, **changes)

def test_optional_strings_and_dnf_are_normalized():
    value = record(location="  Can Tho  ", bib=" ", result_url="", user_note="good day")
    value["is_dnf"] = True
    result = normalize_manual_result(value)
    assert result["location"] == "Can Tho" and result["bib"] is None
    assert result["result_url"] is None and result["finish_time_sec"] is None

@pytest.mark.parametrize("url", ["javascript:alert(1)", "file:///tmp/result", "https://a:b@example.org/r"])
def test_unsafe_url_is_rejected(url):
    with pytest.raises(ValueError, match="Result URL"):
        normalize_manual_result(record(result_url=url))

@pytest.mark.parametrize("fields", [
    {"rank_overall": 3, "total_overall": 2},
    {"rank_gender": 0}, {"rank_age_group": 12, "total_age_group": 10},
    {"elevation_gain_m": -1}, {"location": "x" * 201},
])
def test_invalid_metadata_is_rejected(fields):
    with pytest.raises(ValueError):
        normalize_manual_result(record(**fields))
```

Add this API regression using the existing `client` and `auth_headers` fixtures:

```python
def test_manual_link_metadata_and_rank_only_patch(client, auth_headers):
    h = auth_headers["headers"]
    created = client.post("/api/race-history/results", headers=h, json={
        "discipline": "road", "race_name": "City Marathon", "race_date": "2023-12-03",
        "distance_km": 42.195, "finish_time_sec": 13154,
        "location": "Can Tho", "result_url": "https://example.org/results/42",
        "rank_overall": 30, "total_overall": 100, "bib": "42",
    })
    assert created.status_code == 200, created.text
    r = created.json()
    assert r["source"] == "manual" and r["location"] == "Can Tho"
    endpoint = f"/api/race-history/results/{r['id']}"
    assert client.patch(endpoint, headers=h, json={"rank_overall": 101}).status_code == 422
    cleared = client.patch(endpoint, headers=h, json={"result_url": None, "location": None})
    assert cleared.status_code == 200
    assert cleared.json()["result_url"] is None and cleared.json()["location"] is None
    assert client.patch(endpoint, headers=h, json={"selected": None}).status_code == 422
```

- [ ] **Step 2: Run the tests and confirm the intended failures.**

Run from backend: `python -m pytest tests/unit/test_race_result_fields.py tests/integration/test_race_history.py -q`. Tests must use `uphill_ai_test`; integration fixtures truncate tables. Expected new-unit collection failure until the module exists and metadata assertions failing until implemented.

- [ ] **Step 3: Implement normalized manual-result validation.**

Use this core in `race_result_fields.py`; keep existing date/distance validation behavior and messages at the API boundary:

```python
from datetime import date
import math
from typing import Any
from urllib.parse import urlsplit

def normalize_manual_result(data: dict[str, Any]) -> dict[str, Any]:
    value = dict(data)
    for key, limit in {"race_name": 200, "location": 200, "bib": 100,
                       "result_url": 2048, "user_note": 2000}.items():
        text = value.get(key)
        if text is not None and not isinstance(text, str):
            raise ValueError(f"Invalid {key}")
        text = text.strip() if text is not None else None
        if text and len(text) > limit:
            raise ValueError(f"Invalid {key}")
        value[key] = text or None
    if not value["race_name"] or value.get("discipline") not in ("road", "trail"):
        raise ValueError("Race name and discipline are required")
    try:
        date.fromisoformat(value["race_date"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("Invalid race date") from None
    km = value.get("distance_km")
    if not isinstance(km, (int, float)) or not math.isfinite(km) or not 0 < km <= 1000:
        raise ValueError("Invalid race distance")
    gain = value.get("elevation_gain_m")
    if gain is not None and (not isinstance(gain, (int, float)) or not math.isfinite(gain) or gain < 0):
        raise ValueError("Invalid elevation gain")
    for group in ("overall", "gender", "age_group"):
        rank, total = value.get(f"rank_{group}"), value.get(f"total_{group}")
        if any(x is not None and (type(x) is not int or x < 1) for x in (rank, total)):
            raise ValueError(f"Invalid {group} rank")
        if rank is not None and total is not None and rank > total:
            raise ValueError(f"Invalid {group} rank")
    if value.get("is_dnf"):
        value["finish_time_sec"] = None
    elif type(value.get("finish_time_sec")) is not int or value["finish_time_sec"] <= 0:
        raise ValueError("Finish time is required for a finish")
    if value["result_url"]:
        try:
            url = urlsplit(value["result_url"])
            if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password:
                raise ValueError("Result URL must be an absolute HTTP(S) URL without credentials")
        except ValueError:
            raise ValueError("Result URL must be an absolute HTTP(S) URL without credentials") from None
    return value
```

Add the nullable fields to both request models. Set Pydantic `extra="forbid"`. Use integer rank fields with strict validation and positive values. PATCH nullable optional fields remain clearable; reject explicit null for required fields and booleans before merging. For every manual PATCH run `normalized = normalize_manual_result({**existing, **changes})` and persist only requested keys, plus `finish_time_sec` when DNF normalizes it. Wrap `ValueError` as HTTP 422. Preserve imported allowlists and existing reconciliation hooks.

In `create_manual` extend the existing INSERT column/value lists by `location, bib, result_url, user_note, rank_gender, total_gender, rank_age_group, total_age_group`; parameters come from the validated Pydantic model including null defaults. Add those names to `_EDITABLE_MANUAL`. SQL remains parameterized.

- [ ] **Step 4: Add and verify the dual schema change.**

Add `location TEXT` to the `race_results` CREATE statement and `ALTER TABLE race_results ADD COLUMN IF NOT EXISTS location TEXT` during init. Create the migration with `alembic revision --rev-id a713c9e6f024 -m "race result location"`; keep its generated parent from the execution branch. The inspected main-checkout head was `a7c3e9d1f2b4`; do not hardcode that if execution has advanced.

```python
def upgrade() -> None:
    op.execute("ALTER TABLE race_results ADD COLUMN IF NOT EXISTS location TEXT")

def downgrade() -> None:
    op.execute("ALTER TABLE race_results DROP COLUMN IF EXISTS location")
```

On two disposable databases compare `information_schema.columns` for the table: one initialized with `init_db()`; one using `alembic upgrade head` from its previous migration head. Location must be nullable text in both. Run `init_db()` twice and confirm idempotence. Exercise downgrade/upgrade only on a disposable migration database, never the developer's existing training data.

- [ ] **Step 5: Run targeted tests and commit.**

Run `python -m pytest tests/unit/test_race_result_fields.py tests/integration/test_race_history.py -q`; expect PASS. Add explicit integration cases for other-user PATCH 404, optional elevation clearing, all rank groups, required-field null, and imported metadata edits rejected.

Commit only Task 1's listed files: `git commit -m "feat: extend manual race result metadata"` after staging them individually.

### Task 2: Make road PB calculation authoritative and preserve selection

**Files:**
- Create: `backend/services/race_personal_bests.py`, `backend/tests/unit/test_race_personal_bests.py`
- Modify: `backend/services/race_history.py:build_summary`, `backend/tests/integration/test_race_history.py`

**Interfaces:** Produces `compute_road_prs(rows: list[dict[str, Any]], today: date) -> dict[str, dict[str, Any] | None]`. Keys `5k/10k/hm/fm`; PR values use existing `result_id/time_sec/date/stale`. `build_summary` adds `road_prs` and preserves legacy HM/FM keys. No additional DB query is needed beyond existing selected deduped rows.

- [ ] **Step 1: Write a failing PB eligibility test.**

```python
from datetime import date
from services.race_personal_bests import compute_road_prs

def test_pending_trail_dnf_and_hidden_have_correct_pb_semantics():
    base = dict(race_date="2023-12-03", discipline="road", distance_km=42.195,
                selected=True, hidden=False, is_dnf=False, finish_time_sec=13154)
    rows = [{**base, "id": 1, "hidden": True},
            {**base, "id": 2, "selected": False, "finish_time_sec": 12000},
            {**base, "id": 3, "discipline": "trail", "finish_time_sec": 11000},
            {**base, "id": 4, "is_dnf": True, "finish_time_sec": None}]
    prs = compute_road_prs(rows, date(2026, 10, 13))
    assert prs["fm"] == {"result_id": 1, "time_sec": 13154, "date": "2023-12-03", "stale": True}
    assert prs["hm"] is None and prs["5k"] is None and prs["10k"] is None
```

Add tests for fastest-time ties resolved by date/ID, 5K and 10K near-boundary distances (e.g. 5.05 included, 5.11 excluded), stale versus current dates, and absence of any eligible result.

- [ ] **Step 2: Run `python -m pytest tests/unit/test_race_personal_bests.py -q`; confirm it fails before implementation.**

- [ ] **Step 3: Implement the deterministic calculator and wire the summary.**

```python
from datetime import date
from typing import Any

ROAD_DISTANCES = {"5k": (5.0, 0.1), "10k": (10.0, 0.2),
                  "hm": (21.0975, 0.5), "fm": (42.195, 0.5)}

def compute_road_prs(rows: list[dict[str, Any]], today: date) -> dict[str, dict[str, Any] | None]:
    eligible = [r for r in rows if r.get("selected") and r.get("discipline") == "road"
                and not r.get("is_dnf") and (r.get("finish_time_sec") or 0) > 0]
    output = {}
    for key, (km, tolerance) in ROAD_DISTANCES.items():
        candidates = [r for r in eligible if abs(r["distance_km"] - km) < tolerance]
        if not candidates:
            output[key] = None
            continue
        best = min(candidates, key=lambda r: (r["finish_time_sec"],
                   -date.fromisoformat(r["race_date"]).toordinal(), r["id"]))
        output[key] = {"result_id": best["id"], "time_sec": best["finish_time_sec"],
                       "date": best["race_date"],
                       "stale": (today - date.fromisoformat(best["race_date"])).days > 730}
    return output
```

Replace `build_summary`'s nested road-PR function with a single call to `compute_road_prs(rows, today)`. Return `road_prs`, `road_hm_pr=prs['hm']`, and `road_fm_pr=prs['fm']`; retain all trail statistics and prompt-specific hidden filtering. Do not alter provider import defaults.

- [ ] **Step 4: Extend the existing VBM refresh integration test and run it.**

After its selection PATCH assert FM exists in `summary.road_prs`, matches the legacy FM key, and disappears after deselection. Sync again and assert the deselected row remains false. Add the same test sequence for HM 6,244 seconds with synthetic provider data. Run `python -m pytest tests/unit/test_race_personal_bests.py tests/unit/test_race_history.py tests/integration/test_race_history.py -q`; expect PASS.

- [ ] **Step 5: Commit the four listed files with `git commit -m "fix: calculate road PBs from confirmed race results"`.**

### Task 3: Implement native confirmation, editing, and correct Me refresh

**Files:**
- Create: `ios-native/UphillAI/Core/RaceHistory/RaceHistoryViewModel.swift`, `ManualRaceDraft.swift`
- Modify: `ios-native/UphillAI/Core/RaceHistory/RaceHistoryModels.swift`
- Modify: `ios-native/UphillAI/Features/RaceHistory/RaceHistoryScreen.swift`, `AddRaceSheet.swift`, `DistanceBadgeGrid.swift`
- Modify: `ios-native/UphillAI/Features/Me/ProfileView.swift`
- Create: `ios-native/UphillAITests/RaceHistory/RaceHistoryViewModelTests.swift`, `ManualRaceDraftTests.swift`, `RaceAchievementTests.swift`
- Create: `ios-native/UphillAIUITests/RaceHistoryFlowUITests.swift`
- Modify: `backend/scripts/seed_ios_preview.py` (local synthetic race-history rows only)

**Interfaces:** Consumes `RaceHistoryServicing.history/updateResult/addResult/deleteResult` and Phase A fields. Produces `@MainActor @Observable RaceHistoryViewModel` with `history`, `isMutating`, `errorMessage`, `load() async`, `confirm(id: Int, selected: Bool) async`, `deleteManual(id: Int) async`. `ManualRaceDraft.init(result: RaceResult? = nil)` and `payload() throws -> ManualResultPayload` own add/edit form validation. Add `ManualResultPayload.patchChanges() throws -> [String: JSONValue]` using encoded snake-case fields and explicit nulls for cleared optional fields. Add an `onHistoryChanged: ((RaceHistoryResponse) -> Void)?` callback to `RaceHistoryScreen` without removing its existing badge callback.

- [ ] **Step 1: Write native behavior regressions before the views.**

Use `makeStubClient` with `RaceHistoryService` rather than a new unchecked Sendable fake. Assert PATCH path, method, and parsed JSON selected flag; respond with a minimal result followed by history. For refresh failure return 500 on GET and assert the exact saved-but-refresh-failed error and previous model history retained:

```swift
import Foundation
import Testing
@testable import UphillAI

@MainActor
struct RaceHistoryViewModelTests {
    @Test func confirmedWriteWithFailedRefreshRetainsOldHistoryAndShowsRetryError() async throws {
        let pending = RaceResult(id: 7, source: "vbm", raceName: "City Marathon",
                                 raceDate: "2023-12-03", discipline: "road",
                                 distanceKm: 42.195, finishTimeSec: 13154, selected: false)
        let history = RaceHistoryResponse(claims: [], results: [pending], summary: HistorySummary())
        let client = makeStubClient { request in
            if request.httpMethod == "PATCH" {
                #expect(request.url?.path == "/api/race-history/results/7")
                let body = try JSONSerialization.jsonObject(with: request.httpBody!) as! [String: Bool]
                #expect(body["selected"] == true)
                return (200, try JSONCoding.encoder.encode(pending))
            }
            return (500, json(["detail": "Unavailable"]))
        }
        let model = RaceHistoryViewModel(service: RaceHistoryService(client: client), history: history)
        await model.confirm(id: 7, selected: true)
        #expect(model.history == history)
        #expect(model.errorMessage == "Saved, but refresh failed. Retry.")
        #expect(model.isMutating == false)
    }
}
```

For PATCH failure return 422 and assert there is no new selected state. For successful refresh return encoded updated RaceHistoryResponse and assert the selected result and summary change together.

```swift
import Testing
@testable import UphillAI

struct RaceAchievementTests {
    @Test func hiddenFinishStillUnlocksAchievement() {
        let row = RaceResult(id: 1, raceName: "Trail 50", raceDate: "2026-05-16",
                             distanceKm: 51, finishTimeSec: 22191, hidden: true)
        let badges = DistanceBadge.deriveBadges(from: [row])
        #expect(badges.first { $0.category == .fiftyK }?.unlocked == true)
    }
    @Test func pendingAndDnfDoNotUnlock() {
        let pending = RaceResult(id: 1, source: "vbm", raceName: "HM", raceDate: "2023-11-19",
                                 discipline: "road", distanceKm: 21.0975,
                                 finishTimeSec: 6244, selected: false)
        #expect(DistanceBadge.deriveBadges(from: [pending]).allSatisfy { !$0.unlocked })
        let dnf = RaceResult(id: 2, raceName: "Trail 50", raceDate: "2026-05-16",
                             distanceKm: 51, isDnf: true)
        #expect(DistanceBadge.deriveBadges(from: [dnf]).allSatisfy { !$0.unlocked })
    }
}
```

Draft tests: blank optional elevation returns nil; zero elevation persists 0; invalid integer text throws rather than becoming nil; rank greater than total throws; DNF payload time is nil; edit payload clears location/link with JSON null. Decoder tests include both new summary and legacy summary without `road_prs`.

- [ ] **Step 2: Run `ios-native/scripts/test.sh -only-testing:UphillAITests/RaceAchievementTests -only-testing:UphillAITests/ManualRaceDraftTests -only-testing:UphillAITests/RaceHistoryViewModelTests`; verify the new behavior is red.**

- [ ] **Step 3: Implement models, mutation state, and add/edit form.**

Add optional result metadata properties with default-nil initializer arguments. In the existing `PRTime`, add `resultId: Int?` and `date: String?`, both default nil, so new cards can show dates and navigate by result ID while legacy payloads still decode. Add `roadPrs: [String: PRTime]?` to `HistorySummary`, including its initializer with default nil. Keep `JSONCoding` snake-case conventions. `ManualRaceDraft` stores numeric optional fields as strings, with nil defaults; required duration begins empty for add and uses the record for edit. `payload()` enforces the spec before calling the API. Edit mode sends `patchChanges()` so null clears survive Swift Codable's normal omit-nil behavior. Implement that helper by encoding required fields and explicitly inserting `.null` for every nil optional field; use the existing `JSONValue` enum cases.

The selection mutation core is:

```swift
@MainActor @Observable
final class RaceHistoryViewModel {
    private let service: any RaceHistoryServicing
    var history: RaceHistoryResponse?
    var isMutating = false
    var errorMessage: String?
    init(service: any RaceHistoryServicing, history: RaceHistoryResponse? = nil) {
        self.service = service; self.history = history
    }
    func load() async {
        do { history = try await service.history(); errorMessage = nil }
        catch { errorMessage = error.localizedDescription }
    }
    func confirm(id: Int, selected: Bool) async {
        guard !isMutating else { return }
        isMutating = true; errorMessage = nil
        defer { isMutating = false }
        do { _ = try await service.updateResult(id: id, changes: ["selected": .bool(selected)]) }
        catch { errorMessage = error.localizedDescription; return }
        do { history = try await service.history() }
        catch { errorMessage = "Saved, but refresh failed. Retry." }
    }
    func deleteManual(id: Int) async {
        guard !isMutating, history?.results.first(where: { $0.id == id })?.source == "manual" else { return }
        isMutating = true; errorMessage = nil
        defer { isMutating = false }
        do { try await service.deleteResult(id: id) }
        catch { errorMessage = error.localizedDescription; return }
        do { history = try await service.history() }
        catch { errorMessage = "Saved, but refresh failed. Retry." }
    }
}
```

Keep errors visible when history already exists, add an accessible Retry action, and emit `onHistoryChanged` only after the refreshed history is available. Other add/edit/unlink actions use the same explicit write-then-refresh pattern, without silently swallowing errors. Poll pending claims in a cancellation-aware screen task using `Task.sleep(for: .seconds(5))` and checking `Task.isCancelled`; stop when none remain.

Render pending VBM rows separately. Selected list filtering is `result.selected && (filter == "all" || result.discipline == filter)`. Manual menus provide Edit and confirmed Delete; VBM menus provide Not my result; UTMB menus have no deletion. Replace the achievement grid's PB heading/time lines with “Distance achievements”, Completed/Locked, and latest-finish name/date. In `deriveBadges`, remove hidden filtering and pick latest date (ID tie-break), preserving existing categories/model fields for callers. Road PB cards read `summary.roadPrs` only, with legacy HM/FM fallback when it is absent; display full finish time and date.

`ProfileView` retains the latest history, derives its achievements and road cards from that same response, passes the mutation callback to RaceHistoryScreen, and refreshes on return to Me. Do not introduce a second independently cached PB calculation.

- [ ] **Step 4: Test real navigation and capture native evidence.**

Use the existing local-backend E2E infrastructure (`ios-native/scripts/e2e.sh`, `-UPHILL_ENVIRONMENT local -UITEST_NO_AUTOFILL YES`). It does not currently have an app fixture-launch switch. Extend `backend/scripts/seed_ios_preview.py` with `_seed_race_history(athlete_id: int) -> None` called from its main function after `_ensure_user(EMAIL, ...)`. Preserve its localhost database guard. Seed only that preview athlete's two pending VBM road rows plus a selected manual 43 km trail finish; do not contact the live providers. For idempotence replace only the claim with external_id `race-history-preview` and manual rows whose source_key starts with `race-history-preview:`. The two VBM rows are FM 13,154 seconds on 2023-12-03 and HM 6,244 seconds on 2023-11-19. Populate all required normalization fields by `normalize_vbm`, and persist them with the existing `_upsert_result` and a locally inserted claim. For the manual row use parameterized SQL with source_key `race-history-preview:trail`, race_date 2024-09-01, finish_time_sec 22,696, and source manual. No real user is touched.

E2E signs in as the existing `ios-preview@uphill.ai` local user and opens Me -> Race history. Assert pending rows have visible confirm controls, imported context menus have no Delete, confirmation refreshes the road FM card to 3:39:14, Me retains it after back navigation, and a manual result can be edited and deleted. Unit tests provide the exact PATCH-success/GET-failure fixture. In the running simulator use a temporarily unavailable local backend to inspect error/retry layout without changing production.

Run unit tests with the command above. For E2E generate the project then run `xcodebuild test -project ios-native/UphillAI.xcodeproj -scheme UphillAI-E2E -destination "$DESTINATION" -only-testing:UphillAIUITests/RaceHistoryFlowUITests` after setting DESTINATION to an installed simulator as documented by the test script. Boot/open that simulator, navigate the actual app flow, and capture with `xcrun simctl io booted screenshot <absolute-output-path>`. Save pending, confirmed-Me, manual-edit, long-name/Dynamic-Type, and refresh-error screenshots under `ios-native/docs/screenshots/race-history-results/` and inspect them. Renderer-only screenshots are supplementary.

- [ ] **Step 5: Commit the native files and new evidence with `git commit -m "feat: manage native race results and separate road PBs"`.**

### Task 4: Bring the web management flow to the same contract

**Files:**
- Create: `frontend/src/lib/raceHistory.ts`, `frontend/src/lib/raceHistory.test.ts`
- Modify: `frontend/src/components/RaceHistoryPanel.tsx`, `RaceHistory.module.css`
- Create: `frontend/src/components/RaceHistoryPanel.test.tsx`, `frontend/tests/race-history-results.spec.ts`

**Interfaces:** Export existing `Result`, `Claim`, `History` types from `lib/raceHistory.ts`, renamed `RaceResult`, `RaceClaim`, `RaceHistory` for sharing with Phase B. Produce `safeResultUrl(value: string | null | undefined): string | null` and `manualResultPayload(draft: Record<string, string | boolean>): Record<string, unknown>`; throws on invalid field text. Consumes additive metadata and `summary.road_prs`, preserving existing read-only athlete mode.

- [ ] **Step 1: Add URL/payload and behavior tests.**

```typescript
import { describe, expect, it } from "vitest";
import { safeResultUrl } from "./raceHistory";
describe("safeResultUrl", () => {
  it("accepts external web links and rejects executable/credential links", () => {
    expect(safeResultUrl("https://example.org/result")).toBe("https://example.org/result");
    expect(safeResultUrl("javascript:alert(1)")).toBeNull();
    expect(safeResultUrl("https://a:b@example.org/result")).toBeNull();
    expect(safeResultUrl(null)).toBeNull();
  });
});
```

Component tests mock fetch and localStorage token, then mount `<RaceHistoryPanel initiallyOpen />`. Return a full history fixture with one pending VBM and one selected trail result. Click This is my result, assert PATCH `{selected:true}`, return updated GET and assert FM 3:39:14. In a second case return successful PATCH then failed GET: assert the saved-but-refresh-failed error and retry. Test athleteId mode exposes no write controls; hidden selected results retain PB cards; imported records never expose Delete; manual editing serializes blank metadata as null.

- [ ] **Step 2: Run `npm test -- src/lib/raceHistory.test.ts src/components/RaceHistoryPanel.test.tsx` from frontend and confirm red tests.**

- [ ] **Step 3: Implement helpers and form fields.**

```typescript
export function safeResultUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) && url.hostname && !url.username && !url.password
      ? url.href : null;
  } catch { return null; }
}
```

Extend the manual state with location, bib, result_url, user_note, rank_gender, total_gender, rank_age_group, total_age_group as empty strings. `manualResultPayload` trims strings, uses null for empty optional strings/numbers, throws on nonfinite/invalid/negative numeric fields, validates each rank pair, parses `h:mm:ss` with the existing duration parser, and nulls finish time for DNF. Persist every optional key during edits to support clearing. Bind inputs using the existing `styles.field` pattern:

```tsx
{(["location", "bib", "result_url", "user_note"] as const).map((field) => (
  <label className={styles.field} key={field}>
    {field === "location" ? t("Location", "Địa điểm") :
     field === "bib" ? "Bib" : field === "result_url" ?
     t("Result link", "Link kết quả") : t("Race note", "Ghi chú Race")}
    <input value={manual[field]} onChange={(event) => setManual({ ...manual, [field]: event.target.value })} />
  </label>
))}
```

Provide all three rank pairs with distinct labels, numeric inputs, and pair validation errors. Adapt existing edit prefill from the result, add maxLength limits, and retain the existing add/manual delete confirmation flow. Change pending checkbox into a clearly labeled confirmation action; retain pending section and read-only suppression. Add four road PB cards from `summary.road_prs`, with HM/FM fallback when absent. Render source links only through `safeResultUrl`, with `target="_blank" rel="noopener noreferrer"`. Split write and GET failure handling so refresh failure uses the agreed message and retry button.

- [ ] **Step 4: Run component checks and capture running web evidence.**

Run the targeted npm test command, `npx tsc --noEmit`, and `npx eslint src/components/RaceHistoryPanel.tsx src/lib/raceHistory.ts`. Use the ui-screenshot-evidence skill to start a local backend/frontend, authenticate only against a local synthetic user, and exercise confirmation plus manual add/edit/clear. The E2E test may intercept race-history GET/PATCH for deterministic fixtures but must navigate the actual panel. Run `npx playwright test tests/race-history-results.spec.ts`; save mobile-width pending/confirmed/error/manual-edit screenshots under `docs/screenshots/race-history-results/web/`. Check Vietnamese labels with the Vietnamese-copy skill and capture at least one VI state. Test Tab/keyboard operation and small-screen long-name wrapping.

- [ ] **Step 5: Commit listed frontend files and evidence with `git commit -m "feat: extend web race result management and road PB cards"`.**

## Phase A completion and handoff

Run the touched backend unit/integration suites, native targeted tests/E2E, and web targeted tests once after final edits. Review the branch diff for unrelated changes and summarize evidence. No production database update, deployment, or native release is included. Phase A can ship independently; Phase B adds tappable detail and review on top of these contracts.
