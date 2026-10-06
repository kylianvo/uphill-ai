import Foundation

struct ParsedWorkoutDescription: Equatable, Sendable {
    let overview: String?
    let process: String?
    let benefit: String?
    let warning: String?
    let coachNotes: String?
}

enum ExecutionStepPhase: String, CaseIterable, Sendable {
    case warmup = "Warm-up"
    case main = "Main Set"
    case cooldown = "Cool-down"

    var iconName: String {
        switch self {
        case .warmup: return "arrow.up.circle.fill"
        case .main: return "play.circle.fill"
        case .cooldown: return "wind.circle.fill"
        }
    }
}
typealias StepPhase = ExecutionStepPhase

struct ExecutionStepItem: Identifiable, Equatable, Sendable {
    let id: String
    let phase: ExecutionStepPhase
    let duration: String?
    let target: String
    let recovery: String?
    let steps: [String]
}

enum WorkoutStepParser {

    // MARK: - Parse Structured Sections

    static func parseDescription(_ raw: String?) -> ParsedWorkoutDescription {
        guard let text = raw?.trimmingCharacters(in: .whitespacesAndNewlines), !text.isEmpty else {
            return ParsedWorkoutDescription(overview: nil, process: nil, benefit: nil, warning: nil, coachNotes: nil)
        }

        func extract(keywords: [String]) -> String? {
            for kw in keywords {
                let pattern = "(?i)(?:^|\\n)\\s*" + NSRegularExpression.escapedPattern(for: kw) + "[:\\-]\\s*([\\s\\S]*?)(?=(?:\\n\\s*(?:Process|Overall|Reason|Benefit|Warning|What it builds|Common mistake|Coach Uphill note|Coach note)[:\\-]|$))"
                if let regex = try? NSRegularExpression(pattern: pattern) {
                    let nsString = text as NSString
                    let matches = regex.matches(in: text, range: NSRange(location: 0, length: nsString.length))
                    if let match = matches.first, match.numberOfRanges > 1 {
                        let val = nsString.substring(with: match.range(at: 1)).trimmingCharacters(in: .whitespacesAndNewlines)
                        if !val.isEmpty { return val }
                    }
                }
            }
            return nil
        }

        let process = extract(keywords: ["Process", "How to execute", "Execution", "Steps"])
        let benefit = extract(keywords: ["What it builds", "Benefit", "Reason", "Builds"])
        let warning = extract(keywords: ["Common mistake", "Warning", "Mistake"])
        let coachNotes = extract(keywords: ["Coach Uphill note", "Coach note", "Overall"])

        let hasStructured = (process != nil || benefit != nil || warning != nil || coachNotes != nil)

        return ParsedWorkoutDescription(
            overview: hasStructured ? nil : text,
            process: process ?? (hasStructured ? nil : text),
            benefit: benefit,
            warning: warning,
            coachNotes: coachNotes
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
            let cleanWarmup = cleanStepText(warmupText, prefix: "warm-up:")
            items.append(ExecutionStepItem(
                id: "warmup",
                phase: .warmup,
                duration: extractMinutes(warmupText) ?? "10–15 min",
                target: isTreadmill ? "Treadmill warm-up at easy jog (0% grade)" : cleanWarmup,
                recovery: nil,
                steps: [cleanWarmup]
            ))
        }

        // 2. Main Set
        let mainTarget: String
        let recovery: String?
        if isTreadmill, let tm = treadmillSettings(workout: workout) {
            mainTarget = "\(tm.speed) · \(tm.incline)"
            recovery = "Maintain stable uphill cadence"
        } else if let reps = workout.intervalReps, reps > 0, let val = workout.intervalRepValue, let unit = workout.intervalRepUnit {
            let paceStr = workout.targetPace.map { " @ \($0)" } ?? ""
            mainTarget = "\(reps) × \(Int(val)) \(unit)\(paceStr)"
            if let walk = workout.walkIntervalValue, walk > 0 {
                recovery = "Recovery: \(Int(walk)) \(unit) jog / walk"
            } else {
                recovery = "Recovery: easy jog between intervals"
            }
        } else if let detectedReps = detectReps(parts.main.first ?? "") {
            mainTarget = detectedReps.reps
            recovery = detectedReps.recovery
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

        let cleanMainSteps = parts.main.map { cleanStepText($0, prefix: "main set:") }
        items.append(ExecutionStepItem(
            id: "main",
            phase: .main,
            duration: mainDuration,
            target: mainTarget,
            recovery: recovery,
            steps: cleanMainSteps.isEmpty ? [mainTarget] : cleanMainSteps
        ))

        // 3. Cool-down
        if !workout.isRest {
            let cooldownText = parts.cooldown ?? "5–10 min easy jog and light mobility"
            let cleanCooldown = cleanStepText(cooldownText, prefix: "cool-down:")
            items.append(ExecutionStepItem(
                id: "cooldown",
                phase: .cooldown,
                duration: extractMinutes(cooldownText) ?? "5–10 min",
                target: isTreadmill ? "0% grade easy walk to lower HR" : cleanCooldown,
                recovery: nil,
                steps: [cleanCooldown]
            ))
        }

        return items
    }

    private static func cleanStepText(_ text: String, prefix: String) -> String {
        var res = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if res.lowercased().hasPrefix(prefix) {
            res = String(res.dropFirst(prefix.count)).trimmingCharacters(in: .whitespacesAndNewlines)
        }
        return res
    }

    private static func detectReps(_ text: String) -> (reps: String, recovery: String?)? {
        let pattern = #"(?i)(\d+\s*[x×]\s*\d+\s*min[^\n,]*)(?:with\s*([^\n.]*))?"#
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return nil }
        let ns = text as NSString
        guard let m = regex.firstMatch(in: text, range: NSRange(location: 0, length: ns.length)), m.numberOfRanges > 1 else { return nil }
        let reps = ns.substring(with: m.range(at: 1)).trimmingCharacters(in: .whitespacesAndNewlines)
        var recovery: String? = nil
        if m.numberOfRanges > 2 && m.range(at: 2).location != NSNotFound {
            recovery = "Recovery: " + ns.substring(with: m.range(at: 2)).trimmingCharacters(in: .whitespacesAndNewlines)
        }
        return (reps, recovery)
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

        let lines = text.components(separatedBy: "\n").map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }.filter { !$0.isEmpty }
        var warmup: String? = nil
        var cooldown: String? = nil
        var main: [String] = []
        var inMetadataSection = false

        for line in lines {
            let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmed.isEmpty { continue }
            let lower = trimmed.lowercased()

            // Skip coach/metadata sections so they do not leak into execution steps
            if lower.hasPrefix("what it builds") ||
               lower.hasPrefix("common mistake") ||
               lower.hasPrefix("coach uphill note") ||
               lower.hasPrefix("coach note") ||
               lower.hasPrefix("coach:") ||
               lower.hasPrefix("benefit:") ||
               lower.hasPrefix("warning:") ||
               lower.hasPrefix("reason:") ||
               lower.hasPrefix("overview:") {
                inMetadataSection = true
                continue
            }

            if inMetadataSection {
                if lower.hasPrefix("warm-up") || lower.hasPrefix("main set") || lower.hasPrefix("cool-down") {
                    inMetadataSection = false
                } else {
                    continue
                }
            }

            if warmup == nil && (lower.hasPrefix("warm-up") || lower.contains("warm up")) {
                warmup = trimmed
            } else if lower.hasPrefix("cool-down") || lower.contains("cool down") {
                cooldown = trimmed
            } else if lower.hasPrefix("main set") {
                main.append(trimmed)
            } else if !main.isEmpty {
                main.append(trimmed)
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
            return ("12.6 km/h", "6.0% grade")
        }

        let grade = workout.gradePercent ?? 6.0
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
