import CoreLocation
import Foundation
import HealthKit

/// HealthStoring over HKHealthStore. Read-only: Uphill never writes to Health.
final class HealthKitStore: HealthStoring, @unchecked Sendable {
    private let store = HKHealthStore()
    private var observer: HKObserverQuery?
    private let lock = NSLock()

    private static let activityTypes: [HKWorkoutActivityType] = [
        .running, .hiking, .stairClimbing, .stairs, .traditionalStrengthTraining, .functionalStrengthTraining,
    ]

    var isAvailable: Bool { HKHealthStore.isHealthDataAvailable() }

    func requestAuthorization() async throws {
        let read: Set<HKObjectType> = [
            .workoutType(), HKSeriesType.workoutRoute(),
            HKQuantityType(.heartRate), HKQuantityType(.distanceWalkingRunning), HKQuantityType(.activeEnergyBurned),
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

    func startObserving(onUpdate: @escaping @Sendable () async -> Void) async throws {
        await stopObserving()
        let query = HKObserverQuery(sampleType: .workoutType(), predicate: nil) { _, completion, error in
            // HealthKit's completion handler isn't Sendable; it is safe to call from any thread.
            nonisolated(unsafe) let done = completion
            guard error == nil else { done(); return }
            Task { await onUpdate(); done() }
        }
        lock.withLock { observer = query }
        store.execute(query)
        try await store.enableBackgroundDelivery(for: .workoutType(), frequency: .immediate)
    }

    func stopObserving() async {
        let current = lock.withLock { () -> HKObserverQuery? in defer { observer = nil }; return observer }
        if let current { store.stop(current) }
        try? await store.disableBackgroundDelivery(for: .workoutType())
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
