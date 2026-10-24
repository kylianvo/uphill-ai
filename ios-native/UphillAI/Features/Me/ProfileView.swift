import SwiftUI

struct ProfileView: View {
    @Bindable var app: AppModel
    @State private var showDeveloperMenu = false
    @AppStorage(AppLanguage.storageKey) private var language = AppLanguage.en
    @AppStorage(AppAppearance.storageKey) private var appearance = AppAppearance.system
    @State private var path: [TrainingDestination] = []
    @State private var showSchedule = false
    @State private var selectedShoeSlot: ShoeRotationSlot? = nil
    @State private var detailResult: RaceResult?
    @State private var raceHistory: RaceHistoryResponse?
    @State private var badges: [DistanceBadge] = DistanceBadge.deriveBadges(from: [])

    init(app: AppModel, initialBadges: [DistanceBadge]? = nil) {
        self.app = app
        if let initialBadges {
            _badges = State(initialValue: initialBadges)
        }
    }

    var body: some View {
        NavigationStack(path: $path) {
            List {
                if let user = app.session.user {
                    Section {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(user.name).font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
                            Text(user.email).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        }
                        .padding(.vertical, 4)
                    }

                    if let history = raceHistory {
                        Section {
                            RoadPersonalBestsView(summary: history.summary) { id in detailResult = history.results.first { $0.id == id } }
                                .listRowBackground(Color.clear)
                        }
                    }

                    // Distance Badges (the grid draws its own title and unlocked counter)
                    Section {
                        DistanceBadgeGrid(badges: badges) { badge in
                            detailResult = raceHistory?.results.first { $0.id == badge.resultId }
                        }
                        .listRowInsets(EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16))
                        .listRowBackground(Color.clear)
                    }

                    // Shoe Rotation (the view draws its own title)
                    Section {
                        ShoeRotationView(rotation: $app.shoeRotation) { slot in
                            selectedShoeSlot = slot
                        }
                        .listRowInsets(EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16))
                        .listRowBackground(Color.clear)
                    }

                    Section("Training") {
                        NavigationLink("About you", value: TrainingDestination.aboutYou)
                        NavigationLink("Training zones", value: TrainingDestination.trainingZones)
                        NavigationLink("Race history", value: TrainingDestination.raceHistory)
                    }

                    if app.notifications.preferences.available == true {
                        Section {
                            NavigationLink("Notifications") { NotificationSettingsView(model: app.notifications) }
                        }
                    }

                    Section("Tools & Labs") {
                        NavigationLink("Pace Strategy", value: TrainingDestination.paceStrategy)
                            .accessibilityIdentifier("me.tool.paceStrategy")
                        NavigationLink("Goal Determiner", value: TrainingDestination.goalDeterminer)
                            .accessibilityIdentifier("me.tool.goalDeterminer")
                        NavigationLink("Nutrition Lab", value: TrainingDestination.nutritionLab)
                            .accessibilityIdentifier("me.tool.nutritionLab")
                        NavigationLink("Gear Vault", value: TrainingDestination.gearVault)
                            .accessibilityIdentifier("me.tool.gearVault")
                        NavigationLink("Knowledge Hub", value: TrainingDestination.knowledgeHub)
                            .accessibilityIdentifier("me.tool.knowledgeHub")
                    }

                    Section("Training profile") {
                        row(L("Weekly volume"), user.currentWeeklyKm.map { "\(Int($0.rounded())) km" })
                        row(L("Days per week"), user.daysPerWeek.map(String.init))
                        row(L("Long run day"), user.longRunDay.flatMap { $0.isEmpty ? nil : L($0) })
                        row(L("Aerobic threshold HR"), user.aetHr.map { "\($0) bpm" })
                        row(L("Anaerobic threshold HR"), user.antHr.map { "\($0) bpm" })
                        row(L("Zone 2 pace"), zone2(user))
                    }

                    // Connected Accounts (COROS & Watch Integration). No section header: the
                    // card carries its own "CONNECTED ACCOUNTS" title.
                    Section {
                        ConnectedAccountsView(service: app.deviceConnectionService)
                            .listRowInsets(EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16))
                            .listRowBackground(Color.clear)
                        if app.appleHealthEnabled {
                            AppleHealthRow(app: app)
                                .listRowInsets(EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16))
                                .listRowBackground(Color.clear)
                                .listRowSeparator(.hidden, edges: .top)
                        }
                    }
                }

                Section {
                    Picker("Language", selection: $language) {
                        ForEach(AppLanguage.allCases) { Text(verbatim: $0.nativeName).tag($0) }
                    }
                    .accessibilityIdentifier("me.language")
                    Picker("Appearance", selection: $appearance) {
                        ForEach(AppAppearance.allCases) { Text($0.label).tag($0) }
                    }
                    .accessibilityIdentifier("me.appearance")
                }

                Section("Account") {
                    if app.session.user?.provider == "email" {
                        NavigationLink("Change password") { ChangePasswordScreen(app: app) }
                    }
                    Button("Sign out", role: .destructive) {
                        Task { await app.signOut() }
                    }
                }

                Section {
                    Text(versionLabel)
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.muted)
                        .frame(maxWidth: .infinity)
                        .onLongPressGesture { showDeveloperMenu = DeveloperMenu.isAvailable }
                }
                .listRowBackground(Color.clear)
            }
            .navigationTitle("Me")
            .navigationDestination(isPresented: Binding(get: { detailResult != nil }, set: { if !$0 { detailResult = nil } })) {
                if let detailResult {
                    RaceDetailScreen(result: detailResult, service: app.raceHistoryService) {
                        Task { if let history = try? await app.raceHistoryService.history() { app.raceHistory = history } }
                    }
                }
            }
            .navigationDestination(for: TrainingDestination.self) { destination in
                switch destination {
                case .raceHistory:
                    RaceHistoryScreen(service: app.raceHistoryService, onSelectBadge: { _ in }, initialHistory: app.raceHistory ?? raceHistory, onHistoryChanged: { app.raceHistory = $0 })
                case .nutritionLab:
                    NutritionLabSheet(service: app.nutritionService, activePlan: app.plan.snapshot?.plan, user: app.session.user)
                case .gearVault:
                    GearVaultSheet(service: app.gearService, activePlan: app.plan.snapshot?.plan, user: app.session.user, raceMatchService: app.raceMatchService) { newShoe in
                        app.shoeRotation.shoes.removeAll { $0.slot == newShoe.slot }
                        app.shoeRotation.shoes.append(newShoe)
                    }
                case .goalDeterminer:
                    GoalDeterminerSheet(
                        service: app.goalEstimateService,
                        pacingService: app.pacingService,
                        activePlan: app.plan.snapshot?.plan,
                        user: app.session.user,
                        raceHistoryService: app.raceHistoryService,
                        onApplyGoal: { targetMinutes in
                            if let planId = app.plan.snapshot?.plan.id {
                                Task { try? await app.planService.applyGoal(planID: planId, targetMinutes: targetMinutes) }
                            }
                        },
                        onPlanPacing: { _ in
                            path.append(.paceStrategy)
                        },
                        raceMatchService: app.raceMatchService
                    )
                case .paceStrategy:
                    PaceStrategySheet(
                        service: app.pacingService,
                        activePlan: app.plan.snapshot?.plan,
                        user: app.session.user,
                        onOpenNutrition: { path.append(.nutritionLab) },
                        onOpenGear: { path.append(.gearVault) }
                    )
                case .watch:
                    ScrollView {
                        VStack(spacing: UH.Space.regular) {
                            ConnectedAccountsView(service: app.deviceConnectionService)
                            if app.appleHealthEnabled { AppleHealthRow(app: app) }
                        }
                        .padding(UH.Space.regular)
                    }
                    .background(UH.Palette.surface)
                    .navigationTitle("Connected accounts")
                    .navigationBarTitleDisplayMode(.inline)
                    .onDisappear { Task { await app.loadCorosStatus() } }
                case .knowledgeHub:
                    KnowledgeHubScreen(service: app.knowledgeService)
                default:
                    if app.session.user != nil { ProfileSettingsScreen(app: app, section: destination) }
                }
            }
            .onChange(of: app.trainingDestination, initial: true) { _, destination in
                guard let destination else { return }
                app.trainingDestination = nil
                if destination == .schedule { showSchedule = true }
                else { path.append(destination) }
            }
            .sheet(isPresented: $showSchedule) { ScheduleChangeSheet(model: app.plan) }
            .sheet(isPresented: $showDeveloperMenu) { DeveloperMenu() }
            .sheet(item: $selectedShoeSlot) { slot in
                ShoeSlotDetailSheet(
                    slot: slot,
                    rotation: $app.shoeRotation,
                    onOpenGearVault: {
                        selectedShoeSlot = nil
                        path.append(.gearVault)
                    }
                )
            }
            .task {
                async let rotation: Void = app.loadShoeRotation()
                async let history: Void = app.loadRaceHistory()
                async let health: Void = app.loadAppleHealthStatus()
                _ = await (rotation, history, health)
            }
            .onChange(of: app.raceHistory, initial: true) { _, history in
                if let history { raceHistory = history; badges = DistanceBadge.deriveBadges(from: history.results) }
            }
        }
    }

    private func row(_ title: String, _ value: String?) -> some View {
        LabeledContent(title, value: value ?? L("Not set"))
            .foregroundStyle(UH.Palette.ink)
    }

    private func zone2(_ user: User) -> String? {
        guard let min = user.zone2PaceMin, let max = user.zone2PaceMax else { return nil }
        return "\(min)–\(max) /km"
    }

    private var versionLabel: String {
        let info = Bundle.main.infoDictionary
        let version = info?["CFBundleShortVersionString"] as? String ?? "?"
        let build = info?["CFBundleVersion"] as? String ?? "?"
        return "Uphill AI \(version) (\(build))"
    }
}
