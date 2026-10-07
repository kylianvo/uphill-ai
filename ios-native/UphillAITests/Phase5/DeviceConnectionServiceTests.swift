import Foundation
import Synchronization
import Testing
@testable import UphillAI

/// The service must surface real backend state and real failures -- never a
/// made-up "connected" or "sent" result when a request fails.
struct DeviceConnectionServiceTests {
    @Test func fetchStatusThrowsInsteadOfFakingConnected() async throws {
        let service = DeviceConnectionService(client: makeStubClient { _ in (500, json(["detail": "boom"])) })
        await #expect(throws: APIError.self) { _ = try await service.fetchStatus() }
    }

    @Test func syncNowThrowsWhenCorosFails() async throws {
        let service = DeviceConnectionService(client: makeStubClient { _ in
            (502, json(["detail": "COROS sync failed. Please try again shortly."]))
        })
        await #expect(throws: APIError.self) { _ = try await service.syncNow(days: 30) }
    }

    @Test func syncNowRunsMatchingAfterSync() async throws {
        let paths = Mutex<[String]>([])
        let service = DeviceConnectionService(client: makeStubClient { request in
            paths.withLock { $0.append(request.url?.path() ?? "") }
            if request.url?.path() == "/api/integrations/matching/run" {
                #expect(request.url?.query()?.contains("days=30") == true)
                return (200, json(["matched": 2]))
            }
            return (200, json(["activities": 2, "daily_metrics": 30]))
        })
        let result = try await service.syncNow(days: 30)
        #expect(result.activities == 2)
        #expect(paths.withLock { $0 } == ["/api/integrations/coros/sync", "/api/integrations/matching/run"])
    }

    @Test func syncFitnessThrowsWhenCorosFails() async throws {
        let service = DeviceConnectionService(client: makeStubClient { _ in (502, json(["detail": "x"])) })
        await #expect(throws: APIError.self) { _ = try await service.syncFitness() }
    }

    @Test func fetchPushStatusReadsBackendShape() async throws {
        let service = DeviceConnectionService(client: makeStubClient { request in
            #expect(request.url?.path() == "/api/integrations/coros/push-status")
            return (200, json([
                "connected": true, "last_pushed_at": "2026-10-06T09:15:00+00:00",
                "out_of_date": true, "partial": false,
                "last_summary": ["days_sent": 12, "workouts_sent": 7, "left_in_uphill": 1, "locked_days": 0,
                                 "invalid": 0, "window_end": "2026-11-02"],
            ]))
        })
        let status = try await service.fetchPushStatus(clientToday: "2026-10-07")
        #expect(status.connected)
        #expect(status.outOfDate == true)
        #expect(status.lastPushedAt == "2026-10-06T09:15:00+00:00")
        #expect(status.lastSummary?.workoutsSent == 7)
    }

    @Test func fetchPushStatusNotConnected() async throws {
        let service = DeviceConnectionService(client: makeStubClient { _ in (200, json(["connected": false])) })
        let status = try await service.fetchPushStatus(clientToday: "2026-10-07")
        #expect(status.connected == false)
        #expect(status.lastSummary == nil)
    }

    @Test func pushToCorosReportsBackendRefusal() async throws {
        let service = DeviceConnectionService(client: makeStubClient { _ in
            (409, json(["detail": ["code": "NOTHING_to_push", "params": [:]]]))
        })
        let outcome = try await service.pushToCoros(clientToday: "2026-10-07", lang: "en")
        #expect(outcome.isSuccess == false)
        #expect(outcome.errorCode == "NOTHING_to_push")
        #expect(outcome.errorMessage == "Nothing to send: there are no upcoming runs in your plan.")
    }

    @Test func pushToCorosThrowsOnTransportFailure() async throws {
        let service = DeviceConnectionService(client: makeStubClient { _ in (500, json(["detail": "boom"])) })
        await #expect(throws: APIError.self) { _ = try await service.pushToCoros(clientToday: "2026-10-07", lang: "en") }
    }

    @Test func completeCorosPostsTheOneTimeTokenOnce() async throws {
        let posts = Mutex(0)
        let service = DeviceConnectionService(client: makeStubClient { _ in
            posts.withLock { $0 += 1 }
            return (400, json(["detail": "COROS connection could not be completed."]))
        })
        await #expect(throws: APIError.self) { _ = try await service.completeCoros(state: "s", token: "t") }
        #expect(posts.withLock { $0 } == 1)
    }
}
