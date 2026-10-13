import Foundation

protocol AppleHealthUploading: Sendable {
    func sync(_ body: AppleHealthSyncBody) async throws -> AppleHealthSyncResult
    func disconnect() async throws
}

struct AppleHealthAPI: AppleHealthUploading {
    let client: APIClient

    func sync(_ body: AppleHealthSyncBody) async throws -> AppleHealthSyncResult {
        try await client.send(.send(.post, "/api/integrations/apple-health/sync", body: body))
    }

    /// Deletes everything Uphill received from Apple Health. HealthKit permission itself
    /// can only be revoked by the athlete in Settings.
    func disconnect() async throws {
        let _: EmptyResponse = try await client.send(.delete("/api/integrations/apple-health"))
    }
}
