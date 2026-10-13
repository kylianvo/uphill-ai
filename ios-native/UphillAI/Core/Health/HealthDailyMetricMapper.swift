import Foundation

/// Turns Health's daily statistics and sleep samples into one upload row per local day.
/// Pure, so the night boundary and source rules are unit-tested without HealthKit.
enum HealthDailyMetricMapper {
    /// One sleep sample. `source` is the writing app's name, used only on the phone to keep
    /// one app's night; `asleep` is false for in-bed and awake samples.
    struct SleepInterval: Sendable, Equatable {
        let start: Date
        let end: Date
        let source: String
        let asleep: Bool
    }

    /// A night runs from 18:00 the day before to 14:00 on the wake date.
    static let nightStartHour = 18
    static let nightEndHour = 14

    /// `yyyy-MM-dd` of `date` in `calendar`'s time zone.
    static func dayKey(_ date: Date, calendar: Calendar) -> String {
        let c = calendar.dateComponents([.year, .month, .day], from: date)
        return String(format: "%04d-%02d-%02d", c.year ?? 0, c.month ?? 0, c.day ?? 0)
    }

    /// The wake date a sample ending at `end` belongs to, or nil for a daytime nap
    /// (ending after 14:00 and before 18:00). Watch writes a night as many stage samples, so
    /// one ending at 23:40 still belongs to the next morning.
    static func wakeDate(for end: Date, calendar: Calendar) -> String? {
        let day = calendar.startOfDay(for: end)
        guard let nightStart = calendar.date(bySettingHour: nightStartHour, minute: 0, second: 0, of: day),
              let nightEnd = calendar.date(bySettingHour: nightEndHour, minute: 0, second: 0, of: day) else { return nil }
        if end >= nightStart, let next = calendar.date(byAdding: .day, value: 1, to: day) {
            return dayKey(next, calendar: calendar)
        }
        return end <= nightEnd ? dayKey(day, calendar: calendar) : nil
    }

    /// Asleep minutes per wake date. Overlapping samples from one app count once; when several
    /// apps recorded the night, the one with the most asleep time wins (sources never add up).
    static func sleepMinutes(_ intervals: [SleepInterval], calendar: Calendar) -> [String: Int] {
        var grouped: [String: [String: [SleepInterval]]] = [:]
        for interval in intervals where interval.asleep && interval.end > interval.start {
            guard let date = wakeDate(for: interval.end, calendar: calendar) else { continue }
            grouped[date, default: [:]][interval.source, default: []].append(interval)
        }
        var result: [String: Int] = [:]
        for (date, sources) in grouped {
            let best = sources.values.map(mergedSeconds).max() ?? 0
            let minutes = Int((best / 60).rounded())
            if minutes > 0 { result[date] = minutes }
        }
        return result
    }

    private static func mergedSeconds(_ intervals: [SleepInterval]) -> TimeInterval {
        var total: TimeInterval = 0
        var current: (start: Date, end: Date)?
        for interval in intervals.sorted(by: { $0.start < $1.start }) {
            if let c = current, interval.start <= c.end {
                current = (c.start, max(c.end, interval.end))
            } else {
                if let c = current { total += c.end.timeIntervalSince(c.start) }
                current = (interval.start, interval.end)
            }
        }
        if let c = current { total += c.end.timeIntervalSince(c.start) }
        return total
    }

    /// One row per date with any value, sorted by date. Resting HR rounds to whole bpm, HRV to 0.1 ms.
    static func rows(restingHr: [String: Double], hrv: [String: Double], sleep: [String: Int]) -> [AppleHealthDailyMetricUpload] {
        let dates = Set(restingHr.keys).union(hrv.keys).union(sleep.keys)
        return dates.sorted().compactMap { date in
            let rhr = restingHr[date].map { Int($0.rounded()) }
            let sdnn = hrv[date].map { ($0 * 10).rounded() / 10 }
            let asleep = sleep[date]
            guard rhr != nil || sdnn != nil || asleep != nil else { return nil }
            return AppleHealthDailyMetricUpload(date: date, restingHr: rhr, hrvSdnnMs: sdnn, sleepMinutes: asleep)
        }
    }
}
