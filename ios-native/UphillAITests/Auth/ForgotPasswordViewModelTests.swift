import Foundation
import Testing
@testable import UphillAI

@MainActor
struct ForgotPasswordViewModelTests {
    private func success() throws -> AuthResponse { try Fixture.decode(AuthResponse.self, "auth_login.json") }
    private let start = Date(timeIntervalSince1970: 1_000_000)

    private func make(_ auth: FakeAuthService, session: SessionStore? = nil) -> ForgotPasswordViewModel {
        ForgotPasswordViewModel(auth: auth, session: session ?? SessionStore(tokenStore: InMemoryTokenStore()),
                                email: "  ana@example.com ", now: { self.start })
    }

    @Test func sendCodeTrimsEmailAndMovesToCodeStep() async throws {
        let auth = FakeAuthService(.success(try success()))
        let model = make(auth)
        await model.sendCode()
        #expect(auth.calls.withLock { $0 } == ["forgot ana@example.com \(AppLanguage.code)"])
        #expect(model.step == .code)
        #expect(model.canResend(at: start.addingTimeInterval(59)) == false)
        #expect(model.canResend(at: start.addingTimeInterval(60)) == true)
    }

    @Test func sendCodeFailureStaysOnEmailStep() async {
        let model = make(FakeAuthService(.failure(.http(status: 500, message: nil, code: nil))))
        await model.sendCode()
        #expect(model.step == .email)
        #expect(model.errorMessage != nil)
    }

    @Test func resetTrimsCodeAndSignsIn() async throws {
        let auth = FakeAuthService(.success(try success()))
        let session = SessionStore(tokenStore: InMemoryTokenStore())
        let model = make(auth, session: session)
        model.step = .code
        model.code = " 012345 "
        model.newPassword = "secret123"
        await model.reset()
        #expect(auth.calls.withLock { $0 } == ["reset ana@example.com 012345"])
        #expect(session.user != nil)
        #expect(model.errorMessage == nil)
    }

    @Test func rejectedCodeShowsInvalidMessage() async {
        let model = make(FakeAuthService(.failure(.http(status: 400, message: "Invalid or expired code.", code: nil))))
        model.step = .code
        model.code = "000000"
        model.newPassword = "secret123"
        await model.reset()
        #expect(model.errorMessage == L("That code is wrong or has expired. Request a new one."))
    }

    @Test func canResetNeedsSixDigitCodeAndEightCharPassword() {
        let model = make(FakeAuthService(.failure(.unauthorized)))
        model.code = "12345"
        model.newPassword = "longenough"
        #expect(model.canReset == false)
        model.code = "123456"
        model.newPassword = "short"
        #expect(model.canReset == false)
        model.newPassword = "longenough"
        #expect(model.canReset == true)
    }
}
