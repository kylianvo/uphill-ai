import Foundation
import SwiftUI

struct DayVolume: Identifiable, Equatable, Sendable {
    var id: String { weekday.rawValue }
    let weekday: Weekday
    let km: Double
    let minutes: Double
    let primaryType: String
    let color: Color
    let isDone: Bool
    let isToday: Bool
    let isRest: Bool
    let workoutCount: Int
}

struct WeekVolume: Equatable, Sendable {
    let week: Int
    let km: Double
    let minutes: Double
    let gainM: Double
    let generated: Bool
    let actualKm: Double
    let phase: String?

    var hours: Double { (minutes / 60 * 10).rounded() / 10 }

    init(
        week: Int,
        km: Double,
        minutes: Double,
        gainM: Double,
        generated: Bool,
        actualKm: Double = 0.0,
        phase: String? = nil
    ) {
        self.week = week
        self.km = km
        self.minutes = minutes
        self.gainM = gainM
        self.generated = generated
        self.actualKm = actualKm
        self.phase = phase
    }
}

struct WeekVolumeComparison: Equatable, Sendable {
    let currentHours: Double
    let previousHours: Double?
    let diffHours: Double?
    let plannedKm: Double
    let actualKm: Double
    let adherencePct: Int
}

enum DayState: Equatable, Sendable {
    case done, missed, planned, rest
}

struct DayStatus: Equatable, Sendable {
    let weekday: Weekday
    let state: DayState
}

/// Port of frontend/src/utils/planSummary.ts.
enum PlanSummary {
    static func volume(week: Int, workouts: [Workout]) -> WeekVolume {
        let items = workouts.filter { $0.weekNumber == week }
        let actualKm = items.filter(\.isDone).reduce(0.0) { $0 + ($1.distanceKm ?? 0) }
        let phase = (items.first { !$0.isRest } ?? items.first)?.phase
        return WeekVolume(
            week: week,
            km: items.reduce(0) { $0 + ($1.distanceKm ?? 0) },
            minutes: items.reduce(0) { $0 + $1.durationMinutes },
            gainM: items.reduce(0) { $0 + ($1.elevationGainM ?? 0) },
            generated: !items.isEmpty,
            actualKm: actualKm,
            phase: phase
        )
    }

    static func volumeComparison(week: Int, workouts: [Workout]) -> WeekVolumeComparison {
        let currentItems = workouts.filter { $0.weekNumber == week }
        let currentMins = currentItems.reduce(0.0) { $0 + $1.durationMinutes }
        let currentHours = (currentMins / 60.0 * 10).rounded() / 10

        let previousItems = workouts.filter { $0.weekNumber == week - 1 }
        let previousHours: Double? = {
            guard week > 1, !previousItems.isEmpty else { return nil }
            let mins = previousItems.reduce(0.0) { $0 + $1.durationMinutes }
            return (mins / 60.0 * 10).rounded() / 10
        }()

        let diffHours = previousHours.map { ((currentHours - $0) * 10).rounded() / 10 }

        let plannedKm = currentItems.reduce(0.0) { $0 + ($1.distanceKm ?? 0) }
        let actualKm = currentItems.filter { $0.isDone }.reduce(0.0) { $0 + ($1.distanceKm ?? 0) }

        let active = currentItems.filter { !$0.isRest }
        let done = active.filter { $0.isDone }
        let adherence = active.isEmpty ? 100 : Int((Double(done.count) / Double(active.count) * 100.0).rounded())

        return WeekVolumeComparison(
            currentHours: currentHours,
            previousHours: previousHours,
            diffHours: diffHours,
            plannedKm: plannedKm,
            actualKm: actualKm,
            adherencePct: adherence
        )
    }

    static func weeklyVolumes(_ workouts: [Workout], totalWeeks: Int) -> [WeekVolume] {
        let lastWeek = max(totalWeeks, workouts.map(\.weekNumber).max() ?? 0)
        guard lastWeek > 0 else { return [] }
        return (1...lastWeek).map { volume(week: $0, workouts: workouts) }
    }

    static func isRestDay(_ dayWorkouts: [Workout]) -> Bool {
        dayWorkouts.allSatisfy(\.isRest)
    }

    static func dayStates(week: Int, workouts: [Workout]) -> [DayStatus] {
        Weekday.allCases.map { day in
            let active = workouts.filter { $0.weekNumber == week && $0.weekday == day && !$0.isRest }
            let state: DayState
            if active.isEmpty { state = .rest }
            else if active.allSatisfy(\.isDone) { state = .done }
            else if active.contains(where: \.isMissedFlag) { state = .missed }
            else { state = .planned }
            return DayStatus(weekday: day, state: state)
        }
    }

    static func dayVolumes(
        week: Int,
        workouts: [Workout],
        now: Date = Date(),
        plan: Plan? = nil,
        calendar: Calendar = PlanCalendar.calendar
    ) -> [DayVolume] {
        Weekday.allCases.map { day in
            let dayWorkouts = workouts.filter { $0.weekNumber == week && $0.weekday == day }
            let km = dayWorkouts.reduce(0.0) { $0 + ($1.distanceKm ?? 0) }
            let minutes = dayWorkouts.reduce(0.0) { $0 + $1.durationMinutes }
            let isRest = dayWorkouts.isEmpty || dayWorkouts.allSatisfy(\.isRest)
            let isDone = !dayWorkouts.isEmpty && dayWorkouts.allSatisfy(\.isDone)

            let primaryWorkout = dayWorkouts.first { !$0.isRest } ?? dayWorkouts.first
            let primaryType = primaryWorkout?.type ?? (isRest ? "Rest" : "Workout")
            let color: Color = {
                if isRest { return UH.Palette.line }
                if let w = primaryWorkout { return WorkoutTypePresentation.zoneColor(for: w) }
                return UH.Palette.accentInk
            }()

            let isToday: Bool = {
                guard let plan else { return false }
                guard let date = PlanCalendar.date(week: week, weekday: day, plan: plan, workouts: workouts, calendar: calendar) else { return false }
                return calendar.isDate(date, inSameDayAs: now)
            }()

            return DayVolume(
                weekday: day,
                km: km,
                minutes: minutes,
                primaryType: primaryType,
                color: color,
                isDone: isDone,
                isToday: isToday,
                isRest: isRest,
                workoutCount: dayWorkouts.count
            )
        }
    }

    static func phase(week: Int, workouts: [Workout]) -> String? {
        let items = workouts.filter { $0.weekNumber == week }
        return (items.first { !$0.isRest } ?? items.first)?.phase
    }
}
