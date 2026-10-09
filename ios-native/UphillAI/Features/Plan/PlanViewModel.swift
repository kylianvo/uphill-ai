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

struct NextWeekOffer: Equatable {
    let blockNumber: Int
    let weekStart: Int
    let weekEnd: Int
    let previousCompletionPct: Double?
    let unlocked: Bool

    var title: String { weekStart == weekEnd ? L("Build week %lld", weekStart) : L("Build weeks %lld–%lld", weekStart, weekEnd) }
}

enum NextWeekResult: Equatable {
    case started, needsConfirmation(String), failed(String)
}

enum FatigueLevel: String, CaseIterable, Identifiable {
    case easy, medium, hard, exhausted

    var id: String { rawValue }
    var title: String {
        switch self {
        case .easy: L("Fresh")
        case .medium: L("Normal tiredness")
        case .hard: L("Heavy legs")
        case .exhausted: L("Exhausted")
        }
    }
    var subtitle: String {
        switch self {
        case .easy: L("Ready for more")
        case .medium: L("About what I expected")
        case .hard: L("Struggling to hit the paces")
        case .exhausted: L("I need a lighter week")
        }
    }
}

@Observable
@MainActor
final class PlanViewModel {
    enum LoadState: Equatable { case loading, empty, loaded, failed(String) }

    static var offlineMessage: String { L("You're offline. Changes need a connection.") }

    private(set) var state: LoadState = .loading
    private(set) var snapshot: PlanSnapshot?
    /// Set while the screen shows cached data because the last fetch failed.
    private(set) var cachedAt: Date?
    var selectedWeek = 1
    private(set) var actionError: String?
    private(set) var calendarNotice: ScheduleNotice?
    /// Last workout marked done; the view keys its success haptic on it.
    private(set) var lastCompletedID: Int?

    private(set) var blockCompletion: BlockCompletionResponse?
    private(set) var nextWeekOffer: NextWeekOffer?
    private(set) var goal: PlanGoal?
    private(set) var isSyncingWatch = false
    private(set) var watchSyncNotice: String?
    private(set) var contextKnowledgeCard: KnowledgeCardModel?

    private let service: any PlanServicing
    private let generation: GenerationCenter?
    private let generationService: (any GenerationServicing)?
    private let cache: OfflineCache
    private let now: @MainActor () -> Date
    private let calendar: Calendar
    /// Writes finishing after sign-out must not repopulate the offline cache.
    private let isSignedIn: @MainActor () -> Bool

    init(service: any PlanServicing, cache: OfflineCache,
         now: @escaping @MainActor () -> Date = { .now }, calendar: Calendar = PlanCalendar.calendar,
         isSignedIn: @escaping @MainActor () -> Bool = { true },
         generation: GenerationCenter? = nil, generationService: (any GenerationServicing)? = nil) {
        self.isSignedIn = isSignedIn
        self.generation = generation
        self.generationService = generationService
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
                await loadBlockCompletion()
                await loadGoal()
                await loadKnowledgeCard()
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

    func syncWatch() async -> String? {
        guard !isSyncingWatch else { return nil }
        guard let plan = snapshot?.plan else { return L("No active plan to sync.") }
        isSyncingWatch = true
        defer { isSyncingWatch = false }
        do {
            let msg = try await service.syncWatch(planID: plan.id)
            await load()
            watchSyncNotice = msg
            return msg
        } catch let apiError as APIError {
            let msg: String
            switch apiError {
            // A 401 here is the Uphill session, not COROS; COROS problems come back as 400 with a message.
            case .unauthorized, .http(status: 401, _, _):
                msg = L("Your session expired. Please sign in again.")
            default:
                msg = apiError.userMessage
            }
            watchSyncNotice = msg
            return msg
        } catch {
            let msg = L("Couldn't sync watch activities. Please try again.")
            watchSyncNotice = msg
            return msg
        }
    }

    func clearWatchSyncNotice() {
        watchSyncNotice = nil
    }


    private func apply(_ snapshot: PlanSnapshot, resetWeek: Bool) {
        self.snapshot = snapshot
        state = .loaded
        if resetWeek { selectedWeek = currentWeek }
    }

    /// A freshly generated plan or week from a finished job.
    func adopt(_ snapshot: PlanSnapshot) {
        apply(snapshot, resetWeek: true)
        cachedAt = nil
        actionError = nil
        if isSignedIn() { cache.save(snapshot, as: .plan) }
        Task { await loadBlockCompletion(); await loadGoal(); await loadKnowledgeCard() }
    }

    func reset() {
        blockCompletion = nil
        nextWeekOffer = nil
        goal = nil
        state = .loading
        snapshot = nil
        cachedAt = nil
        selectedWeek = 1
        actionError = nil
        lastCompletedID = nil
        calendarNotice = nil
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

    func days(for week: Int) -> [PlanDay] {
        guard let snapshot else { return [] }
        let today = now()
        return Weekday.allCases.map { weekday in
            let date = PlanCalendar.date(week: week, weekday: weekday, plan: snapshot.plan,
                                         workouts: snapshot.workouts, calendar: calendar)
            return PlanDay(
                week: week,
                weekday: weekday,
                date: date,
                workouts: snapshot.workouts.filter { $0.weekNumber == week && $0.weekday == weekday },
                eyebrow: PlanCalendar.eyebrow(for: date, now: today, calendar: calendar)
            )
        }
    }

    var days: [PlanDay] { days(for: selectedWeek) }

    var selectedVolume: WeekVolume { PlanSummary.volume(week: selectedWeek, workouts: snapshot?.workouts ?? []) }

    var weekComparison: WeekVolumeComparison {
        PlanSummary.volumeComparison(week: selectedWeek, workouts: snapshot?.workouts ?? [])
    }

    var weeklyVolumes: [WeekVolume] {
        guard let snapshot else { return [] }
        return PlanSummary.weeklyVolumes(snapshot.workouts, totalWeeks: snapshot.plan.totalWeeks)
    }

    var dayStates: [DayStatus] {
        PlanSummary.dayStates(week: selectedWeek, workouts: snapshot?.workouts ?? [])
    }

    var dayVolumes: [DayVolume] {
        guard let snapshot else { return [] }
        return PlanSummary.dayVolumes(week: selectedWeek, workouts: snapshot.workouts, now: now(), plan: snapshot.plan, calendar: calendar)
    }

    func dayVolumes(for week: Int) -> [DayVolume] {
        guard let snapshot else { return [] }
        return PlanSummary.dayVolumes(week: week, workouts: snapshot.workouts, now: now(), plan: snapshot.plan, calendar: calendar)
    }

    var phase: String? { PlanSummary.phase(week: selectedWeek, workouts: snapshot?.workouts ?? []) }

    var maxGeneratedWeek: Int {
        if let maxFromBlock = blockCompletion?.maxGeneratedWeek, maxFromBlock > 0 {
            return maxFromBlock
        }
        return snapshot?.workouts.map(\.weekNumber).max() ?? 0
    }

    func isWeekUngenerated(_ week: Int) -> Bool {
        guard let snapshot, week > 0 else { return false }
        if let maxGen = blockCompletion?.maxGeneratedWeek, maxGen > 0 {
            return week > maxGen
        }
        let weekWorkouts = snapshot.workouts.filter { $0.weekNumber == week }
        if weekWorkouts.isEmpty { return true }
        let hasActiveWorkout = weekWorkouts.contains { !$0.isRest }
        return !hasActiveWorkout
    }

    func canAdaptWeek(_ week: Int) -> Bool {
        return !isWeekUngenerated(week) && week <= maxGeneratedWeek
    }

    var selectedWeekNarrative: BlockCompletion? {
        guard let blockCompletion else { return nil }
        return blockCompletion.blocks.first { block in
            (block.weekStart...block.weekEnd).contains(selectedWeek)
        }
    }

    var daysToRace: Int? { PlanCalendar.daysToRace(snapshot?.plan.raceDate, now: now(), calendar: calendar) }

    var goalText: String? {
        guard let plan = snapshot?.plan else { return nil }
        switch plan.goalType {
        case "time":
            guard let hours = plan.targetTimeHours else { return nil }
            let total = Int((hours * 60).rounded())
            return L("Goal %lldh %@m", total / 60, String(format: "%02d", total % 60))
        case "finish": return L("Goal: finish strong")
        case "optimal": return L("Goal: best possible time")
        default: return nil
        }
    }

    // MARK: Writes

    func clearActionError() { actionError = nil }
    func dismissCalendarNotice() { calendarNotice = nil }

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
        let generatedWeeks = snapshot.workouts.map(\.weekNumber).max() ?? currentWeek
        let lastWeek = min(currentWeek + 1, snapshot.plan.totalWeeks, generatedWeeks)
        guard lastWeek >= currentWeek else { return [] }
        let generated = Set(snapshot.workouts.map(\.weekNumber))
        var targets: [MoveTarget] = []
        for week in currentWeek...max(currentWeek, lastWeek) {
            guard generated.contains(week) else { continue }
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
        calendarNotice = nil
        guard let planID = snapshot?.plan.id else { return false }
        let today = PlanCalendar.ymd(now(), calendar: calendar)
        return await write {
            let result = try await self.service.move(planID: planID, workoutID: workout.id,
                                        toWeek: target.week, toDay: target.weekday, clientToday: today)
            if !result.warnings.isEmpty {
                self.calendarNotice = ScheduleNotice(text: L("Heads-up: ") + result.warnings.map(ScheduleMessages.warningText).joined(separator: "\n"), style: .warning)
            }
            return result.workouts
        }
    }

    func swapDays(week: Int, day1: Weekday, day2: Weekday) async -> Bool {
        calendarNotice = nil
        guard let planID = snapshot?.plan.id else { return false }
        let today = PlanCalendar.ymd(now(), calendar: calendar)
        return await write {
            let result = try await self.service.swapDays(planID: planID, weekNumber: week, day1: day1, day2: day2, clientToday: today)
            if !result.warnings.isEmpty {
                self.calendarNotice = ScheduleNotice(text: L("Heads-up: ") + result.warnings.map(ScheduleMessages.warningText).joined(separator: "\n"), style: .warning)
            }
            return result.workouts
        }
    }

    func deletePlan(id: Int) async -> Bool {
        guard cachedAt == nil else {
            actionError = Self.offlineMessage
            return false
        }
        actionError = nil
        do {
            try await service.deletePlan(id: id)
            if snapshot?.plan.id == id {
                await load()
            }
            return true
        } catch let error as APIError {
            actionError = error.userMessage
            return false
        } catch {
            actionError = error.localizedDescription
            return false
        }
    }

    static func moveMessage(code: String?) -> String {
        ScheduleMessages.guardText(code: code ?? "unknown")
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
        } catch APIError.scheduleGuard(_, let code, let params) {
            actionError = ScheduleMessages.guardText(code: code, params: params)
            calendarNotice = ScheduleNotice(text: actionError!, style: .error)
        } catch APIError.http(422, _, let code?) {
            actionError = Self.moveMessage(code: code)
            calendarNotice = ScheduleNotice(text: actionError!, style: .error)
        } catch let error as APIError {
            actionError = error.userMessage
        } catch {
            actionError = error.localizedDescription
        }
        return false
    }

    // MARK: Next week

    /// The offer exists only on the last generated week while later weeks are still to come.
    func loadBlockCompletion() async {
        guard let snapshot, cachedAt == nil else { return }
        if let response = try? await service.blockCompletion(planID: snapshot.plan.id) {
            self.blockCompletion = response
            updateNextWeekOffer()
        }
    }

    /// The offer exists only on the last generated week while later weeks are still to come.
    func refreshNextWeekOffer() async {
        if blockCompletion == nil, let snapshot, cachedAt == nil {
            if let response = try? await service.blockCompletion(planID: snapshot.plan.id) {
                self.blockCompletion = response
            }
        }
        updateNextWeekOffer()
    }

    private func updateNextWeekOffer() {
        guard let snapshot, cachedAt == nil,
              let response = blockCompletion,
              let generatedWeeks = snapshot.workouts.map(\.weekNumber).max(),
              generatedWeeks < snapshot.plan.totalWeeks,
              (selectedWeek == generatedWeeks || selectedWeek > generatedWeeks),
              let last = response.blocks.max(by: { $0.blockNumber < $1.blockNumber }) else {
            nextWeekOffer = nil
            return
        }
        let start = response.maxGeneratedWeek + 1
        nextWeekOffer = NextWeekOffer(
            blockNumber: last.blockNumber + 1,
            weekStart: start,
            weekEnd: min(start + (last.weekEnd - last.weekStart), snapshot.plan.totalWeeks),
            previousCompletionPct: last.completionPct,
            unlocked: last.unlocked
        )
    }

    func buildNextWeek(rpe: Int?, notes: String, override: Bool, schedule: ScheduleDraft? = nil) async -> NextWeekResult {
        guard let offer = nextWeekOffer, let planID = snapshot?.plan.id,
              let generation, let generationService else { return .failed(L("Couldn't start the next week. Try again.")) }
        guard cachedAt == nil else { return .failed(Self.offlineMessage) }
        let trimmed = notes.trimmingCharacters(in: .whitespacesAndNewlines)
        var body = NextBlockBody(
            planId: planID, blockNumber: offer.blockNumber, overallRpe: rpe,
            notes: trimmed.isEmpty ? nil : trimmed, overrideGate: override, lang: AppLanguage.code)
        schedule?.applyChanges(to: &body)
        do {
            let job = try await generationService.generateNextBlock(body)
            generation.track(kind: .nextWeek, jobID: job.jobId, summary: [])
            return .started
        } catch APIError.http(403, let message?, _) where !override {
            return .needsConfirmation(message)
        } catch APIError.http(400, let message, _) {
            nextWeekOffer = nil
            return .failed(message ?? L("Every week of this plan is already built."))
        } catch let error as APIError {
            return .failed(error.userMessage)
        } catch {
            return .failed(error.localizedDescription)
        }
    }

    // MARK: Adapt and review

    func canAdapt(week: Int) -> Bool {
        guard let snapshot, let last = snapshot.workouts.map(\.weekNumber).max() else { return false }
        return week >= currentWeek && week <= last
    }

    /// Returns an error message, or nil once the job has started.
    func adaptWeek(_ week: Int, fatigue: FatigueLevel, rpe: Int?, notes: String, schedule: ScheduleDraft? = nil) async -> String? {
        guard let planID = snapshot?.plan.id, let generation, let generationService else {
            return L("Couldn't start adapting this week. Try again.")
        }
        guard cachedAt == nil else { return Self.offlineMessage }
        let trimmed = notes.trimmingCharacters(in: .whitespacesAndNewlines)
        do {
            var body = AdaptWeekBody(
                planId: planID, weekNumber: week, overallRpe: rpe, fatigueLevel: fatigue.rawValue,
                fatigueNotes: trimmed.isEmpty ? nil : trimmed, lang: AppLanguage.code,
                clientToday: PlanCalendar.ymd(now(), calendar: calendar))
            schedule?.applyChanges(to: &body)
            let job = try await generationService.adaptWeek(body)
            generation.track(kind: .adaptWeek, jobID: job.jobId, summary: [])
            return nil
        } catch let error as APIError {
            return error.userMessage
        } catch {
            return error.localizedDescription
        }
    }

    func weekReview(_ week: Int) async -> Result<WeekReview, APIError> {
        guard let planID = snapshot?.plan.id else { return .failure(.http(status: 404, message: nil, code: nil)) }
        do {
            return .success(try await service.weekReview(planID: planID, week: week))
        } catch let error as APIError {
            return .failure(error)
        } catch {
            return .failure(.transport(error.localizedDescription))
        }
    }

    // MARK: Goal

    static func formatMinutes(_ minutes: Double) -> String {
        let total = Int(minutes.rounded())
        return "\(total / 60):\(String(format: "%02d", total % 60))"
    }

    /// The suggested time to offer as a new target, when it differs from the current one.
    var suggestedMinutes: Double? {
        guard let goal else { return nil }
        let suggestion = goal.status.suggestedMins ?? goal.assessment?.goals?.b
        guard let suggestion else { return nil }
        if let hours = goal.targetTimeHours, Int((hours * 60).rounded()) == Int(suggestion.rounded()) { return nil }
        return suggestion
    }

    var goalPillText: String? {
        guard let goal, snapshot?.plan.courseDistanceKm != nil else { return nil }
        switch goal.status.kind {
        case .onTrack: return L("On track")
        case .ahead: return L("Ahead of target")
        case .behind: return L("Behind target")
        case .noTarget: return goal.status.suggestedMins.map { L("Suggested %@", Self.formatMinutes($0)) } ?? L("Not assessed yet")
        case .notAssessed: return L("Not assessed yet")
        }
    }


    func loadKnowledgeCard() async {
        guard snapshot?.plan != nil, cachedAt == nil else { return }
        let phase = (self.phase ?? "").lowercased()
        let days = daysToRace

        let topic: String
        if let days, days <= 21 {
            topic = "Pacing"
        } else if phase.contains("taper") || phase.contains("peak") {
            topic = "Pacing"
        } else if phase.contains("recovery") {
            topic = "Recovery"
        } else if phase.contains("strength") || phase.contains("me") {
            topic = "Training"
        } else {
            topic = "Training"
        }

        contextKnowledgeCard = await service.knowledgeCard(topic: topic, lang: AppLanguage.code)
    }

    func loadGoal() async {
        guard let plan = snapshot?.plan, plan.courseDistanceKm != nil, cachedAt == nil else { return }
        if let fresh = try? await service.goal(planID: plan.id) { goal = fresh }
    }

    /// Returns an error message, or nil on success.
    func reassessGoal() async -> String? {
        guard let planID = snapshot?.plan.id else { return nil }
        guard cachedAt == nil else { return Self.offlineMessage }
        do {
            goal = try await service.reassessGoal(planID: planID)
            return nil
        } catch APIError.http(429, _, _) {
            return L("You've used today's goal checks. Try again tomorrow.")
        } catch let error as APIError {
            return error.userMessage
        } catch {
            return error.localizedDescription
        }
    }

    func applySuggestedGoal() async -> String? {
        guard let planID = snapshot?.plan.id, let minutes = suggestedMinutes else { return nil }
        guard cachedAt == nil else { return Self.offlineMessage }
        do {
            goal = try await service.applyGoal(planID: planID, targetMinutes: minutes)
            await load()
            return nil
        } catch let error as APIError {
            return error.userMessage
        } catch {
            return error.localizedDescription
        }
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
                await loadBlockCompletion()
                await loadGoal()
                await loadKnowledgeCard()
            }
        } catch let error as APIError {
            actionError = error.userMessage
        } catch {
            actionError = error.localizedDescription
        }
    }
}
