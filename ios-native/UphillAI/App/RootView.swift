import SwiftUI

struct RootView: View {
    let app: AppModel
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.scenePhase) private var scenePhase
    @AppStorage(AppLanguage.storageKey) private var language = AppLanguage.en

    var body: some View {
        Group {
            switch app.session.state {
            case .signedOut:
                SignInScreen(app: app)
            case .restoring:
                restoringView
            case .signedIn:
                // Rebuilt on a language change so strings computed in code (`L(…)`) re-resolve.
                MainTabs(app: app).id(language)
            }
        }
        .animation(reduceMotion ? nil : UH.Motion.standard, value: app.session.state)
        // Warms the Athletes tab for coaches on every sign-in, not just on restore.
        .task(id: app.session.user?.id) { await app.prefetchCoachDashboard() }
        .task {
            await app.restore()
            if app.session.user != nil { app.generation.resumeIfNeeded() }
        }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active {
                Task {
                    await app.notifications.refresh(userID: app.session.user?.id)
                    await app.autoSyncWatchIfDue()
                    await app.syncAppleHealthIfDue()
                }
            }
        }
        .task(id: app.session.user?.id) {
            if app.session.user != nil {
                await app.notifications.refresh(userID: app.session.user?.id)
                await app.autoSyncWatchIfDue()
                await app.syncAppleHealthIfDue()
            }
        }
    }

    private var restoringView: some View {
        LaunchView(error: app.restoreError) { Task { await app.restore() } }
    }
}

/// Owns the sign-in view model. Leaving `.signedOut` removes this view, so the
/// next sign-out starts with a fresh model and empty fields.
private struct SignInScreen: View {
    @State private var model: SignInViewModel

    init(app: AppModel) {
        _model = State(initialValue: SignInViewModel(auth: app.auth, session: app.session))
    }

    var body: some View {
        SignInView(model: model)
    }
}

private enum Overlay: Identifiable {
    case onboarding, progress, setup(PlanSetupViewModel)

    var id: String {
        switch self {
        case .onboarding: "onboarding"
        case .progress: "progress"
        case .setup(let model): "setup-\(ObjectIdentifier(model).hashValue)"
        }
    }
}

private struct MainTabs: View {
    let app: AppModel
    @State private var overlay: Overlay?
    @State private var selection = Tab.plan
    @State private var knowledgeRoute: NotificationRoute?
    @State private var routeError: String?

    private enum Tab: Hashable { case athletes, plan, progress, coach, me }

    var body: some View {
        TabView(selection: $selection) {
            if app.session.user?.isCoach == true {
                SwiftUI.Tab("Athletes", systemImage: "person.3.sequence.fill", value: Tab.athletes) {
                    AthletesView(app: app, onSelectTab: { tabIndex in
                        if tabIndex == 1 {
                            selection = .plan
                        }
                    })
                }
            }
            SwiftUI.Tab("Plan", systemImage: "figure.run", value: Tab.plan) {
                PlanView(model: app.plan, generation: app.generation,
                         onBuildPlan: {
                             if app.actingAsAthlete != nil {
                                 // Coaching: build for the runner, never for the coach's own account.
                                 guard let athlete = app.coachedAthleteProfile else { return }
                                 overlay = .setup(app.makeSetup(mode: .newPlan, athlete: athlete))
                             } else {
                                 overlay = .setup(app.makeSetup(mode: app.session.user?.onboardingComplete == false ? .onboarding : .newPlan))
                             }
                         },
                         onViewProgress: { overlay = .progress }, user: app.session.user,
                         onSharpen: { destination in
                             app.trainingDestination = destination
                             selection = .me
                         },
                         app: app)
            }
            SwiftUI.Tab("Progress", systemImage: "chart.line.uptrend.xyaxis", value: Tab.progress) {
                ProgressTabView(model: app.progress, goalPath: app.plan.goal?.path,
                                deviceService: app.deviceConnectionService,
                                onBuildPlan: { selection = .plan })
            }
            SwiftUI.Tab("Coach", systemImage: "bubble.left.and.bubble.right.fill", value: Tab.coach) {
                ChatView(service: app.chat, plan: app.plan.snapshot?.plan, planModel: app.plan)
            }
            SwiftUI.Tab("Me", systemImage: "person.crop.circle", value: Tab.me) {
                ProfileView(app: app)
            }
        }
        .task(id: app.notifications.pendingID) { await openNotification() }
        .sheet(isPresented: Binding(get: { knowledgeRoute != nil }, set: { if !$0 { knowledgeRoute = nil; app.notifications.visibleRoute = nil } })) {
            if let route = knowledgeRoute, let card = route.cardId {
                NavigationStack {
                    KnowledgeDetailScreen(service: app.knowledgeService, cardID: card, language: route.lang ?? AppLanguage.code) {
                        Task { await app.notifications.didOpen() }
                    }
                }
            }
        }
        .alert("Notification unavailable", isPresented: Binding(get: { routeError != nil }, set: { if !$0 { routeError = nil } })) {
            Button("Try again") { Task { await openNotification() } }
            Button("Cancel", role: .cancel) { app.notifications.pendingID = nil; app.notifications.pendingRoute = nil }
        } message: { Text(routeError ?? "") }
        // An always-visible bar material: content scrolls cleanly behind the tab bar instead of
        // showing through it (e.g. the Plan tab's "Coach's pick this week" label).
        .toolbarBackground(.visible, for: .tabBar)
        .toolbarBackground(.bar, for: .tabBar)
        .safeAreaInset(edge: .top) {
            if let athlete = app.actingAsAthlete {
                CoachedAthleteBanner(athlete: athlete) {
                    Task { await app.exitAthleteView() }
                }
            }
        }
        .onChange(of: app.actingAsAthlete?.athleteId) { _, newId in
            if newId != nil {
                selection = .plan
            }
        }
        .fullScreenCover(item: $overlay) { current in
            switch current {
            case .onboarding: OnboardingScreen(app: app, close: closeSetup)
            case .progress:
                GenerationProgressView(
                    generation: app.generation,
                    hasPlan: app.plan.snapshot != nil,
                    onShowPlan: { app.generation.clearOutcome(); selection = .plan; overlay = nil },
                    onLeave: { overlay = nil },
                    onRetry: { reopen(at: .review) },
                    onEditAnswers: { reopen(at: .goal) })
            case .setup(let model): PlanSetupFlow(model: model, onClose: closeSetup)
            }
        }
        .onChange(of: app.needsOnboarding, initial: true) { _, needs in
            if needs, overlay == nil { overlay = .onboarding }
        }
        .onChange(of: app.generation.running?.jobID, initial: true) { _, job in
            if job != nil, app.generation.running?.kind == .newPlan { overlay = .progress }
        }
        .onChange(of: app.generation.lastOutcome) { _, outcome in
            if outcome?.kind == .newPlan { overlay = .progress }
        }
    }

    private func openNotification() async {
        guard let route = app.notifications.pendingRoute else { return }
        if app.actingAsAthlete != nil { await app.exitAthleteView() }
        overlay = nil
        if route.kind == "knowledge" {
            knowledgeRoute = route
            app.notifications.visibleRoute = route
            return
        }
        if let destination = route.trainingDestination {
            app.trainingDestination = destination
            selection = .me
            await app.notifications.didOpen()
            return
        }
        await app.plan.load()
        guard app.plan.cachedAt == nil, app.plan.snapshot?.plan.id == route.planId else {
            selection = .plan
            routeError = L("This item is no longer available. Your current plan is shown.")
            return
        }
        if let id = route.workoutId, app.plan.snapshot?.workouts.contains(where: { $0.id == id }) != true {
            routeError = L("This item is no longer available. Your current plan is shown.")
            return
        }
        selection = .plan
        app.plan.notificationRoute = route
        await app.notifications.didOpen()
    }

    /// The flow calls this after a successful start too; that must not hide the progress screen.
    private func closeSetup() {
        app.onboardingDeferred = true
        if case .progress = overlay { return }
        overlay = nil
    }

    private func reopen(at step: SetupStep) {
        guard let setup = app.lastSetup else { overlay = nil; return }
        app.generation.clearOutcome()
        if step == .review { setup.reopenAtReview() } else { setup.jump(to: step) }
        overlay = .setup(setup)
    }
}

private struct OnboardingScreen: View {
    let app: AppModel
    let close: () -> Void
    @State private var setup: PlanSetupViewModel?

    var body: some View {
        if let setup {
            PlanSetupFlow(model: setup, onClose: close)
        } else {
            WelcomeView(onStart: { setup = app.makeSetup(mode: .onboarding) }, onNotNow: close)
        }
    }
}
