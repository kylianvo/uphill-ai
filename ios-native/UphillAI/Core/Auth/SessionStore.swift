import Foundation
import Observation

@Observable
@MainActor
final class SessionStore {
    enum State: Equatable {
        /// A token is stored; waiting for /api/auth/me to confirm it.
        case restoring
        case signedOut
        case signedIn(User)
    }

    private(set) var state: State
    private let tokenStore: any TokenStore
    private let onUserChange: @MainActor (User?) -> Void

    init(tokenStore: any TokenStore, onUserChange: @escaping @MainActor (User?) -> Void = { _ in }) {
        self.tokenStore = tokenStore
        self.onUserChange = onUserChange
        state = tokenStore.read() == nil ? .signedOut : .restoring
    }

    var user: User? {
        if case .signedIn(let user) = state { user } else { nil }
    }

    func didSignIn(_ response: AuthResponse) {
        tokenStore.write(response.sessionToken)
        state = .signedIn(response.user)
        onUserChange(response.user)
    }

    func setUser(_ user: User) {
        state = .signedIn(user)
        onUserChange(user)
    }

    func signOut() {
        tokenStore.write(nil)
        state = .signedOut
        onUserChange(nil)
    }
}
