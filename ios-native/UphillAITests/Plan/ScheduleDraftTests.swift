import Foundation
import Testing
@testable import UphillAI

struct ScheduleDraftTests {
    private func body(_ draft: ScheduleDraft) throws -> [String: Any] {
        var body = AdaptWeekBody(planId: 1, weekNumber: 2, overallRpe: nil, fatigueLevel: "medium", fatigueNotes: nil, lang: "en", clientToday: "2026-10-02")
        draft.applyChanges(to: &body)
        return try #require(try JSONSerialization.jsonObject(with: JSONCoding.encoder.encode(body)) as? [String: Any])
    }
    @Test func unchangedFieldsAreOmitted() throws {
        let draft = ScheduleDraft(plan: TestData.plan())
        let json = try body(draft)
        for key in ["preferred_days", "long_run_day", "days_per_week", "double_session_days", "has_gym_access", "use_treadmill", "training_environment", "mountain_days", "stair_access", "treadmill_max_incline", "max_continuous_jog_min"] { #expect(json[key] == nil) }
    }
    @Test func onlyChangedFieldsAreSent() throws {
        var draft = ScheduleDraft(plan: TestData.plan(["long_run_day": "Saturday", "has_gym_access": true]))
        draft.longRunDay = .sunday
        draft.hasGymAccess = false
        let json = try body(draft)
        #expect(json["long_run_day"] as? String == "Sunday")
        #expect(json["has_gym_access"] as? Bool == false)
        #expect(json["days_per_week"] == nil)
        #expect(json["preferred_days"] == nil)
    }
    @Test func jogFieldIsOnlyForGettingStarted() throws {
        var race = ScheduleDraft(plan: TestData.plan())
        race.maxContinuousJogMin = 15
        #expect(try body(race)["max_continuous_jog_min"] == nil)
        var beginner = ScheduleDraft(plan: TestData.plan(["goal_type": "start_running"]))
        beginner.maxContinuousJogMin = 15
        #expect(try body(beginner)["max_continuous_jog_min"] as? Int == 15)
    }
    @Test func trainingVenueChangesAreSent() throws {
        var draft = ScheduleDraft(plan: TestData.plan(["mountain_days": "[\"Sunday\"]", "stair_access": false, "treadmill_max_incline": 15]))
        #expect(draft.mountainDays == [.sunday])
        #expect(!draft.hasChanges)
        draft.mountainDays.insert(.saturday)
        draft.stairAccess = true
        draft.treadmillMaxIncline = 25
        #expect(draft.hasChanges)
        let json = try body(draft)
        #expect(json["mountain_days"] as? [String] == ["Saturday", "Sunday"])
        #expect(json["stair_access"] as? Bool == true)
        #expect(json["treadmill_max_incline"] as? Int == 25)
    }
    @Test func venueDefaultsForAnOlderPlan() {
        let draft = ScheduleDraft(plan: TestData.plan())
        #expect(draft.mountainDays.isEmpty)
        #expect(!draft.stairAccess)
        #expect(draft.treadmillMaxIncline == 15)
    }
    @Test func unknownLongRunDayCanBeSet() throws {
        var draft = ScheduleDraft(plan: TestData.plan())
        #expect(draft.longRunDay == nil)
        draft.longRunDay = .saturday
        #expect(try body(draft)["long_run_day"] as? String == "Saturday")
    }
}
