import Testing
@testable import UphillAI

@Suite("WorkoutStepParserTests")
struct WorkoutStepParserTests {
    private func makeWorkout(
        title: String = "Hill Repeats",
        type: String = "Interval",
        duration: Double = 60,
        pace: String? = "5:30 /km",
        reps: Int? = 6,
        repVal: Double? = 3,
        repUnit: String? = "min",
        walkVal: Double? = 2,
        desc: String? = "Overall: Build uphill power.\nProcess: 15 min warm-up → 6 x 3 min uphill intervals → 10 min cool-down.\nBenefit: Improves VO2 max and fatigue resistance.\nWarning: Do not sprint the first 30 seconds."
    ) -> Workout {
        let json = """
        {
            "id": 10,
            "plan_id": 1,
            "week_number": 1,
            "day_of_week": "Tuesday",
            "phase": "Base",
            "title": "\(title)",
            "type": "\(type)",
            "duration_minutes": \(duration),
            "target_zone": "Z4",
            "target_pace": \(pace != nil ? "\"\(pace!)\"" : "null"),
            "interval_reps": \(reps != nil ? String(reps!) : "null"),
            "interval_rep_value": \(repVal != nil ? String(repVal!) : "null"),
            "interval_rep_unit": \(repUnit != nil ? "\"\(repUnit!)\"" : "null"),
            "walk_interval_value": \(walkVal != nil ? String(walkVal!) : "null"),
            "description": \(desc != nil ? "\"\(desc!.replacingOccurrences(of: "\n", with: "\\n"))\"" : "null")
        }
        """.data(using: .utf8)!
        return try! JSONCoding.decoder.decode(Workout.self, from: json)
    }

    @Test func parseStructuredDescription() {
        let w = makeWorkout()
        let parsed = WorkoutStepParser.parseDescription(w.description)
        #expect(parsed.benefit == "Improves VO2 max and fatigue resistance.")
        #expect(parsed.warning == "Do not sprint the first 30 seconds.")
        #expect(parsed.process?.contains("15 min warm-up") == true)
    }

    @Test func parseExecutionStepsTimeline() {
        let w = makeWorkout()
        let parsed = WorkoutStepParser.parseDescription(w.description)
        let steps = WorkoutStepParser.parseSteps(workout: w, description: parsed, isTreadmill: false)

        #expect(steps.count == 3)
        #expect(steps[0].phase == .warmup)
        #expect(steps[1].phase == .main)
        #expect(steps[1].target.contains("6 × 3 min"))
        #expect(steps[1].recovery?.contains("2 min") == true)
        #expect(steps[2].phase == .cooldown)
    }

    @Test func treadmillToggleCalculatesSpeed() {
        let w = makeWorkout(pace: "6:00 /km")
        let parsed = WorkoutStepParser.parseDescription(w.description)
        let tmSteps = WorkoutStepParser.parseSteps(workout: w, description: parsed, isTreadmill: true)
        #expect(tmSteps[1].target.contains("km/h"))
    }
}
