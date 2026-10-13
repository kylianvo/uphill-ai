import Foundation

/// One workout summary for POST /api/integrations/apple-health/sync. Routes and HR series
/// never leave the phone; these fields are all the backend gets.
struct AppleHealthWorkoutUpload: Codable, Sendable, Equatable {
    let externalId: String
    let activityType: String
    let startTime: String
    let endTime: String
    let durationSeconds: Double
    let distanceKm: Double?
    let elevationGainM: Double?
    let avgHr: Int?
    let maxHr: Int?
    let calories: Int?
    let sourceName: String?
}

struct AppleHealthSyncBody: Encodable, Sendable {
    let workouts: [AppleHealthWorkoutUpload]
    let deletedIds: [String]
    let planId: Int?
    let tzOffsetMinutes: Int
}

struct AppleHealthSyncResult: Decodable, Sendable, Equatable {
    struct Rejected: Decodable, Sendable, Equatable {
        let externalId: String
        let reason: String
    }

    let accepted: Int
    let rejected: [Rejected]
    let deleted: Int
}

public struct AppleHealthConnectionStatus: Codable, Sendable, Equatable {
    public let enabled: Bool
    public let connected: Bool
    public let lastSyncAt: String?
}
