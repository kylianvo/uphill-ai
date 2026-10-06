import Foundation
import Testing
@testable import UphillAI

@MainActor
struct SignInViewModelTests {
    private func success() throws -> AuthResponse { try Fixture.decode(AuthResponse.self, "auth_login.json") }

    @Test func emailSignInTrimsEmailAndSignsIn() async throws {
        let auth = FakeAuthService(.success(try success()))
        let session = SessionStore(tokenStore: InMemoryTokenStore())
        let model = SignInViewModel(auth: auth, session: session)
        model.email = "  ana@example.com "
        model.password = "secret123"
        await model.submitEmail()
        #expect(auth.calls.withLock { $0 } == ["login ana@example.com"])
        #expect(session.user != nil)
        #expect(model.errorMessage == nil)
        #expect(model.isBusy == false)
    }

    @Test func registerModeCallsRegister() async throws {
        let auth = FakeAuthService(.success(try success()))
        let model = SignInViewModel(auth: auth, session: SessionStore(tokenStore: InMemoryTokenStore()))
        model.mode = .register
        model.name = "Ana"
        model.email = "ana@example.com"
        model.password = "secret123"
        await model.submitEmail()
        #expect(auth.calls.withLock { $0 } == ["register Ana ana@example.com"])
    }

    @Test func canSubmitNeedsEmailAndEightCharPasswordAndNameWhenRegistering() {
        let model = SignInViewModel(auth: FakeAuthService(.failure(.unauthorized)),
                                    session: SessionStore(tokenStore: InMemoryTokenStore()))
        #expect(model.canSubmit == false)
        model.email = "ana@example.com"
        model.password = "short"
        #expect(model.canSubmit == false)
        model.password = "longenough"
        #expect(model.canSubmit == true)
        model.mode = .register
        #expect(model.canSubmit == false)
        model.name = "Ana"
        #expect(model.canSubmit == true)
    }

    @Test func failureShowsServerMessage() async {
        let auth = FakeAuthService(.failure(.http(status: 401, message: "Invalid email or password.", code: nil)))
        let session = SessionStore(tokenStore: InMemoryTokenStore())
        let model = SignInViewModel(auth: auth, session: session)
        model.email = "ana@example.com"
        model.password = "wrongpass"
        await model.submitEmail()
        #expect(model.errorMessage == "Invalid email or password.")
        #expect(session.state == .signedOut)
    }

    @Test func appleAndGoogleForwardTokens() async throws {
        let auth = FakeAuthService(.success(try success()))
        let model = SignInViewModel(auth: auth, session: SessionStore(tokenStore: InMemoryTokenStore()))
        await model.completeApple(identityToken: "jwt", fullName: "Ana Le")
        await model.completeGoogle(idToken: "gid")
        #expect(auth.calls.withLock { $0 } == ["apple jwt Ana Le", "google gid"])
    }

    @Test func returnWalksNameEmailPasswordThenSubmits() {
        let model = SignInViewModel(auth: FakeAuthService(.failure(.unauthorized)),
                                    session: SessionStore(tokenStore: InMemoryTokenStore()))
        #expect(model.returnAction(in: .name) == .focus(.email))
        #expect(model.returnAction(in: .email) == .focus(.password))
        #expect(model.returnAction(in: .password) == .none)  // form not valid yet
        model.email = "ana@example.com"
        model.password = "longenough"
        #expect(model.returnAction(in: .password) == .submit)
    }
}
