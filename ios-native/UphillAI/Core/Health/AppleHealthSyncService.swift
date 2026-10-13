import Foundation

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

    private let store: any HealthStoring
    private let api: any AppleHealthUploading
    private let anchors: any HealthAnchorStoring
    private let planId: @Sendable () async -> Int?
    private let now: @Sendable () -> Date
    private let timeZone: TimeZone
    private var running: Task<AppleHealthSyncOutcome, Error>?

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

    func connect(userId: Int) async throws -> AppleHealthSyncOutcome {
        guard store.isAvailable else { throw AppleHealthSyncError.unavailable }
        try await store.requestAuthorization()
        if anchors.observingUserId != userId { anchors.setAnchor(nil, for: userId) }
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

        var accepted = 0, rejected = 0, removed = 0
        // At least one request, even when nothing changed: it advances last_sync_at, which
        // tells the fitness snapshot the recent weeks were covered.
        let batches = max(1, Int((Double(max(uploads.count, deleted.count)) / Double(Self.batchSize)).rounded(.up)))
        for i in 0..<batches {
            // Signed out or switched athlete mid-sync: stop before another batch goes up under the new session.
            guard anchors.observingUserId == userId else { throw AppleHealthSyncError.notObserving }
            let range = { (count: Int) in min(i * Self.batchSize, count)..<min((i + 1) * Self.batchSize, count) }
            let body = AppleHealthSyncBody(workouts: Array(uploads[range(uploads.count)]),
                                           deletedIds: Array(deleted[range(deleted.count)]),
                                           planId: plan, tzOffsetMinutes: offset)
            let result = try await api.sync(body)
            accepted += result.accepted
            rejected += result.rejected.count
            removed += result.deleted
        }
        // Signed out or switched athlete while uploading: don't move anyone's anchor.
        guard anchors.observingUserId == userId else { throw AppleHealthSyncError.notObserving }
        anchors.setAnchor(page.anchor, for: userId)
        return AppleHealthSyncOutcome(accepted: accepted, rejected: rejected, deleted: removed,
                                      nothingFound: previous == nil && uploads.isEmpty)
    }
}
