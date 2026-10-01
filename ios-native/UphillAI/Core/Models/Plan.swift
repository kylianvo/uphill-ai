import Foundation

enum Weekday: String, CaseIterable, Codable, Sendable, Identifiable {
    case monday = "Monday", tuesday = "Tuesday", wednesday = "Wednesday", thursday = "Thursday"
    case friday = "Friday", saturday = "Saturday", sunday = "Sunday"

    var id: String { rawValue }
    /// Days after Monday: Monday 0 … Sunday 6.
    var offset: Int { Weekday.allCases.firstIndex(of: self)! }
    var short: String { String(rawValue.prefix(3)) }
}

/// Mirrors a `plans` row. Unused columns (prediction JSONB, athlete notes…) are not decoded.
struct Plan: Codable, Sendable, Equatable, Identifiable {
    let id: Int
    let raceName: String
    let raceDate: String
    let goalType: String
    let targetTimeHours: Double?
    let totalWeeks: Int
    let currentWeek: Int?
    let courseDistanceKm: Double?
    let courseElevationGainM: Double?
    let startDate: String?
    let planStatus: String?
    let createdAt: String?
}

/// Mirrors a `workouts` row.
struct Workout: Codable, Sendable, Equatable, Identifiable {
    let id: Int
    let planId: Int
    let weekNumber: Int
    let dayOfWeek: String
    let phase: String
    let title: String
    let type: String
    let durationMinutes: Double
    let distanceKm: Double?
    let targetZone: String
    let targetHrRange: String?
    let targetPace: String?
    let treadmillIncline: String?
    let treadmillSpeed: String?
    let elevationGainM: Double?
    let gradePercent: Double?
    let intervalReps: Int?
    let intervalRepValue: Double?
    let intervalRepUnit: String?
    let walkIntervalValue: Double?
    let description: String?
    let fuelingTip: String?
    let source: String?
    let isCompleted: Int?
    let isMissed: Int?
    let approvedAt: String?
    let rpe: Int?
    let notes: String?
    let sessionSlot: String?
    let isPriority: Bool

    enum CodingKeys: String, CodingKey {
        case id, planId, weekNumber, dayOfWeek, phase, title, type, durationMinutes, distanceKm, targetZone
        case targetHrRange, targetPace, treadmillIncline, treadmillSpeed, elevationGainM, gradePercent
        case intervalReps, intervalRepValue, intervalRepUnit, walkIntervalValue, description, fuelingTip
        case source, isCompleted, isMissed, approvedAt, rpe, notes, sessionSlot, isPriority
    }

    init(from decoder: any Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(Int.self, forKey: .id)
        planId = try c.decode(Int.self, forKey: .planId)
        weekNumber = try c.decode(Int.self, forKey: .weekNumber)
        dayOfWeek = try c.decode(String.self, forKey: .dayOfWeek)
        phase = try c.decode(String.self, forKey: .phase)
        title = try c.decode(String.self, forKey: .title)
        type = try c.decode(String.self, forKey: .type)
        durationMinutes = try c.decode(Double.self, forKey: .durationMinutes)
        distanceKm = try c.decodeIfPresent(Double.self, forKey: .distanceKm)
        targetZone = try c.decode(String.self, forKey: .targetZone)
        targetHrRange = try c.decodeIfPresent(String.self, forKey: .targetHrRange)
        targetPace = try c.decodeIfPresent(String.self, forKey: .targetPace)
        treadmillIncline = try c.decodeIfPresent(String.self, forKey: .treadmillIncline)
        treadmillSpeed = try c.decodeIfPresent(String.self, forKey: .treadmillSpeed)
        elevationGainM = try c.decodeIfPresent(Double.self, forKey: .elevationGainM)
        gradePercent = try c.decodeIfPresent(Double.self, forKey: .gradePercent)
        intervalReps = try c.decodeIfPresent(Int.self, forKey: .intervalReps)
        intervalRepValue = try c.decodeIfPresent(Double.self, forKey: .intervalRepValue)
        intervalRepUnit = try c.decodeIfPresent(String.self, forKey: .intervalRepUnit)
        walkIntervalValue = try c.decodeIfPresent(Double.self, forKey: .walkIntervalValue)
        description = try c.decodeIfPresent(String.self, forKey: .description)
        fuelingTip = try c.decodeIfPresent(String.self, forKey: .fuelingTip)
        source = try c.decodeIfPresent(String.self, forKey: .source)
        isCompleted = try c.decodeIfPresent(Int.self, forKey: .isCompleted)
        isMissed = try c.decodeIfPresent(Int.self, forKey: .isMissed)
        approvedAt = try c.decodeIfPresent(String.self, forKey: .approvedAt)
        rpe = try c.decodeIfPresent(Int.self, forKey: .rpe)
        notes = try c.decodeIfPresent(String.self, forKey: .notes)
        sessionSlot = try c.decodeIfPresent(String.self, forKey: .sessionSlot)
        // Older backends (before the web Phase 1 merge) don't send it.
        isPriority = try c.decodeIfPresent(Bool.self, forKey: .isPriority) ?? false
    }

    /// The web defaults unknown days to Monday; so do we.
    var weekday: Weekday { Weekday(rawValue: dayOfWeek) ?? .monday }
    var isRest: Bool { type == "Rest" || durationMinutes == 0 }
    var isDone: Bool { isCompleted == 1 }
    var isMissedFlag: Bool { isMissed == 1 }
}

struct PlanSnapshot: Codable, Sendable, Equatable {
    let plan: Plan
    var workouts: [Workout]
}

/// GET /api/coach/active-plan and POST /api/coach/select-plan.
/// `{"active": false}` when the athlete has no plan.
struct ActivePlanResponse: Decodable, Sendable {
    let active: Bool
    let plan: Plan?
    let workouts: [Workout]?

    var snapshot: PlanSnapshot? {
        guard active, let plan else { return nil }
        return PlanSnapshot(plan: plan, workouts: workouts ?? [])
    }
}
