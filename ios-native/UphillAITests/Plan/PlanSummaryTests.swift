import Foundation
import Testing
@testable import UphillAI

struct PlanSummaryTests {
    private let week2 = [
        TestData.workout(["id": 1, "week_number": 2, "day_of_week": "Monday", "type": "Rest", "duration_minutes": 0, "distance_km": NSNull(), "elevation_gain_m": 0]),
        TestData.workout(["id": 2, "week_number": 2, "day_of_week": "Tuesday", "duration_minutes": 60, "distance_km": 8.0, "elevation_gain_m": 350, "is_completed": 1]),
        TestData.workout(["id": 3, "week_number": 2, "day_of_week": "Wednesday", "duration_minutes": 45, "distance_km": 7.0, "elevation_gain_m": 80, "is_missed": 1]),
        TestData.workout(["id": 4, "week_number": 2, "day_of_week": "Saturday", "duration_minutes": 120, "distance_km": 18.0, "elevation_gain_m": 600, "phase": "Build"]),
    ]

    @Test func volumeSumsOneWeek() {
        let v = PlanSummary.volume(week: 2, workouts: week2)
        #expect(v.km == 33.0)
        #expect(v.minutes == 225)
        #expect(v.hours == 3.8)
        #expect(v.gainM == 1030)
        #expect(v.generated)
    }

    @Test func weeklyVolumesMarksMissingWeeks() {
        let vols = PlanSummary.weeklyVolumes(week2, totalWeeks: 3)
        #expect(vols.map(\.week) == [1, 2, 3])
        #expect(vols.map(\.generated) == [false, true, false])
        #expect(vols[0].km == 0)
    }

    @Test func dayStates() {
        let states = PlanSummary.dayStates(week: 2, workouts: week2)
        #expect(states.map(\.weekday) == Weekday.allCases)
        #expect(states.map(\.state) == [.rest, .done, .missed, .rest, .rest, .planned, .rest])
    }

    @Test func restDayRules() {
        #expect(PlanSummary.isRestDay([]))
        #expect(PlanSummary.isRestDay([TestData.workout(["type": "Rest", "duration_minutes": 0])]))
        #expect(!PlanSummary.isRestDay([TestData.workout(["type": "Rest", "duration_minutes": 0]),
                                         TestData.workout(["id": 2, "duration_minutes": 20])]))
    }

    @Test func phaseUsesFirstNonRestWorkoutOfWeek() {
        #expect(PlanSummary.phase(week: 2, workouts: week2) == "Base")
        #expect(PlanSummary.phase(week: 5, workouts: week2) == nil)
    }
}
