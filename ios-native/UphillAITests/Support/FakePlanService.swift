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
