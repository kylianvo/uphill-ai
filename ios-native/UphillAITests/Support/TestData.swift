import Foundation
@testable import UphillAI

/// Builds models through the real decoder so tests exercise the same path as
/// production. Pass only the fields a test cares about.
enum TestData {
    static func plan(_ overrides: [String: Any] = [:]) -> Plan {
        var base: [String: Any] = [
            "id": 1, "user_id": 1, "race_name": "Test Race", "race_date": "2026-12-19",
            "goal_type": "finish", "total_weeks": 12, "current_week": 1,
            "start_date": "2026-09-30", "plan_status": "active",
        ]
        base.merge(overrides) { _, new in new }
        return try! JSONCoding.decoder.decode(Plan.self, from: json(base))
    }

    static func workout(_ overrides: [String: Any] = [:]) -> Workout {
        var base: [String: Any] = [
            "id": 1, "plan_id": 1, "week_number": 1, "day_of_week": "Monday", "phase": "Base",
            "title": "Easy Run", "type": "Easy Run", "duration_minutes": 45.0, "distance_km": 7.0,
            "target_zone": "Z2", "elevation_gain_m": 50.0, "source": "ai_generated",
            "is_completed": 0, "is_missed": 0, "is_priority": false,
        ]
        base.merge(overrides) { _, new in new }
        return try! JSONCoding.decoder.decode(Workout.self, from: json(base))
    }
}
