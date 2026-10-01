import Foundation
import Observation

@Observable
@MainActor
final class AppModel {
    let session: SessionStore
    let client: APIClient
    let auth: any AuthServicing
    private(set) var restoreError: String?

    init(
        tokenStore: any TokenStore,
        makeAuth: (APIClient) -> any AuthServicing = { AuthService(client: $0) },
        baseURL: @escaping @Sendable () -> URL = { AppEnvironment.current().baseURL },
        session urlSession: URLSession = .shared
    ) {
        let session = SessionStore(tokenStore: tokenStore)
        self.session = session
        client = APIClient(
            baseURL: baseURL,
            tokenStore: tokenStore,
            session: urlSession,
            onUnauthorized: { await session.signOut() }
        )
        auth = makeAuth(client)
    }

    /// Confirms a stored token with /api/auth/me. Offline keeps the token so a
    /// retry (or Phase 1's cache) can still use it.
    func restore() async {
        guard session.state == .restoring else { return }
        restoreError = nil
        do {
            session.setUser(try await auth.me())
        } catch APIError.unauthorized {
            session.signOut()
        } catch let error as APIError {
            restoreError = error.userMessage
        } catch {
            restoreError = error.localizedDescription
        }
    }

    func signOut() async {
        await auth.logout()
        session.signOut()
    }
}
