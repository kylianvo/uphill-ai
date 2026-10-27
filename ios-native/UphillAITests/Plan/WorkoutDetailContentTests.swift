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

struct SessionNotesContentTests {
    @Test func vietnameseReasonIsItsOwnSection() {
        let w = TestData.workout(["description": "Warm-up 10 phút nhẹ → 40 phút Zone 2. Tổng quan: Buổi nhẹ đều. Lý do: Tuần 6 của ladder. Lợi ích: Nền aerobic. Lưu ý: Dừng nếu đau gối."])
        let about = WorkoutDetailContent.make(workout: w, isTreadmill: false).about
        #expect(about.map(\.kind) == [.overall, .reason, .benefit, .caution])
        #expect(about.first { $0.kind == .reason }?.text == "Tuần 6 của ladder.")
    }

    @Test func raceLineSitsBeforeTheCaution() {
        let w = TestData.workout(["description": "Overall: Long day. Reason: Ladder. Benefit: Base. Warning: Walk the descents.",
                                  "race_fit": "3 h 30 on your feet, of the 29 h cutoff at VHT 100K."])
        let about = WorkoutDetailContent.make(workout: w, isTreadmill: false).about
        #expect(about.map(\.kind) == [.overall, .reason, .benefit, .raceFit, .caution])
    }

    @Test func whyTodayIsTheReasonsFirstSentence() {
        let w = TestData.workout(["description": "Overall: Long day. Reason: Week 6 of your long-run ladder: 3 h 30. It builds time on feet. Benefit: Base."])
        #expect(WorkoutDetailContent.make(workout: w, isTreadmill: false).whyToday == "Week 6 of your long-run ladder: 3 h 30.")
    }

    @Test func anOverallThatRepeatsTheStepsIsLeftOut() {
        let w = TestData.workout(["description": "Warm-up 15 min easy → 185 min steady Zone 2, power-hiking anything steeper → Cool-down 10 min easy. Overall: Steady Zone 2, power-hiking anything steeper, easy warm-up and cool-down. Reason: Ladder."])
        let about = WorkoutDetailContent.make(workout: w, isTreadmill: false).about
        #expect(!about.contains { $0.kind == .overall })
    }
}
