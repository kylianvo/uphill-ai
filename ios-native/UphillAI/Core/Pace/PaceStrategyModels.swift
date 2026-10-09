import Foundation

struct CourseCheckpoint: Codable, Sendable, Identifiable, Equatable {
    var id: String { name + "\(distanceMeters)" }
    let name: String
    let distanceMeters: Double
    let elevationMeters: Double
    let segmentGainMeters: Double
    let segmentLossMeters: Double

    init(
        name: String,
        distanceMeters: Double,
        elevationMeters: Double,
        segmentGainMeters: Double,
        segmentLossMeters: Double
    ) {
        self.name = name
        self.distanceMeters = distanceMeters
        self.elevationMeters = elevationMeters
        self.segmentGainMeters = segmentGainMeters
        self.segmentLossMeters = segmentLossMeters
    }

    enum CodingKeys: String, CodingKey {
        case name
        case distanceMeters = "distance_meters"
        case elevationMeters = "elevation_meters"
        case segmentGainMeters = "segment_gain_meters"
        case segmentLossMeters = "segment_loss_meters"
    }
}

struct PacedCheckpoint: Codable, Sendable, Identifiable, Equatable {
    var id: String { name + "\(distanceKm)" }
    let name: String
    let distanceKm: Double
    let elevationM: Double
    let targetPace: String
    let splitTime: String
    let cumulativeTimeMins: Double
    let flatEquivalentKm: Double
    let gradePct: Double
    let effort: String // "run" or "hike"
    let tempC: Double?
    let rainMm: Double?
    let afterSunset: Bool?
    let energyKcal: Int?

    init(
        name: String,
        distanceKm: Double,
        elevationM: Double,
        targetPace: String,
        splitTime: String,
        cumulativeTimeMins: Double,
        flatEquivalentKm: Double,
        gradePct: Double,
        effort: String,
        tempC: Double? = nil,
        rainMm: Double? = nil,
        afterSunset: Bool? = nil,
        energyKcal: Int? = nil
    ) {
        self.name = name
        self.distanceKm = distanceKm
        self.elevationM = elevationM
        self.targetPace = targetPace
        self.splitTime = splitTime
        self.cumulativeTimeMins = cumulativeTimeMins
        self.flatEquivalentKm = flatEquivalentKm
        self.gradePct = gradePct
        self.effort = effort
        self.tempC = tempC
        self.rainMm = rainMm
        self.afterSunset = afterSunset
        self.energyKcal = energyKcal
    }

    enum CodingKeys: String, CodingKey {
        case name
        case distanceKm = "distance_km"
        case elevationM = "elevation_m"
        case targetPace = "target_pace"
        case splitTime = "split_time"
        case cumulativeTimeMins = "cumulative_time_mins"
        case flatEquivalentKm = "flat_equivalent_km"
        case gradePct = "grade_pct"
        case effort
        case tempC = "temp_c"
        case rainMm = "rain_mm"
        case afterSunset = "after_sunset"
        case energyKcal = "energy_kcal"
    }
}

struct PacingRequest: Codable, Sendable {
    let checkpoints: [CourseCheckpoint]
    let targetTimeMins: Double?
    let targetFlatPaceMinKm: Double?
    let splitBias: Double?
    let runnerWeightKg: Double?
    let raceStartIso: String?

    init(
        checkpoints: [CourseCheckpoint],
        targetTimeMins: Double? = nil,
        targetFlatPaceMinKm: Double? = nil,
        splitBias: Double? = nil,
        runnerWeightKg: Double? = nil,
        raceStartIso: String? = nil
    ) {
        self.checkpoints = checkpoints
        self.targetTimeMins = targetTimeMins
        self.targetFlatPaceMinKm = targetFlatPaceMinKm
        self.splitBias = splitBias
        self.runnerWeightKg = runnerWeightKg
        self.raceStartIso = raceStartIso
    }

    enum CodingKeys: String, CodingKey {
        case checkpoints
        case targetTimeMins = "target_time_mins"
        case targetFlatPaceMinKm = "target_flat_pace_min_km"
        case splitBias = "split_bias"
        case runnerWeightKg = "runner_weight_kg"
        case raceStartIso = "race_start_iso"
    }
}

// MARK: - Standalone Pacing Physics Engine (Minetti 2002)

enum PacingCalculator {
    private static let minettiCoeffs = [155.4, -30.4, -43.3, 46.3, 19.5, 3.6]
    private static let flatCost = 3.6
    private static let gradeClamp = 0.45
    private static let descentEfficiency = 0.4
    static let hikeGrade = 0.20
    private static let climbCapGrade = 0.30
    private static let assumedHillGrade = 0.10
    private static let fatigueFreeKm = 15.0
    private static let fatiguePerKm = 0.0015
    private static let joulesPerKcal = 4184.0

    private static func minettiCost(grade: Double) -> Double {
        let i = max(-gradeClamp, min(gradeClamp, grade))
        let a = minettiCoeffs
        return a[0] * pow(i, 5) + a[1] * pow(i, 4) + a[2] * pow(i, 3) + a[3] * pow(i, 2) + a[4] * i + a[5]
    }

    static func gradePaceMultiplier(grade: Double) -> Double {
        var g = grade
        if g > climbCapGrade { g = climbCapGrade }
        let ratio = minettiCost(grade: g) / flatCost
        if g < 0 {
            return 1.0 + (ratio - 1.0) * descentEfficiency
        }
        return ratio
    }

    static func sliderBoundsMins(distanceKm: Double, gainM: Double) -> (min: Double, max: Double) {
        // Fast elite: ~3.8 min/km flat equivalent; Cutoff/Back of pack: ~13 min/km
        let flatEqKm = distanceKm + (gainM / 100.0)
        let minMins = max(30.0, flatEqKm * 3.8)
        let maxMins = max(minMins + 60.0, flatEqKm * 13.0)
        return (minMins, maxMins)
    }

    static func synthesizeCourse(
        distanceKm: Double,
        gainM: Double,
        lossM: Double? = nil,
        baseElevationM: Double = 0.0,
        intervalKm: Double = 1.0
    ) -> [CourseCheckpoint] {
        let loss = lossM ?? gainM
        let n = max(1, Int(ceil(distanceKm / intervalKm)))
        var checkpoints: [CourseCheckpoint] = [
            CourseCheckpoint(
                name: L("Start"),
                distanceMeters: 0,
                elevationMeters: baseElevationM,
                segmentGainMeters: 0,
                segmentLossMeters: 0
            )
        ]

        var currentElevation = baseElevationM
        let gainPerKm = distanceKm > 0 ? (gainM / distanceKm) : 0
        let lossPerKm = distanceKm > 0 ? (loss / distanceKm) : 0

        for i in 1...n {
            let distM = min(Double(i) * intervalKm * 1000.0, distanceKm * 1000.0)
            let prevDistM = checkpoints[i - 1].distanceMeters
            let frac = (distM - prevDistM) / 1000.0
            currentElevation += (gainPerKm - lossPerKm) * frac
            let bump = sin((min(Double(i), Double(n)) / Double(n)) * .pi) * min(gainM, loss) * 0.25

            checkpoints.append(
                CourseCheckpoint(
                    name: "KM \(Int(round(distM / 1000.0)))",
                    distanceMeters: distM,
                    elevationMeters: round(currentElevation + bump),
                    segmentGainMeters: gainPerKm * frac,
                    segmentLossMeters: lossPerKm * frac
                )
            )
        }
        return checkpoints
    }

    static func calculateCheckpointPaces(
        checkpoints: [CourseCheckpoint],
        targetTimeMins: Double? = nil,
        targetFlatPaceMinKm: Double? = nil,
        splitBias: Double = 0.0,
        runnerWeightKg: Double = 68.0
    ) -> [PacedCheckpoint] {
        guard checkpoints.count >= 2 else { return [] }

        let totalDistKm = checkpoints.last!.distanceMeters / 1000.0
        let totalGainM = checkpoints.reduce(0.0) { $0 + $1.segmentGainMeters }

        // Determine base flat pace
        let baseFlatPace: Double
        if let targetFlatPaceMinKm {
            baseFlatPace = targetFlatPaceMinKm
        } else if let targetTimeMins {
            let approxFlatEq = totalDistKm + (totalGainM / 100.0)
            baseFlatPace = max(2.5, min(14.0, targetTimeMins / max(1.0, approxFlatEq)))
        } else {
            baseFlatPace = 5.5
        }

        var paced: [PacedCheckpoint] = []
        var cumTimeMins: Double = 0.0
        var cumFlatEqKm: Double = 0.0
        var totalKcal: Double = 0.0

        for i in 0..<checkpoints.count {
            let cp = checkpoints[i]
            if i == 0 {
                paced.append(
                    PacedCheckpoint(
                        name: cp.name,
                        distanceKm: 0,
                        elevationM: cp.elevationMeters,
                        targetPace: "—",
                        splitTime: "0:00",
                        cumulativeTimeMins: 0,
                        flatEquivalentKm: 0,
                        gradePct: 0,
                        effort: "run",
                        energyKcal: 0
                    )
                )
                continue
            }

            let prev = checkpoints[i - 1]
            let segDistM = cp.distanceMeters - prev.distanceMeters
            let segDistKm = segDistM / 1000.0
            let segGainM = cp.segmentGainMeters
            let segLossM = cp.segmentLossMeters

            // Grade fraction
            let gradeFraction = segDistM > 0 ? (segGainM - segLossM) / segDistM : 0.0
            let gradePct = gradeFraction * 100.0

            // Multipliers
            let gradeMult = gradePaceMultiplier(grade: gradeFraction)

            // Fatigue multiplier
            let fatigueMult = 1.0 + fatiguePerKm * max(0.0, cumFlatEqKm - fatigueFreeKm)

            // Split bias: linear slope from (1 - bias) at start to (1 + bias) at finish
            let progressFrac = totalDistKm > 0 ? (cp.distanceMeters / 1000.0) / totalDistKm : 0.5
            let biasMult = 1.0 + (progressFrac - 0.5) * 2.0 * splitBias

            let segmentPace = baseFlatPace * gradeMult * fatigueMult * biasMult
            let segmentMins = segmentPace * segDistKm
            cumTimeMins += segmentMins

            let segFlatEq = segDistKm * gradeMult
            cumFlatEqKm += segFlatEq

            // Energy expenditure
            let segCost = minettiCost(grade: gradeFraction)
            let segJoules = segCost * segDistM * runnerWeightKg
            totalKcal += segJoules / joulesPerKcal

            let effort = gradeFraction >= hikeGrade ? "hike" : "run"

            paced.append(
                PacedCheckpoint(
                    name: cp.name,
                    distanceKm: round((cp.distanceMeters / 1000.0) * 10) / 10,
                    elevationM: cp.elevationMeters,
                    targetPace: formatPace(segmentPace),
                    splitTime: formatMinutes(segmentMins),
                    cumulativeTimeMins: cumTimeMins,
                    flatEquivalentKm: cumFlatEqKm,
                    gradePct: round(gradePct * 10) / 10,
                    effort: effort,
                    energyKcal: Int(totalKcal)
                )
            )
        }

        return paced
    }

    static func addClockEtas(
        paced: [PacedCheckpoint],
        restMins: [Int: Int] = [:],
        startClock: String = "05:00"
    ) -> [String] {
        let parts = startClock.split(separator: ":").compactMap { Int($0) }
        let startMinutes = (parts.count >= 2) ? (parts[0] * 60 + parts[1]) : 300 // default 05:00 AM

        var restSoFar = 0
        return paced.enumerated().map { idx, cp in
            let arrival = cp.cumulativeTimeMins + Double(restSoFar)
            restSoFar += restMins[idx] ?? 0

            let totalClockMins = Int(Double(startMinutes) + arrival) % (24 * 60)
            let h = totalClockMins / 60
            let m = totalClockMins % 60
            return String(format: "%02d:%02d", h, m)
        }
    }

    static func formatPace(_ paceMinKm: Double) -> String {
        let totalSec = Int(paceMinKm * 60.0)
        let m = totalSec / 60
        let s = totalSec % 60
        return String(format: "%d:%02d", m, s)
    }

    static func formatMinutes(_ minutes: Double) -> String {
        let totalSec = Int(minutes * 60.0)
        let h = totalSec / 3600
        let m = (totalSec % 3600) / 60
        if h > 0 {
            return String(format: "%d:%02d", h, m)
        } else {
            return String(format: "%d min", m)
        }
    }
}
