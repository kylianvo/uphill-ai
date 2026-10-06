import SwiftUI

enum WorkoutTypePresentation {
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

    static func zoneColor(for workout: Workout) -> Color {
        let t = workout.type.lowercased()
        let z = workout.targetZone.lowercased()
        if t.contains("strength") || t.contains("me") || t.contains("muscular") {
            return Color(hex: "#8b5cf6")
        }
        if t.contains("interval") || t.contains("hill") || z.contains("4") || z.contains("5") {
            return Color(hex: "#ef4444")
        }
        if t.contains("tempo") || t.contains("threshold") || z.contains("3") {
            return Color(hex: "#f59e0b")
        }
        if t.contains("long") {
            return Color(hex: "#10b981")
        }
        if t.contains("recovery") || z.contains("1") {
            return Color(hex: "#0ea5e9")
        }
        if t.contains("easy") || z.contains("2") {
            return Color(hex: "#3b82f6")
        }
        if t.contains("cross") {
            return Color(hex: "#14b8a6")
        }
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

    /// Compact pace for the stat tile, whose label already says "(/KM)":
    /// "6:24 - 5:42 /km" -> "6:24–5:42", "5:30 /km" -> "5:30".
    static func paceTileValue(_ pace: String?) -> String {
        guard var value = pace?.trimmingCharacters(in: .whitespacesAndNewlines), !value.isEmpty else { return "—" }
        value = value.replacingOccurrences(of: #"\s*/\s*km\s*$"#, with: "", options: [.regularExpression, .caseInsensitive])
        value = value.replacingOccurrences(of: #"\s*[-–—]\s*"#, with: "–", options: .regularExpression)
        return value.isEmpty ? "—" : value
    }
}
