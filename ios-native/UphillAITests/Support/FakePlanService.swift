import Foundation
import Synchronization
@testable import UphillAI

/// Scriptable PlanServicing. Set the results before use; read `calls` after.
final class FakePlanService: PlanServicing {
    let beforeGoalReturn = Mutex<(@Sendable () async -> Void)?>(nil)
    let beforeActiveReturn = Mutex<(@Sendable () async -> Void)?>(nil)
    let activeResult = Mutex<Result<PlanSnapshot?, APIError>>(.success(nil))
    let logResult = Mutex<Result<[Workout], APIError>>(.success([]))
    let moveWarnings = Mutex<[ScheduleWarning]>([])
    let moveResult = Mutex<Result<[Workout], APIError>>(.success([]))
    let swapWarnings = Mutex<[ScheduleWarning]>([])
    let swapResult = Mutex<Result<[Workout], APIError>>(.success([]))
    let deleteResult = Mutex<Result<Void, APIError>>(.success(()))
    let recentResult = Mutex<Result<[Plan], APIError>>(.success([]))
    let selectResult = Mutex<Result<PlanSnapshot?, APIError>>(.success(nil))
    let completionResult = Mutex<Result<BlockCompletionResponse, APIError>>(.failure(.http(status: 404, message: nil, code: nil)))
    let reviewResult = Mutex<Result<WeekReview, APIError>>(.failure(.http(status: 404, message: nil, code: nil)))
    let goalResult = Mutex<Result<PlanGoal, APIError>>(.failure(.http(status: 404, message: nil, code: nil)))
    let syncWatchResult = Mutex<Result<String, APIError>>(.success("Watch synced · Up to date"))
    let watchActivitiesResult = Mutex<Result<[WatchActivity], APIError>>(.success([]))
    let evaluationResult = Mutex<Result<BlockEvaluation, APIError>>(.failure(.http(status: 404, message: nil, code: nil)))
    let milestoneResult = Mutex<Result<PlanMilestones, APIError>>(.failure(.http(status: 404, message: nil, code: nil)))
    let assessResult = Mutex<Result<BRaceAssessment, APIError>>(.failure(.http(status: 404, message: nil, code: nil)))
    let raceChangeResult = Mutex<Result<BRaceChange, APIError>>(.failure(.http(status: 404, message: nil, code: nil)))
    let debriefResult = Mutex<Result<BRaceDebriefResult, APIError>>(.failure(.http(status: 404, message: nil, code: nil)))
    let calls = Mutex<[String]>([])

    private func record(_ call: String) { calls.withLock { $0.append(call) } }

    func activePlan() async throws -> PlanSnapshot? {
        record("active")
        let result = activeResult.withLock { $0 }
        if let wait = beforeActiveReturn.withLock({ $0 }) { await wait() }
        return try result.get()
    }

    func log(workoutID: Int, _ update: WorkoutLogUpdate) async throws -> [Workout] {
        record("log \(workoutID) done=\(update.isCompleted.map(String.init) ?? "-") missed=\(update.isMissed.map(String.init) ?? "-") rpe=\(update.rpe.map(String.init) ?? "-")")
        return try logResult.withLock { $0 }.get()
    }

    func move(planID: Int, workoutID: Int, toWeek: Int, toDay: Weekday, clientToday: String) async throws -> CalendarMoveResult {
        record("move \(workoutID) -> w\(toWeek) \(toDay.rawValue) today=\(clientToday)")
        return CalendarMoveResult(workouts: try moveResult.withLock { $0 }.get(), warnings: moveWarnings.withLock { $0 })
    }

    func swapDays(planID: Int, weekNumber: Int, day1: Weekday, day2: Weekday, clientToday: String?) async throws -> CalendarMoveResult {
        record("swap w\(weekNumber) \(day1.rawValue) <-> \(day2.rawValue) today=\(clientToday ?? "-")")
        return CalendarMoveResult(workouts: try swapResult.withLock { $0 }.get(), warnings: swapWarnings.withLock { $0 })
    }

    func markMilestone(planID: Int, key: String) async throws -> PlanMilestones {
        record("milestone mark \(key)")
        return try milestoneResult.withLock { $0 }.get()
    }

    func undoMilestone(planID: Int, key: String) async throws -> PlanMilestones {
        record("milestone undo \(key)")
        return try milestoneResult.withLock { $0 }.get()
    }

    func assessRace(planID: Int, input: BRaceInput) async throws -> BRaceAssessment {
        record("race assess \(input.raceName) \(input.distanceKm.map { String($0) } ?? "-") \(input.effort.rawValue)")
        return try assessResult.withLock { $0 }.get()
    }

    func addRace(planID: Int, input: BRaceInput) async throws -> BRaceChange {
        record("race add \(input.raceName) \(input.distanceKm.map { String($0) } ?? "-") \(input.effort.rawValue)")
        return try raceChangeResult.withLock { $0 }.get()
    }

    func updateRace(planID: Int, raceID: Int, input: BRaceInput) async throws -> BRaceChange {
        record("race update \(raceID) \(input.effort.rawValue)")
        return try raceChangeResult.withLock { $0 }.get()
    }

    func cancelRace(planID: Int, raceID: Int) async throws -> BRaceChange {
        record("race cancel \(raceID)")
        return try raceChangeResult.withLock { $0 }.get()
    }

    func submitRaceResult(planID: Int, raceID: Int, seconds: Int) async throws {
        record("race result \(raceID) \(seconds)")
    }

    func submitRaceDebrief(planID: Int, raceID: Int, answers: BRaceDebriefAnswers) async throws -> BRaceDebriefResult {
        record("race debrief \(raceID) \(answers.fuel ?? "-") \(answers.pacing ?? "-") \(answers.gear ?? "-")")
        return try debriefResult.withLock { $0 }.get()
    }

    func deletePlan(id: Int) async throws {
        record("delete \(id)")
        _ = try deleteResult.withLock { $0 }.get()
    }

    func recentPlans() async throws -> [Plan] {
        record("recent")
        return try recentResult.withLock { $0 }.get()
    }

    func selectPlan(id: Int) async throws -> PlanSnapshot? {
        record("select \(id)")
        return try selectResult.withLock { $0 }.get()
    }

    func blockCompletion(planID: Int) async throws -> BlockCompletionResponse {
        record("completion \(planID)")
        return try completionResult.withLock { $0 }.get()
    }

    func weekReview(planID: Int, week: Int) async throws -> WeekReview {
        record("review \(planID) w\(week)")
        return try reviewResult.withLock { $0 }.get()
    }

    let journeyResult = Mutex<PlanJourney?>(nil)
    let nudgeResult = Mutex<CoachNudge?>(nil)

    func journey(planID: Int) async throws -> PlanJourney {
        record("journey \(planID)")
        guard let journey = journeyResult.withLock({ $0 }) else { throw URLError(.notConnectedToInternet) }
        return journey
    }

    func coachNudge(planID: Int) async throws -> CoachNudge? {
        record("nudge \(planID)")
        return nudgeResult.withLock { $0 }
    }

    func goal(planID: Int) async throws -> PlanGoal {
        record("goal \(planID)")
        return try goalResult.withLock { $0 }.get()
    }

    func reassessGoal(planID: Int) async throws -> PlanGoal {
        record("reassess \(planID)")
        let result = goalResult.withLock { $0 }
        if let wait = beforeGoalReturn.withLock({ $0 }) { await wait() }
        return try result.get()
    }

    func applyGoal(planID: Int, targetMinutes: Double) async throws -> PlanGoal {
        record("apply \(planID) \(Int(targetMinutes))")
        let result = goalResult.withLock { $0 }
        if let wait = beforeGoalReturn.withLock({ $0 }) { await wait() }
        return try result.get()
    }

    func syncWatch(planID: Int) async throws -> String {
        record("syncWatch \(planID)")
        return try syncWatchResult.withLock { $0 }.get()
    }
    func watchActivities(planID: Int) async throws -> [WatchActivity] {
        record("watchActivities \(planID)")
        return try watchActivitiesResult.withLock { $0 }.get()
    }

    let failingMatchLinks = Mutex<Set<Int>>([])

    func setMatch(activityID: Int, workoutID: Int?) async throws {
        record("setMatch \(activityID) -> \(workoutID.map(String.init) ?? "none")")
        if workoutID != nil, failingMatchLinks.withLock({ $0.contains(activityID) }) { throw APIError.transport("offline") }
    }

    func blockEvaluation(planID: Int, block: Int) async throws -> BlockEvaluation {
        record("evaluation \(planID) b\(block)")
        return try evaluationResult.withLock { $0 }.get()
    }

    /// Scoping keeps this fake (so tests see every call) and records the athlete.
    func scoped(toAthlete athleteId: Int?) -> any PlanServicing {
        record("scoped \(athleteId.map(String.init) ?? "self")")
        return self
    }
}
