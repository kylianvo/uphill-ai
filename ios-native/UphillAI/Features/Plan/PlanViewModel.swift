import Foundation
import Observation

struct PlanDay: Identifiable, Equatable {
    let week: Int
    let weekday: Weekday
    let date: Date?
    let workouts: [Workout]
    let eyebrow: String?

    var id: String { "\(week)-\(weekday.rawValue)" }
    var isToday: Bool { eyebrow == "TODAY" }
    var isRest: Bool { PlanSummary.isRestDay(workouts) }
    /// Rest days collapse unless something on them was logged.
    var isCollapsed: Bool { isRest && !workouts.contains { $0.isDone || $0.isMissedFlag } }
}

struct MoveTarget: Identifiable, Hashable {
    let week: Int
    let weekday: Weekday
    let date: Date
    var id: String { "\(week)-\(weekday.rawValue)" }
}

@Observable
@MainActor
final class PlanViewModel {
    enum LoadState: Equatable { case loading, empty, loaded, failed(String) }

    static let offlineMessage = "You're offline. Changes need a connection."

    private(set) var state: LoadState = .loading
    private(set) var snapshot: PlanSnapshot?
    /// Set while the screen shows cached data because the last fetch failed.
    private(set) var cachedAt: Date?
    var selectedWeek = 1
    private(set) var actionError: String?
    /// Last workout marked done; the view keys its success haptic on it.
    private(set) var lastCompletedID: Int?

    private let service: any PlanServicing
    private let cache: OfflineCache
    private let now: @MainActor () -> Date
    private let calendar: Calendar
    /// Writes finishing after sign-out must not repopulate the offline cache.
    private let isSignedIn: @MainActor () -> Bool

    init(service: any PlanServicing, cache: OfflineCache,
         now: @escaping @MainActor () -> Date = { .now }, calendar: Calendar = PlanCalendar.calendar,
         isSignedIn: @escaping @MainActor () -> Bool = { true }) {
        self.isSignedIn = isSignedIn
        self.service = service
        self.cache = cache
        self.now = now
        self.calendar = calendar
    }

    // MARK: Loading

    func load() async {
        let hadSnapshot = snapshot != nil
        if !hadSnapshot, let cached = cache.load(PlanSnapshot.self, .plan) {
            apply(cached.value, resetWeek: true)
            cachedAt = cached.savedAt
        }
        do {
            if let fresh = try await service.activePlan() {
                let resetWeek = !hadSnapshot && cachedAt == nil
                apply(fresh, resetWeek: resetWeek)
                cachedAt = nil
                if isSignedIn() { cache.save(fresh, as: .plan) }
            } else {
                snapshot = nil
                cachedAt = nil
                cache.remove(.plan)
                state = .empty
            }
        } catch let error as APIError {
            if case .transport = error, snapshot != nil {
                cachedAt = cache.load(PlanSnapshot.self, .plan)?.savedAt ?? now()
                return
            }
            if snapshot == nil { state = .failed(error.userMessage) }
        } catch {
            if snapshot == nil { state = .failed(error.localizedDescription) }
        }
    }

    private func apply(_ snapshot: PlanSnapshot, resetWeek: Bool) {
        self.snapshot = snapshot
        state = .loaded
        if resetWeek { selectedWeek = currentWeek }
    }

    // MARK: Derived values

    var currentWeek: Int {
        guard let snapshot else { return 1 }
        return PlanCalendar.resolveCurrentWeek(plan: snapshot.plan, workouts: snapshot.workouts, now: now(), calendar: calendar)
    }

    var weeks: [Int] {
        guard let snapshot else { return [] }
        let last = max(snapshot.plan.totalWeeks, snapshot.workouts.map(\.weekNumber).max() ?? 0)
        return last > 0 ? Array(1...last) : []
    }

    var days: [PlanDay] {
        guard let snapshot else { return [] }
        let today = now()
        return Weekday.allCases.map { weekday in
            let date = PlanCalendar.date(week: selectedWeek, weekday: weekday, plan: snapshot.plan,
                                         workouts: snapshot.workouts, calendar: calendar)
            return PlanDay(
                week: selectedWeek,
                weekday: weekday,
                date: date,
                workouts: snapshot.workouts.filter { $0.weekNumber == selectedWeek && $0.weekday == weekday },
                eyebrow: PlanCalendar.eyebrow(for: date, now: today, calendar: calendar)
            )
        }
    }

    var selectedVolume: WeekVolume { PlanSummary.volume(week: selectedWeek, workouts: snapshot?.workouts ?? []) }

    var weeklyVolumes: [WeekVolume] {
        guard let snapshot else { return [] }
        return PlanSummary.weeklyVolumes(snapshot.workouts, totalWeeks: snapshot.plan.totalWeeks)
    }

    var dayStates: [DayStatus] {
        PlanSummary.dayStates(week: selectedWeek, workouts: snapshot?.workouts ?? [])
    }

    var phase: String? { PlanSummary.phase(week: selectedWeek, workouts: snapshot?.workouts ?? []) }

    var daysToRace: Int? { PlanCalendar.daysToRace(snapshot?.plan.raceDate, now: now(), calendar: calendar) }

    var goalText: String? {
        guard let plan = snapshot?.plan else { return nil }
        switch plan.goalType {
        case "time":
            guard let hours = plan.targetTimeHours else { return nil }
            let total = Int((hours * 60).rounded())
            return "Goal \(total / 60)h \(String(format: "%02d", total % 60))m"
        case "finish": return "Goal: finish strong"
        case "optimal": return "Goal: best possible time"
        default: return nil
        }
    }

    // MARK: Writes

    func clearActionError() { actionError = nil }

    func setDone(_ workout: Workout, _ done: Bool) async {
        let update = done ? WorkoutLogUpdate(isCompleted: 1) : WorkoutLogUpdate(isCompleted: 0, isMissed: 0)
        if await write({ try await self.service.log(workoutID: workout.id, update) }), done {
            lastCompletedID = workout.id
        }
    }

    func setMissed(_ workout: Workout) async {
        _ = await write { try await self.service.log(workoutID: workout.id, WorkoutLogUpdate(isMissed: 1)) }
    }

    func saveLog(_ workout: Workout, rpe: Int?, notes: String) async -> Bool {
        await write { try await self.service.log(workoutID: workout.id, WorkoutLogUpdate(rpe: rpe, notes: notes)) }
    }

    func moveTargets(for workout: Workout) -> [MoveTarget] {
        guard let snapshot else { return [] }
        let today = calendar.startOfDay(for: now())
        let lastWeek = min(currentWeek + 1, snapshot.plan.totalWeeks)
        var targets: [MoveTarget] = []
        for week in currentWeek...max(currentWeek, lastWeek) {
            for weekday in Weekday.allCases {
                if week == workout.weekNumber && weekday == workout.weekday { continue }
                guard let date = PlanCalendar.date(week: week, weekday: weekday, plan: snapshot.plan,
                                                   workouts: snapshot.workouts, calendar: calendar),
                      date >= today else { continue }
                targets.append(MoveTarget(week: week, weekday: weekday, date: date))
            }
        }
        return targets
    }

    func move(_ workout: Workout, to target: MoveTarget) async -> Bool {
        guard let planID = snapshot?.plan.id else { return false }
        let today = PlanCalendar.ymd(now(), calendar: calendar)
        return await write {
            try await self.service.move(planID: planID, workoutID: workout.id,
                                        toWeek: target.week, toDay: target.weekday, clientToday: today)
        }
    }

    static func moveMessage(code: String?) -> String {
        switch code {
        case "G2_history": "Completed or synced workouts can't be moved."
        case "G3_past_target": "Workouts can't be moved into the past."
        case "G4_window": "Workouts can only move within this week or into next week."
        case "G5_out_of_plan": "That day is outside your plan."
        case "G6_coach_linked": "Your coach manages this workout."
        default: "This workout can't be moved right now."
        }
    }

    /// Runs a write that returns the plan's workouts. Returns true on success.
    private func write(_ operation: () async throws -> [Workout]) async -> Bool {
        guard cachedAt == nil else {
            actionError = Self.offlineMessage
            return false
        }
        actionError = nil
        do {
            let workouts = try await operation()
            guard var snapshot else { return false }
            snapshot.workouts = workouts
            self.snapshot = snapshot
            if isSignedIn() { cache.save(snapshot, as: .plan) }
            return true
        } catch APIError.http(422, _, let code?) {
            actionError = Self.moveMessage(code: code)
        } catch let error as APIError {
            actionError = error.userMessage
        } catch {
            actionError = error.localizedDescription
        }
        return false
    }

    // MARK: Recent plans

    /// Throws on failure so the sheet can show why the list is missing.
    func recentPlans() async throws -> [Plan] {
        try await service.recentPlans()
    }

    func select(_ plan: Plan) async {
        guard cachedAt == nil else {
            actionError = Self.offlineMessage
            return
        }
        do {
            if let snapshot = try await service.selectPlan(id: plan.id) {
                apply(snapshot, resetWeek: true)
                if isSignedIn() { cache.save(snapshot, as: .plan) }
            }
        } catch let error as APIError {
            actionError = error.userMessage
        } catch {
            actionError = error.localizedDescription
        }
    }
}
