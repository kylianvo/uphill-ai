import SwiftUI
import Testing
import UIKit
@testable import UphillAI

/// Whole-tab renders of the Plan screen with the goal-reliable-plans data (journey, coach nudge, week brief).
/// Written only when SCREENSHOT_DIR is set.
@MainActor
struct PlanAuditScreenshots {
    private let outDir = ProcessInfo.processInfo.environment["SCREENSHOT_DIR"]

    private func save<V: View>(_ view: V, name: String, height: CGFloat) {
        guard let outDir else { return }
        let size = CGSize(width: 402, height: height)
        let controller = UIHostingController(rootView: view.frame(width: size.width, height: size.height))
        if ProcessInfo.processInfo.environment["SCREENSHOT_DARK"] != nil { controller.overrideUserInterfaceStyle = .dark }
        let window = UIWindow(frame: CGRect(origin: .zero, size: size))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        controller.view.layoutIfNeeded()
        let format = UIGraphicsImageRendererFormat()
        format.scale = 2
        let img = UIGraphicsImageRenderer(size: size, format: format).image { _ in
            controller.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: true)
        }
        try? img.pngData()?.write(to: URL(fileURLWithPath: "\(outDir)/\(name).png"))
    }

    private func decode<T: Decodable>(_ type: T.Type, _ object: [String: Any]) throws -> T {
        try JSONCoding.decoder.decode(T.self, from: JSONSerialization.data(withJSONObject: object))
    }

    @Test func renderPlanTab() async throws {
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        let now = cal.date(from: DateComponents(year: 2026, month: 10, day: 21, hour: 7))!  // Wednesday of week 5

        let plan = TestData.plan(["id": 7, "race_name": "Vietnam Mountain Marathon 70K", "race_date": "2026-12-12",
                                  "goal_type": "time", "target_time_hours": 11.0, "course_distance_km": 70, "course_elevation_gain_m": 4000, "total_weeks": 12, "current_week": 5,
                                  "start_date": "2026-09-21", "plan_status": "active"])
        func w(_ id: Int, _ week: Int, _ day: String, _ type: String, _ min: Double, _ title: String, _ extra: [String: Any] = [:]) -> Workout {
            TestData.workout(["id": id, "week_number": week, "day_of_week": day, "type": type, "duration_minutes": min,
                              "title": title, "target_zone": "Z2"].merging(extra) { $1 })
        }
        let prev = [w(41, 4, "Tuesday", "Easy Run", 45, "Easy Run", ["is_completed": 1]),
                    w(42, 4, "Thursday", "Tempo", 50, "Tempo", ["is_missed": 1]),
                    w(43, 4, "Saturday", "Long Run", 100, "Long Run", ["is_completed": 1])]
        let cur = [w(51, 5, "Monday", "Rest", 0, "Rest Day"),
                   w(52, 5, "Tuesday", "Easy Run", 50, "Aerobic Easy Run", ["is_completed": 1, "distance_km": 8.0]),
                   w(53, 5, "Wednesday", "Hill Intervals", 60, "Hill Repeats 6×3 min", ["target_zone": "Z4", "elevation_gain_m": 240.0, "is_priority": true]),
                   w(54, 5, "Thursday", "Strength", 40, "Mountain Legs Strength"),
                   w(55, 5, "Friday", "Rest", 0, "Rest Day"),
                   w(56, 5, "Saturday", "Long Run", 140, "Long Trail Run", ["elevation_gain_m": 900.0, "is_priority": true]),
                   w(57, 5, "Sunday", "Recovery", 30, "Recovery Jog", ["target_zone": "Z1"])]

        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(PlanSnapshot(plan: plan, workouts: prev + cur)) }
        service.journeyResult.withLock { $0 = try? decode(PlanJourney.self, [
            "current_week": 5, "total_weeks": 12, "days_to_race": 52,
            "phases": [["name": "Base", "start_week": 1, "end_week": 4], ["name": "Build", "start_week": 5, "end_week": 9],
                       ["name": "Peak", "start_week": 10, "end_week": 10], ["name": "Taper", "start_week": 11, "end_week": 12]],
            "milestones": [["key": "first_recovery_week", "week": 4, "done": true], ["key": "long_run_3h", "week": 7, "done": false]],
            "preferences": ["days_per_week": 5, "long_run_day": "Saturday", "mountain": "ba_den"], "deviations": []]) }
        service.nudgeResult.withLock { $0 = try? decode(CoachNudge.self, [
            "tone": "encourage", "text": "You completed 2/3 sessions last week. Keep this rhythm."]) }
        service.reviewResult.withLock { $0 = .success(try! decode(WeekReview.self, [
            "week_number": 5, "completion_pct": 20, "per_workout": [],
            "narrative": ["ai_this_week_description": "First Build week: hills come in and the long run grows to 2h20."],
            "brief": ["why": "Build starts this week, so the long run grows from 100 to 140 minutes and hill repeats replace tempo. Thursday's missed tempo is not made up; it is folded into Wednesday's hills.",
                      "benefits": ["Hill Repeats: climbing power for the 4,000 m of race gain", "Long Trail Run: time on feet and practising fuel every 30 minutes"],
                      "watch": "If your calves are still sore on Friday, swap Thursday's strength for an easy walk."]])) }

        service.goalResult.withLock { $0 = .success(try! decode(PlanGoal.self, [
            "assessment": ["id": 1, "goals": ["a": 600, "b": 660, "c": 735], "reasoning": [], "missing": [], "engine": "rules"],
            "status": ["state": "on_track", "suggested_mins": NSNull(), "tier": "b"], "target_time_hours": 11.0,
            "path": ["b": "on", "a": "behind", "measured_pct": 2.1, "expected_pct": 2.5, "weeks": 4, "confidence": "medium"],
            "targets": ["long_run_min": 300, "peak_week_km": 75],
            "a_feasibility": ["verdict": "stretch", "capacity_h": 9.5, "needed_h": 10.5, "levers": ["more_days", "mountain_access"], "confidence": "measured"]])) }
        let model = PlanViewModel(service: service, cache: .inMemory(), now: { now }, calendar: cal)
        await model.load()
        model.selectedWeek = 5
        await model.loadWeekBrief()
        await model.loadJourney()
        await model.loadGoal()
        let gen = GenerationCenter(service: FakeGenerationService(), defaults: UserDefaults(suiteName: UUID().uuidString)!)

        let oldLanguage = UserDefaults.standard.string(forKey: AppLanguage.storageKey)
        defer { UserDefaults.standard.set(oldLanguage, forKey: AppLanguage.storageKey) }
        for lang in [AppLanguage.en, .vi] {
            UserDefaults.standard.set(lang.rawValue, forKey: AppLanguage.storageKey)
            let suffix = lang == .en ? "en" : "vi"
            let view = PlanView(model: model, generation: gen, onBuildPlan: {}, onViewProgress: {}).environment(\.locale, lang.locale)
            save(view, name: "plan-first-screen-\(suffix)", height: 874)
            save(SummaryCarousel(model: model, onReview: {}, onAdapt: {}, onGoal: {}).goalProgressCard(model.goalProgress!)
                    .environment(\.locale, lang.locale), name: "goal-progress-card-\(suffix)", height: 260)
            save(PlanView(model: model, generation: gen, onBuildPlan: {}, onViewProgress: {}, initialCoachExpanded: true)
                    .environment(\.locale, lang.locale), name: "plan-coach-review-\(suffix)", height: 1400)
            save(GoalSheet(model: model).environment(\.locale, lang.locale), name: "goal-ladder-\(suffix)", height: 1100)
            save(ChooseAGoalSheet(minutes: 600, feasibility: model.goal?.aFeasibility, onConfirm: {}).environment(\.locale, lang.locale), name: "goal-choose-a-\(suffix)", height: 874)
            save(AdaptWeekSheet(model: model, week: 5).environment(\.locale, lang.locale), name: "adapt-\(suffix)", height: 1600)
        }
    }

    /// Week 1 of a fresh plan: nothing reviewed yet, so the coach card welcomes; the goal card shows target, A/B/C and status.
    @Test func renderWeekOne() async throws {
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        let now = cal.date(from: DateComponents(year: 2026, month: 10, day: 22, hour: 9))!
        let plan = TestData.plan(["id": 131, "race_name": "Vietnam Highlands Trail by UTMB", "race_date": "2027-01-09",
                                  "goal_type": "time", "target_time_hours": 15.75, "course_distance_km": 56, "course_elevation_gain_m": 2800,
                                  "total_weeks": 12, "current_week": 1, "start_date": "2026-10-19", "plan_status": "active"])
        func w(_ id: Int, _ day: String, _ type: String, _ min: Double, _ title: String, _ extra: [String: Any] = [:]) -> Workout {
            TestData.workout(["id": id, "week_number": 1, "day_of_week": day, "type": type, "duration_minutes": min,
                              "title": title, "target_zone": "Z2"].merging(extra) { $1 })
        }
        let week = [w(1, "Monday", "Rest", 0, "Rest Day"), w(2, "Thursday", "Easy Run", 50, "Aerobic Easy Run"),
                    w(3, "Saturday", "Long Run", 150, "Trail Long Run", ["is_priority": true]), w(4, "Sunday", "Easy Run", 60, "Easy Run")]
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(PlanSnapshot(plan: plan, workouts: week)) }
        service.goalResult.withLock { $0 = .success(try! decode(PlanGoal.self, [
            "assessment": ["id": 1, "goals": ["a": 870, "b": 945, "c": 1050], "reasoning": [], "missing": [], "engine": "rules"],
            "status": ["state": "ahead", "suggested_mins": NSNull()], "target_time_hours": 15.75,
            "targets": ["long_run_min": 214, "peak_week_km": 120]])) }
        let model = PlanViewModel(service: service, cache: .inMemory(), now: { now }, calendar: cal)
        await model.load()
        model.selectedWeek = 1
        await model.loadGoal()

        let oldLanguage = UserDefaults.standard.string(forKey: AppLanguage.storageKey)
        defer { UserDefaults.standard.set(oldLanguage, forKey: AppLanguage.storageKey) }
        for lang in [AppLanguage.en, .vi] {
            UserDefaults.standard.set(lang.rawValue, forKey: AppLanguage.storageKey)
            let suffix = lang == .en ? "en" : "vi"
            save(SummaryCarousel(model: model, onReview: {}, onAdapt: {}, onGoal: {}).goalProgressCard(model.goalProgress!)
                    .environment(\.locale, lang.locale), name: "week1-goal-card-\(suffix)", height: 260)
            save(CoachReviewCard(model: model, onOpenReview: {}, initialExpanded: true)
                    .padding().environment(\.locale, lang.locale), name: "week1-coach-welcome-\(suffix)", height: 420)
        }
    }
}
