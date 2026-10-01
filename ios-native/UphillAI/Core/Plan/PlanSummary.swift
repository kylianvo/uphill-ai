import Foundation

struct WeekVolume: Equatable, Sendable {
    let week: Int
    let km: Double
    let minutes: Double
    let gainM: Double
    let generated: Bool

    var hours: Double { (minutes / 60 * 10).rounded() / 10 }
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
        return WeekVolume(
            week: week,
            km: items.reduce(0) { $0 + ($1.distanceKm ?? 0) },
            minutes: items.reduce(0) { $0 + $1.durationMinutes },
            gainM: items.reduce(0) { $0 + ($1.elevationGainM ?? 0) },
            generated: !items.isEmpty
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

    static func phase(week: Int, workouts: [Workout]) -> String? {
        let items = workouts.filter { $0.weekNumber == week }
        return (items.first { !$0.isRest } ?? items.first)?.phase
    }
}
