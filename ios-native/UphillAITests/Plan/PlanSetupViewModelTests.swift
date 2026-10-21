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

    private func make(_ mode: PlanSetupViewModel.Mode, service: FakeGenerationService = FakeGenerationService(),
                      loadWatchVolume: (@Sendable () async -> WatchVolume?)? = nil,
                      connectAppleHealth: (@MainActor () async -> String?)? = nil)
        -> (PlanSetupViewModel, FakeGenerationService, GenerationCenter, SessionStore) {
        let session = SessionStore(tokenStore: InMemoryTokenStore())
        let center = GenerationCenter(service: service, defaults: UserDefaults(suiteName: UUID().uuidString)!,
                                      makePoller: { JobPoller(service: $0, interval: .seconds(60), timeout: .seconds(120)) })
        let now = self.now
        let model = PlanSetupViewModel(mode: mode, user: nil, service: service, generation: center,
                                       session: session, now: { now }, calendar: cal, loadWatchVolume: loadWatchVolume,
                                       connectAppleHealth: connectAppleHealth)
        return (model, service, center, session)
    }

    @Test func raceAndNonRacePathsHaveSingleQuestionScreens() {
        let (model, _, _, _) = make(.onboarding)
        model.selectGoal(.race)
        #expect(model.steps.count == 12)
        model.back()
        model.selectGoal(.recovery)
        #expect(model.steps == [.goal, .details, .daysSinceRace, .recoveryFeel, .watch, .schedule, .venues, .body, .trainingZones, .raceHistory, .startDate, .review])
    }

    @Test func revisitingSetupKeepsAnEditedCourse() async {
        let (model, _, _, _) = make(.newPlan)
        model.selectGoal(.race)
        model.selectRace(RaceMatch(raceName: "VMM", distanceLabel: "42K", distanceKm: 42, elevationGainM: 2400))
        model.draft.distanceKm = 43
        await model.searchRace()
        #expect(model.selectedRace?.raceName == "VMM")
        #expect(model.draft.raceName == "VMM")
        #expect(model.draft.distanceKm == 43)
    }

    @Test func pendingLookupPreservesCourseEdits() async {
        let (original, service, center, session) = make(.newPlan)
        let base = StubURLProtocol.register { _ in
            (200, json(["matched": true, "auto_apply": true, "match": ["race_name": "VMM", "distance_km": 42, "elevation_gain_m": 2400]]))
        }
        let client = APIClient(baseURL: { base }, tokenStore: InMemoryTokenStore(), session: StubURLProtocol.session())
        let model = PlanSetupViewModel(mode: .newPlan, user: nil, service: service, generation: center, session: session,
                                       now: { original.today }, calendar: cal, raceService: RaceMatchService(client: client))
        model.selectGoal(.race)
        model.draft.raceName = "VMM"
        let lookup = Task { await model.searchRace() }
        await Task.yield()
        model.draft.distanceKm = 43
        model.draft.elevationGainM = 2500
        await lookup.value
        #expect(model.selectedRace?.raceName == "VMM")
        #expect(model.draft.distanceKm == 43)
        #expect(model.draft.elevationGainM == 2500)
    }

    @Test func changingRunCountClearsDoublesOnRemovedDays() {
        let (model, _, _, _) = make(.newPlan)
        model.draft.doubleSessionDays = [.sunday]
        model.setDaysPerWeek(3)
        #expect(model.draft.doubleSessionDays.isEmpty)
    }

    @Test func choosingRaceAppliesCourseValues() {
        let (model, _, _, _) = make(.onboarding)
        model.selectRace(RaceMatch(raceName: "VMM", distanceLabel: "42K", distanceKm: 42, elevationGainM: 2400))
        #expect(model.draft.distanceKm == 42)
        #expect(model.draft.elevationGainM == 2400)
    }

    @Test func raceWithoutDistanceKeepsTypedDistanceAndCanAdvance() {
        let (model, _, _, _) = make(.onboarding)
        model.selectGoal(.race)
        model.draft.raceName = "Vietnam Highlands Trail by UTMB"
        model.draft.distanceKm = 70
        model.selectRace(RaceMatch(raceName: "Vietnam Highlands Trail by UTMB", distanceLabel: nil, distanceKm: nil, elevationGainM: nil))
        #expect(model.draft.distanceKm == 70)
        model.next()
        #expect(model.step == .raceDate)
    }

    @Test func multiDistanceRaceOffersDistancesAndPickFillsCourse() {
        let (model, _, _, _) = make(.onboarding)
        model.selectGoal(.race)
        let race = RaceMatch(raceName: "Vietnam Highlands Trail by UTMB", distanceLabel: nil, distanceKm: nil, elevationGainM: nil,
                             distances: [RaceDistance(label: "100km", distanceKm: 104, elevationGainM: 5533),
                                         RaceDistance(label: "50km / Elephant 50", distanceKm: 55.4, elevationGainM: 3200)])
        model.selectRace(race)
        #expect(model.raceDistances.map(\.distanceKm) == [55.4, 104])
        model.pickDistance(model.raceDistances[0])
        #expect(model.draft.distanceKm == 55.4)
        #expect(model.draft.elevationGainM == 3200)
        #expect(model.isPicked(model.raceDistances[0]))
    }

    @Test func toggledRunDaysDriveCountLongRunAndDoubles() {
        let (model, _, _, _) = make(.onboarding)
        model.draft.preferredDays = [.tuesday, .thursday, .saturday, .sunday]
        model.draft.daysPerWeek = 4
        model.draft.longRunDay = .saturday
        model.toggleDoubleDay(.tuesday)
        model.toggleDay(.saturday)
        #expect(model.draft.daysPerWeek == 3)
        #expect(model.draft.longRunDay == .sunday)
        model.toggleDay(.tuesday)
        #expect(model.draft.doubleSessionDays.isEmpty)
        model.toggleDoubleDay(.monday)
        #expect(model.draft.doubleSessionDays.isEmpty)
    }

    @Test func goalDeterminerResultSetsTimeGoal() {
        let (model, _, _, _) = make(.onboarding)
        model.applyEstimatedGoal(minutes: 412.4)
        #expect(model.draft.raceGoal == .time)
        #expect(model.draft.targetMinutes == 412)
    }

    @Test func appleHealthVolumeIsLabelledAsAppleHealth() async {
        let (model, _, _, _) = make(.newPlan, loadWatchVolume: { WatchVolume(weeklyKm: 52.4, weeklyKmSource: "apple_health") })
        await model.prefillWatchVolume()
        #expect(model.draft.currentWeeklyKm == 52)
        #expect(model.watchVolumeSource == "apple_health")
    }

    @Test func connectingAppleHealthMarksItAndPrefills() async {
        let (model, _, _, _) = make(.newPlan,
                                    loadWatchVolume: { WatchVolume(weeklyKm: 60, weeklyKmSource: "apple_health") },
                                    connectAppleHealth: { nil })
        let error = await model.connectAppleHealth()
        #expect(error == nil)
        #expect(model.appleHealthConnected)
        #expect(model.draft.currentWeeklyKm == 60)
    }

    @Test func appleHealthConnectErrorIsReturned() async {
        let (model, _, _, _) = make(.newPlan, connectAppleHealth: { "Apple Health isn't available on this device." })
        #expect(await model.connectAppleHealth() == "Apple Health isn't available on this device.")
        #expect(!model.appleHealthConnected)
    }

    @Test func watchStepIsNotSkipOnceAppleHealthIsConnected() async {
        let (model, _, _, _) = make(.onboarding, connectAppleHealth: { nil })
        _ = await model.connectAppleHealth()
        model.jump(to: .watch)
        #expect(model.primaryTitle != L("Skip for now"))
    }

    @Test func watchVolumePrefillsUntilTheAthleteTypes() async {
        let (model, _, _, _) = make(.newPlan, loadWatchVolume: { WatchVolume(weeklyKm: 41.6, weeklyKmSource: "coros") })
        model.draft.currentWeeklyKm = 25
        await model.prefillWatchVolume()
        #expect(model.draft.currentWeeklyKm == 42)
        #expect(model.draft.weeklyKmFromWatch)
        #expect(model.draft.planBody(calendar: PlanCalendar.calendar).weeklyKmFromWatch)
        model.setWeeklyKm(50)
        #expect(!model.draft.weeklyKmFromWatch)
        await model.prefillWatchVolume()
        #expect(model.draft.currentWeeklyKm == 50)
    }

    @Test func onboardingAsksForWatchBeforeTheWeek() {
        let (model, _, _, _) = make(.onboarding)
        model.selectGoal(.startRunning)
        #expect(model.step == .beginnerGoal)
        model.next()
        #expect(model.step == .watch)
        #expect(model.primaryTitle == "Skip for now")
    }

    @Test func goalTapAdvances() {
        let (model, _, _, _) = make(.onboarding)
        #expect(model.step == .goal)
        model.selectGoal(.startRunning)
        #expect(model.step == .beginnerGoal)
        #expect(model.steps == [.goal, .beginnerGoal, .watch, .schedule, .venues, .body, .trainingZones, .raceHistory, .startDate, .review])
        #expect(model.direction == .forward)
    }

    @Test func newPlanSkipsAboutYou() {
        let (model, _, _, _) = make(.newPlan)
        model.selectGoal(.race)
        #expect(model.steps == [.goal, .details, .raceDate, .raceGoal, .schedule, .venues, .startDate, .review])
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
        model.next()
        model.next()
        model.next()
        #expect(model.step == .review)
        #expect(model.primaryTitle == "Build my plan")
    }
    @Test func reviewCanReturnToScheduleWithoutLosingAnswers() {
        let (model, _, _, _) = make(.newPlan)
        model.selectGoal(.startRunning)
        model.next()
        model.next()
        model.jump(to: .schedule)
        #expect(model.step == .schedule)
        #expect(model.direction == .backward)
        #expect(model.draft.goal == .startRunning)
    }
    @Test func eventDefaultsMatchTheVisiblePickers() {
        let (model, _, _, _) = make(.newPlan)
        model.selectGoal(.race)
        #expect(model.draft.raceDate == model.earliestRaceDate)
        model.selectRaceGoal(.time)
        #expect(model.draft.targetMinutes == nil)
    }
    @Test func reopenAtReviewKeepsAnswersAndAllowsResubmit() {
        let (model, _, _, _) = make(.newPlan)
        model.selectGoal(.startRunning)
        model.next()
        model.reopenAtReview()
        #expect(model.step == .review)
        #expect(!model.didStart)
        #expect(model.draft.goal == .startRunning)
    }
    @Test func unknownZonesNeedExplicitConfirmation() {
        let (model, _, _, _) = make(.onboarding)
        model.selectGoal(.startRunning)
        model.jump(to: .trainingZones)
        model.next()
        #expect(model.step == .trainingZones)
        #expect(model.showZoneEstimateWarning)
        model.showZoneEstimateWarning = false // Review values keeps the step open.
        #expect(model.step == .trainingZones)
        model.next()
        model.continueWithEstimatedZones()
        #expect(!model.showZoneEstimateWarning && model.step == .raceHistory)
    }

    @Test func enteredThresholdsNeedTheirSource() {
        let (model, _, _, _) = make(.onboarding)
        model.selectGoal(.startRunning)
        model.jump(to: .trainingZones)
        model.draft.aetHr = 145; model.draft.antHr = 170
        model.next()
        #expect(model.showZoneEstimateWarning && model.step == .trainingZones)
        model.showZoneEstimateWarning = false
        model.draft.maxHr = 190; model.draft.restingHr = 55
        model.draft.thresholdSource = "estimated"
        model.next()
        #expect(model.step == .raceHistory && !model.showZoneEstimateWarning)
    }

    @Test func submissionReturnsToMissingContext() async {
        let (model, service, _, _) = make(.newPlan)
        model.selectGoal(.startRunning)
        model.draft.currentWeeklyKm = nil
        model.jump(to: .review)
        await model.submit()
        #expect(model.step == .schedule)
        #expect(model.showIssues)
        #expect(!model.didStart)
        #expect(!model.isSubmitting)
    }

}
