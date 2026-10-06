import Foundation

protocol CoachingServicing: Sendable {
    func fetchOverview(days: Int?, athleteId: Int?, level: String?) async throws -> CoachOverview
    func fetchRoster() async throws -> [CoachedAthleteRow]
    func fetchMyInvites() async throws -> [CoachingInvite]
    func sendInvite(athleteEmail: String) async throws -> CoachedAthleteRow
    func acceptInvite(inviteId: Int) async throws
    func declineInvite(inviteId: Int) async throws
    func removeFromRoster(linkId: Int) async throws
    func fetchAthleteProfile(athleteId: Int) async throws -> User
    func fetchAthleteActivePlan(athleteId: Int) async throws -> PlanSnapshot?
    func fetchAthleteDraftPlan(athleteId: Int) async throws -> PlanSnapshot?
    func approveWorkout(athleteId: Int, planId: Int, workoutId: Int) async throws -> Workout
    func removeWorkout(athleteId: Int, planId: Int, workoutId: Int) async throws -> Workout
    func editWorkout(athleteId: Int, planId: Int, workoutId: Int, payload: CoachWorkoutUpdatePayload) async throws -> Workout
    func addWorkout(athleteId: Int, planId: Int, payload: CoachWorkoutCreatePayload) async throws -> Workout
    func aiCreateWorkout(athleteId: Int, planId: Int, payload: CoachWorkoutAiCreatePayload) async throws -> Workout
    func fetchNotes(athleteId: Int, targetType: String?, targetId: Int?) async throws -> [CoachNote]
    func addNote(athleteId: Int, payload: CoachNoteCreatePayload) async throws -> CoachNote
}

struct DraftPlanResponse: Decodable, Sendable {
    let draft: Bool
    let plan: Plan?
    let workouts: [Workout]?

    var snapshot: PlanSnapshot? {
        guard draft, let plan else { return nil }
        return PlanSnapshot(plan: plan, workouts: workouts ?? [])
    }
}

struct CoachInvitePayload: Encodable, Sendable {
    let athleteEmail: String
    enum CodingKeys: String, CodingKey {
        case athleteEmail = "athlete_email"
    }
}

struct CoachWorkoutUpdatePayload: Encodable, Sendable {
    var title: String?
    var type: String?
    var durationMinutes: Double?
    var distanceKm: Double?
    var targetZone: String?
    var description: String?
    var fuelingTip: String?
    var dayOfWeek: String?

    enum CodingKeys: String, CodingKey {
        case title, type, description
        case durationMinutes = "duration_minutes"
        case distanceKm = "distance_km"
        case targetZone = "target_zone"
        case fuelingTip = "fueling_tip"
        case dayOfWeek = "day_of_week"
    }
}

struct CoachWorkoutCreatePayload: Encodable, Sendable {
    let weekNumber: Int
    let dayOfWeek: String
    let phase: String
    let title: String
    let type: String
    let durationMinutes: Double
    let targetZone: String
    var distanceKm: Double?
    var description: String?
    var fuelingTip: String?

    enum CodingKeys: String, CodingKey {
        case weekNumber = "week_number"
        case dayOfWeek = "day_of_week"
        case phase, title, type, description
        case durationMinutes = "duration_minutes"
        case targetZone = "target_zone"
        case distanceKm = "distance_km"
        case fuelingTip = "fueling_tip"
    }
}

struct CoachWorkoutAiCreatePayload: Encodable, Sendable {
    let weekNumber: Int
    let dayOfWeek: String
    let workoutType: String
    let durationMinutes: Double

    enum CodingKeys: String, CodingKey {
        case weekNumber = "week_number"
        case dayOfWeek = "day_of_week"
        case workoutType = "workout_type"
        case durationMinutes = "duration_minutes"
    }
}

struct CoachingService: CoachingServicing {
    private let client: APIClient

    init(client: APIClient) {
        self.client = client
    }

    func fetchOverview(days: Int? = 14, athleteId: Int? = nil, level: String? = nil) async throws -> CoachOverview {
        var items: [URLQueryItem] = []
        if let days { items.append(URLQueryItem(name: "days", value: "\(days)")) }
        if let athleteId { items.append(URLQueryItem(name: "athlete_id", value: "\(athleteId)")) }
        if let level, level != "all" { items.append(URLQueryItem(name: "level", value: level)) }
        let endpoint = Endpoint<CoachOverview>.get("/api/coaching/overview", query: items)
        return try await client.send(endpoint)
    }

    func fetchRoster() async throws -> [CoachedAthleteRow] {
        let endpoint = Endpoint<[CoachedAthleteRow]>.get("/api/coaching/roster")
        return try await client.send(endpoint)
    }

    func fetchMyInvites() async throws -> [CoachingInvite] {
        let endpoint = Endpoint<[CoachingInvite]>.get("/api/coaching/my-invites")
        return try await client.send(endpoint)
    }

    func sendInvite(athleteEmail: String) async throws -> CoachedAthleteRow {
        let payload = CoachInvitePayload(athleteEmail: athleteEmail)
        let endpoint = try Endpoint<CoachedAthleteRow>.send(.post, "/api/coaching/invite", body: payload)
        return try await client.send(endpoint)
    }

    func acceptInvite(inviteId: Int) async throws {
        let endpoint = Endpoint<EmptyResponse>.post("/api/coaching/invites/\(inviteId)/accept")
        _ = try await client.send(endpoint)
    }

    func declineInvite(inviteId: Int) async throws {
        let endpoint = Endpoint<EmptyResponse>.post("/api/coaching/invites/\(inviteId)/decline")
        _ = try await client.send(endpoint)
    }

    func removeFromRoster(linkId: Int) async throws {
        let endpoint = Endpoint<EmptyResponse>.delete("/api/coaching/roster/\(linkId)")
        _ = try await client.send(endpoint)
    }

    func fetchAthleteProfile(athleteId: Int) async throws -> User {
        let endpoint = Endpoint<User>.get("/api/coaching/athletes/\(athleteId)/profile")
        return try await client.send(endpoint)
    }

    func fetchAthleteActivePlan(athleteId: Int) async throws -> PlanSnapshot? {
        let endpoint = Endpoint<ActivePlanResponse>.get("/api/coaching/athletes/\(athleteId)/active-plan")
        let res = try await client.send(endpoint)
        return res.snapshot
    }

    func fetchAthleteDraftPlan(athleteId: Int) async throws -> PlanSnapshot? {
        let endpoint = Endpoint<DraftPlanResponse>.get("/api/coaching/athletes/\(athleteId)/plans/draft")
        let res = try await client.send(endpoint)
        return res.snapshot
    }

    func approveWorkout(athleteId: Int, planId: Int, workoutId: Int) async throws -> Workout {
        let endpoint = Endpoint<Workout>.post("/api/coaching/athletes/\(athleteId)/plans/\(planId)/workouts/\(workoutId)/approve")
        return try await client.send(endpoint)
    }

    func removeWorkout(athleteId: Int, planId: Int, workoutId: Int) async throws -> Workout {
        let endpoint = Endpoint<Workout>.post("/api/coaching/athletes/\(athleteId)/plans/\(planId)/workouts/\(workoutId)/remove")
        return try await client.send(endpoint)
    }

    func editWorkout(athleteId: Int, planId: Int, workoutId: Int, payload: CoachWorkoutUpdatePayload) async throws -> Workout {
        let endpoint = try Endpoint<Workout>.send(.put, "/api/coaching/athletes/\(athleteId)/plans/\(planId)/workouts/\(workoutId)", body: payload)
        return try await client.send(endpoint)
    }

    func addWorkout(athleteId: Int, planId: Int, payload: CoachWorkoutCreatePayload) async throws -> Workout {
        let endpoint = try Endpoint<Workout>.send(.post, "/api/coaching/athletes/\(athleteId)/plans/\(planId)/workouts", body: payload)
        return try await client.send(endpoint)
    }

    func aiCreateWorkout(athleteId: Int, planId: Int, payload: CoachWorkoutAiCreatePayload) async throws -> Workout {
        let endpoint = try Endpoint<Workout>.send(.post, "/api/coaching/athletes/\(athleteId)/plans/\(planId)/workouts/ai-create", body: payload)
        return try await client.send(endpoint)
    }

    func fetchNotes(athleteId: Int, targetType: String? = nil, targetId: Int? = nil) async throws -> [CoachNote] {
        var items: [URLQueryItem] = []
        if let targetType { items.append(URLQueryItem(name: "target_type", value: targetType)) }
        if let targetId { items.append(URLQueryItem(name: "target_id", value: "\(targetId)")) }
        let endpoint = Endpoint<CoachNotesResponse>.get("/api/coaching/athletes/\(athleteId)/notes", query: items)
        let res = try await client.send(endpoint)
        return res.notes
    }

    func addNote(athleteId: Int, payload: CoachNoteCreatePayload) async throws -> CoachNote {
        let endpoint = try Endpoint<CoachNote>.send(.post, "/api/coaching/athletes/\(athleteId)/notes", body: payload)
        return try await client.send(endpoint)
    }
}
