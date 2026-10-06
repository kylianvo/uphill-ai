import GoogleSignIn
import UIKit

@MainActor
enum GoogleSignInProvider {
    enum Failure: Error { case noPresenter, noIDToken }

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
