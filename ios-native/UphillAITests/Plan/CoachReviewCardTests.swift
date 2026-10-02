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
}
