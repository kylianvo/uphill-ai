import Foundation
import Testing
@testable import UphillAI

struct PlanJourneyTests {
    private func journey(_ extra: [String: Any] = [:]) throws -> PlanJourney {
        var object: [String: Any] = [
            "current_week": 5, "total_weeks": 12, "days_to_race": 49,
            "phases": [["name": "Base", "start_week": 1, "end_week": 4], ["name": "Build", "start_week": 5, "end_week": 10]],
            "milestones": [["key": "first_recovery_week", "week": 4, "done": true], ["key": "long_run_3h", "week": 6, "done": false]],
            "preferences": ["days_per_week": 4, "long_run_day": "Saturday", "mountain": "chau_thoi"],
            "deviations": [],
        ]
        object.merge(extra) { $1 }
        return try JSONCoding.decoder.decode(PlanJourney.self, from: JSONSerialization.data(withJSONObject: object))
    }

    @Test func decodesPhasesMilestonesAndTheNextOne() throws {
        let j = try journey()
        #expect(j.phases.map(\.weeks) == [4, 6])
        #expect(j.nextMilestone?.key == "long_run_3h")
        #expect(j.nextMilestone?.title == "First 3-hour Long Run")
        #expect(j.followsSchedule)
    }

    @Test func builtAroundYouNamesDaysLongRunAndMountain() throws {
        #expect(try journey().builtAroundYou == "4 days a week · long run Sat · Mountain training")
        let bare = try journey(["preferences": ["days_per_week": NSNull(), "long_run_day": NSNull(), "mountain": NSNull()]])
        #expect(bare.builtAroundYou == "")
    }

    @Test func deviationsMeanThePlanDoesNotFollowTheSchedule() throws {
        #expect(try journey(["deviations": [["code": "LONG_RUN_DAY", "week": 7]]]).followsSchedule == false)
    }

    @Test func coachNudgeDecodesAndNilWhenQuiet() throws {
        let quiet = try JSONCoding.decoder.decode(CoachNudgeResponse.self, from: Data(#"{"nudge":null}"#.utf8))
        #expect(quiet.nudge == nil)
        let loud = try JSONCoding.decoder.decode(CoachNudgeResponse.self, from: Data(#"{"nudge":{"tone":"heads_up","text":"x","source":"rules"}}"#.utf8))
        #expect(loud.nudge?.kind == .headsUp)
    }
}
