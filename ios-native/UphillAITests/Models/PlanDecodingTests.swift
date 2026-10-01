import Foundation
import Testing
@testable import UphillAI

struct PlanDecodingTests {
    @Test func decodesRecordedActivePlan() throws {
        let response = try Fixture.decode(ActivePlanResponse.self, "active_plan.json")
        let snapshot = try #require(response.snapshot)
        #expect(snapshot.plan.raceName == "Vietnam Mountain Marathon 42K")
        #expect(snapshot.workouts.count == 21)
        #expect(snapshot.workouts.contains { $0.isPriority })
        #expect(snapshot.workouts.contains { $0.isRest })
    }

    @Test func decodesInactivePlan() throws {
        let response = try Fixture.decode(ActivePlanResponse.self, "active_plan_none.json")
        #expect(response.active == false)
        #expect(response.snapshot == nil)
    }

    @Test func decodesRecentPlans() throws {
        struct Recent: Decodable { let plans: [Plan] }
        let recent = try Fixture.decode(Recent.self, "recent_plans.json")
        #expect(recent.plans.count == 2)
    }

    @Test func missingPriorityDecodesAsFalse() throws {
        let object: [String: Any] = [
            "id": 3, "plan_id": 1, "week_number": 1, "day_of_week": "Tuesday", "phase": "Base",
            "title": "Easy", "type": "Easy Run", "duration_minutes": 30, "target_zone": "Z2",
            "source": "ai_generated", "is_completed": 0, "is_missed": 0,
        ]
        let workout = try JSONCoding.decoder.decode(Workout.self, from: json(object))
        #expect(workout.isPriority == false)
        #expect(workout.weekday == .tuesday)
    }

    @Test func restRules() {
        #expect(TestData.workout(["type": "Rest", "duration_minutes": 0]).isRest)
        #expect(TestData.workout(["type": "Mobility", "duration_minutes": 0]).isRest)
        #expect(!TestData.workout(["type": "Easy Run", "duration_minutes": 30]).isRest)
    }

    @Test func unknownDayFallsBackToMonday() {
        #expect(TestData.workout(["day_of_week": "Funday"]).weekday == .monday)
    }
}
