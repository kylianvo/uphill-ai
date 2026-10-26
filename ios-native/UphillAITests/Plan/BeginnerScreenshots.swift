import SwiftUI
import Testing
import UIKit
@testable import UphillAI

/// First 5K / First 10K screens: setup goal and review, plan header and path card, the list and a celebration.
/// Written only when SCREENSHOT_DIR is set.
@MainActor
@Suite(.serialized)
struct BeginnerScreenshots {
    private let outDir = ProcessInfo.processInfo.environment["SCREENSHOT_DIR"]

    private func save<V: View>(_ view: V, name: String, height: CGFloat) async throws {
        guard let outDir else { return }
        let size = CGSize(width: 402, height: height)
        let controller = UIHostingController(rootView: view.frame(width: size.width, height: size.height))
        let window = UIWindow(frame: CGRect(origin: .zero, size: size))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        defer { window.isHidden = true }
        controller.view.layoutIfNeeded()
        try await Task.sleep(for: .milliseconds(200))
        let img = UIGraphicsImageRenderer(size: size).image { _ in
            controller.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: true)
        }
        try img.pngData()?.write(to: URL(fileURLWithPath: "\(outDir)/\(name).png"))
    }

    private func item(_ key: String, _ kind: String, _ threshold: Double, _ weeks: [Int], at: String? = nil, source: String? = nil) -> [String: Any] {
        ["key": key, "kind": kind, "threshold": threshold, "stage": "A", "typical_weeks": weeks,
         "achieved_at": at as Any? ?? NSNull(), "source": source as Any? ?? NSNull()]
    }

    @Test func renderBeginnerScreens() async throws {
        guard outDir != nil else { return }
        let oldLanguage = UserDefaults.standard.string(forKey: AppLanguage.storageKey)
        defer { UserDefaults.standard.set(oldLanguage, forKey: AppLanguage.storageKey) }

        // Setup: goal step and review with the path preview.
        let genService = FakeGenerationService()
        let generation = GenerationCenter(service: genService, defaults: UserDefaults(suiteName: UUID().uuidString)!)
        let base = StubURLProtocol.register { _ in (200, json([:])) }
        let client = APIClient(baseURL: { base }, tokenStore: InMemoryTokenStore(), session: StubURLProtocol.session())
        let setup = PlanSetupViewModel(mode: .onboarding, user: nil, service: genService, generation: generation,
                                       session: SessionStore(tokenStore: InMemoryTokenStore()),
                                       goalEstimateService: GoalEstimateService(client: client), raceHistoryService: RaceHistoryService(client: client))
        setup.selectGoal(.startRunning)
        setup.draft.milestoneTarget = .tenK
        setup.draft.currentJogMin = 3
        setup.draft.hasBeginnerEvent = true
        setup.draft.beginnerEventName = "Hanoi 10K"
        setup.draft.beginnerEventDate = Calendar.current.date(byAdding: .weekOfYear, value: 10, to: Date())

        // Plan: a First 5K plan two milestones in, with the latest one not yet celebrated.
        let milestones: [String: Any] = ["target": "5k", "has_event": false, "next_key": "jog_10", "items": [
            item("first_session", "sessions", 1, [1, 1], at: "2026-10-06T07:00:00+00:00", source: "auto"),
            item("jog_5", "jog_min", 5, [3, 5], at: "2026-10-19T07:00:00+00:00", source: "auto"),
            item("jog_10", "jog_min", 10, [4, 6]), item("jog_20", "jog_min", 20, [5, 8]),
            item("jog_30", "jog_min", 30, [7, 10]), item("first_5k", "distance_km", 5, [9, 12])]]
        let plan = TestData.plan(["id": 5, "race_name": "First 5K", "race_date": "2026-12-21", "goal_type": "start_running",
                                  "milestone_target": "5k", "has_target_event": false, "start_date": "2026-10-05",
                                  "total_weeks": 12, "current_week": 3, "beginner_milestones": milestones])
        func w(_ id: Int, _ day: String, _ type: String, _ min: Double, _ title: String) -> Workout {
            TestData.workout(["id": id, "week_number": 3, "day_of_week": day, "type": type, "duration_minutes": min, "title": title, "target_zone": "Z1"])
        }
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(PlanSnapshot(plan: plan, workouts: [
            w(1, "Tuesday", "Walk/Run", 30, "Run 3 min / walk 2 min × 6"), w(2, "Thursday", "Walk/Run", 30, "Run 4 min / walk 2 min × 5"),
            w(3, "Saturday", "Walk/Run", 35, "Run 5 min / walk 2 min × 5")])) }
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        let now = cal.date(from: DateComponents(year: 2026, month: 10, day: 20, hour: 7))!
        UserDefaults.standard.removeObject(forKey: "milestonesSeen.5")
        let model = PlanViewModel(service: service, cache: .inMemory(), now: { now }, calendar: cal)
        await model.load()
        model.selectedWeek = 3
        let gen = GenerationCenter(service: FakeGenerationService(), defaults: UserDefaults(suiteName: UUID().uuidString)!)
        let ms = try #require(model.beginnerMilestones)
        let reached = try #require(ms.items.first { $0.key == "jog_5" })
        let finish = try #require(ms.items.first { $0.key == "first_5k" })

        for lang in [AppLanguage.en, .vi] {
            UserDefaults.standard.set(lang.rawValue, forKey: AppLanguage.storageKey)
            let s = lang.rawValue
            setup.jump(to: .beginnerGoal)
            try await save(PlanSetupFlow(model: setup, onClose: {}).environment(\.locale, lang.locale), name: "beginner-setup-goal-\(s)", height: 1300)
            setup.jump(to: .review)
            try await save(PlanSetupFlow(model: setup, onClose: {}).environment(\.locale, lang.locale), name: "beginner-setup-review-\(s)", height: 1800)
            try await save(PlanView(model: model, generation: gen, onBuildPlan: {}, onViewProgress: {}).environment(\.locale, lang.locale),
                           name: "beginner-plan-\(s)", height: 1100)
            try await save(MilestonePathCard(model: model).padding().environment(\.locale, lang.locale), name: "beginner-path-card-\(s)", height: 340)
            try await save(MilestoneListSheet(model: model).environment(\.locale, lang.locale), name: "beginner-path-list-\(s)", height: 874)
            try await save(MilestoneCelebrationSheet(item: reached, next: ms.next, targetTitle: ms.targetTitle, canUpgrade: false, onUpgrade: {})
                .environment(\.locale, lang.locale), name: "beginner-celebrate-\(s)", height: 700)
            try await save(MilestoneCelebrationSheet(item: finish, next: nil, targetTitle: ms.targetTitle, canUpgrade: true, onUpgrade: {})
                .environment(\.locale, lang.locale), name: "beginner-celebrate-5k-\(s)", height: 700)
        }
    }
}
