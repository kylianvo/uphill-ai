import Foundation

/// Plan week and date maths. Port of frontend/src/utils/planDate.ts: weeks run
/// Monday to Sunday and all arithmetic is in local calendar days.
enum PlanCalendar {
    static var calendar: Calendar {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = .current
        return c
    }

    /// "YYYY-MM-DD" (a longer ISO string is cut to its date) → local midnight.
    static func day(from string: String?, calendar: Calendar = calendar) -> Date? {
        guard let s = string?.prefix(10), s.count == 10 else { return nil }
        let parts = s.split(separator: "-")
        guard parts.count == 3, parts[0].count == 4, parts[1].count == 2, parts[2].count == 2,
              let y = Int(parts[0]), let m = Int(parts[1]), let d = Int(parts[2]) else { return nil }
        return calendar.date(from: DateComponents(year: y, month: m, day: d))
    }

    static func ymd(_ date: Date, calendar: Calendar = calendar) -> String {
        let c = calendar.dateComponents([.year, .month, .day], from: date)
        return String(format: "%04d-%02d-%02d", c.year!, c.month!, c.day!)
    }

    static func monday(of date: Date, calendar: Calendar = calendar) -> Date {
        let start = calendar.startOfDay(for: date)
        let weekday = calendar.component(.weekday, from: start)  // 1 = Sunday … 7 = Saturday
        let daysSinceMonday = (weekday + 5) % 7
        return calendar.date(byAdding: .day, value: -daysSinceMonday, to: start)!
    }

    static func weekOneMonday(plan: Plan, workouts: [Workout], calendar: Calendar = calendar) -> Date? {
        if let start = day(from: plan.startDate, calendar: calendar) {
            return monday(of: start, calendar: calendar)
        }
        guard let race = day(from: plan.raceDate, calendar: calendar) else { return nil }
        let raceWorkout = workouts.first {
            $0.title.uppercased().contains("TARGET EVENT") || $0.type.uppercased() == "RACE"
        }
        let raceWeek = raceWorkout?.weekNumber ?? plan.totalWeeks
        return calendar.date(byAdding: .day, value: -(raceWeek - 1) * 7, to: monday(of: race, calendar: calendar))
    }

    static func date(week: Int, weekday: Weekday, plan: Plan, workouts: [Workout], calendar: Calendar = calendar) -> Date? {
        guard let weekOne = weekOneMonday(plan: plan, workouts: workouts, calendar: calendar) else { return nil }
        return calendar.date(byAdding: .day, value: (week - 1) * 7 + weekday.offset, to: weekOne)
    }

    static func currentWeek(plan: Plan, workouts: [Workout], now: Date, calendar: Calendar = calendar) -> Int {
        guard plan.totalWeeks >= 1,
              let weekOne = weekOneMonday(plan: plan, workouts: workouts, calendar: calendar) else { return 1 }
        let days = calendar.dateComponents([.day], from: weekOne, to: calendar.startOfDay(for: now)).day ?? 0
        let week = Int((Double(days) / 7).rounded(.down)) + 1
        return min(max(week, 1), plan.totalWeeks)
    }

    /// The week to show by default: the calendar week, but never past the last generated week.
    static func resolveCurrentWeek(plan: Plan, workouts: [Workout], now: Date, calendar: Calendar = calendar) -> Int {
        let week = currentWeek(plan: plan, workouts: workouts, now: now, calendar: calendar)
        let maxGenerated = workouts.map(\.weekNumber).max() ?? 0
        return maxGenerated > 0 ? min(week, maxGenerated) : week
    }

    /// Whole days from today to the race; nil when unknown or past.
    static func daysToRace(_ raceDate: String?, now: Date, calendar: Calendar = calendar) -> Int? {
        guard let race = day(from: raceDate, calendar: calendar) else { return nil }
        let days = calendar.dateComponents([.day], from: calendar.startOfDay(for: now), to: race).day ?? -1
        return days >= 0 ? days : nil
    }

    static func eyebrow(for date: Date?, now: Date, calendar: Calendar = calendar) -> String? {
        guard let date else { return nil }
        if calendar.isDate(date, inSameDayAs: now) { return "TODAY" }
        let tomorrow = calendar.date(byAdding: .day, value: 1, to: calendar.startOfDay(for: now))!
        return calendar.isDate(date, inSameDayAs: tomorrow) ? "TOMORROW" : nil
    }
}
