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

    @Test func aboutJoinsWhyBenefitCautionInOrder() {
        let w = TestData.workout(["description": "Overall: Steady hour. Reason: Base phase. Benefit: Builds aerobic base. Warning: Stop if your knee hurts."])
        let about = WorkoutDetailContent.make(workout: w, isTreadmill: false).about
        #expect(about.map(\.kind) == [.overall, .reason, .benefit, .caution])
        #expect(about.last?.text == "Stop if your knee hurts.")
    }

    @Test func aboutIsEmptyWithoutDescription() {
        #expect(WorkoutDetailContent.make(workout: TestData.workout(["description": ""]), isTreadmill: false).about.isEmpty)
    }

    @Test func fuelingLineIsTrimmedTipOrNil() {
        #expect(WorkoutDetailContent.make(workout: TestData.workout(["fueling_tip": "  One gel at 45 min. "]), isTreadmill: false).fuelingLine == "One gel at 45 min.")
        #expect(WorkoutDetailContent.make(workout: TestData.workout(["fueling_tip": "  "]), isTreadmill: false).fuelingLine == nil)
    }
}
