import Foundation

struct ScheduleWarning: Decodable, Sendable, Equatable {
    let code: String
    let params: [String: String]
    init(code: String, params: [String: String]) { self.code = code; self.params = params }
    private enum CodingKeys: String, CodingKey { case code, params }
    private struct Scalar: Decodable {
        let text: String
        init(from decoder: Decoder) throws {
            let c = try decoder.singleValueContainer()
            if let s = try? c.decode(String.self) { text = s }
            else if let n = try? c.decode(Int.self) { text = String(n) }
            else if let n = try? c.decode(Double.self) { text = String(n) }
            else if let b = try? c.decode(Bool.self) { text = String(b) }
            else { text = "" }
        }
    }
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        code = try c.decode(String.self, forKey: .code)
        params = try c.decodeIfPresent([String: Scalar].self, forKey: .params)?.mapValues(\.text) ?? [:]
    }
}

struct CalendarMoveResult: Decodable, Sendable {
    let workouts: [Workout]
    let warnings: [ScheduleWarning]
    init(workouts: [Workout], warnings: [ScheduleWarning] = []) { self.workouts = workouts; self.warnings = warnings }
    private enum CodingKeys: String, CodingKey { case workouts, warnings }
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        workouts = try c.decode([Workout].self, forKey: .workouts)
        warnings = try c.decodeIfPresent([ScheduleWarning].self, forKey: .warnings) ?? []
    }
}

struct ScheduleNotice: Identifiable, Equatable {
    enum Style { case warning, error }
    let id = UUID()
    let text: String
    let style: Style
}

enum ScheduleMessages {
    static func guardText(code: String, params: [String: String] = [:]) -> String {
        let text: String
        switch code {
        case "G1_not_owner": text = L("This workout isn't in your active plan.")
        case "G2_history": text = L("This workout is already completed or matched to an activity, so it can't be moved.")
        case "G3_past_target": text = L("You can't move a workout to a day that has already passed.")
        case "G4_window": text = L("Workouts can only move between this week and next week.")
        case "G5_out_of_plan": text = L("That week is outside your plan.")
        case "G6_coach_linked": text = L("You have a coach — ask them to change your schedule.")
        case "G7_no_dates": text = L("This plan has no start date, so only same-week day swaps are possible.")
        case "STALE_changed": text = L("Your plan changed since this was proposed.")
        case "NOTHING_to_move": text = L("Nothing would change.")
        case "INVALID_operation": text = L("That change isn't valid.")
        default: text = L("That change couldn't be made.")
        }
        return fill(text, params)
    }

    static func warningText(_ warning: ScheduleWarning) -> String {
        var params = warning.params
        let text: String
        switch warning.code {
        case "W1_hard_stacking", "W1_same_day", "W1_before_long_run":
            text = warning.params["kind"] == "before_long_run" || warning.code == "W1_before_long_run"
                ? L("Hard session on {day} (week {week}) right before the long run.")
                : L("Two hard sessions on {day} (week {week}).")
        case "W2_volume_shift":
            text = L("Week {week} volume changes from {before} to {after} min.")
            params["before"] = params["before_minutes"]; params["after"] = params["after_minutes"]
        case "W3_pending_draft": text = L("“{title}” is still pending coach review.")
        default: return warning.code
        }
        return fill(text, params)
    }

    private static func fill(_ text: String, _ params: [String: String]) -> String {
        var text = text
        for (key, raw) in params {
            let value = key == "day" ? Weekday.allCases.first { $0.rawValue == raw || $0.short == raw }?.rawValue ?? raw : raw
            text = text.replacingOccurrences(of: "{\(key)}", with: value)
        }
        return text
    }
}
