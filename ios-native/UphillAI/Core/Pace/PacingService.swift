import Foundation

protocol PacingServicing: Sendable {
    func calculatePacing(request: PacingRequest) async throws -> [PacedCheckpoint]
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
}
