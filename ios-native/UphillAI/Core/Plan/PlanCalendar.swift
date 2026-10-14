struct CalendarDayCell: Identifiable, Equatable, Sendable {
    let date: Date
    let isCurrentMonth: Bool
    let isToday: Bool
    let isRaceDay: Bool
    let weekNumber: Int?
    let workouts: [Workout]

    var id: String { PlanCalendar.ymd(date) }
    var primaryWorkout: Workout? { workouts.first { !$0.isRest } ?? workouts.first }
}

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

extension CalendarDayCell {
    /// Non-rest workouts, in plan order.
    var sessions: [Workout] { workouts.filter { !$0.isRest } }
    var km: Double { sessions.reduce(0) { $0 + ($1.distanceKm ?? 0) } }
}

extension Workout {
    /// Weight behind a calendar bar's height: km, else minutes at a flat ~10 min/km so
    /// strength and cross sessions still show. shortcut: no real effort model, add one if non-run load must rank.
    var calendarLoad: Double { (distanceKm ?? 0) > 0 ? distanceKm! : durationMinutes / 10 }
}

/// One Monday-to-Sunday row of the month grid.
struct CalendarWeekRow: Identifiable, Equatable, Sendable {
    let cells: [CalendarDayCell]
    var id: String { cells[0].id }
    /// Plan week, shared by all seven days; nil outside the plan.
    var weekNumber: Int? { cells[0].weekNumber }
    var km: Double { cells.reduce(0) { $0 + $1.km } }
    var containsToday: Bool { cells.contains(where: \.isToday) }
}

/// A month of the plan laid out for the calendar grid, with the totals its header and bars need.
struct CalendarMonth: Equatable, Sendable {
    let weeks: [CalendarWeekRow]
    let isCurrentMonth: Bool
    /// Month-only totals (days spilling in from a neighbouring month are not counted).
    let km: Double
    let hours: Double
    let sessionsDone: Int
    let sessionsTotal: Int
    /// Plan-wide scale for the bars, so heights compare across months: the biggest single session
    /// (race day left out, or one event flattens every training day) and the biggest week.
    let maxSessionLoad: Double
    let maxWeekKm: Double

    static func make(month: Date, plan: Plan?, workouts: [Workout], now: Date,
                     calendar: Calendar = PlanCalendar.calendar) -> CalendarMonth {
        let first = calendar.date(from: calendar.dateComponents([.year, .month], from: month))!
        let dayCount = calendar.range(of: .day, in: .month, for: first)!.count
        let last = calendar.date(byAdding: .day, value: dayCount - 1, to: first)!
        let start = PlanCalendar.monday(of: first, calendar: calendar)
        let end = calendar.date(byAdding: .day, value: 6, to: PlanCalendar.monday(of: last, calendar: calendar))!

        let weekOne = plan.flatMap { PlanCalendar.weekOneMonday(plan: $0, workouts: workouts, calendar: calendar) }
        let lastWeek = plan.map { max($0.totalWeeks, workouts.map(\.weekNumber).max() ?? 0) } ?? 0
        var byDay: [String: [Workout]] = [:]
        if let weekOne {
            for w in workouts {
                guard let d = calendar.date(byAdding: .day, value: (w.weekNumber - 1) * 7 + w.weekday.offset, to: weekOne) else { continue }
                byDay[PlanCalendar.ymd(d, calendar: calendar), default: []].append(w)
            }
        }
        let raceDay = PlanCalendar.day(from: plan?.raceDate, calendar: calendar)

        var rows: [CalendarWeekRow] = []
        var cells: [CalendarDayCell] = []
        var day = start
        while day <= end {
            var week: Int?
            if let weekOne {
                let days = calendar.dateComponents([.day], from: weekOne, to: day).day ?? 0
                let n = Int((Double(days) / 7).rounded(.down)) + 1
                week = (1...max(lastWeek, 1)).contains(n) ? n : nil
            }
            cells.append(CalendarDayCell(
                date: day,
                isCurrentMonth: calendar.isDate(day, equalTo: first, toGranularity: .month),
                isToday: calendar.isDate(day, inSameDayAs: now),
                isRaceDay: raceDay.map { calendar.isDate(day, inSameDayAs: $0) } ?? false,
                weekNumber: week,
                workouts: byDay[PlanCalendar.ymd(day, calendar: calendar)] ?? []
            ))
            if cells.count == 7 { rows.append(CalendarWeekRow(cells: cells)); cells = [] }
            day = calendar.date(byAdding: .day, value: 1, to: day)!
        }

        let raceKey = raceDay.map { PlanCalendar.ymd($0, calendar: calendar) }
        var weekKm: [Int: Double] = [:]
        for w in workouts where !w.isRest { weekKm[w.weekNumber, default: 0] += w.distanceKm ?? 0 }

        let inMonth = rows.flatMap(\.cells).filter(\.isCurrentMonth).flatMap(\.sessions)
        return CalendarMonth(
            weeks: rows,
            isCurrentMonth: calendar.isDate(now, equalTo: first, toGranularity: .month),
            km: inMonth.reduce(0) { $0 + ($1.distanceKm ?? 0) },
            hours: inMonth.reduce(0) { $0 + $1.durationMinutes } / 60,
            sessionsDone: inMonth.filter(\.isDone).count,
            sessionsTotal: inMonth.count,
            maxSessionLoad: byDay.filter { $0.key != raceKey }.values.flatMap { $0 }.filter { !$0.isRest }.map(\.calendarLoad).max() ?? 0,
            maxWeekKm: weekKm.values.max() ?? 0
        )
    }
}

extension PlanCalendar {
    /// The date whose month the grid opens on: today when it falls inside `week`, else that week's Thursday
    /// (the day that decides which month a week mostly belongs to).
    static func focusDate(week: Int, plan: Plan, workouts: [Workout], now: Date, calendar: Calendar = calendar) -> Date {
        guard let monday = date(week: week, weekday: .monday, plan: plan, workouts: workouts, calendar: calendar) else { return now }
        let days = calendar.dateComponents([.day], from: monday, to: calendar.startOfDay(for: now)).day ?? -1
        return (0...6).contains(days) ? now : calendar.date(byAdding: .day, value: 3, to: monday)!
    }
}
