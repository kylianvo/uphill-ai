import Foundation

struct ParsedWorkoutDescription: Equatable, Sendable {
    let overview: String?
    let process: String?
    let benefit: String?
    let warning: String?
    let coachNotes: String?
    /// The "Overall:" line: what the session is for.
    var intent: String? = nil
    var reason: String? = nil
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

        var sections: [Section: [String]] = [:]
        var free: [String] = []
        var current: Section?
        var sawLabel = false

        for segment in segments(of: text) {
            if let (section, body) = label(of: segment) {
                sawLabel = true
                current = section
                if !body.isEmpty { sections[section, default: []].append(body) }
            } else if let current, current == .process || !isStepLike(segment) {
                // A labelled paragraph wrapped over several lines; steps never belong to a note.
                sections[current, default: []].append(segment)
            } else {
                current = nil
                free.append(segment)
            }
        }

        func joined(_ section: Section) -> String? {
            let value = sections[section]?.joined(separator: "\n").trimmingCharacters(in: .whitespacesAndNewlines)
            return value?.isEmpty == false ? value : nil
        }

        guard sawLabel else {
            return ParsedWorkoutDescription(overview: text, process: text, benefit: nil, warning: nil, coachNotes: nil)
        }
        return ParsedWorkoutDescription(
            overview: nil,
            process: joined(.process) ?? (free.isEmpty ? nil : free.joined(separator: "\n")),
            benefit: joined(.builds),
            warning: joined(.warning),
            coachNotes: joined(.coach),
            intent: joined(.intent),
            reason: joined(.reason)
        )
    }

    // MARK: - Segments & labels

    private enum Section { case process, builds, warning, coach, intent, reason }

    /// Longest keywords first so "coach uphill note" wins over "coach".
    private static let labels: [(String, Section)] = [
        ("coach uphill note", .coach), ("coach note", .coach), ("coach", .coach),
        ("what it builds", .builds), ("benefit", .builds), ("builds", .builds),
        ("reason", .reason), ("why", .reason),
        ("common mistake", .warning), ("warning", .warning), ("mistake", .warning),
        ("how to execute", .process), ("process", .process), ("execution", .process), ("steps", .process),
        ("overall", .intent), ("overview", .intent),
        // Vietnamese plans: the server's copy lexicon rewrites the English labels to these.
        ("tổng quan", .intent), ("lý do", .reason), ("lợi ích", .builds), ("lưu ý", .warning), ("cách làm", .process),
    ]

    /// Descriptions arrive with sections separated by newlines or by " / ".
    static func stripSectionMetadata(_ text: String) -> String {
        let pattern = #"(?i)\s*(?:\b(?:overall|overview|reason|why|benefit|builds|what it builds|warning|common mistake|mistake|coach note|coach uphill note|tổng quan|lý do|lợi ích|lưu ý)\s*[:\-]).*$"#
        return text.replacingOccurrences(of: pattern, with: "", options: .regularExpression).trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private static func segments(of text: String) -> [String] {
        let keywordPattern = #"(?i)(?<=[.!?;]|\s)\s*(?=(?:overall|overview|reason|why|benefit|builds|what it builds|warning|common mistake|mistake|coach note|coach uphill note|process|execution|steps|tổng quan|lý do|lợi ích|lưu ý|cách làm)\s*[:\-])"#
        let normalized = text
            .replacingOccurrences(of: keywordPattern, with: "\n", options: .regularExpression)
            .replacingOccurrences(of: #"\s+/\s+"#, with: "\n", options: .regularExpression)
        return normalized
            .components(separatedBy: .newlines)
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    }

    /// "Reason: Acts as…" -> (.builds, "Acts as…"); nil when the segment has no section label.
    private static func label(of segment: String) -> (Section, String)? {
        for (keyword, section) in labels {
            guard let range = segment.range(of: keyword, options: [.caseInsensitive, .anchored]) else { continue }
            let rest = segment[range.upperBound...].drop(while: { $0 == " " })
            guard let separator = rest.first, separator == ":" || separator == "-" else { continue }
            return (section, rest.dropFirst().trimmingCharacters(in: .whitespacesAndNewlines))
        }
        return nil
    }

    /// A line that is part of the workout itself rather than a note about it.
    private static func isStepLike(_ segment: String) -> Bool {
        let lower = segment.lowercased()
        if lower.hasPrefix("warm") || lower.hasPrefix("main set") || lower.hasPrefix("cool")
            || lower.hasPrefix("target pace") { return true }
        return lower.range(of: #"^\d+(?:[–\-]\d+)?\s*(?:min(?:ute)?s?|km|m|sec|s|x|×)\b"#, options: .regularExpression) != nil
    }

    // MARK: - Execution Steps Timeline

    static func parseSteps(workout: Workout, description: ParsedWorkoutDescription, isTreadmill: Bool) -> [ExecutionStepItem] {
        let extracted = WorkoutDescriptionParser.extractDescriptionSections(workout.description ?? "")
        let processText: String
        if let p = description.process, !p.isEmpty {
            processText = p
        } else if let ep = extracted.process, !ep.isEmpty {
            processText = ep
        } else if extracted.overall != nil || extracted.reason != nil || extracted.benefit != nil || extracted.warning != nil {
            processText = ""
        } else {
            processText = workout.description ?? ""
        }
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
        let detectedReps = parts.main.compactMap { detectReps($0) }.first
        let isIntervalSet = (workout.intervalReps ?? 0) > 0 || detectedReps != nil
        if isTreadmill, let tm = treadmillSettings(workout: workout) {
            mainTarget = "\(tm.speed) · \(tm.incline)"
            recovery = "Maintain stable uphill cadence"
        } else if let reps = workout.intervalReps, reps > 0, let val = workout.intervalRepValue, let unit = workout.intervalRepUnit {
            let paceStr = hidesRepPace(workout) ? "" : (workout.targetPace.map { " @ \($0)" } ?? "")
            mainTarget = "\(reps) × \(fmtRepValue(val)) \(unit)\(paceStr)"
            if let walk = workout.walkIntervalValue, walk > 0 {
                recovery = "Recovery: \(fmtRepValue(walk)) \(unit) jog / walk"
            } else {
                recovery = "Recovery: easy jog between intervals"
            }
        } else if let detectedReps {
            mainTarget = detectedReps.reps
            recovery = detectedReps.recovery
        } else {
            if !workout.isStrengthOrME, let pace = workout.targetPace?.trimmingCharacters(in: .whitespacesAndNewlines), !pace.isEmpty {
                mainTarget = "Target pace: \(pace)"
            } else {
                mainTarget = workout.title
            }
            recovery = nil
        }

        // The description's own number wins (an explicit "25 min steady…" line); only when it
        // states none do we fall back to total minus warm-up and cool-down.
        let mainDuration: String? = {
            if !isIntervalSet, let stated = leadingMinutes(of: parts.main.first) { return stated }
            guard workout.durationMinutes > 0 else { return nil }
            let warm = firstNumber(in: extractMinutes(warmupText)) ?? 10
            let cool = firstNumber(in: extractMinutes(parts.cooldown ?? "")) ?? 5
            return "\(max(5, Int(workout.durationMinutes) - warm - cool)) min"
        }()

        let cleanMainSteps = parts.main
            .filter { line in
                let lower = line.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
                return !lower.hasPrefix("overall:") && !lower.hasPrefix("reason:") && !lower.hasPrefix("why:") && !lower.hasPrefix("benefit:") && !lower.hasPrefix("warning:")
            }
            .map { cleanStepText($0, prefix: "main set:") }
            .filter { !$0.isEmpty }
        // A run with strides, or a gym session, written as "→" steps: one card per step, so the steady
        // running and the strides (or each exercise) read separately. Interval and treadmill views keep one card.
        let ownCards = processText.contains("→") && cleanMainSteps.count >= 2 && !isTreadmill
            && (workout.intervalReps ?? 0) == 0
            && !cleanMainSteps.contains { $0.lowercased().hasPrefix("target pace") }
        if ownCards {
            for (index, step) in cleanMainSteps.enumerated() {
                let reps = detectReps(step)
                items.append(ExecutionStepItem(
                    id: "main-\(index)",
                    phase: .main,
                    duration: reps != nil ? nil : leadingMinutes(of: step)
                        ?? (step.range(of: #"(?i)rest|nghỉ"#, options: .regularExpression) == nil ? extractMinutes(step) : nil),
                    target: reps?.reps ?? step,
                    recovery: reps?.recovery,
                    // the recovery has its own line: "6 × 15 s strides with easy jog back" -> "6 × 15 s strides"
                    steps: [reps?.recovery == nil ? step : (step.components(separatedBy: " with ").first ?? step)]
                ))
            }
        } else {
        items.append(ExecutionStepItem(
            id: "main",
            phase: .main,
            duration: mainDuration,
            target: mainTarget,
            recovery: recovery,
            steps: cleanMainSteps.isEmpty ? [mainTarget] : cleanMainSteps
        ))
        }

        // 3. Cool-down
        if !workout.isRest {
            let cooldownText = parts.cooldown ?? "5–10 min easy jog and light mobility"
            let cleanCooldown = cleanStepText(cooldownText, prefix: "cool-down:")
            let dur = extractMinutes(cleanCooldown) ?? extractMinutes(cooldownText) ?? "5–10 min"
            items.append(ExecutionStepItem(
                id: "cooldown",
                phase: .cooldown,
                duration: dur,
                target: isTreadmill ? "0% grade easy walk to lower HR" : cleanCooldown,
                recovery: nil,
                steps: [cleanCooldown]
            ))
        }

        return items
    }

    private static func cleanStepText(_ text: String, prefix: String) -> String {
        var res = stripSectionMetadata(text).trimmingCharacters(in: .whitespacesAndNewlines)
        if res.lowercased().hasPrefix(prefix) {
            res = String(res.dropFirst(prefix.count)).trimmingCharacters(in: .whitespacesAndNewlines)
        }
        return res
    }

    static func hidesRepPace(_ workout: Workout) -> Bool {
        let zone = workout.targetZone.lowercased().replacingOccurrences(of: " ", with: "")
        return zone == "zone5" || zone == "z5"
            || workout.title.range(of: #"(?i)hill[ -]?sprints?|strides"#, options: .regularExpression) != nil
    }

    private static func fmtRepValue(_ value: Double) -> String {
        String(format: value.rounded() == value ? "%.0f" : "%.1f", value)
    }

    private static func detectReps(_ text: String) -> (reps: String, recovery: String?)? {
        let pattern = #"(?i)(?<![\d.\-])(\d+)\s*(?:[x×]|reps?\s+of)\s*(\d+(?:\.\d+)?)\s*-?\s*(seconds?|secs?|s|min(?:utes?)?|phút|giây|km|m)\b(?:[^\n,]*?\bwith\s+([^\n.]*))?"#
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return nil }
        let ns = text as NSString
        guard let m = regex.firstMatch(in: text, range: NSRange(location: 0, length: ns.length)),
              let count = Int(ns.substring(with: m.range(at: 1))), count > 0,
              let value = Double(ns.substring(with: m.range(at: 2))), value > 0 else { return nil }
        let rawUnit = ns.substring(with: m.range(at: 3)).lowercased()
        let unit = rawUnit == "phút" || rawUnit.hasPrefix("min") ? "min"
            : (rawUnit == "giây" || rawUnit.hasPrefix("s") ? "s" : rawUnit)
        let recovery = m.range(at: 4).location == NSNotFound ? nil
            : "Recovery: " + ns.substring(with: m.range(at: 4)).trimmingCharacters(in: .whitespacesAndNewlines)
        return ("\(count) × \(fmtRepValue(value)) \(unit)", recovery)
    }

    static func splitProcess(_ text: String) -> (warmup: String?, main: [String], cooldown: String?) {
        guard !text.isEmpty else { return (nil, [], nil) }

        if text.contains("→") {
            let segments = text.components(separatedBy: "→").map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }.filter { !$0.isEmpty }
            var warmup: String? = nil
            var cooldown: String? = nil
            var main: [String] = []

            for s in segments {
                let lower = s.lowercased()
                if warmup == nil && (lower.contains("warm") || lower.contains("easy jog") || lower.contains("khởi động")) {
                    warmup = s
                // Vietnamese cues must lead the step: "thả lỏng" also appears mid-step in
                // "nghỉ đi bộ thả lỏng 2 phút" (sprint recovery), which is not a cool-down.
                } else if lower.contains("cool") || lower.contains("stretch") || lower.hasPrefix("thả lỏng") || lower.hasPrefix("hạ nhiệt") {
                    cooldown = s
                } else {
                    main.append(s)
                }
            }
            return (warmup, main, cooldown)
        }

        var warmup: String? = nil
        var cooldown: String? = nil
        var main: [String] = []
        var inNote = false

        for segment in segments(of: text) {
            var step = segment
            if let (section, body) = label(of: segment) {
                if section == .process {
                    step = body
                    inNote = false
                } else {
                    inNote = true   // a note about the workout, never a step
                    continue
                }
            } else if inNote {
                if isStepLike(segment) { inNote = false } else { continue }
            }
            if step.isEmpty { continue }

            let lower = step.lowercased()
            if warmup == nil && (lower.hasPrefix("warm") || lower.contains("warm up") || lower.contains("warm-up") || lower.hasPrefix("khởi động")) {
                warmup = step
            } else if lower.hasPrefix("cool") || lower.contains("cool down") || lower.contains("cool-down") || lower.hasPrefix("thả lỏng") || lower.hasPrefix("hạ nhiệt") {
                cooldown = step
            } else {
                main.append(step)
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

    /// "25 min steady running @ Zone 1-2" -> "25 min"; nil unless the line opens with a duration.
    private static func leadingMinutes(of text: String?) -> String? {
        guard let text,
              let range = text.range(of: #"^\s*(?:main set:?\s*)?(\d+(?:[–\-]\d+)?\s*(?:min|phút))(?![\p{L}])"#,
                                     options: [.regularExpression, .caseInsensitive]) else { return nil }
        return extractMinutes(String(text[range]))
    }

    private static func firstNumber(in text: String?) -> Int? {
        guard let text, let range = text.range(of: #"\d+"#, options: .regularExpression) else { return nil }
        return Int(text[range])
    }

    private static func extractMinutes(_ text: String) -> String? {
        guard let regex = try? NSRegularExpression(pattern: #"(\d+[–\-]\d+\s*(?:min|phút)|\d+\s*(?:min|phút))"#, options: .caseInsensitive) else { return nil }
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
