import Foundation
import Testing
@testable import UphillAI

@Suite("MilestonePathTests")
@MainActor
struct MilestonePathTests {
    private func item(_ key: String, weeks: [Int], at: String? = nil, source: String? = nil) -> [String: Any] {
        ["key": key, "kind": "jog_min", "threshold": 5, "stage": "A", "typical_weeks": weeks,
         "achieved_at": at as Any? ?? NSNull(), "source": source as Any? ?? NSNull()]
    }

    private func milestones(next: String? = "jog_10", hasEvent: Bool = false, target: String = "5k", items: [[String: Any]]? = nil) -> [String: Any] {
        ["target": target, "has_event": hasEvent, "next_key": next as Any? ?? NSNull(),
         "items": items ?? [item("first_session", weeks: [1, 1], at: "2026-10-06T07:00:00+00:00", source: "auto"),
                            item("jog_5", weeks: [3, 5], at: "2026-10-12T07:00:00+00:00", source: "auto"),
                            item("jog_10", weeks: [4, 6]), item("first_5k", weeks: [9, 12])]]
    }

    private func makeModel(_ ms: [String: Any]?, extra: [String: Any] = [:]) -> (PlanViewModel, FakePlanService) {
        var overrides: [String: Any] = ["id": 5, "race_name": "First 5K", "goal_type": "start_running", "milestone_target": "5k", "start_date": "2026-10-05"]
        if let ms { overrides["beginner_milestones"] = ms }
        overrides.merge(extra) { _, new in new }
        let plan = TestData.plan(overrides)
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(PlanSnapshot(plan: plan, workouts: [TestData.workout(["plan_id": 5])])) }
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(secondsFromGMT: 0)!
        let model = PlanViewModel(service: service, cache: .inMemory(), now: { cal.date(from: DateComponents(year: 2026, month: 10, day: 20))! }, calendar: cal)
        UserDefaults.standard.removeObject(forKey: "milestonesSeen.5")
        return (model, service)
    }

    @Test func headerTextCountsReachedOfTotal() async throws {
        let (model, _) = makeModel(milestones())
        await model.load()
        #expect(model.beginnerHeaderText == "First 5K · 2 of 4 milestones")
    }

    @Test func legacyPlanHasNoMilestoneHeader() async {
        let (model, _) = makeModel(nil)
        await model.load()
        #expect(model.beginnerMilestones == nil && model.beginnerHeaderText == nil)
    }

    @Test func newlyAchievedKeyIgnoresBaselineAndSeen() async throws {
        let items = [item("jog_5", weeks: [3, 5], at: "2026-10-06T07:00:00+00:00", source: "baseline"), item("jog_10", weeks: [4, 6])]
        let (baseline, _) = makeModel(milestones(items: items))
        await baseline.load()
        baseline.refreshCelebration()
        #expect(baseline.celebration == nil)

        let (model, _) = makeModel(milestones())
        await model.load()
        model.refreshCelebration()
        #expect(model.celebration?.key == "jog_5")
        model.dismissCelebration()
        model.refreshCelebration()
        #expect(model.celebration == nil)  // everything reached is now seen
    }

    @Test func markUpdatesMilestonesFromResponse() async throws {
        let (model, service) = makeModel(milestones())
        await model.load()
        let updated = try JSONCoding.decoder.decode(PlanMilestones.self, from: JSONSerialization.data(withJSONObject: milestones(next: "first_5k", items: [
            item("jog_10", weeks: [4, 6], at: "2026-10-20T07:00:00+00:00", source: "manual"), item("first_5k", weeks: [9, 12])])))
        service.milestoneResult.withLock { $0 = .success(updated) }
        await model.markMilestone("jog_10")
        #expect(model.beginnerMilestones?.nextKey == "first_5k")
        #expect(service.calls.withLock { $0 }.contains("milestone mark jog_10"))
    }

    @Test func firstFiveKOnA5kTargetCanUpgrade() throws {
        let ms = try JSONCoding.decoder.decode(PlanMilestones.self, from: JSONSerialization.data(withJSONObject: milestones(next: nil, items: [
            item("first_5k", weeks: [9, 12], at: "2026-11-20T07:00:00+00:00", source: "auto")])))
        #expect(ms.canUpgrade)
    }

    @Test func decodesMilestonesOnThePlan() throws {
        let plan = TestData.plan(["milestone_target": "10k", "has_target_event": true, "beginner_milestones": milestones(hasEvent: true, target: "10k")])
        #expect(plan.milestoneTarget == "10k" && plan.hasTargetEvent == true)
        #expect(plan.beginnerMilestones?.items.count == 4 && plan.beginnerMilestones?.hasEvent == true)
    }
}
