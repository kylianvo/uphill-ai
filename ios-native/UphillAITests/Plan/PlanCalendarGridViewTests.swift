import Testing
import Foundation
@testable import UphillAI

@Suite("PlanCalendarGridViewTests")
struct PlanCalendarGridViewTests {
    @Test func calendarDayCellIdentifiable() {
        let now = Date()
        let cell = CalendarDayCell(
            date: now,
            isCurrentMonth: true,
            isToday: true,
            isRaceDay: false,
            weekNumber: 1,
            workouts: []
        )
        #expect(cell.isToday)
        #expect(cell.isCurrentMonth)
        #expect(cell.primaryWorkout == nil)
    }

    @Test func calendarDayCellIdentifiesPrimaryWorkout() {
        let now = Date()
        let rest = TestData.workout(["id": 1, "type": "Rest", "duration_minutes": 0])
        let run = TestData.workout(["id": 2, "type": "Easy Run", "duration_minutes": 45])
        let cell = CalendarDayCell(
            date: now,
            isCurrentMonth: true,
            isToday: false,
            isRaceDay: false,
            weekNumber: 1,
            workouts: [rest, run]
        )
        #expect(cell.primaryWorkout?.id == 2)
    }

    // Plan week 1 = Mon 28 Sep 2026. Week 2 has a double session on Tue 6 Oct, a done long run on Sat 10 Oct.
    private let plan = TestData.plan(["start_date": "2026-09-30"])
    private var workouts: [Workout] {
        [
            TestData.workout(["id": 1, "week_number": 1, "day_of_week": "Thursday", "distance_km": 10.0]),
            TestData.workout(["id": 2, "week_number": 2, "day_of_week": "Monday", "type": "Rest", "duration_minutes": 0, "distance_km": NSNull()]),
            TestData.workout(["id": 3, "week_number": 2, "day_of_week": "Tuesday", "distance_km": 8.0]),
            TestData.workout(["id": 4, "week_number": 2, "day_of_week": "Tuesday", "distance_km": 5.0]),
            TestData.workout(["id": 5, "week_number": 2, "day_of_week": "Saturday", "type": "Long Run", "distance_km": 20.0, "is_completed": 1]),
        ]
    }
    private let now = PlanCalendar.day(from: "2026-10-07")!

    private func month(_ ymd: String) -> CalendarMonth {
        CalendarMonth.make(month: PlanCalendar.day(from: ymd)!, plan: plan, workouts: workouts, now: now)
    }

    @Test func monthGridRunsMondayToSundayAndTotalsOnlyInMonthDays() {
        let oct = month("2026-10-01")
        #expect(oct.weeks.count == 5)
        #expect(PlanCalendar.ymd(oct.weeks[0].cells[0].date) == "2026-09-28")
        #expect(oct.weeks[0].cells[0].isCurrentMonth == false)
        #expect(PlanCalendar.ymd(oct.weeks[4].cells[6].date) == "2026-11-01")
        #expect(oct.weeks.map(\.weekNumber) == [1, 2, 3, 4, 5])
        #expect(oct.weeks[0].km == 10)
        #expect(oct.weeks[1].km == 33)
        #expect(oct.km == 43)
        #expect(oct.sessionsTotal == 4)
        #expect(oct.sessionsDone == 1)
        #expect(oct.isCurrentMonth)
    }

    @Test func restDaysInsidePlanHaveAWeekAndDoubleSessionsKeepBoth() {
        let oct = month("2026-10-01")
        let tuesday = oct.weeks[1].cells[1]
        #expect(tuesday.sessions.count == 2)
        let wednesday = oct.weeks[1].cells[2]
        #expect(wednesday.weekNumber == 2)
        #expect(wednesday.sessions.isEmpty)
        #expect(oct.weeks[1].cells[2].isToday)
        #expect(oct.maxSessionLoad == 20)
    }

    @Test func monthOutsideThePlanIsEmptyAndHasNoWeeks() {
        let aug = month("2026-08-01")
        #expect(aug.weeks.allSatisfy { $0.weekNumber == nil })
        #expect(aug.sessionsTotal == 0)
        #expect(!aug.isCurrentMonth)
    }

    @Test func gridOpensOnTodayWhenTodayIsInTheWeekElseThatWeeksThursday() {
        let w2 = PlanCalendar.focusDate(week: 2, plan: plan, workouts: workouts, now: now)
        #expect(PlanCalendar.ymd(w2) == "2026-10-07")
        let w5 = PlanCalendar.focusDate(week: 5, plan: plan, workouts: workouts, now: now)
        #expect(PlanCalendar.ymd(w5) == "2026-10-29")
    }
}
