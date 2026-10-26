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
    @Test func switchWritesAllThreeCategories() async throws {
        let service = NotificationService(client: makeStubClient { request in
            let data = try #require(StubURLProtocol.bodyData(request))
            let body = try #require(JSONSerialization.jsonObject(with: data) as? [String: Any])
            #expect(body["workouts_enabled"] as? Bool == true && body["coaching_enabled"] as? Bool == true && body["results_enabled"] as? Bool == true)
            return (200, data)
        })
        let coordinator = await NotificationCoordinator(service: service, defaults: UserDefaults(suiteName: "switch-\(UUID())")!)
        await MainActor.run { coordinator.userID = 1 }
        await coordinator.setEnabled(true, requestPermission: false)
        await MainActor.run { #expect(coordinator.preferences.workoutsEnabled && coordinator.preferences.resultsEnabled) }
    }
    @Test func unmuteSendsShrunkList() async throws {
        let service = NotificationService(client: makeStubClient { request in
            let data = try #require(StubURLProtocol.bodyData(request))
            let body = try #require(JSONSerialization.jsonObject(with: data) as? [String: Any])
            #expect(body["muted_kinds"] as? [String] == ["week_brief"])
            return (200, data)
        })
        let coordinator = await NotificationCoordinator(service: service, defaults: UserDefaults(suiteName: "unmute-\(UUID())")!)
        await MainActor.run { coordinator.userID = 1; coordinator.preferences.mutedKinds = ["week_brief", "knowledge"] }
        await coordinator.unmute("knowledge")
        await MainActor.run { #expect(coordinator.preferences.mutedKinds == ["week_brief"]) }
    }
    @Test func feedbackPostsLess() async throws {
        let id = UUID()
        let service = NotificationService(client: makeStubClient { request in
            #expect(request.httpMethod == "POST" && request.url?.path == "/api/notifications/\(id.uuidString)/feedback")
            let data = try #require(StubURLProtocol.bodyData(request))
            let body = try #require(JSONSerialization.jsonObject(with: data) as? [String: Any])
            #expect(body["less"] as? Bool == true)
            return (200, json([:]))
        })
        try await service.feedback(id: id)
    }
    @Test func adaptIntentRouteIsValid() {
        let route = NotificationRoute(payload: ["v": 1, "destination": ["kind": "plan", "plan_id": 1, "week_number": 2, "intent": "adapt"]])
        #expect(route?.intent == "adapt" && route?.weekNumber == 2)
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
