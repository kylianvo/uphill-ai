import Foundation
import Testing
@testable import UphillAI

struct PlanSetupDraftTests {
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

    private func raceDraft() -> PlanSetupDraft {
        var d = PlanSetupDraft(prefill: nil, today: today, calendar: cal)
        d.goal = .race
        d.raceName = "  Vietnam Mountain Marathon 42K "
        d.raceDate = day("2026-12-19")
        d.distanceKm = 42
        d.elevationGainM = 2400
        d.raceGoal = .time
        d.targetMinutes = 390
        d.daysPerWeek = 4
        d.preferredDays = [.tuesday, .thursday, .saturday, .sunday]
        d.longRunDay = .saturday
        d.currentWeeklyKm = 30
        d.environment = .hilly
        return d
    }

    @Test func stepsDependOnGoal() {
        #expect(SetupStep.steps(for: nil, includeAboutYou: true) == [.goal])
        #expect(SetupStep.steps(for: .race, includeAboutYou: true) == [.goal, .details, .schedule, .aboutYou, .review])
        #expect(SetupStep.steps(for: .startRunning, includeAboutYou: true) == [.goal, .schedule, .aboutYou, .review])
        #expect(SetupStep.steps(for: .returning, includeAboutYou: false) == [.goal, .details, .schedule, .review])
    }

    @Test func defaultsFromPrefillAndToday() throws {
        let user = try Fixture.decode(User.self, "auth_me.json")
        let d = PlanSetupDraft(prefill: user, today: today, calendar: cal)
        #expect(d.startDate == today)
        #expect(d.preferredDays.count == d.daysPerWeek)
        #expect(d.preferredDays.contains(d.longRunDay))
    }

    @Test func validRaceDraftHasNoIssues() {
        let d = raceDraft()
        for step in [SetupStep.goal, .details, .schedule, .aboutYou, .review] {
            #expect(d.issues(for: step, today: today, calendar: cal).isEmpty, "step \(step)")
        }
    }

    @Test func raceDetailIssues() {
        var d = raceDraft()
        d.raceName = "   "
        d.raceDate = day("2026-10-15")
        d.distanceKm = 0
        d.targetMinutes = nil
        let fields = d.issues(for: .details, today: today, calendar: cal).map(\.field)
        #expect(fields == [.raceName, .raceDate, .distance, .targetTime])
        #expect(d.issues(for: .details, today: today, calendar: cal).first?.message == "Add the race name.")
    }

    @Test func distanceGoalNeedsNoName() {
        var d = raceDraft()
        d.goal = .distance
        d.raceName = ""
        #expect(d.issues(for: .details, today: today, calendar: cal).isEmpty)
    }

    @Test func scheduleIssues() {
        var d = raceDraft()
        d.daysPerWeek = 5
        d.longRunDay = .monday
        d.currentWeeklyKm = 300
        d.startDate = day("2026-10-06")
        let issues = d.issues(for: .schedule, today: today, calendar: cal)
        #expect(issues.map(\.field) == [.preferredDays, .longRunDay, .weeklyKm, .startDate])
        #expect(issues[0].message == "Pick 5 days to match 5 runs a week.")
    }

    @Test func returnAndRecoveryDetails() {
        var d = PlanSetupDraft(prefill: nil, today: today, calendar: cal)
        d.goal = .returning
        #expect(d.issues(for: .details, today: today, calendar: cal).map(\.field) == [.timeAway, .fitnessFeel])
        d.goal = .recovery
        d.daysSinceRace = 90
        #expect(d.issues(for: .details, today: today, calendar: cal).map(\.field) == [.raceCompleted, .daysSinceRace, .recoveryFeel])
    }

    @Test func aboutYouRanges() {
        var d = raceDraft()
        d.heightCm = 90
        d.maxHr = 250
        #expect(d.issues(for: .aboutYou, today: today, calendar: cal).map(\.field) == [.height, .maxHr])
    }

    @Test func onboardingBodyForTimedRace() throws {
        var d = raceDraft()
        d.birthDate = day("1991-04-02")
        d.injuryHistory = "  "
        let body = try encoded(d.onboardingBody(skipPlan: false, calendar: cal))
        #expect(body["goal_type"] as? String == "race")
        #expect(body["race_goal"] as? String == "time")
        #expect(body["expected_finish_time"] as? String == "6:30")
        #expect(body["race_name"] as? String == "Vietnam Mountain Marathon 42K")
        #expect(body["race_date"] as? String == "2026-12-19")
        #expect(body["course_distance_km"] as? Double == 42)
        #expect(body["preferred_run_days"] as? [String] == ["Tuesday", "Thursday", "Saturday", "Sunday"])
        #expect(body["long_run_day"] as? String == "Saturday")
        #expect(body["training_environment"] as? String == "hilly")
        #expect(body["plan_start_date"] as? String == "2026-10-07")
        #expect(body["dob"] as? String == "1991-04-02")
        #expect(body["skip_plan"] as? Bool == false)
        #expect(body["lang"] as? String == "en")
        #expect(body["injury_history"] == nil)
        #expect(body["time_away"] == nil)
    }

    @Test func planBodyMapsRaceGoalToGoalType() throws {
        let body = try encoded(raceDraft().planBody(calendar: cal))
        #expect(body["goal_type"] as? String == "time")
        #expect(body["target_time_hours"] as? Double == 6.5)
        #expect(body["preferred_days"] as? [String] == ["Tuesday", "Thursday", "Saturday", "Sunday"])
        #expect(body["current_weekly_km"] as? Double == 30)
        #expect(body["terrain"] as? String == "trail")
    }

    @Test func planBodyForStartRunningOmitsRaceFields() throws {
        var d = raceDraft()
        d.goal = .startRunning
        let body = try encoded(d.planBody(calendar: cal))
        #expect(body["goal_type"] as? String == "start_running")
        #expect(body["race_name"] == nil)
        #expect(body["race_date"] == nil)
        #expect(body["target_time_hours"] == nil)
    }

    @Test func distanceGoalGetsGeneratedName() throws {
        var d = raceDraft()
        d.goal = .distance
        d.raceName = ""
        d.distanceKm = 21.1
        d.raceGoal = .finish
        let body = try encoded(d.planBody(calendar: cal))
        #expect(body["race_name"] as? String == "21.1 km goal")
        #expect(body["goal_type"] as? String == "finish")
    }

    @Test func summaryLinesDescribeInputs() {
        #expect(raceDraft().summaryLines == [
            "Vietnam Mountain Marathon 42K on Sat 19 Dec",
            "Target time 6:30",
            "4 runs a week, long run on Saturday",
            "Starting from 30 km a week",
        ])
    }
}
