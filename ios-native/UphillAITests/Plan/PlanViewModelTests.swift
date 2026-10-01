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
}
