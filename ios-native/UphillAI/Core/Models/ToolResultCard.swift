import Foundation

struct WeekScheduleCardData: Codable, Sendable, Equatable {
    let weekNumber: Int?
    let totalDistanceKm: Double?
    let totalElevationGainM: Double?
    let workouts: [Workout]?

    init(
        weekNumber: Int? = nil,
        totalDistanceKm: Double? = nil,
        totalElevationGainM: Double? = nil,
        workouts: [Workout]? = nil
    ) {
        self.weekNumber = weekNumber
        self.totalDistanceKm = totalDistanceKm
        self.totalElevationGainM = totalElevationGainM
        self.workouts = workouts
    }
}

struct WeekReviewCardData: Codable, Sendable, Equatable {
    let weekNumber: Int?
    let plannedDistanceKm: Double?
    let actualDistanceKm: Double?
    let compliancePercent: Double?
    let summary: String?

    init(
        weekNumber: Int? = nil,
        plannedDistanceKm: Double? = nil,
        actualDistanceKm: Double? = nil,
        compliancePercent: Double? = nil,
        summary: String? = nil
    ) {
        self.weekNumber = weekNumber
        self.plannedDistanceKm = plannedDistanceKm
        self.actualDistanceKm = actualDistanceKm
        self.compliancePercent = compliancePercent
        self.summary = summary
    }
}

struct PacingSplitRow: Codable, Sendable, Equatable, Identifiable {
    var id: String { checkpoint }
    let checkpoint: String
    let distanceKm: Double?
    let targetPace: String?
    let elevationGainM: Double?
    let elapsedTarget: String?

    init(
        checkpoint: String,
        distanceKm: Double? = nil,
        targetPace: String? = nil,
        elevationGainM: Double? = nil,
        elapsedTarget: String? = nil
    ) {
        self.checkpoint = checkpoint
        self.distanceKm = distanceKm
        self.targetPace = targetPace
        self.elevationGainM = elevationGainM
        self.elapsedTarget = elapsedTarget
    }
}

struct PacingSplitsCardData: Codable, Sendable, Equatable {
    let raceName: String?
    let distanceLabel: String?
    let totalDistanceKm: Double?
    let splits: [PacingSplitRow]?

    init(
        raceName: String? = nil,
        distanceLabel: String? = nil,
        totalDistanceKm: Double? = nil,
        splits: [PacingSplitRow]? = nil
    ) {
        self.raceName = raceName
        self.distanceLabel = distanceLabel
        self.totalDistanceKm = totalDistanceKm
        self.splits = splits
    }
}

/// The few workout fields the chat cards show (the full Workout model is too strict for drafts).
struct ProposalWorkout: Codable, Sendable, Equatable {
    let title: String?
    let type: String?
    let durationMinutes: Double?
    let distanceKm: Double?
}

/// One moved workout in a schedule_proposal diff.
struct ProposalMove: Codable, Sendable, Equatable {
    let workoutId: Int?
    let fromWeek: Int?
    let fromDay: String?
    let toWeek: Int?
    let toDay: String?
    let workout: ProposalWorkout?
}

struct ScheduleProposalCardData: Decodable, Sendable, Equatable {
    let proposalId: Int?
    let status: String?
    let rationale: String?
    let warnings: [ScheduleWarning]?
    let diff: [ProposalMove]?
    /// Rebuild cards only.
    let week: Int?
    let fromDay: String?

    init(
        proposalId: Int? = nil,
        status: String? = "proposed",
        rationale: String? = nil,
        warnings: [ScheduleWarning]? = nil,
        diff: [ProposalMove]? = nil,
        week: Int? = nil,
        fromDay: String? = nil
    ) {
        self.proposalId = proposalId
        self.status = status
        self.rationale = rationale
        self.warnings = warnings
        self.diff = diff
        self.week = week
        self.fromDay = fromDay
    }
}

struct RebuildTotals: Codable, Sendable, Equatable {
    let min: Double?
    let km: Double?
    let vert: Double?
}

struct RebuildDay: Codable, Sendable, Equatable {
    let day: String
    let kept: [ProposalWorkout]
    let before: [ProposalWorkout]
    let after: [ProposalWorkout]
}

struct RebuildDiff: Codable, Sendable, Equatable {
    struct Totals: Codable, Sendable, Equatable {
        let before: RebuildTotals
        let after: RebuildTotals
    }
    let week: Int?
    let fromDay: String?
    let days: [RebuildDay]
    let totals: Totals?
}

/// GET /api/coach/chat/proposals/{id}. `diff` is `{}` until a rebuild draft is ready.
struct ProposalDetail: Decodable, Sendable, Equatable {
    let id: Int
    let kind: String?
    let status: String
    let rebuild: RebuildDiff?
    let warnings: [ScheduleWarning]?
    let staleReason: String?

    enum CodingKeys: String, CodingKey { case id, kind, status, diff, warnings, staleReason }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(Int.self, forKey: .id)
        kind = try? c.decode(String.self, forKey: .kind)
        status = try c.decode(String.self, forKey: .status)
        rebuild = try? c.decode(RebuildDiff.self, forKey: .diff)
        warnings = try? c.decode([ScheduleWarning].self, forKey: .warnings)
        staleReason = try? c.decode(String.self, forKey: .staleReason)
    }

    init(id: Int, status: String, rebuild: RebuildDiff? = nil) {
        self.id = id
        self.kind = nil
        self.status = status
        self.rebuild = rebuild
        self.warnings = nil
        self.staleReason = nil
    }
}

extension ToolResultPayload {
    func decodeWeekSchedule() -> WeekScheduleCardData? {
        guard let cardData else { return nil }
        guard let data = try? JSONEncoder().encode(cardData) else { return nil }
        return try? JSONCoding.decoder.decode(WeekScheduleCardData.self, from: data)
    }

    func decodeWeekReview() -> WeekReviewCardData? {
        guard let cardData else { return nil }
        guard let data = try? JSONEncoder().encode(cardData) else { return nil }
        return try? JSONCoding.decoder.decode(WeekReviewCardData.self, from: data)
    }

    func decodePacingSplits() -> PacingSplitsCardData? {
        guard let cardData else { return nil }
        guard let data = try? JSONEncoder().encode(cardData) else { return nil }
        return try? JSONCoding.decoder.decode(PacingSplitsCardData.self, from: data)
    }

    func decodeScheduleProposal() -> ScheduleProposalCardData? {
        guard let cardData else { return nil }
        guard let data = try? JSONEncoder().encode(cardData) else { return nil }
        return try? JSONCoding.decoder.decode(ScheduleProposalCardData.self, from: data)
    }
}

extension ToolResultPayload {
    func decodeNutritionPlan() -> NutritionPlan? {
        guard let cardData else { return nil }
        guard let data = try? JSONEncoder().encode(cardData) else { return nil }
        return try? JSONCoding.decoder.decode(NutritionPlan.self, from: data)
    }

    func decodeGearPlan() -> GearPlan? {
        guard let cardData else { return nil }
        guard let data = try? JSONEncoder().encode(cardData) else { return nil }
        return try? JSONCoding.decoder.decode(GearPlan.self, from: data)
    }

    func decodeGoalEstimate() -> GoalEstimate? {
        guard let cardData else { return nil }
        guard let data = try? JSONEncoder().encode(cardData) else { return nil }
        return try? JSONCoding.decoder.decode(GoalEstimate.self, from: data)
    }
}
