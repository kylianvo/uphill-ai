import Foundation
import Testing
@testable import UphillAI

struct ReviewModelsTests {
    @Test func decodesBlockCompletion() throws {
        let r = try Fixture.decode(BlockCompletionResponse.self, "block_completion.json")
        #expect(r.maxGeneratedWeek >= 1)
        #expect(!r.blocks.isEmpty)
        #expect(r.blocks.allSatisfy { $0.weekStart <= $0.weekEnd })
    }

    @Test func decodesWeekReview() throws {
        let r = try Fixture.decode(WeekReview.self, "week_review.json")
        #expect(r.weekNumber == 1)
        #expect(!r.perWorkout.isEmpty)
        #expect(r.narrative?.summary != nil)
    }

    /// The recorded rules-tier assessment has no tiers yet (no race history), so `goals` is nil.
    @Test func decodesPlanGoal() throws {
        let g = try Fixture.decode(PlanGoal.self, "plan_goal.json")
        #expect(g.assessment != nil)
        #expect(g.assessment?.goals == nil)
        #expect(g.status.kind == .notAssessed)
        #expect(g.targetTimeHours == 6.5)
    }

    @Test func decodesTiers() throws {
        let a = try JSONCoding.decoder.decode(GoalAssessment.self, from: json(["id": 1, "goals": ["a": 360.0, "b": 390.0, "c": 420.0], "reasoning": ["x"], "missing": []]))
        #expect(a.goals == GoalTiers(a: 360, b: 390, c: 420))
        #expect(a.reasoning == ["x"])
    }

    @Test func goalStatusKinds() throws {
        func status(_ s: String) throws -> GoalStatus {
            try JSONCoding.decoder.decode(GoalStatus.self, from: json(["state": s, "suggested_mins": 380]))
        }
        #expect(try status("on_track").kind == .onTrack)
        #expect(try status("behind").kind == .behind)
        #expect(try status("weird").kind == .notAssessed)
    }

    @Test func narrativeToleratesMissingArrays() throws {
        let n = try JSONCoding.decoder.decode(WeekNarrative.self, from: json(["summary": "Solid week."]))
        #expect(n.highlights.isEmpty)
        #expect(n.watch.isEmpty)
    }
}
