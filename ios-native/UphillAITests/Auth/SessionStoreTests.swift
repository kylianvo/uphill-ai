import Foundation
import Testing
@testable import UphillAI

@MainActor
struct SessionStoreTests {
    private func user() throws -> User { try Fixture.decode(User.self, "auth_me.json") }

    @Test func startsSignedOutWithoutToken() {
        let session = SessionStore(tokenStore: InMemoryTokenStore())
        #expect(session.state == .signedOut)
    }

    @Test func startsRestoringWithStoredToken() {
        let session = SessionStore(tokenStore: InMemoryTokenStore("saved"))
        #expect(session.state == .restoring)
    }

    @Test func signInStoresTokenAndUser() throws {
        let tokens = InMemoryTokenStore()
        let session = SessionStore(tokenStore: tokens)
        let u = try user()
        session.didSignIn(AuthResponse(sessionToken: "new", user: u))
        #expect(tokens.read() == "new")
        #expect(session.state == .signedIn(u))
        #expect(session.user == u)
    }

    @Test func signOutClearsToken() throws {
        let tokens = InMemoryTokenStore("saved")
        let session = SessionStore(tokenStore: tokens)
        session.setUser(try user())
        session.signOut()
        #expect(tokens.read() == nil)
        #expect(session.state == .signedOut)
        #expect(session.user == nil)
    }
}
