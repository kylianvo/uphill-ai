import Foundation
import Observation

@Observable
@MainActor
final class PlanSetupViewModel {
    enum Mode: Equatable { case onboarding, newPlan }
    enum Direction { case forward, backward }

    var draft: PlanSetupDraft
    private(set) var stepIndex = 0
    private(set) var direction: Direction = .forward
    private(set) var showIssues = false
    private(set) var isSubmitting = false
    private(set) var submitError: String?
    private(set) var didStart = false

    let mode: Mode
    private let service: any GenerationServicing
    private let generation: GenerationCenter
    private let session: SessionStore
    private let now: () -> Date
    private let calendar: Calendar
    private let raceService: RaceMatchService?
    let goalEstimateService: (any GoalEstimateServicing)?
    let raceHistoryService: (any RaceHistoryServicing)?
    var selectedRace: RaceMatch?
    var raceCandidates: [RaceMatch] = []
    /// Set once the athlete links a UTMB or VBM profile during setup.
    var linkedRaceHistory = false

    init(mode: Mode, user: User?, service: any GenerationServicing, generation: GenerationCenter,
         session: SessionStore, now: @escaping () -> Date = { .now }, calendar: Calendar = PlanCalendar.calendar, raceService: RaceMatchService? = nil,
         goalEstimateService: (any GoalEstimateServicing)? = nil, raceHistoryService: (any RaceHistoryServicing)? = nil) {
        self.raceService = raceService
        self.goalEstimateService = goalEstimateService
        self.raceHistoryService = raceHistoryService
        self.mode = mode
        self.service = service
        self.generation = generation
        self.session = session
        self.now = now
        self.calendar = calendar
        draft = PlanSetupDraft(prefill: user, today: now(), calendar: calendar)
    }

    var today: Date { calendar.startOfDay(for: now()) }
    var earliestRaceDate: Date { calendar.date(byAdding: .day, value: 14, to: today)! }

    func reopenAtReview() {
        didStart = false
        jump(to: .review)
    }

    func jump(to step: SetupStep) {
        guard let index = steps.firstIndex(of: step) else { return }
        direction = index < stepIndex ? .backward : .forward
        stepIndex = index
        showIssues = false
    }

    var steps: [SetupStep] { SetupStep.steps(for: draft.goal, includeProfile: mode == .onboarding) }
    var step: SetupStep { steps[min(stepIndex, steps.count - 1)] }
    var progress: Double { Double(min(stepIndex, steps.count - 1) + 1) / Double(max(steps.count, 1)) }
    var isFirstStep: Bool { stepIndex == 0 }
    var isLastStep: Bool { step == .review }
    var primaryTitle: String {
        if isLastStep { return L("Build my plan") }
        if step == .raceHistory, !linkedRaceHistory { return L("Skip for now") }
        return L("Next")
    }

    var issues: [SetupIssue] {
        showIssues ? draft.issues(for: step, today: now(), calendar: calendar) : []
    }

    func issue(for field: SetupField) -> String? {
        issues.first { $0.field == field }?.message
    }

    var latestStartDate: Date { calendar.date(byAdding: .day, value: 14, to: today)! }
    var weeksToRace: Int { max(0, calendar.dateComponents([.day], from: today, to: draft.raceDate ?? earliestRaceDate).day ?? 0) / 7 }

    func searchRace() async {
        let name = draft.raceName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard draft.goal == .race, step == .details, selectedRace?.raceName != name else { return }
        selectedRace = nil
        raceCandidates = []
        guard name.count >= 3, let raceService else { return }
        let initialDistance = draft.distanceKm
        let initialElevation = draft.elevationGainM
        do {
            try await Task.sleep(for: .milliseconds(500))
            let result = try await raceService.match(name: name)
            try Task.checkCancellation()
            guard draft.raceName.trimmingCharacters(in: .whitespacesAndNewlines) == name else { return }
            if result.autoApply == true, let match = result.match {
                let typedDistance = draft.distanceKm
                let typedElevation = draft.elevationGainM
                selectRace(match)
                if typedDistance != initialDistance {
                    draft.distanceKm = typedDistance
                    draft.distanceLabel = nil
                }
                if typedElevation != initialElevation { draft.elevationGainM = typedElevation }
            }
            else { raceCandidates = result.candidates ?? [] }
        } catch { }
    }

    func selectRace(_ race: RaceMatch) {
        draft.raceName = race.raceName
        selectedRace = race
        raceCandidates = []
        if let km = race.distanceKm {
            draft.distanceKm = km
            draft.elevationGainM = race.elevationGainM
            draft.distanceLabel = race.distanceLabel
        } else if let only = raceDistances.first, raceDistances.count == 1 {
            pickDistance(only)
        }
    }

    /// Distances the selected race offers, shortest first.
    var raceDistances: [RaceDistance] {
        (selectedRace?.distances ?? []).sorted { $0.distanceKm < $1.distanceKm }
    }

    func pickDistance(_ distance: RaceDistance) {
        draft.distanceKm = distance.distanceKm
        draft.elevationGainM = distance.elevationGainM
        draft.distanceLabel = distance.label
    }

    func isPicked(_ distance: RaceDistance) -> Bool {
        draft.distanceKm == distance.distanceKm && draft.distanceLabel == distance.label
    }

    /// Goal Determiner result: a target in minutes becomes the race's time goal.
    func applyEstimatedGoal(minutes: Double) {
        draft.raceGoal = .time
        draft.targetMinutes = Int(minutes.rounded())
    }

    func selectGoal(_ goal: SetupGoal) {
        draft.goal = goal
        if goal.isEvent, draft.raceDate == nil { draft.raceDate = earliestRaceDate }
        next()
    }

    func selectRaceGoal(_ goal: RaceGoal) {
        draft.raceGoal = goal
        if goal == .time, draft.targetMinutes == nil { draft.targetMinutes = 390 }
    }

    func next() {
        guard draft.issues(for: step, today: now(), calendar: calendar).isEmpty else {
            showIssues = true
            return
        }
        showIssues = false
        direction = .forward
        stepIndex = min(stepIndex + 1, steps.count - 1)
    }

    func back() {
        showIssues = false
        direction = .backward
        stepIndex = max(stepIndex - 1, 0)
    }

    func setDaysPerWeek(_ n: Int) {
        let count = min(max(n, 3), 7)
        draft.daysPerWeek = count
        draft.preferredDays = PlanSetupDraft.defaultDays(count: count)
        draft.doubleSessionDays.formIntersection(draft.preferredDays)
        if !draft.preferredDays.contains(draft.longRunDay) {
            draft.longRunDay = draft.preferredDays.contains(.saturday) ? .saturday : draft.orderedDays.last!
        }
    }

    func toggleDay(_ day: Weekday) {
        if draft.preferredDays.contains(day) {
            draft.preferredDays.remove(day)
            draft.doubleSessionDays.remove(day)
        } else {
            draft.preferredDays.insert(day)
        }
        if (3...7).contains(draft.preferredDays.count) { draft.daysPerWeek = draft.preferredDays.count }
        if !draft.preferredDays.contains(draft.longRunDay), let last = draft.orderedDays.last {
            draft.longRunDay = draft.preferredDays.contains(.saturday) ? .saturday : last
        }
    }

    func toggleDoubleDay(_ day: Weekday) {
        if draft.doubleSessionDays.contains(day) {
            draft.doubleSessionDays.remove(day)
        } else if draft.doubleSessionDays.count < 2, draft.preferredDays.contains(day) {
            draft.doubleSessionDays.insert(day)
        }
    }

    func submit() async {
        guard !isSubmitting else { return }
        isSubmitting = true
        submitError = nil
        defer { isSubmitting = false }
        do {
            let jobID: String?
            switch mode {
            case .onboarding:
                jobID = try await service.completeOnboarding(draft.onboardingBody(skipPlan: false, calendar: calendar)).jobId
            case .newPlan:
                jobID = try await service.generatePlan(draft.planBody(calendar: calendar)).jobId
            }
            guard let jobID else {
                submitError = L("We couldn't start building your plan. Please try again.")
                return
            }
            generation.track(kind: .newPlan, jobID: jobID, summary: draft.summaryLines)
            didStart = true
        } catch let error as APIError {
            submitError = error.userMessage
        } catch {
            submitError = error.localizedDescription
        }
    }

    func saveProfileOnly() async {
        guard mode == .onboarding, !isSubmitting else { return }
        isSubmitting = true
        submitError = nil
        defer { isSubmitting = false }
        do {
            let result = try await service.completeOnboarding(draft.onboardingBody(skipPlan: true, calendar: calendar))
            if let user = result.user { session.setUser(user) }
            didStart = true
        } catch let error as APIError {
            submitError = error.userMessage
        } catch {
            submitError = error.localizedDescription
        }
    }
}
