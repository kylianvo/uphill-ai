import Foundation

protocol AuthServicing: Sendable {
    func login(email: String, password: String) async throws -> AuthResponse
    func register(name: String, email: String, password: String) async throws -> AuthResponse
    func signInWithGoogle(idToken: String) async throws -> AuthResponse
    func signInWithApple(identityToken: String, fullName: String?) async throws -> AuthResponse
    func me() async throws -> User
    func logout() async
}

struct AuthService: AuthServicing {
    let client: APIClient

    private struct LoginBody: Encodable { let email: String; let password: String }
    private struct RegisterBody: Encodable { let name: String; let email: String; let password: String }
    private struct GoogleBody: Encodable { let credential: String }
    private struct AppleBody: Encodable { let identityToken: String; let fullName: String? }

    func login(email: String, password: String) async throws -> AuthResponse {
        try await client.send(.send(.post, "/api/auth/login",
                                    body: LoginBody(email: email, password: password), requiresAuth: false))
    }

    func register(name: String, email: String, password: String) async throws -> AuthResponse {
        try await client.send(.send(.post, "/api/auth/register",
                                    body: RegisterBody(name: name, email: email, password: password), requiresAuth: false))
    }

    func signInWithGoogle(idToken: String) async throws -> AuthResponse {
        try await client.send(.send(.post, "/api/auth/google", body: GoogleBody(credential: idToken), requiresAuth: false))
    }

    func signInWithApple(identityToken: String, fullName: String?) async throws -> AuthResponse {
        try await client.send(.send(.post, "/api/auth/apple",
                                    body: AppleBody(identityToken: identityToken, fullName: fullName), requiresAuth: false))
    }

    func me() async throws -> User {
        try await client.send(.get("/api/auth/me"))
    }

    /// Best effort: the local sign-out happens whatever the server answers.
    func logout() async {
        let endpoint = Endpoint<EmptyResponse>(method: .post, path: "/api/auth/logout")
        _ = try? await client.send(endpoint)
    }
}
