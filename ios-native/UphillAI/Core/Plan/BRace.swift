import Foundation

/// B-races: tune-up races inside a race plan (backend `services/b_race.py`). The server sends codes and
/// numbers; the app labels them.
enum BRaceLevel: String, Codable, Sendable {
    case good, conditions, risky
    case notRecommended = "not_recommended"

    var title: String {
        switch self {
        case .good: L("Good test")
        case .conditions: L("OK with conditions")
        case .risky: L("Risky")
        case .notRecommended: L("Not recommended")
        }
    }
}

enum BRaceEffort: String, Codable, Sendable { case race, training }

struct BRaceSuggestion: Codable, Sendable, Equatable {
    let distanceKm: Double
    let effort: BRaceEffort

    var label: String {
        let km = "\(distanceKm.formatted(.number.precision(.fractionLength(0...1)))) km"
        return effort == .training ? L("%@ · as a training run", km) : km
    }
}

struct BRaceVerdict: Codable, Sendable, Equatable {
    struct Change: Codable, Sendable, Equatable {
        let week: Int
        let day: String
        let titleBefore: String
        let titleAfter: String
        let minutesBefore: Double
        let minutesAfter: Double
    }
    struct Cost: Codable, Sendable, Equatable { let changed: [Change] }

    let level: BRaceLevel
    let reasons: [String]
    let taperDays: Int
    let recoveryDays: Int
    let suggestion: BRaceSuggestion?
    let cost: Cost?

    static func reasonTitle(_ code: String) -> String {
        switch code {
        case "longer_than_trained": L("Longer than your longest recent run")
        case "too_close": L("Close to your goal race")
        case "overlaps_taper": L("Recovery runs into your goal-race taper")
        case "overlaps_peak": L("Lands on your peak block")
        case "stacked": L("Another race is too close")
        case "base_phase": L("Big for this early in the plan")
        default: code
        }
    }
}

struct BRaceBand: Codable, Sendable, Equatable {
    let lowSec: Int
    let highSec: Int
}

struct BRace: Codable, Sendable, Equatable, Identifiable {
    struct Debrief: Codable, Sendable, Equatable { let text: String? }

    let id: Int
    let raceName: String
    let raceDate: String
    let distanceKm: Double
    let elevationGainM: Double?
    let optionsKm: [Double]?
    let effort: BRaceEffort
    let status: String
    let keptAgainst: String?
    let verdict: BRaceVerdict
    let opinion: String?
    let predicted: BRaceBand?
    let resultSeconds: Int?
    let debrief: Debrief?

    /// The race is past and still waiting for its debrief.
    func needsDebrief(today: Date, calendar: Calendar = PlanCalendar.calendar) -> Bool {
        guard status != "cancelled", debrief?.text == nil, let day = PlanCalendar.day(from: raceDate, calendar: calendar) else { return false }
        return day <= calendar.startOfDay(for: today)
    }
}

/// What the app sends to assess, add or change a race.
struct BRaceInput: Codable, Sendable, Equatable {
    var raceName: String
    var raceDate: String
    var distanceKm: Double?
    var elevationGainM: Double?
    var effort: BRaceEffort = .race
}

/// POST /races/assess: the resolved race and the verdict, before anything is saved.
struct BRaceAssessment: Decodable, Sendable, Equatable {
    struct Resolved: Decodable, Sendable, Equatable {
        let distanceKm: Double
        let elevationGainM: Double?
        let optionsKm: [Double]
    }
    let race: Resolved
    let verdict: BRaceVerdict
    let predicted: BRaceBand?
}

/// Add, change or cancel: the race and the re-plan jobs started for the weeks it touches.
struct BRaceChange: Decodable, Sendable {
    let race: BRace
    let rebuildJobIds: [String]
}

struct BRaceDebriefAnswers: Encodable, Sendable, Equatable {
    var fuel: String?
    var pacing: String?
    var gear: String?
}

struct BRaceDebriefResult: Decodable, Sendable, Equatable {
    struct Goal: Decodable, Sendable, Equatable { let suggestedTargetHours: Double? }
    let debrief: BRace.Debrief
    let goal: Goal
}

extension Int {
    /// 11460 → "3:11:00"
    var raceTime: String { String(format: "%d:%02d:%02d", self / 3600, self % 3600 / 60, self % 60) }
}
