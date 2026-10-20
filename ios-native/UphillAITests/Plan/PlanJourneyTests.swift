import Foundation
import Testing
@testable import UphillAI

struct PlanJourneyTests {
    private func journey(_ extra: [String: Any] = [:]) throws -> PlanJourney {
        var object: [String: Any] = [
            "current_week": 5, "total_weeks": 12, "days_to_race": 49,
            "phases": [["name": "Base", "start_week": 1, "end_week": 4], ["name": "Build", "start_week": 5, "end_week": 10]],
            "milestones": [["key": "first_recovery_week", "week": 4, "done": true], ["key": "long_run_3h", "week": 6, "done": false]],
            "preferences": ["days_per_week": 4, "long_run_day": "Saturday", "mountain": "chau_thoi"],
            "deviations": [],
        ]
        object.merge(extra) { $1 }
        return try JSONCoding.decoder.decode(PlanJourney.self, from: JSONSerialization.data(withJSONObject: object))
    }

    @Test func decodesPhasesMilestonesAndTheNextOne() throws {
        let j = try journey()
        #expect(j.phases.map(\.weeks) == [4, 6])
        #expect(j.nextMilestone?.key == "long_run_3h")
        #expect(j.nextMilestone?.title == "First 3-hour Long Run")
        #expect(j.followsSchedule)
    }

    @Test func builtAroundYouNamesDaysLongRunAndMountain() throws {
        #expect(try journey().builtAroundYou == "4 days a week · long run Sat · Mountain training")
        let bare = try journey(["preferences": ["days_per_week": NSNull(), "long_run_day": NSNull(), "mountain": NSNull()]])
        #expect(bare.builtAroundYou == "")
    }

    @Test func deviationsMeanThePlanDoesNotFollowTheSchedule() throws {
        #expect(try journey(["deviations": [["code": "LONG_RUN_DAY", "week": 7]]]).followsSchedule == false)
    }

    @Test func coachNudgeDecodesAndNilWhenQuiet() throws {
        let quiet = try JSONCoding.decoder.decode(CoachNudgeResponse.self, from: Data(#"{"nudge":null}"#.utf8))
        #expect(quiet.nudge == nil)
        let loud = try JSONCoding.decoder.decode(CoachNudgeResponse.self, from: Data(#"{"nudge":{"tone":"heads_up","text":"x","source":"rules"}}"#.utf8))
        #expect(loud.nudge?.kind == .headsUp)
    }
}

struct TodayFocusTests {
    private func day(_ weekday: Weekday, today: Bool = false, week: Int = 3, _ workouts: [Workout]) -> PlanDay {
        PlanDay(week: week, weekday: weekday, date: nil, workouts: workouts, eyebrow: today ? "TODAY" : nil)
    }

    private func run(_ weekday: String, title: String, done: Int = 0, missed: Int = 0, week: Int = 3) -> Workout {
        TestData.workout(["id": title.hashValue & 0xFFFF, "week_number": week, "day_of_week": weekday, "title": title,
                          "is_completed": done, "is_missed": missed])
    }

    @Test func aSessionTodayIsTheFocusAndReportsItsState() {
        let todo = TodayFocus.make(days: [day(.wednesday, today: true, [run("Wednesday", title: "Tempo")])], nextWeek: [])
        #expect(todo.workout?.title == "Tempo" && todo.isToday && todo.state == .todo)
        let done = TodayFocus.make(days: [day(.wednesday, today: true, [run("Wednesday", title: "Tempo", done: 1)])], nextWeek: [])
        #expect(done.state == .done)
        let missed = TodayFocus.make(days: [day(.wednesday, today: true, [run("Wednesday", title: "Tempo", missed: 1)])], nextWeek: [])
        #expect(missed.state == .missed)
    }

    @Test func aRestDayPointsAtTheNextOpenSession() {
        let days = [
            day(.tuesday, [run("Tuesday", title: "Done run", done: 1)]),
            day(.wednesday, today: true, []),
            day(.thursday, [run("Thursday", title: "Hills")]),
        ]
        let focus = TodayFocus.make(days: days, nextWeek: [])
        #expect(focus.workout?.title == "Hills" && !focus.isToday && focus.isRestToday)
    }

    @Test func whenTheWeekIsFinishedItLooksToNextWeek() {
        let days = [day(.sunday, today: true, [run("Sunday", title: "Long", done: 1)])]
        let next = [day(.monday, week: 4, [run("Monday", title: "Easy start", week: 4)])]
        let focus = TodayFocus.make(days: days, nextWeek: next)
        #expect(focus.isToday && focus.state == .done)  // today's own session stays the focus until the day ends
        let restDay = TodayFocus.make(days: [day(.sunday, today: true, [])], nextWeek: next)
        #expect(restDay.workout?.title == "Easy start" && restDay.isRestToday)
    }
}
