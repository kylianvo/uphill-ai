import CoreLocation
import Foundation
import HealthKit

/// HealthStoring over HKHealthStore. Read-only: Uphill never writes to Health.
final class HealthKitStore: HealthStoring, @unchecked Sendable {
    private let store = HKHealthStore()
    private var observers: [HKObserverQuery] = []
    private let lock = NSLock()

    private static let activityTypes: [HKWorkoutActivityType] = [
        .running, .hiking, .stairClimbing, .stairs, .traditionalStrengthTraining, .functionalStrengthTraining,
    ]

    var isAvailable: Bool { HKHealthStore.isHealthDataAvailable() }

    func requestAuthorization() async throws {
        let read: Set<HKObjectType> = [
            .workoutType(), HKSeriesType.workoutRoute(),
            HKQuantityType(.heartRate), HKQuantityType(.distanceWalkingRunning), HKQuantityType(.activeEnergyBurned),
            HKQuantityType(.restingHeartRate), HKQuantityType(.heartRateVariabilitySDNN), HKCategoryType(.sleepAnalysis),
        ]
        try await store.requestAuthorization(toShare: [], read: read)
    }

    func workouts(after anchor: Data?, since start: Date) async throws -> HealthWorkoutPage {
        let types = NSCompoundPredicate(orPredicateWithSubpredicates: Self.activityTypes.map { HKQuery.predicateForWorkouts(with: $0) })
        let window = HKQuery.predicateForSamples(withStart: start, end: nil)
        let predicate = NSCompoundPredicate(andPredicateWithSubpredicates: [types, window])
        let queryAnchor = anchor.flatMap { try? NSKeyedUnarchiver.unarchivedObject(ofClass: HKQueryAnchor.self, from: $0) }
        let descriptor = HKAnchoredObjectQueryDescriptor(predicates: [.workout(predicate)], anchor: queryAnchor)
        let result = try await descriptor.result(for: store)
        var samples: [HealthWorkoutSample] = []
        for workout in result.addedSamples {
            samples.append(await sample(from: workout))
        }
        let newAnchor = try NSKeyedArchiver.archivedData(withRootObject: result.newAnchor, requiringSecureCoding: true)
        return HealthWorkoutPage(samples: samples, deleted: result.deletedObjects.map(\.uuid), anchor: newAnchor)
    }

    func dailyMetrics(from: Date, to: Date) async throws -> [AppleHealthDailyMetricUpload] {
        let calendar = Calendar.current
        let bpm = HKUnit.count().unitDivided(by: .minute())
        let restingHr = try await dailyAverages(.restingHeartRate, unit: bpm, from: from, to: to, calendar: calendar)
        let hrv = try await dailyAverages(.heartRateVariabilitySDNN, unit: .secondUnit(with: .milli), from: from, to: to, calendar: calendar)
        let sleep = try await sleepIntervals(from: from.addingTimeInterval(-86_400), to: to)
        let fromKey = HealthDailyMetricMapper.dayKey(from, calendar: calendar)
        let nights = HealthDailyMetricMapper.sleepMinutes(sleep, calendar: calendar).filter { $0.key >= fromKey }
        return HealthDailyMetricMapper.rows(restingHr: restingHr, hrv: hrv, sleep: nights)
    }

    /// Health's own daily value per local day: the average of that day's samples.
    private func dailyAverages(_ id: HKQuantityTypeIdentifier, unit: HKUnit, from: Date, to: Date,
                               calendar: Calendar) async throws -> [String: Double] {
        let start = calendar.startOfDay(for: from)
        let descriptor = HKStatisticsCollectionQueryDescriptor(
            predicate: .quantitySample(type: HKQuantityType(id), predicate: HKQuery.predicateForSamples(withStart: start, end: to)),
            options: .discreteAverage,
            anchorDate: start,
            intervalComponents: DateComponents(day: 1)
        )
        let collection = try await descriptor.result(for: store)
        var values: [String: Double] = [:]
        for stats in collection.statistics() {
            if let value = stats.averageQuantity()?.doubleValue(for: unit) {
                values[HealthDailyMetricMapper.dayKey(stats.startDate, calendar: calendar)] = value
            }
        }
        return values
    }

    private func sleepIntervals(from: Date, to: Date) async throws -> [HealthDailyMetricMapper.SleepInterval] {
        let asleep: Set<Int> = [
            HKCategoryValueSleepAnalysis.asleepUnspecified.rawValue, HKCategoryValueSleepAnalysis.asleepCore.rawValue,
            HKCategoryValueSleepAnalysis.asleepDeep.rawValue, HKCategoryValueSleepAnalysis.asleepREM.rawValue,
        ]
        let samples = try await HKSampleQueryDescriptor(
            predicates: [.categorySample(type: HKCategoryType(.sleepAnalysis), predicate: HKQuery.predicateForSamples(withStart: from, end: to))],
            sortDescriptors: []
        ).result(for: store)
        // The source name is used only here, to keep one app's night; it never leaves the phone.
        return samples.map {
            .init(start: $0.startDate, end: $0.endDate, source: $0.sourceRevision.source.name, asleep: asleep.contains($0.value))
        }
    }

    /// Workouts wake the app at once; sleep hourly, so a morning wake-up sends last night; resting HR daily.
    private static var observed: [(HKSampleType, HKUpdateFrequency)] {
        [
            (.workoutType(), .immediate),
            (HKCategoryType(.sleepAnalysis), .hourly),
            (HKQuantityType(.restingHeartRate), .daily),
        ]
    }

    func startObserving(onUpdate: @escaping @Sendable () async -> Void) async throws {
        await stopObserving()
        var queries: [HKObserverQuery] = []
        for (type, _) in Self.observed {
            let query = HKObserverQuery(sampleType: type, predicate: nil) { _, completion, error in
                // HealthKit's completion handler isn't Sendable; it is safe to call from any thread.
                nonisolated(unsafe) let done = completion
                guard error == nil else { done(); return }
                Task { await onUpdate(); done() }
            }
            queries.append(query)
            store.execute(query)
        }
        let registered = queries
        lock.withLock { observers = registered }
        try await store.enableBackgroundDelivery(for: .workoutType(), frequency: .immediate)
        // Recovery types are optional: an athlete connected before they existed may not have
        // granted them yet, and that must not stop workout delivery.
        for (type, frequency) in Self.observed.dropFirst() {
            try? await store.enableBackgroundDelivery(for: type, frequency: frequency)
        }
    }

    func stopObserving() async {
        let current = lock.withLock { () -> [HKObserverQuery] in defer { observers = [] }; return observers }
        for query in current { store.stop(query) }
        for (type, _) in Self.observed { try? await store.disableBackgroundDelivery(for: type) }
    }

    private func sample(from workout: HKWorkout) async -> HealthWorkoutSample {
        let kind: HealthWorkoutSample.Kind = switch workout.workoutActivityType {
        case .running: .running
        case .hiking: .hiking
        case .stairClimbing, .stairs: .stairs
        case .traditionalStrengthTraining, .functionalStrengthTraining: .strength
        default: .other
        }
        let bpm = HKUnit.count().unitDivided(by: .minute())
        let hr = workout.statistics(for: HKQuantityType(.heartRate))
        let ascended = (workout.metadata?[HKMetadataKeyElevationAscended] as? HKQuantity)?.doubleValue(for: .meter())
        // Parenthesised: `try?` can't sit to the right of the ternary operator unparenthesised.
        let altitudes = (ascended == nil && kind != .strength) ? (try? await routeAltitudes(for: workout)) : nil
        return HealthWorkoutSample(
            uuid: workout.uuid,
            kind: kind,
            isIndoor: workout.metadata?[HKMetadataKeyIndoorWorkout] as? Bool ?? false,
            start: workout.startDate,
            end: workout.endDate,
            duration: workout.duration,
            distanceMeters: workout.statistics(for: HKQuantityType(.distanceWalkingRunning))?.sumQuantity()?.doubleValue(for: .meter()),
            elevationAscendedMeters: ascended,
            routeAltitudes: altitudes,
            averageHeartRate: hr?.averageQuantity()?.doubleValue(for: bpm),
            maxHeartRate: hr?.maximumQuantity()?.doubleValue(for: bpm),
            activeEnergyKcal: workout.statistics(for: HKQuantityType(.activeEnergyBurned))?.sumQuantity()?.doubleValue(for: .kilocalorie()),
            sourceName: workout.sourceRevision.source.name
        )
    }

    /// Altitudes along the workout's route, used only to compute climb on the phone.
    private func routeAltitudes(for workout: HKWorkout) async throws -> [Double]? {
        let routes = try await HKSampleQueryDescriptor(
            predicates: [.workoutRoute(HKQuery.predicateForObjects(from: workout))], sortDescriptors: []
        ).result(for: store)
        guard let route = routes.first else { return nil }
        var altitudes: [Double] = []
        for try await location in HKWorkoutRouteQueryDescriptor(route).results(for: store) where location.verticalAccuracy >= 0 {
            altitudes.append(location.altitude)
        }
        return altitudes.isEmpty ? nil : altitudes
    }
}
