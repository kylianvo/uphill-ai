import Foundation

struct KnowledgeSource: Codable, Sendable, Identifiable, Equatable {
    let id: Int
    let title: String
    let type: String // "pdf", "youtube", "web"
    let url: String?

    init(id: Int, title: String, type: String, url: String? = nil) {
        self.id = id
        self.title = title
        self.type = type
        self.url = url
    }
}

struct KnowledgeExtractionStatus: Codable, Sendable, Equatable {
    let status: String
    let currentTopic: String?
    let progress: Int?
    let total: Int?
    let cardCount: Int?

    init(
        status: String = "idle",
        currentTopic: String? = nil,
        progress: Int? = nil,
        total: Int? = nil,
        cardCount: Int? = nil
    ) {
        self.status = status
        self.currentTopic = currentTopic
        self.progress = progress
        self.total = total
        self.cardCount = cardCount
    }

    enum CodingKeys: String, CodingKey {
        case status
        case currentTopic = "current_topic"
        case progress
        case total
        case cardCount = "card_count"
    }
}
