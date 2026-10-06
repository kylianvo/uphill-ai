import Foundation
import Synchronization
import Testing
@testable import UphillAI

@MainActor
struct GenerationCenterTests {
    private func defaults() -> UserDefaults { UserDefaults(suiteName: "gen-\(UUID().uuidString)")! }

    private func center(_ service: FakeGenerationService, defaults: UserDefaults) -> GenerationCenter {
        GenerationCenter(service: service, defaults: defaults,
                         makePoller: { JobPoller(service: $0, interval: .milliseconds(1), timeout: .seconds(1), sleep: { _ in }) })
    }

    @Test func tracksUntilDoneAndReports() async {
        let service = FakeGenerationService()
        let snapshot = PlanSnapshot(plan: TestData.plan(["id": 9]), workouts: [])
        service.statuses.withLock { $0 = [.success(.generating()), .success(.done(snapshot))] }
        let store = defaults()
        let center = center(service, defaults: store)
        let finished = Mutex<[String]>([])
        center.onFinished = { kind, outcome in finished.withLock { $0.append("\(kind) \(outcome == .done(snapshot))") } }

        center.track(kind: .newPlan, jobID: "job-9", summary: ["A"])
        #expect(center.running?.jobID == "job-9")
        #expect(store.data(forKey: GenerationCenter.defaultsKey) != nil)

        while center.running != nil { await Task.yield() }
        #expect(finished.withLock { $0 } == ["newPlan true"])
        #expect(center.lastOutcome?.outcome == .done(snapshot))
        #expect(store.data(forKey: GenerationCenter.defaultsKey) == nil)
    }

    @Test func resumesPersistedJob() async {
        let service = FakeGenerationService()
        service.statuses.withLock { $0 = [.success(.done(nil))] }
        let store = defaults()
        let slow = FakeGenerationService()
        slow.statuses.withLock { $0 = [.success(.generating())] }
        // A real-sleep poller, so the first center is still waiting when we "relaunch".
        let first = GenerationCenter(service: slow, defaults: store,
                                     makePoller: { JobPoller(service: $0, interval: .seconds(60), timeout: .seconds(120)) })
        first.track(kind: .adaptWeek, jobID: "job-2", summary: [])
        let persisted = store.data(forKey: GenerationCenter.defaultsKey)!
        first.reset()
        store.set(persisted, forKey: GenerationCenter.defaultsKey)   // the old process is gone; its persisted job stays
        // Simulate relaunch: a new center reading the same defaults.
        let second = center(service, defaults: store)
        second.resumeIfNeeded()
        #expect(second.running?.jobID == "job-2")
        #expect(second.running?.kind == .adaptWeek)
        while second.running != nil { await Task.yield() }
        #expect(service.calls.withLock { $0 }.first == "status job-2")
    }

    @Test func resetStopsPollingAndClearsAccountState() async {
        let service = FakeGenerationService()
        let store = defaults()
        let center = center(service, defaults: store)
        center.track(kind: .newPlan, jobID: "old-account", summary: [])
        center.reset()
        await Task.yield()
        #expect(center.running == nil)
        #expect(center.lastOutcome == nil)
        #expect(store.data(forKey: GenerationCenter.defaultsKey) == nil)
    }

    @Test func lostJobIsReported() async {
        let service = FakeGenerationService()   // empty script → 404 → lost
        let center = center(service, defaults: defaults())
        center.track(kind: .nextWeek, jobID: "gone", summary: [])
        while center.running != nil { await Task.yield() }
        #expect(center.lastOutcome?.outcome == .lost)
    }
}
