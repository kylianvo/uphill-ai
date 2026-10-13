import Foundation

/// What HealthKitStore reads from one HKWorkout, as plain values so the mapping is testable
/// without HealthKit. `routeAltitudes` is read only when the workout has no climb metadata.
struct HealthWorkoutSample: Sendable, Equatable {
    enum Kind: Sendable, Equatable { case running, hiking, stairs, strength, other }

    let uuid: UUID
    let kind: Kind
    let isIndoor: Bool
    let start: Date
    let end: Date
    let duration: TimeInterval
    let distanceMeters: Double?
    let elevationAscendedMeters: Double?
    let routeAltitudes: [Double]?
    let averageHeartRate: Double?
    let maxHeartRate: Double?
    let activeEnergyKcal: Double?
    let sourceName: String
}

enum HealthWorkoutMapper {
    /// nil for kinds Uphill doesn't import.
    static func upload(for s: HealthWorkoutSample, timeZone: TimeZone = .current) -> AppleHealthWorkoutUpload? {
        let type: String
        switch s.kind {
        case .running: type = s.isIndoor ? "indoor_run" : "outdoor_run"
        // COROS files hikes as "hike" too; volume counts it on foot and matching scores it as endurance.
        case .hiking, .stairs: type = "hike"
        case .strength: type = "strength"
        case .other: return nil
        }
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        formatter.timeZone = timeZone
        let climb = s.elevationAscendedMeters ?? s.routeAltitudes.map { climb(altitudes: $0) }
        return AppleHealthWorkoutUpload(
            externalId: s.uuid.uuidString,
            activityType: type,
            startTime: formatter.string(from: s.start),
            endTime: formatter.string(from: s.end),
            durationSeconds: s.duration.rounded(),
            distanceKm: s.distanceMeters.map { ($0 / 1000 * 1000).rounded() / 1000 },
            elevationGainM: climb.map { ($0 * 10).rounded() / 10 },
            avgHr: s.averageHeartRate.map { Int($0.rounded()) },
            maxHr: s.maxHeartRate.map { Int($0.rounded()) },
            calories: s.activeEnergyKcal.map { Int($0.rounded()) },
            sourceName: s.sourceName
        )
    }

    /// Metres climbed, counting a rise only once it clears `threshold` above the last
    /// low point, so GPS altitude jitter doesn't add up to fake vert.
    static func climb(altitudes: [Double], threshold: Double = 3) -> Double {
        guard var reference = altitudes.first else { return 0 }
        var gain = 0.0
        for altitude in altitudes.dropFirst() {
            if altitude - reference >= threshold {
                gain += altitude - reference
                reference = altitude
            } else if reference - altitude >= threshold {
                reference = altitude
            }
        }
        return gain
    }
}
