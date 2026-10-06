import GoogleSignIn
import OSLog
import UIKit

@MainActor
enum GoogleSignInProvider {
    enum Failure: Error { case noPresenter, noIDToken }

    private static let log = Logger(subsystem: "ai.uphill.UphillAI", category: "google-signin")

    /// User-facing text for a failed Google sign-in, or nil when the user simply cancelled.
    /// Stays friendly but carries the GIDSignInError code so a report is diagnosable
    /// (e.g. -4 = no keychain auth, which is what an unsigned build produces).
    static func failureMessage(for error: Error) -> String? {
        if let failure = error as? Failure {
            switch failure {
            case .noPresenter: return "Google sign-in couldn't open. Please try again."
            case .noIDToken: return "Google didn't return a sign-in token. Please try again."
            }
        }
        let ns = error as NSError
        guard ns.domain == GIDSignInError.errorDomain else {
            return "Google sign-in failed (\(ns.domain) \(ns.code)). Please try again."
        }
        if ns.code == GIDSignInError.canceled.rawValue { return nil }
        return "Google sign-in failed (error \(ns.code)). Please try again."
    }

    /// Logs the underlying error (no tokens are ever part of it).
    static func logFailure(_ error: Error) {
        let ns = error as NSError
        log.error("Google sign-in failed: domain=\(ns.domain, privacy: .public) code=\(ns.code) \(ns.localizedDescription, privacy: .public)")
    }

    /// Presents Google sign-in and returns the ID token for /api/auth/google.
    /// Throws GIDSignInError.canceled when the user backs out.
    static func signIn() async throws -> String {
        let scenes = UIApplication.shared.connectedScenes
        let activeScene = scenes.first(where: { $0.activationState == .foregroundActive }) as? UIWindowScene
        let windowScene = activeScene ?? (scenes.first as? UIWindowScene)
        let window = windowScene?.windows.first(where: { $0.isKeyWindow }) ?? windowScene?.windows.first

        guard var presenter = window?.rootViewController ?? UIApplication.shared.connectedScenes
            .compactMap({ ($0 as? UIWindowScene)?.keyWindow?.rootViewController })
            .first
        else { throw Failure.noPresenter }

        while let presented = presenter.presentedViewController {
            presenter = presented
        }

        // Callback API: only a String crosses the continuation, because older Xcode
        // rejects sending the non-Sendable GIDSignInResult out of the async overload.
        let token: String = try await withCheckedThrowingContinuation { continuation in
            GIDSignIn.sharedInstance.signIn(withPresenting: presenter) { result, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                guard let token = result?.user.idToken?.tokenString else {
                    continuation.resume(throwing: Failure.noIDToken)
                    return
                }
                continuation.resume(returning: token)
            }
        }
        return token
    }
}
