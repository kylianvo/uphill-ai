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

public struct DeviceConnectionStatus: Codable, Sendable, Equatable {
    public let coros: CorosConnectionStatus?

    public init(coros: CorosConnectionStatus? = nil) {
        self.coros = coros
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
