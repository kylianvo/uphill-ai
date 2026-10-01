import Foundation
import Testing
@testable import UphillAI

@MainActor
struct PlanViewModelTests {
    private let cal: Calendar = {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        return c
    }()

    /// Wednesday of week 2 for a plan starting Monday 2026-09-28.
    private var now: Date { cal.date(from: DateComponents(year: 2026, month: 10, day: 7, hour: 9))! }

    private func snapshot() -> PlanSnapshot {
        let plan = TestData.plan(["id": 7, "start_date": "2026-09-28", "total_weeks": 12, "race_date": "2026-12-19",
                                  "goal_type": "time", "target_time_hours": 6.5])
        var workouts: [Workout] = []
        var id = 1
        for week in 1...3 {
            for day in Weekday.allCases {
                let rest = day == .monday || day == .thursday
                workouts.append(TestData.workout([
                    "id": id, "plan_id": 7, "week_number": week, "day_of_week": day.rawValue,
                    "type": rest ? "Rest" : "Easy Run", "duration_minutes": rest ? 0 : 45,
                    "is_priority": day == .saturday,
                ]))
                id += 1
            }
        }
        return PlanSnapshot(plan: plan, workouts: workouts)
    }

    private func make(_ service: FakePlanService, cache: OfflineCache = .inMemory()) -> PlanViewModel {
        let now = self.now
        return PlanViewModel(service: service, cache: cache, now: { now }, calendar: cal)
    }

    @Test func loadSelectsCurrentWeekAndCaches() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        let cache = OfflineCache.inMemory()
        let model = make(service, cache: cache)
        await model.load()
        #expect(model.state == .loaded)
        #expect(model.selectedWeek == 2)
        #expect(model.currentWeek == 2)
        #expect(model.cachedAt == nil)
        #expect(cache.load(PlanSnapshot.self, .plan) != nil)
    }

    @Test func daysForSelectedWeek() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        let model = make(service)
        await model.load()
        let days = model.days
        #expect(days.map(\.weekday) == Weekday.allCases)
        #expect(days[0].isCollapsed)                         // Monday rest
        #expect(days[2].eyebrow == "TODAY")                  // Wednesday 2026-10-07
        #expect(days[3].eyebrow == "TOMORROW")
        #expect(days[5].workouts.first?.isPriority == true)  // Saturday
    }

    @Test func restDayWithLoggedWorkoutStaysExpanded() async {
        var snap = snapshot()
        let mondayIndex = snap.workouts.firstIndex { $0.weekNumber == 2 && $0.weekday == .monday }!
        snap.workouts[mondayIndex] = TestData.workout(["id": 99, "plan_id": 7, "week_number": 2, "day_of_week": "Monday",
                                                       "type": "Rest", "duration_minutes": 0, "is_completed": 1])
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snap) }
        let model = make(service)
        await model.load()
        #expect(model.days[0].isRest)
        #expect(!model.days[0].isCollapsed)
    }

    @Test func emptyWhenNoPlan() async {
        let model = make(FakePlanService())
        await model.load()
        #expect(model.state == .empty)
    }

    @Test func offlineShowsCacheAndBlocksWrites() async throws {
        let cache = OfflineCache.inMemory()
        let saved = Date(timeIntervalSince1970: 5_000)
        cache.save(snapshot(), as: .plan, now: saved)
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .failure(.transport("offline")) }
        let model = make(service, cache: cache)
        await model.load()
        #expect(model.state == .loaded)
        #expect(model.cachedAt == saved)
        let workout = try #require(model.days[2].workouts.first)
        await model.setDone(workout, true)
        #expect(model.actionError == PlanViewModel.offlineMessage)
        #expect(service.calls.withLock { $0 } == ["active"])
    }

    @Test func failedWithoutCache() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .failure(.transport("offline")) }
        let model = make(service)
        await model.load()
        #expect(model.state == .failed(APIError.transport("offline").userMessage))
    }

    @Test func markDoneUpdatesWorkoutsAndCache() async throws {
        let snap = snapshot()
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snap) }
        let target = snap.workouts.first { $0.weekNumber == 2 && $0.weekday == .wednesday }!
        let updated = snap.workouts.map { $0.id == target.id
            ? TestData.workout(["id": target.id, "plan_id": 7, "week_number": 2, "day_of_week": "Wednesday", "is_completed": 1])
            : $0 }
        service.logResult.withLock { $0 = .success(updated) }
        let cache = OfflineCache.inMemory()
        let model = make(service, cache: cache)
        await model.load()
        await model.setDone(target, true)
        #expect(service.calls.withLock { $0 }.last == "log \(target.id) done=1 missed=- rpe=-")
        #expect(model.days[2].workouts.first?.isDone == true)
        #expect(model.lastCompletedID == target.id)
        #expect(cache.load(PlanSnapshot.self, .plan)?.value.workouts == updated)
    }

    @Test func undoDoneClearsBothFlags() async throws {
        let snap = snapshot()
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snap) }
        service.logResult.withLock { $0 = .success(snap.workouts) }
        let model = make(service)
        await model.load()
        await model.setDone(snap.workouts[1], false)
        #expect(service.calls.withLock { $0 }.last == "log 2 done=0 missed=0 rpe=-")
    }

    @Test func moveTargetsRunFromTodayToEndOfNextWeek() async throws {
        let snap = snapshot()
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snap) }
        let model = make(service)
        await model.load()
        let saturday = snap.workouts.first { $0.weekNumber == 2 && $0.weekday == .saturday }!
        let targets = model.moveTargets(for: saturday)
        #expect(targets.first?.week == 2)
        #expect(targets.first?.weekday == .wednesday)        // today
        #expect(targets.last?.week == 3)
        #expect(targets.last?.weekday == .sunday)
        #expect(!targets.contains { $0.week == 2 && $0.weekday == .saturday })
        #expect(targets.count == 4 + 7)                      // Wed–Sun of week 2 minus Saturday (4), all of week 3 (7)
    }

    @Test func moveSendsClientTodayAndMapsGuardErrors() async throws {
        let snap = snapshot()
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snap) }
        service.moveResult.withLock { $0 = .failure(.http(status: 422, message: nil, code: "G4_window")) }
        let model = make(service)
        await model.load()
        let workout = snap.workouts.first { $0.weekNumber == 2 && $0.weekday == .saturday }!
        let target = try #require(model.moveTargets(for: workout).first { $0.week == 3 && $0.weekday == .tuesday })
        let ok = await model.move(workout, to: target)
        #expect(!ok)
        #expect(service.calls.withLock { $0 }.last == "move \(workout.id) -> w3 Tuesday today=2026-10-07")
        #expect(model.actionError == "Workouts can only move within this week or into next week.")
    }

    @Test func summaryValues() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        let model = make(service)
        await model.load()
        #expect(model.goalText == "Goal 6h 30m")
        #expect(model.daysToRace == 73)
        #expect(model.phase == "Base")
        #expect(model.selectedVolume.minutes == 5 * 45)
        #expect(model.weeks == Array(1...12))
    }

    @Test func selectPlanReloadsAndResetsWeek() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        service.selectResult.withLock { $0 = .success(snapshot()) }
        let model = make(service)
        await model.load()
        model.selectedWeek = 5
        await model.select(TestData.plan(["id": 3]))
        #expect(service.calls.withLock { $0 }.last == "select 3")
        #expect(model.selectedWeek == 2)
    }

    @Test func transportFailureAfterOnlineLoadBlocksEveryWrite() async throws {
        let service = FakePlanService()
        let snap = snapshot()
        service.activeResult.withLock { $0 = .success(snap) }
        let model = make(service)
        await model.load()
        service.activeResult.withLock { $0 = .failure(.transport("offline")) }
        await model.load()
        #expect(model.cachedAt != nil)
        let workout = snap.workouts[9]
        await model.setDone(workout, true)
        await model.setMissed(workout)
        #expect(await model.saveLog(workout, rpe: 5, notes: "offline") == false)
        let target = try #require(model.moveTargets(for: workout).first)
        #expect(await model.move(workout, to: target) == false)
        await model.select(snap.plan)
        #expect(service.calls.withLock { $0 } == ["active", "active"])
        #expect(model.actionError == PlanViewModel.offlineMessage)
    }

    @Test func confirmedEmptyPlanCannotReappearOfflineAndPreservesUser() async throws {
        let cache = OfflineCache.inMemory()
        let user = try Fixture.decode(User.self, "auth_me.json")
        cache.save(user, as: .user)
        cache.save(snapshot(), as: .plan)
        let service = FakePlanService()
        let model = make(service, cache: cache)
        await model.load()
        #expect(model.state == .empty)
        #expect(cache.load(PlanSnapshot.self, .plan) == nil)
        #expect(cache.load(User.self, .user)?.value == user)
        service.activeResult.withLock { $0 = .failure(.transport("offline")) }
        let relaunched = make(service, cache: cache)
        await relaunched.load()
        #expect(relaunched.snapshot == nil)
    }

    @Test func writeCompletingAfterSignOutDoesNotCache() async throws {
        let snap = snapshot()
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snap) }
        let target = snap.workouts.first { $0.weekNumber == 2 && $0.weekday == .wednesday }!
        service.logResult.withLock { $0 = .success(snap.workouts) }
        let cache = OfflineCache.inMemory()
        var signedIn = true
        let now = self.now
        let model = PlanViewModel(service: service, cache: cache, now: { now }, calendar: cal, isSignedIn: { signedIn })
        await model.load()
        cache.remove(.plan)          // as the sign-out wipe does
        signedIn = false             // signed out while the write was in flight
        await model.setDone(target, true)
        #expect(cache.load(PlanSnapshot.self, .plan) == nil)
    }

    @Test func recentPlansPropagatesErrors() async {
        let service = FakePlanService()
        service.recentResult.withLock { $0 = .failure(.transport("offline")) }
        let model = make(service)
        await #expect(throws: APIError.self) { try await model.recentPlans() }
    }

    private func completion(_ pct: Double, unlocked: Bool, maxWeek: Int = 3) -> BlockCompletionResponse {
        try! JSONCoding.decoder.decode(BlockCompletionResponse.self, from: json([
            "plan_id": 7, "max_generated_week": maxWeek,
            "blocks": (1...maxWeek).map { ["block_number": $0, "week_start": $0, "week_end": $0,
                                           "completion_pct": $0 == maxWeek ? pct : 100, "unlocked": $0 == maxWeek ? unlocked : true] as [String: Any] },
        ]))
    }

    private func makeWithGeneration(_ service: FakePlanService, gen: FakeGenerationService) -> (PlanViewModel, GenerationCenter) {
        let center = GenerationCenter(service: gen, defaults: UserDefaults(suiteName: UUID().uuidString)!,
                                      makePoller: { JobPoller(service: $0, interval: .seconds(60), timeout: .seconds(120)) })
        let now = self.now
        return (PlanViewModel(service: service, cache: .inMemory(), now: { now }, calendar: cal,
                              generation: center, generationService: gen), center)
    }

    @Test func offerAppearsOnLastGeneratedWeek() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        service.completionResult.withLock { $0 = .success(completion(80, unlocked: true)) }
        let (model, _) = makeWithGeneration(service, gen: FakeGenerationService())
        await model.load()
        model.selectedWeek = 3
        await model.refreshNextWeekOffer()
        #expect(model.nextWeekOffer == NextWeekOffer(blockNumber: 4, weekStart: 4, weekEnd: 4, previousCompletionPct: 80, unlocked: true))
        #expect(model.nextWeekOffer?.title == "Build week 4")
        model.selectedWeek = 2
        await model.refreshNextWeekOffer()
        #expect(model.nextWeekOffer == nil)
    }

    @Test func gateNeedsConfirmationThenOverride() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        service.completionResult.withLock { $0 = .success(completion(40, unlocked: false)) }
        let gen = FakeGenerationService()
        gen.startResult.withLock { $0 = .failure(.http(status: 403, message: "Block 3 is 40% complete. Need 70% to unlock the next block.", code: nil)) }
        let (model, center) = makeWithGeneration(service, gen: gen)
        await model.load()
        model.selectedWeek = 3
        await model.refreshNextWeekOffer()
        let first = await model.buildNextWeek(rpe: 6, notes: "", override: false)
        #expect(first == .needsConfirmation("Block 3 is 40% complete. Need 70% to unlock the next block."))
        gen.startResult.withLock { $0 = .success(JobStart(jobId: "nb")) }
        #expect(await model.buildNextWeek(rpe: 6, notes: "", override: true) == .started)
        #expect(gen.calls.withLock { $0.filter { $0.hasPrefix("next") } } == ["next 4 override=false", "next 4 override=true"])
        #expect(center.running?.kind == .nextWeek)
    }

    @Test func everythingGeneratedClearsOfferOn400() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        service.completionResult.withLock { $0 = .success(completion(90, unlocked: true)) }
        let gen = FakeGenerationService()
        gen.startResult.withLock { $0 = .failure(.http(status: 400, message: "All blocks generated.", code: nil)) }
        let (model, _) = makeWithGeneration(service, gen: gen)
        await model.load()
        model.selectedWeek = 3
        await model.refreshNextWeekOffer()
        #expect(await model.buildNextWeek(rpe: nil, notes: "", override: false) == .failed("All blocks generated."))
        #expect(model.nextWeekOffer == nil)
    }

    /// Phase 1 offered "next week" even when it was not generated yet.
    @Test func moveTargetsStopAtLastGeneratedWeek() async {
        let service = FakePlanService()
        var snap = snapshot()
        snap.workouts = snap.workouts.filter { $0.weekNumber <= 2 }   // weeks 1-2 generated; current week is 2
        service.activeResult.withLock { $0 = .success(snap) }
        let model = make(service)
        await model.load()
        let targets = model.moveTargets(for: snap.workouts.first { $0.weekNumber == 2 }!)
        #expect(targets.allSatisfy { $0.week <= 2 })
    }

    @Test func adaptSendsFatigueAndTracksJob() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        let gen = FakeGenerationService()
        gen.startResult.withLock { $0 = .success(JobStart(jobId: "ad")) }
        let (model, center) = makeWithGeneration(service, gen: gen)
        await model.load()
        #expect(model.canAdapt(week: 2))
        #expect(!model.canAdapt(week: 1))      // past week
        #expect(!model.canAdapt(week: 4))      // not generated
        let error = await model.adaptWeek(2, fatigue: .hard, rpe: 8, notes: "Bad sleep")
        #expect(error == nil)
        #expect(gen.calls.withLock { $0.filter { $0.hasPrefix("adapt") } } == ["adapt 2 hard"])
        #expect(center.running?.kind == .adaptWeek)
    }

    @Test func adaptBlockedOffline() async {
        let cache = OfflineCache.inMemory()
        cache.save(snapshot(), as: .plan)
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .failure(.transport("offline")) }
        let gen = FakeGenerationService()
        let center = GenerationCenter(service: gen, defaults: UserDefaults(suiteName: UUID().uuidString)!)
        let now = self.now
        let model = PlanViewModel(service: service, cache: cache, now: { now }, calendar: cal, generation: center, generationService: gen)
        await model.load()
        #expect(await model.adaptWeek(2, fatigue: .easy, rpe: nil, notes: "") == PlanViewModel.offlineMessage)
        #expect(gen.calls.withLock { $0 }.isEmpty)
    }

    @Test func weekReviewPassesThroughService() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        service.reviewResult.withLock { $0 = .success(try! Fixture.decode(WeekReview.self, "week_review.json")) }
        let model = make(service)
        await model.load()
        let result = await model.weekReview(1)
        #expect((try? result.get())?.weekNumber == 1)
        #expect(service.calls.withLock { $0 }.contains("review 7 w1"))
    }

    @Test func goalPillTextAndApply() async throws {
        let service = FakePlanService()
        var event = snapshot()
        event = PlanSnapshot(plan: TestData.plan(["id": 7, "start_date": "2026-09-28", "total_weeks": 12, "race_date": "2026-12-19",
                                                  "goal_type": "time", "target_time_hours": 6.0, "course_distance_km": 42]),
                             workouts: event.workouts)
        service.activeResult.withLock { $0 = .success(event) }
        let behind = try JSONCoding.decoder.decode(PlanGoal.self, from: json([
            "assessment": ["id": 1, "goals": ["a": 360, "b": 385, "c": 410], "reasoning": [], "missing": [], "engine": "rules"],
            "status": ["state": "behind", "suggested_mins": 385], "target_time_hours": 6.0,
        ]))
        service.goalResult.withLock { $0 = .success(behind) }
        let model = make(service)
        await model.load()
        await model.loadGoal()
        #expect(model.goalPillText == "Behind target")
        #expect(PlanViewModel.formatMinutes(385) == "6:25")
        _ = await model.applySuggestedGoal()
        #expect(service.calls.withLock { $0 }.contains("apply 7 385"))
    }

    @Test func reassessRateLimitMessage() async {
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snapshot()) }
        service.goalResult.withLock { $0 = .failure(.http(status: 429, message: "limit", code: nil)) }
        let model = make(service)
        await model.load()
        #expect(await model.reassessGoal() == "You've used today's goal checks. Try again tomorrow.")
    }
}
