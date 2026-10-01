import Foundation
import Testing
@testable import UphillAI

@MainActor
struct AppModelTests {
    @Test func restoreLoadsUserForStoredToken() async throws {
        let response = try Fixture.decode(AuthResponse.self, "auth_login.json")
        let app = AppModel(tokenStore: InMemoryTokenStore("saved"), makeAuth: { _ in FakeAuthService(.success(response)) }, cache: .inMemory())
        #expect(app.session.state == .restoring)
        await app.restore()
        #expect(app.session.user == response.user)
    }

    @Test func restoreOfflineKeepsTokenAndReportsError() async {
        let tokens = InMemoryTokenStore("saved")
        let app = AppModel(tokenStore: tokens, makeAuth: { _ in FakeAuthService(.failure(.transport("offline"))) }, cache: .inMemory())
        await app.restore()
        #expect(app.session.state == .restoring)
        #expect(tokens.read() == "saved")
        #expect(app.restoreError == APIError.transport("offline").userMessage)
    }

    @Test func expiredTokenSignsOut() async {
        let tokens = InMemoryTokenStore("saved")
        let app = AppModel(tokenStore: tokens, makeAuth: { _ in FakeAuthService(.failure(.unauthorized)) }, cache: .inMemory())
        await app.restore()
        #expect(app.session.state == .signedOut)
        #expect(tokens.read() == nil)
    }

    @Test func unauthorizedFromAnyRequestSignsOut() async {
        let tokens = InMemoryTokenStore("saved")
        let base = StubURLProtocol.register { _ in (401, json(["detail": "Session expired or invalid."])) }
        let app = AppModel(tokenStore: tokens, baseURL: { base }, session: StubURLProtocol.session(), cache: .inMemory())
        let _: EmptyResponse? = try? await app.client.send(.get("/api/coach/active-plan"))
        #expect(app.session.state == .signedOut)
        #expect(tokens.read() == nil)
    }

    @Test func signOutCallsLogoutAndClearsSession() async throws {
        let response = try Fixture.decode(AuthResponse.self, "auth_login.json")
        let fake = FakeAuthService(.success(response))
        let app = AppModel(tokenStore: InMemoryTokenStore(), makeAuth: { _ in fake }, cache: .inMemory())
        app.session.didSignIn(response)
        await app.signOut()
        #expect(fake.calls.withLock { $0 } == ["logout"])
        #expect(app.session.state == .signedOut)
    }
    @Test func restoreOfflineUsesCachedUser() async throws {
        let user = try Fixture.decode(User.self, "auth_me.json")
        let cache = OfflineCache.inMemory()
        cache.save(user, as: .user)
        let app = AppModel(tokenStore: InMemoryTokenStore("saved"),
                           makeAuth: { _ in FakeAuthService(.failure(.transport("offline"))) },
                           cache: cache)
        await app.restore()
        #expect(app.session.user == user)
        #expect(app.isOffline)
    }

    @Test func signInCachesUserAndSignOutClearsCache() async throws {
        let response = try Fixture.decode(AuthResponse.self, "auth_login.json")
        let cache = OfflineCache.inMemory()
        let app = AppModel(tokenStore: InMemoryTokenStore(), makeAuth: { _ in FakeAuthService(.success(response)) }, cache: cache)
        app.session.didSignIn(response)
        #expect(cache.load(User.self, .user)?.value == response.user)
        await app.signOut()
        #expect(cache.load(User.self, .user) == nil)
    }
}
