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
    func syncWatch(planID: Int) async throws -> String
    func knowledgeCard(topic: String, lang: String) async -> KnowledgeCardModel?
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
        guard var snapshot = response.snapshot else { return nil }
        snapshot.workouts = await withWatchMatches(snapshot.workouts, planID: snapshot.plan.id)
        return snapshot
    }

    /// One row of GET /api/integrations/matching.
    private struct MatchedActivity: Decodable {
        let activityId: Int
        let workoutId: Int?
        let distanceKm: Double?
        let durationSeconds: Double?
        let avgHr: Double?
        let deviceModel: String?
    }

    private struct MatchesResponse: Decodable { let activities: [MatchedActivity] }

    /// Active-plan workouts carry no watch data, so attach each workout's matched
    /// activity here. Best effort: the plan still loads if matching can't be read.
    private func withWatchMatches(_ workouts: [Workout], planID: Int) async -> [Workout] {
        guard let response: MatchesResponse = try? await client.send(
            .get("/api/integrations/matching", query: [URLQueryItem(name: "plan_id", value: "\(planID)")])
        ) else { return workouts }
        var byWorkout: [Int: MatchedActivity] = [:]
        for activity in response.activities {
            guard let id = activity.workoutId, byWorkout[id] == nil else { continue }
            byWorkout[id] = activity
        }
        return workouts.map { workout in
            guard let activity = byWorkout[workout.id] else { return workout }
            var matched = workout
            matched.matchedActivityId = activity.activityId
            matched.matchedDeviceModel = activity.deviceModel
            matched.matchedDistanceKm = activity.distanceKm
            matched.matchedDurationSeconds = activity.durationSeconds
            matched.matchedAvgHr = activity.avgHr.map { Int($0.rounded()) }
            return matched
        }
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
        try await client.send(.get("/api/plans/\(planID)/goal", query: [URLQueryItem(name: "lang", value: AppLanguage.code)]))
    }

    func reassessGoal(planID: Int) async throws -> PlanGoal {
        struct Body: Encodable { let exclude: [String]; let lang: String }
        return try await client.send(.send(.post, "/api/plans/\(planID)/goal/reassess", body: Body(exclude: [], lang: AppLanguage.code)))
    }

    func applyGoal(planID: Int, targetMinutes: Double) async throws -> PlanGoal {
        struct Body: Encodable { let targetMins: Double }
        return try await client.send(.send(.post, "/api/plans/\(planID)/goal/apply", body: Body(targetMins: targetMinutes)))
    }

    func syncWatch(planID: Int) async throws -> String {
        struct SyncResponse: Decodable {
            let activities: Int?
            let dailyMetrics: Int?
        }
        let resp: SyncResponse = try await client.send(.post("/api/integrations/coros/sync", query: [URLQueryItem(name: "plan_id", value: "\(planID)")]))
        // Sync only stores activities; matching links them to this plan's workouts.
        struct MatchCounts: Decodable {}
        let tzOffset = TimeZone.current.secondsFromGMT() / 60
        let _: MatchCounts = try await client.send(.post("/api/integrations/matching/run", query: [
            URLQueryItem(name: "plan_id", value: "\(planID)"),
            URLQueryItem(name: "tz_offset_minutes", value: "\(tzOffset)"),
        ]))
        let count = resp.activities ?? 0
        return count > 0 ? "Synced \(count) activities from watch" : "Watch synced · Up to date"
    }
    func knowledgeCard(topic: String, lang: String = AppLanguage.code) async -> KnowledgeCardModel? {
        do {
            let resp: KnowledgeCardsResponse = try await client.send(.get("/api/knowledge/cards", query: [
                URLQueryItem(name: "topic", value: topic),
                URLQueryItem(name: "lang", value: lang)
            ]))
            return resp.cards.first
        } catch {
            return nil
        }
    }
}
