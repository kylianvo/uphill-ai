import Foundation

protocol PacingServicing: Sendable {
    func calculatePacing(request: PacingRequest) async throws -> [PacedCheckpoint]
    /// Curated past results for a known race (empty when unknown or uncurated).
    func benchmarks(raceName: String, distanceKm: Double) async -> [RaceBenchmark]
}

extension PacingServicing {
    func benchmarks(raceName: String, distanceKm: Double) async -> [RaceBenchmark] { [] }
}

struct PacingService: PacingServicing {
    private let client: APIClient

    init(client: APIClient) {
        self.client = client
    }

    func calculatePacing(request: PacingRequest) async throws -> [PacedCheckpoint] {
        do {
            let endpoint = try Endpoint<[PacedCheckpoint]>.send(.post, "/api/coach/calculate-pacing", body: request)
            return try await client.send(endpoint)
        } catch {
            // Local fallback using client-side Minetti physics engine
            return PacingCalculator.calculateCheckpointPaces(
                checkpoints: request.checkpoints,
                targetTimeMins: request.targetTimeMins,
                targetFlatPaceMinKm: request.targetFlatPaceMinKm,
                splitBias: request.splitBias ?? 0.0,
                runnerWeightKg: request.runnerWeightKg ?? 68.0
            )
        }
    }

    func benchmarks(raceName: String, distanceKm: Double) async -> [RaceBenchmark] {
        struct Response: Decodable, Sendable { let matched: Bool; let results: [RaceBenchmark]? }
        let endpoint = Endpoint<Response>.get("/api/coach/pace-strategy/benchmarks", query: [
            URLQueryItem(name: "name", value: raceName),
            URLQueryItem(name: "distance_km", value: String(distanceKm)),
        ], requiresAuth: false)
        guard let response = try? await client.send(endpoint), response.matched else { return [] }
        return response.results ?? []
    }
}
