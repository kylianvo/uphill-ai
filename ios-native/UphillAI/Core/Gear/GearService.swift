import Foundation

protocol GearServicing: Sendable {
    func recommendShoes(params: GearParams) async throws -> GearPlan
    func sendFeedback(token: String, value: Int) async throws
}

struct GearService: GearServicing {
    private let client: APIClient

    init(client: APIClient) {
        self.client = client
    }

    private struct FeedbackBody: Encodable {
        let token: String
        let value: Int
    }

    func recommendShoes(params: GearParams) async throws -> GearPlan {
        let endpoint = try Endpoint<GearPlan>.send(.post, "/api/coach/recommend-shoes", body: params, requiresAuth: false)
        return try await client.send(endpoint)
    }

    func sendFeedback(token: String, value: Int) async throws {
        let body = FeedbackBody(token: token, value: value)
        let endpoint = try Endpoint<EmptyResponse>.send(.post, "/api/feedback/result", body: body, requiresAuth: false)
        _ = try await client.send(endpoint)
    }
}
