import GoogleSignIn
import UIKit

@MainActor
enum GoogleSignInProvider {
    enum Failure: Error { case noPresenter, noIDToken }

    /// Presents Google's sign-in and returns the ID token for /api/auth/google.
    /// Throws GIDSignInError.canceled when the user backs out.
    static func signIn() async throws -> String {
        guard let presenter = UIApplication.shared.connectedScenes
            .compactMap({ ($0 as? UIWindowScene)?.keyWindow?.rootViewController })
            .first
        else { throw Failure.noPresenter }
        let result = try await GIDSignIn.sharedInstance.signIn(withPresenting: presenter)
        guard let token = result.user.idToken?.tokenString else { throw Failure.noIDToken }
        return token
    }
}
