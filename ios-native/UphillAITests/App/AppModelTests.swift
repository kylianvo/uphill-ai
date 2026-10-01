import Foundation
import Testing
@testable import UphillAI

@MainActor
struct AppModelTests {
    @Test func restoreLoadsUserForStoredToken() async throws {
        let response = try Fixture.decode(AuthResponse.self, "auth_login.json")
        let app = AppModel(tokenStore: InMemoryTokenStore("saved"), makeAuth: { _ in FakeAuthService(.success(response)) })
        #expect(app.session.state == .restoring)
        await app.restore()
        #expect(app.session.user == response.user)
    }

    @Test func restoreOfflineKeepsTokenAndReportsError() async {
        let tokens = InMemoryTokenStore("saved")
        let app = AppModel(tokenStore: tokens, makeAuth: { _ in FakeAuthService(.failure(.transport("offline"))) })
        await app.restore()
        #expect(app.session.state == .restoring)
        #expect(tokens.read() == "saved")
        #expect(app.restoreError == APIError.transport("offline").userMessage)
    }

    @Test func expiredTokenSignsOut() async {
        let tokens = InMemoryTokenStore("saved")
        let app = AppModel(tokenStore: tokens, makeAuth: { _ in FakeAuthService(.failure(.unauthorized)) })
        await app.restore()
        #expect(app.session.state == .signedOut)
        #expect(tokens.read() == nil)
    }

    @Test func unauthorizedFromAnyRequestSignsOut() async {
        let tokens = InMemoryTokenStore("saved")
        let base = StubURLProtocol.register { _ in (401, json(["detail": "Session expired or invalid."])) }
        let app = AppModel(tokenStore: tokens, baseURL: { base }, session: StubURLProtocol.session())
        let _: EmptyResponse? = try? await app.client.send(.get("/api/coach/active-plan"))
        #expect(app.session.state == .signedOut)
        #expect(tokens.read() == nil)
    }

    @Test func signOutCallsLogoutAndClearsSession() async throws {
        let response = try Fixture.decode(AuthResponse.self, "auth_login.json")
        let fake = FakeAuthService(.success(response))
        let app = AppModel(tokenStore: InMemoryTokenStore(), makeAuth: { _ in fake })
        app.session.didSignIn(response)
        await app.signOut()
        #expect(fake.calls.withLock { $0 } == ["logout"])
        #expect(app.session.state == .signedOut)
    }
}
