import Foundation

public struct CorosConnectionStatus: Codable, Sendable, Equatable {
    public let connected: Bool
    public let lastSyncAt: String?
    public let deviceModel: String?

    public init(connected: Bool, lastSyncAt: String? = nil, deviceModel: String? = nil) {
        self.connected = connected
        self.lastSyncAt = lastSyncAt
        self.deviceModel = deviceModel
    }
}

/// Display name of a backend `source_provider`, for "Source:" lines. Brand names, never translated.
public func deviceSourceName(_ provider: String) -> String {
    switch provider {
    case "apple_health": "Apple Health"
    case "garmin": "Garmin"
    case "coros": "COROS"
    default: provider
    }
}

/// A race course created on the athlete's Garmin account from their GPX.
public struct GarminCourseResult: Codable, Sendable, Equatable {
    public let status: String
    public let courseId: String?
    public let distanceKm: Double
    public let points: Int
}

/// Garmin delivers data by push after the athlete's next watch sync, so there is no
/// "Sync now"; `lastSyncAt` is when data last arrived.
public struct GarminConnectionStatus: Codable, Sendable, Equatable {
    /// Off until Garmin's production review passes (backend GARMIN_ENABLED).
    public let enabled: Bool
    public let connected: Bool
    public let lastSyncAt: String?
    public var permissions: [String]? = nil
}

public struct DeviceConnectionStatus: Codable, Sendable, Equatable {
    public let coros: CorosConnectionStatus?
    /// Absent on backends older than the Apple Health release.
    public let appleHealth: AppleHealthConnectionStatus?
    /// Absent on backends older than the Garmin release.
    public let garmin: GarminConnectionStatus?

    public init(
        coros: CorosConnectionStatus? = nil,
        appleHealth: AppleHealthConnectionStatus? = nil,
        garmin: GarminConnectionStatus? = nil
    ) {
        self.coros = coros
        self.appleHealth = appleHealth
        self.garmin = garmin
    }

    public var isCorosConnected: Bool {
        coros?.connected ?? false
    }
}

public struct DeviceSyncResult: Codable, Sendable, Equatable {
    public let activities: Int
    public let dailyMetrics: Int

    public init(activities: Int, dailyMetrics: Int) {
        self.activities = activities
        self.dailyMetrics = dailyMetrics
    }
}

public struct FitnessSyncResult: Codable, Sendable, Equatable {
    public let status: String
    public let thresholdPace: String?
    public let corosVo2Max: Double?
    public let corosRunningLevel: Double?

    public var corosVo2max: Double? { corosVo2Max }

    public init(
        status: String,
        thresholdPace: String? = nil,
        corosVo2max: Double? = nil,
        corosRunningLevel: Double? = nil
    ) {
        self.status = status
        self.thresholdPace = thresholdPace
        self.corosVo2Max = corosVo2max
        self.corosRunningLevel = corosRunningLevel
    }
}

public struct CorosPushSummary: Codable, Sendable, Equatable {
    public let mode: String?
    public let daysSent: Int
    public let workoutsSent: Int
    public let leftInUphill: Int
    public let lockedDays: Int
    public let invalid: Int
    public let stale: Int?
    public let windowEnd: String
    public let planStart: String?

    public init(
        mode: String? = nil,
        daysSent: Int,
        workoutsSent: Int,
        leftInUphill: Int = 0,
        lockedDays: Int = 0,
        invalid: Int = 0,
        stale: Int? = nil,
        windowEnd: String,
        planStart: String? = nil
    ) {
        self.mode = mode
        self.daysSent = daysSent
        self.workoutsSent = workoutsSent
        self.leftInUphill = leftInUphill
        self.lockedDays = lockedDays
        self.invalid = invalid
        self.stale = stale
        self.windowEnd = windowEnd
        self.planStart = planStart
    }
}

public struct CorosPushStatus: Codable, Sendable, Equatable {
    public let connected: Bool
    public let lastPushedAt: String?
    public let outOfDate: Bool?
    public let partial: Bool?
    public let lastSummary: CorosPushSummary?

    public init(
        connected: Bool,
        lastPushedAt: String? = nil,
        outOfDate: Bool? = nil,
        partial: Bool? = nil,
        lastSummary: CorosPushSummary? = nil
    ) {
        self.connected = connected
        self.lastPushedAt = lastPushedAt
        self.outOfDate = outOfDate
        self.partial = partial
        self.lastSummary = lastSummary
    }
}

public struct CorosPushOutcome: Codable, Sendable, Equatable {
    public let isSuccess: Bool
    public let status: String
    public let summary: CorosPushSummary?
    public let lastPushedAt: String?
    public let errorCode: String?
    public let errorMessage: String?

    public init(
        isSuccess: Bool,
        status: String,
        summary: CorosPushSummary? = nil,
        lastPushedAt: String? = nil,
        errorCode: String? = nil,
        errorMessage: String? = nil
    ) {
        self.isSuccess = isSuccess
        self.status = status
        self.summary = summary
        self.lastPushedAt = lastPushedAt
        self.errorCode = errorCode
        self.errorMessage = errorMessage
    }
}

/// The part of /api/auth/fitness-snapshot that plan setup reads: measured weekly volume and where it came from.
struct WatchVolume: Decodable, Sendable {
    let weeklyKm: Double
    let weeklyKmSource: String
}
