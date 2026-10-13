import Foundation
import Testing
@testable import UphillAI

struct SharpenChecklistTests {
    private func user(_ values: [String: Any]) throws -> User {
        var json = try #require(try JSONSerialization.jsonObject(with: Fixture.data("auth_me.json")) as? [String: Any])
        for field in ["aet_hr", "ant_hr", "zone2_pace_min", "threshold_pace", "athlete_notes", "injury_history", "field_sources"] {
            json.removeValue(forKey: field)
        }
        json.merge(values) { _, new in new }
        return try JSONCoding.decoder.decode(User.self, from: JSONSerialization.data(withJSONObject: json))
    }

    private func items(_ values: [String: Any], coros: Bool = false, races: Bool = false) throws -> [String: Bool] {
        let list = SharpenChecklist.items(user: try user(values), corosConnected: coros, raceHistoryLinked: races)
        return Dictionary(uniqueKeysWithValues: list.map { ($0.id, $0.done) })
    }

    @Test func listsTheFiveContextItemsInOrder() throws {
        let list = SharpenChecklist.items(user: try user([:]), corosConnected: false, raceHistoryLinked: false)
        #expect(list.map(\.id) == ["watch", "races", "hr", "pace", "injuries"])
        #expect(list.map(\.destination) == [.watch, .raceHistory, .heartRate, .paces, .aboutYou])
        #expect(list.allSatisfy { !$0.done })
    }

    @Test func watchAndRacesFollowConnections() throws {
        let done = try items([:], coros: true, races: true)
        #expect(done["watch"] == true)
        #expect(done["races"] == true)
    }

    @Test func estimatedThresholdsAndPacesStayOpen() throws {
        let estimated: [String: Any] = [
            "aet_hr": 140, "ant_hr": 165, "zone2_pace_min": "6:30",
            "field_sources": ["aet_hr": ["source": "default"], "ant_hr": ["source": "default"],
                              "zone2_pace_min": ["source": "default"]],
        ]
        let done = try items(estimated)
        #expect(done["hr"] == false)
        #expect(done["pace"] == false)
    }

    @Test func enteredValuesCountAsDone() throws {
        let done = try items([
            "aet_hr": 140, "ant_hr": 165, "threshold_pace": "4:45", "injury_history": "minor",
            "field_sources": ["aet_hr": ["source": "athlete"], "ant_hr": ["source": "coach"]],
        ])
        #expect(done["hr"] == true)
        #expect(done["pace"] == true)
        #expect(done["injuries"] == true)
    }

    @Test @MainActor func snoozeLastsTwoWeeks() {
        let defaults = UserDefaults(suiteName: "sharpen-\(UUID())")!
        let start = Date(timeIntervalSince1970: 1_000_000)
        let before = SharpenChecklistCard.isSnoozed(at: start, defaults: defaults)
        defaults.set(start.timeIntervalSince1970, forKey: SharpenChecklistCard.snoozeKey)
        let within = SharpenChecklistCard.isSnoozed(at: start.addingTimeInterval(13 * 86_400), defaults: defaults)
        let after = SharpenChecklistCard.isSnoozed(at: start.addingTimeInterval(15 * 86_400), defaults: defaults)
        #expect(!before)
        #expect(within)
        #expect(!after)
    }
}
