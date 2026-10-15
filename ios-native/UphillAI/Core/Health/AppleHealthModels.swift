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

/// One day of recovery data for the same sync. `date` is the athlete's local calendar day
/// (`yyyy-MM-dd`); sleep belongs to the day the athlete woke up. Stages and samples stay on the phone.
struct AppleHealthDailyMetricUpload: Codable, Sendable, Equatable {
    let date: String
    let restingHr: Int?
    let hrvSdnnMs: Double?
    let sleepMinutes: Int?
}

struct AppleHealthSyncBody: Encodable, Sendable {
    let workouts: [AppleHealthWorkoutUpload]
    let deletedIds: [String]
    let planId: Int?
    let tzOffsetMinutes: Int
    var dailyMetrics: [AppleHealthDailyMetricUpload] = []
}

struct AppleHealthSyncResult: Decodable, Sendable, Equatable {
    struct Rejected: Decodable, Sendable, Equatable {
        let externalId: String
        let reason: String
    }

    struct DailyMetrics: Decodable, Sendable, Equatable {
        struct Rejected: Decodable, Sendable, Equatable {
            let date: String
            let reason: String
        }

        let accepted: Int
        let rejected: [Rejected]
        /// The server has recovery metrics turned off and stored nothing.
        var disabled: Bool? = nil
    }

    let accepted: Int
    let rejected: [Rejected]
    let deleted: Int
    /// Absent on backends older than recovery metrics.
    var dailyMetrics: DailyMetrics? = nil
}

public struct AppleHealthConnectionStatus: Codable, Sendable, Equatable {
    public let enabled: Bool
    public let connected: Bool
    public let lastSyncAt: String?
    /// Absent on backends older than recovery metrics, which means on.
    public var recoveryEnabled: Bool? = nil
}
