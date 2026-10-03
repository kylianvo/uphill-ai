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
    func move(planID: Int, workoutID: Int, toWeek: Int, toDay: Weekday, clientToday: String) async throws -> CalendarMoveResult
    func swapDays(planID: Int, weekNumber: Int, day1: Weekday, day2: Weekday, clientToday: String?) async throws -> CalendarMoveResult
    func deletePlan(id: Int) async throws
    func recentPlans() async throws -> [Plan]
    func selectPlan(id: Int) async throws -> PlanSnapshot?
    func blockCompletion(planID: Int) async throws -> BlockCompletionResponse
    func weekReview(planID: Int, week: Int) async throws -> WeekReview
    func goal(planID: Int) async throws -> PlanGoal
    func reassessGoal(planID: Int) async throws -> PlanGoal
    func applyGoal(planID: Int, targetMinutes: Double) async throws -> PlanGoal
}

struct PlanService: PlanServicing {
    let client: APIClient

    private struct WorkoutsResponse: Decodable, Sendable { let workouts: [Workout] }
    private struct RecentResponse: Decodable, Sendable { let plans: [Plan] }
    private struct DeleteResponse: Decodable, Sendable {
        let success: Bool
        let message: String
        let planId: Int
    }

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

    private struct SwapBody: Encodable {
        let planId: Int
        let weekNumber: Int
        let day1: String
        let day2: String
        let clientToday: String?

        enum CodingKeys: String, CodingKey {
            case planId = "plan_id"
            case weekNumber = "week_number"
            case day1 = "day_1"
            case day2 = "day_2"
            case clientToday = "client_today"
        }
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

    func move(planID: Int, workoutID: Int, toWeek: Int, toDay: Weekday, clientToday: String) async throws -> CalendarMoveResult {
        let body = MoveBody(planId: planID,
                            operations: [.init(workoutId: workoutID, targetWeek: toWeek, targetDay: toDay.rawValue)],
                            clientToday: clientToday)
        let response: CalendarMoveResult = try await client.send(.send(.post, "/api/coach/calendar/move", body: body))
        return response
    }

    func swapDays(planID: Int, weekNumber: Int, day1: Weekday, day2: Weekday, clientToday: String?) async throws -> CalendarMoveResult {
        let body = SwapBody(planId: planID, weekNumber: weekNumber, day1: day1.rawValue, day2: day2.rawValue, clientToday: clientToday)
        let response: CalendarMoveResult = try await client.send(.send(.post, "/api/coach/modify-calendar", body: body))
        return response
    }

    func deletePlan(id: Int) async throws {
        let _: DeleteResponse = try await client.send(.delete("/api/coach/plans/\(id)"))
    }

    func recentPlans() async throws -> [Plan] {
        let response: RecentResponse = try await client.send(.get("/api/coach/recent-plans"))
        return response.plans
    }

    func selectPlan(id: Int) async throws -> PlanSnapshot? {
        let response: ActivePlanResponse = try await client.send(.send(.post, "/api/coach/select-plan", body: SelectBody(planId: id)))
        return response.snapshot
    }

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
}
