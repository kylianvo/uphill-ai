import Foundation

enum ChatRole: String, Codable, Sendable, Equatable {
    case user
    case assistant
}

struct ToolResultPayload: Codable, Sendable, Equatable, Identifiable {
    var id: String { toolCallId }
    let toolCallId: String
    let name: String
    let status: String
    let cardType: String?
    let cardData: [String: JSONValue]?

    init(
        toolCallId: String,
        name: String,
        status: String = "success",
        cardType: String? = nil,
        cardData: [String: JSONValue]? = nil
    ) {
        self.toolCallId = toolCallId
        self.name = name
        self.status = status
        self.cardType = cardType
        self.cardData = cardData
    }

    enum CodingKeys: String, CodingKey {
        case toolCallId
        case name
        case status
        case cardType
        case cardData
    }
}

struct ChatMessage: Codable, Sendable, Equatable, Identifiable {
    let id: String
    let numericId: Int?
    let role: ChatRole
    var content: String
    let createdAt: String?
    let requestId: String?
    var citations: [CitationItem]?
    var evidenceStatus: String?
    var interrupted: Bool?
    var toolCalls: [ToolResultPayload]?
    var feedback: Int?

    init(
        id: String = UUID().uuidString,
        numericId: Int? = nil,
        role: ChatRole,
        content: String,
        createdAt: String? = nil,
        requestId: String? = nil,
        citations: [CitationItem]? = nil,
        evidenceStatus: String? = nil,
        interrupted: Bool? = nil,
        toolCalls: [ToolResultPayload]? = nil,
        feedback: Int? = nil
    ) {
        self.id = id
        self.numericId = numericId
        self.role = role
        self.content = content
        self.createdAt = createdAt
        self.requestId = requestId
        self.citations = citations
        self.evidenceStatus = evidenceStatus
        self.interrupted = interrupted
        self.toolCalls = toolCalls
        self.feedback = feedback
    }

    enum CodingKeys: String, CodingKey {
        case id
        case numericId = "messageId"
        case role
        case content
        case createdAt
        case requestId
        case citations
        case evidenceStatus
        case interrupted
        case toolCalls
        case feedback
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)

        if let intId = try? container.decode(Int.self, forKey: .id) {
            self.id = String(intId)
            self.numericId = intId
        } else if let strId = try? container.decode(String.self, forKey: .id) {
            self.id = strId
            self.numericId = try? container.decode(Int.self, forKey: .numericId)
        } else {
            self.id = UUID().uuidString
            self.numericId = nil
        }

        self.role = try container.decode(ChatRole.self, forKey: .role)
        self.content = try container.decode(String.self, forKey: .content)
        self.createdAt = try? container.decode(String.self, forKey: .createdAt)
        self.requestId = try? container.decode(String.self, forKey: .requestId)
        self.citations = try? container.decode([CitationItem].self, forKey: .citations)
        self.evidenceStatus = try? container.decode(String.self, forKey: .evidenceStatus)
        self.interrupted = try? container.decode(Bool.self, forKey: .interrupted)
        self.toolCalls = try? container.decode([ToolResultPayload].self, forKey: .toolCalls)
        self.feedback = try? container.decode(Int.self, forKey: .feedback)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        if let numericId {
            try container.encode(numericId, forKey: .numericId)
        }
        try container.encode(role, forKey: .role)
        try container.encode(content, forKey: .content)
        try container.encodeIfPresent(createdAt, forKey: .createdAt)
        try container.encodeIfPresent(requestId, forKey: .requestId)
        try container.encodeIfPresent(citations, forKey: .citations)
        try container.encodeIfPresent(evidenceStatus, forKey: .evidenceStatus)
        try container.encodeIfPresent(interrupted, forKey: .interrupted)
        try container.encodeIfPresent(toolCalls, forKey: .toolCalls)
        try container.encodeIfPresent(feedback, forKey: .feedback)
    }
}

struct ChatThreadResponse: Codable, Sendable, Equatable {
    let messages: [ChatMessage]
    let summary: String?
    let hasMore: Bool
    let oldestId: Int?
    let proposals: [String: String]?

    init(
        messages: [ChatMessage],
        summary: String? = nil,
        hasMore: Bool = false,
        oldestId: Int? = nil,
        proposals: [String: String]? = nil
    ) {
        self.messages = messages
        self.summary = summary
        self.hasMore = hasMore
        self.oldestId = oldestId
        self.proposals = proposals
    }
}

struct MessageSourcesResponse: Codable, Sendable, Equatable {
    let messageId: Int
    let citations: [CitationItem]
    let evidence: [JSONValue]
    let evidenceStatus: String

    init(
        messageId: Int,
        citations: [CitationItem] = [],
        evidence: [JSONValue] = [],
        evidenceStatus: String = "empty"
    ) {
        self.messageId = messageId
        self.citations = citations
        self.evidence = evidence
        self.evidenceStatus = evidenceStatus
    }
}
