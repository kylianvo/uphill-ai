import Foundation
import Testing
@testable import UphillAI

struct GearPromptContextTests {
    @Test func profileContextMatchesWebFormat() throws {
        let user = try Fixture.decode(User.self, "auth_me.json")
        #expect(GearParams.profileContext(user) == "Age: 30, Max HR: 185, Resting HR: 60, Weekly volume: 30km")
        #expect(GearParams.profileContext(nil) == "None")
    }

    @Test func planContextMatchesWebFormat() throws {
        let plan = try Fixture.decode(PlanSnapshot.self, "active_plan.json").plan
        #expect(GearParams.planContext(plan) == "Vietnam Mountain Marathon 42K on 2026-12-12, Goal: time, Distance: 42km, Elevation: 2400m, Target Time: 6.5h")
        #expect(GearParams.planContext(nil) == "None")
    }
}
