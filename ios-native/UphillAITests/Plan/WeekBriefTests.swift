import Foundation
import Testing
@testable import UphillAI

struct WeekBriefTests {
    @Test func decodesBriefAndMissedReasonAndWeekContext() throws {
        let review = try JSONCoding.decoder.decode(WeekReview.self, from: json([
            "week_number": 2, "completion_pct": 50.0,
            "brief": ["why": "Rebuild after the missed long run.", "benefits": ["Steady load"], "watch": NSNull()],
        ]))
        #expect(review.brief?.why == "Rebuild after the missed long run.")
        #expect(review.brief?.watch == nil)

        let w = TestData.workout(["is_missed": 1, "missed_reason": "sick"])
        #expect(w.missedReason == "sick")

        let ctx = try JSONCoding.decoder.decode(WeekContext.self, from: json([
            "done_min": 120, "planned_min": 300,
            "next_key": ["day_of_week": "Saturday", "title": "Long Run", "type": "Long Run"],
        ]))
        #expect(ctx.nextKey?.dayOfWeek == "Saturday")
        #expect(WorkoutDetailSheet.weekSoFarNote(ctx).hasPrefix("Week so far: 120 of 300 min."))
    }
}

struct SessionsToUnlockTests {
    @Test func countsSessionsLeftToSeventyPercent() {
        #expect(PlanViewModel.sessionsToUnlock(sessions: 10, completionPct: 50) == 2)
        #expect(PlanViewModel.sessionsToUnlock(sessions: 10, completionPct: 90) == 0)
        #expect(PlanViewModel.sessionsToUnlock(sessions: 0, completionPct: 50) == nil)
    }
}

struct GoalProgressTests {
    @Test func barsComeFromCompletedWorkoutsAndOnlyFill() throws {
        let workouts = [
            TestData.workout(["id": 1, "week_number": 1, "type": "Long Run", "duration_minutes": 100.0, "distance_km": 15.0, "is_completed": 1]),
            TestData.workout(["id": 2, "week_number": 1, "type": "Easy Run", "duration_minutes": 50.0, "distance_km": 8.0, "is_completed": 1]),
            TestData.workout(["id": 3, "week_number": 2, "type": "Long Run", "duration_minutes": 140.0, "distance_km": 20.0]),
        ]
        let p = try #require(GoalProgress.make(workouts: workouts, targets: GoalTargets(longRunMin: 300, peakWeekKm: 70), path: nil))
        #expect(p.longRun == .init(done: 100, target: 300))
        #expect(p.weekKm?.done == 23)
        #expect(GoalProgress.Bar(done: 9, target: 5).fraction == 1)
        #expect(GoalProgress.make(workouts: workouts, targets: nil, path: nil) == nil)
    }
}
