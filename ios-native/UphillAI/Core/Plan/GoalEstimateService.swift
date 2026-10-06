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
        let endpoint = try Endpoint<GoalEstimate>.send(.post, "/api/coach/goal-estimate", body: request)
        return try await client.send(endpoint)
    }
}
