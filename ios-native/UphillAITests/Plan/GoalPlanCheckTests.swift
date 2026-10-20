import Foundation
import Testing
@testable import UphillAI

struct GoalPlanCheckTests {
    private func decode<T: Decodable>(_ type: T.Type, _ object: [String: Any]) throws -> T {
        try JSONCoding.decoder.decode(type, from: JSONSerialization.data(withJSONObject: object))
    }

    private func feasibility(
        _ verdict: String,
        levers: [String] = ["more_days", "double_sessions", "shorter_race"],
        weeks: Int? = nil,
        confidence: String = "measured"
    ) throws -> GoalFeasibility {
        try decode(GoalFeasibility.self, [
            "verdict": verdict, "capacity_h": 3.7, "needed_h": 10.9,
            "weeks_needed": weeks.map { $0 as Any } ?? NSNull(),
            "levers": levers, "confidence": confidence,
        ])
    }

    @Test func planGoalDecodesFeasibilityAndStaysOptional() throws {
        let status: [String: Any] = ["state": "no_target", "suggested_mins": NSNull()]
        let with = try decode(PlanGoal.self, [
            "assessment": NSNull(), "status": status, "target_time_hours": 9.0,
            "feasibility": ["verdict": "unsupported", "capacity_h": 3.7, "needed_h": 10.9, "weeks_needed": NSNull(),
                            "levers": ["more_days"], "confidence": "measured"],
        ])
        #expect(with.feasibility?.verdict == "unsupported")
        let without = try decode(PlanGoal.self, ["assessment": NSNull(), "status": status, "target_time_hours": 9.0])
        #expect(without.feasibility == nil)
    }

    @Test func aSupportedGoalSaysNothing() throws {
        #expect(try feasibility("supported").check == nil)
    }

    @Test func anUnsupportedGoalShowsWhatTheWeekHoldsAndTwoLevers() throws {
        let check = try #require(try feasibility("unsupported").check)
        #expect(check.tone == .short)
        #expect(check.line == "Your week holds about 3.7h; this goal needs about 10.9h.")
        #expect(check.levers == ["More training days would close the gap.", "Double sessions would help."])
    }

    @Test func aTightGoalIsMarkedTight() throws {
        #expect(try feasibility("stretch").check?.tone == .tight)
    }

    @Test func weeksLeverUsesTheCountAndAnEstimatedPaceIsNoted() throws {
        let check = try #require(try feasibility("unsupported", levers: ["more_weeks"], weeks: 18, confidence: "estimated").check)
        #expect(check.levers == ["Reaching peak week takes about 18 weeks."])
        #expect(check.note == "Pace is estimated.")
    }

    @Test func planSupportNoticeNamesTheShiftAndStaysQuietWhenBacked() throws {
        func assessment(supported: Bool) throws -> GoalAssessment {
            try decode(GoalAssessment.self, [
                "id": 1, "goals": ["a": 819.0, "b": 870.0, "c": 960.0], "reasoning": [], "missing": [],
                "plan_support": ["a_supported": supported, "shortfall_pct": 1.2,
                                 "improvement_assumed_pct": 2.75, "improvement_supported_pct": 1.5],
            ])
        }
        let notice = try #require(try assessment(supported: false).planSupportNotice)
        #expect(notice == "Goals moved 1.2% later: the plan delivers 1.5% of the 2.8% improvement they assume.")
        #expect(try assessment(supported: true).planSupportNotice == nil)
    }
}

struct GoalPathTests {
    private func path(_ extra: [String: Any] = [:]) throws -> GoalPath {
        var o: [String: Any] = ["b": "on", "a": "behind", "measured_pct": 2.14, "expected_pct": 1.5, "weeks": 6, "confidence": "medium"]
        o.merge(extra) { $1 }
        return try JSONCoding.decoder.decode(GoalPath.self, from: JSONSerialization.data(withJSONObject: o))
    }

    @Test func wordsAndLine() throws {
        let p = try path()
        #expect(GoalPath.word(p.b) == "on track" && GoalPath.word(p.a) == "behind" && GoalPath.word("ahead") == "ahead")
        #expect(p.line == "Aerobic speed is 2.1% faster than at the start.")
        #expect(try path(["measured_pct": -1.0]).line == "Aerobic speed is 1% slower than at the start.")
    }

    @Test func earlyReadsAreFlagged() throws {
        #expect(try path(["confidence": "low"]).note == "Early read: only a few weeks of runs.")
        #expect(try path().note == nil)
    }
}

struct ClimbVenuePromptTests {
    private func section(steepness: Double?, mountain: String? = nil, stairs: Bool = false, treadmill: Bool = false) -> TrainingVenueSection {
        TrainingVenueSection(
            mountainDays: .constant([]), trainingMountain: .constant(mountain), mountainMinMinutes: .constant(nil),
            stairAccess: .constant(stairs), useTreadmill: .constant(treadmill), treadmillMaxIncline: nil,
            courseSteepness: steepness
        )
    }

    @Test func aSteepCourseWithNoPlaceToClimbAsksWhere() {
        #expect(section(steepness: 53).needsClimbVenue)
    }

    @Test func aMountainStairsOrTreadmillSilencesIt() {
        #expect(!section(steepness: 53, mountain: "nui_dinh").needsClimbVenue)
        #expect(!section(steepness: 53, stairs: true).needsClimbVenue)
        #expect(!section(steepness: 53, treadmill: true).needsClimbVenue)
    }

    @Test func aFlatOrUnknownCourseNeverAsks() {
        #expect(!section(steepness: 8).needsClimbVenue)
        #expect(!section(steepness: nil).needsClimbVenue)
    }
}
