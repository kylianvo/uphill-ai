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

    @Test @MainActor func planWith6GeneratedWeeksReviewShowsWeek3BlockText() async throws {
        let fake = FakePlanService()
        let vm = PlanViewModel(service: fake, cache: .inMemory())

        let block1 = BlockCompletion(
            blockNumber: 1, weekStart: 1, weekEnd: 2, completionPct: 90, unlocked: true,
            aiLastWeekReview: "Pre-season foundation complete.",
            aiThisWeekDescription: "Week 1-2 base volume focus."
        )
        let block2 = BlockCompletion(
            blockNumber: 2, weekStart: 3, weekEnd: 4, completionPct: 80, unlocked: true,
            aiLastWeekReview: "Solid consistency through the initial base block.",
            aiThisWeekDescription: "Week 3 block focus: tempo progression and hill work."
        )
        let block3 = BlockCompletion(
            blockNumber: 3, weekStart: 5, weekEnd: 6, completionPct: 0, unlocked: false,
            aiLastWeekReview: "Great tempo execution in block 2.",
            aiThisWeekDescription: "Peak mountain volume and long run simulation."
        )
        let blockResp = BlockCompletionResponse(
            blocks: [block1, block2, block3],
            maxGeneratedWeek: 6
        )

        var workouts: [Workout] = []
        for w in 1...6 {
            workouts.append(TestData.workout(["id": w, "week_number": w, "title": "Run W\(w)"]))
        }
        let snapshot = PlanSnapshot(plan: TestData.plan(["current_week": 1, "total_weeks": 8]), workouts: workouts)
        fake.activeResult.withLock { $0 = .success(snapshot) }
        fake.completionResult.withLock { $0 = .success(blockResp) }

        // load() fetches blockCompletion independently of selectedWeek
        await vm.load()
        vm.selectedWeek = 3

        let narrative = vm.selectedWeekNarrative
        #expect(narrative?.aiThisWeekDescription == "Week 3 block focus: tempo progression and hill work.")
        #expect(narrative?.aiLastWeekReview == "Solid consistency through the initial base block.")
    }

    @Test @MainActor func narrativeSelectsBlockContainingWeekWith3WeekBlocks() async throws {
        let fake = FakePlanService()
        let vm = PlanViewModel(service: fake, cache: .inMemory())

        let block1 = BlockCompletion(
            blockNumber: 1, weekStart: 1, weekEnd: 3, completionPct: 95, unlocked: true,
            aiThisWeekDescription: "Block 1 endurance foundation"
        )
        let block2 = BlockCompletion(
            blockNumber: 2, weekStart: 4, weekEnd: 6, completionPct: 85, unlocked: true,
            aiThisWeekDescription: "Block 2 threshold development"
        )
        let block3 = BlockCompletion(
            blockNumber: 3, weekStart: 7, weekEnd: 9, completionPct: 0, unlocked: false,
            aiThisWeekDescription: "Block 3 peak ultra prep"
        )
        let blockResp = BlockCompletionResponse(
            blocks: [block1, block2, block3],
            maxGeneratedWeek: 9
        )

        var workouts: [Workout] = []
        for w in 1...9 {
            workouts.append(TestData.workout(["id": w, "week_number": w, "title": "Run W\(w)"]))
        }
        let snapshot = PlanSnapshot(plan: TestData.plan(["current_week": 1, "total_weeks": 12]), workouts: workouts)
        fake.activeResult.withLock { $0 = .success(snapshot) }
        fake.completionResult.withLock { $0 = .success(blockResp) }

        await vm.load()

        // Block 1 (weeks 1...3)
        vm.selectedWeek = 1
        #expect(vm.selectedWeekNarrative?.aiThisWeekDescription == "Block 1 endurance foundation")
        vm.selectedWeek = 2
        #expect(vm.selectedWeekNarrative?.aiThisWeekDescription == "Block 1 endurance foundation")
        vm.selectedWeek = 3
        #expect(vm.selectedWeekNarrative?.aiThisWeekDescription == "Block 1 endurance foundation")

        // Block 2 (weeks 4...6)
        vm.selectedWeek = 4
        #expect(vm.selectedWeekNarrative?.aiThisWeekDescription == "Block 2 threshold development")
        vm.selectedWeek = 5
        #expect(vm.selectedWeekNarrative?.aiThisWeekDescription == "Block 2 threshold development")
        vm.selectedWeek = 6
        #expect(vm.selectedWeekNarrative?.aiThisWeekDescription == "Block 2 threshold development")

        // Block 3 (weeks 7...9)
        vm.selectedWeek = 7
        #expect(vm.selectedWeekNarrative?.aiThisWeekDescription == "Block 3 peak ultra prep")
        vm.selectedWeek = 8
        #expect(vm.selectedWeekNarrative?.aiThisWeekDescription == "Block 3 peak ultra prep")
        vm.selectedWeek = 9
        #expect(vm.selectedWeekNarrative?.aiThisWeekDescription == "Block 3 peak ultra prep")

        // Beyond generated blocks
        vm.selectedWeek = 10
        #expect(vm.selectedWeekNarrative == nil)
    }

    @Test @MainActor func isWeekUngeneratedUsesMaxGeneratedWeekAndPreservesAllRestWeeks() async throws {
        let fake = FakePlanService()
        let vm = PlanViewModel(service: fake, cache: .inMemory())

        let blockResp = BlockCompletionResponse(
            blocks: [],
            maxGeneratedWeek: 6
        )
        // Week 4 is a real recovery all-rest week within generated range (week 4 <= 6)
        let snapshot = PlanSnapshot(
            plan: TestData.plan(["total_weeks": 8]),
            workouts: [
                TestData.workout(["id": 1, "week_number": 1, "title": "Run 1"]),
                TestData.workout(["id": 2, "week_number": 2, "title": "Run 2"]),
                TestData.workout(["id": 3, "week_number": 3, "title": "Run 3"]),
                // Week 4: all-rest real recovery week
                TestData.workout(["id": 41, "week_number": 4, "title": "Rest", "type": "Rest", "duration_minutes": 0.0, "distance_km": 0.0]),
                TestData.workout(["id": 42, "week_number": 4, "title": "Rest", "type": "Rest", "duration_minutes": 0.0, "distance_km": 0.0]),
                TestData.workout(["id": 5, "week_number": 5, "title": "Run 5"]),
                TestData.workout(["id": 6, "week_number": 6, "title": "Run 6"])
            ]
        )
        fake.activeResult.withLock { $0 = .success(snapshot) }
        fake.completionResult.withLock { $0 = .success(blockResp) }

        await vm.load()

        // Weeks 1...6 are generated; real all-rest week 4 must NOT be treated as ungenerated
        #expect(!vm.isWeekUngenerated(1))
        #expect(!vm.isWeekUngenerated(4))
        #expect(!vm.isWeekUngenerated(6))

        // Week 7 and 8 are beyond maxGeneratedWeek (6) -> ungenerated
        #expect(vm.isWeekUngenerated(7))
        #expect(vm.isWeekUngenerated(8))
    }

    @Test @MainActor func isWeekUngeneratedFallbackWhenBlockCompletionNil() throws {
        let fake = FakePlanService()
        let vm = PlanViewModel(service: fake, cache: .inMemory())

        let snapshot = PlanSnapshot(
            plan: TestData.plan(["total_weeks": 6]),
            workouts: [
                TestData.workout(["id": 1, "week_number": 1, "title": "Run 1"]),
                TestData.workout(["id": 2, "week_number": 2, "title": "Rest", "type": "Rest", "duration_minutes": 0.0, "distance_km": 0.0])
            ]
        )
        // blockCompletion is nil
        vm.adopt(snapshot)

        #expect(!vm.isWeekUngenerated(1)) // active workouts -> false
        #expect(vm.isWeekUngenerated(2))  // all rest fallback -> true
        #expect(vm.isWeekUngenerated(3))  // no workouts -> true
    }

    @Test @MainActor func canAdaptWeekRules() async throws {
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
        fake.activeResult.withLock { $0 = .success(snapshot) }
        fake.completionResult.withLock { $0 = .success(blockResp) }

        await vm.load()

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
