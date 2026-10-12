import SwiftUI
import Testing
import UIKit
@testable import UphillAI

/// Opt-in simulator captures of the real setup and weekly-action views with controlled test data.
@MainActor
struct SetupFlowScreenshots {
    private let outDir = ProcessInfo.processInfo.environment["SCREENSHOT_DIR"]

    private func capture<V: View>(_ view: V, name: String, size: CGSize = CGSize(width: 393, height: 852)) async throws {
        guard let outDir else { return }
        let controller = UIHostingController(rootView: view)
        let window = UIWindow(frame: CGRect(origin: .zero, size: size))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        defer { window.isHidden = true }
        controller.view.layoutIfNeeded()
        try await Task.sleep(for: .milliseconds(200))
        let image = UIGraphicsImageRenderer(size: size).image { _ in
            controller.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: true)
        }
        let data = try #require(image.pngData())
        try data.write(to: URL(fileURLWithPath: outDir).appendingPathComponent(name + ".png"))
    }

    @Test func renderSetupAndWeeklyActions() async throws {
        guard outDir != nil else { return }
        let oldLanguage = UserDefaults.standard.string(forKey: AppLanguage.storageKey)
        defer { UserDefaults.standard.set(oldLanguage, forKey: AppLanguage.storageKey) }
        let service = FakeGenerationService()
        let generation = GenerationCenter(service: service, defaults: UserDefaults(suiteName: UUID().uuidString)!)
        let session = SessionStore(tokenStore: InMemoryTokenStore())
        let base = StubURLProtocol.register { _ in (200, json([:])) }
        let client = APIClient(baseURL: { base }, tokenStore: InMemoryTokenStore(), session: StubURLProtocol.session())
        let setup = PlanSetupViewModel(mode: .onboarding, user: nil, service: service, generation: generation, session: session,
                                       goalEstimateService: GoalEstimateService(client: client), raceHistoryService: RaceHistoryService(client: client))
        setup.selectGoal(.race)
        setup.selectRace(RaceMatch(raceName: "Vietnam Highlands Trail by UTMB", distanceLabel: nil, distanceKm: nil, elevationGainM: nil,
                                  distances: [RaceDistance(label: "20 km", distanceKm: 20, elevationGainM: 1000),
                                              RaceDistance(label: "50 km", distanceKm: 55.4, elevationGainM: 3200),
                                              RaceDistance(label: "100 km", distanceKm: 104, elevationGainM: 5533)]))
        setup.pickDistance(setup.raceDistances[1])
        setup.draft.raceDate = Calendar.current.date(byAdding: .month, value: 3, to: Date())
        setup.draft.environment = .hilly
        for language in [AppLanguage.en, .vi] {
            UserDefaults.standard.set(language.rawValue, forKey: AppLanguage.storageKey)
            for (step, name) in [(SetupStep.details, "race"), (.raceGoal, "goal"), (.schedule, "week"), (.venues, "venues"), (.body, "body"), (.raceHistory, "history"), (.review, "review")] {
                setup.jump(to: step)
                try await capture(PlanSetupFlow(model: setup, onClose: {}).environment(\.locale, language.locale), name: "setup-\(name)-\(language.rawValue)")
            }
            setup.jump(to: .schedule)
            try await capture(PlanSetupFlow(model: setup, onClose: {}).environment(\.locale, language.locale).dynamicTypeSize(.accessibility3), name: "setup-week-large-\(language.rawValue)", size: CGSize(width: 375, height: 812))
        }
        UserDefaults.standard.set("en", forKey: AppLanguage.storageKey)
        let plan = TestData.plan(["start_date": PlanCalendar.ymd(Date()), "total_weeks": 12,
                                  "days_per_week": 4, "preferred_run_days": "[\"Tuesday\",\"Thursday\",\"Saturday\",\"Sunday\"]", "long_run_day": "Saturday"])
        let snapshot = PlanSnapshot(plan: plan, workouts: [TestData.workout(["week_number": 1, "type": "Easy Run"])])
        let model = PlanViewModel(service: FakePlanService(), cache: .inMemory())
        model.adopt(snapshot)
        let offer = NextWeekOffer(blockNumber: 2, weekStart: 2, weekEnd: 2, previousCompletionPct: 75, unlocked: true)
        for language in [AppLanguage.en, .vi] {
            UserDefaults.standard.set(language.rawValue, forKey: AppLanguage.storageKey)
            try await capture(NextWeekSheet(model: model, offer: offer).environment(\.locale, language.locale), name: "next-week-\(language.rawValue)")
            try await capture(AdaptWeekSheet(model: model, week: 1).environment(\.locale, language.locale), name: "adapt-week-\(language.rawValue)")
            try await capture(ScrollView { ScheduleEditor(draft: .constant(ScheduleDraft(plan: plan)), workouts: []).padding() }.environment(\.locale, language.locale), name: "weekly-schedule-\(language.rawValue)", size: CGSize(width: 393, height: 1500))
        }
    }
}
