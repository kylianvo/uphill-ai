# iOS Native Phase 1: Plan Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The athlete's daily-use Plan tab in the native app: plan summary carousel, week list with collapsed rest days, Today/Tomorrow labels and Priority markers, workout detail with logging and moving, a Manage sheet to switch to a recent plan, and a read-only offline cache.

**Architecture:** Pure date and summary logic (`PlanCalendar`, `PlanSummary`) is ported from the web (`frontend/src/utils/planDate.ts`, `planSummary.ts`) with the same rules and unit tests. `PlanService` wraps the existing endpoints. `OfflineCache` (SwiftData) stores the last user and plan snapshot. `PlanViewModel` combines them; SwiftUI views stay thin. The signed-in root becomes a `TabView` with Plan and Me tabs (Coach arrives in Phase 3).

**Tech Stack:** Swift 6, SwiftUI, SwiftData, Swift Charts, Swift Testing, XCUITest.

**Spec:** `docs/superpowers/specs/2026-10-01-ios-native-app-design.md`. **Depends on:** Phase 0 (`docs/superpowers/plans/2026-10-01-ios-native-phase0-foundations.md`) merged, and the web Phase 1 branch merged (it adds the `workouts.is_priority` column the seed script sets).

## Global Constraints

- Everything in Phase 0's Global Constraints still applies (iOS 18, Swift 6 strict concurrency, XcodeGen, tokens only, system fonts, apple-design motion rules, fixtures never hand-edited, screenshots for every UI task, never run backend integration tests against `uphill_ai`).
- Screenshots go in `ios-native/docs/screenshots/phase1/`.
- Training weeks run Monday to Sunday. Week 1 starts on the Monday on or before `plan.start_date`; without `start_date`, it is anchored back from `race_date` (rules in Task 2). Same rules as the web.
- A day is a **rest day** when it has no workouts, or every workout is `type == "Rest"` or `duration_minutes == 0`. Rest days render as a collapsed row (min height 44 pt) unless a workout on that day is completed or missed.
- Day labels: `TODAY` / `TOMORROW` eyebrow from the workout's computed local date.
- Priority: `is_priority == true` shows a `PRIORITY` label and an accent-ink 1.5 pt outline. Field may be absent in older responses; decode as `false`.
- Mark done: `.sensoryFeedback(.success)`. Week change: `.sensoryFeedback(.selection)`. Failed save: `.sensoryFeedback(.error)`. No other haptics.
- Offline: cached data is read-only. Every write path shows "You're offline. Changes need a connection." instead of calling the network when the last fetch failed with a transport error.
- Sign-out clears the offline cache.
- Copy is English; labels exactly as written in this plan.
- Plan creation is not in this phase. With no active plan the Plan tab shows an empty state pointing to the web app (Phase 2 replaces it).

## File Structure

```
backend/scripts/seed_ios_preview.py             local-only preview athlete with plans around today
ios-native/
  project.yml                                    + UphillAIUITests target, UphillAI-E2E scheme
  scripts/record_fixtures.sh                     + plan fixtures
  scripts/e2e.sh                                 seed + run UI tests against local backend
  UphillAI/
    Core/Models/Plan.swift                       Plan, Workout, Weekday, PlanSnapshot, ActivePlanResponse
    Core/Plan/PlanCalendar.swift                 week/date maths (port of planDate.ts)
    Core/Plan/PlanSummary.swift                  volumes, day states, rest days (port of planSummary.ts)
    Core/Plan/PlanService.swift                  PlanServicing + PlanService
    Core/Persistence/OfflineCache.swift          SwiftData cache of user + plan snapshot
    Core/Auth/SessionStore.swift                 + onUserChange hook
    App/AppModel.swift                           + cache, planService, offline restore
    App/RootView.swift                           signed-in TabView
    Features/Plan/PlanViewModel.swift
    Features/Plan/PlanView.swift                 screen: header, carousel, week switcher, day list
    Features/Plan/SummaryCarousel.swift
    Features/Plan/WeekSwitcher.swift
    Features/Plan/DayRow.swift                   workout day row + collapsed rest row
    Features/Plan/WorkoutDetailSheet.swift
    Features/Plan/ManagePlanSheet.swift
  UphillAITests/
    Support/TestData.swift                       Plan/Workout builders
    Support/FakePlanService.swift
    Fixtures/active_plan.json, active_plan_none.json, recent_plans.json   recorded
    Models/PlanDecodingTests.swift
    Plan/PlanCalendarTests.swift
    Plan/PlanSummaryTests.swift
    Plan/PlanServiceTests.swift
    Persistence/OfflineCacheTests.swift
    Plan/PlanViewModelTests.swift
  UphillAIUITests/PlanFlowUITests.swift
```

---

### Task 1: Preview data, plan fixtures and plan models

**Files:**
- Create: `backend/scripts/seed_ios_preview.py`, `ios-native/UphillAI/Core/Models/Plan.swift`, `ios-native/UphillAITests/Support/TestData.swift`, `ios-native/UphillAITests/Models/PlanDecodingTests.swift`
- Modify: `ios-native/scripts/record_fixtures.sh`
- Recorded: `ios-native/UphillAITests/Fixtures/active_plan.json`, `active_plan_none.json`, `recent_plans.json`

**Interfaces:**
- Consumes: `JSONCoding`, `Fixture` (Phase 0).
- Produces:
  - `enum Weekday: String, CaseIterable, Codable, Sendable, Identifiable` (`"Monday"`…`"Sunday"`) with `offset: Int` (Mon 0 … Sun 6) and `short: String` ("Mon")
  - `struct Plan: Codable, Sendable, Equatable, Identifiable` (fields below)
  - `struct Workout: Codable, Sendable, Equatable, Identifiable` (fields below) with `weekday: Weekday`, `isRest: Bool`, `isDone: Bool`, `isMissedFlag: Bool`
  - `struct PlanSnapshot: Codable, Sendable, Equatable { let plan: Plan; var workouts: [Workout] }`
  - `struct ActivePlanResponse: Decodable, Sendable { let active: Bool; let plan: Plan?; let workouts: [Workout]?; var snapshot: PlanSnapshot? }`
  - Test builders `TestData.plan(_ overrides: [String: Any] = [:]) -> Plan`, `TestData.workout(_ overrides: [String: Any] = [:]) -> Workout`
  - Preview athlete `ios-preview@uphill.ai` / password `uphill-preview-1` in the local database

- [ ] **Step 1: Write** `backend/scripts/seed_ios_preview.py`

```python
"""Seeds a LOCAL-ONLY preview athlete with plans around today, for the native
iOS app's screenshots, fixtures and UI tests.

Usage, from backend/, against the local Docker database only:
    DATABASE_URL=postgresql://uphill:uphill_secret@localhost:5433/uphill_ai python scripts/seed_ios_preview.py

Re-running replaces the preview athlete's plans. No other user is touched.
The password is a local test credential, also used by ios-native/UphillAIUITests.
"""

import datetime
import os
import sys
from urllib.parse import urlparse

EMAIL = "ios-preview@uphill.ai"
PASSWORD = "uphill-preview-1"

# Must run before importing db: db builds its engine from DATABASE_URL at import time.
_host = urlparse(os.environ.get("DATABASE_URL", "")).hostname
if _host not in {"localhost", "127.0.0.1"}:
    sys.exit(f"Refusing to seed database host {_host!r}: local databases only.")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text  # noqa: E402

import db  # noqa: E402
from services.auth_service import hash_password  # noqa: E402

# (day, title, type, minutes, km, zone, gain_m, priority)
WEEK = [
    ("Monday", "Rest Day", "Rest", 0, None, "Rest", 0, False),
    ("Tuesday", "Hill Repeats", "Hill Repeats", 60, 8.0, "Z4", 350, True),
    ("Wednesday", "Easy Run", "Easy Run", 45, 7.0, "Z2", 80, False),
    ("Thursday", "Rest Day", "Rest", 0, None, "Rest", 0, False),
    ("Friday", "Easy Run + Strides", "Easy Run", 40, 6.5, "Z2", 40, False),
    ("Saturday", "Long Run", "Long Run", 120, 18.0, "Z2", 600, True),
    ("Sunday", "Recovery Jog", "Recovery Run", 30, 4.5, "Z1", 20, False),
]


def _workouts(weeks):
    out = []
    for week in weeks:
        for day, title, wtype, minutes, km, zone, gain, _ in WEEK:
            out.append(
                {
                    "week_number": week,
                    "day_of_week": day,
                    "phase": "Base",
                    "title": title,
                    "type": wtype,
                    "duration_minutes": minutes,
                    "distance_km": km,
                    "target_zone": zone,
                    "target_hr_range": None if wtype == "Rest" else "130-145 bpm",
                    "target_pace": None if wtype == "Rest" else "6:10-6:50 /km",
                    "elevation_gain_m": gain,
                    "description": "Rest and recover." if wtype == "Rest" else f"{title}: keep it controlled.",
                    "fueling_tip": None if minutes < 90 else "Take 40 g carbs per hour after the first 45 minutes.",
                }
            )
    return out


def main():
    today = datetime.date.today()
    this_monday = today - datetime.timedelta(days=today.weekday())
    start = this_monday - datetime.timedelta(days=7)  # today falls in week 2
    total_weeks = 12
    race = start + datetime.timedelta(days=(total_weeks - 1) * 7 + 5)  # Saturday of week 12

    user = db.get_user_by_email(EMAIL)
    if not user:
        user = db.create_user_with_password(email=EMAIL, name="Preview Runner", password_hash=hash_password(PASSWORD))
    else:
        db.set_user_password(user["id"], hash_password(PASSWORD))
    uid = user["id"]

    with db.engine.connect() as conn:
        conn.execute(text("DELETE FROM plans WHERE user_id = :u"), {"u": uid})
        conn.execute(text("UPDATE users SET onboarding_complete = TRUE WHERE id = :u"), {"u": uid})
        conn.commit()

    older = db.create_plan(
        user_id=uid,
        race_name="Sky Race 25K",
        race_date=(race - datetime.timedelta(days=70)).isoformat(),
        goal_type="finish",
        target_time_hours=None,
        total_weeks=8,
        start_date=(start - datetime.timedelta(days=28)).isoformat(),
    )
    db.save_workouts(older, _workouts([1]))

    plan_id = db.create_plan(
        user_id=uid,
        race_name="Vietnam Mountain Marathon 42K",
        race_date=race.isoformat(),
        goal_type="time",
        target_time_hours=6.5,
        total_weeks=total_weeks,
        course_distance_km=42.0,
        course_elevation_gain_m=2400.0,
        start_date=start.isoformat(),
    )
    db.save_workouts(plan_id, _workouts([1, 2, 3]))
    db.set_plan_active(uid, plan_id)

    priority_titles = [title for _, title, *_rest, prio in WEEK if prio]
    with db.engine.connect() as conn:
        conn.execute(
            text("UPDATE workouts SET is_priority = TRUE WHERE plan_id = :p AND title = ANY(:t)"),
            {"p": plan_id, "t": priority_titles},
        )
        # Week 1: everything done except Friday, which was missed.
        conn.execute(
            text(
                "UPDATE workouts SET is_completed = 1 WHERE plan_id = :p AND week_number = 1 "
                "AND type <> 'Rest' AND day_of_week <> 'Friday'"
            ),
            {"p": plan_id},
        )
        conn.execute(
            text("UPDATE workouts SET is_missed = 1 WHERE plan_id = :p AND week_number = 1 AND day_of_week = 'Friday'"),
            {"p": plan_id},
        )
        # Week 2 (this week): days before today are done.
        done_days = [WEEK[i][0] for i in range(today.weekday())]
        if done_days:
            conn.execute(
                text(
                    "UPDATE workouts SET is_completed = 1, rpe = 5 WHERE plan_id = :p AND week_number = 2 "
                    "AND type <> 'Rest' AND day_of_week = ANY(:d)"
                ),
                {"p": plan_id, "d": done_days},
            )
        conn.commit()

    print(f"Seeded {EMAIL} (user {uid}): active plan {plan_id}, older plan {older}. Week 1 starts {start}.")


if __name__ == "__main__":
    main()
```

Check the helper names this script uses exist with these signatures before running: `grep -n "def get_user_by_email\|def create_user_with_password\|def set_user_password\|def create_plan\|def save_workouts\|def set_plan_active" backend/db.py` and `grep -n "def hash_password" backend/services/auth_service.py`. If one differs, adapt the call, not the helper.

Run: `cd backend && DATABASE_URL=postgresql://uphill:uphill_secret@localhost:5433/uphill_ai python scripts/seed_ios_preview.py`
Expected: `Seeded ios-preview@uphill.ai (user N): active plan P, older plan O. Week 1 starts YYYY-MM-DD.`
Run it a second time: same output with new plan ids, no error (idempotent).

- [ ] **Step 2: Extend** `ios-native/scripts/record_fixtures.sh`

Append before the final `echo`:

```bash
get /api/coach/active-plan active_plan_none.json   # ios-fixtures has no plan

# The preview athlete (backend/scripts/seed_ios_preview.py) has plans.
PREVIEW=$(curl -sf -X POST "$BASE/api/auth/mock-login" \
  -H 'Content-Type: application/json' -d '{"email":"ios-preview@uphill.ai"}')
TOKEN=$(printf '%s' "$PREVIEW" | python3 -c 'import json,sys; print(json.load(sys.stdin)["session_token"])')
get /api/coach/active-plan active_plan.json
get /api/coach/recent-plans recent_plans.json
```

Run: `ios-native/scripts/record_fixtures.sh`
Expected: three new fixtures. `active_plan_none.json` is `{"active": false}`. `active_plan.json` has `"active": true`, a `plan` and 21 `workouts`. `recent_plans.json` has 2 plans.

- [ ] **Step 3: Write** `UphillAITests/Support/TestData.swift`

```swift
import Foundation
@testable import UphillAI

/// Builds models through the real decoder so tests exercise the same path as
/// production. Pass only the fields a test cares about.
enum TestData {
    static func plan(_ overrides: [String: Any] = [:]) -> Plan {
        var base: [String: Any] = [
            "id": 1, "user_id": 1, "race_name": "Test Race", "race_date": "2026-12-19",
            "goal_type": "finish", "total_weeks": 12, "current_week": 1,
            "start_date": "2026-09-30", "plan_status": "active",
        ]
        base.merge(overrides) { _, new in new }
        return try! JSONCoding.decoder.decode(Plan.self, from: json(base))
    }

    static func workout(_ overrides: [String: Any] = [:]) -> Workout {
        var base: [String: Any] = [
            "id": 1, "plan_id": 1, "week_number": 1, "day_of_week": "Monday", "phase": "Base",
            "title": "Easy Run", "type": "Easy Run", "duration_minutes": 45.0, "distance_km": 7.0,
            "target_zone": "Z2", "elevation_gain_m": 50.0, "source": "ai_generated",
            "is_completed": 0, "is_missed": 0, "is_priority": false,
        ]
        base.merge(overrides) { _, new in new }
        return try! JSONCoding.decoder.decode(Workout.self, from: json(base))
    }
}
```

`json(_:)` comes from `Support/StubURLProtocol.swift` (Phase 0). Passing `NSNull()` as an override value sends JSON `null`.

- [ ] **Step 4: Write the failing tests** `UphillAITests/Models/PlanDecodingTests.swift`

```swift
import Foundation
import Testing
@testable import UphillAI

struct PlanDecodingTests {
    @Test func decodesRecordedActivePlan() throws {
        let response = try Fixture.decode(ActivePlanResponse.self, "active_plan.json")
        let snapshot = try #require(response.snapshot)
        #expect(snapshot.plan.raceName == "Vietnam Mountain Marathon 42K")
        #expect(snapshot.workouts.count == 21)
        #expect(snapshot.workouts.contains { $0.isPriority })
        #expect(snapshot.workouts.contains { $0.isRest })
    }

    @Test func decodesInactivePlan() throws {
        let response = try Fixture.decode(ActivePlanResponse.self, "active_plan_none.json")
        #expect(response.active == false)
        #expect(response.snapshot == nil)
    }

    @Test func decodesRecentPlans() throws {
        struct Recent: Decodable { let plans: [Plan] }
        let recent = try Fixture.decode(Recent.self, "recent_plans.json")
        #expect(recent.plans.count == 2)
    }

    @Test func missingPriorityDecodesAsFalse() throws {
        let object: [String: Any] = [
            "id": 3, "plan_id": 1, "week_number": 1, "day_of_week": "Tuesday", "phase": "Base",
            "title": "Easy", "type": "Easy Run", "duration_minutes": 30, "target_zone": "Z2",
            "source": "ai_generated", "is_completed": 0, "is_missed": 0,
        ]
        let workout = try JSONCoding.decoder.decode(Workout.self, from: json(object))
        #expect(workout.isPriority == false)
        #expect(workout.weekday == .tuesday)
    }

    @Test func restRules() {
        #expect(TestData.workout(["type": "Rest", "duration_minutes": 0]).isRest)
        #expect(TestData.workout(["type": "Mobility", "duration_minutes": 0]).isRest)
        #expect(!TestData.workout(["type": "Easy Run", "duration_minutes": 30]).isRest)
    }

    @Test func unknownDayFallsBackToMonday() {
        #expect(TestData.workout(["day_of_week": "Funday"]).weekday == .monday)
    }
}
```

- [ ] **Step 5: Run to verify failure**

Run: `ios-native/scripts/test.sh`
Expected: compile errors (`Plan`, `Workout`, `ActivePlanResponse` missing).

- [ ] **Step 6: Implement** `Core/Models/Plan.swift`

```swift
import Foundation

enum Weekday: String, CaseIterable, Codable, Sendable, Identifiable {
    case monday = "Monday", tuesday = "Tuesday", wednesday = "Wednesday", thursday = "Thursday"
    case friday = "Friday", saturday = "Saturday", sunday = "Sunday"

    var id: String { rawValue }
    /// Days after Monday: Monday 0 … Sunday 6.
    var offset: Int { Weekday.allCases.firstIndex(of: self)! }
    var short: String { String(rawValue.prefix(3)) }
}

/// Mirrors a `plans` row. Unused columns (prediction JSONB, athlete notes…) are not decoded.
struct Plan: Codable, Sendable, Equatable, Identifiable {
    let id: Int
    let raceName: String
    let raceDate: String
    let goalType: String
    let targetTimeHours: Double?
    let totalWeeks: Int
    let currentWeek: Int?
    let courseDistanceKm: Double?
    let courseElevationGainM: Double?
    let startDate: String?
    let planStatus: String?
    let createdAt: String?
}

/// Mirrors a `workouts` row.
struct Workout: Codable, Sendable, Equatable, Identifiable {
    let id: Int
    let planId: Int
    let weekNumber: Int
    let dayOfWeek: String
    let phase: String
    let title: String
    let type: String
    let durationMinutes: Double
    let distanceKm: Double?
    let targetZone: String
    let targetHrRange: String?
    let targetPace: String?
    let treadmillIncline: String?
    let treadmillSpeed: String?
    let elevationGainM: Double?
    let gradePercent: Double?
    let intervalReps: Int?
    let intervalRepValue: Double?
    let intervalRepUnit: String?
    let walkIntervalValue: Double?
    let description: String?
    let fuelingTip: String?
    let source: String?
    let isCompleted: Int?
    let isMissed: Int?
    let approvedAt: String?
    let rpe: Int?
    let notes: String?
    let sessionSlot: String?
    let isPriority: Bool

    enum CodingKeys: String, CodingKey {
        case id, planId, weekNumber, dayOfWeek, phase, title, type, durationMinutes, distanceKm, targetZone
        case targetHrRange, targetPace, treadmillIncline, treadmillSpeed, elevationGainM, gradePercent
        case intervalReps, intervalRepValue, intervalRepUnit, walkIntervalValue, description, fuelingTip
        case source, isCompleted, isMissed, approvedAt, rpe, notes, sessionSlot, isPriority
    }

    init(from decoder: any Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(Int.self, forKey: .id)
        planId = try c.decode(Int.self, forKey: .planId)
        weekNumber = try c.decode(Int.self, forKey: .weekNumber)
        dayOfWeek = try c.decode(String.self, forKey: .dayOfWeek)
        phase = try c.decode(String.self, forKey: .phase)
        title = try c.decode(String.self, forKey: .title)
        type = try c.decode(String.self, forKey: .type)
        durationMinutes = try c.decode(Double.self, forKey: .durationMinutes)
        distanceKm = try c.decodeIfPresent(Double.self, forKey: .distanceKm)
        targetZone = try c.decode(String.self, forKey: .targetZone)
        targetHrRange = try c.decodeIfPresent(String.self, forKey: .targetHrRange)
        targetPace = try c.decodeIfPresent(String.self, forKey: .targetPace)
        treadmillIncline = try c.decodeIfPresent(String.self, forKey: .treadmillIncline)
        treadmillSpeed = try c.decodeIfPresent(String.self, forKey: .treadmillSpeed)
        elevationGainM = try c.decodeIfPresent(Double.self, forKey: .elevationGainM)
        gradePercent = try c.decodeIfPresent(Double.self, forKey: .gradePercent)
        intervalReps = try c.decodeIfPresent(Int.self, forKey: .intervalReps)
        intervalRepValue = try c.decodeIfPresent(Double.self, forKey: .intervalRepValue)
        intervalRepUnit = try c.decodeIfPresent(String.self, forKey: .intervalRepUnit)
        walkIntervalValue = try c.decodeIfPresent(Double.self, forKey: .walkIntervalValue)
        description = try c.decodeIfPresent(String.self, forKey: .description)
        fuelingTip = try c.decodeIfPresent(String.self, forKey: .fuelingTip)
        source = try c.decodeIfPresent(String.self, forKey: .source)
        isCompleted = try c.decodeIfPresent(Int.self, forKey: .isCompleted)
        isMissed = try c.decodeIfPresent(Int.self, forKey: .isMissed)
        approvedAt = try c.decodeIfPresent(String.self, forKey: .approvedAt)
        rpe = try c.decodeIfPresent(Int.self, forKey: .rpe)
        notes = try c.decodeIfPresent(String.self, forKey: .notes)
        sessionSlot = try c.decodeIfPresent(String.self, forKey: .sessionSlot)
        // Older backends (before the web Phase 1 merge) don't send it.
        isPriority = try c.decodeIfPresent(Bool.self, forKey: .isPriority) ?? false
    }

    /// The web defaults unknown days to Monday; so do we.
    var weekday: Weekday { Weekday(rawValue: dayOfWeek) ?? .monday }
    var isRest: Bool { type == "Rest" || durationMinutes == 0 }
    var isDone: Bool { isCompleted == 1 }
    var isMissedFlag: Bool { isMissed == 1 }
}

struct PlanSnapshot: Codable, Sendable, Equatable {
    let plan: Plan
    var workouts: [Workout]
}

/// GET /api/coach/active-plan and POST /api/coach/select-plan.
/// `{"active": false}` when the athlete has no plan.
struct ActivePlanResponse: Decodable, Sendable {
    let active: Bool
    let plan: Plan?
    let workouts: [Workout]?

    var snapshot: PlanSnapshot? {
        guard active, let plan else { return nil }
        return PlanSnapshot(plan: plan, workouts: workouts ?? [])
    }
}
```

`Workout` keeps the synthesized `Encodable` (the cache encodes it with `JSONCoding.encoder`, which writes snake_case keys that this decoder reads back).

- [ ] **Step 7: Run tests**

Run: `ios-native/scripts/test.sh`
Expected: all pass. If a recorded fixture fails to decode, fix the Swift type (e.g. `currentWeek` type, a `Double` that arrives as `Int` is fine; a `String` that arrives as number is not), never the fixture.

- [ ] **Step 8: Commit**

```bash
git add backend/scripts/seed_ios_preview.py ios-native
git commit -m "feat(ios): plan models, preview seed and recorded plan fixtures"
```

---

### Task 2: Plan calendar maths

**Files:**
- Create: `ios-native/UphillAI/Core/Plan/PlanCalendar.swift`
- Test: `ios-native/UphillAITests/Plan/PlanCalendarTests.swift`

**Interfaces:**
- Consumes: `Plan`, `Workout`, `Weekday` (Task 1).
- Produces (all `static`, all take `calendar: Calendar = PlanCalendar.calendar`):
  - `PlanCalendar.calendar: Calendar` (Gregorian, current time zone)
  - `day(from: String?) -> Date?` ("YYYY-MM-DD…" → local midnight)
  - `ymd(_ date: Date) -> String`
  - `monday(of: Date) -> Date`
  - `weekOneMonday(plan: Plan, workouts: [Workout]) -> Date?`
  - `date(week: Int, weekday: Weekday, plan: Plan, workouts: [Workout]) -> Date?`
  - `currentWeek(plan: Plan, workouts: [Workout], now: Date) -> Int`
  - `resolveCurrentWeek(plan: Plan, workouts: [Workout], now: Date) -> Int`
  - `daysToRace(_ raceDate: String?, now: Date) -> Int?`
  - `eyebrow(for date: Date?, now: Date) -> String?` (`"TODAY"`, `"TOMORROW"` or nil)

Rules (from `frontend/src/utils/planDate.ts`):
1. Week 1 starts on the Monday on or before `start_date`.
2. Without `start_date`: find the race workout (title contains "TARGET EVENT" or type is "RACE", case-insensitive); race week = its week, else `total_weeks`. Week 1 Monday = Monday of `race_date`'s week minus (race week − 1) × 7 days.
3. Current week = whole weeks from week 1 Monday to today, plus 1, clamped to [1, total_weeks]. `resolveCurrentWeek` further clamps to the highest generated week.
4. Day differences use calendar days (DST-safe), never 86 400-second division.

- [ ] **Step 1: Write the failing tests** `PlanCalendarTests.swift`

```swift
import Foundation
import Testing
@testable import UphillAI

struct PlanCalendarTests {
    private let cal: Calendar = {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        return c
    }()

    private func d(_ s: String, hour: Int = 9) -> Date {
        let day = PlanCalendar.day(from: s, calendar: cal)!
        return cal.date(byAdding: .hour, value: hour, to: day)!
    }

    @Test func parsesDayStringsAndRejectsJunk() {
        #expect(PlanCalendar.ymd(PlanCalendar.day(from: "2026-09-30T00:00:00", calendar: cal)!, calendar: cal) == "2026-09-30")
        #expect(PlanCalendar.day(from: nil, calendar: cal) == nil)
        #expect(PlanCalendar.day(from: "2026-9-3", calendar: cal) == nil)
        #expect(PlanCalendar.day(from: "garbage!!", calendar: cal) == nil)
    }

    @Test func mondayOfAnyDay() {
        #expect(PlanCalendar.ymd(PlanCalendar.monday(of: d("2026-09-30"), calendar: cal), calendar: cal) == "2026-09-28")
        #expect(PlanCalendar.ymd(PlanCalendar.monday(of: d("2026-10-04"), calendar: cal), calendar: cal) == "2026-09-28") // Sunday
        #expect(PlanCalendar.ymd(PlanCalendar.monday(of: d("2026-09-28"), calendar: cal), calendar: cal) == "2026-09-28")
    }

    @Test func weekOneFromStartDate() {
        let plan = TestData.plan(["start_date": "2026-09-30"])
        let monday = PlanCalendar.weekOneMonday(plan: plan, workouts: [], calendar: cal)!
        #expect(PlanCalendar.ymd(monday, calendar: cal) == "2026-09-28")
    }

    @Test func weekOneFromRaceDateUsesTotalWeeks() {
        let plan = TestData.plan(["start_date": NSNull(), "race_date": "2026-12-19", "total_weeks": 12])
        let monday = PlanCalendar.weekOneMonday(plan: plan, workouts: [], calendar: cal)!
        #expect(PlanCalendar.ymd(monday, calendar: cal) == "2026-09-28")
    }

    @Test func weekOneFromRaceDateUsesRaceWorkoutWeek() {
        let plan = TestData.plan(["start_date": NSNull(), "race_date": "2026-12-19", "total_weeks": 12])
        let race = TestData.workout(["week_number": 10, "title": "TARGET EVENT: VMM", "type": "Race"])
        let monday = PlanCalendar.weekOneMonday(plan: plan, workouts: [race], calendar: cal)!
        #expect(PlanCalendar.ymd(monday, calendar: cal) == "2026-10-12")
    }

    @Test func dateOfWeekday() {
        let plan = TestData.plan(["start_date": "2026-09-30"])
        let date = PlanCalendar.date(week: 2, weekday: .saturday, plan: plan, workouts: [], calendar: cal)!
        #expect(PlanCalendar.ymd(date, calendar: cal) == "2026-10-10")
    }

    @Test(arguments: [
        ("2026-09-20", 1),  // before the plan starts
        ("2026-09-28", 1),
        ("2026-10-04", 1),  // Sunday of week 1
        ("2026-10-05", 2),
        ("2027-06-01", 12), // after the plan ends
    ])
    func currentWeek(now: String, expected: Int) {
        let plan = TestData.plan(["start_date": "2026-09-30", "total_weeks": 12])
        #expect(PlanCalendar.currentWeek(plan: plan, workouts: [], now: d(now), calendar: cal) == expected)
    }

    @Test func currentWeekAcrossDSTChange() {
        var ny = Calendar(identifier: .gregorian)
        ny.timeZone = TimeZone(identifier: "America/New_York")!
        let plan = TestData.plan(["start_date": "2026-10-26", "total_weeks": 12])
        let now = PlanCalendar.day(from: "2026-11-02", calendar: ny)!  // DST ended Nov 1
        #expect(PlanCalendar.currentWeek(plan: plan, workouts: [], now: now, calendar: ny) == 2)
    }

    @Test func resolveCurrentWeekClampsToGeneratedWeeks() {
        let plan = TestData.plan(["start_date": "2026-09-30", "total_weeks": 12])
        let workouts = [TestData.workout(["week_number": 1]), TestData.workout(["id": 2, "week_number": 2])]
        #expect(PlanCalendar.resolveCurrentWeek(plan: plan, workouts: workouts, now: d("2026-11-20"), calendar: cal) == 2)
        #expect(PlanCalendar.resolveCurrentWeek(plan: plan, workouts: [], now: d("2026-11-20"), calendar: cal) == 8)
    }

    @Test func daysToRace() {
        #expect(PlanCalendar.daysToRace("2026-10-10", now: d("2026-10-01", hour: 23), calendar: cal) == 9)
        #expect(PlanCalendar.daysToRace("2026-10-01", now: d("2026-10-01"), calendar: cal) == 0)
        #expect(PlanCalendar.daysToRace("2026-09-30", now: d("2026-10-01"), calendar: cal) == nil)
        #expect(PlanCalendar.daysToRace(nil, now: d("2026-10-01"), calendar: cal) == nil)
    }

    @Test func eyebrow() {
        let now = d("2026-10-01", hour: 22)
        #expect(PlanCalendar.eyebrow(for: d("2026-10-01", hour: 0), now: now, calendar: cal) == "TODAY")
        #expect(PlanCalendar.eyebrow(for: d("2026-10-02", hour: 0), now: now, calendar: cal) == "TOMORROW")
        #expect(PlanCalendar.eyebrow(for: d("2026-10-03", hour: 0), now: now, calendar: cal) == nil)
        #expect(PlanCalendar.eyebrow(for: nil, now: now, calendar: cal) == nil)
    }
}
```

- [ ] **Step 2: Run to verify failure**

Run: `ios-native/scripts/test.sh`
Expected: compile error, `PlanCalendar` not found.

- [ ] **Step 3: Implement** `Core/Plan/PlanCalendar.swift`

```swift
import Foundation

/// Plan week and date maths. Port of frontend/src/utils/planDate.ts: weeks run
/// Monday to Sunday and all arithmetic is in local calendar days.
enum PlanCalendar {
    static var calendar: Calendar {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = .current
        return c
    }

    /// "YYYY-MM-DD" (a longer ISO string is cut to its date) → local midnight.
    static func day(from string: String?, calendar: Calendar = calendar) -> Date? {
        guard let s = string?.prefix(10), s.count == 10 else { return nil }
        let parts = s.split(separator: "-")
        guard parts.count == 3, parts[0].count == 4, parts[1].count == 2, parts[2].count == 2,
              let y = Int(parts[0]), let m = Int(parts[1]), let d = Int(parts[2]) else { return nil }
        return calendar.date(from: DateComponents(year: y, month: m, day: d))
    }

    static func ymd(_ date: Date, calendar: Calendar = calendar) -> String {
        let c = calendar.dateComponents([.year, .month, .day], from: date)
        return String(format: "%04d-%02d-%02d", c.year!, c.month!, c.day!)
    }

    static func monday(of date: Date, calendar: Calendar = calendar) -> Date {
        let start = calendar.startOfDay(for: date)
        let weekday = calendar.component(.weekday, from: start)  // 1 = Sunday … 7 = Saturday
        let daysSinceMonday = (weekday + 5) % 7
        return calendar.date(byAdding: .day, value: -daysSinceMonday, to: start)!
    }

    static func weekOneMonday(plan: Plan, workouts: [Workout], calendar: Calendar = calendar) -> Date? {
        if let start = day(from: plan.startDate, calendar: calendar) {
            return monday(of: start, calendar: calendar)
        }
        guard let race = day(from: plan.raceDate, calendar: calendar) else { return nil }
        let raceWorkout = workouts.first {
            $0.title.uppercased().contains("TARGET EVENT") || $0.type.uppercased() == "RACE"
        }
        let raceWeek = raceWorkout?.weekNumber ?? plan.totalWeeks
        return calendar.date(byAdding: .day, value: -(raceWeek - 1) * 7, to: monday(of: race, calendar: calendar))
    }

    static func date(week: Int, weekday: Weekday, plan: Plan, workouts: [Workout], calendar: Calendar = calendar) -> Date? {
        guard let weekOne = weekOneMonday(plan: plan, workouts: workouts, calendar: calendar) else { return nil }
        return calendar.date(byAdding: .day, value: (week - 1) * 7 + weekday.offset, to: weekOne)
    }

    static func currentWeek(plan: Plan, workouts: [Workout], now: Date, calendar: Calendar = calendar) -> Int {
        guard plan.totalWeeks >= 1,
              let weekOne = weekOneMonday(plan: plan, workouts: workouts, calendar: calendar) else { return 1 }
        let days = calendar.dateComponents([.day], from: weekOne, to: calendar.startOfDay(for: now)).day ?? 0
        let week = Int((Double(days) / 7).rounded(.down)) + 1
        return min(max(week, 1), plan.totalWeeks)
    }

    /// The week to show by default: the calendar week, but never past the last generated week.
    static func resolveCurrentWeek(plan: Plan, workouts: [Workout], now: Date, calendar: Calendar = calendar) -> Int {
        let week = currentWeek(plan: plan, workouts: workouts, now: now, calendar: calendar)
        let maxGenerated = workouts.map(\.weekNumber).max() ?? 0
        return maxGenerated > 0 ? min(week, maxGenerated) : week
    }

    /// Whole days from today to the race; nil when unknown or past.
    static func daysToRace(_ raceDate: String?, now: Date, calendar: Calendar = calendar) -> Int? {
        guard let race = day(from: raceDate, calendar: calendar) else { return nil }
        let days = calendar.dateComponents([.day], from: calendar.startOfDay(for: now), to: race).day ?? -1
        return days >= 0 ? days : nil
    }

    static func eyebrow(for date: Date?, now: Date, calendar: Calendar = calendar) -> String? {
        guard let date else { return nil }
        if calendar.isDate(date, inSameDayAs: now) { return "TODAY" }
        let tomorrow = calendar.date(byAdding: .day, value: 1, to: calendar.startOfDay(for: now))!
        return calendar.isDate(date, inSameDayAs: tomorrow) ? "TOMORROW" : nil
    }
}
```

- [ ] **Step 4: Run tests**

Run: `ios-native/scripts/test.sh`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add ios-native
git commit -m "feat(ios): plan calendar maths ported from the web"
```

---

### Task 3: Plan summary maths

**Files:**
- Create: `ios-native/UphillAI/Core/Plan/PlanSummary.swift`
- Test: `ios-native/UphillAITests/Plan/PlanSummaryTests.swift`

**Interfaces:**
- Consumes: `Workout`, `Weekday` (Task 1).
- Produces:
  - `struct WeekVolume: Equatable, Sendable { let week: Int; let km: Double; let minutes: Double; let gainM: Double; let generated: Bool; var hours: Double }` (`hours` rounded to 1 decimal)
  - `enum DayState: Equatable, Sendable { case done, missed, planned, rest }`
  - `struct DayStatus: Equatable, Sendable { let weekday: Weekday; let state: DayState }`
  - `enum PlanSummary` with `static func volume(week: Int, workouts: [Workout]) -> WeekVolume`, `static func weeklyVolumes(_ workouts: [Workout], totalWeeks: Int) -> [WeekVolume]`, `static func isRestDay(_ dayWorkouts: [Workout]) -> Bool`, `static func dayStates(week: Int, workouts: [Workout]) -> [DayStatus]`, `static func phase(week: Int, workouts: [Workout]) -> String?`

Rules (from `frontend/src/utils/planSummary.ts`): a day's active workouts are those that are not rest. No active workouts → `rest`; all active done → `done`; any active missed → `missed`; otherwise `planned`.

- [ ] **Step 1: Write the failing tests** `PlanSummaryTests.swift`

```swift
import Testing
@testable import UphillAI

struct PlanSummaryTests {
    private let week2 = [
        TestData.workout(["id": 1, "week_number": 2, "day_of_week": "Monday", "type": "Rest", "duration_minutes": 0, "distance_km": NSNull(), "elevation_gain_m": 0]),
        TestData.workout(["id": 2, "week_number": 2, "day_of_week": "Tuesday", "duration_minutes": 60, "distance_km": 8.0, "elevation_gain_m": 350, "is_completed": 1]),
        TestData.workout(["id": 3, "week_number": 2, "day_of_week": "Wednesday", "duration_minutes": 45, "distance_km": 7.0, "elevation_gain_m": 80, "is_missed": 1]),
        TestData.workout(["id": 4, "week_number": 2, "day_of_week": "Saturday", "duration_minutes": 120, "distance_km": 18.0, "elevation_gain_m": 600, "phase": "Build"]),
    ]

    @Test func volumeSumsOneWeek() {
        let v = PlanSummary.volume(week: 2, workouts: week2)
        #expect(v.km == 33.0)
        #expect(v.minutes == 225)
        #expect(v.hours == 3.8)
        #expect(v.gainM == 1030)
        #expect(v.generated)
    }

    @Test func weeklyVolumesMarksMissingWeeks() {
        let vols = PlanSummary.weeklyVolumes(week2, totalWeeks: 3)
        #expect(vols.map(\.week) == [1, 2, 3])
        #expect(vols.map(\.generated) == [false, true, false])
        #expect(vols[0].km == 0)
    }

    @Test func dayStates() {
        let states = PlanSummary.dayStates(week: 2, workouts: week2)
        #expect(states.map(\.weekday) == Weekday.allCases)
        #expect(states.map(\.state) == [.rest, .done, .missed, .rest, .rest, .planned, .rest])
    }

    @Test func restDayRules() {
        #expect(PlanSummary.isRestDay([]))
        #expect(PlanSummary.isRestDay([TestData.workout(["type": "Rest", "duration_minutes": 0])]))
        #expect(!PlanSummary.isRestDay([TestData.workout(["type": "Rest", "duration_minutes": 0]),
                                         TestData.workout(["id": 2, "duration_minutes": 20])]))
    }

    @Test func phaseUsesFirstNonRestWorkoutOfWeek() {
        #expect(PlanSummary.phase(week: 2, workouts: week2) == "Base")
        #expect(PlanSummary.phase(week: 5, workouts: week2) == nil)
    }
}
```

- [ ] **Step 2: Run to verify failure**

Run: `ios-native/scripts/test.sh`
Expected: compile error, `PlanSummary` not found.

- [ ] **Step 3: Implement** `Core/Plan/PlanSummary.swift`

```swift
import Foundation

struct WeekVolume: Equatable, Sendable {
    let week: Int
    let km: Double
    let minutes: Double
    let gainM: Double
    let generated: Bool

    var hours: Double { (minutes / 60 * 10).rounded() / 10 }
}

enum DayState: Equatable, Sendable {
    case done, missed, planned, rest
}

struct DayStatus: Equatable, Sendable {
    let weekday: Weekday
    let state: DayState
}

/// Port of frontend/src/utils/planSummary.ts.
enum PlanSummary {
    static func volume(week: Int, workouts: [Workout]) -> WeekVolume {
        let items = workouts.filter { $0.weekNumber == week }
        return WeekVolume(
            week: week,
            km: items.reduce(0) { $0 + ($1.distanceKm ?? 0) },
            minutes: items.reduce(0) { $0 + $1.durationMinutes },
            gainM: items.reduce(0) { $0 + ($1.elevationGainM ?? 0) },
            generated: !items.isEmpty
        )
    }

    static func weeklyVolumes(_ workouts: [Workout], totalWeeks: Int) -> [WeekVolume] {
        let lastWeek = max(totalWeeks, workouts.map(\.weekNumber).max() ?? 0)
        guard lastWeek > 0 else { return [] }
        return (1...lastWeek).map { volume(week: $0, workouts: workouts) }
    }

    static func isRestDay(_ dayWorkouts: [Workout]) -> Bool {
        dayWorkouts.allSatisfy(\.isRest)
    }

    static func dayStates(week: Int, workouts: [Workout]) -> [DayStatus] {
        Weekday.allCases.map { day in
            let active = workouts.filter { $0.weekNumber == week && $0.weekday == day && !$0.isRest }
            let state: DayState
            if active.isEmpty { state = .rest }
            else if active.allSatisfy(\.isDone) { state = .done }
            else if active.contains(where: \.isMissedFlag) { state = .missed }
            else { state = .planned }
            return DayStatus(weekday: day, state: state)
        }
    }

    static func phase(week: Int, workouts: [Workout]) -> String? {
        let items = workouts.filter { $0.weekNumber == week }
        return (items.first { !$0.isRest } ?? items.first)?.phase
    }
}
```

- [ ] **Step 4: Run tests**

Run: `ios-native/scripts/test.sh`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add ios-native
git commit -m "feat(ios): plan summary maths ported from the web"
```

---

### Task 4: Plan service

**Files:**
- Create: `ios-native/UphillAI/Core/Plan/PlanService.swift`, `ios-native/UphillAITests/Support/FakePlanService.swift`
- Test: `ios-native/UphillAITests/Plan/PlanServiceTests.swift`

**Interfaces:**
- Consumes: `APIClient`, `Endpoint`, `makeStubClient`, `StubURLProtocol.bodyData` (Phase 0); models (Task 1).
- Produces:
  - `struct WorkoutLogUpdate: Equatable, Sendable { var isCompleted: Int?; var isMissed: Int?; var rpe: Int?; var notes: String? }`
  - `protocol PlanServicing: Sendable` with `activePlan() async throws -> PlanSnapshot?`, `log(workoutID: Int, _ update: WorkoutLogUpdate) async throws -> [Workout]`, `move(planID: Int, workoutID: Int, toWeek: Int, toDay: Weekday, clientToday: String) async throws -> [Workout]`, `recentPlans() async throws -> [Plan]`, `selectPlan(id: Int) async throws -> PlanSnapshot?`
  - `struct PlanService: PlanServicing { let client: APIClient }`
  - Test double `final class FakePlanService: PlanServicing` (below)

Backend contract (`backend/main.py`):
- `GET /api/coach/active-plan` → `{active, plan?, workouts?}`
- `PATCH /api/coach/workouts/log` body `{workout_id, is_completed?, is_missed?, rpe?, notes?}` → `{workouts}`. Setting `is_completed: 1` clears missed, and vice versa.
- `POST /api/coach/calendar/move` body `{plan_id, operations: [{workout_id, target_week, target_day}], client_today}` → `{workouts, warnings}`; 422 `{detail: {code, params}}` on a guard violation.
- `GET /api/coach/recent-plans` → `{plans}`
- `POST /api/coach/select-plan` body `{plan_id}` → `{active, plan, workouts}`

- [ ] **Step 1: Write the test double** `UphillAITests/Support/FakePlanService.swift`

```swift
import Foundation
import Synchronization
@testable import UphillAI

/// Scriptable PlanServicing. Set the results before use; read `calls` after.
final class FakePlanService: PlanServicing {
    let activeResult = Mutex<Result<PlanSnapshot?, APIError>>(.success(nil))
    let logResult = Mutex<Result<[Workout], APIError>>(.success([]))
    let moveResult = Mutex<Result<[Workout], APIError>>(.success([]))
    let recentResult = Mutex<Result<[Plan], APIError>>(.success([]))
    let selectResult = Mutex<Result<PlanSnapshot?, APIError>>(.success(nil))
    let calls = Mutex<[String]>([])

    private func record(_ call: String) { calls.withLock { $0.append(call) } }

    func activePlan() async throws -> PlanSnapshot? {
        record("active")
        return try activeResult.withLock { $0 }.get()
    }

    func log(workoutID: Int, _ update: WorkoutLogUpdate) async throws -> [Workout] {
        record("log \(workoutID) done=\(update.isCompleted.map(String.init) ?? "-") missed=\(update.isMissed.map(String.init) ?? "-") rpe=\(update.rpe.map(String.init) ?? "-")")
        return try logResult.withLock { $0 }.get()
    }

    func move(planID: Int, workoutID: Int, toWeek: Int, toDay: Weekday, clientToday: String) async throws -> [Workout] {
        record("move \(workoutID) -> w\(toWeek) \(toDay.rawValue) today=\(clientToday)")
        return try moveResult.withLock { $0 }.get()
    }

    func recentPlans() async throws -> [Plan] {
        record("recent")
        return try recentResult.withLock { $0 }.get()
    }

    func selectPlan(id: Int) async throws -> PlanSnapshot? {
        record("select \(id)")
        return try selectResult.withLock { $0 }.get()
    }
}
```

- [ ] **Step 2: Write the failing tests** `PlanServiceTests.swift`

```swift
import Foundation
import Testing
@testable import UphillAI

private func body(_ request: URLRequest) throws -> [String: Any] {
    let data = try #require(StubURLProtocol.bodyData(request))
    return try #require(try JSONSerialization.jsonObject(with: data) as? [String: Any])
}

struct PlanServiceTests {
    @Test func activePlanReturnsSnapshot() async throws {
        let fixture = try Fixture.data("active_plan.json")
        let service = PlanService(client: makeStubClient { request in
            #expect(request.url?.path() == "/api/coach/active-plan")
            return (200, fixture)
        })
        let snapshot = try await service.activePlan()
        #expect(snapshot?.workouts.count == 21)
    }

    @Test func activePlanNilWhenInactive() async throws {
        let service = PlanService(client: makeStubClient { _ in (200, json(["active": false])) })
        #expect(try await service.activePlan() == nil)
    }

    @Test func logSendsOnlySetFields() async throws {
        let service = PlanService(client: makeStubClient { request in
            #expect(request.httpMethod == "PATCH")
            #expect(request.url?.path() == "/api/coach/workouts/log")
            let b = try body(request)
            #expect(b["workout_id"] as? Int == 42)
            #expect(b["is_completed"] as? Int == 1)
            #expect(b["rpe"] as? Int == 6)
            #expect(b["is_missed"] == nil)
            #expect(b["notes"] == nil)
            return (200, json(["workouts": []]))
        })
        _ = try await service.log(workoutID: 42, WorkoutLogUpdate(isCompleted: 1, rpe: 6))
    }

    @Test func moveSendsOneOperationWithClientToday() async throws {
        let service = PlanService(client: makeStubClient { request in
            #expect(request.url?.path() == "/api/coach/calendar/move")
            let b = try body(request)
            #expect(b["plan_id"] as? Int == 7)
            #expect(b["client_today"] as? String == "2026-10-01")
            let ops = try #require(b["operations"] as? [[String: Any]])
            #expect(ops.count == 1)
            #expect(ops[0]["workout_id"] as? Int == 42)
            #expect(ops[0]["target_week"] as? Int == 3)
            #expect(ops[0]["target_day"] as? String == "Thursday")
            return (200, json(["workouts": [], "warnings": []]))
        })
        _ = try await service.move(planID: 7, workoutID: 42, toWeek: 3, toDay: .thursday, clientToday: "2026-10-01")
    }

    @Test func moveGuardViolationSurfacesCode() async {
        let service = PlanService(client: makeStubClient { _ in
            (422, json(["detail": ["code": "G4_window", "params": [:]]]))
        })
        await #expect(throws: APIError.http(status: 422, message: nil, code: "G4_window")) {
            _ = try await service.move(planID: 7, workoutID: 42, toWeek: 9, toDay: .monday, clientToday: "2026-10-01")
        }
    }

    @Test func recentAndSelect() async throws {
        let recent = try Fixture.data("recent_plans.json")
        let active = try Fixture.data("active_plan.json")
        let service = PlanService(client: makeStubClient { request in
            switch request.url?.path() {
            case "/api/coach/recent-plans": return (200, recent)
            case "/api/coach/select-plan":
                #expect(try body(request)["plan_id"] as? Int == 5)
                return (200, active)
            default: return (404, Data())
            }
        })
        #expect(try await service.recentPlans().count == 2)
        #expect(try await service.selectPlan(id: 5) != nil)
    }
}
```

- [ ] **Step 3: Run to verify failure**

Run: `ios-native/scripts/test.sh`
Expected: compile errors.

- [ ] **Step 4: Implement** `Core/Plan/PlanService.swift`

```swift
import Foundation

struct WorkoutLogUpdate: Equatable, Sendable {
    var isCompleted: Int?
    var isMissed: Int?
    var rpe: Int?
    var notes: String?
}

protocol PlanServicing: Sendable {
    func activePlan() async throws -> PlanSnapshot?
    func log(workoutID: Int, _ update: WorkoutLogUpdate) async throws -> [Workout]
    func move(planID: Int, workoutID: Int, toWeek: Int, toDay: Weekday, clientToday: String) async throws -> [Workout]
    func recentPlans() async throws -> [Plan]
    func selectPlan(id: Int) async throws -> PlanSnapshot?
}

struct PlanService: PlanServicing {
    let client: APIClient

    private struct WorkoutsResponse: Decodable, Sendable { let workouts: [Workout] }
    private struct RecentResponse: Decodable, Sendable { let plans: [Plan] }

    private struct LogBody: Encodable {
        let workoutId: Int
        let isCompleted: Int?
        let isMissed: Int?
        let rpe: Int?
        let notes: String?
    }

    private struct MoveBody: Encodable {
        struct Operation: Encodable { let workoutId: Int; let targetWeek: Int; let targetDay: String }
        let planId: Int
        let operations: [Operation]
        let clientToday: String
    }

    private struct SelectBody: Encodable { let planId: Int }

    func activePlan() async throws -> PlanSnapshot? {
        let response: ActivePlanResponse = try await client.send(.get("/api/coach/active-plan"))
        return response.snapshot
    }

    func log(workoutID: Int, _ update: WorkoutLogUpdate) async throws -> [Workout] {
        let body = LogBody(workoutId: workoutID, isCompleted: update.isCompleted, isMissed: update.isMissed,
                           rpe: update.rpe, notes: update.notes)
        let response: WorkoutsResponse = try await client.send(.send(.patch, "/api/coach/workouts/log", body: body))
        return response.workouts
    }

    func move(planID: Int, workoutID: Int, toWeek: Int, toDay: Weekday, clientToday: String) async throws -> [Workout] {
        let body = MoveBody(planId: planID,
                            operations: [.init(workoutId: workoutID, targetWeek: toWeek, targetDay: toDay.rawValue)],
                            clientToday: clientToday)
        let response: WorkoutsResponse = try await client.send(.send(.post, "/api/coach/calendar/move", body: body))
        return response.workouts
    }

    func recentPlans() async throws -> [Plan] {
        let response: RecentResponse = try await client.send(.get("/api/coach/recent-plans"))
        return response.plans
    }

    func selectPlan(id: Int) async throws -> PlanSnapshot? {
        let response: ActivePlanResponse = try await client.send(.send(.post, "/api/coach/select-plan", body: SelectBody(planId: id)))
        return response.snapshot
    }
}
```

`JSONEncoder` omits `nil` optionals, which is what makes `logSendsOnlySetFields` pass: the backend only updates fields that are present.

- [ ] **Step 5: Run tests**

Run: `ios-native/scripts/test.sh`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add ios-native
git commit -m "feat(ios): plan service for active plan, logging, moves and recent plans"
```

---

### Task 5: Offline cache and session wiring

**Files:**
- Create: `ios-native/UphillAI/Core/Persistence/OfflineCache.swift`
- Modify: `ios-native/UphillAI/Core/Auth/SessionStore.swift`, `ios-native/UphillAI/App/AppModel.swift`, `ios-native/UphillAITests/App/AppModelTests.swift`
- Test: `ios-native/UphillAITests/Persistence/OfflineCacheTests.swift`

**Interfaces:**
- Consumes: `User` (Phase 0), `PlanSnapshot` (Task 1), `PlanService` (Task 4).
- Produces:
  - `enum CacheKey: String { case user, plan }`
  - `struct Cached<Value> { let value: Value; let savedAt: Date }`
  - `@MainActor final class OfflineCache` with `static func onDisk() -> OfflineCache`, `static func inMemory() -> OfflineCache`, `func save<T: Encodable>(_ value: T, as key: CacheKey, now: Date = .now)`, `func load<T: Decodable>(_ type: T.Type, _ key: CacheKey) -> Cached<T>?`, `func clearAll()`
  - `SessionStore.init(tokenStore:onUserChange:)` where `onUserChange: @MainActor (User?) -> Void` is called with the user on sign-in/`setUser` and `nil` on sign-out
  - `AppModel`: new init parameter `cache: OfflineCache` (default `.onDisk()`), new `let cache: OfflineCache`, `let planService: any PlanServicing`, `private(set) var isOffline: Bool`; `restore()` falls back to the cached user when offline

- [ ] **Step 1: Write the failing tests** `OfflineCacheTests.swift`

```swift
import Foundation
import Testing
@testable import UphillAI

@MainActor
struct OfflineCacheTests {
    @Test func roundTripsAPlanSnapshot() throws {
        let cache = OfflineCache.inMemory()
        let snapshot = try #require(try Fixture.decode(ActivePlanResponse.self, "active_plan.json").snapshot)
        let saved = Date(timeIntervalSince1970: 1_000)
        cache.save(snapshot, as: .plan, now: saved)
        let loaded = try #require(cache.load(PlanSnapshot.self, .plan))
        #expect(loaded.value == snapshot)
        #expect(loaded.savedAt == saved)
    }

    @Test func saveOverwrites() throws {
        let cache = OfflineCache.inMemory()
        let user = try Fixture.decode(User.self, "auth_me.json")
        cache.save(user, as: .user)
        cache.save(user, as: .user)
        #expect(cache.load(User.self, .user)?.value == user)
    }

    @Test func clearAllRemovesEverything() throws {
        let cache = OfflineCache.inMemory()
        cache.save(try Fixture.decode(User.self, "auth_me.json"), as: .user)
        cache.clearAll()
        #expect(cache.load(User.self, .user) == nil)
    }
}
```

Add to `AppModelTests.swift` (and pass `cache: .inMemory()` to every existing `AppModel(...)` call in that file so tests never touch the on-disk store):

```swift
    @Test func restoreOfflineUsesCachedUser() async throws {
        let user = try Fixture.decode(User.self, "auth_me.json")
        let cache = OfflineCache.inMemory()
        cache.save(user, as: .user)
        let app = AppModel(tokenStore: InMemoryTokenStore("saved"),
                           makeAuth: { _ in FakeAuthService(.failure(.transport("offline"))) },
                           cache: cache)
        await app.restore()
        #expect(app.session.user == user)
        #expect(app.isOffline)
    }

    @Test func signInCachesUserAndSignOutClearsCache() async throws {
        let response = try Fixture.decode(AuthResponse.self, "auth_login.json")
        let cache = OfflineCache.inMemory()
        let app = AppModel(tokenStore: InMemoryTokenStore(), makeAuth: { _ in FakeAuthService(.success(response)) }, cache: cache)
        app.session.didSignIn(response)
        #expect(cache.load(User.self, .user)?.value == response.user)
        await app.signOut()
        #expect(cache.load(User.self, .user) == nil)
    }
```

- [ ] **Step 2: Run to verify failure**

Run: `ios-native/scripts/test.sh`
Expected: compile errors.

- [ ] **Step 3: Implement** `Core/Persistence/OfflineCache.swift`

```swift
import Foundation
import SwiftData

enum CacheKey: String {
    case user, plan
}

struct Cached<Value> {
    let value: Value
    let savedAt: Date
}

@Model
final class CacheEntry {
    @Attribute(.unique) var key: String
    var payload: Data
    var savedAt: Date

    init(key: String, payload: Data, savedAt: Date) {
        self.key = key
        self.payload = payload
        self.savedAt = savedAt
    }
}

/// Last-known user and plan, for read-only offline viewing. One signed-in user
/// per device, so entries are keyed by kind only; sign-out clears everything.
@MainActor
final class OfflineCache {
    private let context: ModelContext

    private init(container: ModelContainer) {
        context = ModelContext(container)
    }

    static func onDisk() -> OfflineCache {
        let container = try! ModelContainer(for: CacheEntry.self)
        return OfflineCache(container: container)
    }

    static func inMemory() -> OfflineCache {
        let container = try! ModelContainer(for: CacheEntry.self, configurations: ModelConfiguration(isStoredInMemoryOnly: true))
        return OfflineCache(container: container)
    }

    func save<T: Encodable>(_ value: T, as key: CacheKey, now: Date = .now) {
        guard let payload = try? JSONCoding.encoder.encode(value) else { return }
        if let entry = entry(key) {
            entry.payload = payload
            entry.savedAt = now
        } else {
            context.insert(CacheEntry(key: key.rawValue, payload: payload, savedAt: now))
        }
        try? context.save()
    }

    func load<T: Decodable>(_ type: T.Type, _ key: CacheKey) -> Cached<T>? {
        guard let entry = entry(key),
              let value = try? JSONCoding.decoder.decode(T.self, from: entry.payload) else { return nil }
        return Cached(value: value, savedAt: entry.savedAt)
    }

    func clearAll() {
        try? context.delete(model: CacheEntry.self)
        try? context.save()
    }

    private func entry(_ key: CacheKey) -> CacheEntry? {
        let raw = key.rawValue
        var descriptor = FetchDescriptor<CacheEntry>(predicate: #Predicate { $0.key == raw })
        descriptor.fetchLimit = 1
        return try? context.fetch(descriptor).first
    }
}
```

The cache is a best-effort convenience: a failed write or a payload that no longer decodes after an app update behaves like an empty cache. `try!` on container creation is deliberate: a store that can't open is a programmer error caught in development.

- [ ] **Step 4: Add the hook to** `SessionStore.swift`

Replace the stored properties and init, and call the hook from the three mutators:

```swift
    private(set) var state: State
    private let tokenStore: any TokenStore
    private let onUserChange: @MainActor (User?) -> Void

    init(tokenStore: any TokenStore, onUserChange: @escaping @MainActor (User?) -> Void = { _ in }) {
        self.tokenStore = tokenStore
        self.onUserChange = onUserChange
        state = tokenStore.read() == nil ? .signedOut : .restoring
    }
```

```swift
    func didSignIn(_ response: AuthResponse) {
        tokenStore.write(response.sessionToken)
        state = .signedIn(response.user)
        onUserChange(response.user)
    }

    func setUser(_ user: User) {
        state = .signedIn(user)
        onUserChange(user)
    }

    func signOut() {
        tokenStore.write(nil)
        state = .signedOut
        onUserChange(nil)
    }
```

- [ ] **Step 5: Update** `AppModel.swift`

```swift
@Observable
@MainActor
final class AppModel {
    let session: SessionStore
    let client: APIClient
    let auth: any AuthServicing
    let planService: any PlanServicing
    let cache: OfflineCache
    private(set) var restoreError: String?
    /// True when the last restore had to fall back to cached data.
    private(set) var isOffline = false

    init(
        tokenStore: any TokenStore,
        makeAuth: (APIClient) -> any AuthServicing = { AuthService(client: $0) },
        baseURL: @escaping @Sendable () -> URL = { AppEnvironment.current().baseURL },
        session urlSession: URLSession = .shared,
        cache: OfflineCache = .onDisk()
    ) {
        self.cache = cache
        let session = SessionStore(tokenStore: tokenStore) { user in
            if let user { cache.save(user, as: .user) } else { cache.clearAll() }
        }
        self.session = session
        client = APIClient(
            baseURL: baseURL,
            tokenStore: tokenStore,
            session: urlSession,
            onUnauthorized: { await session.signOut() }
        )
        auth = makeAuth(client)
        planService = PlanService(client: client)
    }

    /// Confirms a stored token with /api/auth/me. Offline, it signs in with the
    /// cached user (read-only) when there is one, and keeps the token either way.
    func restore() async {
        guard session.state == .restoring else { return }
        restoreError = nil
        do {
            session.setUser(try await auth.me())
            isOffline = false
        } catch APIError.unauthorized {
            session.signOut()
        } catch let error as APIError {
            if case .transport = error, let cached = cache.load(User.self, .user) {
                isOffline = true
                session.setUser(cached.value)
            } else {
                restoreError = error.userMessage
            }
        } catch {
            restoreError = error.localizedDescription
        }
    }

    func signOut() async {
        await auth.logout()
        session.signOut()
    }
}
```

- [ ] **Step 6: Run tests**

Run: `ios-native/scripts/test.sh`
Expected: all pass, including the updated Phase 0 `AppModelTests`.

- [ ] **Step 7: Commit**

```bash
git add ios-native
git commit -m "feat(ios): SwiftData offline cache for user and plan, cleared on sign-out"
```

---

### Task 6: Plan view model

**Files:**
- Create: `ios-native/UphillAI/Features/Plan/PlanViewModel.swift`
- Test: `ios-native/UphillAITests/Plan/PlanViewModelTests.swift`

**Interfaces:**
- Consumes: `PlanServicing`, `FakePlanService` (Task 4); `OfflineCache` (Task 5); `PlanCalendar` (Task 2); `PlanSummary` (Task 3); `APIError`.
- Produces:
  - `struct PlanDay: Identifiable, Equatable { let week: Int; let weekday: Weekday; let date: Date?; let workouts: [Workout]; let eyebrow: String?; var id: String; var isRest: Bool; var isCollapsed: Bool }` (`isCollapsed` = rest day with no done/missed workout)
  - `struct MoveTarget: Identifiable, Hashable { let week: Int; let weekday: Weekday; let date: Date; var id: String }`
  - `@Observable @MainActor final class PlanViewModel` with:
    - `enum LoadState: Equatable { case loading, empty, loaded, failed(String) }`
    - `private(set) var state`, `private(set) var snapshot: PlanSnapshot?`, `private(set) var cachedAt: Date?` (non-nil while showing cached data), `var selectedWeek: Int`, `private(set) var actionError: String?`, `private(set) var lastCompletedID: Int?`
    - `init(service: any PlanServicing, cache: OfflineCache, now: @escaping @MainActor () -> Date = { .now }, calendar: Calendar = PlanCalendar.calendar)`
    - `func load() async`
    - `var currentWeek: Int`, `var weeks: [Int]`, `var days: [PlanDay]` (selected week, Mon–Sun), `var selectedVolume: WeekVolume`, `var weeklyVolumes: [WeekVolume]`, `var dayStates: [DayStatus]`, `var phase: String?`, `var daysToRace: Int?`, `var goalText: String?`
    - `func setDone(_ workout: Workout, _ done: Bool) async`, `func setMissed(_ workout: Workout) async`, `func saveLog(_ workout: Workout, rpe: Int?, notes: String) async -> Bool`
    - `func moveTargets(for workout: Workout) -> [MoveTarget]`, `func move(_ workout: Workout, to target: MoveTarget) async -> Bool`
    - `func recentPlans() async -> [Plan]`, `func select(_ plan: Plan) async`
    - `func clearActionError()`
    - `static let offlineMessage = "You're offline. Changes need a connection."`
    - `static func moveMessage(code: String?) -> String`

Behaviour:
1. `load()` shows the cached snapshot first (state `.loaded`, `cachedAt` set), then fetches. Success: replace, save to cache, clear `cachedAt`. `nil` snapshot: state `.empty`, cache cleared for `.plan` by saving nothing (call `cache.clearAll()` is wrong because it also drops the user; instead keep the stale entry but show `.empty`). Transport error with cache: keep showing cache. Any error without cache: `.failed(message)`.
2. On the first successful load (and after `select`), `selectedWeek = PlanCalendar.resolveCurrentWeek(...)`.
3. Writes when `cachedAt != nil` set `actionError = offlineMessage` and do not call the service.
4. After a successful write, replace `snapshot.workouts` with the response and save the snapshot to the cache.
5. `setDone(_, true)` sends `is_completed: 1` and sets `lastCompletedID` (drives the success haptic); `setDone(_, false)` sends `is_completed: 0, is_missed: 0`. `setMissed` sends `is_missed: 1`.
6. `moveTargets` lists every day from today through the Sunday of the week after the current week, within `1...totalWeeks`, excluding the workout's own day.
7. Move guard codes map to messages: `G2_history` "Completed or synced workouts can't be moved.", `G3_past_target` "Workouts can't be moved into the past.", `G4_window` "Workouts can only move within this week or into next week.", `G5_out_of_plan` "That day is outside your plan.", `G6_coach_linked` "Your coach manages this workout.", anything else "This workout can't be moved right now."
8. `goalText`: `goal_type == "time"` with `target_time_hours` → "Goal 6h 30m"; `"finish"` → "Goal: finish strong"; `"optimal"` → "Goal: best possible time"; otherwise nil.

- [ ] **Step 1: Write the failing tests** `PlanViewModelTests.swift`

```swift
import Foundation
import Testing
@testable import UphillAI

@MainActor
struct PlanViewModelTests {
    private let cal: Calendar = {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        return c
    }()

    /// Wednesday of week 2 for a plan starting Monday 2026-09-28.
    private var now: Date { cal.date(from: DateComponents(year: 2026, month: 10, day: 7, hour: 9))! }

    private func snapshot() -> PlanSnapshot {
        let plan = TestData.plan(["id": 7, "start_date": "2026-09-28", "total_weeks": 12, "race_date": "2026-12-19",
                                  "goal_type": "time", "target_time_hours": 6.5])
        var workouts: [Workout] = []
        var id = 1
        for week in 1...3 {
            for day in Weekday.allCases {
                let rest = day == .monday || day == .thursday
                workouts.append(TestData.workout([
                    "id": id, "plan_id": 7, "week_number": week, "day_of_week": day.rawValue,
                    "type": rest ? "Rest" : "Easy Run", "duration_minutes": rest ? 0 : 45,
                    "is_priority": day == .saturday,
                ]))
                id += 1
            }
        }
        return PlanSnapshot(plan: plan, workouts: workouts)
    }

    private func make(_ service: FakePlanService, cache: OfflineCache = .inMemory()) -> PlanViewModel {
        let now = self.now
        return PlanViewModel(service: service, cache: cache, now: { now }, calendar: cal)
    }

    @Test func loadSelectsCurrentWeekAndCaches() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        let cache = OfflineCache.inMemory()
        let model = make(service, cache: cache)
        await model.load()
        #expect(model.state == .loaded)
        #expect(model.selectedWeek == 2)
        #expect(model.currentWeek == 2)
        #expect(model.cachedAt == nil)
        #expect(cache.load(PlanSnapshot.self, .plan) != nil)
    }

    @Test func daysForSelectedWeek() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        let model = make(service)
        await model.load()
        let days = model.days
        #expect(days.map(\.weekday) == Weekday.allCases)
        #expect(days[0].isCollapsed)                         // Monday rest
        #expect(days[2].eyebrow == "TODAY")                  // Wednesday 2026-10-07
        #expect(days[3].eyebrow == "TOMORROW")
        #expect(days[5].workouts.first?.isPriority == true)  // Saturday
    }

    @Test func restDayWithLoggedWorkoutStaysExpanded() async {
        var snap = snapshot()
        let mondayIndex = snap.workouts.firstIndex { $0.weekNumber == 2 && $0.weekday == .monday }!
        snap.workouts[mondayIndex] = TestData.workout(["id": 99, "plan_id": 7, "week_number": 2, "day_of_week": "Monday",
                                                       "type": "Rest", "duration_minutes": 0, "is_completed": 1])
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snap) }
        let model = make(service)
        await model.load()
        #expect(model.days[0].isRest)
        #expect(!model.days[0].isCollapsed)
    }

    @Test func emptyWhenNoPlan() async {
        let model = make(FakePlanService())
        await model.load()
        #expect(model.state == .empty)
    }

    @Test func offlineShowsCacheAndBlocksWrites() async throws {
        let cache = OfflineCache.inMemory()
        let saved = Date(timeIntervalSince1970: 5_000)
        cache.save(snapshot(), as: .plan, now: saved)
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .failure(.transport("offline")) }
        let model = make(service, cache: cache)
        await model.load()
        #expect(model.state == .loaded)
        #expect(model.cachedAt == saved)
        let workout = try #require(model.days[2].workouts.first)
        await model.setDone(workout, true)
        #expect(model.actionError == PlanViewModel.offlineMessage)
        #expect(service.calls.withLock { $0 } == ["active"])
    }

    @Test func failedWithoutCache() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .failure(.transport("offline")) }
        let model = make(service)
        await model.load()
        #expect(model.state == .failed(APIError.transport("offline").userMessage))
    }

    @Test func markDoneUpdatesWorkoutsAndCache() async throws {
        let snap = snapshot()
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snap) }
        let target = snap.workouts.first { $0.weekNumber == 2 && $0.weekday == .wednesday }!
        let updated = snap.workouts.map { $0.id == target.id
            ? TestData.workout(["id": target.id, "plan_id": 7, "week_number": 2, "day_of_week": "Wednesday", "is_completed": 1])
            : $0 }
        service.logResult.withLock { $0 = .success(updated) }
        let cache = OfflineCache.inMemory()
        let model = make(service, cache: cache)
        await model.load()
        await model.setDone(target, true)
        #expect(service.calls.withLock { $0 }.last == "log \(target.id) done=1 missed=- rpe=-")
        #expect(model.days[2].workouts.first?.isDone == true)
        #expect(model.lastCompletedID == target.id)
        #expect(cache.load(PlanSnapshot.self, .plan)?.value.workouts == updated)
    }

    @Test func undoDoneClearsBothFlags() async throws {
        let snap = snapshot()
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snap) }
        service.logResult.withLock { $0 = .success(snap.workouts) }
        let model = make(service)
        await model.load()
        await model.setDone(snap.workouts[1], false)
        #expect(service.calls.withLock { $0 }.last == "log 2 done=0 missed=0 rpe=-")
    }

    @Test func moveTargetsRunFromTodayToEndOfNextWeek() async throws {
        let snap = snapshot()
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snap) }
        let model = make(service)
        await model.load()
        let saturday = snap.workouts.first { $0.weekNumber == 2 && $0.weekday == .saturday }!
        let targets = model.moveTargets(for: saturday)
        #expect(targets.first?.week == 2)
        #expect(targets.first?.weekday == .wednesday)        // today
        #expect(targets.last?.week == 3)
        #expect(targets.last?.weekday == .sunday)
        #expect(!targets.contains { $0.week == 2 && $0.weekday == .saturday })
        #expect(targets.count == 4 + 7)                      // Wed–Sun of week 2 minus Saturday (4), all of week 3 (7)
    }

    @Test func moveSendsClientTodayAndMapsGuardErrors() async throws {
        let snap = snapshot()
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snap) }
        service.moveResult.withLock { $0 = .failure(.http(status: 422, message: nil, code: "G4_window")) }
        let model = make(service)
        await model.load()
        let workout = snap.workouts.first { $0.weekNumber == 2 && $0.weekday == .saturday }!
        let target = try #require(model.moveTargets(for: workout).first { $0.week == 3 && $0.weekday == .tuesday })
        let ok = await model.move(workout, to: target)
        #expect(!ok)
        #expect(service.calls.withLock { $0 }.last == "move \(workout.id) -> w3 Tuesday today=2026-10-07")
        #expect(model.actionError == "Workouts can only move within this week or into next week.")
    }

    @Test func summaryValues() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        let model = make(service)
        await model.load()
        #expect(model.goalText == "Goal 6h 30m")
        #expect(model.daysToRace == 73)
        #expect(model.phase == "Base")
        #expect(model.selectedVolume.minutes == 5 * 45)
        #expect(model.weeks == Array(1...12))
    }

    @Test func selectPlanReloadsAndResetsWeek() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        service.selectResult.withLock { $0 = .success(snapshot()) }
        let model = make(service)
        await model.load()
        model.selectedWeek = 5
        await model.select(TestData.plan(["id": 3]))
        #expect(service.calls.withLock { $0 }.last == "select 3")
        #expect(model.selectedWeek == 2)
    }
}
```

- [ ] **Step 2: Run to verify failure**

Run: `ios-native/scripts/test.sh`
Expected: compile error, `PlanViewModel` not found.

- [ ] **Step 3: Implement** `Features/Plan/PlanViewModel.swift`

```swift
import Foundation
import Observation

struct PlanDay: Identifiable, Equatable {
    let week: Int
    let weekday: Weekday
    let date: Date?
    let workouts: [Workout]
    let eyebrow: String?

    var id: String { "\(week)-\(weekday.rawValue)" }
    var isRest: Bool { PlanSummary.isRestDay(workouts) }
    /// Rest days collapse unless something on them was logged.
    var isCollapsed: Bool { isRest && !workouts.contains { $0.isDone || $0.isMissedFlag } }
}

struct MoveTarget: Identifiable, Hashable {
    let week: Int
    let weekday: Weekday
    let date: Date
    var id: String { "\(week)-\(weekday.rawValue)" }
}

@Observable
@MainActor
final class PlanViewModel {
    enum LoadState: Equatable { case loading, empty, loaded, failed(String) }

    static let offlineMessage = "You're offline. Changes need a connection."

    private(set) var state: LoadState = .loading
    private(set) var snapshot: PlanSnapshot?
    /// Set while the screen shows cached data because the last fetch failed.
    private(set) var cachedAt: Date?
    var selectedWeek = 1
    private(set) var actionError: String?
    /// Last workout marked done; the view keys its success haptic on it.
    private(set) var lastCompletedID: Int?

    private let service: any PlanServicing
    private let cache: OfflineCache
    private let now: @MainActor () -> Date
    private let calendar: Calendar

    init(service: any PlanServicing, cache: OfflineCache,
         now: @escaping @MainActor () -> Date = { .now }, calendar: Calendar = PlanCalendar.calendar) {
        self.service = service
        self.cache = cache
        self.now = now
        self.calendar = calendar
    }

    // MARK: Loading

    func load() async {
        let hadSnapshot = snapshot != nil
        if !hadSnapshot, let cached = cache.load(PlanSnapshot.self, .plan) {
            apply(cached.value, resetWeek: true)
            cachedAt = cached.savedAt
        }
        do {
            if let fresh = try await service.activePlan() {
                let resetWeek = !hadSnapshot && cachedAt == nil
                apply(fresh, resetWeek: resetWeek)
                cachedAt = nil
                cache.save(fresh, as: .plan)
            } else {
                snapshot = nil
                cachedAt = nil
                state = .empty
            }
        } catch let error as APIError {
            if case .transport = error, snapshot != nil { return }   // keep showing the cache
            if snapshot == nil { state = .failed(error.userMessage) }
        } catch {
            if snapshot == nil { state = .failed(error.localizedDescription) }
        }
    }

    private func apply(_ snapshot: PlanSnapshot, resetWeek: Bool) {
        self.snapshot = snapshot
        state = .loaded
        if resetWeek { selectedWeek = currentWeek }
    }

    // MARK: Derived values

    var currentWeek: Int {
        guard let snapshot else { return 1 }
        return PlanCalendar.resolveCurrentWeek(plan: snapshot.plan, workouts: snapshot.workouts, now: now(), calendar: calendar)
    }

    var weeks: [Int] {
        guard let snapshot else { return [] }
        let last = max(snapshot.plan.totalWeeks, snapshot.workouts.map(\.weekNumber).max() ?? 0)
        return last > 0 ? Array(1...last) : []
    }

    var days: [PlanDay] {
        guard let snapshot else { return [] }
        let today = now()
        return Weekday.allCases.map { weekday in
            let date = PlanCalendar.date(week: selectedWeek, weekday: weekday, plan: snapshot.plan,
                                         workouts: snapshot.workouts, calendar: calendar)
            return PlanDay(
                week: selectedWeek,
                weekday: weekday,
                date: date,
                workouts: snapshot.workouts.filter { $0.weekNumber == selectedWeek && $0.weekday == weekday },
                eyebrow: PlanCalendar.eyebrow(for: date, now: today, calendar: calendar)
            )
        }
    }

    var selectedVolume: WeekVolume { PlanSummary.volume(week: selectedWeek, workouts: snapshot?.workouts ?? []) }

    var weeklyVolumes: [WeekVolume] {
        guard let snapshot else { return [] }
        return PlanSummary.weeklyVolumes(snapshot.workouts, totalWeeks: snapshot.plan.totalWeeks)
    }

    var dayStates: [DayStatus] {
        PlanSummary.dayStates(week: selectedWeek, workouts: snapshot?.workouts ?? [])
    }

    var phase: String? { PlanSummary.phase(week: selectedWeek, workouts: snapshot?.workouts ?? []) }

    var daysToRace: Int? { PlanCalendar.daysToRace(snapshot?.plan.raceDate, now: now(), calendar: calendar) }

    var goalText: String? {
        guard let plan = snapshot?.plan else { return nil }
        switch plan.goalType {
        case "time":
            guard let hours = plan.targetTimeHours else { return nil }
            let total = Int((hours * 60).rounded())
            return "Goal \(total / 60)h \(String(format: "%02d", total % 60))m"
        case "finish": return "Goal: finish strong"
        case "optimal": return "Goal: best possible time"
        default: return nil
        }
    }

    // MARK: Writes

    func clearActionError() { actionError = nil }

    func setDone(_ workout: Workout, _ done: Bool) async {
        let update = done ? WorkoutLogUpdate(isCompleted: 1) : WorkoutLogUpdate(isCompleted: 0, isMissed: 0)
        if await write({ try await self.service.log(workoutID: workout.id, update) }), done {
            lastCompletedID = workout.id
        }
    }

    func setMissed(_ workout: Workout) async {
        _ = await write { try await self.service.log(workoutID: workout.id, WorkoutLogUpdate(isMissed: 1)) }
    }

    func saveLog(_ workout: Workout, rpe: Int?, notes: String) async -> Bool {
        await write { try await self.service.log(workoutID: workout.id, WorkoutLogUpdate(rpe: rpe, notes: notes)) }
    }

    func moveTargets(for workout: Workout) -> [MoveTarget] {
        guard let snapshot else { return [] }
        let today = calendar.startOfDay(for: now())
        let lastWeek = min(currentWeek + 1, snapshot.plan.totalWeeks)
        var targets: [MoveTarget] = []
        for week in currentWeek...max(currentWeek, lastWeek) {
            for weekday in Weekday.allCases {
                if week == workout.weekNumber && weekday == workout.weekday { continue }
                guard let date = PlanCalendar.date(week: week, weekday: weekday, plan: snapshot.plan,
                                                   workouts: snapshot.workouts, calendar: calendar),
                      date >= today else { continue }
                targets.append(MoveTarget(week: week, weekday: weekday, date: date))
            }
        }
        return targets
    }

    func move(_ workout: Workout, to target: MoveTarget) async -> Bool {
        guard let planID = snapshot?.plan.id else { return false }
        let today = PlanCalendar.ymd(now(), calendar: calendar)
        return await write {
            try await self.service.move(planID: planID, workoutID: workout.id,
                                        toWeek: target.week, toDay: target.weekday, clientToday: today)
        }
    }

    static func moveMessage(code: String?) -> String {
        switch code {
        case "G2_history": "Completed or synced workouts can't be moved."
        case "G3_past_target": "Workouts can't be moved into the past."
        case "G4_window": "Workouts can only move within this week or into next week."
        case "G5_out_of_plan": "That day is outside your plan."
        case "G6_coach_linked": "Your coach manages this workout."
        default: "This workout can't be moved right now."
        }
    }

    /// Runs a write that returns the plan's workouts. Returns true on success.
    private func write(_ operation: () async throws -> [Workout]) async -> Bool {
        guard cachedAt == nil else {
            actionError = Self.offlineMessage
            return false
        }
        actionError = nil
        do {
            let workouts = try await operation()
            guard var snapshot else { return false }
            snapshot.workouts = workouts
            self.snapshot = snapshot
            cache.save(snapshot, as: .plan)
            return true
        } catch APIError.http(422, _, let code?) {
            actionError = Self.moveMessage(code: code)
        } catch let error as APIError {
            actionError = error.userMessage
        } catch {
            actionError = error.localizedDescription
        }
        return false
    }

    // MARK: Recent plans

    func recentPlans() async -> [Plan] {
        (try? await service.recentPlans()) ?? []
    }

    func select(_ plan: Plan) async {
        guard cachedAt == nil else {
            actionError = Self.offlineMessage
            return
        }
        do {
            if let snapshot = try await service.selectPlan(id: plan.id) {
                apply(snapshot, resetWeek: true)
                cache.save(snapshot, as: .plan)
            }
        } catch let error as APIError {
            actionError = error.userMessage
        } catch {
            actionError = error.localizedDescription
        }
    }
}
```

Note on `moveTargets`: the test plan's week 2 is the current week, so targets are Wednesday–Sunday of week 2 (minus the workout's own Saturday) plus all of week 3.

Note on the empty state (Behaviour 1): when the server says there is no active plan, the stale `.plan` cache entry is left in place but not shown; it is overwritten on the next successful load and removed on sign-out.

- [ ] **Step 4: Run tests**

Run: `ios-native/scripts/test.sh`
Expected: all pass. `daysToRace == 73`: from 2026-10-07 to 2026-12-19 is 73 days.

- [ ] **Step 5: Commit**

```bash
git add ios-native
git commit -m "feat(ios): plan view model with offline-aware writes and moves"
```

---

### Task 7: Tab shell, Plan screen and summary carousel

**Files:**
- Create: `ios-native/UphillAI/Features/Plan/PlanView.swift`, `ios-native/UphillAI/Features/Plan/SummaryCarousel.swift`, `ios-native/UphillAI/Features/Plan/WeekSwitcher.swift`
- Modify: `ios-native/UphillAI/App/RootView.swift`

**Interfaces:**
- Consumes: `PlanViewModel` (Task 6), `AppModel.planService`, `AppModel.cache`, `AppModel.isOffline` (Task 5).
- Produces: `struct PlanView` (`init(model:)`); `struct SummaryCarousel` (`init(model:)`); `struct WeekSwitcher` (`init(weeks:selected:currentWeek:)`, `selected` is a `Binding<Int>`); in `RootView`, the signed-in `TabView` with tabs **Plan** (`figure.run`) and **Me** (`person.crop.circle`). Task 8 fills the day list inside `PlanView`; until then it shows the carousel and week switcher only.

Layout (mirrors web Phase 1):
- Navigation title: the plan's race name (inline display mode). Trailing toolbar button "Manage" (Task 9 wires it; in this task it is present but disabled).
- Offline banner when `model.cachedAt != nil`: "Offline · showing your plan from <relative time>" on `UH.Palette.hover`, `wifi.slash` icon.
- Summary carousel: four cards, horizontally paged with a peek of the next card, page dots under it.
  1. **Volume**: "Week N volume", big `km` metric, hours and elevation gain, and a Swift Charts bar chart of every week's km (selected week in `accent`, others in `line`, ungenerated weeks hidden).
  2. **Race**: race name, date formatted "Sat 19 Dec", "N days to go" (or "Race week" at 0–6 days), and `goalText`.
  3. **This week**: seven day dots labelled M T W T F S S; done = filled accent with `checkmark`, missed = `xmark` in `danger`, planned = outlined circle, rest = small muted dot. Shapes differ by state; colour is never the only signal. VoiceOver label per dot: "Tuesday, done".
  4. **Phase**: phase name for the selected week (e.g. "Base"), "Week N of total".
- Week switcher: "Week N" title with chevron buttons (44×44 pt), current week marked "This week". Changing week plays `.selection` haptic and animates with `UH.Motion.standard`.
- States: `.loading` → `ProgressView`; `.empty` → "No active plan yet" + "Create your first plan on uphill-ai.io.vn for now. Plan creation is coming to the app soon."; `.failed(message)` → message + "Try again" button. `.refreshable { await model.load() }` on the scroll view.

- [ ] **Step 1: Implement** `RootView.swift` signed-in tabs

Replace the `.signedIn` case and add `MainTabs`:

```swift
            case .signedIn:
                MainTabs(app: app)
```

```swift
/// Owns the per-session Plan view model. Recreated after sign-out/in.
private struct MainTabs: View {
    let app: AppModel
    @State private var plan: PlanViewModel

    init(app: AppModel) {
        self.app = app
        _plan = State(initialValue: PlanViewModel(service: app.planService, cache: app.cache))
    }

    var body: some View {
        TabView {
            Tab("Plan", systemImage: "figure.run") {
                PlanView(model: plan)
            }
            Tab("Me", systemImage: "person.crop.circle") {
                ProfileView(app: app)
            }
        }
    }
}
```

- [ ] **Step 2: Implement** `WeekSwitcher.swift`

```swift
import SwiftUI

struct WeekSwitcher: View {
    let weeks: [Int]
    @Binding var selected: Int
    let currentWeek: Int

    var body: some View {
        HStack {
            stepButton("chevron.left", label: "Previous week", to: selected - 1)
            Spacer()
            VStack(spacing: 2) {
                Text("Week \(selected)")
                    .font(UH.TextStyle.sectionTitle)
                    .foregroundStyle(UH.Palette.ink)
                    .contentTransition(.numericText())
                Text(selected == currentWeek ? "This week" : " ")
                    .font(UH.TextStyle.eyebrow)
                    .foregroundStyle(UH.Palette.accentInk)
            }
            .accessibilityElement(children: .combine)
            Spacer()
            stepButton("chevron.right", label: "Next week", to: selected + 1)
        }
        .sensoryFeedback(.selection, trigger: selected)
    }

    private func stepButton(_ icon: String, label: String, to week: Int) -> some View {
        Button {
            withAnimation(UH.Motion.standard) { selected = week }
        } label: {
            Image(systemName: icon)
                .font(.body.weight(.semibold))
                .frame(width: 44, height: 44)
        }
        .disabled(!weeks.contains(week))
        .accessibilityLabel(label)
    }
}
```

- [ ] **Step 3: Implement** `SummaryCarousel.swift`

```swift
import Charts
import SwiftUI

struct SummaryCarousel: View {
    let model: PlanViewModel
    @State private var page: Int? = 0

    var body: some View {
        VStack(spacing: UH.Space.compact) {
            ScrollView(.horizontal) {
                LazyHStack(spacing: UH.Space.small) {
                    volumeCard.id(0)
                    raceCard.id(1)
                    weekCard.id(2)
                    phaseCard.id(3)
                }
                .scrollTargetLayout()
            }
            .scrollTargetBehavior(.viewAligned)
            .scrollPosition(id: $page)
            .scrollIndicators(.hidden)
            .contentMargins(.horizontal, UH.Space.medium, for: .scrollContent)

            HStack(spacing: 6) {
                ForEach(0..<4, id: \.self) { index in
                    Circle()
                        .fill(index == (page ?? 0) ? UH.Palette.accentInk : UH.Palette.line)
                        .frame(width: 6, height: 6)
                }
            }
            .accessibilityHidden(true)
        }
    }

    private func card(_ content: some View) -> some View {
        content
            .uhCard()
            .containerRelativeFrame(.horizontal) { width, _ in width - 2 * UH.Space.medium - 24 }
            .frame(height: 176)
    }

    private func eyebrow(_ text: String) -> some View {
        Text(text.uppercased()).font(UH.TextStyle.eyebrow).tracking(0.6).foregroundStyle(UH.Palette.muted)
    }

    private var volumeCard: some View {
        let volume = model.selectedVolume
        return card(
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                eyebrow("Week \(model.selectedWeek) volume")
                HStack(alignment: .firstTextBaseline, spacing: 4) {
                    Text(volume.km, format: .number.precision(.fractionLength(0...1)))
                        .font(UH.TextStyle.metric)
                    Text("km").font(UH.TextStyle.label).foregroundStyle(UH.Palette.secondary)
                }
                .foregroundStyle(UH.Palette.ink)
                Text("\(volume.hours, format: .number.precision(.fractionLength(0...1))) h · \(Int(volume.gainM)) m gain")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                Chart(model.weeklyVolumes.filter(\.generated), id: \.week) { week in
                    BarMark(x: .value("Week", week.week), y: .value("km", week.km))
                        .foregroundStyle(week.week == model.selectedWeek ? UH.Palette.accent : UH.Palette.line)
                        .cornerRadius(2)
                }
                .chartXAxis(.hidden)
                .chartYAxis(.hidden)
                .accessibilityHidden(true)
            }
        )
        .accessibilityElement(children: .combine)
    }

    private var raceCard: some View {
        let plan = model.snapshot?.plan
        let raceDay = PlanCalendar.day(from: plan?.raceDate)
        return card(
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                eyebrow("Race")
                Text(plan?.raceName ?? "")
                    .font(UH.TextStyle.sectionTitle)
                    .foregroundStyle(UH.Palette.ink)
                    .lineLimit(2)
                if let raceDay {
                    Text(raceDay, format: .dateTime.weekday(.abbreviated).day().month(.abbreviated))
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }
                Spacer(minLength: 0)
                if let days = model.daysToRace {
                    Text(days < 7 ? "Race week" : "\(days) days to go")
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.accentInk)
                }
                if let goal = model.goalText {
                    Text(goal).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                }
            }
        )
        .accessibilityElement(children: .combine)
    }

    private var weekCard: some View {
        card(
            VStack(alignment: .leading, spacing: UH.Space.small) {
                eyebrow(model.selectedWeek == model.currentWeek ? "This week" : "Week \(model.selectedWeek)")
                HStack(spacing: 0) {
                    ForEach(model.dayStates, id: \.weekday) { item in
                        VStack(spacing: 6) {
                            Text(String(item.weekday.rawValue.prefix(1)))
                                .font(UH.TextStyle.eyebrow)
                                .foregroundStyle(UH.Palette.muted)
                            dot(item.state)
                        }
                        .frame(maxWidth: .infinity)
                        .accessibilityElement(children: .ignore)
                        .accessibilityLabel("\(item.weekday.rawValue), \(label(item.state))")
                    }
                }
                Spacer(minLength: 0)
                let done = model.dayStates.filter { $0.state == .done }.count
                let active = model.dayStates.filter { $0.state != .rest }.count
                Text("\(done) of \(active) sessions done")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }
        )
    }

    @ViewBuilder
    private func dot(_ state: DayState) -> some View {
        switch state {
        case .done:
            Image(systemName: "checkmark.circle.fill").foregroundStyle(UH.Palette.accentInk).font(.title3)
        case .missed:
            Image(systemName: "xmark.circle").foregroundStyle(UH.Palette.danger).font(.title3)
        case .planned:
            Image(systemName: "circle").foregroundStyle(UH.Palette.secondary).font(.title3)
        case .rest:
            Circle().fill(UH.Palette.line).frame(width: 6, height: 6).frame(height: 22)
        }
    }

    private func label(_ state: DayState) -> String {
        switch state {
        case .done: "done"
        case .missed: "missed"
        case .planned: "planned"
        case .rest: "rest"
        }
    }

    private var phaseCard: some View {
        card(
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                eyebrow("Phase")
                Text(model.phase ?? "Not generated yet")
                    .font(UH.TextStyle.metric)
                    .foregroundStyle(UH.Palette.ink)
                Text("Week \(model.selectedWeek) of \(model.snapshot?.plan.totalWeeks ?? 0)")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }
        )
        .accessibilityElement(children: .combine)
    }
}
```

- [ ] **Step 4: Implement** `PlanView.swift`

```swift
import SwiftUI

struct PlanView: View {
    @Bindable var model: PlanViewModel

    var body: some View {
        NavigationStack {
            content
                .background(UH.Palette.surface.ignoresSafeArea())
                .navigationTitle(model.snapshot?.plan.raceName ?? "Plan")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button("Manage") {}
                            .disabled(true)   // Task 9
                    }
                }
        }
        .task { if model.state == .loading { await model.load() } }
    }

    @ViewBuilder
    private var content: some View {
        switch model.state {
        case .loading:
            ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
        case .empty:
            message(title: "No active plan yet",
                    body: "Create your first plan on uphill-ai.io.vn for now. Plan creation is coming to the app soon.")
        case .failed(let error):
            VStack(spacing: UH.Space.regular) {
                message(title: "Couldn't load your plan", body: error)
                Button("Try again") { Task { await model.load() } }
                    .buttonStyle(.uhPrimary)
                    .frame(maxWidth: 220)
            }
        case .loaded:
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    if let cachedAt = model.cachedAt { offlineBanner(cachedAt) }
                    SummaryCarousel(model: model)
                    WeekSwitcher(weeks: model.weeks, selected: $model.selectedWeek, currentWeek: model.currentWeek)
                        .padding(.horizontal, UH.Space.regular)
                    // Task 8 adds the day list here.
                }
                .padding(.vertical, UH.Space.regular)
            }
            .refreshable { await model.load() }
        }
    }

    private func offlineBanner(_ date: Date) -> some View {
        Label {
            Text("Offline · showing your plan from \(date, format: .relative(presentation: .named))")
        } icon: {
            Image(systemName: "wifi.slash")
        }
        .font(UH.TextStyle.caption)
        .foregroundStyle(UH.Palette.secondary)
        .padding(UH.Space.small)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.hover, in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .padding(.horizontal, UH.Space.regular)
    }

    private func message(title: String, body: String) -> some View {
        VStack(spacing: UH.Space.compact) {
            Text(title).font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
            Text(body).font(UH.TextStyle.body).foregroundStyle(UH.Palette.secondary).multilineTextAlignment(.center)
        }
        .padding(UH.Space.section)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
```

- [ ] **Step 5: Run tests and build**

Run: `ios-native/scripts/test.sh`
Expected: all pass (no new unit tests; this task is views).

- [ ] **Step 6: Screenshots**

Seed (`cd backend && DATABASE_URL=postgresql://uphill:uphill_secret@localhost:5433/uphill_ai python scripts/seed_ios_preview.py`), build/install/launch as in Phase 0 Task 8 Step 8, sign in as `ios-preview@uphill.ai` / `uphill-preview-1`. Capture into `ios-native/docs/screenshots/phase1/`:
- `plan-carousel-volume.png` (first card), then swipe and capture `plan-carousel-race.png`, `plan-carousel-week.png`, `plan-carousel-phase.png`.
- `plan-week-switch.png` after tapping the right chevron once.
- `plan-empty.png`: sign out, register a new account, open Plan.
- `plan-offline.png`: sign in as the preview athlete, stop the backend container, kill and relaunch the app (the banner shows and the plan still renders). Start the backend again.
- Turn on the largest Dynamic Type size (`xcrun simctl ui booted content_size extra-extra-extra-large`), capture `plan-large-text.png`, then reset with `xcrun simctl ui booted content_size large`. Cards may grow taller but text must not be clipped; if it is, change `.frame(height: 176)` to `.frame(minHeight: 176)`.

Look at every screenshot.

- [ ] **Step 7: Commit**

```bash
git add ios-native
git commit -m "feat(ios): Plan tab with summary carousel, week switcher and offline banner"
```

---

### Task 8: Day list: workout rows, rest rows, Today and Priority

**Files:**
- Create: `ios-native/UphillAI/Features/Plan/DayRow.swift`
- Modify: `ios-native/UphillAI/Features/Plan/PlanView.swift`

**Interfaces:**
- Consumes: `PlanDay`, `PlanViewModel` (Task 6).
- Produces: `struct DayRow: View` (`init(day: PlanDay, onSelect: (Workout) -> Void)`), which renders either the collapsed rest row or a workout day card; `PlanView` gains `@State private var selectedWorkout: Workout?` (Task 9's detail sheet reads it) and auto-scrolls to today.

Row rules:
- **Collapsed rest row**: one line, min height 44 pt: weekday + date ("Mon 5 Oct") left, "Rest" in muted text right, `moon.zzz` icon. Eyebrow (`TODAY`/`TOMORROW`) shown before the weekday when set. No tap action.
- **Workout day card** (`uhCard`, radius `workoutDay`): eyebrow line (`TODAY`/`TOMORROW` in `accentInk`, plus `PRIORITY` in `accentInk` when any workout on the day has `isPriority`), weekday + date, then one tappable row per workout: title (`label` font), "45 min · 7 km · Z2" in caption, and a trailing state icon (done `checkmark.circle.fill` accent ink, missed `xmark.circle` danger, else `chevron.right` muted). Priority days get a 1.5 pt `accentInk` stroke instead of the `line` stroke. Today's card gets `UH.Palette.activeFill` background.
- Each workout row is a `Button` (min height 44 pt) calling `onSelect`; VoiceOver label "Hill Repeats, 60 minutes, 8 kilometres, priority, done".
- `PlanView` wraps the list in a `ScrollViewReader`; on first load and when returning to the current week it scrolls the `TODAY` day into view (anchor `.top`), animated with `UH.Motion.standard` unless Reduce Motion is on.

- [ ] **Step 1: Implement** `DayRow.swift`

```swift
import SwiftUI

struct DayRow: View {
    let day: PlanDay
    let onSelect: (Workout) -> Void

    var body: some View {
        if day.isCollapsed {
            restRow
        } else {
            workoutCard
        }
    }

    private var dateText: String {
        guard let date = day.date else { return day.weekday.short }
        return date.formatted(.dateTime.weekday(.abbreviated).day().month(.abbreviated))
    }

    private var isPriority: Bool { day.workouts.contains(where: \.isPriority) }

    private var restRow: some View {
        HStack(spacing: UH.Space.compact) {
            if let eyebrow = day.eyebrow {
                Text(eyebrow).font(UH.TextStyle.eyebrow).foregroundStyle(UH.Palette.accentInk)
            }
            Text(dateText).font(UH.TextStyle.label).foregroundStyle(UH.Palette.secondary)
            Spacer()
            Label("Rest", systemImage: "moon.zzz")
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.muted)
        }
        .padding(.horizontal, UH.Space.regular)
        .frame(minHeight: 44)
        .accessibilityElement(children: .combine)
    }

    private var workoutCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            HStack(spacing: UH.Space.compact) {
                if let eyebrow = day.eyebrow {
                    Text(eyebrow).font(UH.TextStyle.eyebrow).tracking(0.6).foregroundStyle(UH.Palette.accentInk)
                }
                if isPriority {
                    Text("PRIORITY").font(UH.TextStyle.eyebrow).tracking(0.6).foregroundStyle(UH.Palette.accentInk)
                }
                Text(dateText).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
            }
            ForEach(day.workouts) { workout in
                Button { onSelect(workout) } label: { workoutRow(workout) }
                    .buttonStyle(.plain)
            }
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(day.eyebrow == "TODAY" ? UH.Palette.activeFill : UH.Palette.card,
                    in: RoundedRectangle(cornerRadius: UH.Radius.workoutDay))
        .overlay(
            RoundedRectangle(cornerRadius: UH.Radius.workoutDay)
                .stroke(isPriority ? UH.Palette.accentInk : UH.Palette.line, lineWidth: isPriority ? 1.5 : 1)
        )
    }

    private func workoutRow(_ workout: Workout) -> some View {
        HStack(spacing: UH.Space.small) {
            VStack(alignment: .leading, spacing: 2) {
                Text(workout.title).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                Text(details(workout)).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
            }
            Spacer()
            stateIcon(workout)
        }
        .frame(minHeight: 44)
        .contentShape(Rectangle())
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(accessibility(workout))
        .accessibilityAddTraits(.isButton)
    }

    private func details(_ w: Workout) -> String {
        var parts = ["\(Int(w.durationMinutes)) min"]
        if let km = w.distanceKm, km > 0 { parts.append(km.formatted(.number.precision(.fractionLength(0...1))) + " km") }
        if !w.targetZone.isEmpty, w.targetZone != "Rest" { parts.append(w.targetZone) }
        return parts.joined(separator: " · ")
    }

    @ViewBuilder
    private func stateIcon(_ w: Workout) -> some View {
        if w.isDone {
            Image(systemName: "checkmark.circle.fill").foregroundStyle(UH.Palette.accentInk)
        } else if w.isMissedFlag {
            Image(systemName: "xmark.circle").foregroundStyle(UH.Palette.danger)
        } else {
            Image(systemName: "chevron.right").foregroundStyle(UH.Palette.muted).font(.footnote.weight(.semibold))
        }
    }

    private func accessibility(_ w: Workout) -> String {
        var parts = [w.title, "\(Int(w.durationMinutes)) minutes"]
        if let km = w.distanceKm, km > 0 { parts.append(km.formatted(.number.precision(.fractionLength(0...1))) + " kilometres") }
        if w.isPriority { parts.append("priority") }
        if w.isDone { parts.append("done") } else if w.isMissedFlag { parts.append("missed") }
        return parts.joined(separator: ", ")
    }
}
```

- [ ] **Step 2: Add the list and auto-scroll to** `PlanView.swift`

Add state and environment:

```swift
    @State private var selectedWorkout: Workout?
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
```

Replace the `.loaded` case with:

```swift
        case .loaded:
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(alignment: .leading, spacing: UH.Space.regular) {
                        if let cachedAt = model.cachedAt { offlineBanner(cachedAt) }
                        SummaryCarousel(model: model)
                        WeekSwitcher(weeks: model.weeks, selected: $model.selectedWeek, currentWeek: model.currentWeek)
                            .padding(.horizontal, UH.Space.regular)
                        LazyVStack(spacing: UH.Space.compact) {
                            ForEach(model.days) { day in
                                DayRow(day: day) { selectedWorkout = $0 }
                                    .id(day.id)
                            }
                        }
                        .padding(.horizontal, UH.Space.regular)
                    }
                    .padding(.vertical, UH.Space.regular)
                }
                .refreshable { await model.load() }
                .onAppear { scrollToToday(proxy) }
                .onChange(of: model.selectedWeek) { _, week in
                    if week == model.currentWeek { scrollToToday(proxy) }
                }
            }
```

Add the helper:

```swift
    private func scrollToToday(_ proxy: ScrollViewProxy) {
        guard let today = model.days.first(where: { $0.eyebrow == "TODAY" }) else { return }
        if reduceMotion {
            proxy.scrollTo(today.id, anchor: .top)
        } else {
            withAnimation(UH.Motion.standard) { proxy.scrollTo(today.id, anchor: .top) }
        }
    }
```

- [ ] **Step 3: Run tests and build**

Run: `ios-native/scripts/test.sh`
Expected: all pass.

- [ ] **Step 4: Screenshots**

Re-seed, launch, sign in as the preview athlete. Capture into `ios-native/docs/screenshots/phase1/`:
- `plan-today.png`: opens scrolled to today's card with `TODAY` and the active fill.
- `plan-week-list.png`: scroll to show a collapsed rest row (Monday/Thursday) next to workout cards.
- `plan-priority.png`: Tuesday or Saturday card with `PRIORITY` and the darker outline.
- `plan-week1.png`: week 1 with done ticks and Friday's missed mark.

Check with the Accessibility Inspector or VoiceOver that a workout row reads as one element with the label described above, and that rest rows are at least 44 pt tall.

- [ ] **Step 5: Commit**

```bash
git add ios-native
git commit -m "feat(ios): day list with collapsed rest days, Today and Priority markers"
```

---

### Task 9: Workout detail sheet and Manage sheet

**Files:**
- Create: `ios-native/UphillAI/Features/Plan/WorkoutDetailSheet.swift`, `ios-native/UphillAI/Features/Plan/ManagePlanSheet.swift`
- Modify: `ios-native/UphillAI/Features/Plan/PlanView.swift`

**Interfaces:**
- Consumes: `PlanViewModel` writes and `moveTargets` (Task 6); `selectedWorkout` (Task 8).
- Produces: `struct WorkoutDetailSheet` (`init(model: PlanViewModel, workoutID: Int)`), `struct ManagePlanSheet` (`init(model: PlanViewModel)`).

Workout detail (`.sheet(item:)`, detents `.medium` and `.large`, drag indicator visible). It reads the workout from `model.snapshot` by id so it updates after each write.
- Header: eyebrow (`PRIORITY` when set), title (`sectionTitle`), "Tue 6 Oct · Base".
- Facts grid (two columns, only fields that are present): Duration, Distance, Elevation gain, Zone, Heart rate, Pace, Intervals ("6 × 400 m, walk 200 m" from `interval_reps`/`interval_rep_value`/`interval_rep_unit`/`walk_interval_value`), Treadmill ("8.1–9.2 km/h · 2–4 %").
- Description and fueling tip as body text.
- Primary action: "Mark as done" (`.uhPrimary`) or, when done, "Undo done" (`.uhSecondary`). Secondary: "Mark as missed" when neither done nor missed. Success haptic: `.sensoryFeedback(.success, trigger: model.lastCompletedID)`.
- Log section: RPE stepper 1–10 labelled "Effort (RPE)" with "Not set" until changed, notes `TextField` (axis vertical, 3–6 lines), "Save" button enabled when RPE or notes changed. Shows "Saved" for 2 s after success.
- Move: `Menu("Move to…")` listing `model.moveTargets(for:)` as "Thu 8 Oct" (prefix "Next week · " for the following week). Rest workouts cannot be moved (hide the menu).
- Errors: `model.actionError` shown in `danger` caption above the actions; `.sensoryFeedback(.error, trigger: model.actionError)`. Clear it when the sheet closes.
- Workouts that are not yet approved by a coach (`approved_at == nil`) show "Waiting for your coach's approval" and hide every write action.

Manage sheet (toolbar "Manage" button, detent `.medium`): title "Manage plan", section "Recent plans" listing `model.recentPlans()` (loaded on appear; the active plan has a checkmark and is disabled), tap selects that plan and closes the sheet. A footer note: "Plan settings, new plans, watch sync and calendar export are on the web for now."

- [ ] **Step 1: Implement** `WorkoutDetailSheet.swift`

```swift
import SwiftUI

struct WorkoutDetailSheet: View {
    let model: PlanViewModel
    let workoutID: Int
    @Environment(\.dismiss) private var dismiss
    @State private var rpe: Int?
    @State private var notes = ""
    @State private var didLoadLog = false
    @State private var showSaved = false
    @State private var isBusy = false

    private var workout: Workout? { model.snapshot?.workouts.first { $0.id == workoutID } }

    var body: some View {
        NavigationStack {
            if let workout {
                ScrollView {
                    VStack(alignment: .leading, spacing: UH.Space.section) {
                        header(workout)
                        facts(workout)
                        if let text = workout.description, !text.isEmpty { prose("About", text) }
                        if let tip = workout.fuelingTip, !tip.isEmpty { prose("Fueling", tip) }
                        if let error = model.actionError {
                            Text(error).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger)
                        }
                        if workout.approvedAt == nil {
                            Label("Waiting for your coach's approval", systemImage: "hourglass")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                        } else {
                            actions(workout)
                            if !workout.isRest { logSection(workout) }
                        }
                    }
                    .padding(UH.Space.medium)
                }
                .background(UH.Palette.surface.ignoresSafeArea())
                .toolbar { Button("Done") { dismiss() } }
                .onAppear { loadLog(workout) }
            }
        }
        .presentationDetents([.medium, .large])
        .presentationDragIndicator(.visible)
        .sensoryFeedback(.success, trigger: model.lastCompletedID)
        .sensoryFeedback(.error, trigger: model.actionError) { _, new in new != nil }
        .onDisappear { model.clearActionError() }
    }

    private func header(_ w: Workout) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            if w.isPriority {
                Text("PRIORITY").font(UH.TextStyle.eyebrow).tracking(0.6).foregroundStyle(UH.Palette.accentInk)
            }
            Text(w.title).font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
            Text(subtitle(w)).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
        }
    }

    private func subtitle(_ w: Workout) -> String {
        guard let plan = model.snapshot?.plan,
              let date = PlanCalendar.date(week: w.weekNumber, weekday: w.weekday, plan: plan,
                                           workouts: model.snapshot?.workouts ?? []) else { return w.phase }
        return date.formatted(.dateTime.weekday(.abbreviated).day().month(.abbreviated)) + " · " + w.phase
    }

    private struct Fact: Identifiable {
        let label: String
        let value: String
        var id: String { label }
    }

    private func facts(_ w: Workout) -> some View {
        let candidates: [(String, String?)] = [
            ("Duration", "\(Int(w.durationMinutes)) min"),
            ("Distance", w.distanceKm.flatMap { $0 > 0 ? $0.formatted(.number.precision(.fractionLength(0...1))) + " km" : nil }),
            ("Elevation gain", w.elevationGainM.flatMap { $0 > 0 ? "\(Int($0)) m" : nil }),
            ("Zone", w.targetZone == "Rest" ? nil : w.targetZone),
            ("Heart rate", w.targetHrRange),
            ("Pace", w.targetPace),
            ("Intervals", intervals(w)),
            ("Treadmill", treadmill(w)),
        ]
        let facts = candidates.compactMap { label, value in value.map { Fact(label: label, value: $0) } }
        return LazyVGrid(columns: [GridItem(.flexible(), alignment: .leading), GridItem(.flexible(), alignment: .leading)],
                         alignment: .leading, spacing: UH.Space.small) {
            ForEach(facts) { fact in
                VStack(alignment: .leading, spacing: 2) {
                    Text(fact.label.uppercased()).font(UH.TextStyle.eyebrow).foregroundStyle(UH.Palette.muted)
                    Text(fact.value).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                }
                .accessibilityElement(children: .combine)
            }
        }
        .uhCard()
    }

    private func intervals(_ w: Workout) -> String? {
        guard let reps = w.intervalReps, let value = w.intervalRepValue, let unit = w.intervalRepUnit else { return nil }
        var text = "\(reps) × \(value.formatted(.number.precision(.fractionLength(0...1)))) \(unit)"
        if let walk = w.walkIntervalValue, walk > 0 {
            text += ", walk \(walk.formatted(.number.precision(.fractionLength(0...1)))) \(unit)"
        }
        return text
    }

    private func treadmill(_ w: Workout) -> String? {
        guard let speed = w.treadmillSpeed, speed != "0", !speed.isEmpty else { return nil }
        let incline = w.treadmillIncline.flatMap { $0 == "0" || $0.isEmpty ? nil : $0 }
        let speedText = speed.replacingOccurrences(of: "-", with: "–") + " km/h"
        guard let incline else { return speedText }
        return speedText + " · " + incline.replacingOccurrences(of: "-", with: "–") + " %"
    }

    private func prose(_ title: String, _ text: String) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text(title.uppercased()).font(UH.TextStyle.eyebrow).foregroundStyle(UH.Palette.muted)
            Text(text).font(UH.TextStyle.body).foregroundStyle(UH.Palette.ink)
        }
    }

    @ViewBuilder
    private func actions(_ w: Workout) -> some View {
        VStack(spacing: UH.Space.small) {
            if w.isDone {
                Button("Undo done") { run { await model.setDone(w, false) } }.buttonStyle(.uhSecondary)
            } else if !w.isRest {
                Button("Mark as done") { run { await model.setDone(w, true) } }.buttonStyle(.uhPrimary)
                if !w.isMissedFlag {
                    Button("Mark as missed") { run { await model.setMissed(w) } }.buttonStyle(.uhSecondary)
                } else {
                    Text("Marked as missed").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger)
                }
            }
            if !w.isRest {
                let targets = model.moveTargets(for: w)
                if !targets.isEmpty {
                    Menu {
                        ForEach(targets) { target in
                            Button(moveLabel(target)) { run { if await model.move(w, to: target) { dismiss() } } }
                        }
                    } label: {
                        Label("Move to…", systemImage: "calendar")
                            .frame(maxWidth: .infinity, minHeight: 44)
                    }
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.accentInk)
                }
            }
        }
        .disabled(isBusy)
    }

    private func moveLabel(_ target: MoveTarget) -> String {
        let day = target.date.formatted(.dateTime.weekday(.abbreviated).day().month(.abbreviated))
        return target.week > model.currentWeek ? "Next week · \(day)" : day
    }

    private func logSection(_ w: Workout) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Text("YOUR LOG").font(UH.TextStyle.eyebrow).foregroundStyle(UH.Palette.muted)
            Stepper(value: Binding(get: { rpe ?? 5 }, set: { rpe = $0 }), in: 1...10) {
                LabeledContent("Effort (RPE)", value: rpe.map(String.init) ?? "Not set")
            }
            TextField("Notes", text: $notes, axis: .vertical)
                .lineLimit(3...6)
                .padding(UH.Space.small)
                .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
            Button(showSaved ? "Saved" : "Save") {
                run {
                    if await model.saveLog(w, rpe: rpe, notes: notes) {
                        showSaved = true
                        try? await Task.sleep(for: .seconds(2))
                        showSaved = false
                    }
                }
            }
            .buttonStyle(.uhSecondary)
            .disabled(rpe == w.rpe && notes == (w.notes ?? ""))
        }
        .uhCard()
    }

    private func loadLog(_ w: Workout) {
        guard !didLoadLog else { return }
        rpe = w.rpe
        notes = w.notes ?? ""
        didLoadLog = true
    }

    private func run(_ action: @escaping @MainActor () async -> Void) {
        Task {
            isBusy = true
            await action()
            isBusy = false
        }
    }
}
```

- [ ] **Step 2: Implement** `ManagePlanSheet.swift`

```swift
import SwiftUI

struct ManagePlanSheet: View {
    let model: PlanViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var plans: [Plan]?

    var body: some View {
        NavigationStack {
            List {
                Section("Recent plans") {
                    if let plans {
                        if plans.isEmpty {
                            Text("No other plans yet.").foregroundStyle(UH.Palette.secondary)
                        }
                        ForEach(plans) { plan in
                            let isActive = plan.id == model.snapshot?.plan.id
                            Button {
                                Task {
                                    await model.select(plan)
                                    if model.actionError == nil { dismiss() }
                                }
                            } label: {
                                HStack {
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(plan.raceName).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                                        Text(raceDate(plan)).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                                    }
                                    Spacer()
                                    if isActive {
                                        Image(systemName: "checkmark").foregroundStyle(UH.Palette.accentInk)
                                    }
                                }
                                .frame(minHeight: 44)
                            }
                            .disabled(isActive)
                            .accessibilityAddTraits(isActive ? .isSelected : [])
                        }
                    } else {
                        ProgressView()
                    }
                }
                if let error = model.actionError {
                    Text(error).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger)
                }
                Section {
                    Text("Plan settings, new plans, watch sync and calendar export are on the web for now.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.muted)
                }
            }
            .navigationTitle("Manage plan")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { Button("Done") { dismiss() } }
            .task { plans = await model.recentPlans() }
        }
        .presentationDetents([.medium, .large])
        .onDisappear { model.clearActionError() }
    }

    private func raceDate(_ plan: Plan) -> String {
        guard let day = PlanCalendar.day(from: plan.raceDate) else { return plan.raceDate }
        return "Race " + day.formatted(.dateTime.day().month(.abbreviated).year())
    }
}
```

- [ ] **Step 3: Wire both sheets into** `PlanView.swift`

Add `@State private var showManage = false`. Replace the disabled toolbar button with:

```swift
                        Button("Manage") { showManage = true }
                            .disabled(model.snapshot == nil)
```

Add to the `NavigationStack` content:

```swift
                .sheet(item: $selectedWorkout) { workout in
                    WorkoutDetailSheet(model: model, workoutID: workout.id)
                }
                .sheet(isPresented: $showManage) { ManagePlanSheet(model: model) }
```

- [ ] **Step 4: Run tests and build**

Run: `ios-native/scripts/test.sh`
Expected: all pass.

- [ ] **Step 5: Screenshots and manual checks**

Re-seed, launch, sign in as the preview athlete. Capture into `ios-native/docs/screenshots/phase1/`:
- `detail-today.png`: tap today's workout (medium detent).
- `detail-large.png`: drag to the large detent, showing facts, description, actions and log.
- `detail-done.png`: tap "Mark as done"; the button becomes "Undo done", and the day row shows the tick after closing.
- `detail-move-menu.png`: open "Move to…".
- After moving a workout to tomorrow, capture `plan-after-move.png` showing it on the new day.
- `detail-offline-error.png`: stop the backend, kill and relaunch (cached plan), open a workout, tap "Mark as done": the offline message shows and nothing changes. Restart the backend.
- `manage-sheet.png`: tap Manage; tap "Sky Race 25K"; the Plan tab switches to it (capture `plan-switched.png`); switch back.

- [ ] **Step 6: Commit**

```bash
git add ios-native
git commit -m "feat(ios): workout detail with logging and moves, Manage sheet with recent plans"
```

---

### Task 10: End-to-end UI test against the local backend

**Files:**
- Modify: `ios-native/project.yml` (UI test target and E2E scheme), `ios-native/UphillAI/Features/Auth/SignInView.swift`, `ios-native/UphillAI/Features/Plan/DayRow.swift`, `ios-native/UphillAI/Features/Plan/WorkoutDetailSheet.swift` (accessibility identifiers only)
- Create: `ios-native/UphillAIUITests/PlanFlowUITests.swift`, `ios-native/scripts/e2e.sh`
- Modify: `ios-native/README.md` (E2E section)

**Interfaces:**
- Consumes: the preview athlete from Task 1; every screen above.
- Produces: scheme `UphillAI-E2E` (not run by `test.sh` or CI) and `ios-native/scripts/e2e.sh`.

- [ ] **Step 1: Add the target and scheme to** `project.yml`

Under `targets:`:

```yaml
  UphillAIUITests:
    type: bundle.ui-testing
    platform: iOS
    sources:
      - path: UphillAIUITests
    dependencies:
      - target: UphillAI
    settings:
      base:
        PRODUCT_BUNDLE_IDENTIFIER: ai.uphill.app.uitests
        GENERATE_INFOPLIST_FILE: YES
        TEST_TARGET_NAME: UphillAI
```

Under `schemes:`:

```yaml
  UphillAI-E2E:
    build:
      targets:
        UphillAI: all
        UphillAIUITests: [test]
    test:
      targets:
        - UphillAIUITests
```

- [ ] **Step 2: Add accessibility identifiers**

- `SignInView`: email field `.accessibilityIdentifier("signin.email")`, password `signin.password`, submit button `signin.submit`.
- `DayRow`: on both the workout card and the rest row add `.accessibilityElement(children: .contain)` and `.accessibilityIdentifier(day.eyebrow == "TODAY" ? "day.today" : "day.\(day.weekday.rawValue)")` (the rest row keeps its combined label: apply `.contain` only to the workout card). Each workout row button gets `.accessibilityIdentifier("workout.\(workout.id)")`.
- `WorkoutDetailSheet`: "Mark as done" `detail.markDone`, "Undo done" `detail.undoDone`.

- [ ] **Step 3: Write** `UphillAIUITests/PlanFlowUITests.swift`

```swift
import XCTest

/// Runs against the LOCAL backend with the preview athlete seeded by
/// backend/scripts/seed_ios_preview.py. Use ios-native/scripts/e2e.sh.
final class PlanFlowUITests: XCTestCase {
    override func setUp() {
        continueAfterFailure = false
    }

    @MainActor
    func testSignInSeeTodayMarkDoneAndUndo() {
        let app = XCUIApplication()
        // `-KEY value` launch arguments land in UserDefaults' argument domain.
        app.launchArguments = ["-UPHILL_ENVIRONMENT", "local"]
        app.launch()

        let email = app.textFields["signin.email"]
        XCTAssertTrue(email.waitForExistence(timeout: 10))
        email.tap()
        email.typeText("ios-preview@uphill.ai")
        let password = app.secureTextFields["signin.password"]
        password.tap()
        password.typeText("uphill-preview-1")
        app.buttons["signin.submit"].tap()

        let today = app.descendants(matching: .any)["day.today"]
        XCTAssertTrue(today.waitForExistence(timeout: 15), "Plan should open scrolled to today")

        let firstWorkout = today.buttons.matching(NSPredicate(format: "identifier BEGINSWITH 'workout.'")).firstMatch
        guard firstWorkout.exists else {
            // Today is a rest day in the seeded week (Monday/Thursday): nothing to mark.
            return
        }
        firstWorkout.tap()

        let markDone = app.buttons["detail.markDone"]
        let undoDone = app.buttons["detail.undoDone"]
        if undoDone.waitForExistence(timeout: 3) {
            undoDone.tap()   // seeded as done already: reset first
        }
        XCTAssertTrue(markDone.waitForExistence(timeout: 5))
        markDone.tap()
        XCTAssertTrue(undoDone.waitForExistence(timeout: 10))
        undoDone.tap()
        XCTAssertTrue(markDone.waitForExistence(timeout: 10))
    }
}
```

Note: the seeded week has rest on Monday and Thursday. On those days `day.today` is the collapsed rest row, which has no workout buttons, so the `guard` ends the test after confirming the plan opened on today.

- [ ] **Step 4: Write** `ios-native/scripts/e2e.sh`

```bash
#!/usr/bin/env bash
# Seeds the local preview athlete and runs the UI tests against the LOCAL backend.
# Requires the Docker stack (API on :8000, Postgres on :5433).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
curl -sf http://localhost:8000/api/health >/dev/null || { echo "Local backend is not running on :8000" >&2; exit 1; }
(cd "$ROOT/backend" && DATABASE_URL=postgresql://uphill:uphill_secret@localhost:5433/uphill_ai python scripts/seed_ios_preview.py)
cd "$ROOT/ios-native"
xcodegen generate --quiet
DESTINATION="${DESTINATION:-platform=iOS Simulator,name=iPhone 17 Pro}"
xcodebuild test -project UphillAI.xcodeproj -scheme UphillAI-E2E -destination "$DESTINATION" -quiet
```

Run: `chmod +x ios-native/scripts/e2e.sh && ios-native/scripts/e2e.sh`
Expected: `** TEST SUCCEEDED **`.

- [ ] **Step 5: Document it** in `ios-native/README.md`, after the Test section:

````markdown
## End-to-end (local backend)

```bash
ios-native/scripts/e2e.sh
```

Seeds `ios-preview@uphill.ai` (password `uphill-preview-1`, local only) with plans around today, then runs
`UphillAIUITests`. Not part of CI: it needs the local Docker stack.
````

- [ ] **Step 6: Run everything**

Run: `ios-native/scripts/test.sh && ios-native/scripts/e2e.sh`
Expected: both succeed.

- [ ] **Step 7: Commit**

```bash
git add ios-native
git commit -m "test(ios): end-to-end plan flow against the local backend"
```

---

## Phase 1 done when

- `ios-native/scripts/test.sh` and `ios-native/scripts/e2e.sh` pass.
- `ios-native/docs/screenshots/phase1/` holds every screenshot named in Tasks 7–9.
- A TestFlight build (`ios-native/scripts/release.sh`) is uploaded by your human partner for stakeholders to try.
