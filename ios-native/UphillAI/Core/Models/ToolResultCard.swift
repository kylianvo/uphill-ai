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

struct ScheduleProposalCardData: Codable, Sendable, Equatable {
    let proposalId: Int?
    let status: String?
    let rationale: String?
    let warnings: [String]?
    let diff: [String: JSONValue]?

    init(
        proposalId: Int? = nil,
        status: String? = "proposed",
        rationale: String? = nil,
        warnings: [String]? = nil,
        diff: [String: JSONValue]? = nil
    ) {
        self.proposalId = proposalId
        self.status = status
        self.rationale = rationale
        self.warnings = warnings
        self.diff = diff
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
