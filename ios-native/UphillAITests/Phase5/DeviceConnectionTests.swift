import Testing
import Foundation
@testable import UphillAI

@Suite("DeviceConnectionTests")
struct DeviceConnectionTests {
    @Test func deviceConnectionStatusDecoding() throws {
        let json = """
        {
            "coros": {
                "connected": true,
                "last_sync_at": "2026-10-06T08:30:00Z",
                "device_model": "COROS APEX 2 Pro"
            }
        }
        """.data(using: .utf8)!

        let status = try JSONCoding.decoder.decode(DeviceConnectionStatus.self, from: json)
        #expect(status.isCorosConnected == true)
        #expect(status.coros?.deviceModel == "COROS APEX 2 Pro")
        #expect(status.coros?.lastSyncAt == "2026-10-06T08:30:00Z")
    }

    @Test func disconnectedStatus() throws {
        let json = """
        {
            "coros": {
                "connected": false
            }
        }
        """.data(using: .utf8)!

        let status = try JSONCoding.decoder.decode(DeviceConnectionStatus.self, from: json)
        #expect(status.isCorosConnected == false)
        #expect(status.coros?.deviceModel == nil)
    }

    @Test func fitnessSyncDecoding() throws {
        let json = """
        {
            "status": "ok",
            "threshold_pace": "4:42",
            "coros_vo2max": 59.2,
            "coros_running_level": 75.4
        }
        """.data(using: .utf8)!

        let fitness = try JSONCoding.decoder.decode(FitnessSyncResult.self, from: json)
        #expect(fitness.status == "ok")
        #expect(fitness.thresholdPace == "4:42")
        #expect(fitness.corosVo2max == 59.2)
        #expect(fitness.corosRunningLevel == 75.4)
    }

    @Test func corosPushSummaryAndStatus() throws {
        let json = """
        {
            "connected": true,
            "last_pushed_at": "2026-10-06T09:15:00Z",
            "out_of_date": false,
            "partial": false,
            "last_summary": {
                "mode": "plan",
                "days_sent": 14,
                "workouts_sent": 10,
                "left_in_uphill": 2,
                "locked_days": 1,
                "invalid": 0,
                "stale": 0,
                "window_end": "2026-10-20",
                "plan_start": "2026-10-06"
            }
        }
        """.data(using: .utf8)!

        let pushStatus = try JSONCoding.decoder.decode(CorosPushStatus.self, from: json)
        #expect(pushStatus.connected == true)
        #expect(pushStatus.outOfDate == false)
        #expect(pushStatus.lastSummary?.workoutsSent == 10)
        #expect(pushStatus.lastSummary?.windowEnd == "2026-10-20")
    }

    @Test func corosAttributionFormatting() throws {
        let withModel = CorosAttribution(deviceModel: "COROS PACE 3")
        #expect(withModel.provider == "coros")
        #expect(withModel.deviceModel == "COROS PACE 3")

        let withoutModel = CorosAttribution()
        #expect(withoutModel.deviceModel == nil)
    }
}
