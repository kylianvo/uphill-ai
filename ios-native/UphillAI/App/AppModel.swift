import Foundation
import Observation

@Observable
@MainActor
final class AppModel {
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
    let coachingService: any CoachingServicing
    /// The server (`/api/shoe-rotation`) owns the rotation; every local change is saved back.
    var shoeRotation = ShoeRotation() {
        didSet {
            guard !applyingRemoteRotation, oldValue != shoeRotation else { return }
            scheduleShoeRotationSave()
        }
    }
    private var applyingRemoteRotation = false
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
    var coachedAthleteProfile: User? = nil
    var pendingInvites: [CoachingInvite] = []
    let generation: GenerationCenter
    let plan: PlanViewModel
    let chat: ChatService
    let cache: OfflineCache
    var onboardingDeferred = false
    var trainingDestination: TrainingDestination?
    var needsOnboarding: Bool {
        session.user?.onboardingComplete == false && generation.running == nil && !onboardingDeferred
    }

    /// The setup behind the last generation, so "Try again" re-submits the same answers.
    private(set) var lastSetup: PlanSetupViewModel?

    func makeSetup(mode: PlanSetupViewModel.Mode) -> PlanSetupViewModel {
        let setup = PlanSetupViewModel(mode: mode, user: session.user, service: generationService, generation: generation, session: session, raceService: RaceMatchService(client: client))
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
        var onSignedOut: @MainActor () -> Void = {}
        let session = SessionStore(tokenStore: tokenStore) { user in
            if let user { cache.save(user, as: .user) } else { cache.clearAll(); onSignedOut() }
        }
        self.session = session
        client = APIClient(
            baseURL: baseURL,
            tokenStore: tokenStore,
            session: urlSession,
            onUnauthorized: { await session.signOut() }
        )
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
        coachingService = CoachingService(client: client)
        generation = GenerationCenter(service: generationService)
        plan = PlanViewModel(service: planService, cache: cache, isSignedIn: { [session] in session.user != nil },
                             generation: generation, generationService: generationService)
        chat = ChatService(client: client)
        onSignedOut = { [weak self] in
            self?.generation.reset()
            self?.plan.reset()
            self?.onboardingDeferred = false
            self?.lastSetup = nil
            self?.shoeRotationSave?.cancel()
            self?.applyingRemoteRotation = true
            self?.shoeRotation = ShoeRotation()
            self?.applyingRemoteRotation = false
        }
        generation.onFinished = { [weak self] kind, outcome in
            guard let self, self.session.user != nil else { return }
            switch outcome {
            case .done(let snapshot?): self.plan.adopt(snapshot)
            case .done(nil), .lost: await self.plan.load()
            case .failed, .cancelled: return
            }
            if kind == .newPlan { await self.refreshUser() }
        }
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

    func enterAthleteView(athlete: CoachedAthleteRow) {
        actingAsAthlete = athlete
        Task {
            do {
                async let p = coachingService.fetchAthleteProfile(athleteId: athlete.athleteId)
                async let snap = coachingService.fetchAthleteActivePlan(athleteId: athlete.athleteId)
                let (fetchedP, fetchedSnap) = try await (p, snap)
                self.coachedAthleteProfile = fetchedP
                if let fetchedSnap {
                    self.plan.adopt(fetchedSnap)
                }
            } catch {
                print("Failed to enter athlete view: \(error)")
            }
        }
    }

    func exitAthleteView() {
        actingAsAthlete = nil
        coachedAthleteProfile = nil
        Task {
            await plan.load()
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
        actingAsAthlete = nil
        coachedAthleteProfile = nil
        pendingInvites = []
        await auth.logout()
        session.signOut()
    }
}
