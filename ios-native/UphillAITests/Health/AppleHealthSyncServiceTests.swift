import Foundation
import Synchronization
import Testing
@testable import UphillAI

final class FakeHealthStore: HealthStoring {
    let pages = Mutex<[HealthWorkoutPage]>([])
    let requestedSince = Mutex<[Date]>([])
    let requestedAnchors = Mutex<[Data?]>([])
    let observing = Mutex(false)
    let authorizeError = Mutex<Error?>(nil)
    let authorizations = Mutex(0)
    let metricRanges = Mutex<[(Date, Date)]>([])
    let metricRows = Mutex<[AppleHealthDailyMetricUpload]>([])
    let metricsError = Mutex<Error?>(nil)
    var isAvailable: Bool { true }

    func dailyMetrics(from: Date, to: Date) async throws -> [AppleHealthDailyMetricUpload] {
        metricRanges.withLock { $0.append((from, to)) }
        if let e = metricsError.withLock({ $0 }) { throw e }
        return metricRows.withLock { $0 }
    }

    func requestAuthorization() async throws {
        authorizations.withLock { $0 += 1 }
        if let e = authorizeError.withLock({ $0 }) { throw e }
    }
    func workouts(after anchor: Data?, since start: Date) async throws -> HealthWorkoutPage {
        requestedAnchors.withLock { $0.append(anchor) }
        requestedSince.withLock { $0.append(start) }
        return pages.withLock { $0.isEmpty ? HealthWorkoutPage(samples: [], deleted: [], anchor: anchor) : $0.removeFirst() }
    }
    func startObserving(onUpdate: @escaping @Sendable () async -> Void) async throws { observing.withLock { $0 = true } }
    func stopObserving() async { observing.withLock { $0 = false } }
}

final class FakeUploader: AppleHealthUploading {
    let bodies = Mutex<[AppleHealthSyncBody]>([])
    /// Index of the call (0-based) that throws, if any.
    let failOnCall = Mutex<Int?>(nil)
    let disconnects = Mutex(0)
    /// Runs inside each upload, e.g. to sign the athlete out mid-sync.
    let onSync = Mutex<(@Sendable () -> Void)?>(nil)

    func sync(_ body: AppleHealthSyncBody) async throws -> AppleHealthSyncResult {
        let index = bodies.withLock { $0.append(body); return $0.count - 1 }
        onSync.withLock { $0 }?()
        if failOnCall.withLock({ $0 }) == index { throw APIError.http(status: 503, message: "down", code: nil) }
        return AppleHealthSyncResult(accepted: body.workouts.count, rejected: [], deleted: body.deletedIds.count)
    }
    func disconnect() async throws { disconnects.withLock { $0 += 1 } }
}

final class MemoryAnchorStore: HealthAnchorStoring {
    let anchors = Mutex<[Int: Data]>([:])
    let observer = Mutex<Int?>(nil)
    func anchor(for userId: Int) -> Data? { anchors.withLock { $0[userId] } }
    func setAnchor(_ anchor: Data?, for userId: Int) { anchors.withLock { $0[userId] = anchor } }
    var observingUserId: Int? { observer.withLock { $0 } }
    func setObservingUserId(_ id: Int?) { observer.withLock { $0 = id } }
    let seeded = Mutex<Set<Int>>([])
    func metricsSeeded(for userId: Int) -> Bool { seeded.withLock { $0.contains(userId) } }
    func setMetricsSeeded(_ value: Bool, for userId: Int) {
        seeded.withLock { if value { $0.insert(userId) } else { $0.remove(userId) } }
    }
}

private func run(_ n: Int) -> HealthWorkoutSample {
    let start = Date(timeIntervalSince1970: 1_791_759_600 + Double(n) * 86_400)
    return HealthWorkoutSample(uuid: UUID(), kind: .running, isIndoor: false, start: start, end: start.addingTimeInterval(3600),
                               duration: 3600, distanceMeters: 10_000, elevationAscendedMeters: 100, routeAltitudes: nil,
                               averageHeartRate: 140, maxHeartRate: 160, activeEnergyKcal: 600, sourceName: "Apple Watch")
}

struct AppleHealthSyncServiceTests {
    let store = FakeHealthStore()
    let api = FakeUploader()
    let anchors = MemoryAnchorStore()
    let now = Date(timeIntervalSince1970: 1_792_000_000)

    func service() -> AppleHealthSyncService {
        AppleHealthSyncService(store: store, api: api, anchors: anchors, planId: { 42 }, now: { [now] in now },
                               timeZone: TimeZone(identifier: "UTC")!)
    }

    @Test func connectAuthorizesObservesAndBackfillsTwelveWeeks() async throws {
        store.pages.withLock { $0 = [HealthWorkoutPage(samples: [run(1)], deleted: [], anchor: Data([1]))] }
        let outcome = try await service().connect(userId: 7)
        #expect(outcome == AppleHealthSyncOutcome(accepted: 1, rejected: 0, deleted: 0, nothingFound: false))
        #expect(store.observing.withLock { $0 })
        #expect(anchors.observingUserId == 7)
        #expect(store.requestedSince.withLock { $0 } == [now.addingTimeInterval(-12 * 7 * 86_400)])
        #expect(anchors.anchor(for: 7) == Data([1]))
        #expect(api.bodies.withLock { $0.first?.planId } == 42)
    }

    @Test func firstSyncWithNothingSaysSo() async throws {
        let outcome = try await service().connect(userId: 7)
        #expect(outcome.nothingFound)
    }

    @Test func emptyIncrementalSyncStillCallsTheServer() async throws {
        anchors.setObservingUserId(7)
        anchors.setAnchor(Data([9]), for: 7)
        let outcome = try await service().sync()
        #expect(!outcome.nothingFound)
        #expect(api.bodies.withLock { $0.count } == 1)
        #expect(store.requestedAnchors.withLock { $0 } == [Data([9])])
    }

    @Test func splitsIntoBatchesOf500() async throws {
        anchors.setObservingUserId(7)
        let samples = (0..<1001).map(run)
        let deleted = (0..<3).map { _ in UUID() }
        store.pages.withLock { $0 = [HealthWorkoutPage(samples: samples, deleted: deleted, anchor: Data([2]))] }
        let outcome = try await service().sync()
        let sizes = api.bodies.withLock { $0.map(\.workouts.count) }
        #expect(sizes == [500, 500, 1])
        #expect(api.bodies.withLock { $0.flatMap(\.deletedIds).count } == 3)
        #expect(outcome.accepted == 1001 && outcome.deleted == 3)
    }

    @Test func failedSecondBatchKeepsOldAnchor() async throws {
        anchors.setObservingUserId(7)
        anchors.setAnchor(Data([1]), for: 7)
        store.pages.withLock { $0 = [HealthWorkoutPage(samples: (0..<600).map(run), deleted: [], anchor: Data([2]))] }
        api.failOnCall.withLock { $0 = 1 }
        await #expect(throws: APIError.self) { try await service().sync() }
        #expect(anchors.anchor(for: 7) == Data([1]))
    }

    @Test func syncWithoutObservingThrows() async {
        await #expect(throws: AppleHealthSyncError.notObserving) { try await service().sync() }
    }

    @Test func test_sync_does_not_save_anchor_when_user_changed() async throws {
        anchors.setObservingUserId(7)
        let svc = service()
        store.pages.withLock { $0 = [HealthWorkoutPage(samples: [run(1)], deleted: [], anchor: Data([3]))] }
        // Sign-out lands while the upload is in flight.
        let anchors = self.anchors
        api.onSync.withLock { $0 = { anchors.setObservingUserId(nil) } }
        await #expect(throws: AppleHealthSyncError.notObserving) { try await svc.sync() }
        #expect(anchors.anchor(for: 7) == nil)
    }

    @Test func signOutMidImportStopsFurtherBatches() async throws {
        anchors.setObservingUserId(7)
        let svc = service()
        store.pages.withLock { $0 = [HealthWorkoutPage(samples: (0..<600).map(run), deleted: [], anchor: Data([5]))] }
        let anchors = self.anchors
        api.onSync.withLock { $0 = { anchors.setObservingUserId(nil) } }
        await #expect(throws: AppleHealthSyncError.notObserving) { try await svc.sync() }
        #expect(api.bodies.withLock { $0.count } == 1)
    }

    @Test func signOutStopsObservingWhoeverConnected() async throws {
        store.pages.withLock { $0 = [HealthWorkoutPage(samples: [run(1)], deleted: [], anchor: Data([1]))] }
        let svc = service()
        _ = try await svc.connect(userId: 7)
        #expect(anchors.anchor(for: 7) == Data([1]))
        await svc.stopObservingForSignOut()
        #expect(anchors.observingUserId == nil && anchors.anchor(for: 7) == nil)
    }

    @Test func test_stop_observing_clears_anchor() async throws {
        store.pages.withLock { $0 = [HealthWorkoutPage(samples: [run(1)], deleted: [], anchor: Data([1]))] }
        let svc = service()
        _ = try await svc.connect(userId: 7)
        #expect(anchors.anchor(for: 7) == Data([1]))
        await svc.stopObserving(userId: 7)
        #expect(anchors.observingUserId == nil)
        #expect(anchors.anchor(for: 7) == nil)
        #expect(!store.observing.withLock { $0 })
    }

    @Test func concurrentSyncsShareOneRun() async throws {
        anchors.setObservingUserId(7)
        let svc = service()
        async let a = svc.sync()
        async let b = svc.sync()
        _ = try await (a, b)
        #expect(api.bodies.withLock { $0.count } <= 2)
        #expect(store.requestedAnchors.withLock { $0.count } == api.bodies.withLock { $0.count })
    }

    @Test func otherKindsAreDroppedBeforeUpload() async throws {
        anchors.setObservingUserId(7)
        var other = run(1)
        other = HealthWorkoutSample(uuid: other.uuid, kind: .other, isIndoor: false, start: other.start, end: other.end,
                                    duration: other.duration, distanceMeters: nil, elevationAscendedMeters: nil, routeAltitudes: nil,
                                    averageHeartRate: nil, maxHeartRate: nil, activeEnergyKcal: nil, sourceName: "Yoga App")
        store.pages.withLock { $0 = [HealthWorkoutPage(samples: [other, run(2)], deleted: [], anchor: Data([4]))] }
        _ = try await service().sync()
        #expect(api.bodies.withLock { $0.first?.workouts.count } == 1)
    }

    // MARK: Recovery metrics

    private func metricRow(_ date: String) -> AppleHealthDailyMetricUpload {
        AppleHealthDailyMetricUpload(date: date, restingHr: 52, hrvSdnnMs: 61.4, sleepMinutes: 412)
    }

    private func requestedDays(_ i: Int) -> Int {
        let (from, to) = store.metricRanges.withLock { $0[i] }
        var utc = Calendar(identifier: .gregorian)
        utc.timeZone = TimeZone(identifier: "UTC")!
        return (utc.dateComponents([.day], from: from, to: utc.startOfDay(for: to)).day ?? 0) + 1
    }

    @Test func firstSyncSendsThirtyFiveDaysThenThree() async throws {
        anchors.setObservingUserId(7)
        store.metricRows.withLock { $0 = [metricRow("2026-10-13")] }
        let svc = service()
        _ = try await svc.sync()
        _ = try await svc.sync()
        #expect(requestedDays(0) == 35)
        #expect(requestedDays(1) == 3)
        #expect(api.bodies.withLock { $0.map(\.dailyMetrics.count) } == [1, 1])
    }

    @Test func metricsRideOnTheFirstBatchOnly() async throws {
        anchors.setObservingUserId(7)
        store.metricRows.withLock { $0 = [metricRow("2026-10-13")] }
        store.pages.withLock { $0 = [HealthWorkoutPage(samples: (0..<600).map(run), deleted: [], anchor: Data([2]))] }
        _ = try await service().sync()
        #expect(api.bodies.withLock { $0.map(\.dailyMetrics.count) } == [1, 0])
    }

    @Test func failedUploadLeavesTheSeedUnset() async throws {
        anchors.setObservingUserId(7)
        store.metricRows.withLock { $0 = [metricRow("2026-10-13")] }
        api.failOnCall.withLock { $0 = 0 }
        await #expect(throws: APIError.self) { try await service().sync() }
        #expect(!anchors.metricsSeeded(for: 7))
    }

    @Test func emptyReadDoesNotSeed() async throws {
        // Recovery types not granted yet: HealthKit reads nothing, so the next sync asks for 35 days again.
        anchors.setObservingUserId(7)
        let svc = service()
        _ = try await svc.sync()
        _ = try await svc.sync()
        #expect(requestedDays(1) == 35)
    }

    @Test func recoveryDisabledReadsNothing() async throws {
        anchors.setObservingUserId(7)
        store.metricRows.withLock { $0 = [metricRow("2026-10-13")] }
        let svc = service()
        await svc.setRecoveryEnabled(false)
        _ = try await svc.sync()
        #expect(store.metricRanges.withLock { $0.isEmpty })
        #expect(api.bodies.withLock { $0.first?.dailyMetrics } == [])
    }

    @Test func metricReadFailureStillSyncsWorkouts() async throws {
        anchors.setObservingUserId(7)
        store.metricsError.withLock { $0 = APIError.http(status: 500, message: "health", code: nil) }
        store.pages.withLock { $0 = [HealthWorkoutPage(samples: [run(1)], deleted: [], anchor: Data([6]))] }
        let outcome = try await service().sync()
        #expect(outcome.accepted == 1)
        #expect(api.bodies.withLock { $0.first?.dailyMetrics } == [])
        #expect(anchors.anchor(for: 7) == Data([6]))
    }

    @Test func signOutClearsTheSeed() async throws {
        store.metricRows.withLock { $0 = [metricRow("2026-10-13")] }
        let svc = service()
        _ = try await svc.connect(userId: 7)
        #expect(anchors.metricsSeeded(for: 7))
        await svc.stopObservingForSignOut()
        #expect(!anchors.metricsSeeded(for: 7))
    }
}
