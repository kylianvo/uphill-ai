import Foundation
import Testing
@testable import UphillAI

private func body(_ request: URLRequest) throws -> [String: String] {
    let data = try #require(StubURLProtocol.bodyData(request))
    let object = try #require(try JSONSerialization.jsonObject(with: data) as? [String: Any])
    return object.compactMapValues { $0 as? String }
}

struct AuthServiceTests {
    @Test func loginPostsCredentialsWithoutToken() async throws {
        let fixture = try Fixture.data("auth_login.json")
        let service = AuthService(client: makeStubClient(token: "stale") { request in
            #expect(request.url?.path() == "/api/auth/login")
            #expect(request.httpMethod == "POST")
            #expect(request.value(forHTTPHeaderField: "Authorization") == nil)
            let sent = try body(request)
            #expect(sent == ["email": "a@b.c", "password": "secret123"])
            return (200, fixture)
        })
        let response = try await service.login(email: "a@b.c", password: "secret123")
        #expect(response.sessionToken == "fixture-session-token")
    }

    @Test func registerPostsNameEmailPassword() async throws {
        let fixture = try Fixture.data("auth_login.json")
        let service = AuthService(client: makeStubClient { request in
            #expect(request.url?.path() == "/api/auth/register")
            let sent = try body(request)
            #expect(sent == ["name": "Ana", "email": "a@b.c", "password": "secret123"])
            return (200, fixture)
        })
        _ = try await service.register(name: "Ana", email: "a@b.c", password: "secret123")
    }

    @Test func googleSendsCredential() async throws {
        let fixture = try Fixture.data("auth_login.json")
        let service = AuthService(client: makeStubClient { request in
            #expect(request.url?.path() == "/api/auth/google")
            let sent = try body(request)
            #expect(sent == ["credential": "gid"])
            return (200, fixture)
        })
        _ = try await service.signInWithGoogle(idToken: "gid")
    }

    @Test func appleSendsIdentityTokenAndName() async throws {
        let fixture = try Fixture.data("auth_login.json")
        let service = AuthService(client: makeStubClient { request in
            #expect(request.url?.path() == "/api/auth/apple")
            let sent = try body(request)
            #expect(sent == ["identity_token": "jwt", "full_name": "Ana Le"])
            return (200, fixture)
        })
        _ = try await service.signInWithApple(identityToken: "jwt", fullName: "Ana Le")
    }

    @Test func meUsesBearerToken() async throws {
        let fixture = try Fixture.data("auth_me.json")
        let service = AuthService(client: makeStubClient(token: "tok") { request in
            #expect(request.url?.path() == "/api/auth/me")
            #expect(request.value(forHTTPHeaderField: "Authorization") == "Bearer tok")
            return (200, fixture)
        })
        let user = try await service.me()
        #expect(user.email == "ios-fixtures@uphill.ai")
    }

    @Test func logoutIgnoresServerErrors() async {
        let service = AuthService(client: makeStubClient { _ in (500, Data()) })
        await service.logout()
    }
}
