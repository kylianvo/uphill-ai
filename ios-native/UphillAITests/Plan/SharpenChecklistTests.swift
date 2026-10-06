import Foundation
import Testing
@testable import UphillAI

struct SharpenChecklistTests {
    private func user(_ values: [String: Any]) throws -> User {
        var json = try #require(try JSONSerialization.jsonObject(with: Fixture.data("auth_me.json")) as? [String: Any])
        for field in ["aet_hr", "max_hr", "zone2_pace_min", "threshold_pace", "athlete_notes", "age", "weight_kg"] { json.removeValue(forKey: field) }
        json.merge(values) { _, new in new }
        return try JSONCoding.decoder.decode(User.self, from: JSONSerialization.data(withJSONObject: json))
    }

    @Test func missingInputsRemainIncomplete() throws {
        let items = SharpenChecklist.items(user: try user([:]), plan: TestData.plan())
        #expect(items.count == 5)
        #expect(items.allSatisfy { !$0.done })
    }

    @Test func eachItemUsesItsOwnCompletionRule() throws {
        let values: [String: Any] = ["aet_hr": 140, "max_hr": 185, "threshold_pace": "5:00", "athlete_notes": "Knee", "age": 35, "weight_kg": 65]
        let items = SharpenChecklist.items(user: try user(values), plan: TestData.plan(["long_run_day": "Saturday"]))
        #expect(items.allSatisfy { $0.done })
        #expect(SharpenChecklist.items(user: try user(["aet_hr": 140]), plan: TestData.plan())[0].done == false)
        #expect(SharpenChecklist.items(user: try user(["zone2_pace_min": "6:30"]), plan: TestData.plan())[1].done)
        #expect(SharpenChecklist.items(user: try user(["athlete_notes": "  "]), plan: TestData.plan())[2].done == false)
        #expect(SharpenChecklist.items(user: try user(["age": 35]), plan: TestData.plan())[4].done == false)
    }
}
