import Foundation

public struct DescriptionSections: Equatable, Sendable {
    public let overall: String?
    public let process: String?
    public let reason: String?
    public let benefit: String?
    public let warning: String?

    public init(overall: String?, process: String?, reason: String?, benefit: String?, warning: String?) {
        self.overall = overall
        self.process = process
        self.reason = reason
        self.benefit = benefit
        self.warning = warning
    }
}

public struct ExecutionSteps: Equatable, Sendable {
    public let warmup: String?
    public let mainSteps: [String]
    public let cooldown: String?

    public init(warmup: String?, mainSteps: [String], cooldown: String?) {
        self.warmup = warmup
        self.mainSteps = mainSteps
        self.cooldown = cooldown
    }
}

public struct LibraryExecutionInfo: Equatable, Sendable {
    public let execution: String
    public let overview: String

    public init(execution: String, overview: String) {
        self.execution = execution
        self.overview = overview
    }
}

public struct MainSetText: Equatable, Sendable {
    public let executionText: String
    public let overviewText: String

    public init(executionText: String, overviewText: String) {
        self.executionText = executionText
        self.overviewText = overviewText
    }
}

public struct CoachNotesContent: Equatable, Sendable {
    public let hasSections: Bool
    public let overall: String?
    public let reason: String?
    public let benefit: String?
    public let warning: String?
    public let fallbackText: String

    public init(hasSections: Bool, overall: String?, reason: String?, benefit: String?, warning: String?, fallbackText: String) {
        self.hasSections = hasSections
        self.overall = overall
        self.reason = reason
        self.benefit = benefit
        self.warning = warning
        self.fallbackText = fallbackText
    }
}

public enum WorkoutDescriptionParser {
    private static let sectionKeywords = ["Overall", "Process", "Reason", "Benefit", "Warning"]

    public static func extractSection(_ description: String, sectionName: String) -> String? {
        let pattern = sectionName + #"[:\-]\s*([\s\S]*?)(?=(?:"# + sectionKeywords.joined(separator: "|") + #")[:\-]|(?i)$)"#
        guard let regex = try? NSRegularExpression(pattern: pattern, options: [.caseInsensitive]) else { return nil }
        let ns = description as NSString
        guard let match = regex.firstMatch(in: description, options: [], range: NSRange(location: 0, length: ns.length)),
              match.numberOfRanges > 1 else { return nil }
        let value = ns.substring(with: match.range(at: 1)).trimmingCharacters(in: .whitespacesAndNewlines)
        return value.isEmpty ? nil : value
    }

    public static func looksLikeExercisePrescription(_ sentence: String) -> Bool {
        let hasSets = sentence.range(of: #"\b\d+\s*sets?\b"#, options: [.regularExpression, .caseInsensitive]) != nil
        let hasRepsOrDuration = sentence.range(of: #"\b(reps?|repetitions?)\b"#, options: [.regularExpression, .caseInsensitive]) != nil
            || sentence.range(of: #"\b\d+[\s-]*seconds?\b"#, options: [.regularExpression, .caseInsensitive]) != nil
        return hasSets && hasRepsOrDuration
    }

    public static func splitIntoClauses(_ text: String) -> [String] {
        guard let regex = try? NSRegularExpression(pattern: #"(?<=[.!?;])\s+"#) else {
            return [text.trimmingCharacters(in: .whitespacesAndNewlines)].filter { !$0.isEmpty }
        }
        let ns = text as NSString
        let matches = regex.matches(in: text, options: [], range: NSRange(location: 0, length: ns.length))
        var clauses: [String] = []
        var lastIdx = 0
        for match in matches {
            let clause = ns.substring(with: NSRange(location: lastIdx, length: match.range.location - lastIdx)).trimmingCharacters(in: .whitespacesAndNewlines)
            if !clause.isEmpty { clauses.append(clause) }
            lastIdx = match.range.location + match.range.length
        }
        if lastIdx < ns.length {
            let clause = ns.substring(from: lastIdx).trimmingCharacters(in: .whitespacesAndNewlines)
            if !clause.isEmpty { clauses.append(clause) }
        }
        return clauses
    }

    public static func splitOutExerciseSentences(_ text: String) -> (exercises: [String], remainder: String) {
        let sentences = splitIntoClauses(text)
        var exercises: [String] = []
        var remainder: [String] = []
        for s in sentences {
            if looksLikeExercisePrescription(s) {
                var cleaned = s
                if cleaned.hasSuffix(".") || cleaned.hasSuffix(";") {
                    cleaned = String(cleaned.dropLast())
                }
                exercises.append(cleaned)
            } else {
                remainder.append(s)
            }
        }
        return (exercises, remainder.joined(separator: " ").trimmingCharacters(in: .whitespacesAndNewlines))
    }

    public static func extractDescriptionSections(_ description: String) -> DescriptionSections {
        var process = extractSection(description, sectionName: "Process")
        var overall = extractSection(description, sectionName: "Overall")
        var reason = extractSection(description, sectionName: "Reason")
        var benefit = extractSection(description, sectionName: "Benefit")
        var warning = extractSection(description, sectionName: "Warning")

        var rescued: [String] = []
        if let val = overall {
            let (ex, rem) = splitOutExerciseSentences(val)
            if !ex.isEmpty { rescued.append(contentsOf: ex); overall = rem.isEmpty ? nil : rem }
        }
        if let val = reason {
            let (ex, rem) = splitOutExerciseSentences(val)
            if !ex.isEmpty { rescued.append(contentsOf: ex); reason = rem.isEmpty ? nil : rem }
        }
        if let val = benefit {
            let (ex, rem) = splitOutExerciseSentences(val)
            if !ex.isEmpty { rescued.append(contentsOf: ex); benefit = rem.isEmpty ? nil : rem }
        }
        if let val = warning {
            let (ex, rem) = splitOutExerciseSentences(val)
            if !ex.isEmpty { rescued.append(contentsOf: ex); warning = rem.isEmpty ? nil : rem }
        }

        if !rescued.isEmpty {
            let steps = parseExecutionSteps(process ?? "")
            let mainHasNamedExercise = steps.mainSteps.contains { looksLikeExercisePrescription($0) }
            if !mainHasNamedExercise {
                var parts: [String] = []
                if let w = steps.warmup { parts.append(w) }
                parts.append(contentsOf: rescued)
                if let c = steps.cooldown { parts.append(c) }
                process = parts.joined(separator: " → ")
            } else if process == nil || process?.isEmpty == true {
                process = rescued.joined(separator: " → ")
            }
        }

        return DescriptionSections(
            overall: overall,
            process: process,
            reason: reason,
            benefit: benefit,
            warning: warning
        )
    }

    public static func parseExecutionSteps(_ execution: String) -> ExecutionSteps {
        let isWarmup = { (s: String) -> Bool in
            let l = s.lowercased()
            return l.contains("warm") || (l.contains("easy jog") && l.contains("start"))
        }
        let isCooldown = { (s: String) -> Bool in
            let l = s.lowercased()
            return l.contains("cool") || l.contains("stretch")
        }

        let arrowParts = execution
            .components(separatedBy: "→")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }

        if arrowParts.count > 1 {
            var warmup: [String] = []
            var main: [String] = []
            var cooldown: [String] = []
            var seenMain = false

            for part in arrowParts {
                if !seenMain && isWarmup(part) {
                    warmup.append(part)
                } else if isCooldown(part) {
                    cooldown.append(part)
                } else {
                    main.append(part)
                    seenMain = true
                }
            }

            return ExecutionSteps(
                warmup: warmup.isEmpty ? nil : warmup.joined(separator: " → "),
                mainSteps: expandRunOnSteps(main),
                cooldown: cooldown.isEmpty ? nil : cooldown.joined(separator: " → ")
            )
        }

        // Sentence splitting fallback
        guard let regex = try? NSRegularExpression(pattern: #"(?<=[.!?])\s+"#) else {
            return ExecutionSteps(warmup: nil, mainSteps: expandRunOnSteps(execution.isEmpty ? [] : [execution]), cooldown: nil)
        }
        let ns = execution as NSString
        let matches = regex.matches(in: execution, options: [], range: NSRange(location: 0, length: ns.length))
        var sentences: [String] = []
        var lastIdx = 0
        for match in matches {
            let sentence = ns.substring(with: NSRange(location: lastIdx, length: match.range.location - lastIdx)).trimmingCharacters(in: .whitespacesAndNewlines)
            if !sentence.isEmpty { sentences.append(sentence) }
            lastIdx = match.range.location + match.range.length
        }
        if lastIdx < ns.length {
            let sentence = ns.substring(from: lastIdx).trimmingCharacters(in: .whitespacesAndNewlines)
            if !sentence.isEmpty { sentences.append(sentence) }
        }

        var warmup: [String] = []
        var main: [String] = []
        var cooldown: [String] = []
        var inCooldown = false

        for s in sentences {
            if main.isEmpty && !inCooldown && isWarmup(s) {
                warmup.append(s)
            } else if isCooldown(s) {
                cooldown.append(s)
                inCooldown = true
            } else if inCooldown {
                cooldown.append(s)
            } else {
                main.append(s)
            }
        }

        return ExecutionSteps(
            warmup: warmup.isEmpty ? nil : warmup.joined(separator: " "),
            mainSteps: expandRunOnSteps(main.isEmpty ? (execution.isEmpty ? [] : [execution]) : main),
            cooldown: cooldown.isEmpty ? nil : cooldown.joined(separator: " ")
        )
    }

    public static func expandRunOnSteps(_ steps: [String]) -> [String] {
        var expanded: [String] = []
        for step in steps {
            let parts = step
                .components(separatedBy: ";")
                .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
                .filter { !$0.isEmpty }
            expanded.append(contentsOf: parts)
        }
        return expanded
    }

    public static func extractLeadingMinutes(_ text: String?) -> Int? {
        guard let text, !text.isEmpty else { return nil }
        guard let regex = try? NSRegularExpression(pattern: #"(\d+)"#) else { return nil }
        let ns = text as NSString
        guard let match = regex.firstMatch(in: text, options: [], range: NSRange(location: 0, length: ns.length)),
              match.numberOfRanges > 1 else { return nil }
        return Int(ns.substring(with: match.range(at: 1)))
    }

    public static func mainDurationMinutes(totalMinutes: Double, steps: ExecutionSteps) -> Double {
        guard totalMinutes > 0 else { return totalMinutes }
        guard let warmup = extractLeadingMinutes(steps.warmup),
              let cooldown = extractLeadingMinutes(steps.cooldown) else {
            return totalMinutes
        }
        return max(0, totalMinutes - Double(warmup) - Double(cooldown))
    }

    public static func selectMainSetText(library: LibraryExecutionInfo, description: String?) -> MainSetText {
        guard let description, !description.isEmpty else {
            return MainSetText(executionText: library.execution, overviewText: library.overview)
        }
        let sections = extractDescriptionSections(description)
        let exec = (sections.process?.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty == false)
            ? sections.process!
            : library.execution
        let over = (sections.overall?.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty == false)
            ? sections.overall!
            : library.overview
        return MainSetText(executionText: exec, overviewText: over)
    }

    public static func buildCoachNotesContent(_ description: String) -> CoachNotesContent {
        let sections = extractDescriptionSections(description)
        let hasSections = sections.overall != nil || sections.reason != nil || sections.benefit != nil || sections.warning != nil
        return CoachNotesContent(
            hasSections: hasSections,
            overall: sections.overall,
            reason: sections.reason,
            benefit: sections.benefit,
            warning: sections.warning,
            fallbackText: description
        )
    }
}
