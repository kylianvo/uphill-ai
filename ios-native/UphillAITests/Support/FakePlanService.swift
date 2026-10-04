import Foundation
import Synchronization
@testable import UphillAI

/// Scriptable PlanServicing. Set the results before use; read `calls` after.
final class FakePlanService: PlanServicing {
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

    func move(planID: Int, workoutID: Int, toWeek: Int, toDay: Weekday, clientToday: String) async throws -> CalendarMoveResult {
        record("move \(workoutID) -> w\(toWeek) \(toDay.rawValue) today=\(clientToday)")
        return CalendarMoveResult(workouts: try moveResult.withLock { $0 }.get(), warnings: moveWarnings.withLock { $0 })
    }

    func swapDays(planID: Int, weekNumber: Int, day1: Weekday, day2: Weekday, clientToday: String?) async throws -> CalendarMoveResult {
        record("swap w\(weekNumber) \(day1.rawValue) <-> \(day2.rawValue) today=\(clientToday ?? "-")")
        return CalendarMoveResult(workouts: try swapResult.withLock { $0 }.get(), warnings: swapWarnings.withLock { $0 })
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

    func goal(planID: Int) async throws -> PlanGoal {
        record("goal \(planID)")
        return try goalResult.withLock { $0 }.get()
    }

    func reassessGoal(planID: Int) async throws -> PlanGoal {
        record("reassess \(planID)")
        return try goalResult.withLock { $0 }.get()
    }

    func applyGoal(planID: Int, targetMinutes: Double) async throws -> PlanGoal {
        record("apply \(planID) \(Int(targetMinutes))")
        return try goalResult.withLock { $0 }.get()
    }

    func syncWatch(planID: Int) async throws -> String {
        record("syncWatch \(planID)")
        return "Watch synced · Up to date"
    }
    func knowledgeCard(topic: String, lang: String) async -> KnowledgeCardModel? {
        return KnowledgeCardModel(
            id: 1,
            chapterTitle: "Find your Zone 2 heart rate",
            summary: "Accurately identifying your Zone 2 limits is crucial for effective aerobic development.",
            keyPoints: [
                "Utilize the simple Talk Test or Nose Breathing to gauge effort.",
                "Conduct a Heart Rate Drift Test to pinpoint your Aerobic Threshold."
            ],
            tags: ["heart-rate", "talk-test", "aerobic-threshold"],
            topic: topic,
            sourceLabel: "Uphill Athlete"
        )
    }
}
