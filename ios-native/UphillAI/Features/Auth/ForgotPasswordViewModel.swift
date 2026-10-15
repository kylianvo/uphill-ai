import Foundation
import Observation

@Observable
@MainActor
final class ForgotPasswordViewModel {
    enum Step { case email, code }

    var step: Step = .email
    var email: String
    var code = ""
    var newPassword = ""
    private(set) var isBusy = false
    private(set) var errorMessage: String?
    private(set) var resendAvailableAt: Date?

    private let auth: any AuthServicing
    private let session: SessionStore
    private let now: () -> Date

    init(auth: any AuthServicing, session: SessionStore, email: String = "", now: @escaping () -> Date = Date.init) {
        self.auth = auth
        self.session = session
        self.email = email
        self.now = now
    }

    private var trimmedEmail: String { email.trimmingCharacters(in: .whitespacesAndNewlines) }
    private var trimmedCode: String { code.trimmingCharacters(in: .whitespacesAndNewlines) }

    var canSendCode: Bool { !isBusy && trimmedEmail.contains("@") }
    var canReset: Bool { !isBusy && trimmedCode.count == 6 && newPassword.count >= 8 }

    func canResend(at date: Date) -> Bool {
        !isBusy && (resendAvailableAt.map { date >= $0 } ?? true)
    }

    func sendCode() async {
        isBusy = true
        errorMessage = nil
        defer { isBusy = false }
        do {
            try await auth.requestPasswordReset(email: trimmedEmail, lang: AppLanguage.code)
            step = .code
            resendAvailableAt = now().addingTimeInterval(60)
        } catch {
            errorMessage = L("Couldn't send the code. Check your connection and try again.")
        }
    }

    func reset() async {
        isBusy = true
        errorMessage = nil
        defer { isBusy = false }
        do {
            session.didSignIn(try await auth.resetPassword(email: trimmedEmail, code: trimmedCode, newPassword: newPassword))
        } catch APIError.http(status: 400, message: _, code: _) {
            errorMessage = L("That code is wrong or has expired. Request a new one.")
        } catch let error as APIError {
            errorMessage = error.userMessage
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

extension ForgotPasswordViewModel: Identifiable {}
