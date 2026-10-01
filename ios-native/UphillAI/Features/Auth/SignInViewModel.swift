import Foundation
import Observation

@Observable
@MainActor
final class SignInViewModel {
    enum Mode { case signIn, register }

    var mode: Mode = .signIn
    var name = ""
    var email = ""
    var password = ""
    private(set) var isBusy = false
    private(set) var errorMessage: String?

    private let auth: any AuthServicing
    private let session: SessionStore

    init(auth: any AuthServicing, session: SessionStore) {
        self.auth = auth
        self.session = session
    }

    private var trimmedEmail: String { email.trimmingCharacters(in: .whitespacesAndNewlines) }
    private var trimmedName: String { name.trimmingCharacters(in: .whitespacesAndNewlines) }

    var canSubmit: Bool {
        guard !isBusy, trimmedEmail.contains("@"), password.count >= 8 else { return false }
        return mode == .signIn || !trimmedName.isEmpty
    }

    func submitEmail() async {
        let email = trimmedEmail, name = trimmedName, password = password, mode = mode
        await run {
            switch mode {
            case .signIn: try await self.auth.login(email: email, password: password)
            case .register: try await self.auth.register(name: name, email: email, password: password)
            }
        }
    }

    func completeGoogle(idToken: String) async {
        await run { try await self.auth.signInWithGoogle(idToken: idToken) }
    }

    func completeApple(identityToken: String, fullName: String?) async {
        await run { try await self.auth.signInWithApple(identityToken: identityToken, fullName: fullName) }
    }

    func show(_ message: String) {
        errorMessage = message
    }

    private func run(_ operation: () async throws -> AuthResponse) async {
        isBusy = true
        errorMessage = nil
        defer { isBusy = false }
        do {
            session.didSignIn(try await operation())
        } catch let error as APIError {
            errorMessage = error.userMessage
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
