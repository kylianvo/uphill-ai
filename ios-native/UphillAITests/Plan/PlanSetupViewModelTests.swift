import Foundation
import Testing
@testable import UphillAI

@MainActor
struct PlanSetupViewModelTests {
    private let cal: Calendar = {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        return c
    }()
    private var now: Date { PlanCalendar.day(from: "2026-10-07", calendar: cal)! }

    private func make(_ mode: PlanSetupViewModel.Mode, service: FakeGenerationService = FakeGenerationService())
        -> (PlanSetupViewModel, FakeGenerationService, GenerationCenter, SessionStore) {
        let session = SessionStore(tokenStore: InMemoryTokenStore())
        let center = GenerationCenter(service: service, defaults: UserDefaults(suiteName: UUID().uuidString)!,
                                      makePoller: { JobPoller(service: $0, interval: .seconds(60), timeout: .seconds(120)) })
        let now = self.now
        let model = PlanSetupViewModel(mode: mode, user: nil, service: service, generation: center,
                                       session: session, now: { now }, calendar: cal)
        return (model, service, center, session)
    }

    @Test func goalTapAdvances() {
        let (model, _, _, _) = make(.onboarding)
        #expect(model.step == .goal)
        model.selectGoal(.startRunning)
        #expect(model.step == .schedule)
        #expect(model.steps == [.goal, .schedule, .aboutYou, .review])
        #expect(model.direction == .forward)
    }

    @Test func newPlanSkipsAboutYou() {
        let (model, _, _, _) = make(.newPlan)
        model.selectGoal(.race)
        #expect(model.steps == [.goal, .details, .schedule, .review])
    }

    @Test func nextStaysAndShowsIssuesWhenInvalid() {
        let (model, _, _, _) = make(.onboarding)
        model.selectGoal(.race)
        #expect(model.issues.isEmpty)          // nothing shown before trying
        model.next()
        #expect(model.step == .details)
        #expect(model.issue(for: .raceName) == "Add the race name.")
    }

    @Test func backGoesBackward() {
        let (model, _, _, _) = make(.onboarding)
        model.selectGoal(.startRunning)
        model.back()
        #expect(model.step == .goal)
        #expect(model.direction == .backward)
        model.back()
        #expect(model.stepIndex == 0)
    }

    @Test func daysPerWeekResetsDays() {
        let (model, _, _, _) = make(.onboarding)
        model.setDaysPerWeek(3)
        #expect(model.draft.preferredDays == [.tuesday, .thursday, .saturday])
        #expect(model.draft.preferredDays.contains(model.draft.longRunDay))
        model.toggleDay(.saturday)
        #expect(!model.draft.preferredDays.contains(.saturday))
    }

    @Test func submitOnboardingTracksJob() async {
        let (model, service, center, _) = make(.onboarding)
        model.selectGoal(.startRunning)
        await model.submit()
        #expect(service.calls.withLock { $0 }.first == "onboarding skip=false")
        #expect(center.running?.jobID == "job-1")
        #expect(center.running?.kind == .newPlan)
        #expect(model.didStart)
        center.reset()
    }

    @Test func submitNewPlanUsesGeneratePlan() async {
        let (model, service, center, _) = make(.newPlan)
        model.selectGoal(.startRunning)
        await model.submit()
        #expect(service.calls.withLock { $0 }.first == "generate start_running")
        center.reset()
    }

    @Test func submitErrorKeepsDraft() async {
        let service = FakeGenerationService()
        service.startResult.withLock { $0 = .failure(.http(status: 500, message: nil, code: nil)) }
        let (model, _, center, _) = make(.newPlan, service: service)
        model.selectGoal(.startRunning)
        await model.submit()
        #expect(model.submitError == "Something went wrong (500). Please try again.")
        #expect(model.draft.goal == .startRunning)
        #expect(!model.didStart)
        #expect(center.running == nil)
    }

    @Test func saveProfileOnlySetsUser() async throws {
        let user = try Fixture.decode(User.self, "auth_me.json")
        let service = FakeGenerationService()
        service.onboardingResult.withLock { $0 = .success(OnboardingResult(jobId: nil, user: user)) }
        let (model, _, center, session) = make(.onboarding, service: service)
        model.selectGoal(.startRunning)
        await model.saveProfileOnly()
        #expect(service.calls.withLock { $0 } == ["onboarding skip=true"])
        #expect(session.user == user)
        #expect(center.running == nil)
        #expect(model.didStart)
    }

    @Test func primaryTitle() {
        let (model, _, _, _) = make(.newPlan)
        model.selectGoal(.startRunning)
        #expect(model.primaryTitle == "Next")
        model.next()
        #expect(model.step == .review)
        #expect(model.primaryTitle == "Build my plan")
    }
}
