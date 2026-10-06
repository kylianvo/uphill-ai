import Foundation

/// Everything the workout detail sheet derives from a workout's description: the parsed
/// sections and the execution steps. Pure and Sendable so the sheet can open on cheap data
/// and compute this after presentation, off the main actor.
struct WorkoutDetailContent: Equatable, Sendable {
    let description: ParsedWorkoutDescription
    let steps: [ExecutionStepItem]

    static func make(workout: Workout, isTreadmill: Bool) -> WorkoutDetailContent {
        let parsed = WorkoutStepParser.parseDescription(workout.description)
        return WorkoutDetailContent(
            description: parsed,
            steps: WorkoutStepParser.parseSteps(workout: workout, description: parsed, isTreadmill: isTreadmill)
        )
    }
}
