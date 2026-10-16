import Foundation
import Testing
@testable import UphillAI

struct NotificationRoutingTests {
    @Test func rejectsUnknownVersionAndUnnamespacedCard() {
        #expect(NotificationRoute(payload: ["v": 99, "destination": ["kind": "plan", "plan_id": 1]]) == nil)
        #expect(NotificationRoute(payload: ["v": 1, "destination": ["kind": "knowledge", "card_id": 1, "lang": "en"]]) == nil)
    }
    @Test func workoutRequiresBothPositiveIdentifiers() {
        #expect(NotificationRoute(payload: ["v": 1, "destination": ["kind": "workout", "plan_id": 2, "workout_id": 3]])?.workoutId == 3)
        #expect(NotificationRoute(payload: ["v": 1, "destination": ["kind": "workout", "plan_id": 2]]) == nil)
    }
    @Test func serverCardIsDistinctFromBundledCard() {
        #expect(NotificationRoute(payload: ["v": 1, "destination": ["kind": "knowledge", "card_id": 1, "lang": "en", "namespace": "server"]])?.cardId == 1)
    }
}

struct NotificationScopeTests {
    @Test @MainActor func exitingAthleteScopeFinishesBeforeReturning() async {
        let base = StubURLProtocol.register { _ in (200, json(["active": false])) }
        let app = AppModel(tokenStore: InMemoryTokenStore("test"), baseURL: { base }, session: StubURLProtocol.session(), cache: .inMemory())
        await app.plan.setAthleteScope(123)
        #expect(app.plan.athleteId == 123)
        await app.exitAthleteView()
        #expect(app.plan.athleteId == nil)
    }
}
