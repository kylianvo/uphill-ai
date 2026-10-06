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
}
