import SwiftUI

struct RootView: View {
    let app: AppModel
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        Group {
            switch app.session.state {
            case .signedOut:
                SignInScreen(app: app)
            case .restoring:
                restoringView
            case .signedIn:
                MainTabs(app: app)
            }
        }
        .animation(reduceMotion ? nil : UH.Motion.standard, value: app.session.state)
        .task {
            await app.restore()
            if app.session.user != nil { app.generation.resumeIfNeeded() }
        }
    }

    private var restoringView: some View {
        VStack(spacing: UH.Space.regular) {
            if let error = app.restoreError {
                Text(error)
                    .font(UH.TextStyle.body)
                    .foregroundStyle(UH.Palette.secondary)
                    .multilineTextAlignment(.center)
                Button("Try again") { Task { await app.restore() } }
                    .buttonStyle(.uhPrimary)
                    .frame(maxWidth: 220)
            } else {
                ProgressView()
            }
        }
        .padding(UH.Space.section)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(UH.Palette.surface.ignoresSafeArea())
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

    private enum Tab: Hashable { case athletes, plan, coach, me }

    var body: some View {
        TabView(selection: $selection) {
            if app.session.user?.isCoach == true {
                SwiftUI.Tab("Athletes", systemImage: "person.3.sequence.fill", value: Tab.athletes) {
                    CoachDashboardView(app: app, onSelectTab: { tabIndex in
                        if tabIndex == 1 {
                            selection = .plan
                        }
                    })
                }
            }
            SwiftUI.Tab("Plan", systemImage: "figure.run", value: Tab.plan) {
                PlanView(model: app.plan, generation: app.generation,
                         onBuildPlan: { overlay = .setup(app.makeSetup(mode: app.session.user?.onboardingComplete == false ? .onboarding : .newPlan)) },
                         onViewProgress: { overlay = .progress }, user: app.session.user,
                         onSharpen: { destination in
                             app.trainingDestination = destination
                             selection = .me
                         },
                         app: app)
            }
            SwiftUI.Tab("Coach", systemImage: "bubble.left.and.bubble.right.fill", value: Tab.coach) {
                ChatView(service: app.chat, plan: app.plan.snapshot?.plan, planModel: app.plan)
            }
            SwiftUI.Tab("Me", systemImage: "person.crop.circle", value: Tab.me) {
                ProfileView(app: app)
            }
        }
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
