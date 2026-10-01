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

    init(mode: Mode, user: User?, service: any GenerationServicing, generation: GenerationCenter,
         session: SessionStore, now: @escaping () -> Date = { .now }, calendar: Calendar = PlanCalendar.calendar) {
        self.mode = mode
        self.service = service
        self.generation = generation
        self.session = session
        self.now = now
        self.calendar = calendar
        draft = PlanSetupDraft(prefill: user, today: now(), calendar: calendar)
    }

    var steps: [SetupStep] { SetupStep.steps(for: draft.goal, includeAboutYou: mode == .onboarding) }
    var step: SetupStep { steps[min(stepIndex, steps.count - 1)] }
    var progress: Double { Double(min(stepIndex, steps.count - 1) + 1) / Double(max(steps.count, 1)) }
    var isFirstStep: Bool { stepIndex == 0 }
    var isLastStep: Bool { step == .review }
    var primaryTitle: String { isLastStep ? "Build my plan" : "Next" }

    var issues: [SetupIssue] {
        showIssues ? draft.issues(for: step, today: now(), calendar: calendar) : []
    }

    func issue(for field: SetupField) -> String? {
        issues.first { $0.field == field }?.message
    }

    func selectGoal(_ goal: SetupGoal) {
        draft.goal = goal
        next()
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
        if !draft.preferredDays.contains(draft.longRunDay) {
            draft.longRunDay = draft.preferredDays.contains(.saturday) ? .saturday : draft.orderedDays.last!
        }
    }

    func toggleDay(_ day: Weekday) {
        if draft.preferredDays.contains(day) { draft.preferredDays.remove(day) } else { draft.preferredDays.insert(day) }
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
                submitError = "We couldn't start building your plan. Please try again."
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
