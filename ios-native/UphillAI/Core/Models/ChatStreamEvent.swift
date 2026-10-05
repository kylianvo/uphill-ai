import Foundation

/// Models an individual source citation returned in a citations event or message details.
public struct CitationItem: Codable, Sendable, Equatable, Identifiable {
    public var id: String { sourceId ?? ref ?? "\(book ?? "")-\(chapter ?? "")-\(title ?? "")" }

    public let ref: String?
    public let sourceId: String?
    public let title: String?
    public let book: String?
    public let chapter: String?
    public let chapterNum: Int?
    public let chapterTitle: String?
    public let section: String?
    public let topic: String?
    public let citationLabel: String?
    public let sourceLabel: String?
    public let url: String?
    public let domain: String?
    public let quote: String?

    public init(
        ref: String? = nil,
        sourceId: String? = nil,
        title: String? = nil,
        book: String? = nil,
        chapter: String? = nil,
        chapterNum: Int? = nil,
        chapterTitle: String? = nil,
        section: String? = nil,
        topic: String? = nil,
        citationLabel: String? = nil,
        sourceLabel: String? = nil,
        url: String? = nil,
        domain: String? = nil,
        quote: String? = nil
    ) {
        self.ref = ref
        self.sourceId = sourceId
        self.title = title
        self.book = book
        self.chapter = chapter
        self.chapterNum = chapterNum
        self.chapterTitle = chapterTitle
        self.section = section
        self.topic = topic
        self.citationLabel = citationLabel
        self.sourceLabel = sourceLabel
        self.url = url
        self.domain = domain
        self.quote = quote
    }
}

/// Typed Server-Sent Events emitted by `/api/coach/chat/stream`.
public enum ChatStreamEvent: Sendable, Equatable {
    case status(step: String, requestId: String)
    case token(text: String)
    case citations(citations: [CitationItem], evidenceStatus: String)
    case toolCall(id: String, name: String, args: [String: JSONValue])
    case toolResult(id: String, name: String, status: String, cardType: String?, cardData: [String: JSONValue]?)
    case clarify(prompt: String, options: [String])
    case done(requestId: String, messageId: Int?, replayed: Bool)
    case error(code: String, message: String?)
}
