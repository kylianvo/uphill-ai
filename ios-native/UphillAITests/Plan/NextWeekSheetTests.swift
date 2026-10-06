import Testing
import Foundation
@testable import UphillAI

@Suite("NextWeekSheetTests")
@MainActor
struct NextWeekSheetTests {
    private func completion(_ pct: Double, unlocked: Bool, maxWeek: Int = 1) -> BlockCompletionResponse {
        try! JSONCoding.decoder.decode(BlockCompletionResponse.self, from: json([
            "plan_id": 1, "max_generated_week": maxWeek,
            "blocks": [["block_number": 1, "week_start": 1, "week_end": 1,
                        "completion_pct": pct, "unlocked": unlocked] as [String: Any]],
        ]))
    }

    private func makeViewModel() -> (PlanViewModel, FakePlanService, FakeGenerationService) {
        let plan = TestData.plan([
            "id": 1,
            "race_name": "Ultra Trail",
            "start_date": "2026-10-05",
            "total_weeks": 4
        ])
        let w1 = TestData.workout(["id": 101, "week_number": 1, "day_of_week": "Monday", "type": "Easy Run", "duration_minutes": 45])
        let snap = PlanSnapshot(plan: plan, workouts: [w1])

        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snap) }

        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(secondsFromGMT: 0)!
        cal.locale = Locale(identifier: "en_US_POSIX")

        var c = DateComponents()
        c.year = 2026; c.month = 10; c.day = 5
        let now = cal.date(from: c)!

        let genService = FakeGenerationService()
        let genCenter = GenerationCenter(service: genService, defaults: UserDefaults(suiteName: UUID().uuidString)!)

        let model = PlanViewModel(
            service: service,
            cache: .inMemory(),
            now: { now },
            calendar: cal,
            generation: genCenter,
            generationService: genService
        )
        return (model, service, genService)
    }

    @Test func sheetInitializesWithOffer() async {
        let (model, _, _) = makeViewModel()
        let offer = NextWeekOffer(blockNumber: 2, weekStart: 2, weekEnd: 2, previousCompletionPct: 50, unlocked: false)
        let sheet = NextWeekSheet(model: model, offer: offer)
        #expect(sheet.offer.blockNumber == 2)
        #expect(!sheet.offer.unlocked)
    }

    @Test func buildingNextWeekWithOverrideCallsGeneration() async {
        let (model, service, gen) = makeViewModel()
        service.completionResult.withLock { $0 = .success(completion(50, unlocked: false, maxWeek: 1)) }
        gen.startResult.withLock { $0 = .success(JobStart(jobId: "nb-123")) }
        await model.load()
        await model.refreshNextWeekOffer()

        #expect(model.nextWeekOffer != nil)
        let res = await model.buildNextWeek(rpe: 8, notes: "Hard block", override: true)
        #expect(res == .started)
        let calls = gen.calls.withLock { $0 }
        #expect(calls.contains { $0.contains("next 2 override=true") })
    }
}
