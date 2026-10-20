import Foundation

/// Whether the athlete's week, runway and training venue can hold the goal (services/goal_feasibility.py).
struct GoalFeasibility: Decodable, Sendable, Equatable {
    let verdict: String  // supported | stretch | unsupported
    let capacityH: Double
    let neededH: Double
    let weeksNeeded: Int?
    let levers: [String]
    let confidence: String  // measured | estimated
}

/// How much of the improvement the goals assume the plan delivers (services/plan_adequacy.py).
struct PlanSupport: Decodable, Sendable, Equatable {
    let aSupported: Bool
    let shortfallPct: Double
    let improvementAssumedPct: Double
    let improvementSupportedPct: Double
}

/// What the Goal sheet tells the athlete about the plan carrying the goal. Nothing when it can.
struct GoalPlanCheck: Equatable {
    enum Tone { case tight, short }

    let tone: Tone
    let title: String
    let line: String
    let levers: [String]
    let note: String?
}

extension GoalFeasibility {
    private static let maxLevers = 2

    var check: GoalPlanCheck? {
        let tone: GoalPlanCheck.Tone
        let title: String
        switch verdict {
        case "unsupported": (tone, title) = (.short, L("Not enough room in your week"))
        case "stretch": (tone, title) = (.tight, L("Possible, but tight"))
        default: return nil
        }
        return GoalPlanCheck(
            tone: tone,
            title: title,
            line: L("Your week holds about %@h; this goal needs about %@h.", RaceDisplay.number(capacityH), RaceDisplay.number(neededH)),
            levers: levers.compactMap(leverText).prefix(Self.maxLevers).map { $0 },
            note: confidence == "estimated" ? L("Pace is estimated.") : nil
        )
    }

    private func leverText(_ lever: String) -> String? {
        switch lever {
        case "more_days": L("More training days would close the gap.")
        case "double_sessions": L("Double sessions would help.")
        case "more_weeks": weeksNeeded.map { L("Reaching peak week takes about %lld weeks.", $0) } ?? L("It needs more weeks before the race.")
        case "shorter_race": L("A shorter race would fit better.")
        case "finish_only": L("Treat it as a finish-only goal.")
        case "steeper_venue": L("Train on a steeper mountain to rehearse the climbing.")
        case "mountain_access": L("Add mountain trips, or stair and treadmill climbing.")
        case "fewer_mountain_minimum": L("Your mountain Long Run minimum does not fit your week.")
        default: nil
        }
    }
}

extension GoalAssessment {
    /// One line when the plan cannot back the improvement the goals assume; nil when it can.
    var planSupportNotice: String? {
        guard let support = planSupport, !support.aSupported else { return nil }
        return L(
            "Goals moved %@%% later: the plan delivers %@%% of the %@%% improvement they assume.",
            RaceDisplay.number(support.shortfallPct),
            RaceDisplay.number(support.improvementSupportedPct),
            RaceDisplay.number(support.improvementAssumedPct)
        )
    }
}

/// Is the athlete getting faster on the path to B and A (`services/aerobic_speed.py`)?
struct GoalPath: Decodable, Sendable, Equatable {
    let b: String  // ahead | on | behind
    let a: String
    let measuredPct: Double
    let expectedPct: Double
    let weeks: Int
    let confidence: String  // low | medium | high

    static func word(_ status: String) -> String {
        switch status {
        case "ahead": L("ahead")
        case "on": L("on track")
        default: L("behind")
        }
    }

    var line: String {
        measuredPct >= 0
            ? L("Aerobic speed is %@%% faster than at the start.", RaceDisplay.number(measuredPct))
            : L("Aerobic speed is %@%% slower than at the start.", RaceDisplay.number(-measuredPct))
    }

    var note: String? { confidence == "low" ? L("Early read: only a few weeks of runs.") : nil }
}
