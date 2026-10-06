import Foundation
import Testing
@testable import UphillAI

struct WorkoutDetailContentTests {
    private let description = "Warm up 5 min easy jogging\n25 min steady running\nBenefit: Builds aerobic base."

    @Test func buildsParsedDescriptionAndStepsTogether() {
        let w = TestData.workout(["description": description])
        let content = WorkoutDetailContent.make(workout: w, isTreadmill: false)
        #expect(content.description == WorkoutStepParser.parseDescription(w.description))
        #expect(content.steps.map(\.phase) == [.warmup, .main, .cooldown])
    }

    @Test func treadmillChangesTheSteps() {
        let w = TestData.workout(["description": description, "target_pace": "6:00 /km"])
        let outdoor = WorkoutDetailContent.make(workout: w, isTreadmill: false)
        let treadmill = WorkoutDetailContent.make(workout: w, isTreadmill: true)
        #expect(outdoor.steps != treadmill.steps)
    }
}
