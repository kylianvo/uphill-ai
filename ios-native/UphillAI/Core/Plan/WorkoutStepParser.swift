import Foundation
import SwiftUI

struct ParsedWorkoutDescription: Equatable, Sendable {
    let overview: String?
    let process: String?
    let benefit: String?    // What it builds
    let warning: String?    // Common mistake
    let coachNotes: String? // Quote
}

enum StepPhase: String, Sendable {
    case warmup = "Warm-up"
    case main = "Main Set"
    case cooldown = "Cool-down"

    var iconName: String {
        switch self {
        case .warmup: "arrow.up.circle.fill"
        case .main: "play.circle.fill"
        case .cooldown: "wind.circle.fill"
        }
    }
}

struct ExecutionStepItem: Identifiable, Equatable, Sendable {
    let id: String
    let phase: StepPhase
    let duration: String?
    let target: String
    let recovery: String?
    let steps: [String]
}

enum WorkoutStepParser {
    // MARK: - Section Extraction

    static func parseDescription(_ text: String?) -> ParsedWorkoutDescription {
        guard let text = text?.trimmingCharacters(in: .whitespacesAndNewlines), !text.isEmpty else {
            return ParsedWorkoutDescription(overview: nil, process: nil, benefit: nil, warning: nil, coachNotes: nil)
        }

        func extract(keyword: String) -> String? {
            let pattern = "(?i)\\b" + keyword + "[:\\-]\\s*([\\s\\S]*?)(?=(Process|Overall|Reason|Benefit|Warning)[:\\-]|$)"
            guard let regex = try? NSRegularExpression(pattern: pattern) else { return nil }
            let nsString = text as NSString
            let matches = regex.matches(in: text, range: NSRange(location: 0, length: nsString.length))
            guard let match = matches.first, match.numberOfRanges > 1 else { return nil }
            let val = nsString.substring(with: match.range(at: 1)).trimmingCharacters(in: .whitespacesAndNewlines)
            return val.isEmpty ? nil : val
        }

        let overall = extract(keyword: "Overall")
        let process = extract(keyword: "Process")
        let reason = extract(keyword: "Reason")
        let benefit = extract(keyword: "Benefit")
        let warning = extract(keyword: "Warning")

        let hasStructured = (overall != nil || process != nil || reason != nil || benefit != nil || warning != nil)

        return ParsedWorkoutDescription(
            overview: overall ?? (hasStructured ? nil : text),
            process: process,
            benefit: benefit ?? reason,
            warning: warning,
            coachNotes: overall ?? reason
        )
    }

    // MARK: - Execution Steps Timeline

    static func parseSteps(workout: Workout, description: ParsedWorkoutDescription, isTreadmill: Bool) -> [ExecutionStepItem] {
        let processText = description.process ?? workout.description ?? ""
        let parts = splitProcess(processText)

        var items: [ExecutionStepItem] = []

        // 1. Warm-up
        let warmupText = parts.warmup ?? defaultWarmup(for: workout)
        if !workout.isRest {
            items.append(ExecutionStepItem(
                id: "warmup",
                phase: .warmup,
                duration: extractMinutes(warmupText) ?? "10–15 min",
                target: isTreadmill ? "Treadmill warm-up at easy jog" : warmupText,
                recovery: nil,
                steps: [warmupText]
            ))
        }

        // 2. Main Set
        let mainTarget: String
        let recovery: String?
        if isTreadmill, let tm = treadmillSettings(workout: workout) {
            mainTarget = "\(tm.speed) · \(tm.incline)"
            recovery = "Maintain stable cadence"
        } else if let reps = workout.intervalReps, reps > 0, let val = workout.intervalRepValue, let unit = workout.intervalRepUnit {
            let paceStr = workout.targetPace.map { " @ \($0)" } ?? ""
            mainTarget = "\(reps) × \(Int(val)) \(unit)\(paceStr)"
            if let walk = workout.walkIntervalValue, walk > 0 {
                recovery = "Recovery: \(Int(walk)) \(unit) jog / walk"
            } else {
                recovery = "Recovery: easy jog between intervals"
            }
        } else {
            mainTarget = workout.targetPace.map { "Target pace: \($0)" } ?? workout.title
            recovery = nil
        }

        let mainDuration: String? = {
            if workout.durationMinutes > 0 {
                let dur = Int(workout.durationMinutes)
                return "\(max(10, dur - 20)) min"
            }
            return nil
        }()

        let mainSteps = parts.main.isEmpty ? [mainTarget] : parts.main
        items.append(ExecutionStepItem(
            id: "main",
            phase: .main,
            duration: mainDuration,
            target: mainTarget,
            recovery: recovery,
            steps: mainSteps
        ))

        // 3. Cool-down
        if !workout.isRest {
            let cooldownText = parts.cooldown ?? "5–10 min easy jog and light stretching"
            items.append(ExecutionStepItem(
                id: "cooldown",
                phase: .cooldown,
                duration: extractMinutes(cooldownText) ?? "5–10 min",
                target: isTreadmill ? "0% grade easy walk to lower HR" : cooldownText,
                recovery: nil,
                steps: [cooldownText]
            ))
        }

        return items
    }

    private static func splitProcess(_ text: String) -> (warmup: String?, main: [String], cooldown: String?) {
        guard !text.isEmpty else { return (nil, [], nil) }

        if text.contains("→") {
            let segments = text.components(separatedBy: "→").map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }.filter { !$0.isEmpty }
            var warmup: String? = nil
            var cooldown: String? = nil
            var main: [String] = []

            for s in segments {
                let lower = s.lowercased()
                if warmup == nil && (lower.contains("warm") || lower.contains("easy jog")) {
                    warmup = s
                } else if lower.contains("cool") || lower.contains("stretch") {
                    cooldown = s
                } else {
                    main.append(s)
                }
            }
            return (warmup, main, cooldown)
        }

        let sentences = text.components(separatedBy: CharacterSet(charactersIn: ".\n")).map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }.filter { !$0.isEmpty }
        var warmup: String? = nil
        var cooldown: String? = nil
        var main: [String] = []

        for s in sentences {
            let lower = s.lowercased()
            if warmup == nil && (lower.contains("warm") || lower.contains("easy jog")) {
                warmup = s
            } else if lower.contains("cool") || lower.contains("stretch") {
                cooldown = s
            } else {
                main.append(s)
            }
        }
        return (warmup, main, cooldown)
    }

    private static func defaultWarmup(for workout: Workout) -> String {
        let t = workout.type.lowercased()
        if t.contains("interval") || t.contains("hill") || t.contains("tempo") {
            return "15 min easy Zone 1/2 jog + 4 dynamic drills"
        }
        return "10 min easy jog to build into effort"
    }

    private static func extractMinutes(_ text: String) -> String? {
        guard let regex = try? NSRegularExpression(pattern: #"(\d+[–\-]\d+\s*min|\d+\s*min)"#, options: .caseInsensitive) else { return nil }
        let ns = text as NSString
        if let match = regex.firstMatch(in: text, range: NSRange(location: 0, length: ns.length)) {
            return ns.substring(with: match.range)
        }
        return nil
    }

    // MARK: - Treadmill Calculation

    static func treadmillSettings(workout: Workout) -> (speed: String, incline: String)? {
        if let s = workout.treadmillSpeed, !s.isEmpty, s != "0",
           let i = workout.treadmillIncline, !i.isEmpty {
            return ("\(s) km/h", "\(i)% grade")
        }

        guard let pace = workout.targetPace, let minPerKm = parsePace(pace) else {
            return ("8.5–10.0 km/h", "1.0% grade")
        }

        let grade = workout.gradePercent ?? 1.0
        let speed = 60.0 / minPerKm / (1.0 + 0.045 * max(0, grade))
        let roundedSpeed = String(format: "%.1f", speed)
        let roundedGrade = String(format: "%.1f", max(1.0, grade))
        return ("\(roundedSpeed) km/h", "\(roundedGrade)% grade")
    }

    private static func parsePace(_ pace: String) -> Double? {
        guard let regex = try? NSRegularExpression(pattern: #"(\d+):(\d{2})"#) else { return nil }
        let ns = pace as NSString
        let matches = regex.matches(in: pace, range: NSRange(location: 0, length: ns.length))
        guard let m = matches.first, m.numberOfRanges >= 3 else { return nil }
        let min = Double(ns.substring(with: m.range(at: 1))) ?? 0
        let sec = Double(ns.substring(with: m.range(at: 2))) ?? 0
        return min + sec / 60.0
    }
}
