import Foundation
import Testing
@testable import UphillAI

struct PlanCalendarTests {
    private let cal: Calendar = {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        return c
    }()

    private func d(_ s: String, hour: Int = 9) -> Date {
        let day = PlanCalendar.day(from: s, calendar: cal)!
        return cal.date(byAdding: .hour, value: hour, to: day)!
    }

    @Test func parsesDayStringsAndRejectsJunk() {
        #expect(PlanCalendar.ymd(PlanCalendar.day(from: "2026-09-30T00:00:00", calendar: cal)!, calendar: cal) == "2026-09-30")
        #expect(PlanCalendar.day(from: nil, calendar: cal) == nil)
        #expect(PlanCalendar.day(from: "2026-9-3", calendar: cal) == nil)
        #expect(PlanCalendar.day(from: "garbage!!", calendar: cal) == nil)
    }

    @Test func mondayOfAnyDay() {
        #expect(PlanCalendar.ymd(PlanCalendar.monday(of: d("2026-09-30"), calendar: cal), calendar: cal) == "2026-09-28")
        #expect(PlanCalendar.ymd(PlanCalendar.monday(of: d("2026-10-04"), calendar: cal), calendar: cal) == "2026-09-28") // Sunday
        #expect(PlanCalendar.ymd(PlanCalendar.monday(of: d("2026-09-28"), calendar: cal), calendar: cal) == "2026-09-28")
    }

    @Test func weekOneFromStartDate() {
        let plan = TestData.plan(["start_date": "2026-09-30"])
        let monday = PlanCalendar.weekOneMonday(plan: plan, workouts: [], calendar: cal)!
        #expect(PlanCalendar.ymd(monday, calendar: cal) == "2026-09-28")
    }

    @Test func weekOneFromRaceDateUsesTotalWeeks() {
        let plan = TestData.plan(["start_date": NSNull(), "race_date": "2026-12-19", "total_weeks": 12])
        let monday = PlanCalendar.weekOneMonday(plan: plan, workouts: [], calendar: cal)!
        #expect(PlanCalendar.ymd(monday, calendar: cal) == "2026-09-28")
    }

    @Test func weekOneFromRaceDateUsesRaceWorkoutWeek() {
        let plan = TestData.plan(["start_date": NSNull(), "race_date": "2026-12-19", "total_weeks": 12])
        let race = TestData.workout(["week_number": 10, "title": "TARGET EVENT: VMM", "type": "Race"])
        let monday = PlanCalendar.weekOneMonday(plan: plan, workouts: [race], calendar: cal)!
        #expect(PlanCalendar.ymd(monday, calendar: cal) == "2026-10-12")
    }

    @Test func dateOfWeekday() {
        let plan = TestData.plan(["start_date": "2026-09-30"])
        let date = PlanCalendar.date(week: 2, weekday: .saturday, plan: plan, workouts: [], calendar: cal)!
        #expect(PlanCalendar.ymd(date, calendar: cal) == "2026-10-10")
    }

    @Test(arguments: [
        ("2026-09-20", 1),  // before the plan starts
        ("2026-09-28", 1),
        ("2026-10-04", 1),  // Sunday of week 1
        ("2026-10-05", 2),
        ("2027-06-01", 12), // after the plan ends
    ])
    func currentWeek(now: String, expected: Int) {
        let plan = TestData.plan(["start_date": "2026-09-30", "total_weeks": 12])
        #expect(PlanCalendar.currentWeek(plan: plan, workouts: [], now: d(now), calendar: cal) == expected)
    }

    @Test func currentWeekAcrossDSTChange() {
        var ny = Calendar(identifier: .gregorian)
        ny.timeZone = TimeZone(identifier: "America/New_York")!
        let plan = TestData.plan(["start_date": "2026-10-26", "total_weeks": 12])
        let now = PlanCalendar.day(from: "2026-11-02", calendar: ny)!  // DST ended Nov 1
        #expect(PlanCalendar.currentWeek(plan: plan, workouts: [], now: now, calendar: ny) == 2)
    }

    @Test func resolveCurrentWeekClampsToGeneratedWeeks() {
        let plan = TestData.plan(["start_date": "2026-09-30", "total_weeks": 12])
        let workouts = [TestData.workout(["week_number": 1]), TestData.workout(["id": 2, "week_number": 2])]
        #expect(PlanCalendar.resolveCurrentWeek(plan: plan, workouts: workouts, now: d("2026-11-20"), calendar: cal) == 2)
        #expect(PlanCalendar.resolveCurrentWeek(plan: plan, workouts: [], now: d("2026-11-20"), calendar: cal) == 8)
    }

    @Test func daysToRace() {
        #expect(PlanCalendar.daysToRace("2026-10-10", now: d("2026-10-01", hour: 23), calendar: cal) == 9)
        #expect(PlanCalendar.daysToRace("2026-10-01", now: d("2026-10-01"), calendar: cal) == 0)
        #expect(PlanCalendar.daysToRace("2026-09-30", now: d("2026-10-01"), calendar: cal) == nil)
        #expect(PlanCalendar.daysToRace(nil, now: d("2026-10-01"), calendar: cal) == nil)
    }

    @Test func eyebrow() {
        let now = d("2026-10-01", hour: 22)
        #expect(PlanCalendar.eyebrow(for: d("2026-10-01", hour: 0), now: now, calendar: cal) == "TODAY")
        #expect(PlanCalendar.eyebrow(for: d("2026-10-02", hour: 0), now: now, calendar: cal) == "TOMORROW")
        #expect(PlanCalendar.eyebrow(for: d("2026-10-03", hour: 0), now: now, calendar: cal) == nil)
        #expect(PlanCalendar.eyebrow(for: nil, now: now, calendar: cal) == nil)
    }
}
