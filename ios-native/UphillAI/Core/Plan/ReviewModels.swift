import Foundation

struct BlockCompletion: Decodable, Sendable, Equatable {
    let blockNumber: Int
    let weekStart: Int
    let weekEnd: Int
    let completionPct: Double
    let unlocked: Bool
}

struct BlockCompletionResponse: Decodable, Sendable {
    let blocks: [BlockCompletion]
    let maxGeneratedWeek: Int
}

struct WeekReview: Decodable, Sendable {
    let weekNumber: Int
    let completionPct: Double
    let checkboxCompletionPct: Double?
    let perWorkout: [WeekReviewEntry]
    let narrative: WeekNarrative?
}

struct WeekReviewEntry: Decodable, Sendable, Identifiable {
    struct Actual: Decodable, Sendable {
        let state: String
        let distanceKm: Double?
        let durationMinutes: Double?
    }

    let workoutId: Int
    let dayOfWeek: String?
    let title: String?
    let type: String?
    let actual: Actual

    var id: Int { workoutId }
}

struct WeekNarrative: Decodable, Sendable {
    let summary: String?
    let highlights: [String]
    let watch: [String]

    private enum CodingKeys: String, CodingKey { case summary, highlights, watch }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        summary = try c.decodeIfPresent(String.self, forKey: .summary)
        highlights = try c.decodeIfPresent([String].self, forKey: .highlights) ?? []
        watch = try c.decodeIfPresent([String].self, forKey: .watch) ?? []
    }
}

struct PlanGoal: Decodable, Sendable, Equatable {
    let assessment: GoalAssessment?
    let status: GoalStatus
    let targetTimeHours: Double?
}

struct GoalStatus: Decodable, Sendable, Equatable {
    enum Kind { case onTrack, ahead, behind, noTarget, notAssessed }

    let state: String
    let suggestedMins: Double?

    var kind: Kind {
        switch state {
        case "on_track": .onTrack
        case "ahead": .ahead
        case "behind": .behind
        case "no_target": .noTarget
        default: .notAssessed
        }
    }
}

/// Minutes for the three tiers: A (stretch), B (target), C (safe).
struct GoalTiers: Decodable, Sendable, Equatable {
    let a: Double
    let b: Double
    let c: Double
}

struct GoalAssessment: Decodable, Sendable, Equatable {
    let id: Int
    let goals: GoalTiers?
    let confidence: String?
    let reasoning: [String]
    let missing: [String]
    let engine: String?
    let createdAt: String?

    private enum CodingKeys: String, CodingKey { case id, goals, confidence, reasoning, missing, engine, createdAt }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(Int.self, forKey: .id)
        goals = try c.decodeIfPresent(GoalTiers.self, forKey: .goals)
        confidence = try c.decodeIfPresent(String.self, forKey: .confidence)
        // The recorded fixture only has empty arrays, so item shape is unverified: tolerate non-strings.
        reasoning = (try? c.decodeIfPresent([String].self, forKey: .reasoning)) ?? []
        missing = (try? c.decodeIfPresent([String].self, forKey: .missing)) ?? []
        engine = try c.decodeIfPresent(String.self, forKey: .engine)
        createdAt = try c.decodeIfPresent(String.self, forKey: .createdAt)
    }
}
