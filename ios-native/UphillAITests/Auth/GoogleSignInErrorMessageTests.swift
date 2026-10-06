import Foundation
import GoogleSignIn
import Testing
@testable import UphillAI

@MainActor
struct GoogleSignInErrorMessageTests {
    private func gid(_ code: GIDSignInError.Code) -> NSError {
        NSError(domain: GIDSignInError.errorDomain, code: code.rawValue)
    }

    @Test func cancelIsSilent() {
        #expect(GoogleSignInProvider.failureMessage(for: gid(.canceled)) == nil)
    }

    @Test func otherGoogleErrorsIncludeTheCode() throws {
        let message = try #require(GoogleSignInProvider.failureMessage(for: gid(.hasNoAuthInKeychain)))
        #expect(message.contains("\(GIDSignInError.Code.hasNoAuthInKeychain.rawValue)"))
        #expect(message.contains("Please try again"))
    }

    @Test func nonGoogleErrorsAreStillFriendlyAndCoded() throws {
        let message = try #require(GoogleSignInProvider.failureMessage(for: NSError(domain: "NSURLErrorDomain", code: -1009)))
        #expect(message.contains("-1009"))
    }

    @Test func providerFailuresHaveOwnCopy() throws {
        #expect(try #require(GoogleSignInProvider.failureMessage(for: GoogleSignInProvider.Failure.noIDToken)).contains("token"))
    }
}
