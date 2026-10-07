import Foundation

protocol GoalEstimateServicing: Sendable {
    func estimateGoal(request: GoalEstimateRequest) async throws -> GoalEstimate
}

struct GoalEstimateService: GoalEstimateServicing {
    private let client: APIClient

    init(client: APIClient) {
        self.client = client
    }

    func estimateGoal(request: GoalEstimateRequest) async throws -> GoalEstimate {
        let endpoint = try Endpoint<GoalAssessmentResponse>.send(.post, "/api/goal/assess", body: request)
        return try await client.send(endpoint).estimate
    }
}

/// Wire shape of a goal assessment (`services/goal_service.py:_present`).
struct GoalAssessmentResponse: Decodable, Sendable {
    struct Tiers: Decodable, Sendable {
        let a: Double
        let b: Double
        let c: Double
    }
    struct Context: Decodable, Sendable {
        struct Race: Decodable, Sendable { let profileSource: String? }
        struct Athlete: Decodable, Sendable { let easyPaceMinKm: Double? }
        let race: Race?
        let athlete: Athlete?
    }

    let raceName: String?
    let distanceKm: Double
    let elevationGainM: Double?
    let goals: Tiers?
    let confidence: String?
    let reasoning: [String]?
    let sources: [GoalSourceItem]?
    let benchmarks: [RaceBenchmark]?
    let context: Context?

    var estimate: GoalEstimate {
        GoalEstimate(
            raceName: raceName,
            distanceKm: distanceKm,
            elevationGainM: elevationGainM ?? 0,
            baseFlatPaceMinKm: context?.athlete?.easyPaceMinKm,
            goals: goals.map { GoalEstimateTiers(ambitious: $0.a, realistic: $0.b, safe: $0.c) },
            benchmarks: benchmarks,
            targetProfileSource: context?.race?.profileSource,
            referenceConfidence: confidence,
            sources: sources,
            reasoning: reasoning
        )
    }
}
