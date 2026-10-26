import Foundation
import Testing
@testable import UphillAI

struct BeginnerSetupTests {
    private let cal: Calendar = {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        return c
    }()
    private var today: Date { PlanCalendar.day(from: "2026-10-07", calendar: cal)! }
    private func day(_ s: String) -> Date { PlanCalendar.day(from: s, calendar: cal)! }
    private func encoded(_ body: some Encodable) throws -> [String: Any] {
        try #require(try JSONSerialization.jsonObject(with: JSONCoding.encoder.encode(body)) as? [String: Any])
    }

    private func draft() -> PlanSetupDraft {
        var d = PlanSetupDraft(prefill: nil, today: today, calendar: cal)
        d.goal = .startRunning
        d.milestoneTarget = .tenK
        d.currentJogMin = 10
        return d
    }

    @Test func startRunningStepsIncludeBeginnerGoal() {
        #expect(SetupStep.steps(for: .startRunning, includeProfile: false) == [.goal, .beginnerGoal, .schedule, .venues, .startDate, .review])
    }

    @Test func bothBodiesCarryTargetAndJog() throws {
        let d = draft()
        let plan = try encoded(d.planBody(calendar: cal))
        let onboarding = try encoded(d.onboardingBody(skipPlan: false, calendar: cal))
        for body in [plan, onboarding] {
            #expect(body["milestone_target"] as? String == "10k")
            #expect(body["current_jog_min"] as? Int == 10)
            #expect(body["event_date"] == nil)
        }
    }

    @Test func eventFieldsAreSentOnlyWhenOn() throws {
        var d = draft()
        d.hasBeginnerEvent = true
        d.beginnerEventName = "Parkrun"
        d.beginnerEventDate = day("2026-12-12")
        let plan = try encoded(d.planBody(calendar: cal))
        #expect(plan["event_name"] as? String == "Parkrun" && plan["event_date"] as? String == "2026-12-12")
        d.hasBeginnerEvent = false
        #expect(try encoded(d.planBody(calendar: cal))["event_date"] == nil)
    }

    @Test func otherGoalsSendNoMilestoneFields() throws {
        var d = draft()
        d.goal = .returning
        #expect(try encoded(d.planBody(calendar: cal))["milestone_target"] == nil)
    }

    @Test func eventNeedsAFutureDate() {
        var d = draft()
        d.hasBeginnerEvent = true
        d.beginnerEventDate = nil
        #expect(!d.issues(for: .beginnerGoal, today: today, calendar: cal).isEmpty)
        d.beginnerEventDate = day("2026-12-12")
        #expect(d.issues(for: .beginnerGoal, today: today, calendar: cal).isEmpty)
    }

    @Test func minimumWeeksMirrorsTheBackend() {
        #expect(BeginnerMilestones.minimumWeeks(target: .tenK, currentJogMin: 30) == 9)
        #expect(BeginnerMilestones.minimumWeeks(target: .fiveK, currentJogMin: 0) == 9)
        #expect(BeginnerMilestones.minimumWeeks(target: .tenK, currentJogMin: 0) == 17)
        #expect(BeginnerMilestones.minimumWeeks(target: .tenK, currentJogMin: 10) == 13)
    }

    @Test func weeksUntilCountsMondayAlignedWeeks() {
        #expect(BeginnerMilestones.weeksUntil(event: day("2026-12-12"), start: day("2026-10-05"), calendar: cal) == 10)
        #expect(BeginnerMilestones.weeksUntil(event: day("2026-10-01"), start: day("2026-10-05"), calendar: cal) == nil)
    }

    @Test func previewHasSixRowsFor5kAndNineFor10k() {
        #expect(BeginnerMilestones.preview(for: .fiveK).count == 6)
        #expect(BeginnerMilestones.preview(for: .tenK).count == 9)
    }
}
