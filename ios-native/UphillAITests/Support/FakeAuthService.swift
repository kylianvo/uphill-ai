import Foundation
import Synchronization
@testable import UphillAI

/// Records each call as a short string and answers every sign-in with `result`.
final class FakeAuthService: AuthServicing {
    let result: Result<AuthResponse, APIError>
    let calls = Mutex<[String]>([])

    init(_ result: Result<AuthResponse, APIError>) { self.result = result }

    private func record(_ call: String) throws -> AuthResponse {
        calls.withLock { $0.append(call) }
        return try result.get()
    }

    func login(email: String, password: String) async throws -> AuthResponse { try record("login \(email)") }
    func register(name: String, email: String, password: String) async throws -> AuthResponse {
        try record("register \(name) \(email)")
    }
    func signInWithGoogle(idToken: String) async throws -> AuthResponse { try record("google \(idToken)") }
    func signInWithApple(identityToken: String, fullName: String?) async throws -> AuthResponse {
        try record("apple \(identityToken) \(fullName ?? "-")")
    }
    func me() async throws -> User { try result.get().user }
    func logout() async { calls.withLock { $0.append("logout") } }
}
