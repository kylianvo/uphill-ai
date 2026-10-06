import Testing
import Foundation
@testable import UphillAI

@Suite("MoveSwapDaySheetTests")
@MainActor
struct MoveSwapDaySheetTests {
    private func makeViewModel() -> (PlanViewModel, FakePlanService, PlanSnapshot) {
        let plan = TestData.plan([
            "id": 1,
            "race_name": "Ultra Trail",
            "start_date": "2026-10-05",
            "total_weeks": 4
        ])
        let w1 = TestData.workout(["id": 101, "week_number": 1, "day_of_week": "Monday", "type": "Easy Run", "duration_minutes": 45])
        let w2 = TestData.workout(["id": 102, "week_number": 1, "day_of_week": "Tuesday", "type": "Intervals", "duration_minutes": 60])
        let w3 = TestData.workout(["id": 103, "week_number": 1, "day_of_week": "Wednesday", "type": "Rest", "duration_minutes": 0])
        let snap = PlanSnapshot(plan: plan, workouts: [w1, w2, w3])

        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snap) }

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
        return (model, service, snap)
    }

    @MainActor
    @Test func sheetInitializesWithSourceDay() async {
        let (model, _, _) = makeViewModel()
        await model.load()

        let days = model.days(for: 1)
        let monday = days.first { $0.weekday == .monday }!

        let sheet = MoveSwapDaySheet(model: model, sourceDay: monday)
        #expect(sheet.sourceDay.weekday == .monday)
        #expect(sheet.sourceDay.workouts.count == 1)
    }

    @Test func performingSwapCallsViewModel() async {
        let (model, service, _) = makeViewModel()
        await model.load()

        let ok = await model.swapDays(week: 1, day1: .monday, day2: .tuesday)
        #expect(ok)
        let calls = service.calls.withLock { $0 }
        #expect(calls.contains { $0.contains("swap w1 Monday <-> Tuesday") })
    }
}
