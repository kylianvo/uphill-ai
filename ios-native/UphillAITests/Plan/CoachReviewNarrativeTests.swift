import Foundation
import Testing
@testable import UphillAI

@Suite("CoachReviewNarrativeTests")
struct CoachReviewNarrativeTests {
    @Test func decodesBlockCompletionWithNarratives() throws {
        let jsonStr = """
        {
            "block_number": 1,
            "week_start": 1,
            "week_end": 2,
            "unlocked": true,
            "completion_pct": 85,
            "completed_minutes": 240.0,
            "total_minutes": 280.0,
            "ai_this_week_description": "Build volume with controlled Zone 2 effort.",
            "ai_last_week_review": "Excellent consistency on your long run."
        }
        """
        let block = try JSONCoding.decoder.decode(BlockCompletion.self, from: jsonStr.data(using: .utf8)!)
        #expect(block.aiThisWeekDescription == "Build volume with controlled Zone 2 effort.")
        #expect(block.aiLastWeekReview == "Excellent consistency on your long run.")
        #expect(block.weekStart == 1)
        #expect(block.weekEnd == 2)
    }

    @Test @MainActor func planViewModelExposesNarrativeForActiveWeek() throws {
        let fake = FakePlanService()
        let vm = PlanViewModel(service: fake, cache: .inMemory())

        let block = BlockCompletion(
            blockNumber: 1,
            weekStart: 1,
            weekEnd: 2,
            completionPct: 90,
            unlocked: true,
            aiLastWeekReview: "Strong endurance gains last week.",
            aiThisWeekDescription: "Focus on uphill pacing and fueling."
        )
        let blockResp = BlockCompletionResponse(
            blocks: [block],
            maxGeneratedWeek: 4
        )

        let snapshot = PlanSnapshot(plan: TestData.plan(), workouts: [
            TestData.workout(["id": 1, "week_number": 1, "title": "Base Run"])
        ])
        vm.adopt(snapshot)
        vm.adoptBlockCompletion(blockResp)
        vm.selectedWeek = 1

        let narrative = vm.selectedWeekNarrative
        #expect(narrative?.aiThisWeekDescription == "Focus on uphill pacing and fueling.")
        #expect(narrative?.aiLastWeekReview == "Strong endurance gains last week.")
    }

    @Test @MainActor func isWeekUngeneratedIdentifiesUngeneratedWeeks() throws {
        let fake = FakePlanService()
        let vm = PlanViewModel(service: fake, cache: .inMemory())

        let blockResp = BlockCompletionResponse(
            blocks: [],
            maxGeneratedWeek: 4
        )
        let snapshot = PlanSnapshot(
            plan: TestData.plan(["total_weeks": 8]),
            workouts: [
                TestData.workout(["id": 1, "week_number": 1, "title": "Easy Run"]),
                TestData.workout(["id": 2, "week_number": 2, "title": "Tempo Run"]),
                TestData.workout(["id": 3, "week_number": 3, "title": "Long Run"]),
                TestData.workout(["id": 4, "week_number": 4, "title": "Recovery"]),
                // Week 5 has only rest days
                TestData.workout(["id": 5, "week_number": 5, "title": "Rest", "type": "Rest", "duration_minutes": 0.0, "distance_km": 0.0]),
                TestData.workout(["id": 6, "week_number": 5, "title": "Rest", "type": "Rest", "duration_minutes": 0.0, "distance_km": 0.0]),
                TestData.workout(["id": 7, "week_number": 5, "title": "Rest", "type": "Rest", "duration_minutes": 0.0, "distance_km": 0.0]),
                TestData.workout(["id": 8, "week_number": 5, "title": "Rest", "type": "Rest", "duration_minutes": 0.0, "distance_km": 0.0]),
                TestData.workout(["id": 9, "week_number": 5, "title": "Rest", "type": "Rest", "duration_minutes": 0.0, "distance_km": 0.0]),
                TestData.workout(["id": 10, "week_number": 5, "title": "Rest", "type": "Rest", "duration_minutes": 0.0, "distance_km": 0.0]),
                TestData.workout(["id": 11, "week_number": 5, "title": "Rest", "type": "Rest", "duration_minutes": 0.0, "distance_km": 0.0])
            ]
        )
        vm.adopt(snapshot)
        vm.adoptBlockCompletion(blockResp)

        #expect(!vm.isWeekUngenerated(1))
        #expect(!vm.isWeekUngenerated(4))
        #expect(vm.isWeekUngenerated(5))
        #expect(vm.isWeekUngenerated(6))
    }

    @Test @MainActor func canAdaptWeekRules() throws {
        let fake = FakePlanService()
        let vm = PlanViewModel(service: fake, cache: .inMemory())

        let blockResp = BlockCompletionResponse(
            blocks: [],
            maxGeneratedWeek: 4
        )
        let snapshot = PlanSnapshot(
            plan: TestData.plan(["current_week": 2, "total_weeks": 6]),
            workouts: [
                TestData.workout(["id": 1, "week_number": 1, "title": "Run 1"]),
                TestData.workout(["id": 2, "week_number": 2, "title": "Run 2"]),
                TestData.workout(["id": 3, "week_number": 3, "title": "Run 3"]),
                TestData.workout(["id": 4, "week_number": 4, "title": "Run 4"])
            ]
        )
        vm.adopt(snapshot)
        vm.adoptBlockCompletion(blockResp)

        // Generated weeks can be adapted (matching web: week <= maxGeneratedWeek)
        #expect(vm.canAdaptWeek(1))
        #expect(vm.canAdaptWeek(2))
        #expect(vm.canAdaptWeek(3))
        #expect(vm.canAdaptWeek(4))
        // Ungenerated weeks cannot be adapted
        #expect(!vm.canAdaptWeek(5))
        #expect(!vm.canAdaptWeek(6))
    }
}
