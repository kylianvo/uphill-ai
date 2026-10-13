import Foundation
import Testing
@testable import UphillAI

struct HealthDailyMetricMapperTests {
    typealias Interval = HealthDailyMetricMapper.SleepInterval

    func calendar(_ id: String) -> Calendar {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: id)!
        return c
    }

    func at(_ text: String, _ cal: Calendar) -> Date {
        let f = DateFormatter()
        f.calendar = cal
        f.timeZone = cal.timeZone
        f.locale = Locale(identifier: "en_US_POSIX")
        f.dateFormat = "yyyy-MM-dd HH:mm"
        return f.date(from: text)!
    }

    @Test func overlappingSamplesFromOneSourceCountOnce() {
        let cal = calendar("Asia/Ho_Chi_Minh")
        let sleep = HealthDailyMetricMapper.sleepMinutes([
            Interval(start: at("2026-10-12 23:00", cal), end: at("2026-10-13 03:00", cal), source: "Watch", asleep: true),
            Interval(start: at("2026-10-13 02:00", cal), end: at("2026-10-13 06:00", cal), source: "Watch", asleep: true),
        ], calendar: cal)
        #expect(sleep == ["2026-10-13": 420])
    }

    @Test func theSourceWithMoreSleepWinsAndSourcesNeverAdd() {
        let cal = calendar("Asia/Ho_Chi_Minh")
        let sleep = HealthDailyMetricMapper.sleepMinutes([
            Interval(start: at("2026-10-12 23:20", cal), end: at("2026-10-13 06:00", cal), source: "Watch", asleep: true),
            Interval(start: at("2026-10-12 23:00", cal), end: at("2026-10-13 06:10", cal), source: "AutoSleep", asleep: true),
        ], calendar: cal)
        #expect(sleep == ["2026-10-13": 430])
    }

    @Test func afternoonNapIsExcluded() {
        let cal = calendar("Asia/Ho_Chi_Minh")
        let sleep = HealthDailyMetricMapper.sleepMinutes([
            Interval(start: at("2026-10-13 14:30", cal), end: at("2026-10-13 15:00", cal), source: "Watch", asleep: true),
        ], calendar: cal)
        #expect(sleep.isEmpty)
    }

    @Test func nightLandsOnTheWakeDateIncludingStagesBeforeMidnight() {
        let cal = calendar("Asia/Ho_Chi_Minh")
        let sleep = HealthDailyMetricMapper.sleepMinutes([
            Interval(start: at("2026-10-12 23:30", cal), end: at("2026-10-12 23:55", cal), source: "Watch", asleep: true),
            Interval(start: at("2026-10-12 23:55", cal), end: at("2026-10-13 06:45", cal), source: "Watch", asleep: true),
            Interval(start: at("2026-10-13 06:45", cal), end: at("2026-10-13 07:00", cal), source: "Watch", asleep: false),
        ], calendar: cal)
        #expect(sleep == ["2026-10-13": 435])
    }

    @Test func dstNightCountsRealMinutes() {
        // 2026-11-01 02:00 EDT falls back to 01:00 EST: 23:00 → 07:00 is 9 hours asleep.
        let cal = calendar("America/New_York")
        let sleep = HealthDailyMetricMapper.sleepMinutes([
            Interval(start: at("2026-10-31 23:00", cal), end: at("2026-11-01 07:00", cal), source: "Watch", asleep: true),
        ], calendar: cal)
        #expect(sleep == ["2026-11-01": 540])
    }

    @Test func rowsUnionDatesRoundAndSort() {
        let rows = HealthDailyMetricMapper.rows(
            restingHr: ["2026-10-13": 51.6, "2026-10-12": 50.2],
            hrv: ["2026-10-13": 61.44],
            sleep: ["2026-10-11": 400]
        )
        #expect(rows == [
            AppleHealthDailyMetricUpload(date: "2026-10-11", restingHr: nil, hrvSdnnMs: nil, sleepMinutes: 400),
            AppleHealthDailyMetricUpload(date: "2026-10-12", restingHr: 50, hrvSdnnMs: nil, sleepMinutes: nil),
            AppleHealthDailyMetricUpload(date: "2026-10-13", restingHr: 52, hrvSdnnMs: 61.4, sleepMinutes: nil),
        ])
    }
}
