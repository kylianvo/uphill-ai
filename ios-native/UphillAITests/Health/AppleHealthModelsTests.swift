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

    @Test func dailyMetricsEncodeSnakeCase() throws {
        var body = AppleHealthSyncBody(workouts: [], deletedIds: [], planId: nil, tzOffsetMinutes: 0)
        body.dailyMetrics = [AppleHealthDailyMetricUpload(date: "2026-10-13", restingHr: 52, hrvSdnnMs: 61.4, sleepMinutes: nil)]
        let json = try #require(String(data: JSONCoding.encoder.encode(body), encoding: .utf8))
        #expect(json.contains(#""daily_metrics":[{"#))
        #expect(json.contains(#""resting_hr":52"#))
        #expect(json.contains(#""hrv_sdnn_ms":61.4"#))
        #expect(!json.contains("sleep_minutes"))
    }

    @Test func syncResultDecodesDailyMetrics() throws {
        let raw = #"{"accepted":0,"rejected":[],"deleted":0,"daily_metrics":{"accepted":2,"rejected":[{"date":"2026-10-01","reason":"no values"}]}}"#
        let result = try JSONCoding.decoder.decode(AppleHealthSyncResult.self, from: Data(raw.utf8))
        #expect(result.dailyMetrics?.accepted == 2)
        #expect(result.dailyMetrics?.rejected.first?.reason == "no values")
        #expect(result.dailyMetrics?.disabled == nil)
    }

    @Test func statusWithoutRecoveryFlagDecodesAsNil() throws {
        let raw = #"{"apple_health":{"enabled":true,"connected":true,"last_sync_at":null}}"#
        let status = try JSONCoding.decoder.decode(DeviceConnectionStatus.self, from: Data(raw.utf8))
        #expect(status.appleHealth?.recoveryEnabled == nil)
        let off = #"{"apple_health":{"enabled":true,"connected":true,"recovery_enabled":false}}"#
        #expect(try JSONCoding.decoder.decode(DeviceConnectionStatus.self, from: Data(off.utf8)).appleHealth?.recoveryEnabled == false)
    }
}
