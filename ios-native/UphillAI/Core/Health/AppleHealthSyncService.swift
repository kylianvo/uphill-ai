import Foundation
import os

struct AppleHealthSyncOutcome: Sendable, Equatable {
    let accepted: Int
    let rejected: Int
    let deleted: Int
    /// The first sync found no workouts in 12 weeks. HealthKit never reports a denied
    /// read, so this is the only sign the athlete may have turned access off.
    let nothingFound: Bool
}

enum AppleHealthSyncError: Error, Equatable {
    case notObserving
    case unavailable
}

/// Reads new and deleted workouts from Apple Health and sends them to Uphill. The anchor
/// moves only after every batch was accepted, so a failed upload is retried, never lost.
actor AppleHealthSyncService {
    static let backfill: TimeInterval = 12 * 7 * 86_400
    static let batchSize = 500
    /// Recovery data: 28 days for the server's HRV baseline plus the 7-day readiness window on
    /// the first sync, then the last 3 days, which late Watch writes and overnight sleep firm up.
    static let metricsSeedDays = 35
    static let metricsResendDays = 3
    private static let log = Logger(subsystem: "ai.uphill.app", category: "apple-health")

    private let store: any HealthStoring
    private let api: any AppleHealthUploading
    private let anchors: any HealthAnchorStoring
    private let planId: @Sendable () async -> Int?
    private let now: @Sendable () -> Date
    private let timeZone: TimeZone
    private var running: Task<AppleHealthSyncOutcome, Error>?
    /// From /status; off means the server ignores recovery data, so the phone doesn't read it.
    private var recoveryEnabled = true

    init(store: any HealthStoring, api: any AppleHealthUploading, anchors: any HealthAnchorStoring,
         planId: @escaping @Sendable () async -> Int?, now: @escaping @Sendable () -> Date = { .now },
         timeZone: TimeZone = .current) {
        self.store = store
        self.api = api
        self.anchors = anchors
        self.planId = planId
        self.now = now
        self.timeZone = timeZone
    }

    var isAvailable: Bool { store.isAvailable }

    func isObserving(userId: Int) -> Bool { anchors.observingUserId == userId }

    func setRecoveryEnabled(_ enabled: Bool) { recoveryEnabled = enabled }

    /// "Add recovery data" for athletes who connected before recovery metrics: asks HealthKit
    /// again (the sheet then lists only the new types) and re-sends the full 35 days.
    func addRecoveryAccess(userId: Int) async throws -> AppleHealthSyncOutcome {
        guard store.isAvailable else { throw AppleHealthSyncError.unavailable }
        try await store.requestAuthorization()
        anchors.setMetricsSeeded(false, for: userId)
        return try await sync()
    }

    func connect(userId: Int) async throws -> AppleHealthSyncOutcome {
        guard store.isAvailable else { throw AppleHealthSyncError.unavailable }
        try await store.requestAuthorization()
        if anchors.observingUserId != userId {
            anchors.setAnchor(nil, for: userId)
            anchors.setMetricsSeeded(false, for: userId)
        }
        anchors.setObservingUserId(userId)
        try await startObserving()
        return try await sync()
    }

    func resumeObservingIfNeeded() async {
        guard anchors.observingUserId != nil else { return }
        try? await startObserving()
    }

    func stopObserving(userId: Int) async {
        await store.stopObserving()
        anchors.setAnchor(nil, for: userId)
        anchors.setMetricsSeeded(false, for: userId)
        if anchors.observingUserId == userId { anchors.setObservingUserId(nil) }
    }

    /// Sign-out runs after the session's user is gone, so it uses whoever connected on this phone.
    func stopObservingForSignOut() async {
        guard let id = anchors.observingUserId else { return }
        await stopObserving(userId: id)
    }

    /// A call while a run is in flight waits for it, then joins (or starts) one fresh run: the
    /// in-flight run read Health before this call, possibly for another athlete, so its result
    /// can't stand in for this one.
    func sync() async throws -> AppleHealthSyncOutcome {
        if let previous = running { _ = try? await previous.value }
        if let running { return try await running.value }
        let task = Task {
            defer { self.running = nil }
            return try await self.performSync()
        }
        running = task
        return try await task.value
    }

    private func startObserving() async throws {
        try await store.startObserving { [weak self] in
            _ = try? await self?.sync()
        }
    }

    private func performSync() async throws -> AppleHealthSyncOutcome {
        guard let userId = anchors.observingUserId else { throw AppleHealthSyncError.notObserving }
        let previous = anchors.anchor(for: userId)
        let page = try await store.workouts(after: previous, since: now().addingTimeInterval(-Self.backfill))
        let uploads = page.samples.compactMap { HealthWorkoutMapper.upload(for: $0, timeZone: timeZone) }
        let deleted = page.deleted.map(\.uuidString)
        let plan = await planId()
        let offset = timeZone.secondsFromGMT(for: now()) / 60
        let metrics: [AppleHealthDailyMetricUpload] = if recoveryEnabled {
            await readMetrics(seeded: anchors.metricsSeeded(for: userId))
        } else {
            []
        }

        var accepted = 0, rejected = 0, removed = 0
        var metricsStored = false
        // At least one request, even when nothing changed: it advances last_sync_at, which
        // tells the fitness snapshot the recent weeks were covered.
        let batches = max(1, Int((Double(max(uploads.count, deleted.count)) / Double(Self.batchSize)).rounded(.up)))
        for i in 0..<batches {
            // Signed out or switched athlete mid-sync: stop before another batch goes up under the new session.
            guard anchors.observingUserId == userId else { throw AppleHealthSyncError.notObserving }
            let range = { (count: Int) in min(i * Self.batchSize, count)..<min((i + 1) * Self.batchSize, count) }
            let body = AppleHealthSyncBody(workouts: Array(uploads[range(uploads.count)]),
                                           deletedIds: Array(deleted[range(deleted.count)]),
                                           planId: plan, tzOffsetMinutes: offset,
                                           dailyMetrics: i == 0 ? metrics : [])
            let result = try await api.sync(body)
            if i == 0 { metricsStored = !metrics.isEmpty && result.dailyMetrics?.disabled != true }
            accepted += result.accepted
            rejected += result.rejected.count
            removed += result.deleted
        }
        // Signed out or switched athlete while uploading: don't move anyone's anchor.
        guard anchors.observingUserId == userId else { throw AppleHealthSyncError.notObserving }
        anchors.setAnchor(page.anchor, for: userId)
        // Only a sync that actually delivered rows counts as seeded: an athlete who hasn't
        // granted the recovery types yet reads nothing, and must get the 35 days once they do.
        if metricsStored { anchors.setMetricsSeeded(true, for: userId) }
        return AppleHealthSyncOutcome(accepted: accepted, rejected: rejected, deleted: removed,
                                      nothingFound: previous == nil && uploads.isEmpty)
    }

    /// A read failure never blocks the workouts: it logs and sends nothing.
    private func readMetrics(seeded: Bool) async -> [AppleHealthDailyMetricUpload] {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = timeZone
        let end = now()
        let days = seeded ? Self.metricsResendDays : Self.metricsSeedDays
        guard let start = calendar.date(byAdding: .day, value: -(days - 1), to: calendar.startOfDay(for: end)) else { return [] }
        do {
            return try await store.dailyMetrics(from: start, to: end)
        } catch {
            Self.log.error("apple health daily metrics read failed: \(error.localizedDescription, privacy: .public)")
            return []
        }
    }
}
