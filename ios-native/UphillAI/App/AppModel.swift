import Foundation
import Observation

@Observable
@MainActor
final class AppModel {
    let session: SessionStore
    let client: APIClient
    let auth: any AuthServicing
    let planService: any PlanServicing
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
        let session = SessionStore(tokenStore: tokenStore) { user in
            if let user { cache.save(user, as: .user) } else { cache.clearAll() }
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

    func signOut() async {
        await auth.logout()
        session.signOut()
    }
}
