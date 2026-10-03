import Testing
import Foundation
@testable import UphillAI

@Suite("ManagePlanSheetTests")
@MainActor
struct ManagePlanSheetTests {
    private func makeViewModel() -> (PlanViewModel, FakePlanService) {
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

        let p2 = TestData.plan([
            "id": 2,
            "race_name": "Marathon 42K",
            "start_date": "2026-11-01",
            "total_weeks": 8
        ])
        service.recentResult.withLock { $0 = .success([plan, p2]) }

        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(secondsFromGMT: 0)!
        cal.locale = Locale(identifier: "en_US_POSIX")

        var c = DateComponents()
        c.year = 2026; c.month = 10; c.day = 5
        let now = cal.date(from: c)!

        let model = PlanViewModel(
            service: service,
            cache: .inMemory(),
            now: { now },
            calendar: cal
        )
        return (model, service)
    }

    @Test func sheetLoadsRecentPlans() async throws {
        let (model, service) = makeViewModel()
        await model.load()

        let sheet = ManagePlanSheet(model: model, onStartNew: {})
        let plans = try await model.recentPlans()
        #expect(plans.count == 2)
        #expect(plans[0].id == 1)
        #expect(plans[1].id == 2)
        #expect(service.calls.withLock { $0 }.contains("recent"))
    }

    @Test func deletePlanCallsDeleteOnService() async {
        let (model, service) = makeViewModel()
        await model.load()

        let ok = await model.deletePlan(id: 1)
        #expect(ok)
        let calls = service.calls.withLock { $0 }
        #expect(calls.contains("delete 1"))
    }
}
