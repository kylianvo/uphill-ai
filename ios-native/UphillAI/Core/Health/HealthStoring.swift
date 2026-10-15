import Foundation

struct HealthWorkoutPage: Sendable {
    let samples: [HealthWorkoutSample]
    let deleted: [UUID]
    /// Archived HKQueryAnchor to resume from next time.
    let anchor: Data?
}

/// The HealthKit surface the sync needs, so tests and the debug sample data can stand in for it.
protocol HealthStoring: Sendable {
    var isAvailable: Bool { get }
    func requestAuthorization() async throws
    /// Workouts added or deleted since `anchor`; with no anchor, those starting after `start`.
    func workouts(after anchor: Data?, since start: Date) async throws -> HealthWorkoutPage
    /// Resting HR, HRV and asleep minutes per local day from `from` up to `to`, one row per day
    /// with any value. Sleep is read from the evening before `from`, so the first night is complete.
    func dailyMetrics(from: Date, to: Date) async throws -> [AppleHealthDailyMetricUpload]
    /// Registers background delivery; `onUpdate` runs when a workout, sleep or resting HR is saved to Health.
    func startObserving(onUpdate: @escaping @Sendable () async -> Void) async throws
    func stopObserving() async
}

protocol HealthAnchorStoring: Sendable {
    func anchor(for userId: Int) -> Data?
    func setAnchor(_ anchor: Data?, for userId: Int)
    /// The athlete who connected Apple Health on this phone. Background wakes can come
    /// before the session is restored, so the sync identifies the athlete from this.
    var observingUserId: Int? { get }
    func setObservingUserId(_ id: Int?)
    /// Whether this athlete's first 35 days of recovery data reached the server; after that
    /// each sync re-sends only the last 3 days.
    func metricsSeeded(for userId: Int) -> Bool
    func setMetricsSeeded(_ seeded: Bool, for userId: Int)
}

/// UserDefaults is thread-safe; the class only holds it.
final class UserDefaultsAnchorStore: HealthAnchorStoring, @unchecked Sendable {
    private let defaults: UserDefaults
    private static let observingKey = "UPHILL_HEALTH_OBSERVING_USER"

    init(defaults: UserDefaults = .standard) { self.defaults = defaults }

    func anchor(for userId: Int) -> Data? { defaults.data(forKey: "UPHILL_HEALTH_ANCHOR_\(userId)") }
    func setAnchor(_ anchor: Data?, for userId: Int) { defaults.set(anchor, forKey: "UPHILL_HEALTH_ANCHOR_\(userId)") }
    var observingUserId: Int? { defaults.object(forKey: Self.observingKey) as? Int }
    func setObservingUserId(_ id: Int?) { defaults.set(id, forKey: Self.observingKey) }
    func metricsSeeded(for userId: Int) -> Bool { defaults.bool(forKey: "appleHealthMetricsSeeded_\(userId)") }
    func setMetricsSeeded(_ seeded: Bool, for userId: Int) {
        defaults.set(seeded, forKey: "appleHealthMetricsSeeded_\(userId)")
    }
}

/// Debug-only stand-in for HealthKit (Developer menu → Sample Health data): three workouts
/// from this week on the first sync, nothing after, and 35 days of recovery data whose last
/// five days (today included) dip in HRV, so the server marks them "low".
struct SampleHealthStore: HealthStoring {
    static let defaultsKey = "UPHILL_SAMPLE_HEALTH"
    var isAvailable: Bool { true }

    func requestAuthorization() async throws {}
    func startObserving(onUpdate: @escaping @Sendable () async -> Void) async throws {}
    func stopObserving() async {}

    func dailyMetrics(from: Date, to: Date) async throws -> [AppleHealthDailyMetricUpload] {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)
        var rows: [AppleHealthDailyMetricUpload] = []
        var day = calendar.startOfDay(for: from)
        while day <= to {
            let daysAgo = calendar.dateComponents([.day], from: day, to: today).day ?? 0
            if (0..<35).contains(daysAgo) {
                let dip = (1...4).contains(daysAgo) || daysAgo == 0
                rows.append(AppleHealthDailyMetricUpload(
                    date: HealthDailyMetricMapper.dayKey(day, calendar: calendar),
                    restingHr: 50 + daysAgo % 5,
                    hrvSdnnMs: dip ? 48 + Double(daysAgo % 3) : 62 + Double(daysAgo % 5) - 2,
                    sleepMinutes: 380 + (daysAgo * 17) % 81
                ))
            }
            guard let next = calendar.date(byAdding: .day, value: 1, to: day) else { break }
            day = next
        }
        return rows
    }

    func workouts(after anchor: Data?, since start: Date) async throws -> HealthWorkoutPage {
        guard anchor == nil else { return HealthWorkoutPage(samples: [], deleted: [], anchor: anchor) }
        let day: TimeInterval = 86_400
        let base = Calendar.current.startOfDay(for: .now).addingTimeInterval(6 * 3600)
        func sample(_ id: String, _ kind: HealthWorkoutSample.Kind, daysAgo: Double, minutes: Double, meters: Double?, climb: Double?) -> HealthWorkoutSample {
            let s = base.addingTimeInterval(-daysAgo * day)
            return HealthWorkoutSample(uuid: UUID(uuidString: id)!, kind: kind, isIndoor: false, start: s,
                                       end: s.addingTimeInterval(minutes * 60), duration: minutes * 60, distanceMeters: meters,
                                       elevationAscendedMeters: climb, routeAltitudes: nil, averageHeartRate: 142,
                                       maxHeartRate: 168, activeEnergyKcal: minutes * 10, sourceName: "Apple Watch")
        }
        return HealthWorkoutPage(samples: [
            sample("5A3E0000-0000-4000-8000-000000000001", .running, daysAgo: 1, minutes: 62, meters: 10_400, climb: 412),
            sample("5A3E0000-0000-4000-8000-000000000002", .hiking, daysAgo: 2, minutes: 95, meters: 7_200, climb: 680),
            sample("5A3E0000-0000-4000-8000-000000000003", .strength, daysAgo: 3, minutes: 40, meters: nil, climb: nil),
        ], deleted: [], anchor: Data("sample".utf8))
    }
}
