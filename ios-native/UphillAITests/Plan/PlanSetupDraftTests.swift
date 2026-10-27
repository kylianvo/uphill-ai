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

    @Test func mountainPreferencesReachBothCreationRequests() throws {
        var draft = raceDraft()
        draft.trainingMountain = "nui_dinh"
        draft.mountainMinMinutes = 180
        let plan = try encoded(draft.planBody(calendar: cal))
        let onboarding = try encoded(draft.onboardingBody(skipPlan: false, calendar: cal))
        for json in [plan, onboarding] {
            #expect(json["training_mountain"] as? String == "nui_dinh")
            #expect(json["mountain_min_minutes"] as? Int == 180)
        }
    }

    @Test func longDayFormatReachesBothCreationRequests() throws {
        var draft = raceDraft()
        draft.longDayFormat = .backToBack
        for json in [try encoded(draft.planBody(calendar: cal)), try encoded(draft.onboardingBody(skipPlan: false, calendar: cal))] {
            #expect(json["long_day_format"] as? String == "back_to_back")
        }
    }

    @Test func decodesRecordedRaceSearch() throws {
        let response = try Fixture.decode(RaceMatchResponse.self, "race_match.json")
        #expect(!response.matched)
        #expect(response.match == nil)
    }

    @Test func onlyRequiredAnswersBuildBothBodies() throws {
        var d = PlanSetupDraft(prefill: nil, today: today, calendar: cal)
        d.goal = .startRunning
        d.maxHr = 190
        d.heightCm = 90
        for step in SetupStep.steps(for: .startRunning, includeProfile: true) {
            #expect(d.issues(for: step, today: today, calendar: cal).isEmpty)
        }
        let onboarding = try encoded(d.onboardingBody(skipPlan: false, calendar: cal))
        let plan = try encoded(d.planBody(calendar: cal))
        for body in [onboarding, plan] {
            #expect(body["days_per_week"] as? Int == 4)
            #expect(body["current_weekly_km"] as? Double == 30)
            #expect(body["training_environment"] as? String == "flat")
            #expect(body["has_gym_access"] as? Bool == false)
            #expect(body["mountain_days"] as? [String] == [])
            #expect(body["stair_access"] as? Bool == false)
        }
    }

    @Test func stepsDependOnGoal() {
        #expect(SetupStep.steps(for: nil, includeProfile: true) == [.goal])
        #expect(SetupStep.steps(for: .race, includeProfile: true)
                == [.goal, .details, .raceDate, .raceGoal, .watch, .schedule, .venues, .body, .trainingZones, .raceHistory, .startDate, .review])
        #expect(SetupStep.steps(for: .race, includeProfile: false)
                == [.goal, .details, .raceDate, .raceGoal, .schedule, .venues, .startDate, .review])
        #expect(SetupStep.steps(for: .startRunning, includeProfile: true) == [.goal, .beginnerGoal, .watch, .schedule, .venues, .body, .trainingZones, .raceHistory, .startDate, .review])
        #expect(SetupStep.steps(for: .returning, includeProfile: false) == [.goal, .details, .fitnessFeel, .schedule, .venues, .startDate, .review])
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
        for step in [SetupStep.goal, .details, .raceGoal, .schedule, .venues, .body, .review] {
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
        #expect(fields == [.raceName, .distance])
        #expect(d.issues(for: .raceDate, today: today, calendar: cal).map(\.field) == [.raceDate])
        #expect(d.issues(for: .details, today: today, calendar: cal).first?.message == "Add the race name.")
    }

    @Test func startedTuneUpRaceNeedsNameDistanceAndEarlierDate() {
        var d = raceDraft()
        let ok = SetupBRace(name: "Ta Xua", date: day("2026-11-08"), distanceKm: 25)
        d.bRaces = [SetupBRace(name: " ", date: day("2026-11-08"), distanceKm: nil), ok]  // a blank row is ignored
        #expect(d.issues(for: .raceDate, today: today, calendar: cal).isEmpty)
        for bad in [SetupBRace(name: "Ta Xua", date: day("2026-11-08"), distanceKm: nil),
                    SetupBRace(name: "", date: day("2026-11-08"), distanceKm: 25),
                    SetupBRace(name: "Ta Xua", date: day("2026-12-19"), distanceKm: 25)] {
            d.bRaces = [ok, bad]
            let issues = d.issues(for: .raceDate, today: today, calendar: cal)
            #expect(issues.map(\.field) == [.bRaces])
            #expect(issues.first?.message == "Add the name, distance and a date before your goal race, or remove it.")
        }
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
        #expect(issues.map(\.field) == [.preferredDays, .weeklyKm])
        #expect(issues.first?.message == "Pick 5 run days.")
        #expect(d.issues(for: .startDate, today: today, calendar: cal).map(\.field) == [.startDate])
    }

    @Test func returnAndRecoveryDetails() {
        var d = PlanSetupDraft(prefill: nil, today: today, calendar: cal)
        d.goal = .returning
        #expect(d.issues(for: .details, today: today, calendar: cal).map(\.field) == [])
        d.goal = .recovery
        d.daysSinceRace = 90
        #expect(d.issues(for: .details, today: today, calendar: cal).map(\.field) == [])
    }

    @Test func timeGoalNeedsTarget() {
        var d = raceDraft()
        d.raceGoal = .time
        d.targetMinutes = nil
        #expect(d.issues(for: .raceGoal, today: today, calendar: cal).map(\.field) == [.targetTime])
        d.targetMinutes = 330
        #expect(d.issues(for: .raceGoal, today: today, calendar: cal).isEmpty)
    }

    @Test func doubleSessionsAndTreadmillReachBothBodies() throws {
        var d = raceDraft()
        d.doubleSessionDays = [.tuesday, .monday]
        d.useTreadmill = true
        d.treadmillMaxIncline = 20
        let plan = try encoded(d.planBody(calendar: cal))
        let onboarding = try encoded(d.onboardingBody(skipPlan: false, calendar: cal))
        let expectedDoubles = Weekday.allCases.filter { [.tuesday, .monday].contains($0) && d.preferredDays.contains($0) }.map(\.rawValue)
        #expect(plan["double_session_days"] as? [String] == expectedDoubles)
        #expect(onboarding["double_session_days"] as? [String] == expectedDoubles)
        #expect(plan["use_treadmill"] as? Bool == true)
        #expect(plan["treadmill_max_incline"] as? Int == 20)
        #expect(onboarding["treadmill_max_incline"] as? Int == 20)
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
            "42 km · 2,400 m D+",
            "Target time 6:30",
            "4 runs a week, long run on Saturday",
            "Starting from 30 km a week",
            "Terrain near home: Hilly",
        ])
    }

    @Test func onboardingKeepsTreadmillSeparateFromGym() throws {
        var d = raceDraft()
        d.hasGymAccess = true
        d.useTreadmill = false
        #expect(try encoded(d.onboardingBody(skipPlan: false, calendar: cal))["use_treadmill"] as? Bool == false)
    }

    @Test func trainingVenuesReachBothBodiesInWeekdayOrder() throws {
        var d = PlanSetupDraft(prefill: nil, today: today, calendar: cal)
        d.goal = .startRunning
        d.mountainDays = [.sunday, .saturday]
        d.stairAccess = true
        for body in [try encoded(d.onboardingBody(skipPlan: false, calendar: cal)), try encoded(d.planBody(calendar: cal))] {
            #expect(body["mountain_days"] as? [String] == ["Saturday", "Sunday"])
            #expect(body["stair_access"] as? Bool == true)
        }
    }
    @Test func trainingZonesAreOptionalAndEncodeKnownValues() throws {
        var d = raceDraft()
        #expect(d.issues(for: .trainingZones, today: today, calendar: cal).isEmpty)
        var body = try encoded(d.onboardingBody(skipPlan: false, calendar: cal))
        #expect(body["aet_hr"] == nil && body["threshold_pace"] == nil)
        d.aetHr = 145; d.antHr = 170; d.thresholdSource = "field"
        d.zone2PaceMin = " 6:40 "; d.zone2PaceMax = "5:50"; d.thresholdPace = "4:45"
        body = try encoded(d.onboardingBody(skipPlan: false, calendar: cal))
        #expect(body["aet_hr"] as? Int == 145)
        #expect(body["ant_hr"] as? Int == 170)
        #expect(body["threshold_source"] as? String == "field")
        #expect(body["zone2_pace_min"] as? String == "6:40")
        #expect(body["threshold_pace"] as? String == "4:45")
        d.antHr = nil
        body = try encoded(d.onboardingBody(skipPlan: false, calendar: cal))
        #expect(body["threshold_source"] as? String == "unknown")
    }

    @Test func trainingZonesRejectMalformedAndReversedValues() {
        var d = raceDraft()
        d.aetHr = 175; d.antHr = 160
        #expect(d.trainingZonesError != nil)
        d.aetHr = 145; d.antHr = 170
        d.zone2PaceMin = "6:99"
        #expect(d.trainingZonesError != nil)
        d.zone2PaceMin = "5:30"; d.zone2PaceMax = "6:30"
        #expect(d.trainingZonesError != nil)
        d.zone2PaceMin = "6:30"; d.zone2PaceMax = "5:30"; d.thresholdPace = "6:00"
        #expect(d.trainingZonesError != nil)
        d.thresholdPace = "4:45"
        #expect(d.trainingZonesError == nil)
    }

    @Test func trainingZonesPrefillFromSavedProfile() throws {
        let fixture = try Fixture.data("auth_me.json")
        var values = try #require(JSONSerialization.jsonObject(with: fixture) as? [String: Any])
        values["aet_hr"] = 145; values["ant_hr"] = 170
        values["zone2_pace_min"] = "6:40"; values["zone2_pace_max"] = "5:50"; values["threshold_pace"] = "4:45"
        let user = try JSONCoding.decoder.decode(User.self, from: JSONSerialization.data(withJSONObject: values))
        let d = PlanSetupDraft(prefill: user, today: today, calendar: cal)
        #expect(d.aetHr == 145 && d.antHr == 170)
        #expect(d.zone2PaceMin == "6:40" && d.thresholdPace == "4:45")
    }

    @Test func appDefaultsAreNotPrefilledAsMeasurements() throws {
        var values = try #require(JSONSerialization.jsonObject(with: Fixture.data("auth_me.json")) as? [String: Any])
        values["aet_hr"] = 135; values["ant_hr"] = 165
        values["zone2_pace_min"] = "6:30"; values["zone2_pace_max"] = "5:45"
        values["field_sources"] = Dictionary(uniqueKeysWithValues:
            ["max_hr", "resting_hr", "aet_hr", "ant_hr", "zone2_pace_min", "zone2_pace_max", "threshold_pace"].map { ($0, ["source": "default"]) })
        let user = try JSONCoding.decoder.decode(User.self, from: JSONSerialization.data(withJSONObject: values))
        let d = PlanSetupDraft(prefill: user, today: today, calendar: cal)
        #expect(d.aetHr == nil && d.antHr == nil && d.maxHr == nil && d.restingHr == nil)
        #expect(d.zone2PaceMin.isEmpty && d.zone2PaceMax.isEmpty)
        #expect(d.needsZoneEstimateWarning)
    }

    @Test func shortRaceTargetsAndEventStartWindow() {
        var d = raceDraft()
        d.targetMinutes = 15
        #expect(d.issues(for: .raceGoal, today: today, calendar: cal).isEmpty)
        d.targetMinutes = 0
        #expect(!d.issues(for: .raceGoal, today: today, calendar: cal).isEmpty)
        d.raceDate = day("2026-10-21")
        #expect(d.latestStartDate(today: today, calendar: cal) == today)
        d.startDate = day("2026-10-08")
        #expect(!d.issues(for: .startDate, today: today, calendar: cal).isEmpty)
    }

    @Test func missingVolumeMustBeAnsweredAndDistanceDoesNotReuseRaceName() {
        var d = raceDraft()
        d.currentWeeklyKm = nil
        #expect(!d.issues(for: .schedule, today: today, calendar: cal).isEmpty)
        d.currentWeeklyKm = 0
        #expect(d.issues(for: .schedule, today: today, calendar: cal).isEmpty)
        d.goal = .distance
        d.distanceKm = 21
        #expect(d.planBody(calendar: cal).raceName == "21 km goal")
    }

    @Test func longRunOnlyOffersTrailDaysWhenThereAreAny() {
        let run: [Weekday] = [.tuesday, .thursday, .saturday, .sunday]
        #expect(Weekday.longRunChoices(runDays: run, trailDays: [.saturday]) == [.saturday])
        #expect(Weekday.longRunChoices(runDays: run, trailDays: [.saturday, .sunday]) == [.saturday, .sunday])
        #expect(Weekday.longRunChoices(runDays: run, trailDays: [.monday]) == run)
        #expect(Weekday.longRunChoices(runDays: run, trailDays: []) == run)
    }
}
