import Foundation

protocol NutritionServicing: Sendable {
    func calculateFueling(params: NutritionParams) async throws -> NutritionPlan
    func catalog() async throws -> [CatalogProduct]
    func sendFeedback(token: String, value: Int) async throws
}

struct NutritionService: NutritionServicing {
    private let client: APIClient

    init(client: APIClient) {
        self.client = client
    }

    private struct FeedbackBody: Encodable {
        let token: String
        let value: Int
    }

    func calculateFueling(params: NutritionParams) async throws -> NutritionPlan {
        let endpoint = try Endpoint<NutritionPlan>.send(.post, "/api/coach/calculate-fueling", body: params, requiresAuth: false)
        return try await client.send(endpoint)
    }

    func catalog() async throws -> [CatalogProduct] {
        try await client.send(.get("/api/coach/nutrition-catalog", requiresAuth: false))
    }

    func sendFeedback(token: String, value: Int) async throws {
        let body = FeedbackBody(token: token, value: value)
        let endpoint = try Endpoint<EmptyResponse>.send(.post, "/api/feedback/result", body: body, requiresAuth: false)
        _ = try await client.send(endpoint)
    }
}
