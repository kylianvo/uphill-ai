import Foundation
import Synchronization
import Testing
@testable import UphillAI

struct JobPollerTests {
    private func poller(_ service: FakeGenerationService, timeout: Duration = .seconds(10)) -> JobPoller {
        JobPoller(service: service, interval: .seconds(2), timeout: timeout, sleep: { _ in })
    }

    private func snapshot() -> PlanSnapshot {
        PlanSnapshot(plan: TestData.plan(["id": 7]), workouts: [TestData.workout(["id": 1, "plan_id": 7])])
    }

    @Test func returnsSnapshotWhenDone() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = [.success(.generating()), .success(.generating()), .success(.done(snapshot()))] }
        let outcome = await poller(service).wait(jobID: "job-1")
        #expect(outcome == .done(snapshot()))
        #expect(service.calls.withLock { $0 }.count == 3)
    }

    @Test func serverErrorMessageIsShown() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = [.success(.error("Gemini quota exceeded"))] }
        #expect(await poller(service).wait(jobID: "j") == .failed("Gemini quota exceeded"))
    }

    @Test func missingServerErrorUsesDefault() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = [.success(.error(nil))] }
        #expect(await poller(service).wait(jobID: "j") == .failed("We couldn't build this plan. Please try again."))
    }

    @Test func notFoundMeansLost() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = [.failure(.http(status: 404, message: "Job not found.", code: nil))] }
        #expect(await poller(service).wait(jobID: "j") == .lost)
    }

    @Test func transportErrorsRetryThenFail() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = Array(repeating: .failure(.transport("offline")), count: 6) }
        #expect(await poller(service).wait(jobID: "j") == .failed(JobPoller.offlineMessage))
        #expect(service.calls.withLock { $0 }.count == 5)
    }

    @Test func transportBlipThenDone() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = [.failure(.transport("blip")), .success(.done(nil))] }
        #expect(await poller(service).wait(jobID: "j") == .done(nil))
    }

    @Test func timesOut() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = [.success(.generating())] }
        let outcome = await poller(service, timeout: .seconds(6)).wait(jobID: "j")
        #expect(outcome == .failed(JobPoller.slowMessage))
        #expect(service.calls.withLock { $0 }.count == 3)   // 6 s / 2 s
    }

    @Test func cancellationStops() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = [.success(.generating())] }
        let real = JobPoller(service: service, interval: .seconds(2), timeout: .seconds(60),
                             sleep: { try await Task.sleep(for: $0) })
        let task = Task { await real.wait(jobID: "j") }
        task.cancel()
        #expect(await task.value == .cancelled)
    }

    @Test func serviceHitsRealPaths() async throws {
        let client = makeStubClient { request in
            switch (request.httpMethod, request.url?.path()) {
            case ("GET", "/api/coach/plan-status/abc"):
                return (200, json(["status": "generating", "plan_id": 3]))
            case ("POST", "/api/coach/adapt-week"):
                return (200, json(["job_id": "abc", "plan_id": 3, "week_number": 2]))
            default:
                return (404, Data())
            }
        }
        let service = GenerationService(client: client)
        let start = try await service.adaptWeek(AdaptWeekBody(planId: 3, weekNumber: 2, overallRpe: nil, fatigueLevel: "hard",
                                                               fatigueNotes: nil, lang: "en", clientToday: "2026-10-07"))
        #expect(start.jobId == "abc")
        #expect(try await service.status(jobID: "abc").status == "generating")
    }
}
