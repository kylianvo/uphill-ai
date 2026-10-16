import Foundation
import Testing
@testable import UphillAI

struct NotificationServiceTests {
    @Test func clearingPauseSendsExplicitNull() async throws {
        let service = NotificationService(client: makeStubClient { request in
            #expect(request.httpMethod == "PATCH")
            let data = try #require(StubURLProtocol.bodyData(request))
            let body = try #require(JSONSerialization.jsonObject(with: data) as? [String: Any])
            #expect(body["paused_until"] is NSNull)
            return (200, data)
        })
        let value = try await service.updatePreferences(NotificationPreferences())
        #expect(!value.workoutsEnabled)
    }
    @Test func exactCardNeverFallsBackToBundledContent() async {
        let service = KnowledgeService(client: makeStubClient { request in
            #expect(request.url?.path == "/api/knowledge/cards/1")
            return (404, json(["detail": "Unavailable"]))
        })
        do {
            _ = try await service.fetchCard(id: 1, lang: "en")
            Issue.record("Missing server card must not return bundled card 1")
        } catch { }
    }
}
