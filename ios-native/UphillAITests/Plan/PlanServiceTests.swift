import Foundation
import Synchronization
import Testing
@testable import UphillAI

private func body(_ request: URLRequest) throws -> [String: Any] {
    let data = try #require(StubURLProtocol.bodyData(request))
    return try #require(try JSONSerialization.jsonObject(with: data) as? [String: Any])
}

struct PlanServiceTests {
    @Test func activePlanReturnsSnapshot() async throws {
        let fixture = try Fixture.data("active_plan.json")
        let service = PlanService(client: makeStubClient { request in
            if request.url?.path() == "/api/integrations/matching" { return (200, json(["activities": []])) }
            #expect(request.url?.path() == "/api/coach/active-plan")
            return (200, fixture)
        })
        let snapshot = try await service.activePlan()
        #expect(snapshot?.workouts.count == 21)
    }

    @Test func activePlanMergesMatchedWatchActivities() async throws {
        let fixture = try Fixture.data("active_plan.json")
        let service = PlanService(client: makeStubClient { request in
            if request.url?.path() == "/api/integrations/matching" {
                #expect(request.url?.query()?.contains("plan_id=93") == true)
                return (200, json(["activities": [
                    ["activity_id": 555, "workout_id": 1242, "distance_km": 10.2, "duration_seconds": 3120,
                     "avg_hr": 142.6, "device_model": "COROS PACE 3", "start_time": "2026-10-06T06:00:00",
                     "source_provider": "coros"],
                    ["activity_id": 556, "workout_id": NSNull(), "distance_km": 3.0, "duration_seconds": 900,
                     "start_time": "2026-10-06T18:00:00", "source_provider": "coros"],
                ]]))
            }
            return (200, fixture)
        })
        let snapshot = try #require(try await service.activePlan())
        let matched = try #require(snapshot.workouts.first { $0.id == 1242 })
        #expect(matched.isMatched)
        #expect(matched.matchedActivityId == 555)
        #expect(matched.matchedDeviceModel == "COROS PACE 3")
        #expect(matched.matchedDistanceKm == 10.2)
        #expect(matched.matchedDurationSeconds == 3120)
        #expect(matched.matchedAvgHr == 143)
        #expect(snapshot.workouts.filter(\.isMatched).count == 1)
    }

    @Test func activePlanStillLoadsWhenMatchingFails() async throws {
        let fixture = try Fixture.data("active_plan.json")
        let service = PlanService(client: makeStubClient { request in
            if request.url?.path() == "/api/integrations/matching" { return (500, json(["detail": "boom"])) }
            return (200, fixture)
        })
        let snapshot = try await service.activePlan()
        #expect(snapshot?.workouts.count == 21)
        #expect(snapshot?.workouts.contains(where: \.isMatched) == false)
    }

    @Test func activePlanNilWhenInactive() async throws {
        let service = PlanService(client: makeStubClient { _ in (200, json(["active": false])) })
        #expect(try await service.activePlan() == nil)
    }

    @Test func logSendsOnlySetFields() async throws {
        let service = PlanService(client: makeStubClient { request in
            #expect(request.httpMethod == "PATCH")
            #expect(request.url?.path() == "/api/coach/workouts/log")
            let b = try body(request)
            #expect(b["workout_id"] as? Int == 42)
            #expect(b["is_completed"] as? Int == 1)
            #expect(b["rpe"] as? Int == 6)
            #expect(b["is_missed"] == nil)
            #expect(b["notes"] == nil)
            return (200, json(["workouts": []]))
        })
        _ = try await service.log(workoutID: 42, WorkoutLogUpdate(isCompleted: 1, rpe: 6))
    }

    @Test func moveSendsOneOperationWithClientToday() async throws {
        let service = PlanService(client: makeStubClient { request in
            #expect(request.url?.path() == "/api/coach/calendar/move")
            let b = try body(request)
            #expect(b["plan_id"] as? Int == 7)
            #expect(b["client_today"] as? String == "2026-10-01")
            let ops = try #require(b["operations"] as? [[String: Any]])
            #expect(ops.count == 1)
            #expect(ops[0]["workout_id"] as? Int == 42)
            #expect(ops[0]["target_week"] as? Int == 3)
            #expect(ops[0]["target_day"] as? String == "Thursday")
            return (200, json(["workouts": [], "warnings": []]))
        })
        _ = try await service.move(planID: 7, workoutID: 42, toWeek: 3, toDay: .thursday, clientToday: "2026-10-01")
    }

    @Test func moveGuardViolationSurfacesCode() async {
        let service = PlanService(client: makeStubClient { _ in
            (422, json(["detail": ["code": "G4_window", "params": [:]]]))
        })
        await #expect(throws: APIError.scheduleGuard(status: 422, code: "G4_window", params: [:])) {
            _ = try await service.move(planID: 7, workoutID: 42, toWeek: 9, toDay: .monday, clientToday: "2026-10-01")
        }
    }

    @Test func recentAndSelect() async throws {
        let recent = try Fixture.data("recent_plans.json")
        let active = try Fixture.data("active_plan.json")
        let service = PlanService(client: makeStubClient { request in
            switch request.url?.path() {
            case "/api/coach/recent-plans": return (200, recent)
            case "/api/coach/select-plan":
                let payload = try body(request)
                #expect(payload["plan_id"] as? Int == 5)
                return (200, active)
            default: return (404, Data())
            }
        })
        #expect(try await service.recentPlans().count == 2)
        #expect(try await service.selectPlan(id: 5) != nil)
    }

    @Test func swapDaysSendsPayloadAndDecodesResponse() async throws {
        let fixture = try Fixture.data("modify_calendar.json")
        let service = PlanService(client: makeStubClient { request in
            #expect(request.httpMethod == "POST")
            #expect(request.url?.path() == "/api/coach/modify-calendar")
            let b = try body(request)
            #expect(b["plan_id"] as? Int == 93)
            #expect(b["week_number"] as? Int == 3)
            #expect(b["day_1"] as? String == "Tuesday")
            #expect(b["day_2"] as? String == "Wednesday")
            #expect(b["client_today"] as? String == "2026-10-03")
            return (200, fixture)
        })
        let result = try await service.swapDays(planID: 93, weekNumber: 3, day1: .tuesday, day2: .wednesday, clientToday: "2026-10-03")
        #expect(result.workouts.count > 0)
        #expect(result.warnings.isEmpty)
    }

    @Test func deletePlanSendsDeleteRequest() async throws {
        let fixture = try Fixture.data("delete_plan.json")
        let service = PlanService(client: makeStubClient { request in
            #expect(request.httpMethod == "DELETE")
            #expect(request.url?.path() == "/api/coach/plans/92")
            return (200, fixture)
        })
        try await service.deletePlan(id: 92)
    }

    @Test func syncWatchRunsMatchingAfterSync() async throws {
        let paths = Mutex<[String]>([])
        let service = PlanService(client: makeStubClient { request in
            #expect(request.httpMethod == "POST")
            paths.withLock { $0.append(request.url?.path() ?? "") }
            if request.url?.path() == "/api/integrations/matching/run" {
                let query = request.url?.query() ?? ""
                #expect(query.contains("plan_id=93"))
                #expect(query.contains("tz_offset_minutes="))
                return (200, json(["matched": 1, "suggested": 0, "unmatched": 0, "skipped_manual": 0]))
            }
            return (200, json(["activities": 1, "daily_metrics": 1]))
        })
        _ = try await service.syncWatch(planID: 93)
        #expect(paths.withLock { $0 } == ["/api/integrations/coros/sync", "/api/integrations/matching/run"])
    }

    @Test func syncWatchReturnsMatchCountOnSuccess() async throws {
        let service = PlanService(client: makeStubClient { request in
            #expect(request.httpMethod == "POST")
            if request.url?.path() == "/api/integrations/matching/run" { return (200, json([:])) }
            #expect(request.url?.path() == "/api/integrations/coros/sync")
            return (200, json(["activities": 3, "dailyMetrics": 1]))
        })
        let result = try await service.syncWatch(planID: 93)
        #expect(result == "Synced 3 activities from watch")
    }

    @Test func syncWatchReturnsUpToDateWhenZero() async throws {
        let service = PlanService(client: makeStubClient { request in
            #expect(request.httpMethod == "POST")
            if request.url?.path() == "/api/integrations/matching/run" { return (200, json([:])) }
            #expect(request.url?.path() == "/api/integrations/coros/sync")
            return (200, json(["activities": 0, "dailyMetrics": 0]))
        })
        let result = try await service.syncWatch(planID: 93)
        #expect(result == "Watch synced · Up to date")
    }

    @Test func syncWatchPropagatesError() async throws {
        let service = PlanService(client: makeStubClient { _ in
            (500, json(["detail": "Watch token expired"]))
        })
        await #expect(throws: Error.self) {
            _ = try await service.syncWatch(planID: 93)
        }
    }
}
