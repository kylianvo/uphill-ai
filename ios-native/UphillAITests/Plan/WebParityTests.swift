import Foundation
import Synchronization
import Testing
@testable import UphillAI

/// Coach plan actions, block evaluation, watch-match fixing, auto mark-done and race benchmarks.
struct PlanServiceScopeTests {
    @Test func coachScopeRoutesPlanReadsToAthleteMirrors() async throws {
        let paths = Mutex<[String]>([])
        let base = PlanService(client: makeStubClient { request in
            paths.withLock { $0.append(request.url?.path() ?? "") }
            switch request.url?.path() {
            case "/api/coaching/athletes/42/active-plan": return (200, json(["active": false]))
            case "/api/coaching/athletes/42/plans/draft": return (200, json(["draft": false]))
            case "/api/coaching/athletes/42/block-completion/7":
                return (200, json(["blocks": [], "max_generated_week": 2]))
            default: return (404, json(["detail": "unexpected"]))
            }
        })
        let scoped = base.scoped(toAthlete: 42)
        _ = try await scoped.activePlan()
        _ = try await scoped.blockCompletion(planID: 7)
        _ = try? await scoped.goal(planID: 7)
        _ = try? await scoped.weekReview(planID: 7, week: 3)
        _ = try? await scoped.blockEvaluation(planID: 7, block: 1)
        #expect(paths.withLock { $0 } == [
            "/api/coaching/athletes/42/active-plan",
            "/api/coaching/athletes/42/plans/draft",  // no active plan: a coach also looks for an unpublished draft
            "/api/coaching/athletes/42/block-completion/7",
            "/api/coaching/athletes/42/plans/7/goal",
            "/api/coaching/athletes/42/week-review/7/3",
            "/api/coaching/athletes/42/block-evaluation/7/1",
        ])
    }

    @Test func ownScopeKeepsAthleteEndpoints() async throws {
        let paths = Mutex<[String]>([])
        let service = PlanService(client: makeStubClient { request in
            paths.withLock { $0.append(request.url?.path() ?? "") }
            return (404, json(["detail": "x"]))
        }).scoped(toAthlete: nil)
        _ = try? await service.blockEvaluation(planID: 7, block: 2)
        _ = try? await service.reassessGoal(planID: 7)
        #expect(paths.withLock { $0 } == ["/api/coach/block-evaluation/7/2", "/api/plans/7/goal/reassess"])
    }

    @Test func generationScopeUsesCoachEndpoints() async throws {
        let paths = Mutex<[String]>([])
        let service = GenerationService(client: makeStubClient { request in
            paths.withLock { $0.append(request.url?.path() ?? "") }
            if let data = StubURLProtocol.bodyData(request),
               let body = try? JSONSerialization.jsonObject(with: data) as? [String: Any], body["block_number"] != nil {
                #expect(body["coach_notes"] as? String == "Keep it easy")
            }
            return (200, json(["job_id": "j1"]))
        }).scoped(toAthlete: 9)
        var next = NextBlockBody(planId: 1, blockNumber: 2, overallRpe: nil, notes: nil, overrideGate: false, lang: "en")
        next.coachNotes = "Keep it easy"
        _ = try await service.generateNextBlock(next)
        _ = try await service.adaptWeek(AdaptWeekBody(planId: 1, weekNumber: 3, overallRpe: nil, fatigueLevel: "easy",
                                                      fatigueNotes: nil, lang: "en", clientToday: "2026-10-13"))
        #expect(paths.withLock { $0 } == ["/api/coaching/athletes/9/generate-next-block",
                                         "/api/coaching/athletes/9/adapt-week"])
    }

    @Test func setMatchSendsWorkoutOrUnlinks() async throws {
        let requests = Mutex<[String]>([])
        let service = PlanService(client: makeStubClient { request in
            #expect(request.httpMethod == "PATCH")
            requests.withLock { $0.append((request.url?.path() ?? "") + "?" + (request.url?.query() ?? "")) }
            return (200, json(["ok": true]))
        })
        try await service.setMatch(activityID: 55, workoutID: 12)
        try await service.setMatch(activityID: 55, workoutID: nil)
        #expect(requests.withLock { $0 } == ["/api/integrations/matching/55?workout_id=12", "/api/integrations/matching/55?"])
    }

    @Test func blockEvaluationDecodes() throws {
        let data = try JSONSerialization.data(withJSONObject: [
            "block_number": 1, "week_start": 1, "week_end": 2, "sessions_total": 10, "sessions_completed": 8,
            "sessions_missed": 2, "completion_pct": 80, "planned_km": 60.5, "actual_km": 48.2,
            "planned_minutes": 420, "actual_minutes": 340, "avg_quality_score": NSNull(), "quality_grade": NSNull(),
            "coaching_takeaways": [], "coach_summary": "Solid block.", "coach_notes": ["Watch the long run"],
            "athlete_rpe": NSNull(), "athlete_notes": NSNull(),
        ])
        let evaluation = try JSONCoding.decoder.decode(BlockEvaluation.self, from: data)
        #expect(evaluation.sessionsCompleted == 8)
        #expect(evaluation.qualityGrade == nil)
        #expect(evaluation.coachNotes == ["Watch the long run"])
    }

    @Test func benchmarkMarkersAverageAcrossEditions() {
        let benchmarks = [
            RaceBenchmark(year: 2024, winnerTime: "6:00:00", percentiles: ["overall": PercentileSet(p50: "10:00:00")]),
            RaceBenchmark(year: 2025, winnerTime: "5:00:00", percentiles: ["overall": PercentileSet(p50: "9:00:00")]),
        ]
        let all = BenchmarkMarker.markers(benchmarks, year: nil)
        #expect(all.map(\.label) == ["Winner", "P50"])
        #expect(all.map(\.minutes) == [330, 570])
        let one = BenchmarkMarker.markers(benchmarks, year: 2025)
        #expect(one.map(\.minutes) == [300, 540])
    }
}

@MainActor
struct PlanAutoDoneTests {
    private let cal: Calendar = {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        return c
    }()
    /// Wednesday of week 2 for a plan starting Monday 2026-09-28.
    private var now: Date { cal.date(from: DateComponents(year: 2026, month: 10, day: 7, hour: 9))! }

    private func snapshot() -> PlanSnapshot {
        let plan = TestData.plan(["id": 7, "start_date": "2026-09-28", "total_weeks": 12, "race_date": "2026-12-19"])
        let workouts = [
            TestData.workout(["id": 1, "plan_id": 7, "week_number": 2, "day_of_week": "Tuesday", "type": "Easy Run", "duration_minutes": 40]),
            TestData.workout(["id": 2, "plan_id": 7, "week_number": 2, "day_of_week": "Wednesday", "type": "Easy Run", "duration_minutes": 40]),
            TestData.workout(["id": 3, "plan_id": 7, "week_number": 2, "day_of_week": "Friday", "type": "Easy Run", "duration_minutes": 40]),
            TestData.workout(["id": 4, "plan_id": 7, "week_number": 2, "day_of_week": "Monday", "type": "Easy Run", "duration_minutes": 40]),
        ]
        return PlanSnapshot(plan: plan, workouts: workouts)
    }

    private func activity(_ id: Int, workout: Int?, method: String?) -> WatchActivity {
        WatchActivity(activityId: id, workoutId: workout, workoutTitle: nil, distanceKm: 5, durationSeconds: 1800,
                      avgHr: nil, startTime: nil, deviceModel: nil, matchMethod: method)
    }

    @Test func marksOnlySettledPastMatchesDone() async {
        let snap = snapshot()
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snap) }
        service.logResult.withLock { $0 = .success(snap.workouts) }
        service.watchActivitiesResult.withLock {
            $0 = .success([
                activity(10, workout: 1, method: "auto"),      // Tuesday, past → done
                activity(11, workout: 2, method: "manual"),    // today → done
                activity(12, workout: 3, method: "auto"),      // Friday, future → left alone
                activity(13, workout: 4, method: "suggest"),   // needs confirmation → left alone
            ])
        }
        let now = self.now
        let model = PlanViewModel(service: service, cache: .inMemory(), now: { now }, calendar: cal)
        await model.load()
        let marked = await model.markMatchedWorkoutsDone()
        #expect(marked == 2)
        let logs = service.calls.withLock { $0 }.filter { $0.hasPrefix("log") }
        #expect(logs == ["log 1 done=1 missed=0 rpe=-", "log 2 done=1 missed=0 rpe=-"])
    }

    @Test func coachScopeSkipsCacheAndAutoDone() async {
        let snap = snapshot()
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(snap) }
        service.watchActivitiesResult.withLock { $0 = .success([activity(10, workout: 1, method: "auto")]) }
        let cache = OfflineCache.inMemory()
        let now = self.now
        let model = PlanViewModel(service: service, cache: cache, now: { now }, calendar: cal)
        await model.setAthleteScope(42)
        #expect(model.athleteId == 42)
        #expect(model.state == .loaded)
        #expect(cache.load(PlanSnapshot.self, .plan) == nil)
        #expect(await model.markMatchedWorkoutsDone() == 0)
        model.reset()
        #expect(model.athleteId == nil)
        #expect(service.calls.withLock { $0 }.contains("scoped 42"))
    }

    @Test func coachScopeCannotUseAthleteOwnedActions() async {
        let service = FakePlanService()
        let snap = snapshot()
        service.activeResult.withLock { $0 = .success(snap) }
        service.logResult.withLock { $0 = .success(snap.workouts) }
        let now = self.now
        let model = PlanViewModel(service: service, cache: .inMemory(), now: { now }, calendar: cal)
        await model.setAthleteScope(42)
        service.calls.withLock { $0.removeAll() }
        let workout = snap.workouts[0]
        await model.setDone(workout, true)
        await model.setMissed(workout)
        #expect(await model.saveLog(workout, rpe: 3, notes: "Easy") == false)
        #expect(await model.move(workout, to: MoveTarget(week: 2, weekday: .thursday, date: now)) == false)
        #expect(await model.swapDays(week: 2, day1: .tuesday, day2: .thursday) == false)
        #expect(await model.deletePlan(id: snap.plan.id) == false)
        await model.select(snap.plan)
        #expect(await model.syncWatch() == nil)
        #expect((try? await model.watchActivities()) == [])
        #expect(await model.setMatch(activityID: 10, to: workout) != nil)
        #expect(service.calls.withLock { $0 }.isEmpty)
    }

    @Test func delayedAthleteResponseCannotReplaceOwnPlanOrEnterCache() async {
        let service = FakePlanService()
        let athlete = snapshot()
        let own = PlanSnapshot(plan: TestData.plan(["id": 8]), workouts: [])
        service.activeResult.withLock { $0 = .success(athlete) }
        let cache = OfflineCache.inMemory()
        let model = PlanViewModel(service: service, cache: cache)
        await model.setAthleteScope(42)
        let gate = PlanLoadGate()
        service.beforeActiveReturn.withLock { $0 = { await gate.wait() } }
        let pending = Task { await model.load() }
        while gate.continuation == nil { await Task.yield() }
        service.beforeActiveReturn.withLock { $0 = nil }
        service.activeResult.withLock { $0 = .success(own) }
        await model.setAthleteScope(nil)
        gate.continuation?.resume()
        await pending.value
        #expect(model.snapshot?.plan.id == own.plan.id)
        #expect(cache.load(PlanSnapshot.self, .plan)?.value.plan.id == own.plan.id)
    }

    @Test func replacingWatchRunUnlinksOldActivityFirst() async {
        let service = FakePlanService()
        var snap = snapshot()
        snap.workouts[0].matchedActivityId = 555
        service.activeResult.withLock { $0 = .success(snap) }
        let model = PlanViewModel(service: service, cache: .inMemory())
        await model.load()
        #expect(await model.setMatch(activityID: 556, to: snap.workouts[0]) == nil)
        #expect(service.calls.withLock { $0 }.filter { $0.hasPrefix("setMatch") } == [
            "setMatch 555 -> none", "setMatch 556 -> 1",
        ])
    }

    @Test func failedReplacementRelinksOldRun() async {
        let service = FakePlanService()
        var snap = snapshot()
        snap.workouts[0].matchedActivityId = 555
        service.activeResult.withLock { $0 = .success(snap) }
        service.failingMatchLinks.withLock { $0 = [556] }
        let model = PlanViewModel(service: service, cache: .inMemory())
        await model.load()
        #expect(await model.setMatch(activityID: 556, to: snap.workouts[0]) != nil)
        #expect(service.calls.withLock { $0 }.filter { $0.hasPrefix("setMatch") } == [
            "setMatch 555 -> none", "setMatch 556 -> 1", "setMatch 555 -> 1",
        ])
    }

    @Test func unlinkingRunClearsDone() async {
        let service = FakePlanService()
        var snap = snapshot()
        snap.workouts[0] = TestData.workout(["id": 1, "plan_id": 7, "week_number": 2, "day_of_week": "Tuesday",
                                             "type": "Easy Run", "duration_minutes": 40, "is_completed": 1])
        snap.workouts[0].matchedActivityId = 555
        service.activeResult.withLock { $0 = .success(snap) }
        let model = PlanViewModel(service: service, cache: .inMemory())
        await model.load()
        #expect(await model.setMatch(activityID: 555, to: nil) == nil)
        #expect(service.calls.withLock { $0 }.contains("log \(snap.workouts[0].id) done=0 missed=- rpe=-"))
    }

    @Test func automaticCompletionKeepsWatchCard() async {
        let service = FakePlanService()
        var snap = snapshot()
        let raw = snap.workouts
        snap.workouts[0].matchedActivityId = 555
        snap.workouts[0].matchedDistanceKm = 9.3
        service.activeResult.withLock { $0 = .success(snap) }
        service.logResult.withLock { $0 = .success(raw) }
        service.watchActivitiesResult.withLock { $0 = .success([activity(555, workout: 1, method: "auto")]) }
        let now = self.now
        let model = PlanViewModel(service: service, cache: .inMemory(), now: { now }, calendar: cal)
        await model.load()
        #expect(await model.markMatchedWorkoutsDone() == 1)
        #expect(model.snapshot?.workouts[0].matchedActivityId == 555)
        #expect(model.snapshot?.workouts[0].matchedDistanceKm == 9.3)
    }

    @Test(arguments: [false, true]) func goalWritesIgnoreResponsesFromEarlierScope(apply: Bool) async throws {
        let service = FakePlanService()
        var snap = snapshot()
        snap = PlanSnapshot(plan: TestData.plan(["id": 7, "course_distance_km": 70]), workouts: snap.workouts)
        service.activeResult.withLock { $0 = .success(snap) }
        service.goalResult.withLock { $0 = .success(PlanGoal(assessment: nil, status: GoalStatus(state: "no_target", suggestedMins: 400), targetTimeHours: nil)) }
        let model = PlanViewModel(service: service, cache: .inMemory())
        await model.setAthleteScope(42)
        #expect(model.suggestedMinutes != nil)
        let gate = PlanLoadGate()
        service.beforeGoalReturn.withLock { $0 = { await gate.wait() } }
        let pending = Task { apply ? await model.applySuggestedGoal() : await model.reassessGoal() }
        while gate.continuation == nil { await Task.yield() }
        service.beforeGoalReturn.withLock { $0 = nil }
        service.goalResult.withLock { $0 = .failure(.http(status: 404, message: nil, code: nil)) }
        await model.setAthleteScope(43)
        gate.continuation?.resume()
        _ = await pending.value
        #expect(model.goal == nil)
    }

}

@MainActor
private final class PlanLoadGate {
    var continuation: CheckedContinuation<Void, Never>?
    func wait() async {
        await withCheckedContinuation { continuation = $0 }
    }
}

@MainActor
struct WebParityAppTests {
    @Test func generationFinishedAfterExitingAthleteViewReloadsOwnPlan() async throws {
        let activeData = try Fixture.data("active_plan.json")
        let paths = Mutex<[String]>([])
        let base = StubURLProtocol.register { request in
            let path = request.url!.path
            paths.withLock { $0.append(path) }
            if path == "/api/coach/active-plan" { return (200, activeData) }
            if path == "/api/integrations/matching" { return (200, json(["activities": []])) }
            return (404, json([:]))
        }
        let cache = OfflineCache.inMemory()
        let app = AppModel(tokenStore: InMemoryTokenStore("token"), baseURL: { base }, session: StubURLProtocol.session(), cache: cache)
        app.session.setUser(try Fixture.decode(User.self, "auth_me.json"))
        let athlete = PlanSnapshot(plan: TestData.plan(["id": 999]), workouts: [])
        await app.generation.onFinished?(.nextWeek, .done(athlete))
        #expect(paths.withLock { $0 }.contains("/api/coach/active-plan"))
        #expect(app.plan.snapshot?.plan.id == 93)
        #expect(cache.load(PlanSnapshot.self, .plan)?.value.plan.id == 93)
    }

    @Test func overlappingForegroundCallsSyncOnceWithinFifteenMinutes() async throws {
        let activeData = try Fixture.data("active_plan.json")
        let paths = Mutex<[String]>([])
        let base = StubURLProtocol.register { request in
            let path = request.url!.path
            paths.withLock { $0.append(path) }
            switch path {
            case "/api/integrations/status": return (200, json(["coros": ["connected": true]]))
            case "/api/integrations/coros/sync": return (200, json(["activities": 0]))
            case "/api/integrations/matching/run": return (200, json([:]))
            case "/api/integrations/matching": return (200, json(["activities": []]))
            case "/api/coach/active-plan": return (200, activeData)
            default: return (404, json([:]))
            }
        }
        let app = AppModel(tokenStore: InMemoryTokenStore("token"), baseURL: { base }, session: StubURLProtocol.session(), cache: .inMemory())
        app.session.setUser(try Fixture.decode(User.self, "auth_me.json"))
        await app.plan.load()
        paths.withLock { $0.removeAll() }
        let now = Date()
        let first = Task { await app.autoSyncWatchIfDue(now: now) }
        let second = Task { await app.autoSyncWatchIfDue(now: now) }
        await first.value
        await second.value
        await app.autoSyncWatchIfDue(now: now.addingTimeInterval(14 * 60))
        #expect(paths.withLock { $0 }.filter { $0 == "/api/integrations/status" }.count == 1)
        #expect(paths.withLock { $0 }.filter { $0 == "/api/integrations/coros/sync" }.count == 1)
        await app.autoSyncWatchIfDue(now: now.addingTimeInterval(15 * 60))
        #expect(paths.withLock { $0 }.filter { $0 == "/api/integrations/coros/sync" }.count == 2)
    }
}
