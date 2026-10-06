import Foundation

protocol GearServicing: Sendable {
    func recommendShoes(params: GearParams) async throws -> GearPlan
    func sendFeedback(token: String, value: Int) async throws
    func fetchShoeRotation() async throws -> ShoeRotation
    func saveShoeRotation(_ rotation: ShoeRotation) async throws -> ShoeRotation
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

    func fetchShoeRotation() async throws -> ShoeRotation {
        try await client.send(.get("/api/shoe-rotation"))
    }

    func saveShoeRotation(_ rotation: ShoeRotation) async throws -> ShoeRotation {
        try await client.send(.send(.put, "/api/shoe-rotation", body: rotation))
    }
}
