import SwiftUI

enum RowStatus: Equatable { case done, missed, matched, none }

enum WorkoutTypePresentation {
    /// The one status a day row shows beside the type chip.
    static func rowStatus(for workout: Workout) -> RowStatus {
        if workout.isMatched { return .matched }
        if workout.isDone { return .done }
        if workout.isMissedFlag { return .missed }
        return .none
    }

    static func chipLabel(for workout: Workout) -> String {
        let t = workout.type.lowercased()
        if t.contains("interval") || t.contains("hill") { return "Intervals" }
        if t.contains("long") { return "Long" }
        if t.contains("recovery") { return "Recovery" }
        if t.contains("easy") || t.contains("aerobic") { return "Easy" }
        if t.contains("tempo") { return "Tempo" }
        if t.contains("threshold") { return "Threshold" }
        if t.contains("me") || t.contains("muscular") { return "ME" }
        if t.contains("strength") { return "Strength" }
        if t.contains("cross") { return "Cross" }
        if t == "rest" { return "Rest" }
        return workout.type
    }

    /// One effort palette for the whole app. Light values are the 700-weights (>= 3:1 on white, so thin
    /// bars and outlines hold); Recovery is cyan so it parts from Easy. Dark values are the lighter 400s.
    static func zoneColor(for workout: Workout) -> Color {
        // Colour follows the chip the athlete reads, so every "Easy" is the same blue whatever zone range it targets.
        switch chipLabel(for: workout) {
        case "Intervals": return Color(light: "#dc2626", dark: "#f87171")
        case "Long": return Color(light: "#047857", dark: "#34d399")
        case "Recovery": return Color(light: "#0e7490", dark: "#22d3ee")
        case "Easy": return Color(light: "#3b82f6", dark: "#60a5fa")
        case "Tempo", "Threshold": return Color(light: "#b45309", dark: "#fbbf24")
        case "ME", "Strength": return Color(light: "#7c3aed", dark: "#a78bfa")
        case "Cross": return Color(light: "#0f766e", dark: "#2dd4bf")
        default: break
        }
        // Unrecognised type: fall back to the target zone.
        let z = workout.targetZone.lowercased()
        if z.contains("4") || z.contains("5") { return Color(light: "#dc2626", dark: "#f87171") }
        if z.contains("3") { return Color(light: "#b45309", dark: "#fbbf24") }
        if z.contains("1") { return Color(light: "#0e7490", dark: "#22d3ee") }
        if z.contains("2") { return Color(light: "#3b82f6", dark: "#60a5fa") }
        return Color(hex: "#6b7280")
    }

    static func formatMetrics(for workout: Workout) -> String {
        var parts: [String] = []
        if workout.durationMinutes > 0 {
            parts.append("\(Int(workout.durationMinutes)) min")
        }
        if let km = workout.distanceKm, km > 0 {
            let kmText = km.formatted(.number.precision(.fractionLength(0...1)).locale(Locale(identifier: "en_US_POSIX")))
            parts.append("\(kmText) km")
        }
        if let pace = workout.targetPace, !pace.isEmpty {
            parts.append(pace)
        } else if let gain = workout.elevationGainM, gain > 0 {
            parts.append("+\(Int(gain)) m")
        }
        return parts.joined(separator: " · ")
    }

    // MARK: - Zone & pace text

    /// "Zone 2" from any of the shapes the backend sends ("Z2", "Zone 2", "2", "1-2").
    /// Non-numeric zones ("Recovery") pass through; "Rest"/empty give nil. Never doubles the word.
    static func zoneLabel(_ raw: String) -> String? {
        let trimmed = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        if let n = zoneNumber(trimmed) { return "Zone \(n)" }
        return trimmed.isEmpty || trimmed.lowercased() == "rest" ? nil : trimmed
    }

    /// "Z2" for compact comparisons; nil when the zone has no number.
    static func zoneShort(_ raw: String) -> String? {
        zoneNumber(raw.trimmingCharacters(in: .whitespacesAndNewlines)).map { "Z\($0)" }
    }

    private static func zoneNumber(_ trimmed: String) -> String? {
        var rest = Substring(trimmed.lowercased())
        if rest.hasPrefix("zone") { rest = rest.dropFirst(4) } else if rest.hasPrefix("z") { rest = rest.dropFirst(1) }
        let value = rest.trimmingCharacters(in: .whitespaces)
        guard let first = value.first, first.isNumber else { return nil }
        return value
    }

    static func sessionPaceValue(for workout: Workout) -> String {
        let aerobic = ["Easy", "Long Run"].contains(workout.type) && zoneShort(workout.targetZone) != "Z5"
        if workout.isStrengthOrME || (WorkoutStepParser.hidesRepPace(workout) && !aerobic) { return "—" }
        return paceTileValue(workout.targetPace)
    }

    /// Compact pace for the stat tile, whose label already says "(/KM)":
    /// "6:24 - 5:42 /km" -> "6:24–5:42", "5:30 /km" -> "5:30".
    static func paceTileValue(_ pace: String?) -> String {
        guard var value = pace?.trimmingCharacters(in: .whitespacesAndNewlines), !value.isEmpty else { return "—" }
        value = value.replacingOccurrences(of: #"\s*/\s*km\s*$"#, with: "", options: [.regularExpression, .caseInsensitive])
        value = value.replacingOccurrences(of: #"\s*[-–—]\s*"#, with: "–", options: .regularExpression)
        return value.isEmpty ? "—" : value
    }
}
