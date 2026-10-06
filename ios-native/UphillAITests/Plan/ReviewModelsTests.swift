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

    @Test @MainActor func goalContextFixtureAndEmptyGroups() throws {
        let assessment = try #require(Fixture.decode(PlanGoal.self, "plan_goal.json").assessment)
        let context = try #require(assessment.context)
        #expect(context.race?.distanceKm == 42)
        #expect(context.groups.map { $0.title } == ["Race"])
        #expect(context.groups.first?.rows.map { $0.value } == ["42 km", "2400 m", "Estimated", "6:30"])
        let empty = try JSONCoding.decoder.decode(GoalContext.self, from: json(["race": [:], "athlete": [:]]))
        #expect(empty.groups.isEmpty)
        #expect(assessment.anchors.isEmpty)
    }

    @Test @MainActor func goalContextValuesAndAnchorLabels() throws {
        let context = try JSONCoding.decoder.decode(GoalContext.self, from: json([
            "race": ["distance_km": 0, "gain_m": 0, "profile_source": "gpx", "field": ["winner_mins": 120, "percentile_mins": ["p10": 150, "p50": 180, "p90": 240]]],
            "athlete": ["weight_kg": 65, "threshold_pace": "4:30"]
        ]))
        #expect(context.groups.map { $0.title } == ["Race", "Field", "You"])
        #expect(context.groups[0].rows.map { $0.value } == ["0 km", "0 m", "GPX"])
        #expect(context.groups[1].rows.count == 4)
        #expect(context.groups[2].rows.last?.value == "4:30/km")
        let anchor = try JSONCoding.decoder.decode(GoalAnchor.self, from: json(["id": "a", "method": "easy_pace", "minutes": 180]))
        #expect(anchor.methodLabel == "Course physics from your easy pace")
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

    @Test func decodesWeekReviewPlannedAndActualVolume() throws {
        let jsonStr = "{\"week_number\": 2, \"completion_pct\": 85.0, \"planned\": {\"duration_minutes\": 270.0, \"distance_km\": 45.0, \"elevation_gain_m\": 800.0, \"workout_count\": 5}, \"actual\": {\"total_actual_km\": 46.2, \"total_actual_minutes\": 275.0, \"total_actual_vert_m\": 820.0, \"matched_km\": 46.2, \"matched_count\": 5, \"unplanned_km\": 0.0, \"unplanned_hours\": 0.0, \"unplanned_count\": 0}, \"per_workout\": []}"
        let review = try JSONCoding.decoder.decode(WeekReview.self, from: jsonStr.data(using: .utf8)!)
        #expect(review.planned?.distanceKm == 45.0)
        #expect(review.actual?.totalActualKm == 46.2)
        #expect(review.actual?.totalActualVertM == 820.0)
    }

    @Test func decodesKnowledgeCardModel() throws {
        let jsonStr = "{\"id\": 42, \"chapter_title\": \"Aerobic Nutrition\", \"summary\": \"Fuel early.\", \"key_points\": [\"Carbs\"], \"tags\": [\"nutrition\"], \"topic\": \"Nutrition\"}"
        let card = try JSONCoding.decoder.decode(KnowledgeCardModel.self, from: jsonStr.data(using: .utf8)!)
        #expect(card.id == 42)
        #expect(card.chapterTitle == "Aerobic Nutrition")
        #expect(card.topic == "Nutrition")
        #expect(card.keyPoints.count == 1)
    }
}
