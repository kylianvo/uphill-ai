import Foundation

/// Phases, milestones and schedule fit for the plan screen (`services/plan_journey.py`).
struct PlanJourney: Decodable, Sendable, Equatable {
    struct Phase: Decodable, Sendable, Equatable, Identifiable {
        let name: String
        let startWeek: Int
        let endWeek: Int
        var id: Int { startWeek }
        var weeks: Int { endWeek - startWeek + 1 }
    }

    struct Milestone: Decodable, Sendable, Equatable, Identifiable {
        let key: String
        let week: Int
        let done: Bool
        var id: String { key }

        var title: String {
            switch key {
            case "long_run_3h": L("First 3-hour Long Run")
            case "first_recovery_week": L("First recovery week")
            case "peak_week": L("Peak week")
            case "taper_start": L("Taper starts")
            case "race_week": L("Race week")
            default: key
            }
        }
    }

    struct Preferences: Decodable, Sendable, Equatable {
        let daysPerWeek: Int?
        let longRunDay: String?
        let mountain: String?
    }

    struct Deviation: Decodable, Sendable, Equatable {
        let code: String
        let week: Int
    }

    let currentWeek: Int
    let totalWeeks: Int
    let daysToRace: Int?
    let phases: [Phase]
    let milestones: [Milestone]
    let preferences: Preferences
    let deviations: [Deviation]

    var nextMilestone: Milestone? { milestones.first { !$0.done } }

    /// "4 days a week · long run Sat · Mountain training": what the plan is built around.
    var builtAroundYou: String {
        var parts: [String] = []
        if let days = preferences.daysPerWeek { parts.append(L("%lld days a week", days)) }
        if let day = preferences.longRunDay.flatMap(Weekday.init(rawValue:)) {
            parts.append(L("long run %@", day.localizedShort))
        }
        if preferences.mountain != nil { parts.append(L("Mountain training")) }
        return parts.joined(separator: " · ")
    }

    var followsSchedule: Bool { deviations.isEmpty }
}

/// The one coach message on the plan screen (`services/coach_nudge.py`); absent when there is nothing to say.
struct CoachNudge: Decodable, Sendable, Equatable {
    enum Tone: String, Sendable { case encourage, push, headsUp = "heads_up" }

    let tone: String
    let text: String
    var kind: Tone { Tone(rawValue: tone) ?? .encourage }
}

struct CoachNudgeResponse: Decodable, Sendable {
    let nudge: CoachNudge?
}

extension Weekday {
    /// "Sat" / "T7", in the app language rather than the device region.
    var localizedShort: String {
        var calendar = Calendar(identifier: .gregorian)
        calendar.locale = AppLanguage.current.locale
        let symbols = calendar.shortWeekdaySymbols  // Sunday first
        return symbols[(offset + 1) % 7]
    }
}
