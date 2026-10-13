import Foundation
import Testing
@testable import UphillAI

struct AppleHealthModelsTests {
    @Test func decodesSyncResult() throws {
        let result = try Fixture.decode(AppleHealthSyncResult.self, "apple_health_sync.json")
        #expect(result.accepted == 1)
        #expect(result.rejected.map(\.externalId) == ["6F1C2E9A-0000-4000-8000-000000000002"])
    }

    @Test func decodesStatusWithAppleHealth() throws {
        let status = try Fixture.decode(DeviceConnectionStatus.self, "integrations_status.json")
        #expect(status.appleHealth?.enabled == true)
        #expect(status.appleHealth?.connected == true)
    }

    @Test func statusWithoutAppleHealthStillDecodes() throws {
        let status = try JSONCoding.decoder.decode(DeviceConnectionStatus.self, from: Data(#"{"coros":{"connected":false}}"#.utf8))
        #expect(status.appleHealth == nil)
    }

    @Test func uploadEncodesSnakeCaseAndOmitsNils() throws {
        let body = AppleHealthSyncBody(
            workouts: [AppleHealthWorkoutUpload(externalId: "A", activityType: "strength", startTime: "2026-10-12T06:00:00+07:00",
                                                endTime: "2026-10-12T06:40:00+07:00", durationSeconds: 2400, distanceKm: nil,
                                                elevationGainM: nil, avgHr: 120, maxHr: nil, calories: nil, sourceName: "Apple Watch")],
            deletedIds: ["B"], planId: nil, tzOffsetMinutes: 420)
        let json = try #require(String(data: JSONCoding.encoder.encode(body), encoding: .utf8))
        #expect(json.contains(#""external_id":"A""#))
        #expect(json.contains(#""deleted_ids":["B"]"#))
        #expect(json.contains(#""tz_offset_minutes":420"#))
        #expect(!json.contains("distance_km"))
        #expect(!json.contains("plan_id"))
    }
}
