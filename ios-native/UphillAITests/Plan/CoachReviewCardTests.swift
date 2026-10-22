import Testing
import SwiftUI
@testable import UphillAI

@Suite("CoachReviewCardTests")
struct CoachReviewCardTests {
    @Test @MainActor func coachCardRendersPriorityWorkout() throws {
        let fake = FakePlanService()
        let vm = PlanViewModel(service: fake, cache: .inMemory())
        vm.adopt(PlanSnapshot(plan: TestData.plan(), workouts: [
            TestData.workout(["id": 1, "week_number": 1, "title": "Hill Repeats", "is_priority": true])
        ]))

        #expect(vm.snapshot?.workouts.first?.isPriority == true)
    }

    @Test func oneMessageNudgeFirst() {
        #expect(CoachReviewCard.message(nudge: "Easy this week.", why: "Base", welcome: ["Hi."], pick: "Hills") == "Easy this week.")
    }

    @Test func oneMessageWhyThenWelcomeThenPick() {
        #expect(CoachReviewCard.message(nudge: nil, why: "Build aerobic base.", welcome: nil, pick: "Hills") == "Build aerobic base.")
        #expect(CoachReviewCard.message(nudge: nil, why: nil, welcome: ["Welcome.", "Run easy."], pick: "Hills") == "Welcome. Run easy.")
        #expect(CoachReviewCard.message(nudge: nil, why: nil, welcome: nil, pick: "Hills")
                == L("If you do one session well this week, make it %@.", "Hills"))
        #expect(CoachReviewCard.message(nudge: nil, why: nil, welcome: nil, pick: nil) == nil)
    }
}
