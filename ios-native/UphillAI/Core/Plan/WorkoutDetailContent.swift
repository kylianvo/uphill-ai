import Foundation

/// Everything the workout detail sheet derives from a workout's description: the parsed
/// sections and the execution steps. Pure and Sendable so the sheet can open on cheap data
/// and compute this after presentation, off the main actor.
struct WorkoutDetailContent: Equatable, Sendable {
    struct AboutLine: Equatable, Sendable {
        enum Kind: Equatable, Sendable { case overall, reason, benefit, raceFit, caution }
        let kind: Kind
        let text: String
    }

    let sections: DescriptionSections
    let description: ParsedWorkoutDescription
    let steps: [ExecutionStepItem]
    var fuelingLine: String? = nil
    /// "For your race" (backend services/race_fit.py).
    var raceFit: String? = nil

    /// "About this session": overall, why, benefit, the race line and caution in that order, empty ones left out.
    /// The overall goes when it only repeats the steps.
    var about: [AboutLine] {
        let overall = sections.overall ?? description.overview ?? description.intent
        let pairs: [(AboutLine.Kind, String?)] = [
            (.overall, overall.flatMap { Self.repeatsSteps($0, steps) ? nil : $0 }),
            (.reason, sections.reason ?? description.reason),
            (.benefit, sections.benefit ?? description.benefit),
            (.raceFit, raceFit),
            (.caution, sections.warning ?? description.warning),
        ]
        return pairs.compactMap { kind, text in
            guard let text = text?.trimmingCharacters(in: .whitespacesAndNewlines), !text.isEmpty else { return nil }
            return AboutLine(kind: kind, text: text)
        }
    }

    /// The first sentence of the reason: the line under the title.
    var whyToday: String? {
        guard let reason = about.first(where: { $0.kind == .reason })?.text else { return nil }
        let end = reason.range(of: #"[.!?](\s|$)"#, options: .regularExpression)
        return end.map { String(reason[..<$0.upperBound]).trimmingCharacters(in: .whitespaces) } ?? reason
    }

    /// Most of the overall's words already in the steps: it would say the steps twice.
    static func repeatsSteps(_ overall: String, _ steps: [ExecutionStepItem]) -> Bool {
        let words = { (s: String) in Set(s.lowercased().split { !$0.isLetter }.filter { $0.count >= 4 }.map(String.init)) }
        let own = words(overall)
        guard own.count >= 3 else { return false }
        let inSteps = words(steps.map { "\($0.target) \($0.steps.joined(separator: " "))" }.joined(separator: " "))
        return Double(own.intersection(inSteps).count) / Double(own.count) >= 0.7
    }

    static func make(workout: Workout, isTreadmill: Bool) -> WorkoutDetailContent {
        let extracted = WorkoutDescriptionParser.extractDescriptionSections(workout.description ?? "")
        let parsed = WorkoutStepParser.parseDescription(workout.description ?? "")
        let tip = workout.fuelingTip?.trimmingCharacters(in: .whitespacesAndNewlines)
        return WorkoutDetailContent(
            sections: extracted,
            description: parsed,
            steps: WorkoutStepParser.parseSteps(workout: workout, description: parsed, isTreadmill: isTreadmill),
            fuelingLine: tip?.isEmpty == false ? tip : nil,
            raceFit: workout.raceFit?.isEmpty == false ? workout.raceFit : nil
        )
    }
}
