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
}
