import SwiftUI
import Testing
import UIKit
@testable import UphillAI

/// Opt-in simulator captures of the real setup and weekly-action views with controlled test data.
@MainActor
@Suite(.serialized)
struct SetupFlowScreenshots {
    private let outDir = ProcessInfo.processInfo.environment["SCREENSHOT_DIR"]

    private func capture<V: View>(_ view: V, name: String, size: CGSize = CGSize(width: 393, height: 852)) async throws {
        guard let outDir else { return }
        let controller = UIHostingController(rootView: view)
        // SCREENSHOT_DARK=1 renders the same screens in dark mode.
        if ProcessInfo.processInfo.environment["SCREENSHOT_DARK"] != nil { controller.overrideUserInterfaceStyle = .dark }
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

    @Test func renderWatchStepAndChecklist() async throws {
        guard outDir != nil else { return }
        let oldLanguage = UserDefaults.standard.string(forKey: AppLanguage.storageKey)
        let oldSnooze = UserDefaults.standard.object(forKey: SharpenChecklistCard.snoozeKey)
        UserDefaults.standard.removeObject(forKey: SharpenChecklistCard.snoozeKey)
        defer {
            UserDefaults.standard.set(oldLanguage, forKey: AppLanguage.storageKey)
            UserDefaults.standard.set(oldSnooze, forKey: SharpenChecklistCard.snoozeKey)
        }
        let user = try Fixture.decode(User.self, "auth_me.json")
        for language in [AppLanguage.en, .vi] {
            UserDefaults.standard.set(language.rawValue, forKey: AppLanguage.storageKey)
            for connected in [false, true] {
                let watch = ScrollView {
                    VStack(alignment: .leading, spacing: UH.Space.section) {
                        Text("Connect your watch").font(UH.TextStyle.screenTitle)
                        WatchChannelsList(connected: connected, available: true, healthConnected: false, healthAvailable: true,
                                          connect: { nil }, connectHealth: { nil },
                                          garminConnected: connected, garminAvailable: true, connectGarmin: { nil })
                    }
                    .padding(UH.Space.section)
                }
                .background(UH.Palette.surface)
                .environment(\.locale, language.locale)
                try await capture(watch, name: "watch-step-\(connected ? "connected" : "new")-\(language.rawValue)")
            }
            let card = ScrollView {
                SharpenChecklistCard(user: user, corosConnected: true, raceHistoryLinked: false, onOpen: { _ in })
                    .padding(UH.Space.regular)
            }
            .background(UH.Palette.surface)
            .environment(\.locale, language.locale)
            try await capture(card, name: "plan-checklist-\(language.rawValue)")
        }
    }

    @Test func renderEffortColorBar() async throws {
        guard outDir != nil else { return }
        let oldLanguage = UserDefaults.standard.string(forKey: AppLanguage.storageKey)
        defer { UserDefaults.standard.set(oldLanguage, forKey: AppLanguage.storageKey) }
        for language in [AppLanguage.en, .vi] {
            UserDefaults.standard.set(language.rawValue, forKey: AppLanguage.storageKey)
            let states = VStack(alignment: .leading, spacing: UH.Space.section) {
                Text("Overall effort").font(UH.TextStyle.sectionTitle)
                EffortSelector(selection: .constant(nil), identifier: "preview.effort")
                ForEach(WorkoutFeeling.allCases) { effort in
                    EffortSelector(selection: .constant(effort.rpe), identifier: "preview.effort")
                }
                Spacer()
            }
            .padding(UH.Space.section)
            .background(UH.Palette.surface)
            .environment(\.locale, language.locale)
            try await capture(states, name: "effort-color-states-\(language.rawValue)", size: CGSize(width: 375, height: 900))
            let large = VStack(alignment: .leading, spacing: UH.Space.regular) {
                Text("Overall effort").font(UH.TextStyle.sectionTitle)
                EffortSelector(selection: .constant(8), identifier: "preview.effort")
                Spacer()
            }
            .padding(UH.Space.section)
            .background(UH.Palette.surface)
            .environment(\.locale, language.locale)
            .dynamicTypeSize(.accessibility3)
            try await capture(large, name: "effort-color-large-\(language.rawValue)", size: CGSize(width: 375, height: 1100))
        }
    }

    @Test func renderOnboardingTrainingZones() async throws {
        guard outDir != nil else { return }
        let oldLanguage = UserDefaults.standard.string(forKey: AppLanguage.storageKey)
        defer { UserDefaults.standard.set(oldLanguage, forKey: AppLanguage.storageKey) }
        let service = FakeGenerationService()
        let setup = PlanSetupViewModel(mode: .onboarding, user: nil, service: service,
            generation: GenerationCenter(service: service, defaults: UserDefaults(suiteName: UUID().uuidString)!),
            session: SessionStore(tokenStore: InMemoryTokenStore()))
        setup.selectGoal(.race)
        setup.jump(to: .trainingZones)
        for language in [AppLanguage.en, .vi] {
            UserDefaults.standard.set(language.rawValue, forKey: AppLanguage.storageKey)
            try await capture(PlanSetupFlow(model: setup, onClose: {}).environment(\.locale, language.locale),
                              name: "training-zones-empty-\(language.rawValue)", size: CGSize(width: 393, height: 1400))
            setup.draft.maxHr = 190; setup.draft.restingHr = 55
            setup.draft.aetHr = 145; setup.draft.antHr = 170; setup.draft.thresholdSource = "field"
            setup.draft.zone2PaceMin = "6:40"; setup.draft.zone2PaceMax = "5:50"; setup.draft.thresholdPace = "4:45"
            try await capture(PlanSetupFlow(model: setup, onClose: {}).environment(\.locale, language.locale),
                              name: "training-zones-filled-\(language.rawValue)", size: CGSize(width: 393, height: 1600))
            try await capture(PlanSetupFlow(model: setup, onClose: {}).environment(\.locale, language.locale),
                              name: "training-zones-phone-\(language.rawValue)")
            setup.showPaceInputs = true
            try await capture(PlanSetupFlow(model: setup, onClose: {}).environment(\.locale, language.locale),
                              name: "training-paces-filled-\(language.rawValue)", size: CGSize(width: 393, height: 1600))
            try await capture(PlanSetupFlow(model: setup, onClose: {}).environment(\.locale, language.locale).dynamicTypeSize(.accessibility3),
                              name: "training-paces-large-\(language.rawValue)", size: CGSize(width: 393, height: 2600))
            setup.showPaceInputs = false
            for method in [0, 1] {
                try await capture(WatchZonesGuideSheet(method: method).environment(\.locale, language.locale),
                                  name: "training-guide-\(method)-\(language.rawValue)", size: CGSize(width: 393, height: method == 0 ? 2700 : 1400))
            }
            try await capture(PlanSetupFlow(model: setup, onClose: {}).environment(\.locale, language.locale).dynamicTypeSize(.accessibility3),
                              name: "training-zones-large-\(language.rawValue)", size: CGSize(width: 393, height: 2600))
            setup.draft.maxHr = nil; setup.draft.restingHr = nil
            setup.draft.aetHr = nil; setup.draft.antHr = nil
            setup.draft.zone2PaceMin = ""; setup.draft.zone2PaceMax = ""; setup.draft.thresholdPace = ""
        }
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
            for (step, name) in [(SetupStep.goal, "choose-goal"), (.details, "race"), (.raceDate, "race-date"), (.raceGoal, "goal"), (.schedule, "week"), (.venues, "venues"), (.body, "body"), (.trainingZones, "training-zones"), (.raceHistory, "history"), (.startDate, "start-date"), (.review, "review")] {
                setup.jump(to: step)
                try await capture(PlanSetupFlow(model: setup, onClose: {}).environment(\.locale, language.locale), name: "setup-\(name)-\(language.rawValue)", size: CGSize(width: 393, height: 1600))
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
