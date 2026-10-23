import Foundation

/// Everything the workout detail sheet derives from a workout's description: the parsed
/// sections and the execution steps. Pure and Sendable so the sheet can open on cheap data
/// and compute this after presentation, off the main actor.
struct WorkoutDetailContent: Equatable, Sendable {
    struct AboutLine: Equatable, Sendable {
        enum Kind: Equatable, Sendable { case overall, reason, benefit, caution }
        let kind: Kind
        let text: String
    }

    let sections: DescriptionSections
    let description: ParsedWorkoutDescription
    let steps: [ExecutionStepItem]
    var fuelingLine: String? = nil

    /// "About this session": overall, why, benefit and caution in that order, empty ones left out.
    var about: [AboutLine] {
        let pairs: [(AboutLine.Kind, String?)] = [
            (.overall, sections.overall ?? description.overview ?? description.intent),
            (.reason, sections.reason ?? description.reason),
            (.benefit, sections.benefit ?? description.benefit),
            (.caution, sections.warning ?? description.warning),
        ]
        return pairs.compactMap { kind, text in
            guard let text = text?.trimmingCharacters(in: .whitespacesAndNewlines), !text.isEmpty else { return nil }
            return AboutLine(kind: kind, text: text)
        }
    }

    static func make(workout: Workout, isTreadmill: Bool) -> WorkoutDetailContent {
        let extracted = WorkoutDescriptionParser.extractDescriptionSections(workout.description ?? "")
        let parsed = WorkoutStepParser.parseDescription(workout.description ?? "")
        let tip = workout.fuelingTip?.trimmingCharacters(in: .whitespacesAndNewlines)
        return WorkoutDetailContent(
            sections: extracted,
            description: parsed,
            steps: WorkoutStepParser.parseSteps(workout: workout, description: parsed, isTreadmill: isTreadmill),
            fuelingLine: tip?.isEmpty == false ? tip : nil
        )
    }
}
