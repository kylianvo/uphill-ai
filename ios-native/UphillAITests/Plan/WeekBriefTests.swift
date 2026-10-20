import Foundation
import Testing
@testable import UphillAI

struct WeekBriefTests {
    private func wo(_ id: Int, _ week: Int, _ type: String, _ mins: Double) -> Workout {
        TestData.workout(["id": id, "week_number": week, "type": type, "duration_minutes": mins])
    }

    @Test func chipsReportTimeLongRunAndSessionTypeChanges() {
        let prev = [wo(1, 1, "Easy Run", 45), wo(2, 1, "Long Run", 90), wo(3, 1, "Tempo", 40)]
        let cur = [wo(4, 2, "Easy Run", 45), wo(5, 2, "Long Run", 120), wo(6, 2, "Intervals", 50)]
        let chips = WeekDiff.chips(prev: prev, cur: cur)
        #expect(chips == [.time(delta: 40), .long(from: 90, to: 120), .added(type: "Intervals", count: 1), .removed(type: "Tempo", count: 1)])
        #expect(WeekBriefView.text(chips[0]) == "+40 min")
        #expect(WeekBriefView.text(chips[3]) == "−1 Tempo")
    }

    @Test func noChipsWithoutBothWeeksOrWithRestOnly() {
        #expect(WeekDiff.chips(prev: [], cur: [wo(1, 2, "Easy Run", 30)]).isEmpty)
        #expect(WeekDiff.chips(prev: [wo(1, 1, "Rest", 0)], cur: [wo(2, 2, "Easy Run", 30)]).isEmpty)
    }

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
