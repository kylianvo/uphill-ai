import Foundation
import Testing
@testable import UphillAI

struct UserDecodingTests {
    @Test func decodesRecordedLogin() throws {
        let response = try Fixture.decode(AuthResponse.self, "auth_login.json")
        #expect(response.sessionToken == "fixture-session-token")
        #expect(response.user.email == "ios-fixtures@uphill.ai")
    }

    @Test func decodesRecordedMe() throws {
        let user = try Fixture.decode(User.self, "auth_me.json")
        #expect(user.email == "ios-fixtures@uphill.ai")
        #expect(user.isCoach == false)
    }

    @Test func decodesFullyPopulatedUser() throws {
        let data = Data("""
        {"id": 7, "email": "a@b.c", "name": "Ana", "role": "admin", "onboarding_complete": true,
         "provider": "google", "has_password": false, "age": 34, "dob": "1991-04-02", "gender": "female",
         "height_cm": 165.0, "weight_kg": 55.5, "goal_type": "finish", "current_weekly_km": 42.5,
         "max_hr": 188, "resting_hr": 52, "aet_hr": 140, "ant_hr": 168, "days_per_week": 5,
         "preferred_run_days": "[\\"Tuesday\\",\\"Saturday\\"]", "long_run_day": "Saturday",
         "injury_history": "", "zone2_pace_min": "6:10", "zone2_pace_max": "6:50",
         "threshold_pace": "4:55", "coros_vo2max": null, "coros_running_level": null,
         "pace_zone_model": "5_zone", "custom_pace_zones": null, "is_coach": true}
        """.utf8)
        let user = try JSONCoding.decoder.decode(User.self, from: data)
        #expect(user.isAdmin)
        #expect(user.isCoach)
        #expect(user.longRunDay == "Saturday")
        #expect(user.zone2PaceMin == "6:10")
    }
}
