import Foundation
import Observation

@Observable
@MainActor
final class AppModel {
    let notifications: NotificationCoordinator
    let session: SessionStore
    let client: APIClient
    let auth: any AuthServicing
    let planService: any PlanServicing
    let generationService: any GenerationServicing
    let nutritionService: any NutritionServicing
    let gearService: any GearServicing
    let raceHistoryService: any RaceHistoryServicing
    let goalEstimateService: any GoalEstimateServicing
    let pacingService: any PacingServicing
    let knowledgeService: any KnowledgeServicing
    let deviceConnectionService: any DeviceConnectionServicing
    let appleHealth: AppleHealthSyncService
    let coachingService: any CoachingServicing
    var raceMatchService: RaceMatchService { RaceMatchService(client: client) }
    /// The server (`/api/shoe-rotation`) owns the rotation; every local change is saved back.
    var shoeRotation = ShoeRotation() {
        didSet {
            guard !applyingRemoteRotation, oldValue != shoeRotation else { return }
            scheduleShoeRotationSave()
        }
    }
    private var applyingRemoteRotation = false
    /// Last responses, so revisiting these screens shows data at once and refreshes quietly.
    var raceHistory: RaceHistoryResponse?
    var coachDashboard: CoachDashboardData?

    func loadRaceHistory() async {
        if let history = try? await raceHistoryService.history() { raceHistory = history }
    }

    /// Whether COROS is linked, for the plan screen's "Get the most from your plan" card.
    var corosConnected = false

    func loadCorosStatus() async {
        guard let status = try? await deviceConnectionService.fetchStatus() else { return }
        corosConnected = status.isCorosConnected
        await applyAppleHealthStatus(status.appleHealth)
    }

    /// Apple Health, for Me → Connected accounts and onboarding's watch step.
    var appleHealthEnabled = false
    var appleHealthConnected = false
    var appleHealthLastSync: String?
    var appleHealthSyncing = false
    var appleHealthMessage: String?
    /// Failures show in the danger tone; the nothing-found hint and retry notice don't.
    var appleHealthMessageIsError = false
    /// The last connect read nothing: most likely every Health switch was left off.
    var appleHealthNeedsAccess = false
    private var appleHealthRecoveryEnabled = true
    private var lastAppleHealthSync: Date?

    func loadAppleHealthStatus() async {
        if let status = try? await deviceConnectionService.fetchStatus() { await applyAppleHealthStatus(status.appleHealth) }
    }

    private func applyAppleHealthStatus(_ status: AppleHealthConnectionStatus?) async {
        let available = await appleHealth.isAvailable
        appleHealthEnabled = (status?.enabled ?? false) && available
        let observing = if let id = session.user?.id { await appleHealth.isObserving(userId: id) } else { false }
        // Only this phone's observing counts: after a reinstall, new phone or session expiry the
        // server still says connected, but nothing syncs until the athlete taps Connect again.
        appleHealthConnected = observing
        appleHealthLastSync = status?.lastSyncAt
        appleHealthRecoveryEnabled = status?.recoveryEnabled ?? true
        await appleHealth.setRecoveryEnabled(appleHealthRecoveryEnabled)
    }

    func connectAppleHealth() async {
        guard let userID = session.user?.id, !appleHealthSyncing else { return }
        appleHealthSyncing = true
        defer { appleHealthSyncing = false }
        do {
            let outcome = try await appleHealth.connect(userId: userID)
            appleHealthConnected = true
            lastAppleHealthSync = .now
            appleHealthMessageIsError = false
            appleHealthNeedsAccess = outcome.nothingFound
            appleHealthMessage = outcome.nothingFound
                ? L("No workouts found. Check Settings → Health → Data Access & Devices → Uphill AI.")
                : nil
            await plan.applyWatchMatches()
            await loadAppleHealthStatus()
        } catch AppleHealthSyncError.unavailable {
            appleHealthMessageIsError = true
            appleHealthMessage = L("Apple Health isn't available on this device.")
        } catch {
            // Connected locally; the next foreground or background wake retries the upload.
            appleHealthConnected = await appleHealth.isObserving(userId: userID)
            appleHealthMessageIsError = false
            appleHealthMessage = L("Couldn't sync with Uphill. I'll try again next time you open the app.")
        }
    }

    /// App open / foreground: at most every 5 minutes, only for the athlete who connected on this phone.
    func syncAppleHealthIfDue(now: Date = .now) async {
        guard let userID = session.user?.id, actingAsAthlete == nil, !appleHealthSyncing,
              await appleHealth.isObserving(userId: userID) else { return }
        if let last = lastAppleHealthSync, now.timeIntervalSince(last) < 5 * 60 { return }
        lastAppleHealthSync = now
        appleHealthSyncing = true
        defer { appleHealthSyncing = false }
        guard let outcome = try? await appleHealth.sync() else { return }
        if outcome.accepted > 0 || outcome.deleted > 0 { await plan.applyWatchMatches() }
    }

    func disconnectAppleHealth() async {
        guard let userID = session.user?.id, !appleHealthSyncing else { return }
        appleHealthSyncing = true
        defer { appleHealthSyncing = false }
        do {
            try await AppleHealthAPI(client: client).disconnect()
            await appleHealth.stopObserving(userId: userID)
            appleHealthConnected = false
            appleHealthLastSync = nil
            appleHealthMessage = nil
        } catch {
            appleHealthMessageIsError = true
            appleHealthMessage = L("Couldn't disconnect. Check your connection and try again.")
        }
    }

    /// Matches the dashboard's default filters (14 days, all levels).
    func prefetchCoachDashboard() async {
        guard session.user?.isCoach == true else { return }
        async let ov = coachingService.fetchOverview(days: 14, athleteId: nil, level: "all")
        async let rst = coachingService.fetchRoster()
        async let invs = coachingService.fetchMyInvites()
        if let data = try? await CoachDashboardData(overview: ov, roster: rst, invites: invs) { coachDashboard = data }
    }
    private var shoeRotationSave: Task<Void, Never>?

    func loadShoeRotation() async {
        guard let remote = try? await gearService.fetchShoeRotation() else { return }
        applyingRemoteRotation = true
        shoeRotation = remote
        applyingRemoteRotation = false
    }

    /// Quick taps (+5 km, +5 km) collapse into one save of the latest rotation.
    private func scheduleShoeRotationSave() {
        shoeRotationSave?.cancel()
        let rotation = shoeRotation
        shoeRotationSave = Task { [gearService] in
            try? await Task.sleep(for: .milliseconds(600))
            guard !Task.isCancelled else { return }
            _ = try? await gearService.saveShoeRotation(rotation)
        }
    }
    var actingAsAthlete: CoachedAthleteRow? = nil
    /// The action a coach tapped on the Athletes tab, picked up once by the runner's Plan tab.
    var pendingCoachAction: CoachAction? = nil

    /// Hands the pending Athletes-tab action to the Plan tab exactly once.
    func takePendingCoachAction() -> CoachAction? {
        defer { pendingCoachAction = nil }
        return pendingCoachAction
    }
    var coachedAthleteProfile: User? = nil
    var pendingInvites: [CoachingInvite] = []
    let generation: GenerationCenter
    let plan: PlanViewModel
    let progress: ProgressViewModel
    let chat: ChatService
    let cache: OfflineCache
    var onboardingDeferred = false
    var trainingDestination: TrainingDestination?
    var needsOnboarding: Bool {
        session.user?.onboardingComplete == false && generation.running == nil && !onboardingDeferred
    }

    /// The setup behind the last generation, so "Try again" re-submits the same answers.
    private(set) var lastSetup: PlanSetupViewModel?

    /// With `athlete`, a coach builds a plan for that runner: their profile prefills the setup and the
    /// request goes to the runner's coaching route (a draft the coach then publishes).
    func makeSetup(mode: PlanSetupViewModel.Mode, athlete: User? = nil) -> PlanSetupViewModel {
        // Onboarding treats "nothing found" as success; only a failed connect returns a message.
        var connectHealth: (@MainActor () async -> String?)?
        if appleHealthEnabled {
            connectHealth = { [weak self] in
                guard let self else { return nil }
                await self.connectAppleHealth()
                return self.appleHealthConnected ? nil : self.appleHealthMessage
            }
        }
        let setup = PlanSetupViewModel(mode: mode, user: athlete ?? session.user,
                                       service: generationService.scoped(toAthlete: athlete?.id), generation: generation, session: session, raceService: RaceMatchService(client: client),
                                       goalEstimateService: goalEstimateService, raceHistoryService: raceHistoryService,
                                       deviceService: deviceConnectionService,
                                       loadWatchVolume: { [client] in
                                           guard let snapshot = try? await client.send(Endpoint<WatchVolume>.get("/api/auth/fitness-snapshot")),
                                                 ["coros", "apple_health"].contains(snapshot.weeklyKmSource) else { return nil }
                                           return snapshot
                                       },
                                       connectAppleHealth: connectHealth,
                                       appleHealthConnected: appleHealthConnected)
        lastSetup = setup
        return setup
    }

    private(set) var restoreError: String?
    /// True when the last restore had to fall back to cached data.
    private(set) var isOffline = false

    init(
        tokenStore: any TokenStore,
        makeAuth: (APIClient) -> any AuthServicing = { AuthService(client: $0) },
        baseURL: @escaping @Sendable () -> URL = { AppEnvironment.current().baseURL },
        session urlSession: URLSession = .shared,
        cache: OfflineCache = .onDisk()
    ) {
        self.cache = cache
        // A box rather than a captured `var`: the session's callback is Sendable, and the hook
        // is only filled in once self exists, below.
        let signOutHook = SignOutHook()
        let session = SessionStore(tokenStore: tokenStore) { user in
            if let user { cache.save(user, as: .user) } else { cache.clearAll(); signOutHook.run() }
        }
        self.session = session
        client = APIClient(
            baseURL: baseURL,
            tokenStore: tokenStore,
            session: urlSession,
            onUnauthorized: { await session.signOut() }
        )
        notifications = NotificationCoordinator(service: NotificationService(client: client))
        auth = makeAuth(client)
        planService = PlanService(client: client)
        generationService = GenerationService(client: client)
        nutritionService = NutritionService(client: client)
        gearService = GearService(client: client)
        raceHistoryService = RaceHistoryService(client: client)
        goalEstimateService = GoalEstimateService(client: client)
        pacingService = PacingService(client: client)
        knowledgeService = KnowledgeService(client: client)
        deviceConnectionService = DeviceConnectionService(client: client)
        let planIdBox = PlanIdBox()
        #if DEBUG
        let healthStore: any HealthStoring = UserDefaults.standard.bool(forKey: SampleHealthStore.defaultsKey)
            ? SampleHealthStore() : HealthKitStore()
        #else
        let healthStore: any HealthStoring = HealthKitStore()
        #endif
        let health = AppleHealthSyncService(store: healthStore, api: AppleHealthAPI(client: client),
                                            anchors: UserDefaultsAnchorStore(), planId: { await planIdBox.value() })
        appleHealth = health
        coachingService = CoachingService(client: client)
        generation = GenerationCenter(service: generationService)
        plan = PlanViewModel(service: planService, cache: cache, isSignedIn: { [session] in session.user != nil },
                             generation: generation, generationService: generationService)
        planIdBox.model = plan
        progress = ProgressViewModel(service: ProgressService(client: client))
        chat = ChatService(client: client)
        signOutHook.run = { [weak self] in
            self?.notifications.reset()
            self?.lastAutoWatchSync = nil
            self?.lastAppleHealthSync = nil
            self?.appleHealthConnected = false
            // stopObservingForSignOut also clears the recovery-metrics seeded flag.
            self?.appleHealthLastSync = nil
            self?.appleHealthMessage = nil
            Task { [weak self] in await self?.appleHealth.stopObservingForSignOut() }
            self?.generation.reset()
            self?.plan.reset()
            self?.progress.reset()
            self?.onboardingDeferred = false
            self?.lastSetup = nil
            self?.raceHistory = nil
            self?.coachDashboard = nil
            self?.shoeRotationSave?.cancel()
            self?.applyingRemoteRotation = true
            self?.shoeRotation = ShoeRotation()
            self?.applyingRemoteRotation = false
        }
        generation.onFinished = { [weak self] kind, outcome in
            guard let self, self.session.user != nil else { return }
            switch outcome {
            case .done(let snapshot?):
                if kind == .newPlan && self.plan.athleteId == nil {
                    self.plan.adopt(snapshot)
                } else {
                    // A coach may have left this athlete's view while the job ran.
                    await self.plan.load()
                }
            case .done(nil), .lost: await self.plan.load()
            case .failed, .cancelled: return
            }
            if kind == .newPlan { await self.refreshUser() }
        }
        // Background delivery must be registered on every launch, including background wakes.
        Task { await health.resumeObservingIfNeeded() }
    }

    /// Confirms a stored token with /api/auth/me. Offline, it signs in with the
    /// cached user (read-only) when there is one, and keeps the token either way.
    func restore() async {
        guard session.state == .restoring else { return }
        restoreError = nil
        do {
            session.setUser(try await auth.me())
            isOffline = false
        } catch APIError.unauthorized {
            session.signOut()
        } catch let error as APIError {
            if case .transport = error, let cached = cache.load(User.self, .user) {
                isOffline = true
                session.setUser(cached.value)
            } else {
                restoreError = error.userMessage
            }
        } catch {
            restoreError = error.localizedDescription
        }
    }

    func refreshUser() async {
        let userID = session.user?.id
        if let user = try? await auth.me(), session.user?.id == userID, userID != nil {
            session.setUser(user)
        }
    }

    private var lastAutoWatchSync: Date?
    private var isAutoWatchSyncing = false

    /// Called when the app opens or returns to the foreground: syncs the watch at most every 15 minutes.
    func autoSyncWatchIfDue(now: Date = .now) async {
        guard let userID = session.user?.id, actingAsAthlete == nil, !isAutoWatchSyncing else { return }
        isAutoWatchSyncing = true
        defer { isAutoWatchSyncing = false }
        if let last = lastAutoWatchSync, now.timeIntervalSince(last) < 15 * 60 { return }
        if plan.snapshot == nil { await plan.load() }
        guard plan.snapshot != nil else { return }
        await loadCorosStatus()
        guard session.user?.id == userID, actingAsAthlete == nil, plan.athleteId == nil, corosConnected else { return }
        lastAutoWatchSync = now
        await plan.autoSyncWatch()
    }

    func enterAthleteView(athlete: CoachedAthleteRow) {
        pendingCoachAction = nil // an action tapped for an earlier runner must not fire on this one
        actingAsAthlete = athlete
        Task {
            async let p = try? coachingService.fetchAthleteProfile(athleteId: athlete.athleteId)
            async let scoped: Void = plan.setAthleteScope(athlete.athleteId)
            let (fetchedP, _) = await (p, scoped)
            // Another athlete may have been opened meanwhile.
            if actingAsAthlete?.athleteId == athlete.athleteId { self.coachedAthleteProfile = fetchedP }
        }
    }

    func exitAthleteView() async {
        actingAsAthlete = nil
        coachedAthleteProfile = nil
        await plan.setAthleteScope(nil)
    }

    func acknowledgeCoachProfileChanges() async {
        do {
            let user = try await ProfileService(client: client).acknowledgeCoachChanges()
            session.setUser(user)
        } catch {
            print("Failed to acknowledge coach profile changes: \(error)")
        }
    }

    func refreshPendingInvites() async {
        do {
            pendingInvites = try await coachingService.fetchMyInvites()
        } catch {
            print("Failed to fetch pending invites: \(error)")
        }
    }

    func acceptInvite(inviteId: Int) async {
        do {
            try await coachingService.acceptInvite(inviteId: inviteId)
            pendingInvites.removeAll { $0.id == inviteId }
        } catch {
            print("Failed to accept invite: \(error)")
        }
    }

    func declineInvite(inviteId: Int) async {
        do {
            try await coachingService.declineInvite(inviteId: inviteId)
            pendingInvites.removeAll { $0.id == inviteId }
        } catch {
            print("Failed to decline invite: \(error)")
        }
    }

    @discardableResult
    func handleOpenURL(_ url: URL) async -> Bool {
        guard let params = CorosOAuthCoordinator.parseCallbackURL(url) else {
            return false
        }
        guard !params.isError, let state = params.state, let token = params.token else {
            return false
        }
        do {
            let success = try await deviceConnectionService.completeCoros(state: state, token: token)
            return success
        } catch {
            print("Failed to complete COROS connection via deep link: \(error)")
            return false
        }
    }

    func signOut() async {
        await notifications.unregister()
        lastAutoWatchSync = nil
        actingAsAthlete = nil
        coachedAthleteProfile = nil
        pendingInvites = []
        await auth.logout()
        session.signOut()
    }
}

struct CoachDashboardData {
    var overview: CoachOverview
    var roster: [CoachedAthleteRow]
    var invites: [CoachingInvite]
}

/// Lets the Apple Health sync read the active plan id without capturing AppModel before init ends.
@MainActor
final class PlanIdBox: Sendable {
    weak var model: PlanViewModel?
    nonisolated init() {}
    func value() -> Int? { model?.snapshot?.plan.id }
}

/// Holds AppModel's sign-out work for SessionStore's callback, which is created before AppModel
/// can capture itself. Only touched on the main actor.
@MainActor
final class SignOutHook: Sendable {
    var run: () -> Void = {}
    nonisolated init() {}
}
