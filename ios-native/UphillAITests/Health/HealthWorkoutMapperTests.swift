import Foundation
import Testing
@testable import UphillAI

struct HealthWorkoutMapperTests {
    private let saigon = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
    private let start = Date(timeIntervalSince1970: 1_791_759_600) // 2026-10-12T06:00:00+07:00

    private func sample(_ kind: HealthWorkoutSample.Kind, indoor: Bool = false, distance: Double? = 10_400,
                        ascended: Double? = nil, altitudes: [Double]? = nil) -> HealthWorkoutSample {
        HealthWorkoutSample(uuid: UUID(uuidString: "6F1C2E9A-0000-4000-8000-000000000001")!, kind: kind, isIndoor: indoor,
                            start: start, end: start.addingTimeInterval(3720), duration: 3720,
                            distanceMeters: distance, elevationAscendedMeters: ascended, routeAltitudes: altitudes,
                            averageHeartRate: 147.6, maxHeartRate: 171.2, activeEnergyKcal: 689.7, sourceName: "Apple Watch")
    }

    @Test(arguments: [
        (HealthWorkoutSample.Kind.running, false, "outdoor_run"),
        (.running, true, "indoor_run"),
        (.hiking, false, "hike"),
        (.stairs, false, "hike"),
        (.strength, false, "strength"),
    ])
    func mapsKinds(kind: HealthWorkoutSample.Kind, indoor: Bool, expected: String) {
        #expect(HealthWorkoutMapper.upload(for: sample(kind, indoor: indoor), timeZone: saigon)?.activityType == expected)
    }

    @Test func otherKindsAreSkipped() {
        #expect(HealthWorkoutMapper.upload(for: sample(.other)) == nil)
    }

    @Test func convertsUnitsAndFormatsTimesWithOffset() throws {
        let upload = try #require(HealthWorkoutMapper.upload(for: sample(.running, ascended: 412.4), timeZone: saigon))
        #expect(upload.externalId == "6F1C2E9A-0000-4000-8000-000000000001")
        #expect(upload.startTime == "2026-10-12T06:00:00+07:00")
        #expect(upload.endTime == "2026-10-12T07:02:00+07:00")
        #expect(upload.distanceKm == 10.4)
        #expect(upload.elevationGainM == 412.4)
        #expect(upload.avgHr == 148 && upload.maxHr == 171 && upload.calories == 690)
        #expect(upload.sourceName == "Apple Watch")
    }

    @Test func metadataClimbBeatsRoute() {
        let upload = HealthWorkoutMapper.upload(for: sample(.running, ascended: 300, altitudes: [0, 50, 100]), timeZone: saigon)
        #expect(upload?.elevationGainM == 300)
    }

    @Test func routeClimbIsTheFallback() {
        let upload = HealthWorkoutMapper.upload(for: sample(.hiking, altitudes: [100, 120, 110, 160]), timeZone: saigon)
        #expect(upload?.elevationGainM == 70)
    }

    @Test func noClimbDataLeavesItNil() {
        #expect(HealthWorkoutMapper.upload(for: sample(.running), timeZone: saigon)?.elevationGainM == nil)
    }

    @Test func climbFollowsRealClimbs() {
        #expect(HealthWorkoutMapper.climb(altitudes: [0, 10, 20]) == 20)
        #expect(HealthWorkoutMapper.climb(altitudes: [100, 101, 102, 101, 103, 106, 104, 110]) == 10)
    }

    @Test func noisyAltitudesDoNotInflateClimb() {
        #expect(HealthWorkoutMapper.climb(altitudes: [100, 101, 100, 101, 100, 102, 100]) == 0)
        #expect(HealthWorkoutMapper.climb(altitudes: []) == 0)
    }

    @Test func strengthWithoutDistanceHasNilDistance() {
        #expect(HealthWorkoutMapper.upload(for: sample(.strength, distance: nil), timeZone: saigon)?.distanceKm == nil)
    }
}
