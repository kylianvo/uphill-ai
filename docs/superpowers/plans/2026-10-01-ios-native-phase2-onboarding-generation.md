# iOS Native Phase 2: Onboarding and Plan Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A new athlete can go from sign-up to a generated plan entirely in the app, and an existing athlete can start a new plan, build the next week, adapt a week, read a weekly review and check their Goal, all natively.

**Architecture:** Every AI action on the backend is an async job: the app starts it (`job_id`), then polls `GET /api/coach/plan-status/{job_id}`. One `GenerationCenter` in `AppModel` owns the running job so leaving a screen never loses it, persists the job id across relaunches, and hands the finished plan to `PlanViewModel`. Onboarding and "new plan" share one form model (`PlanSetupDraft`) and one step flow. Next week, adapt week, weekly review and goal are sheets off the Plan tab.

**Tech Stack:** Swift 6, SwiftUI, Swift Testing, XCUITest. No new packages.

**Spec:** `docs/superpowers/specs/2026-10-01-ios-native-app-design.md`. **Depends on:** Phase 1 (`docs/superpowers/plans/2026-10-01-ios-native-phase1-plan-core.md`) merged.

**Design sources:** `.claude/skills/apple-design/SKILL.md` (motion, feedback, spatial consistency) and Impeccable's `onboard`, `harden` and `clarify` references (github.com/pbakaus/impeccable, `skill/reference/`). Impeccable's detector and live mode target web DOM, so this plan carries its rules as constraints below instead of running its tooling.

## Global Constraints

- Everything in the Phase 0 and Phase 1 Global Constraints still applies.
- **Phase 0 and Phase 1 code on `main` is the source of truth.** If a snippet here names something differently from the merged code (a property, an initializer label), adapt the snippet to the code and say so in the task report. Do not rename merged code to match this plan.
- Screenshots go in `ios-native/docs/screenshots/phase2/`.
- Copy is English. Use the exact strings written in this plan.

Onboarding (Impeccable `onboard`):
- Get to first value fast: at most 4 question steps before the plan starts generating. Optional profile questions sit in one skippable step.
- The welcome screen states the outcome and an honest time estimate ("About 2 minutes") and offers **Not now**, which drops the athlete into the app (Plan tab empty state). Onboarding never blocks the app.
- Every field has a visible label and a sensible default; the athlete only types what has no good default.
- The empty Plan tab explains what will appear there, why it matters and has one primary action ("Build my plan").

Robustness (Impeccable `harden`):
- Errors say what failed and how to recover, and keep the athlete's answers. Submit buttons disable while a request runs (no double submission).
- Long operations name the actual operation and give an honest estimate. No fake progress percentages or invented stages.
- Every text container grows with Dynamic Type up to the largest accessibility size; test at `extra-extra-extra-large`.
- Handle 400, 401, 403, 404, 429 and 5xx distinctly where the server sends them (mapping in the tasks).

Copy (Impeccable `clarify`):
- Buttons are verb + object ("Build my plan", "Build week 5", "Adapt this week"). No "Submit", "OK" or "Continue" on final actions.
- Validation appears next to the field, only after the athlete tries to continue, and says what to change without blame.
- Same word for the same thing everywhere: "plan", "week", "goal", "target time".

Motion and feedback (apple-design):
- Step transitions move in the direction of travel: forward slides in from the trailing edge, back from the leading edge; the same path in both directions. Reduce Motion: cross-fade.
- Default `UH.Motion.standard`; no bounce on screens that did not follow a flick.
- Haptics only on causal events: `.success` when a plan or week finishes generating, `.error` when a job fails, `.selection` on step change and option chips.
- The generation screen can be left at any time; the job keeps running.

## Backend contract (all exist today)

| Call | Body | Response |
|---|---|---|
| `POST /api/auth/onboarding` | `OnboardingRequest` (fields in Task 2) | `{job_id, plan: {...}}`; with `skip_plan: true` → `{user}` and no job |
| `POST /api/coach/generate-plan` | `PlanGenerateRequest` (Task 2) | `{job_id, active, plan: {...}}` |
| `GET /api/coach/block-completion/{plan_id}` | – | `{plan_id, blocks: [{block_number, week_start, week_end, completion_pct, unlocked, …}], max_generated_week}` |
| `POST /api/coach/generate-next-block` | `{plan_id, block_number, overall_rpe?, notes?, override_gate, lang}` | `{job_id, plan_id, block_number, week_start, week_end}`; 403 string detail when the previous block is under 70 % and `override_gate` is false; 400 when every block exists |
| `POST /api/coach/adapt-week` | `{plan_id, week_number, overall_rpe?, fatigue_level?, fatigue_notes?, lang, client_today}` | `{job_id, plan_id, week_number}`; 400 for a week not generated yet |
| `GET /api/coach/plan-status/{job_id}` | – | `{status: "generating"\|"done"\|"error", plan_id, plan?, workouts?, error?}`; 404 when the server restarted (jobs live in memory) |
| `GET /api/coach/week-review/{plan_id}/{week}` | – | `{week_number, completion_pct, checkbox_completion_pct, per_workout: [...], narrative: {summary, highlights, watch}, …}` |
| `GET /api/plans/{plan_id}/goal` | – | `{assessment?, status: {state, suggested_mins}, target_time_hours}` |
| `POST /api/plans/{plan_id}/goal/reassess` | `{exclude: [], lang}` | same shape as GET; 429 when over the daily limit |
| `POST /api/plans/{plan_id}/goal/apply` | `{target_mins}` | same shape as GET |

`WEEKS_PER_BLOCK` is 1 on the backend today, so a "block" is one week. Never hard-code that: always read `week_start`/`week_end` from the responses.

## File Structure

```
ios-native/
  scripts/record_fixtures.sh                     + generation, review and goal fixtures
  UphillAI/
    Core/Generation/GenerationModels.swift       JobStart, JobStatus, JobOutcome, JobKind
    Core/Generation/GenerationService.swift      GenerationServicing + GenerationService
    Core/Generation/JobPoller.swift              polling loop with timeout and restart handling
    Core/Generation/GenerationCenter.swift       app-wide owner of the running job
    Core/Plan/PlanSetupDraft.swift               shared onboarding / new-plan form model + request bodies
    Core/Plan/ReviewModels.swift                 BlockCompletion, WeekReview, PlanGoal DTOs
    Core/Plan/PlanService.swift                  + blockCompletion, weekReview, goal calls
    App/AppModel.swift                           + generation center, onboarding routing
    App/RootView.swift                           + onboarding cover
    Features/Onboarding/PlanSetupViewModel.swift
    Features/Onboarding/PlanSetupFlow.swift      container: progress, back, transitions, primary button
    Features/Onboarding/WelcomeView.swift
    Features/Onboarding/SetupSteps.swift         goal, details, schedule, about-you, review step views
    Features/Onboarding/GenerationProgressView.swift
    Features/Plan/PlanViewModel.swift            + adopt(_:), nextWeekOffer
    Features/Plan/PlanView.swift                 + empty state CTA, next-week card, sheets
    Features/Plan/NextWeekSheet.swift
    Features/Plan/AdaptWeekSheet.swift
    Features/Plan/WeekReviewSheet.swift
    Features/Plan/GoalSheet.swift
    Features/Plan/SummaryCarousel.swift          + goal pill on the Race card, Review/Adapt actions on This week
    Features/Plan/ManagePlanSheet.swift          + Start new plan
  UphillAITests/
    Support/FakeGenerationService.swift
    Generation/JobPollerTests.swift
    Generation/GenerationCenterTests.swift
    Plan/PlanSetupDraftTests.swift
    Plan/PlanSetupViewModelTests.swift
    Plan/ReviewModelsTests.swift
  UphillAIUITests/OnboardingFlowUITests.swift
```

---

### Task 1: Job models, generation service and poller

**Files:**
- Create: `ios-native/UphillAI/Core/Generation/GenerationModels.swift`, `GenerationService.swift`, `JobPoller.swift`, `ios-native/UphillAITests/Support/FakeGenerationService.swift`
- Test: `ios-native/UphillAITests/Generation/JobPollerTests.swift`

**Interfaces:**
- Consumes: `APIClient`, `Endpoint`, `APIError`, `Plan`, `Workout`, `PlanSnapshot`, `User`, `makeStubClient`, `json` (Phases 0–1).
- Produces:
  - `enum JobKind: String, Codable, Sendable { case newPlan, nextWeek, adaptWeek }`
  - `struct JobStart: Decodable, Sendable { let jobId: String }`
  - `struct OnboardingResult: Decodable, Sendable { let jobId: String?; let user: User? }`
  - `struct JobStatus: Decodable, Sendable { let status: String; let planId: Int?; let plan: Plan?; let workouts: [Workout]?; let error: String?; var snapshot: PlanSnapshot? }`
  - `enum JobOutcome: Equatable, Sendable { case done(PlanSnapshot?), failed(String), lost, cancelled }`
  - `protocol GenerationServicing: Sendable` with `completeOnboarding(_ body: OnboardingBody) async throws -> OnboardingResult`, `generatePlan(_ body: PlanBody) async throws -> JobStart`, `generateNextBlock(_ body: NextBlockBody) async throws -> JobStart`, `adaptWeek(_ body: AdaptWeekBody) async throws -> JobStart`, `status(jobID: String) async throws -> JobStatus`
  - `struct GenerationService: GenerationServicing { let client: APIClient }`
  - `struct NextBlockBody: Encodable, Sendable { planId, blockNumber, overallRpe: Int?, notes: String?, overrideGate: Bool, lang: String }`, `struct AdaptWeekBody: Encodable, Sendable { planId, weekNumber, overallRpe: Int?, fatigueLevel: String?, fatigueNotes: String?, lang: String, clientToday: String }` (`OnboardingBody` and `PlanBody` come in Task 2; declare them as empty `Encodable, Sendable` structs in `PlanSetupDraft.swift` now so this task compiles, and Task 2 fills them)
  - `struct JobPoller: Sendable` with `init(service:interval:timeout:sleep:)` and `func wait(jobID: String) async -> JobOutcome`
  - `static let JobPoller.slowMessage`, `JobPoller.offlineMessage`
  - Test double `final class FakeGenerationService: GenerationServicing`

Poller rules:
1. Poll every `interval` (default 2 s) until `timeout` (default 240 s).
2. `"done"` → `.done(status.snapshot)`; `"error"` → `.failed(error ?? "We couldn't build this plan. Please try again.")`.
3. `APIError.http(404, …)` → `.lost` (the server restarted; the caller reloads the plan instead).
4. Transport errors are retried; 5 in a row → `.failed(offlineMessage)`.
5. Any other error → `.failed(error.userMessage)`.
6. Timeout → `.failed(slowMessage)`.
7. Task cancellation → `.cancelled`.

- [ ] **Step 1: Write the test double** `UphillAITests/Support/FakeGenerationService.swift`

```swift
import Foundation
import Synchronization
@testable import UphillAI

/// Scriptable GenerationServicing. `statuses` is consumed in order, one per poll;
/// the last element repeats once the script runs out.
final class FakeGenerationService: GenerationServicing {
    let startResult = Mutex<Result<JobStart, APIError>>(.success(JobStart(jobId: "job-1")))
    let onboardingResult = Mutex<Result<OnboardingResult, APIError>>(.success(OnboardingResult(jobId: "job-1", user: nil)))
    let statuses = Mutex<[Result<JobStatus, APIError>]>([])
    let calls = Mutex<[String]>([])

    private func record(_ call: String) { calls.withLock { $0.append(call) } }

    func completeOnboarding(_ body: OnboardingBody) async throws -> OnboardingResult {
        record("onboarding skip=\(body.skipPlan)")
        return try onboardingResult.withLock { $0 }.get()
    }

    func generatePlan(_ body: PlanBody) async throws -> JobStart {
        record("generate \(body.goalType)")
        return try startResult.withLock { $0 }.get()
    }

    func generateNextBlock(_ body: NextBlockBody) async throws -> JobStart {
        record("next \(body.blockNumber) override=\(body.overrideGate)")
        return try startResult.withLock { $0 }.get()
    }

    func adaptWeek(_ body: AdaptWeekBody) async throws -> JobStart {
        record("adapt \(body.weekNumber) \(body.fatigueLevel ?? "-")")
        return try startResult.withLock { $0 }.get()
    }

    func status(jobID: String) async throws -> JobStatus {
        record("status \(jobID)")
        let next: Result<JobStatus, APIError> = statuses.withLock { list in
            if list.count > 1 { return list.removeFirst() }
            return list.first ?? .failure(.http(status: 404, message: "Job not found.", code: nil))
        }
        return try next.get()
    }
}

extension JobStatus {
    static func generating() -> JobStatus {
        try! JSONCoding.decoder.decode(JobStatus.self, from: json(["status": "generating", "plan_id": 7]))
    }

    static func done(_ snapshot: PlanSnapshot?) -> JobStatus {
        var object: [String: Any] = ["status": "done", "plan_id": snapshot?.plan.id ?? 7]
        if let snapshot {
            object["plan"] = try! JSONSerialization.jsonObject(with: JSONCoding.encoder.encode(snapshot.plan))
            object["workouts"] = try! JSONSerialization.jsonObject(with: JSONCoding.encoder.encode(snapshot.workouts))
        }
        return try! JSONCoding.decoder.decode(JobStatus.self, from: json(object))
    }

    static func error(_ message: String?) -> JobStatus {
        var object: [String: Any] = ["status": "error", "plan_id": 7]
        if let message { object["error"] = message }
        return try! JSONCoding.decoder.decode(JobStatus.self, from: json(object))
    }
}
```

- [ ] **Step 2: Write the failing tests** `UphillAITests/Generation/JobPollerTests.swift`

```swift
import Foundation
import Synchronization
import Testing
@testable import UphillAI

struct JobPollerTests {
    private func poller(_ service: FakeGenerationService, timeout: Duration = .seconds(10)) -> JobPoller {
        JobPoller(service: service, interval: .seconds(2), timeout: timeout, sleep: { _ in })
    }

    private func snapshot() -> PlanSnapshot {
        PlanSnapshot(plan: TestData.plan(["id": 7]), workouts: [TestData.workout(["id": 1, "plan_id": 7])])
    }

    @Test func returnsSnapshotWhenDone() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = [.success(.generating()), .success(.generating()), .success(.done(snapshot()))] }
        let outcome = await poller(service).wait(jobID: "job-1")
        #expect(outcome == .done(snapshot()))
        #expect(service.calls.withLock { $0 }.count == 3)
    }

    @Test func serverErrorMessageIsShown() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = [.success(.error("Gemini quota exceeded"))] }
        #expect(await poller(service).wait(jobID: "j") == .failed("Gemini quota exceeded"))
    }

    @Test func missingServerErrorUsesDefault() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = [.success(.error(nil))] }
        #expect(await poller(service).wait(jobID: "j") == .failed("We couldn't build this plan. Please try again."))
    }

    @Test func notFoundMeansLost() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = [.failure(.http(status: 404, message: "Job not found.", code: nil))] }
        #expect(await poller(service).wait(jobID: "j") == .lost)
    }

    @Test func transportErrorsRetryThenFail() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = Array(repeating: .failure(.transport("offline")), count: 6) }
        #expect(await poller(service).wait(jobID: "j") == .failed(JobPoller.offlineMessage))
        #expect(service.calls.withLock { $0 }.count == 5)
    }

    @Test func transportBlipThenDone() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = [.failure(.transport("blip")), .success(.done(nil))] }
        #expect(await poller(service).wait(jobID: "j") == .done(nil))
    }

    @Test func timesOut() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = [.success(.generating())] }
        let outcome = await poller(service, timeout: .seconds(6)).wait(jobID: "j")
        #expect(outcome == .failed(JobPoller.slowMessage))
        #expect(service.calls.withLock { $0 }.count == 3)   // 6 s / 2 s
    }

    @Test func cancellationStops() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = [.success(.generating())] }
        let real = JobPoller(service: service, interval: .seconds(2), timeout: .seconds(60),
                             sleep: { try await Task.sleep(for: $0) })
        let task = Task { await real.wait(jobID: "j") }
        task.cancel()
        #expect(await task.value == .cancelled)
    }

    @Test func serviceHitsRealPaths() async throws {
        let client = makeStubClient { request in
            switch (request.httpMethod, request.url?.path()) {
            case ("GET", "/api/coach/plan-status/abc"):
                return (200, json(["status": "generating", "plan_id": 3]))
            case ("POST", "/api/coach/adapt-week"):
                return (200, json(["job_id": "abc", "plan_id": 3, "week_number": 2]))
            default:
                return (404, Data())
            }
        }
        let service = GenerationService(client: client)
        let start = try await service.adaptWeek(AdaptWeekBody(planId: 3, weekNumber: 2, overallRpe: nil, fatigueLevel: "hard",
                                                               fatigueNotes: nil, lang: "en", clientToday: "2026-10-07"))
        #expect(start.jobId == "abc")
        #expect(try await service.status(jobID: "abc").status == "generating")
    }
}
```

- [ ] **Step 3: Run to verify failure**

Run: `ios-native/scripts/test.sh`
Expected: compile errors.

- [ ] **Step 4: Implement** `Core/Generation/GenerationModels.swift`

```swift
import Foundation

enum JobKind: String, Codable, Sendable {
    case newPlan, nextWeek, adaptWeek
}

/// Every job-starting endpoint returns at least `job_id`.
struct JobStart: Decodable, Sendable, Equatable {
    let jobId: String
}

/// POST /api/auth/onboarding: a job when a plan is being built, the user when `skip_plan` was set.
struct OnboardingResult: Decodable, Sendable {
    let jobId: String?
    let user: User?
}

/// GET /api/coach/plan-status/{job_id}
struct JobStatus: Decodable, Sendable {
    let status: String
    let planId: Int?
    let plan: Plan?
    let workouts: [Workout]?
    let error: String?

    var snapshot: PlanSnapshot? {
        guard let plan else { return nil }
        return PlanSnapshot(plan: plan, workouts: workouts ?? [])
    }
}

enum JobOutcome: Equatable, Sendable {
    /// Finished. The snapshot is nil only if the server omitted the plan; reload in that case.
    case done(PlanSnapshot?)
    case failed(String)
    /// The server no longer knows the job (it restarted). Reload the active plan.
    case lost
    case cancelled
}

struct NextBlockBody: Encodable, Sendable {
    let planId: Int
    let blockNumber: Int
    let overallRpe: Int?
    let notes: String?
    let overrideGate: Bool
    let lang: String
}

struct AdaptWeekBody: Encodable, Sendable {
    let planId: Int
    let weekNumber: Int
    let overallRpe: Int?
    let fatigueLevel: String?
    let fatigueNotes: String?
    let lang: String
    let clientToday: String
}
```

- [ ] **Step 5: Implement** `Core/Generation/GenerationService.swift`

```swift
import Foundation

protocol GenerationServicing: Sendable {
    func completeOnboarding(_ body: OnboardingBody) async throws -> OnboardingResult
    func generatePlan(_ body: PlanBody) async throws -> JobStart
    func generateNextBlock(_ body: NextBlockBody) async throws -> JobStart
    func adaptWeek(_ body: AdaptWeekBody) async throws -> JobStart
    func status(jobID: String) async throws -> JobStatus
}

struct GenerationService: GenerationServicing {
    let client: APIClient

    func completeOnboarding(_ body: OnboardingBody) async throws -> OnboardingResult {
        try await client.send(.send(.post, "/api/auth/onboarding", body: body))
    }

    func generatePlan(_ body: PlanBody) async throws -> JobStart {
        try await client.send(.send(.post, "/api/coach/generate-plan", body: body))
    }

    func generateNextBlock(_ body: NextBlockBody) async throws -> JobStart {
        try await client.send(.send(.post, "/api/coach/generate-next-block", body: body))
    }

    func adaptWeek(_ body: AdaptWeekBody) async throws -> JobStart {
        try await client.send(.send(.post, "/api/coach/adapt-week", body: body))
    }

    func status(jobID: String) async throws -> JobStatus {
        try await client.send(.get("/api/coach/plan-status/\(jobID)"))
    }
}
```

- [ ] **Step 6: Implement** `Core/Generation/JobPoller.swift`

```swift
import Foundation

struct JobPoller: Sendable {
    static let slowMessage = "This is taking longer than usual. Your plan may still appear: pull down on the Plan tab in a minute to check."
    static let offlineMessage = "Lost connection while building your plan. It may still finish: pull down on the Plan tab to check."
    private static let defaultError = "We couldn't build this plan. Please try again."

    let service: any GenerationServicing
    let interval: Duration
    let timeout: Duration
    let sleep: @Sendable (Duration) async throws -> Void

    init(service: any GenerationServicing,
         interval: Duration = .seconds(2),
         timeout: Duration = .seconds(240),
         sleep: @escaping @Sendable (Duration) async throws -> Void = { try await Task.sleep(for: $0) }) {
        self.service = service
        self.interval = interval
        self.timeout = timeout
        self.sleep = sleep
    }

    func wait(jobID: String) async -> JobOutcome {
        let attempts = max(1, Int(timeout / interval))
        var transportFailures = 0
        for attempt in 0..<attempts {
            if Task.isCancelled { return .cancelled }
            do {
                let status = try await service.status(jobID: jobID)
                transportFailures = 0
                switch status.status {
                case "done": return .done(status.snapshot)
                case "error": return .failed(status.error ?? Self.defaultError)
                default: break
                }
            } catch APIError.http(404, _, _) {
                return .lost
            } catch APIError.transport {
                transportFailures += 1
                if transportFailures >= 5 { return .failed(Self.offlineMessage) }
            } catch let error as APIError {
                return .failed(error.userMessage)
            } catch {
                return .failed(error.localizedDescription)
            }
            if attempt < attempts - 1 {
                do { try await sleep(interval) } catch { return .cancelled }
            }
        }
        return .failed(Self.slowMessage)
    }
}
```

Also create `Core/Plan/PlanSetupDraft.swift` with placeholders that Task 2 replaces in full:

```swift
import Foundation

struct OnboardingBody: Encodable, Sendable { var skipPlan = false }
struct PlanBody: Encodable, Sendable { var goalType = "" }
```

- [ ] **Step 7: Run tests**

Run: `ios-native/scripts/test.sh`
Expected: all pass. `timesOut` makes exactly 3 status calls: `Int(6 s / 2 s) = 3` attempts.

- [ ] **Step 8: Commit**

```bash
git add ios-native
git commit -m "feat(ios): generation job service and poller"
```

---

### Task 2: Plan setup draft, validation and request bodies

**Files:**
- Modify: `ios-native/UphillAI/Core/Plan/PlanSetupDraft.swift` (replace the Task 1 placeholders)
- Test: `ios-native/UphillAITests/Plan/PlanSetupDraftTests.swift`

**Interfaces:**
- Consumes: `Weekday`, `PlanCalendar` (Phase 1), `User` (Phase 0).
- Produces:
  - `enum SetupGoal: String, CaseIterable, Sendable { case race, distance, startRunning = "start_running", returning = "return", recovery }` with `title`, `subtitle`, `systemImage`
  - `enum RaceGoal: String, CaseIterable, Sendable { case finish, time, optimal }` with `title`
  - `enum Terrain: String, CaseIterable, Sendable { case trail, road, mixed }`
  - `enum TrainingEnvironment: String, CaseIterable, Sendable { case flat, hilly, mixed }`
  - `enum SetupStep: Equatable, Sendable { case goal, details, schedule, aboutYou, review }` with `static func steps(for goal: SetupGoal?, includeAboutYou: Bool) -> [SetupStep]`
  - `enum SetupField: Hashable, Sendable` (one case per validated field)
  - `struct SetupIssue: Equatable, Sendable { let field: SetupField; let message: String }`
  - `struct PlanSetupDraft: Equatable, Sendable` (fields below) with `init(prefill user: User?, today: Date, calendar: Calendar)`, `func issues(for step: SetupStep, today: Date, calendar: Calendar) -> [SetupIssue]`, `func onboardingBody(skipPlan: Bool, calendar: Calendar) -> OnboardingBody`, `func planBody(calendar: Calendar) -> PlanBody`, `var summaryLines: [String]`
  - Option lists `PlanSetupDraft.timeAwayOptions`, `fitnessFeelOptions`, `raceDistanceOptions`, `recoveryFeelOptions` (exact strings below; the backend passes them to the prompt verbatim, same as the web)
  - Full `OnboardingBody` and `PlanBody`

Validation messages (exact):

| Step | Field | Rule | Message |
|---|---|---|---|
| goal | `.goal` | a goal is chosen | "Choose what you're training for." |
| details (race) | `.raceName` | non-empty after trimming | "Add the race name." |
| details (race, distance) | `.raceDate` | at least 14 days after today | "Pick a date at least 2 weeks away so the plan has room to build." |
| details (race, distance) | `.distance` | 1–400 km | "Enter a distance between 1 and 400 km." |
| details (race, distance) | `.targetTime` | when goal is `time`: 10 min – 120 h | "Enter your target time, for example 6:30." |
| details (return) | `.timeAway`, `.fitnessFeel` | chosen | "Choose how long you've been away." / "Choose how you feel right now." |
| details (recovery) | `.raceCompleted`, `.recoveryFeel` | chosen | "Choose the race you just finished." / "Choose how your body feels." |
| details (recovery) | `.daysSinceRace` | 0–60 | "Enter 0 to 60 days." |
| schedule | `.preferredDays` | count == daysPerWeek | "Pick \(n) days to match \(n) runs a week." |
| schedule | `.longRunDay` | in preferredDays | "Your long run day must be one of your running days." |
| schedule | `.weeklyKm` | 0–250 | "Enter 0 to 250 km." |
| schedule | `.startDate` | not before today | "Start today or later." |
| aboutYou | `.height` | nil or 100–230 | "Height should be between 100 and 230 cm." |
| aboutYou | `.weight` | nil or 30–200 | "Weight should be between 30 and 200 kg." |
| aboutYou | `.maxHr` | nil or 120–230 | "Max heart rate should be between 120 and 230." |
| aboutYou | `.restingHr` | nil or 30–110 | "Resting heart rate should be between 30 and 110." |

- [ ] **Step 1: Write the failing tests** `PlanSetupDraftTests.swift`

```swift
import Foundation
import Testing
@testable import UphillAI

struct PlanSetupDraftTests {
    private let cal: Calendar = {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        return c
    }()
    private var today: Date { PlanCalendar.day(from: "2026-10-07", calendar: cal)! }
    private func day(_ s: String) -> Date { PlanCalendar.day(from: s, calendar: cal)! }

    private func encoded(_ body: some Encodable) throws -> [String: Any] {
        try #require(try JSONSerialization.jsonObject(with: JSONCoding.encoder.encode(body)) as? [String: Any])
    }

    private func raceDraft() -> PlanSetupDraft {
        var d = PlanSetupDraft(prefill: nil, today: today, calendar: cal)
        d.goal = .race
        d.raceName = "  Vietnam Mountain Marathon 42K "
        d.raceDate = day("2026-12-19")
        d.distanceKm = 42
        d.elevationGainM = 2400
        d.raceGoal = .time
        d.targetMinutes = 390
        d.daysPerWeek = 4
        d.preferredDays = [.tuesday, .thursday, .saturday, .sunday]
        d.longRunDay = .saturday
        d.currentWeeklyKm = 30
        d.environment = .hilly
        return d
    }

    @Test func stepsDependOnGoal() {
        #expect(SetupStep.steps(for: nil, includeAboutYou: true) == [.goal])
        #expect(SetupStep.steps(for: .race, includeAboutYou: true) == [.goal, .details, .schedule, .aboutYou, .review])
        #expect(SetupStep.steps(for: .startRunning, includeAboutYou: true) == [.goal, .schedule, .aboutYou, .review])
        #expect(SetupStep.steps(for: .returning, includeAboutYou: false) == [.goal, .details, .schedule, .review])
    }

    @Test func defaultsFromPrefillAndToday() throws {
        let user = try Fixture.decode(User.self, "auth_me.json")
        let d = PlanSetupDraft(prefill: user, today: today, calendar: cal)
        #expect(d.startDate == today)
        #expect(d.preferredDays.count == d.daysPerWeek)
        #expect(d.preferredDays.contains(d.longRunDay))
    }

    @Test func validRaceDraftHasNoIssues() {
        let d = raceDraft()
        for step in [SetupStep.goal, .details, .schedule, .aboutYou, .review] {
            #expect(d.issues(for: step, today: today, calendar: cal).isEmpty, "step \(step)")
        }
    }

    @Test func raceDetailIssues() {
        var d = raceDraft()
        d.raceName = "   "
        d.raceDate = day("2026-10-15")
        d.distanceKm = 0
        d.targetMinutes = nil
        let fields = d.issues(for: .details, today: today, calendar: cal).map(\.field)
        #expect(fields == [.raceName, .raceDate, .distance, .targetTime])
        #expect(d.issues(for: .details, today: today, calendar: cal).first?.message == "Add the race name.")
    }

    @Test func distanceGoalNeedsNoName() {
        var d = raceDraft()
        d.goal = .distance
        d.raceName = ""
        #expect(d.issues(for: .details, today: today, calendar: cal).isEmpty)
    }

    @Test func scheduleIssues() {
        var d = raceDraft()
        d.daysPerWeek = 5
        d.longRunDay = .monday
        d.currentWeeklyKm = 300
        d.startDate = day("2026-10-06")
        let issues = d.issues(for: .schedule, today: today, calendar: cal)
        #expect(issues.map(\.field) == [.preferredDays, .longRunDay, .weeklyKm, .startDate])
        #expect(issues[0].message == "Pick 5 days to match 5 runs a week.")
    }

    @Test func returnAndRecoveryDetails() {
        var d = PlanSetupDraft(prefill: nil, today: today, calendar: cal)
        d.goal = .returning
        #expect(d.issues(for: .details, today: today, calendar: cal).map(\.field) == [.timeAway, .fitnessFeel])
        d.goal = .recovery
        d.daysSinceRace = 90
        #expect(d.issues(for: .details, today: today, calendar: cal).map(\.field) == [.raceCompleted, .daysSinceRace, .recoveryFeel])
    }

    @Test func aboutYouRanges() {
        var d = raceDraft()
        d.heightCm = 90
        d.maxHr = 250
        #expect(d.issues(for: .aboutYou, today: today, calendar: cal).map(\.field) == [.height, .maxHr])
    }

    @Test func onboardingBodyForTimedRace() throws {
        var d = raceDraft()
        d.birthDate = day("1991-04-02")
        d.injuryHistory = "  "
        let body = try encoded(d.onboardingBody(skipPlan: false, calendar: cal))
        #expect(body["goal_type"] as? String == "race")
        #expect(body["race_goal"] as? String == "time")
        #expect(body["expected_finish_time"] as? String == "6:30")
        #expect(body["race_name"] as? String == "Vietnam Mountain Marathon 42K")
        #expect(body["race_date"] as? String == "2026-12-19")
        #expect(body["course_distance_km"] as? Double == 42)
        #expect(body["preferred_run_days"] as? [String] == ["Tuesday", "Thursday", "Saturday", "Sunday"])
        #expect(body["long_run_day"] as? String == "Saturday")
        #expect(body["training_environment"] as? String == "hilly")
        #expect(body["plan_start_date"] as? String == "2026-10-07")
        #expect(body["dob"] as? String == "1991-04-02")
        #expect(body["skip_plan"] as? Bool == false)
        #expect(body["lang"] as? String == "en")
        #expect(body["injury_history"] == nil)
        #expect(body["time_away"] == nil)
    }

    @Test func planBodyMapsRaceGoalToGoalType() throws {
        let body = try encoded(raceDraft().planBody(calendar: cal))
        #expect(body["goal_type"] as? String == "time")
        #expect(body["target_time_hours"] as? Double == 6.5)
        #expect(body["preferred_days"] as? [String] == ["Tuesday", "Thursday", "Saturday", "Sunday"])
        #expect(body["current_weekly_km"] as? Double == 30)
        #expect(body["terrain"] as? String == "trail")
    }

    @Test func planBodyForStartRunningOmitsRaceFields() throws {
        var d = raceDraft()
        d.goal = .startRunning
        let body = try encoded(d.planBody(calendar: cal))
        #expect(body["goal_type"] as? String == "start_running")
        #expect(body["race_name"] == nil)
        #expect(body["race_date"] == nil)
        #expect(body["target_time_hours"] == nil)
    }

    @Test func distanceGoalGetsGeneratedName() throws {
        var d = raceDraft()
        d.goal = .distance
        d.raceName = ""
        d.distanceKm = 21.1
        d.raceGoal = .finish
        let body = try encoded(d.planBody(calendar: cal))
        #expect(body["race_name"] as? String == "21.1 km goal")
        #expect(body["goal_type"] as? String == "finish")
    }

    @Test func summaryLinesDescribeInputs() {
        #expect(raceDraft().summaryLines == [
            "Vietnam Mountain Marathon 42K on Sat 19 Dec",
            "Target time 6:30",
            "4 runs a week, long run on Saturday",
            "Starting from 30 km a week",
        ])
    }
}
```

`summaryLines` formats the date with `en_US_POSIX`-independent `Date.FormatStyle` in the test calendar's time zone; pass the calendar's time zone into the format style (see implementation) so the test is stable.

- [ ] **Step 2: Run to verify failure**

Run: `ios-native/scripts/test.sh`
Expected: compile errors.

- [ ] **Step 3: Implement** `Core/Plan/PlanSetupDraft.swift`

```swift
import Foundation

enum SetupGoal: String, CaseIterable, Sendable {
    case race, distance, startRunning = "start_running", returning = "return", recovery

    var title: String {
        switch self {
        case .race: "A specific race"
        case .distance: "A distance"
        case .startRunning: "Start running"
        case .returning: "Come back after a break"
        case .recovery: "Recover from a race"
        }
    }

    var subtitle: String {
        switch self {
        case .race: "Build toward a race on a set date."
        case .distance: "Be ready for a distance, like your first 21 km."
        case .startRunning: "From walk-run to running 30 minutes."
        case .returning: "Rebuild safely after time off."
        case .recovery: "Easy weeks after a hard effort."
        }
    }

    var systemImage: String {
        switch self {
        case .race: "flag.checkered"
        case .distance: "point.topleft.down.to.point.bottomright.curvepath"
        case .startRunning: "figure.walk"
        case .returning: "arrow.uturn.forward"
        case .recovery: "bed.double"
        }
    }

    var isEvent: Bool { self == .race || self == .distance }
}

enum RaceGoal: String, CaseIterable, Sendable {
    case finish, time, optimal

    var title: String {
        switch self {
        case .finish: "Finish strong"
        case .time: "Hit a target time"
        case .optimal: "My best possible time"
        }
    }
}

enum Terrain: String, CaseIterable, Sendable { case trail, road, mixed }
enum TrainingEnvironment: String, CaseIterable, Sendable { case flat, hilly, mixed }

enum SetupStep: Equatable, Sendable {
    case goal, details, schedule, aboutYou, review

    static func steps(for goal: SetupGoal?, includeAboutYou: Bool) -> [SetupStep] {
        guard let goal else { return [.goal] }
        var steps: [SetupStep] = [.goal]
        if goal != .startRunning { steps.append(.details) }
        steps.append(.schedule)
        if includeAboutYou { steps.append(.aboutYou) }
        steps.append(.review)
        return steps
    }
}

enum SetupField: Hashable, Sendable {
    case goal, raceName, raceDate, distance, targetTime, timeAway, fitnessFeel, raceCompleted, daysSinceRace, recoveryFeel
    case preferredDays, longRunDay, weeklyKm, startDate, height, weight, maxHr, restingHr
}

struct SetupIssue: Equatable, Sendable {
    let field: SetupField
    let message: String
}

/// Answers shared by onboarding and "Start new plan". Free-text option values
/// are sent verbatim: the backend passes them into the generation prompt, same as the web.
struct PlanSetupDraft: Equatable, Sendable {
    static let timeAwayOptions = ["< 2 weeks", "2–6 weeks", "1–3 months", "3–6 months", "6+ months"]
    static let fitnessFeelOptions = [
        "Feeling good, just need structure",
        "A bit rusty, slightly deconditioned",
        "Significant deconditioning — starting nearly fresh",
    ]
    static let raceDistanceOptions = ["5k", "10k", "Half Marathon", "Marathon", "Ultra (< 60k)", "Ultra (60k+)"]
    static let recoveryFeelOptions = [
        "Feeling great, minimal soreness",
        "Moderate fatigue, some soreness",
        "Very fatigued — need real rest",
    ]

    var goal: SetupGoal?
    // Race / distance
    var raceName = ""
    var raceDate: Date?
    var distanceKm: Double?
    var elevationGainM: Double?
    var terrain: Terrain = .trail
    var raceGoal: RaceGoal = .finish
    var targetMinutes: Int?
    // Return
    var timeAway: String?
    var fitnessFeel: String?
    // Recovery
    var raceDistanceCompleted: String?
    var daysSinceRace = 7
    var recoveryFeel: String?
    // Schedule
    var daysPerWeek = 4
    var preferredDays: Set<Weekday> = [.tuesday, .thursday, .saturday, .sunday]
    var longRunDay: Weekday = .saturday
    var currentWeeklyKm: Double = 20
    var environment: TrainingEnvironment = .flat
    var hasGymAccess = false
    var startDate: Date
    // About you (optional)
    var birthDate: Date?
    var gender: String?
    var heightCm: Double?
    var weightKg: Double?
    var maxHr: Int?
    var restingHr: Int?
    var injuryHistory = ""
    var notes = ""

    init(prefill user: User?, today: Date, calendar: Calendar) {
        startDate = calendar.startOfDay(for: today)
        guard let user else { return }
        if let days = user.daysPerWeek, (3...7).contains(days) { daysPerWeek = days }
        if let km = user.currentWeeklyKm { currentWeeklyKm = km }
        if let data = user.preferredRunDays?.data(using: .utf8),
           let names = try? JSONDecoder().decode([String].self, from: data) {
            let days = Set(names.compactMap(Weekday.init(rawValue:)))
            if days.count == daysPerWeek { preferredDays = days }
        }
        if let long = user.longRunDay.flatMap(Weekday.init(rawValue:)) { longRunDay = long }
        if preferredDays.count != daysPerWeek { preferredDays = Self.defaultDays(count: daysPerWeek) }
        if !preferredDays.contains(longRunDay) { longRunDay = preferredDays.contains(.saturday) ? .saturday : orderedDays.last! }
        heightCm = user.heightCm
        weightKg = user.weightKg
        maxHr = user.maxHr
        restingHr = user.restingHr
        gender = user.gender
        birthDate = PlanCalendar.day(from: user.dob, calendar: calendar)
        injuryHistory = user.injuryHistory ?? ""
    }

    /// Spread runs through the week with the long run on Saturday.
    static func defaultDays(count: Int) -> Set<Weekday> {
        switch count {
        case 3: [.tuesday, .thursday, .saturday]
        case 4: [.tuesday, .thursday, .saturday, .sunday]
        case 5: [.monday, .tuesday, .thursday, .saturday, .sunday]
        case 6: [.monday, .tuesday, .wednesday, .thursday, .saturday, .sunday]
        default: Set(Weekday.allCases)
        }
    }

    var orderedDays: [Weekday] { Weekday.allCases.filter(preferredDays.contains) }

    // MARK: Validation

    func issues(for step: SetupStep, today: Date, calendar: Calendar) -> [SetupIssue] {
        var issues: [SetupIssue] = []
        func add(_ field: SetupField, _ message: String) { issues.append(SetupIssue(field: field, message: message)) }
        let start = calendar.startOfDay(for: today)

        switch step {
        case .goal:
            if goal == nil { add(.goal, "Choose what you're training for.") }
        case .details:
            switch goal {
            case .race, .distance:
                if goal == .race, raceName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    add(.raceName, "Add the race name.")
                }
                let earliest = calendar.date(byAdding: .day, value: 14, to: start)!
                if raceDate.map({ $0 < earliest }) ?? true {
                    add(.raceDate, "Pick a date at least 2 weeks away so the plan has room to build.")
                }
                if !(1...400).contains(distanceKm ?? 0) { add(.distance, "Enter a distance between 1 and 400 km.") }
                if raceGoal == .time, !(10...7200).contains(targetMinutes ?? 0) {
                    add(.targetTime, "Enter your target time, for example 6:30.")
                }
            case .returning:
                if timeAway == nil { add(.timeAway, "Choose how long you've been away.") }
                if fitnessFeel == nil { add(.fitnessFeel, "Choose how you feel right now.") }
            case .recovery:
                if raceDistanceCompleted == nil { add(.raceCompleted, "Choose the race you just finished.") }
                if !(0...60).contains(daysSinceRace) { add(.daysSinceRace, "Enter 0 to 60 days.") }
                if recoveryFeel == nil { add(.recoveryFeel, "Choose how your body feels.") }
            case .startRunning, nil:
                break
            }
        case .schedule:
            if preferredDays.count != daysPerWeek {
                add(.preferredDays, "Pick \(daysPerWeek) days to match \(daysPerWeek) runs a week.")
            }
            if !preferredDays.contains(longRunDay) { add(.longRunDay, "Your long run day must be one of your running days.") }
            if !(0...250).contains(currentWeeklyKm) { add(.weeklyKm, "Enter 0 to 250 km.") }
            if calendar.startOfDay(for: startDate) < start { add(.startDate, "Start today or later.") }
        case .aboutYou:
            if let h = heightCm, !(100...230).contains(h) { add(.height, "Height should be between 100 and 230 cm.") }
            if let w = weightKg, !(30...200).contains(w) { add(.weight, "Weight should be between 30 and 200 kg.") }
            if let hr = maxHr, !(120...230).contains(hr) { add(.maxHr, "Max heart rate should be between 120 and 230.") }
            if let hr = restingHr, !(30...110).contains(hr) { add(.restingHr, "Resting heart rate should be between 30 and 110.") }
        case .review:
            break
        }
        return issues
    }

    // MARK: Request bodies

    private var trimmedName: String { raceName.trimmingCharacters(in: .whitespacesAndNewlines) }
    private var eventName: String? {
        guard goal?.isEvent == true else { return nil }
        if !trimmedName.isEmpty { return trimmedName }
        guard let km = distanceKm else { return nil }
        return km.formatted(.number.precision(.fractionLength(0...1)).locale(Locale(identifier: "en_US_POSIX"))) + " km goal"
    }

    private var targetText: String? {
        guard goal?.isEvent == true, raceGoal == .time, let m = targetMinutes else { return nil }
        return "\(m / 60):\(String(format: "%02d", m % 60))"
    }

    private func nonEmpty(_ s: String) -> String? {
        let t = s.trimmingCharacters(in: .whitespacesAndNewlines)
        return t.isEmpty ? nil : t
    }

    func onboardingBody(skipPlan: Bool, calendar: Calendar) -> OnboardingBody {
        let event = goal?.isEvent == true
        return OnboardingBody(
            lang: "en",
            dob: birthDate.map { PlanCalendar.ymd($0, calendar: calendar) },
            gender: gender,
            heightCm: heightCm,
            weightKg: weightKg,
            goalType: goal?.rawValue ?? SetupGoal.startRunning.rawValue,
            maxHr: maxHr,
            restingHr: restingHr,
            injuryHistory: nonEmpty(injuryHistory),
            raceName: event ? eventName : nil,
            raceDate: event ? raceDate.map { PlanCalendar.ymd($0, calendar: calendar) } : nil,
            courseDistanceKm: event ? distanceKm : nil,
            courseElevationGainM: event ? elevationGainM : nil,
            terrain: event ? terrain.rawValue : nil,
            raceGoal: event ? raceGoal.rawValue : nil,
            expectedFinishTime: targetText,
            daysPerWeek: daysPerWeek,
            preferredRunDays: orderedDays.map(\.rawValue),
            longRunDay: longRunDay.rawValue,
            currentWeeklyKm: currentWeeklyKm,
            hasGymAccess: hasGymAccess,
            trainingEnvironment: environment.rawValue,
            timeAway: goal == .returning ? timeAway : nil,
            fitnessFeel: goal == .returning ? fitnessFeel : nil,
            raceDistanceCompleted: goal == .recovery ? raceDistanceCompleted : nil,
            daysSinceRace: goal == .recovery ? daysSinceRace : nil,
            recoveryFeel: goal == .recovery ? recoveryFeel : nil,
            skipPlan: skipPlan,
            planStartDate: PlanCalendar.ymd(startDate, calendar: calendar),
            athleteNotes: nonEmpty(notes)
        )
    }

    func planBody(calendar: Calendar) -> PlanBody {
        let event = goal?.isEvent == true
        return PlanBody(
            lang: "en",
            raceName: event ? eventName : nil,
            raceDate: event ? raceDate.map { PlanCalendar.ymd($0, calendar: calendar) } : nil,
            goalType: event ? raceGoal.rawValue : (goal ?? .startRunning).rawValue,
            currentWeeklyKm: currentWeeklyKm,
            targetTimeHours: (event && raceGoal == .time) ? targetMinutes.map { Double($0) / 60 } : nil,
            terrain: event ? terrain.rawValue : nil,
            courseDistanceKm: event ? distanceKm : nil,
            courseElevationGainM: event ? elevationGainM : nil,
            preferredDays: orderedDays.map(\.rawValue),
            longRunDay: longRunDay.rawValue,
            daysPerWeek: daysPerWeek,
            hasGymAccess: hasGymAccess,
            trainingEnvironment: environment.rawValue,
            planStartDate: PlanCalendar.ymd(startDate, calendar: calendar),
            timeAway: goal == .returning ? timeAway : nil,
            fitnessFeel: goal == .returning ? fitnessFeel : nil,
            raceDistanceCompleted: goal == .recovery ? raceDistanceCompleted : nil,
            daysSinceRace: goal == .recovery ? daysSinceRace : nil,
            recoveryFeel: goal == .recovery ? recoveryFeel : nil,
            athleteNotes: nonEmpty(notes)
        )
    }

    /// Facts the plan is built from, shown while it generates. Inputs, not invented progress.
    var summaryLines: [String] {
        var lines: [String] = []
        if goal?.isEvent == true, let name = eventName {
            if let date = raceDate {
                let style = Date.FormatStyle(date: .omitted, time: .omitted, locale: Locale(identifier: "en_GB"),
                                             calendar: Calendar(identifier: .gregorian), timeZone: .current)
                    .weekday(.abbreviated).day().month(.abbreviated)
                lines.append("\(name) on \(date.formatted(style))")
            } else {
                lines.append(name)
            }
            if let target = targetText { lines.append("Target time \(target)") }
        } else if let goal {
            lines.append(goal.title)
        }
        lines.append("\(daysPerWeek) runs a week, long run on \(longRunDay.rawValue)")
        lines.append("Starting from \(Int(currentWeeklyKm.rounded())) km a week")
        return lines
    }
}

/// POST /api/auth/onboarding. Nil fields are omitted from the JSON.
struct OnboardingBody: Encodable, Sendable {
    var lang: String
    var dob: String?
    var gender: String?
    var heightCm: Double?
    var weightKg: Double?
    var goalType: String
    var maxHr: Int?
    var restingHr: Int?
    var injuryHistory: String?
    var raceName: String?
    var raceDate: String?
    var courseDistanceKm: Double?
    var courseElevationGainM: Double?
    var terrain: String?
    var raceGoal: String?
    var expectedFinishTime: String?
    var daysPerWeek: Int
    var preferredRunDays: [String]
    var longRunDay: String
    var currentWeeklyKm: Double
    var hasGymAccess: Bool
    var trainingEnvironment: String
    var timeAway: String?
    var fitnessFeel: String?
    var raceDistanceCompleted: String?
    var daysSinceRace: Int?
    var recoveryFeel: String?
    var skipPlan: Bool
    var planStartDate: String
    var athleteNotes: String?
}

/// POST /api/coach/generate-plan. Nil fields are omitted from the JSON.
struct PlanBody: Encodable, Sendable {
    var lang: String
    var raceName: String?
    var raceDate: String?
    var goalType: String
    var currentWeeklyKm: Double
    var targetTimeHours: Double?
    var terrain: String?
    var courseDistanceKm: Double?
    var courseElevationGainM: Double?
    var preferredDays: [String]
    var longRunDay: String
    var daysPerWeek: Int
    var hasGymAccess: Bool
    var trainingEnvironment: String
    var planStartDate: String
    var timeAway: String?
    var fitnessFeel: String?
    var raceDistanceCompleted: String?
    var daysSinceRace: Int?
    var recoveryFeel: String?
    var athleteNotes: String?
}
```

Update `FakeGenerationService` (Task 1) if a field name it reads changed: it reads `body.skipPlan` and `body.goalType`, which exist.

`summaryLines` uses `.current` for the time zone; in the test the date was built in Asia/Ho_Chi_Minh. If the simulator's zone shifts the day, build the format style with `timeZone: calendar.timeZone` by adding a `calendar` parameter to `summaryLines(calendar:)` instead, and update the test call. Pick whichever keeps the test deterministic and note it in the report.

- [ ] **Step 4: Run tests**

Run: `ios-native/scripts/test.sh`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add ios-native
git commit -m "feat(ios): plan setup draft with validation and request bodies"
```

---

### Task 3: Generation center (app-wide job owner)

**Files:**
- Create: `ios-native/UphillAI/Core/Generation/GenerationCenter.swift`
- Modify: `ios-native/UphillAI/App/AppModel.swift`, `ios-native/UphillAI/Features/Plan/PlanViewModel.swift`
- Test: `ios-native/UphillAITests/Generation/GenerationCenterTests.swift`

**Interfaces:**
- Consumes: `JobPoller`, `GenerationServicing`, `JobKind`, `JobOutcome` (Task 1); `PlanViewModel` (Phase 1); `AppModel` (Phases 0–1).
- Produces:
  - `@Observable @MainActor final class GenerationCenter` with:
    - `struct Running: Equatable { let kind: JobKind; let jobID: String; let startedAt: Date; let summary: [String] }`
    - `private(set) var running: Running?`, `private(set) var lastOutcome: (kind: JobKind, outcome: JobOutcome)?` (Equatable via a small struct `Finished { kind, outcome }`)
    - `init(service: any GenerationServicing, defaults: UserDefaults = .standard, makePoller: @escaping (any GenerationServicing) -> JobPoller = { JobPoller(service: $0) }, now: @escaping () -> Date = { .now })`
    - `var onFinished: (@MainActor (JobKind, JobOutcome) async -> Void)?`
    - `func track(kind: JobKind, jobID: String, summary: [String])` (starts polling, persists the job)
    - `func resumeIfNeeded()` (on launch: resumes a persisted job)
    - `func clearOutcome()`
    - `static let defaultsKey = "UPHILL_RUNNING_JOB"`
  - `PlanViewModel.adopt(_ snapshot: PlanSnapshot)` (public; resets to the current week, clears `cachedAt`, saves to the cache, sets `state = .loaded`)
  - `AppModel`: `let generation: GenerationCenter`, `let generationService: any GenerationServicing`, `let plan: PlanViewModel` (moved from `MainTabs` so the center can hand results to it), `func refreshUser() async`

Behaviour:
1. `track` cancels nothing already running for a different job; only one job is tracked at a time (a second `track` replaces the first; the backend already de-duplicates jobs per plan).
2. Persist `{kind, jobID, startedAt, summary}` as JSON in `UserDefaults` under `defaultsKey`; clear it when the job ends.
3. On finish call `onFinished(kind, outcome)`, set `lastOutcome`, clear `running`.
4. `AppModel` wires `onFinished`: `.done(snapshot?)` → `plan.adopt(snapshot)` or `await plan.load()` when nil; `.lost` → `await plan.load()`; after `.done`/`.lost` for `.newPlan`, `await refreshUser()` (onboarding flips `onboarding_complete`).

- [ ] **Step 1: Write the failing tests** `GenerationCenterTests.swift`

```swift
import Foundation
import Synchronization
import Testing
@testable import UphillAI

@MainActor
struct GenerationCenterTests {
    private func defaults() -> UserDefaults { UserDefaults(suiteName: "gen-\(UUID().uuidString)")! }

    private func center(_ service: FakeGenerationService, defaults: UserDefaults) -> GenerationCenter {
        GenerationCenter(service: service, defaults: defaults,
                         makePoller: { JobPoller(service: $0, interval: .milliseconds(1), timeout: .seconds(1), sleep: { _ in }) })
    }

    @Test func tracksUntilDoneAndReports() async {
        let service = FakeGenerationService()
        let snapshot = PlanSnapshot(plan: TestData.plan(["id": 9]), workouts: [])
        service.statuses.withLock { $0 = [.success(.generating()), .success(.done(snapshot))] }
        let store = defaults()
        let center = center(service, defaults: store)
        let finished = Mutex<[String]>([])
        center.onFinished = { kind, outcome in finished.withLock { $0.append("\(kind) \(outcome == .done(snapshot))") } }

        center.track(kind: .newPlan, jobID: "job-9", summary: ["A"])
        #expect(center.running?.jobID == "job-9")
        #expect(store.data(forKey: GenerationCenter.defaultsKey) != nil)

        while center.running != nil { await Task.yield() }
        #expect(finished.withLock { $0 } == ["newPlan true"])
        #expect(center.lastOutcome?.outcome == .done(snapshot))
        #expect(store.data(forKey: GenerationCenter.defaultsKey) == nil)
    }

    @Test func resumesPersistedJob() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = [.success(.done(nil))] }
        let store = defaults()
        let slow = FakeGenerationService()
        slow.statuses.withLock { $0 = [.success(.generating())] }
        // A real-sleep poller, so the first center is still waiting when we "relaunch".
        let first = GenerationCenter(service: slow, defaults: store,
                                     makePoller: { JobPoller(service: $0, interval: .seconds(60), timeout: .seconds(120)) })
        first.track(kind: .adaptWeek, jobID: "job-2", summary: [])
        first.cancelForTesting()   // the old process is gone; its persisted job stays
        // Simulate relaunch: a new center reading the same defaults.
        let second = center(service, defaults: store)
        second.resumeIfNeeded()
        #expect(second.running?.jobID == "job-2")
        #expect(second.running?.kind == .adaptWeek)
        while second.running != nil { await Task.yield() }
        #expect(service.calls.withLock { $0 }.first == "status job-2")
    }

    @Test func lostJobIsReported() async {
        let service = FakeGenerationService()   // empty script → 404 → lost
        let center = center(service, defaults: defaults())
        center.track(kind: .nextWeek, jobID: "gone", summary: [])
        while center.running != nil { await Task.yield() }
        #expect(center.lastOutcome?.outcome == .lost)
    }
}
```

`cancelForTesting()` cancels the polling task without clearing the persisted job (a cancelled poll returns `.cancelled`, which `start` ignores). It exists for tests only.

- [ ] **Step 2: Run to verify failure**

Run: `ios-native/scripts/test.sh`
Expected: compile errors.

- [ ] **Step 3: Implement** `Core/Generation/GenerationCenter.swift`

```swift
import Foundation
import Observation

@Observable
@MainActor
final class GenerationCenter {
    struct Running: Codable, Equatable {
        let kind: JobKind
        let jobID: String
        let startedAt: Date
        let summary: [String]
    }

    struct Finished: Equatable {
        let kind: JobKind
        let outcome: JobOutcome
    }

    static let defaultsKey = "UPHILL_RUNNING_JOB"

    private(set) var running: Running?
    private(set) var lastOutcome: Finished?
    var onFinished: (@MainActor (JobKind, JobOutcome) async -> Void)?

    private let service: any GenerationServicing
    private let defaults: UserDefaults
    private let makePoller: (any GenerationServicing) -> JobPoller
    private let now: () -> Date
    private var task: Task<Void, Never>?

    init(service: any GenerationServicing,
         defaults: UserDefaults = .standard,
         makePoller: @escaping (any GenerationServicing) -> JobPoller = { JobPoller(service: $0) },
         now: @escaping () -> Date = { .now }) {
        self.service = service
        self.defaults = defaults
        self.makePoller = makePoller
        self.now = now
    }

    func track(kind: JobKind, jobID: String, summary: [String]) {
        start(Running(kind: kind, jobID: jobID, startedAt: now(), summary: summary))
    }

    func resumeIfNeeded() {
        guard running == nil,
              let data = defaults.data(forKey: Self.defaultsKey),
              let saved = try? JSONDecoder().decode(Running.self, from: data) else { return }
        start(saved)
    }

    func clearOutcome() { lastOutcome = nil }

    func cancelForTesting() { task?.cancel() }

    private func start(_ job: Running) {
        task?.cancel()
        running = job
        lastOutcome = nil
        defaults.set(try? JSONEncoder().encode(job), forKey: Self.defaultsKey)
        let poller = makePoller(service)
        task = Task { [weak self] in
            let outcome = await poller.wait(jobID: job.jobID)
            guard let self, outcome != .cancelled else { return }
            await self.finish(job, outcome)
        }
    }

    private func finish(_ job: Running, _ outcome: JobOutcome) async {
        guard running?.jobID == job.jobID else { return }
        defaults.removeObject(forKey: Self.defaultsKey)
        running = nil
        lastOutcome = Finished(kind: job.kind, outcome: outcome)
        await onFinished?(job.kind, outcome)
    }
}
```

Update the test's `lastOutcome?.outcome` reads: `lastOutcome` is a `Finished?`.

- [ ] **Step 4: Add `adopt` to** `PlanViewModel.swift`

```swift
    /// A freshly generated plan or week from a finished job.
    func adopt(_ snapshot: PlanSnapshot) {
        apply(snapshot, resetWeek: true)
        cachedAt = nil
        actionError = nil
        cache.save(snapshot, as: .plan)
    }
```

- [ ] **Step 5: Wire it into** `AppModel.swift`

Add properties and construct them at the end of `init` (after `planService`):

```swift
    let generationService: any GenerationServicing
    let generation: GenerationCenter
    let plan: PlanViewModel
```

```swift
        generationService = GenerationService(client: client)
        generation = GenerationCenter(service: generationService)
        plan = PlanViewModel(service: planService, cache: cache)
        generation.onFinished = { [weak self] kind, outcome in
            guard let self else { return }
            switch outcome {
            case .done(let snapshot?): self.plan.adopt(snapshot)
            case .done(nil), .lost: await self.plan.load()
            case .failed, .cancelled: break
            }
            if kind == .newPlan, outcome != .cancelled { await self.refreshUser() }
        }
```

```swift
    /// Re-reads /api/auth/me (onboarding completion, profile edits).
    func refreshUser() async {
        if let user = try? await auth.me() { session.setUser(user) }
    }
```

`AppModel.init` needs `self` fully initialised before assigning `onFinished` with `[weak self]`; assign it as the last statement.

In `RootView`, `MainTabs` stops creating its own `PlanViewModel` and uses `app.plan`. Call `app.generation.resumeIfNeeded()` from `RootView`'s `.task` after `await app.restore()`. On sign-out, a new `AppModel` is not created, so reset the plan: in the `SessionStore` `onUserChange` hook path for `nil`, also clear the persisted job (`UserDefaults.standard.removeObject(forKey: GenerationCenter.defaultsKey)`). `PlanViewModel` keeps stale state across accounts otherwise: add `func reset()` to `PlanViewModel` (state `.loading`, snapshot nil, cachedAt nil, selectedWeek 1) and call it on sign-out.

- [ ] **Step 6: Run tests**

Run: `ios-native/scripts/test.sh`
Expected: all pass, including Phase 0–1 tests (update any test that constructed `MainTabs`-owned state).

- [ ] **Step 7: Commit**

```bash
git add ios-native
git commit -m "feat(ios): app-wide generation center that survives navigation and relaunch"
```

---

### Task 4: Plan setup view model

**Files:**
- Create: `ios-native/UphillAI/Features/Onboarding/PlanSetupViewModel.swift`
- Test: `ios-native/UphillAITests/Plan/PlanSetupViewModelTests.swift`

**Interfaces:**
- Consumes: `PlanSetupDraft`, `SetupStep`, `SetupIssue` (Task 2); `GenerationServicing`, `GenerationCenter` (Tasks 1, 3); `SessionStore` (Phase 0).
- Produces: `@Observable @MainActor final class PlanSetupViewModel` with:
  - `enum Mode: Equatable { case onboarding, newPlan }`
  - `enum Direction { case forward, backward }`
  - `var draft: PlanSetupDraft`, `private(set) var stepIndex: Int`, `private(set) var direction: Direction`, `private(set) var showIssues: Bool`, `private(set) var isSubmitting: Bool`, `private(set) var submitError: String?`, `private(set) var didStart: Bool`
  - `init(mode: Mode, user: User?, service: any GenerationServicing, generation: GenerationCenter, session: SessionStore, now: @escaping () -> Date = { .now }, calendar: Calendar = PlanCalendar.calendar)`
  - `var steps: [SetupStep]`, `var step: SetupStep`, `var progress: Double` (0…1, `(stepIndex + 1) / steps.count`), `var isFirstStep: Bool`, `var isLastStep: Bool`, `var issues: [SetupIssue]` (empty unless `showIssues`), `func issue(for field: SetupField) -> String?`
  - `func selectGoal(_ goal: SetupGoal)` (sets the goal and advances, since a goal tap is the answer)
  - `func next()`, `func back()`
  - `func setDaysPerWeek(_ n: Int)` (resets preferred days to `PlanSetupDraft.defaultDays(count:)` and keeps the long run day valid)
  - `func toggleDay(_ day: Weekday)`
  - `func submit() async` (builds the job), `func saveProfileOnly() async` (onboarding only: `skip_plan: true`)
  - `var primaryTitle: String` ("Next" on question steps, "Build my plan" on review)

Behaviour:
1. `next()` validates the current step; with issues it sets `showIssues = true` and stays; otherwise advances, resets `showIssues`, `direction = .forward`.
2. `back()` moves back one step (`direction = .backward`), never below 0.
3. Mode `.onboarding` includes the About-you step; `.newPlan` does not (profile already exists).
4. `submit()`: onboarding → `completeOnboarding(draft.onboardingBody(skipPlan: false))`; new plan → `generatePlan(draft.planBody())`. On a job id: `generation.track(kind: .newPlan, jobID:, summary: draft.summaryLines)`, `didStart = true`. Errors keep the draft and set `submitError` (`APIError.userMessage`).
5. `saveProfileOnly()`: `completeOnboarding(skipPlan: true)`; on success with a user, `session.setUser(user)` and `didStart = true` (the flow closes; Plan shows its empty state).
6. Changing the goal after moving on keeps `stepIndex` within the new step list.

- [ ] **Step 1: Write the failing tests** `PlanSetupViewModelTests.swift`

```swift
import Foundation
import Testing
@testable import UphillAI

@MainActor
struct PlanSetupViewModelTests {
    private let cal: Calendar = {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        return c
    }()
    private var now: Date { PlanCalendar.day(from: "2026-10-07", calendar: cal)! }

    private func make(_ mode: PlanSetupViewModel.Mode, service: FakeGenerationService = FakeGenerationService())
        -> (PlanSetupViewModel, FakeGenerationService, GenerationCenter, SessionStore) {
        let session = SessionStore(tokenStore: InMemoryTokenStore())
        let center = GenerationCenter(service: service, defaults: UserDefaults(suiteName: UUID().uuidString)!,
                                      makePoller: { JobPoller(service: $0, interval: .seconds(60), timeout: .seconds(120)) })
        let now = self.now
        let model = PlanSetupViewModel(mode: mode, user: nil, service: service, generation: center,
                                       session: session, now: { now }, calendar: cal)
        return (model, service, center, session)
    }

    @Test func goalTapAdvances() {
        let (model, _, _, _) = make(.onboarding)
        #expect(model.step == .goal)
        model.selectGoal(.startRunning)
        #expect(model.step == .schedule)
        #expect(model.steps == [.goal, .schedule, .aboutYou, .review])
        #expect(model.direction == .forward)
    }

    @Test func newPlanSkipsAboutYou() {
        let (model, _, _, _) = make(.newPlan)
        model.selectGoal(.race)
        #expect(model.steps == [.goal, .details, .schedule, .review])
    }

    @Test func nextStaysAndShowsIssuesWhenInvalid() {
        let (model, _, _, _) = make(.onboarding)
        model.selectGoal(.race)
        #expect(model.issues.isEmpty)          // nothing shown before trying
        model.next()
        #expect(model.step == .details)
        #expect(model.issue(for: .raceName) == "Add the race name.")
    }

    @Test func backGoesBackward() {
        let (model, _, _, _) = make(.onboarding)
        model.selectGoal(.startRunning)
        model.back()
        #expect(model.step == .goal)
        #expect(model.direction == .backward)
        model.back()
        #expect(model.stepIndex == 0)
    }

    @Test func daysPerWeekResetsDays() {
        let (model, _, _, _) = make(.onboarding)
        model.setDaysPerWeek(3)
        #expect(model.draft.preferredDays == [.tuesday, .thursday, .saturday])
        #expect(model.draft.preferredDays.contains(model.draft.longRunDay))
        model.toggleDay(.saturday)
        #expect(!model.draft.preferredDays.contains(.saturday))
    }

    @Test func submitOnboardingTracksJob() async {
        let (model, service, center, _) = make(.onboarding)
        model.selectGoal(.startRunning)
        await model.submit()
        #expect(service.calls.withLock { $0 }.first == "onboarding skip=false")
        #expect(center.running?.jobID == "job-1")
        #expect(center.running?.kind == .newPlan)
        #expect(model.didStart)
        center.cancelForTesting()
    }

    @Test func submitNewPlanUsesGeneratePlan() async {
        let (model, service, center, _) = make(.newPlan)
        model.selectGoal(.startRunning)
        await model.submit()
        #expect(service.calls.withLock { $0 }.first == "generate start_running")
        center.cancelForTesting()
    }

    @Test func submitErrorKeepsDraft() async {
        let service = FakeGenerationService()
        service.startResult.withLock { $0 = .failure(.http(status: 500, message: nil, code: nil)) }
        let (model, _, center, _) = make(.newPlan, service: service)
        model.selectGoal(.startRunning)
        await model.submit()
        #expect(model.submitError == "Something went wrong (500). Please try again.")
        #expect(model.draft.goal == .startRunning)
        #expect(!model.didStart)
        #expect(center.running == nil)
    }

    @Test func saveProfileOnlySetsUser() async throws {
        let user = try Fixture.decode(User.self, "auth_me.json")
        let service = FakeGenerationService()
        service.onboardingResult.withLock { $0 = .success(OnboardingResult(jobId: nil, user: user)) }
        let (model, _, center, session) = make(.onboarding, service: service)
        model.selectGoal(.startRunning)
        await model.saveProfileOnly()
        #expect(service.calls.withLock { $0 } == ["onboarding skip=true"])
        #expect(session.user == user)
        #expect(center.running == nil)
        #expect(model.didStart)
    }

    @Test func primaryTitle() {
        let (model, _, _, _) = make(.newPlan)
        model.selectGoal(.startRunning)
        #expect(model.primaryTitle == "Next")
        model.next()
        #expect(model.step == .review)
        #expect(model.primaryTitle == "Build my plan")
    }
}
```

- [ ] **Step 2: Run to verify failure**

Run: `ios-native/scripts/test.sh`
Expected: compile errors.

- [ ] **Step 3: Implement** `Features/Onboarding/PlanSetupViewModel.swift`

```swift
import Foundation
import Observation

@Observable
@MainActor
final class PlanSetupViewModel {
    enum Mode: Equatable { case onboarding, newPlan }
    enum Direction { case forward, backward }

    var draft: PlanSetupDraft
    private(set) var stepIndex = 0
    private(set) var direction: Direction = .forward
    private(set) var showIssues = false
    private(set) var isSubmitting = false
    private(set) var submitError: String?
    private(set) var didStart = false

    let mode: Mode
    private let service: any GenerationServicing
    private let generation: GenerationCenter
    private let session: SessionStore
    private let now: () -> Date
    private let calendar: Calendar

    init(mode: Mode, user: User?, service: any GenerationServicing, generation: GenerationCenter,
         session: SessionStore, now: @escaping () -> Date = { .now }, calendar: Calendar = PlanCalendar.calendar) {
        self.mode = mode
        self.service = service
        self.generation = generation
        self.session = session
        self.now = now
        self.calendar = calendar
        draft = PlanSetupDraft(prefill: user, today: now(), calendar: calendar)
    }

    var steps: [SetupStep] { SetupStep.steps(for: draft.goal, includeAboutYou: mode == .onboarding) }
    var step: SetupStep { steps[min(stepIndex, steps.count - 1)] }
    var progress: Double { Double(min(stepIndex, steps.count - 1) + 1) / Double(max(steps.count, 1)) }
    var isFirstStep: Bool { stepIndex == 0 }
    var isLastStep: Bool { step == .review }
    var primaryTitle: String { isLastStep ? "Build my plan" : "Next" }

    var issues: [SetupIssue] {
        showIssues ? draft.issues(for: step, today: now(), calendar: calendar) : []
    }

    func issue(for field: SetupField) -> String? {
        issues.first { $0.field == field }?.message
    }

    func selectGoal(_ goal: SetupGoal) {
        draft.goal = goal
        next()
    }

    func next() {
        guard draft.issues(for: step, today: now(), calendar: calendar).isEmpty else {
            showIssues = true
            return
        }
        showIssues = false
        direction = .forward
        stepIndex = min(stepIndex + 1, steps.count - 1)
    }

    func back() {
        showIssues = false
        direction = .backward
        stepIndex = max(stepIndex - 1, 0)
    }

    func setDaysPerWeek(_ n: Int) {
        let count = min(max(n, 3), 7)
        draft.daysPerWeek = count
        draft.preferredDays = PlanSetupDraft.defaultDays(count: count)
        if !draft.preferredDays.contains(draft.longRunDay) {
            draft.longRunDay = draft.preferredDays.contains(.saturday) ? .saturday : draft.orderedDays.last!
        }
    }

    func toggleDay(_ day: Weekday) {
        if draft.preferredDays.contains(day) { draft.preferredDays.remove(day) } else { draft.preferredDays.insert(day) }
    }

    func submit() async {
        guard !isSubmitting else { return }
        isSubmitting = true
        submitError = nil
        defer { isSubmitting = false }
        do {
            let jobID: String?
            switch mode {
            case .onboarding:
                jobID = try await service.completeOnboarding(draft.onboardingBody(skipPlan: false, calendar: calendar)).jobId
            case .newPlan:
                jobID = try await service.generatePlan(draft.planBody(calendar: calendar)).jobId
            }
            guard let jobID else {
                submitError = "We couldn't start building your plan. Please try again."
                return
            }
            generation.track(kind: .newPlan, jobID: jobID, summary: draft.summaryLines)
            didStart = true
        } catch let error as APIError {
            submitError = error.userMessage
        } catch {
            submitError = error.localizedDescription
        }
    }

    func saveProfileOnly() async {
        guard mode == .onboarding, !isSubmitting else { return }
        isSubmitting = true
        submitError = nil
        defer { isSubmitting = false }
        do {
            let result = try await service.completeOnboarding(draft.onboardingBody(skipPlan: true, calendar: calendar))
            if let user = result.user { session.setUser(user) }
            didStart = true
        } catch let error as APIError {
            submitError = error.userMessage
        } catch {
            submitError = error.localizedDescription
        }
    }
}
```

- [ ] **Step 4: Run tests**

Run: `ios-native/scripts/test.sh`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add ios-native
git commit -m "feat(ios): plan setup view model shared by onboarding and new plans"
```

---

### Task 5: Onboarding and new-plan screens

**Files:**
- Create: `ios-native/UphillAI/Features/Onboarding/WelcomeView.swift`, `PlanSetupFlow.swift`, `SetupSteps.swift`
- Modify: `ios-native/UphillAI/App/RootView.swift`, `ios-native/UphillAI/App/AppModel.swift`

**Interfaces:**
- Consumes: `PlanSetupViewModel` (Task 4); `AppModel.generation`, `generationService` (Task 3).
- Produces: `struct PlanSetupFlow` (`init(model: PlanSetupViewModel, onClose: () -> Void)`), `struct WelcomeView` (`init(onStart:onNotNow:)`); `AppModel.onboardingDeferred: Bool` (session-only) and `func makeSetup(mode:) -> PlanSetupViewModel`; `RootView` shows onboarding as a full-screen cover when the signed-in user has `onboardingComplete == false`, no job is running, and `onboardingDeferred` is false.

Screens:

**Welcome** (onboarding only): title "Let's build your training plan", body "Answer a few questions and Coach Uphill builds a plan around your goal, your week and how you feel today.", line "About 2 minutes", primary "Get started", text button "Not now" (sets `onboardingDeferred`, closes; the Plan tab empty state offers "Build my plan" later). No illustration asset in this phase; use the SF Symbol `mountain.2.fill` at 56 pt in `accent`.

**Flow container** (`PlanSetupFlow`):
- Top bar: back chevron (hidden on the first step; 44×44, label "Back"), a capsule progress bar (`progress`, accent on `line`, 4 pt tall, animated with `UH.Motion.standard`), a close button (`xmark`, label "Close") that dismisses without losing a running job.
- Content: the current step view inside a `ScrollView`, transitioned with `.asymmetric(insertion: .move(edge: forward ? .trailing : .leading).combined(with: .opacity), removal: .move(edge: forward ? .leading : .trailing).combined(with: .opacity))`; Reduce Motion → `.opacity`. Key the step view with `.id(model.step)` so SwiftUI transitions it.
- Bottom (`.safeAreaInset(edge: .bottom)`): `submitError` in `danger` caption when set; primary button with `model.primaryTitle` (`.uhPrimary`, disabled and showing `ProgressView` while submitting). The goal step has no primary button (tapping a goal advances). On the review step in onboarding mode, under the primary button: text button "Save my profile, build a plan later" → `saveProfileOnly()`.
- `.sensoryFeedback(.selection, trigger: model.stepIndex)`.
- When `model.didStart` becomes true, call `onClose()`: the root shows the generation screen (Task 6) for a running job.

**Steps** (`SetupSteps.swift`), each with a title (`screenTitle`) and a one-line subtitle (`secondary`):
1. **Goal** — "What are you training for?" Five large option rows (min height 64 pt) with `systemImage`, title and subtitle; selected row has `accentInk` 1.5 pt border and `activeFill` background. Tap = `selectGoal`.
2. **Details**, by goal:
   - race: "Tell us about your race". Fields: Race name (`TextField`, label above), Race date (`DatePicker`, `.compact`, range from today + 14 days), Distance (km, decimal pad), Elevation gain (m, number pad, optional, placeholder "Optional"), Terrain (segmented: Trail / Road / Mixed), Goal (three option rows from `RaceGoal`), Target time (shown only for `.time`: hours and minutes `Picker`s side by side, labelled "Target time", stored as `targetMinutes`).
   - distance: same without race name; title "Which distance?".
   - return: "How long have you been away?" option list from `timeAwayOptions`; "How do you feel right now?" from `fitnessFeelOptions`.
   - recovery: "Which race did you just finish?" from `raceDistanceOptions`; "Days since the race" stepper 0–60; "How does your body feel?" from `recoveryFeelOptions`.
3. **Schedule** — "Your training week". Runs per week stepper 3–7 (`setDaysPerWeek`); day chips Mon–Sun (44 pt, toggle, selected filled accent; VoiceOver "Tuesday, selected"); Long run day `Picker` limited to selected days; Current weekly distance (km, stepper by 5 plus text field); Where you train (segmented Flat / Hilly / Mixed); "I have gym access" toggle; Start date `DatePicker` from today.
4. **About you** (onboarding only) — "A bit about you". Subtitle "Optional. Helps set your heart rate zones; we estimate anything you skip." Fields: Birth date, Gender (menu: Female / Male / Other / Prefer not to say → nil), Height (cm), Weight (kg), Max heart rate, Resting heart rate, Injuries or niggles (multiline), Anything else your coach should know (multiline).
5. **Review** — "Ready to build your plan". The `summaryLines` as a list in a `uhCard`, each row tappable to jump back to its step (race line → details, schedule lines → schedule). Note under the card: "Coach Uphill builds your first weeks now and adds each new week as you train."

Every field shows its issue message under it in `danger` caption when `model.issue(for:)` returns one, and the first invalid field scrolls into view (`ScrollViewReader`, ids per field).

**Root routing:** in `RootView`'s signed-in branch, attach `.fullScreenCover(isPresented:)` bound to `app.needsOnboarding` (computed: `session.user?.onboardingComplete == false && generation.running == nil && !onboardingDeferred`). Its content: `WelcomeView` first, then `PlanSetupFlow` with `app.makeSetup(mode: .onboarding)`. Dismissing via Close sets `onboardingDeferred = true`.

- [ ] **Step 1: Implement the three files and the routing** as described. Keep each step view a small `struct` in `SetupSteps.swift` taking `@Bindable var model: PlanSetupViewModel`.

- [ ] **Step 2: Build and run tests**

Run: `ios-native/scripts/test.sh`
Expected: all pass.

- [ ] **Step 3: Screenshots**

Register a fresh account against the local backend so onboarding opens. Capture into `ios-native/docs/screenshots/phase2/`:
`welcome.png`, `step-goal.png`, `step-race-details.png` (with Target time showing), `step-race-details-errors.png` (tap Next with empty fields), `step-return.png`, `step-schedule.png`, `step-about-you.png`, `step-review.png`, and `step-schedule-large-text.png` at `extra-extra-extra-large` Dynamic Type. Record a short screen recording of going forward and back (`xcrun simctl io booted recordVideo ios-native/docs/screenshots/phase2/step-transitions.mov`, stop with Ctrl-C) to show the direction-matched transitions. Look at each one: no clipped text, no field hidden behind the keyboard or the bottom button.

- [ ] **Step 4: Commit**

```bash
git add ios-native
git commit -m "feat(ios): onboarding and new-plan setup screens"
```

---

### Task 6: Generation progress screen and empty-state entry points

**Files:**
- Create: `ios-native/UphillAI/Features/Onboarding/GenerationProgressView.swift`
- Modify: `ios-native/UphillAI/App/RootView.swift`, `ios-native/UphillAI/Features/Plan/PlanView.swift`, `ios-native/UphillAI/Features/Plan/ManagePlanSheet.swift`

**Interfaces:**
- Consumes: `GenerationCenter` (Task 3), `PlanSetupFlow` (Task 5), `PlanViewModel`.
- Produces: `struct GenerationProgressView` (`init(generation: GenerationCenter, onShowPlan: () -> Void, onLeave: () -> Void, onEditAnswers: () -> Void)`); Plan tab empty state with "Build my plan"; Manage sheet "Start new plan".

Generation screen (presented full screen over the tabs while `generation.running?.kind == .newPlan`, or while `lastOutcome` for `.newPlan` is not yet cleared):
- **Running**: title "Building your plan"; body "This usually takes under a minute. You can leave this screen; we'll keep working."; an indeterminate `ProgressView` plus elapsed time from `startedAt` in a `TimelineView(.periodic(from: .now, by: 1))` formatted "0:23"; a card titled "Your plan is built around" listing `running.summary` with a `checkmark` icon per line (these are the inputs the athlete gave, not progress steps). Button "Keep using the app" (secondary) → `onLeave`.
  - After 90 s of running, add the line "Still working. Plans with a race far away take longer." (honest, time-based, no fake percentage).
- **Done**: a `checkmark.circle.fill` (64 pt, accent) that scales from 0.6 to 1 with `UH.Motion.standard` (Reduce Motion: opacity only), title "Your plan is ready", primary "See my plan" → `onShowPlan` (clears the outcome, switches to the Plan tab, which already holds the adopted plan). `.sensoryFeedback(.success, trigger:)` on the outcome.
- **Failed(message)**: title "We couldn't build your plan", the message, primary "Try again" (re-submits by reopening `PlanSetupFlow` on the review step with the same answers), secondary "Edit answers" → `onEditAnswers`. `.sensoryFeedback(.error, …)`.
- **Lost**: treat as done if the reload found an active plan, else as failed with "We lost track of your plan while the server restarted. Check the Plan tab; if nothing is there, try again."

To support "Try again" with the same answers, keep the last `PlanSetupViewModel` in `AppModel` (`private(set) var lastSetup: PlanSetupViewModel?`, set by `makeSetup`) and add `func reopenAtReview()` on the view model that sets `stepIndex` to the review step and `didStart = false`.

Plan tab empty state (Phase 1 shows a web pointer; replace it): `mountain.2` symbol, title "No plan yet", body "Your weekly workouts show up here once Coach Uphill builds your plan.", primary "Build my plan" → opens `PlanSetupFlow` (`.onboarding` if the user hasn't completed onboarding, else `.newPlan`).

Manage sheet: add a section "New plan" with "Start new plan" → confirmation dialog "Start a new plan?" message "Your current plan stays in Recent plans. The new plan becomes your active plan." buttons "Start new plan" / "Cancel" → `PlanSetupFlow(.newPlan)`. Remove "new plans" from the Phase 1 footer note.

If a `.newPlan` job is running when the athlete opens the Plan tab, show a slim banner at the top: "Building your plan… 0:41" with "View" → the generation screen.

- [ ] **Step 1: Implement** the view and the entry points above.

- [ ] **Step 2: Build and run tests**

Run: `ios-native/scripts/test.sh`
Expected: all pass.

- [ ] **Step 3: Screenshots**

The local backend without `GEMINI_API_KEY` runs the coach in mock mode; to see the running state long enough, take the screenshot right after submitting. Capture: `generation-running.png`, `generation-running-90s.png` (wait 90 s if generation is that slow; otherwise skip this one and say so in the report), `generation-done.png`, `plan-after-onboarding.png`, `plan-empty-build.png`, `manage-start-new.png`, `plan-building-banner.png` (tap "Keep using the app" during a run). For the failed state, stop the backend container while it runs and wait for the offline message: `generation-failed.png`. Restart the backend.

Kill and relaunch the app while a plan is generating: the banner (or the generation screen) must come back and finish (the job id was persisted). Note the result in the report.

- [ ] **Step 4: Commit**

```bash
git add ios-native
git commit -m "feat(ios): generation progress screen and Build my plan entry points"
```

---

### Task 7: Review, completion and goal models plus fixtures

**Files:**
- Create: `ios-native/UphillAI/Core/Plan/ReviewModels.swift`
- Modify: `ios-native/UphillAI/Core/Plan/PlanService.swift`, `ios-native/UphillAITests/Support/FakePlanService.swift`, `ios-native/scripts/record_fixtures.sh`
- Recorded: `ios-native/UphillAITests/Fixtures/block_completion.json`, `week_review.json`, `plan_goal.json`
- Test: `ios-native/UphillAITests/Plan/ReviewModelsTests.swift`

**Interfaces:**
- Produces:
  - `struct BlockCompletion: Decodable, Sendable, Equatable { let blockNumber: Int; let weekStart: Int; let weekEnd: Int; let completionPct: Double; let unlocked: Bool }`
  - `struct BlockCompletionResponse: Decodable, Sendable { let blocks: [BlockCompletion]; let maxGeneratedWeek: Int }`
  - `struct WeekReview: Decodable, Sendable { let weekNumber: Int; let completionPct: Double; let checkboxCompletionPct: Double?; let perWorkout: [WeekReviewEntry]; let narrative: WeekNarrative? }`
  - `struct WeekReviewEntry: Decodable, Sendable, Identifiable { let workoutId: Int; let dayOfWeek: String?; let title: String?; let type: String?; let actual: Actual; var id: Int }` with `struct Actual: Decodable, Sendable { let state: String; let distanceKm: Double?; let durationMinutes: Double? }`
  - `struct WeekNarrative: Decodable, Sendable { let summary: String?; let highlights: [String]; let watch: [String] }` (missing arrays decode as empty)
  - `struct PlanGoal: Decodable, Sendable, Equatable { let assessment: GoalAssessment?; let status: GoalStatus; let targetTimeHours: Double? }`
  - `struct GoalStatus: Decodable, Sendable, Equatable { let state: String; let suggestedMins: Double? }` with `enum State { onTrack, ahead, behind, noTarget, notAssessed }` via `var kind`
  - `struct GoalAssessment: Decodable, Sendable, Equatable { let id: Int; let goals: GoalTiers?; let confidence: String?; let reasoning: [String]; let missing: [String]; let engine: String?; let createdAt: String? }`, `struct GoalTiers: Decodable, Sendable, Equatable { let a: Double; let b: Double; let c: Double }` (minutes)
  - `PlanServicing` gains `blockCompletion(planID:) async throws -> BlockCompletionResponse`, `weekReview(planID:week:) async throws -> WeekReview`, `goal(planID:) async throws -> PlanGoal`, `reassessGoal(planID:) async throws -> PlanGoal`, `applyGoal(planID:targetMinutes:) async throws -> PlanGoal`

- [ ] **Step 1: Extend the fixture script**

Append to `record_fixtures.sh`, in the preview-athlete section (after `recent_plans.json`):

```bash
PLAN_ID=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["plan"]["id"])' "$OUT/active_plan.json")
get "/api/coach/block-completion/$PLAN_ID" block_completion.json
get "/api/coach/week-review/$PLAN_ID/1" week_review.json
# Creates one assessment (rules tier unless GOAL_LLM_ENABLED). Limited per day on the server.
curl -sf -X POST "$BASE/api/plans/$PLAN_ID/goal/reassess" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"exclude":[],"lang":"en"}' >/dev/null || true
get "/api/plans/$PLAN_ID/goal" plan_goal.json
```

Re-seed (`backend/scripts/seed_ios_preview.py`) and run `ios-native/scripts/record_fixtures.sh`. Check `plan_goal.json` has a non-null `assessment` with `goals`; if the reassess was rate-limited, wait or reseed a fresh preview athlete.

- [ ] **Step 2: Write the failing tests** `ReviewModelsTests.swift`

```swift
import Foundation
import Testing
@testable import UphillAI

struct ReviewModelsTests {
    @Test func decodesBlockCompletion() throws {
        let r = try Fixture.decode(BlockCompletionResponse.self, "block_completion.json")
        #expect(r.maxGeneratedWeek >= 1)
        #expect(!r.blocks.isEmpty)
        #expect(r.blocks.allSatisfy { $0.weekStart <= $0.weekEnd })
    }

    @Test func decodesWeekReview() throws {
        let r = try Fixture.decode(WeekReview.self, "week_review.json")
        #expect(r.weekNumber == 1)
        #expect(!r.perWorkout.isEmpty)
    }

    @Test func decodesPlanGoal() throws {
        let g = try Fixture.decode(PlanGoal.self, "plan_goal.json")
        #expect(g.assessment?.goals != nil)
        #expect(["on_track", "ahead", "behind", "no_target", "not_assessed"].contains(g.status.state))
    }

    @Test func goalStatusKinds() throws {
        func status(_ s: String) throws -> GoalStatus {
            try JSONCoding.decoder.decode(GoalStatus.self, from: json(["state": s, "suggested_mins": 380]))
        }
        #expect(try status("on_track").kind == .onTrack)
        #expect(try status("behind").kind == .behind)
        #expect(try status("weird").kind == .notAssessed)
    }

    @Test func narrativeToleratesMissingArrays() throws {
        let n = try JSONCoding.decoder.decode(WeekNarrative.self, from: json(["summary": "Solid week."]))
        #expect(n.highlights.isEmpty)
        #expect(n.watch.isEmpty)
    }
}
```

- [ ] **Step 3: Run to verify failure**

Run: `ios-native/scripts/test.sh`
Expected: compile errors.

- [ ] **Step 4: Implement** `ReviewModels.swift` with the structs listed under Interfaces. Use `decodeIfPresent(...) ?? []` for `highlights`, `watch`, `reasoning` and `missing`, and map `GoalStatus.kind` from `state` (`"on_track"` → `.onTrack`, `"ahead"`, `"behind"`, `"no_target"` → `.noTarget`, anything else → `.notAssessed`). If the recorded `plan_goal.json` shows `reasoning` items as objects rather than strings, or `confidence` as a number, change the Swift type to match (e.g. `reasoning: [ReasoningItem]` with the fields present) and adapt the Goal sheet in Task 10 accordingly.

- [ ] **Step 5: Add the service calls** to `PlanService` and `FakePlanService`

```swift
    func blockCompletion(planID: Int) async throws -> BlockCompletionResponse {
        try await client.send(.get("/api/coach/block-completion/\(planID)"))
    }

    func weekReview(planID: Int, week: Int) async throws -> WeekReview {
        try await client.send(.get("/api/coach/week-review/\(planID)/\(week)"))
    }

    func goal(planID: Int) async throws -> PlanGoal {
        try await client.send(.get("/api/plans/\(planID)/goal", query: [URLQueryItem(name: "lang", value: "en")]))
    }

    func reassessGoal(planID: Int) async throws -> PlanGoal {
        struct Body: Encodable { let exclude: [String]; let lang: String }
        return try await client.send(.send(.post, "/api/plans/\(planID)/goal/reassess", body: Body(exclude: [], lang: "en")))
    }

    func applyGoal(planID: Int, targetMinutes: Double) async throws -> PlanGoal {
        struct Body: Encodable { let targetMins: Double }
        return try await client.send(.send(.post, "/api/plans/\(planID)/goal/apply", body: Body(targetMins: targetMinutes)))
    }
```

In `FakePlanService`, add `Mutex<Result<…, APIError>>` properties `completionResult`, `reviewResult`, `goalResult` (default `.failure(.http(status: 404, message: nil, code: nil))`), and record calls as `"completion \(id)"`, `"review \(id) w\(week)"`, `"goal \(id)"`, `"reassess \(id)"`, `"apply \(id) \(Int(minutes))"`. `reassessGoal` and `applyGoal` return `goalResult`.

- [ ] **Step 6: Run tests**

Run: `ios-native/scripts/test.sh`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add ios-native
git commit -m "feat(ios): block completion, week review and goal models with recorded fixtures"
```

---

### Task 8: Build the next week

**Files:**
- Create: `ios-native/UphillAI/Features/Plan/NextWeekSheet.swift`
- Modify: `ios-native/UphillAI/Features/Plan/PlanViewModel.swift`, `ios-native/UphillAI/Features/Plan/PlanView.swift`
- Test: add to `ios-native/UphillAITests/Plan/PlanViewModelTests.swift`

**Interfaces:**
- Consumes: `BlockCompletionResponse` (Task 7), `GenerationServicing`, `GenerationCenter` (Tasks 1, 3).
- Produces:
  - `struct NextWeekOffer: Equatable { let blockNumber: Int; let weekStart: Int; let weekEnd: Int; let previousCompletionPct: Double?; let unlocked: Bool; var title: String }` (`title` = "Build week \(weekStart)" or "Build weeks \(weekStart)–\(weekEnd)")
  - `PlanViewModel.nextWeekOffer: NextWeekOffer?` and `func refreshNextWeekOffer() async`
  - `PlanViewModel` init gains `generation: GenerationCenter?` and `generationService: (any GenerationServicing)?` (default nil, so Phase 1 tests compile unchanged); `AppModel` passes both
  - `func buildNextWeek(rpe: Int?, notes: String, override: Bool) async -> NextWeekResult` with `enum NextWeekResult: Equatable { case started, needsConfirmation(String), failed(String) }`

Rules:
1. The offer exists when the plan has fewer generated weeks than `total_weeks` and the selected week is the last generated week. Next block number = last block's `block_number + 1`; `weekStart = maxGeneratedWeek + 1`; `weekEnd = min(weekStart + (lastBlock.weekEnd - lastBlock.weekStart), total_weeks)`. `previousCompletionPct`/`unlocked` come from the last block.
2. `buildNextWeek` with `override: false` and a 403 → `.needsConfirmation(server message)`; the sheet asks and retries with `override: true`.
3. 400 → `.failed(message)` and clear the offer (everything already generated).
4. On a job id: `generation.track(kind: .nextWeek, jobID:, summary: [])` → `.started`.
5. Offline (`cachedAt != nil`) → `.failed(offlineMessage)` without calling the service.

- [ ] **Step 1: Write the failing tests** (append to `PlanViewModelTests`)

```swift
    private func completion(_ pct: Double, unlocked: Bool, maxWeek: Int = 3) -> BlockCompletionResponse {
        try! JSONCoding.decoder.decode(BlockCompletionResponse.self, from: json([
            "plan_id": 7, "max_generated_week": maxWeek,
            "blocks": (1...maxWeek).map { ["block_number": $0, "week_start": $0, "week_end": $0,
                                           "completion_pct": $0 == maxWeek ? pct : 100, "unlocked": $0 == maxWeek ? unlocked : true] },
        ]))
    }

    private func makeWithGeneration(_ service: FakePlanService, gen: FakeGenerationService) -> (PlanViewModel, GenerationCenter) {
        let center = GenerationCenter(service: gen, defaults: UserDefaults(suiteName: UUID().uuidString)!,
                                      makePoller: { JobPoller(service: $0, interval: .seconds(60), timeout: .seconds(120)) })
        let now = self.now
        return (PlanViewModel(service: service, cache: .inMemory(), now: { now }, calendar: cal,
                              generation: center, generationService: gen), center)
    }

    @Test func offerAppearsOnLastGeneratedWeek() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }       // weeks 1–3 generated, 12 total
        service.completionResult.withLock { $0 = .success(completion(80, unlocked: true)) }
        let (model, _) = makeWithGeneration(service, gen: FakeGenerationService())
        await model.load()
        model.selectedWeek = 3
        await model.refreshNextWeekOffer()
        #expect(model.nextWeekOffer == NextWeekOffer(blockNumber: 4, weekStart: 4, weekEnd: 4, previousCompletionPct: 80, unlocked: true))
        #expect(model.nextWeekOffer?.title == "Build week 4")
        model.selectedWeek = 2
        await model.refreshNextWeekOffer()
        #expect(model.nextWeekOffer == nil)
    }

    @Test func gateNeedsConfirmationThenOverride() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        service.completionResult.withLock { $0 = .success(completion(40, unlocked: false)) }
        let gen = FakeGenerationService()
        gen.startResult.withLock { $0 = .failure(.http(status: 403, message: "Block 3 is 40% complete. Need ≥70% to unlock the next block.", code: nil)) }
        let (model, center) = makeWithGeneration(service, gen: gen)
        await model.load()
        model.selectedWeek = 3
        await model.refreshNextWeekOffer()
        let first = await model.buildNextWeek(rpe: 6, notes: "", override: false)
        #expect(first == .needsConfirmation("Block 3 is 40% complete. Need ≥70% to unlock the next block."))
        gen.startResult.withLock { $0 = .success(JobStart(jobId: "nb")) }
        #expect(await model.buildNextWeek(rpe: 6, notes: "", override: true) == .started)
        #expect(gen.calls.withLock { $0 } == ["next 4 override=false", "next 4 override=true"])
        #expect(center.running?.kind == .nextWeek)
        center.cancelForTesting()
    }
```

- [ ] **Step 2: Run to verify failure**

Run: `ios-native/scripts/test.sh`
Expected: compile errors.

- [ ] **Step 3: Implement** `NextWeekOffer`, `refreshNextWeekOffer` and `buildNextWeek` in `PlanViewModel` following the rules. `NextWeekOffer.==` compares the stored properties only (`title` is computed). Call `refreshNextWeekOffer()` at the end of a successful `load()`/`adopt` and from `PlanView` on `.onChange(of: selectedWeek)`.

- [ ] **Step 4: Implement** `NextWeekSheet.swift` and the card

- Card (in the day list, after Sunday, only when `nextWeekOffer != nil`): title `offer.title`, body "Coach Uphill uses how this week went to shape the next one.", completion line "This week: 80 % done" when `previousCompletionPct` is set, primary button `offer.title` → sheet. While a `.nextWeek` job runs, the card shows `ProgressView` and "Building week 4…" instead.
- Sheet (detents `.medium`, `.large`): title "How did this week go?", RPE stepper "Effort (RPE)" 1–10 with "Not set", notes field "Anything Coach Uphill should know?", primary `offer.title`. `.needsConfirmation(message)` → `.confirmationDialog` titled "Build the next week anyway?" with the server message and buttons "Build anyway" (`override: true`) / "Not yet". `.failed(message)` → message in `danger` under the button. `.started` → dismiss.
- When the job finishes, `GenerationCenter.onFinished` adopts the plan (Task 3); add a toast-style banner "Week 4 is ready" for 3 s and play `.success`.

- [ ] **Step 5: Run tests, screenshot, commit**

Run: `ios-native/scripts/test.sh`. With the preview athlete (weeks 1–3 generated), select week 3 and capture `next-week-card.png`, `next-week-sheet.png`, `next-week-confirm.png` (week 3 is under 70 %, so the gate fires), `next-week-building.png`, `next-week-ready.png`.

```bash
git add ios-native
git commit -m "feat(ios): build the next week with review and completion gate"
```

---

### Task 9: Adapt this week and the weekly review

**Files:**
- Create: `ios-native/UphillAI/Features/Plan/AdaptWeekSheet.swift`, `ios-native/UphillAI/Features/Plan/WeekReviewSheet.swift`
- Modify: `ios-native/UphillAI/Features/Plan/PlanViewModel.swift`, `ios-native/UphillAI/Features/Plan/SummaryCarousel.swift`, `ios-native/UphillAI/Features/Plan/PlanView.swift`
- Test: add to `PlanViewModelTests.swift`

**Interfaces:**
- Produces:
  - `enum FatigueLevel: String, CaseIterable { case easy, medium, hard, exhausted }` with titles "Fresh", "Normal tiredness", "Heavy legs", "Exhausted" and subtitles "Ready for more", "About what I expected", "Struggling to hit the paces", "I need a lighter week"
  - `PlanViewModel.canAdapt(week:) -> Bool` (week ≥ current week and ≤ last generated week)
  - `func adaptWeek(_ week: Int, fatigue: FatigueLevel, rpe: Int?, notes: String) async -> String?` (returns an error message, nil on start; tracks `.adaptWeek`)
  - `func weekReview(_ week: Int) async -> Result<WeekReview, APIError>`

- [ ] **Step 1: Write the failing tests**

```swift
    @Test func adaptSendsFatigueAndClientToday() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        let gen = FakeGenerationService()
        gen.startResult.withLock { $0 = .success(JobStart(jobId: "ad")) }
        let (model, center) = makeWithGeneration(service, gen: gen)
        await model.load()
        #expect(model.canAdapt(week: 2))
        #expect(!model.canAdapt(week: 1))      // past week
        #expect(!model.canAdapt(week: 4))      // not generated
        let error = await model.adaptWeek(2, fatigue: .hard, rpe: 8, notes: "Bad sleep")
        #expect(error == nil)
        #expect(gen.calls.withLock { $0 } == ["adapt 2 hard"])
        #expect(center.running?.kind == .adaptWeek)
        center.cancelForTesting()
    }

    @Test func adaptBlockedOffline() async {
        let cache = OfflineCache.inMemory()
        cache.save(snapshot(), as: .plan)
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .failure(.transport("offline")) }
        let gen = FakeGenerationService()
        let center = GenerationCenter(service: gen, defaults: UserDefaults(suiteName: UUID().uuidString)!)
        let now = self.now
        let model = PlanViewModel(service: service, cache: cache, now: { now }, calendar: cal, generation: center, generationService: gen)
        await model.load()
        #expect(await model.adaptWeek(2, fatigue: .easy, rpe: nil, notes: "") == PlanViewModel.offlineMessage)
        #expect(gen.calls.withLock { $0 }.isEmpty)
    }
```

The service body carries `client_today` (`PlanCalendar.ymd(now())`) and `lang: "en"`; `FakeGenerationService` records only week and fatigue, so also assert the body once in `JobPollerTests.serviceHitsRealPaths` style if you change the fake.

- [ ] **Step 2: Run to verify failure, implement, run again**

Implement `canAdapt`, `adaptWeek` and `weekReview` in `PlanViewModel`.

- [ ] **Step 3: Implement the sheets and entry points**

- This-week carousel card (Phase 1): add two buttons under the dots, both 44 pt: "Review week" (any week with workouts) and "Adapt this week" (only when `canAdapt(week: selectedWeek)`).
- **Adapt sheet**: title "Adapt week \(n)", subtitle "Coach Uphill rebuilds the workouts you haven't done yet. Finished and synced workouts stay as they are."; fatigue options as four rows (title + subtitle, single choice, default `.medium`); RPE stepper (optional); notes "What's going on?"; primary "Adapt week \(n)". While the `.adaptWeek` job runs: the sheet closes and the This-week card shows "Adapting week \(n)…" with `ProgressView`. On done: banner "Week \(n) updated", `.success`. On failure: banner with the message and "Try again".
- **Review sheet** (detents `.medium`, `.large`): title "Week \(n) review"; a completion ring (`Gauge` with `.accessoryCircularCapacity` style, tinted `accent`) showing `checkboxCompletionPct ?? completionPct` with the label "sessions done"; `narrative.summary` as body; "Went well" list from `highlights` (`checkmark` icon), "Keep an eye on" list from `watch` (`exclamationmark.triangle` icon, `secondary` colour); then each `perWorkout` entry with day, title and a state label: `matched` "Synced", `checkbox_only` "Done", `missed` "Missed", `pending` "Not yet". Loading: skeleton rows (redacted placeholders, `.redacted(reason: .placeholder)`). Error: message + "Try again".

- [ ] **Step 4: Run tests, screenshots, commit**

Run: `ios-native/scripts/test.sh`. Capture `adapt-sheet.png`, `adapt-running.png`, `adapt-done.png`, `review-week1.png`, `review-loading.png`.

```bash
git add ios-native
git commit -m "feat(ios): adapt this week and weekly review sheets"
```

---

### Task 10: Goal pill and goal sheet

**Files:**
- Create: `ios-native/UphillAI/Features/Plan/GoalSheet.swift`
- Modify: `ios-native/UphillAI/Features/Plan/PlanViewModel.swift`, `ios-native/UphillAI/Features/Plan/SummaryCarousel.swift`
- Test: add to `PlanViewModelTests.swift`

**Interfaces:**
- Produces: `PlanViewModel.goal: PlanGoal?`, `func loadGoal() async`, `func reassessGoal() async -> String?`, `func applySuggestedGoal() async -> String?`, `static func formatMinutes(_ minutes: Double) -> String` ("6:25" for 385), `var goalPillText: String?`

Pill text by state (exact): `on_track` "On track", `ahead` "Ahead of target", `behind` "Behind target", `no_target` "Suggested \(formatMinutes(suggested))", `not_assessed` "Not assessed yet". Only event plans (with a course distance) show the pill.

Error mapping for reassess: 429 → "You've used today's goal checks. Try again tomorrow."; others → `userMessage`.

- [ ] **Step 1: Write the failing tests**

```swift
    @Test func goalPillTextAndApply() async throws {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        let behind = try JSONCoding.decoder.decode(PlanGoal.self, from: json([
            "assessment": ["id": 1, "goals": ["a": 360, "b": 385, "c": 410], "reasoning": [], "missing": [], "engine": "rules"],
            "status": ["state": "behind", "suggested_mins": 385], "target_time_hours": 6.0,
        ]))
        service.goalResult.withLock { $0 = .success(behind) }
        let model = make(service)
        await model.load()
        await model.loadGoal()
        #expect(model.goalPillText == "Behind target")
        #expect(PlanViewModel.formatMinutes(385) == "6:25")
        _ = await model.applySuggestedGoal()
        #expect(service.calls.withLock { $0 }.last == "apply 7 385")
    }

    @Test func reassessRateLimitMessage() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        service.goalResult.withLock { $0 = .failure(.http(status: 429, message: "limit", code: nil)) }
        let model = make(service)
        await model.load()
        #expect(await model.reassessGoal() == "You've used today's goal checks. Try again tomorrow.")
    }
```

- [ ] **Step 2: Run to verify failure, implement, run again**

`applySuggestedGoal` sends `status.suggestedMins` (or `assessment.goals.b`) and replaces `goal` with the response; it also updates `snapshot.plan`'s target by reloading the plan (`await load()`), since `target_time_hours` lives on the plan. Call `loadGoal()` after load/adopt for event plans.

- [ ] **Step 3: Implement the pill and sheet**

- Race card (Phase 1): replace the plain `goalText` line with a capsule pill (`label` font, 32 pt min height, `hover` background; `behind` uses `danger` text, `ahead` and `on_track` use `accentInk`). The pill is a `Button` → Goal sheet.
- **Goal sheet** (detents `.medium`, `.large`): title "Your goal for \(race)"; three tier rows "Stretch" (a), "Realistic" (b, emphasised), "Safe" (c), each with `formatMinutes`; current target line "Your target: 6:00" (or "No target set"); the reasoning bullets and "We'd know more with: …" from `missing`; primary "Set 6:25 as my target" when a suggestion differs from the target → confirmation dialog "Change your target time to 6:25?" message "Your training paces won't change until your next week is built." buttons "Change target" / "Keep 6:00"; secondary "Check again" → `reassessGoal()` with the busy state; footer caption with the engine and date ("Estimated from your race history · 7 Oct").

- [ ] **Step 4: Run tests, screenshots, commit**

Run: `ios-native/scripts/test.sh`. Capture `goal-pill.png`, `goal-sheet.png`, `goal-confirm.png`, `goal-rate-limited.png` (call "Check again" until the server limits it, or skip with a note).

```bash
git add ios-native
git commit -m "feat(ios): Goal pill and goal sheet"
```

---

### Task 11: End-to-end onboarding test and accessibility pass

**Files:**
- Create: `ios-native/UphillAIUITests/OnboardingFlowUITests.swift`
- Modify: views from Tasks 5–6 (accessibility identifiers only), `ios-native/README.md`

**Interfaces:**
- Consumes: every screen above; the `UphillAI-E2E` scheme and `scripts/e2e.sh` from Phase 1.

- [ ] **Step 1: Add identifiers**: welcome `welcome.start`; goal rows `goal.\(goal.rawValue)`; primary button `setup.primary`; generation screen `generation.running`, `generation.done`, `generation.showPlan`; Plan empty state button `plan.build`.

- [ ] **Step 2: Write** `OnboardingFlowUITests.swift`

```swift
import XCTest

/// Fresh account → onboarding → generated plan, against the LOCAL backend.
/// The local backend without GEMINI_API_KEY uses its mock/rules engine, so this finishes quickly.
final class OnboardingFlowUITests: XCTestCase {
    override func setUp() { continueAfterFailure = false }

    @MainActor
    func testNewAthleteGetsAPlan() {
        let app = XCUIApplication()
        app.launchArguments = ["-UPHILL_ENVIRONMENT", "local"]
        app.launch()

        // Register a unique account.
        let email = "ios-e2e-\(Int(Date().timeIntervalSince1970))@uphill.ai"
        app.buttons["New to Uphill? Create an account"].tap()
        let name = app.textFields["Name"]
        XCTAssertTrue(name.waitForExistence(timeout: 10))
        name.tap(); name.typeText("E2E Runner")
        let emailField = app.textFields["signin.email"]
        emailField.tap(); emailField.typeText(email)
        let password = app.secureTextFields["signin.password"]
        password.tap(); password.typeText("uphill-e2e-pass-1")
        app.buttons["signin.submit"].tap()

        XCTAssertTrue(app.buttons["welcome.start"].waitForExistence(timeout: 15))
        app.buttons["welcome.start"].tap()
        app.buttons["goal.start_running"].tap()      // schedule step next
        app.buttons["setup.primary"].tap()           // schedule (defaults are valid)
        app.buttons["setup.primary"].tap()           // about you (optional)
        XCTAssertEqual(app.buttons["setup.primary"].label, "Build my plan")
        app.buttons["setup.primary"].tap()

        XCTAssertTrue(app.otherElements["generation.running"].waitForExistence(timeout: 10)
                      || app.otherElements["generation.done"].waitForExistence(timeout: 1))
        XCTAssertTrue(app.buttons["generation.showPlan"].waitForExistence(timeout: 240))
        app.buttons["generation.showPlan"].tap()
        XCTAssertTrue(app.descendants(matching: .any)["day.today"].waitForExistence(timeout: 15)
                      || app.staticTexts["Week 1"].waitForExistence(timeout: 5))
    }
}
```

Adjust queries to the identifiers and labels that actually exist (for example the "Name" field may need its own identifier `signin.name`; add it).

- [ ] **Step 3: Accessibility pass**

With VoiceOver labels via the Accessibility Inspector, check: every step's options read as "Title, subtitle, selected/not selected"; the progress bar reads "Step 2 of 5"; the generation screen announces "Building your plan" when it appears (`.accessibilityAddTraits(.isHeader)` on the title) and "Your plan is ready" on completion (`AccessibilityNotification.Announcement`). Run the whole flow at `extra-extra-extra-large` text: nothing clipped, the primary button stays reachable. Fix what fails. Note the results in the report.

- [ ] **Step 4: Run everything**

Run: `ios-native/scripts/test.sh && ios-native/scripts/e2e.sh`
Expected: both succeed.

- [ ] **Step 5: README** — under the E2E section add: "OnboardingFlowUITests registers a new `ios-e2e-<timestamp>@uphill.ai` account on each run (local database only)."

- [ ] **Step 6: Commit**

```bash
git add ios-native
git commit -m "test(ios): end-to-end onboarding to generated plan; accessibility fixes"
```

---

## Phase 2 done when

- `ios-native/scripts/test.sh` and `ios-native/scripts/e2e.sh` pass.
- `ios-native/docs/screenshots/phase2/` holds every screenshot named in Tasks 5, 6 and 8–10, plus the step-transition recording.
- Relaunching during generation resumes the job (Task 6 note in the report).
- The PR description lists anything adapted from this plan to match merged Phase 0/1 code, and states "No backend, prompt or schema changes."
