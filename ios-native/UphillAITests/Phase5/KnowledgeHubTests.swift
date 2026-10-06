import Testing
import Foundation
@testable import UphillAI

@Suite("KnowledgeHubTests")
struct KnowledgeHubTests {

    @Test func testFetchCuratedCards() async throws {
        let client = makeStubClient { _ in (404, json(["detail": "not found"])) }
        let service = KnowledgeService(client: client)

        let allCards = try await service.fetchCards(topic: "All", lang: "en")
        #expect(!allCards.isEmpty)
        #expect(allCards.contains { $0.topic == "Training" })
        #expect(allCards.contains { $0.topic == "Nutrition" })

        let nutritionCards = try await service.fetchCards(topic: "Nutrition", lang: "en")
        #expect(!nutritionCards.isEmpty)
        #expect(nutritionCards.allSatisfy { $0.topic == "Nutrition" })
    }

    @Test func testFetchRandomCards() async throws {
        let client = makeStubClient { _ in (404, json(["detail": "not found"])) }
        let service = KnowledgeService(client: client)

        let randomCards = try await service.fetchRandomCards(count: 2, lang: "en")
        #expect(randomCards.count == 2)
    }

    @Test func testFetchTopics() async throws {
        let client = makeStubClient { _ in (404, json(["detail": "not found"])) }
        let service = KnowledgeService(client: client)

        let topics = try await service.fetchTopics()
        #expect(topics.contains("Training"))
        #expect(topics.contains("Nutrition"))
        #expect(topics.contains("Pacing"))
    }
}
