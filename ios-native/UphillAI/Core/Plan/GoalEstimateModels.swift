import Foundation

struct PercentileSet: Codable, Sendable, Equatable {
    let p5: String?
    let p10: String?
    let p25: String?
    let p50: String?
    let p75: String?
    let p90: String?

    init(
        p5: String? = nil,
        p10: String? = nil,
        p25: String? = nil,
        p50: String? = nil,
        p75: String? = nil,
        p90: String? = nil
    ) {
        self.p5 = p5
        self.p10 = p10
        self.p25 = p25
        self.p50 = p50
        self.p75 = p75
        self.p90 = p90
    }
}

struct RaceBenchmark: Codable, Sendable, Identifiable, Equatable {
    var id: Int { year }
    let year: Int
    let finishers: Int?
    let finishersMen: Int?
    let finishersWomen: Int?
    let winnerTime: String?
    let winnerTimeWomen: String?
    let conditionsNote: String?
    let percentiles: [String: PercentileSet]?
    let topTimes: [String: [String: String]]?

    init(
        year: Int,
        finishers: Int? = nil,
        finishersMen: Int? = nil,
        finishersWomen: Int? = nil,
        winnerTime: String? = nil,
        winnerTimeWomen: String? = nil,
        conditionsNote: String? = nil,
        percentiles: [String: PercentileSet]? = nil,
        topTimes: [String: [String: String]]? = nil
    ) {
        self.year = year
        self.finishers = finishers
        self.finishersMen = finishersMen
        self.finishersWomen = finishersWomen
        self.winnerTime = winnerTime
        self.winnerTimeWomen = winnerTimeWomen
        self.conditionsNote = conditionsNote
        self.percentiles = percentiles
        self.topTimes = topTimes
    }
}

struct GoalEstimateTiers: Codable, Sendable, Equatable {
    let ambitious: Double
    let realistic: Double
    let safe: Double

    init(ambitious: Double, realistic: Double, safe: Double) {
        self.ambitious = ambitious
        self.realistic = realistic
        self.safe = safe
    }
}

struct GoalSourceItem: Codable, Sendable, Identifiable, Equatable {
    var id: String { key }
    let key: String
    let label: String
    var included: Bool

    init(key: String, label: String, included: Bool = true) {
        self.key = key
        self.label = label
        self.included = included
    }
}

struct GoalEstimate: Codable, Sendable, Equatable {
    let raceName: String?
    let distanceKm: Double
    let elevationGainM: Double
    let baseFlatPaceMinKm: Double?
    let predictedTimeMins: Double?
    let adjustedTimeMins: Double?
    let improvementPct: Double?
    let goals: GoalEstimateTiers?
    let benchmarks: [RaceBenchmark]?
    let rankTransferMins: Double?
    let percentileTransferMins: Double?
    let targetProfileSource: String?
    let referenceProfileSource: String?
    let referenceConfidence: String?
    let sources: [GoalSourceItem]?
    let reasoning: [String]?

    init(
        raceName: String? = nil,
        distanceKm: Double,
        elevationGainM: Double,
        baseFlatPaceMinKm: Double? = nil,
        predictedTimeMins: Double? = nil,
        adjustedTimeMins: Double? = nil,
        improvementPct: Double? = nil,
        goals: GoalEstimateTiers? = nil,
        benchmarks: [RaceBenchmark]? = nil,
        rankTransferMins: Double? = nil,
        percentileTransferMins: Double? = nil,
        targetProfileSource: String? = nil,
        referenceProfileSource: String? = nil,
        referenceConfidence: String? = nil,
        sources: [GoalSourceItem]? = nil,
        reasoning: [String]? = nil
    ) {
        self.raceName = raceName
        self.distanceKm = distanceKm
        self.elevationGainM = elevationGainM
        self.baseFlatPaceMinKm = baseFlatPaceMinKm
        self.predictedTimeMins = predictedTimeMins
        self.adjustedTimeMins = adjustedTimeMins
        self.improvementPct = improvementPct
        self.goals = goals
        self.benchmarks = benchmarks
        self.rankTransferMins = rankTransferMins
        self.percentileTransferMins = percentileTransferMins
        self.targetProfileSource = targetProfileSource
        self.referenceProfileSource = referenceProfileSource
        self.referenceConfidence = referenceConfidence
        self.sources = sources
        self.reasoning = reasoning
    }

    // MARK: - Computed Math Breakdown Helpers

    var effectiveFlatPace: Double {
        baseFlatPaceMinKm ?? 5.5
    }

    var baseFlatTimeMinutes: Double {
        distanceKm * effectiveFlatPace
    }

    var elevationCostMinutes: Double {
        let total = predictedTimeMins ?? (baseFlatTimeMinutes + (elevationGainM / 100.0) * 4.2)
        return max(0.0, total - baseFlatTimeMinutes)
    }

    var trainingSavingsMinutes: Double {
        let pct = (improvementPct ?? 0.0) / 100.0
        let pred = predictedTimeMins ?? (baseFlatTimeMinutes + elevationCostMinutes)
        return pred * pct
    }

    var climbingPaceTarget: String {
        let climbPace = effectiveFlatPace + max(2.5, min(6.0, (elevationGainM / max(1.0, distanceKm)) * 0.08))
        return String(format: "%.1f min/km", climbPace)
    }

    var flatPaceTarget: String {
        return String(format: "%.1f min/km", effectiveFlatPace)
    }

    var descentPaceTarget: String {
        let desc = max(3.5, effectiveFlatPace * 0.88)
        return String(format: "%.1f min/km", desc)
    }

    var targetAveragePace: String {
        let finish = adjustedTimeMins ?? goals?.realistic ?? predictedTimeMins ?? 330.0
        let avg = finish / max(1.0, distanceKm)
        return String(format: "%.1f min/km", avg)
    }

    /// Parses a pace string formatted as "m:ss" or "mm:ss" (or decimal "5.5") into minutes per kilometer.
    /// E.g. "6:30" -> 6.5, "6:28.5" -> 6.475.
    static func parsePaceToMinutes(_ paceStr: String) -> Double? {
        let trimmed = paceStr.trimmingCharacters(in: .whitespacesAndNewlines)
        let parts = trimmed.split(separator: ":").compactMap { Double($0) }
        if parts.count >= 2 {
            return parts[0] + parts[1] / 60.0
        }
        if let decimal = Double(trimmed), decimal > 0 {
            return decimal
        }
        return nil
    }

    static func parseTimeToMinutes(_ timeStr: String) -> Double? {
        let parts = timeStr.trimmingCharacters(in: .whitespaces).split(separator: ":").compactMap { Double($0) }
        guard parts.count >= 2 else { return nil }
        if parts.count == 3 {
            return parts[0] * 60.0 + parts[1] + parts[2] / 60.0
        } else {
            return parts[0] * 60.0 + parts[1]
        }
    }

    static func formatMinutes(_ minutes: Double) -> String {
        let totalSec = Int(minutes * 60.0)
        let h = totalSec / 3600
        let m = (totalSec % 3600) / 60
        return String(format: "%d:%02d", h, m)
    }
}

struct FieldAnchor: Sendable, Equatable, Identifiable {
    var id: Double { mins }
    let mins: Double
    let percentile: Double // 0 to 100

    init(mins: Double, percentile: Double) {
        self.mins = mins
        self.percentile = percentile
    }
}

struct GoalEstimateRequest: Codable, Sendable {
    var raceName: String?
    var distanceKm: Double?
    var elevationGainM: Double?
    var raceDate: String?
    var flatPaceMinKm: Double?
    var weeksToRace: Double?
    var referenceResultId: Int?
    var referenceRaceName: String?
    var referenceDistanceKm: Double?
    var referenceElevationGainM: Double?
    var referenceTime: String?
    var exclusions: [String]?

    init(
        raceName: String? = nil,
        distanceKm: Double? = nil,
        elevationGainM: Double? = nil,
        raceDate: String? = nil,
        flatPaceMinKm: Double? = nil,
        weeksToRace: Double? = nil,
        referenceResultId: Int? = nil,
        referenceRaceName: String? = nil,
        referenceDistanceKm: Double? = nil,
        referenceElevationGainM: Double? = nil,
        referenceTime: String? = nil,
        exclusions: [String]? = nil
    ) {
        self.raceName = raceName
        self.distanceKm = distanceKm
        self.elevationGainM = elevationGainM
        self.raceDate = raceDate
        self.flatPaceMinKm = flatPaceMinKm
        self.weeksToRace = weeksToRace
        self.referenceResultId = referenceResultId
        self.referenceRaceName = referenceRaceName
        self.referenceDistanceKm = referenceDistanceKm
        self.referenceElevationGainM = referenceElevationGainM
        self.referenceTime = referenceTime
        self.exclusions = exclusions
    }
}
