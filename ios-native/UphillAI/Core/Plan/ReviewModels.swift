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
    let context: GoalContext?
    let anchors: [GoalAnchor]

    private enum CodingKeys: String, CodingKey { case id, goals, confidence, reasoning, missing, engine, createdAt, context, anchors }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(Int.self, forKey: .id)
        goals = try c.decodeIfPresent(GoalTiers.self, forKey: .goals)
        confidence = try c.decodeIfPresent(String.self, forKey: .confidence)
        // The recorded fixture only has empty arrays, so item shape is unverified: tolerate non-strings.
        reasoning = (try? c.decodeIfPresent([String].self, forKey: .reasoning)) ?? []
        missing = (try? c.decodeIfPresent([String].self, forKey: .missing)) ?? []
        engine = try c.decodeIfPresent(String.self, forKey: .engine)
        context = try c.decodeIfPresent(GoalContext.self, forKey: .context)
        anchors = try c.decodeIfPresent([GoalAnchor].self, forKey: .anchors) ?? []
        createdAt = try c.decodeIfPresent(String.self, forKey: .createdAt)
    }
}

struct GoalContext: Decodable, Sendable, Equatable {
    struct Race: Decodable, Sendable, Equatable {
        let distanceKm: Double?
        let gainM: Double?
        let profileSource: String?
        let field: Field?
    }
    struct Field: Decodable, Sendable, Equatable {
        struct Percentiles: Decodable, Sendable, Equatable {
            let p10: Double?
            let p50: Double?
            let p90: Double?
        }
        let winnerMins: Double?
        let percentileMins: Percentiles?
    }
    struct Athlete: Decodable, Sendable, Equatable {
        let weightKg: Double?
        let thresholdPace: String?
    }
    struct Row: Identifiable {
        let label: String
        let value: String
        var id: String { label }
    }
    struct Group: Identifiable {
        let title: String
        let rows: [Row]
        var id: String { title }
    }
    let race: Race?
    let athlete: Athlete?
    let currentTargetMins: Double?

    @MainActor var groups: [Group] {
        func rows(_ values: [(String, String?)]) -> [Row] {
            values.compactMap { label, value in
                guard let value, !value.isEmpty else { return nil }
                return Row(label: label, value: value)
            }
        }
        func time(_ value: Double?) -> String? {
            guard let value, value != 0 else { return nil }
            return PlanViewModel.formatMinutes(value)
        }
        let profile = race?.profileSource.flatMap { $0.isEmpty ? nil : ($0 == "gpx" ? "GPX" : "Estimated") }
        let pace = athlete?.thresholdPace.flatMap { $0.isEmpty ? nil : $0 + "/km" }
        return [
            Group(title: "Race", rows: rows([
                ("Distance", race?.distanceKm.map { "\(Int($0.rounded())) km" }),
                ("D+", race?.gainM.map { "\(Int($0.rounded())) m" }),
                ("Course profile", profile), ("Time Target", time(currentTargetMins))
            ])),
            Group(title: "Field", rows: rows([
                ("Winner", time(race?.field?.winnerMins)),
                ("10% finished", time(race?.field?.percentileMins?.p10)),
                ("Half finished", time(race?.field?.percentileMins?.p50)),
                ("90% finished", time(race?.field?.percentileMins?.p90))
            ])),
            Group(title: "You", rows: rows([
                ("Weight", athlete?.weightKg.map { $0.formatted(.number) + " kg" }),
                ("Threshold pace", pace)
            ]))
        ].filter { !$0.rows.isEmpty }
    }
}

struct GoalAnchor: Decodable, Sendable, Equatable, Identifiable {
    let id: String
    let method: String
    let minutes: Double

    var methodLabel: String {
        switch method {
        case "physics": "Course physics from this result"
        case "field_rank": "Your finishing rank on this field"
        case "percentile_transfer": "Field percentile transfer"
        case "field_prior": "Field position from weekly volume"
        case "easy_pace": "Course physics from your easy pace"
        case "base_pace": "Course physics from your flat pace"
        default: method
        }
    }
}
