import Testing
import SwiftUI
@testable import UphillAI

@Suite("WorkoutRowTests")
struct WorkoutRowTests {
    private func makeWorkout(
        id: Int = 1,
        title: String = "Easy Aerobic Run",
        type: String = "Easy Run",
        duration: Double = 45,
        km: Double? = 7.5,
        pace: String? = "6:00 /km",
        zone: String = "Z2",
        isPriority: Bool = false,
        isCompleted: Int? = 0,
        isMissed: Int? = 0,
        slot: String? = "main",
        matchedId: Int? = nil
    ) -> Workout {
        let json = """
        {
            "id": \(id),
            "plan_id": 1,
            "week_number": 1,
            "day_of_week": "Monday",
            "phase": "Base",
            "title": "\(title)",
            "type": "\(type)",
            "duration_minutes": \(duration),
            "distance_km": \(km != nil ? String(km!) : "null"),
            "target_zone": "\(zone)",
            "target_pace": \(pace != nil ? "\"\(pace!)\"" : "null"),
            "is_completed": \(isCompleted != nil ? String(isCompleted!) : "null"),
            "is_missed": \(isMissed != nil ? String(isMissed!) : "null"),
            "is_priority": \(isPriority),
            "session_slot": \(slot != nil ? "\"\(slot!)\"" : "null"),
            "matched_activity_id": \(matchedId.map(String.init) ?? "null")
        }
        """.data(using: .utf8)!
        return try! JSONCoding.decoder.decode(Workout.self, from: json)
    }

    @Test func chipLabels() {
        #expect(WorkoutTypePresentation.chipLabel(for: makeWorkout(type: "Easy Run")) == "Easy")
        #expect(WorkoutTypePresentation.chipLabel(for: makeWorkout(type: "Long Run")) == "Long")
        #expect(WorkoutTypePresentation.chipLabel(for: makeWorkout(type: "Hill Repeats")) == "Intervals")
        #expect(WorkoutTypePresentation.chipLabel(for: makeWorkout(type: "Recovery Run")) == "Recovery")
        #expect(WorkoutTypePresentation.chipLabel(for: makeWorkout(type: "Muscular Endurance")) == "ME")
        #expect(WorkoutTypePresentation.chipLabel(for: makeWorkout(type: "Strength")) == "Strength")
        #expect(WorkoutTypePresentation.chipLabel(for: makeWorkout(type: "Tempo")) == "Tempo")
    }

    @Test func rowStatus() {
        #expect(WorkoutTypePresentation.rowStatus(for: makeWorkout(isCompleted: 1, matchedId: 9)) == .matched)
        #expect(WorkoutTypePresentation.rowStatus(for: makeWorkout(isCompleted: 1)) == .done)
        #expect(WorkoutTypePresentation.rowStatus(for: makeWorkout(isMissed: 1)) == .missed)
        #expect(WorkoutTypePresentation.rowStatus(for: makeWorkout()) == .none)
    }

    @Test func formatMetrics() {
        let w1 = makeWorkout(duration: 45, km: 7.5, pace: "6:00 /km")
        #expect(WorkoutTypePresentation.formatMetrics(for: w1) == "45 min · 7.5 km · 6:00 /km")

        let w2 = makeWorkout(duration: 60, km: nil, pace: nil)
        #expect(WorkoutTypePresentation.formatMetrics(for: w2) == "60 min")
    }

    @Test func zoneColorNotClear() {
        let easyColor = WorkoutTypePresentation.zoneColor(for: makeWorkout(type: "Easy Run", zone: "Z2"))
        let intervalColor = WorkoutTypePresentation.zoneColor(for: makeWorkout(type: "Hill Repeats", zone: "Z4"))
        #expect(easyColor != intervalColor)
    }

    @Test func unloggedPastWaitsOneDayAndIgnoresDoneMissedAndRest() {
        let cal = PlanCalendar.calendar
        let sat = cal.date(from: DateComponents(year: 2026, month: 10, day: 17))!
        let sun = cal.date(byAdding: .day, value: 1, to: sat)!
        let mon = cal.date(byAdding: .day, value: 2, to: sat)!
        #expect(!PlanCalendar.isUnloggedPast(makeWorkout(), on: sat, now: sun))
        #expect(PlanCalendar.isUnloggedPast(makeWorkout(), on: sat, now: mon))
        #expect(!PlanCalendar.isUnloggedPast(makeWorkout(isCompleted: 1), on: sat, now: mon))
        #expect(!PlanCalendar.isUnloggedPast(makeWorkout(isMissed: 1), on: sat, now: mon))
        #expect(!PlanCalendar.isUnloggedPast(makeWorkout(type: "Rest", duration: 0), on: sat, now: mon))
    }
}
