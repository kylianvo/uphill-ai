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
    let generation: GenerationCenter
    let plan: PlanViewModel
    let cache: OfflineCache
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
        generation = GenerationCenter(service: generationService)
        plan = PlanViewModel(service: planService, cache: cache, isSignedIn: { [session] in session.user != nil })
        onSignedOut = { [weak self] in
            self?.generation.reset()
            self?.plan.reset()
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

    func signOut() async {
        await auth.logout()
        session.signOut()
    }
}
