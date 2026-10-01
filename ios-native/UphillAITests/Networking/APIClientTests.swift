import Foundation
import Synchronization
import Testing
@testable import UphillAI

private struct Thing: Decodable, Sendable, Equatable {
    let raceName: String
    let totalWeeks: Int
}

private struct ThingBody: Encodable {
    let raceName: String
}

struct APIClientTests {
    @Test func sendsBearerTokenAndDecodesSnakeCase() async throws {
        let client = makeStubClient(token: "abc") { request in
            #expect(request.value(forHTTPHeaderField: "Authorization") == "Bearer abc")
            #expect(request.url?.path() == "/api/things")
            #expect(request.httpMethod == "GET")
            return (200, json(["race_name": "VMM", "total_weeks": 12]))
        }
        let thing: Thing = try await client.send(.get("/api/things"))
        #expect(thing == Thing(raceName: "VMM", totalWeeks: 12))
    }

    @Test func omitsTokenWhenAuthNotRequired() async throws {
        let client = makeStubClient(token: "abc") { request in
            #expect(request.value(forHTTPHeaderField: "Authorization") == nil)
            return (200, json([:]))
        }
        let _: EmptyResponse = try await client.send(.get("/api/public", requiresAuth: false))
    }

    @Test func encodesBodyAsSnakeCaseJSON() async throws {
        let client = makeStubClient { request in
            let body = try #require(StubURLProtocol.bodyData(request))
            let object = try #require(try JSONSerialization.jsonObject(with: body) as? [String: String])
            #expect(object == ["race_name": "UTMB"])
            #expect(request.value(forHTTPHeaderField: "Content-Type") == "application/json")
            #expect(request.httpMethod == "POST")
            return (200, json([:]))
        }
        let _: EmptyResponse = try await client.send(.send(.post, "/api/things", body: ThingBody(raceName: "UTMB")))
    }

    @Test func unauthorizedCallsHandlerAndThrows() async {
        let called = Mutex(false)
        let client = makeStubClient(onUnauthorized: { called.withLock { $0 = true } }) { _ in
            (401, json(["detail": "Session expired or invalid."]))
        }
        await #expect(throws: APIError.unauthorized) {
            let _: EmptyResponse = try await client.send(.get("/api/auth/me"))
        }
        #expect(called.withLock { $0 })
    }

    @Test func parsesStringDetail() async {
        let client = makeStubClient { _ in (409, json(["detail": "An account with this email already exists."])) }
        await #expect(throws: APIError.http(status: 409, message: "An account with this email already exists.", code: nil)) {
            let _: EmptyResponse = try await client.send(.get("/api/x"))
        }
    }

    @Test func parsesGuardCodeDetail() async {
        let client = makeStubClient { _ in (422, json(["detail": ["code": "G3_past_date", "params": [:]]])) }
        await #expect(throws: APIError.http(status: 422, message: nil, code: "G3_past_date")) {
            let _: EmptyResponse = try await client.send(.get("/api/x"))
        }
    }

    @Test func badJSONIsDecodingError() async {
        let client = makeStubClient { _ in (200, Data("not json".utf8)) }
        await #expect {
            let _: Thing = try await client.send(.get("/api/things"))
        } throws: { error in
            if case APIError.decoding = error { return true }
            return false
        }
    }

    @Test func environmentSelection() {
        let defaults = UserDefaults(suiteName: "env-\(UUID().uuidString)")!
        #if DEBUG
        #expect(AppEnvironment.current(defaults: defaults) == .local)
        defaults.set("staging", forKey: AppEnvironment.defaultsKey)
        #expect(AppEnvironment.current(defaults: defaults) == .staging)
        #else
        #expect(AppEnvironment.current(defaults: defaults) == .production)
        #endif
        #expect(AppEnvironment.production.baseURL.absoluteString == "https://api.uphill-ai.io.vn")
        #expect(AppEnvironment.staging.baseURL.absoluteString == "https://staging-api.uphill-ai.io.vn")
    }
}
