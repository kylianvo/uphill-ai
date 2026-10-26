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
        #expect(v.actualKm == 8.0)
    }

    @Test func weeklyVolumesMarksMissingWeeks() {
        let vols = PlanSummary.weeklyVolumes(week2, totalWeeks: 3)
        #expect(vols.map(\.week) == [1, 2, 3])
        #expect(vols.map(\.generated) == [false, true, false])
        #expect(vols[0].km == 0)
        #expect(vols[1].actualKm == 8.0)
    }

    @Test func dayStates() {
        let states = PlanSummary.dayStates(week: 2, workouts: week2)
        #expect(states.map(\.weekday) == Weekday.allCases)
        #expect(states.map(\.state) == [.rest, .done, .missed, .rest, .rest, .planned, .rest])
    }

    @Test func dayVolumesCalculatesDailyMetrics() {
        let days = PlanSummary.dayVolumes(week: 2, workouts: week2)
        #expect(days.count == 7)
        #expect(days.map(\.weekday) == Weekday.allCases)
        #expect(days[0].isRest == true)
        #expect(days[0].km == 0.0)
        #expect(days[1].weekday == .tuesday)
        #expect(days[1].km == 8.0)
        #expect(days[1].minutes == 60.0)
        #expect(days[1].isDone == true)
        #expect(days[1].isRest == false)
        #expect(days[2].weekday == .wednesday)
        #expect(days[2].km == 7.0)
        #expect(days[5].weekday == .saturday)
        #expect(days[5].km == 18.0)
    }

    @Test func restDayRules() {
        #expect(PlanSummary.isRestDay([]))
        #expect(PlanSummary.isRestDay([TestData.workout(["type": "Rest", "duration_minutes": 0])]))
        #expect(!PlanSummary.isRestDay([TestData.workout(["type": "Rest", "duration_minutes": 0]),
                                         TestData.workout(["id": 2, "duration_minutes": 20])]))
    }

    @Test func volumeComparisonCalculatesHoursAndAdherence() {
        let comp = PlanSummary.volumeComparison(week: 2, workouts: week2)
        #expect(comp.currentHours == 3.8)
        #expect(comp.plannedKm == 33.0)
        #expect(comp.actualKm == 8.0)
        #expect(comp.adherencePct == 33) // 1 of 3 active done
    }

    @Test func volumeComparisonCarriesTheWeeksDPlusAndItsTarget() {
        let oldLanguage = UserDefaults.standard.string(forKey: AppLanguage.storageKey)
        UserDefaults.standard.set(AppLanguage.en.rawValue, forKey: AppLanguage.storageKey)
        defer { UserDefaults.standard.set(oldLanguage, forKey: AppLanguage.storageKey) }
        let comp = PlanSummary.volumeComparison(week: 2, workouts: week2, vertTargets: ["2": 1200, "3": 1300])
        #expect(comp.plannedVertM == 1030)
        #expect(comp.vertTargetM == 1200)
        #expect(SummaryCarousel.vertLine(comp) == "1,030 of 1,200 m D+ target")
        let noTarget = PlanSummary.volumeComparison(week: 2, workouts: week2)
        #expect(SummaryCarousel.vertLine(noTarget) == "1,030 m D+")
        let flat = PlanSummary.volumeComparison(week: 9, workouts: week2)
        #expect(SummaryCarousel.vertLine(flat) == nil)
    }

    @Test func planDecodesWeeklyVertTargets() {
        #expect(TestData.plan(["weekly_vert_targets": ["1": 600, "9": 2210]]).weeklyVertTargets?["9"] == 2210)
    }

    @Test func volumeComparisonCalculatesPreviousWeekDiff() {
        let w1 = [TestData.workout(["week_number": 1, "duration_minutes": 180, "distance_km": 25.0])]
        let w2 = [TestData.workout(["week_number": 2, "duration_minutes": 240, "distance_km": 35.0])]
        let comp = PlanSummary.volumeComparison(week: 2, workouts: w1 + w2)
        #expect(comp.currentHours == 4.0)
        #expect(comp.previousHours == 3.0)
        #expect(comp.diffHours == 1.0)
    }

    @Test func phaseUsesFirstNonRestWorkoutOfWeek() {
        #expect(PlanSummary.phase(week: 2, workouts: week2) == "Base")
        #expect(PlanSummary.phase(week: 5, workouts: week2) == nil)
    }

    @Test func weekLineFull() {
        let v = WeekVolume(week: 6, km: 52, minutes: 450, gainM: 0, generated: true, phase: "Build")
        #expect(PlanSummary.weekLine(v) == "Week 6 · Build · 7.5 h · 52 km")
    }

    @Test func weekLineNoKm() {
        let v = WeekVolume(week: 3, km: 0, minutes: 240, gainM: 0, generated: true, phase: "Base")
        #expect(PlanSummary.weekLine(v) == "Week 3 · Base · 4 h")
    }

    @Test func weekLineNoPhase() {
        let v = WeekVolume(week: 1, km: 40, minutes: 330, gainM: 0, generated: true)
        #expect(PlanSummary.weekLine(v) == "Week 1 · 5.5 h · 40 km")
    }

    @Test func weekLineEmptyWeekHasNoZeroHours() {
        let v = WeekVolume(week: 12, km: 0, minutes: 0, gainM: 0, generated: true, phase: "Taper")
        #expect(PlanSummary.weekLine(v) == "Week 12 · Taper")
    }

    @Test func trendLabelsKeepSelectedAndSpaceTheRest() {
        #expect(PlanSummary.trendLabelWeeks(total: 13, selected: 1) == [1, 4, 8, 13])
        #expect(PlanSummary.trendLabelWeeks(total: 13, selected: 7) == [1, 4, 7, 13])
        #expect(PlanSummary.trendLabelWeeks(total: 24, selected: 10) == [1, 4, 10, 16, 20, 24])
        #expect(PlanSummary.trendLabelWeeks(total: 0, selected: 1) == [])
    }

    @Test func courseLineShowsDistanceAndGain() {
        #expect(PlanSummary.courseLine(km: 100, gainM: 5533) == "100 km · 5,533 m D+")
        #expect(PlanSummary.courseLine(km: 42.2, gainM: nil) == "42.2 km")
        #expect(PlanSummary.courseLine(km: nil, gainM: 800) == nil)
    }
}
