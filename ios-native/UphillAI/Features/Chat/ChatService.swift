import Foundation
import Observation

enum ChatTurnStatus: String, Sendable, Equatable {
    case idle
    case admitting
    case retrieving
    case generating
    case interrupted
    case error
    case done
}

struct ChatError: Sendable, Equatable, Identifiable {
    var id: String { code }
    let code: String
    let message: String?
}

struct ActiveRequestState: Sendable, Equatable {
    let requestId: String
    let retryOf: String?
}

private struct ChatStreamRequestBody: Encodable {
    let requestId: String
    let message: String?
    let retryOf: String?
    let lang: String
    let clientToday: String?

    enum CodingKeys: String, CodingKey {
        case requestId = "request_id"
        case message
        case retryOf = "retry_of"
        case lang
        case clientToday = "client_today"
    }
}

private struct FeedbackRequestBody: Encodable {
    let value: Int
}

private struct ProposalApplyBody: Encodable {
    let clientToday: String?

    enum CodingKeys: String, CodingKey {
        case clientToday = "client_today"
    }
}

private struct TurnStatusResponse: Decodable {
    let requestId: String?
    let resultMessageId: Int?

    enum CodingKeys: String, CodingKey {
        case requestId = "request_id"
        case resultMessageId = "result_message_id"
    }
}

@Observable
@MainActor
final class ChatService {
    private(set) var messages: [ChatMessage] = []
    private(set) var activeRequest: ActiveRequestState?
    private(set) var status: ChatTurnStatus = .idle
    private(set) var error: ChatError?
    private(set) var hasMore: Bool = false
    private(set) var isLoadingOlder: Bool = false
    private(set) var clarifyOptions: [String]? = nil
    private(set) var proposalStates: [Int: String] = [:]
    private(set) var selectedMessageSources: MessageSourcesResponse? = nil
    private(set) var isExecuting: Bool = false

    private let client: APIClient
    private let store: any ChatStore
    private let parser: SSEStreamParser
    private var activePlanId: Int?
    private var currentStreamTask: Task<Void, Never>?

    init(
        client: APIClient,
        store: any ChatStore = UserDefaultsChatStore(),
        parser: SSEStreamParser = SSEStreamParser()
    ) {
        self.client = client
        self.store = store
        self.parser = parser
    }

    func loadInitial(planId: Int?) async {
        self.activePlanId = planId
        if messages.isEmpty {
            let cached = store.loadMessages(for: planId ?? 0)
            if !cached.isEmpty {
                self.messages = cached
            }
        }

        do {
            let response: ChatThreadResponse = try await client.send(.get("/api/coach/chat/thread", query: [URLQueryItem(name: "limit", value: "50")]))
            self.messages = response.messages
            self.hasMore = response.hasMore
            if let p = response.proposals {
                var map: [Int: String] = [:]
                for (k, v) in p {
                    if let id = Int(k) { map[id] = v }
                }
                self.proposalStates = map
            }
            store.saveMessages(response.messages, for: planId ?? 0)
        } catch {
            // Keep cached messages on network failure
        }
    }

    func loadOlder() async {
        guard !isLoadingOlder, hasMore, let oldestId = messages.first?.numericId else { return }
        isLoadingOlder = true
        defer { isLoadingOlder = false }

        do {
            let response: ChatThreadResponse = try await client.send(.get("/api/coach/chat/thread", query: [
                URLQueryItem(name: "limit", value: "50"),
                URLQueryItem(name: "before_id", value: String(oldestId))
            ]))
            self.messages = response.messages + self.messages
            self.hasMore = response.hasMore
            if let planId = activePlanId {
                store.saveMessages(self.messages, for: planId)
            }
        } catch {
            // Silent error on pagination
        }
    }

    func send(text: String, clientToday: String? = nil, lang: String = AppLanguage.code) async {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty, !isExecuting else { return }

        let reqId = UUID().uuidString
        let userMsg = ChatMessage(role: .user, content: trimmed, requestId: reqId)
        messages.append(userMsg)
        clarifyOptions = nil
        error = nil

        await executeStream(requestId: reqId, message: trimmed, retryOf: nil, clientToday: clientToday, lang: lang)
    }

    func retry(rootRequestId: String, clientToday: String? = nil, lang: String = AppLanguage.code) async {
        guard !rootRequestId.isEmpty, !isExecuting else { return }

        let newReqId = UUID().uuidString
        clarifyOptions = nil
        error = nil

        await executeStream(requestId: newReqId, message: nil, retryOf: rootRequestId, clientToday: clientToday, lang: lang)
    }

    private func executeStream(requestId: String, message: String?, retryOf: String?, clientToday: String?, lang: String) async {
        isExecuting = true
        status = .admitting
        activeRequest = ActiveRequestState(requestId: requestId, retryOf: retryOf)

        let body = ChatStreamRequestBody(
            requestId: requestId,
            message: message,
            retryOf: retryOf,
            lang: lang,
            clientToday: clientToday
        )

        var assistantCreated = false

        do {
            let endpoint: Endpoint<EmptyResponse> = try Endpoint.send(.post, "/api/coach/chat/stream", body: body)
            let (bytes, _) = try await client.stream(endpoint)

            for try await event in parser.parse(bytes: bytes) {
                switch event {
                case let .status(step, _):
                    if step == "retrieving" {
                        self.status = .retrieving
                    } else if step == "generating" {
                        self.status = .generating
                    }

                case let .token(tokenText):
                    self.status = .generating
                    if !assistantCreated {
                        assistantCreated = true
                        let assistantMsg = ChatMessage(
                            role: .assistant,
                            content: tokenText,
                            requestId: requestId
                        )
                        self.messages.append(assistantMsg)
                    } else if let lastIdx = self.messages.indices.last, self.messages[lastIdx].role == .assistant {
                        self.messages[lastIdx].content += tokenText
                    }

                case let .citations(citations, evidenceStatus):
                    if let lastIdx = self.messages.indices.last, self.messages[lastIdx].role == .assistant {
                        self.messages[lastIdx].citations = citations
                        self.messages[lastIdx].evidenceStatus = evidenceStatus
                    }

                case .toolCall:
                    break

                case let .toolResult(toolCallId, name, statusStr, cardType, cardData):
                    let toolPayload = ToolResultPayload(
                        toolCallId: toolCallId,
                        name: name,
                        status: statusStr,
                        cardType: cardType,
                        cardData: cardData
                    )
                    if let lastIdx = self.messages.indices.last, self.messages[lastIdx].role == .assistant {
                        var existing = self.messages[lastIdx].toolCalls ?? []
                        existing.append(toolPayload)
                        self.messages[lastIdx].toolCalls = existing
                    }
                    if cardType == "schedule_proposal", let pId = cardData?["proposal_id"]?.intValue {
                        self.proposalStates[pId] = cardData?["status"]?.stringValue ?? "proposed"
                    }

                case let .clarify(_, options):
                    self.clarifyOptions = options

                case let .done(_, messageId, _):
                    if let lastIdx = self.messages.indices.last, self.messages[lastIdx].role == .assistant {
                        if let mid = messageId {
                            let updated = ChatMessage(
                                id: String(mid),
                                numericId: mid,
                                role: .assistant,
                                content: self.messages[lastIdx].content,
                                createdAt: self.messages[lastIdx].createdAt,
                                requestId: self.messages[lastIdx].requestId,
                                citations: self.messages[lastIdx].citations,
                                evidenceStatus: self.messages[lastIdx].evidenceStatus,
                                interrupted: false,
                                toolCalls: self.messages[lastIdx].toolCalls,
                                feedback: self.messages[lastIdx].feedback
                            )
                            self.messages[lastIdx] = updated
                        }
                    }
                    self.status = .done
                    self.activeRequest = nil
                    self.isExecuting = false
                    if let planId = self.activePlanId {
                        self.store.saveMessages(self.messages, for: planId)
                    }

                case let .error(code, msg):
                    self.status = .error
                    self.error = ChatError(code: code, message: msg)
                    self.activeRequest = nil
                    self.isExecuting = false
                    if let lastIdx = self.messages.indices.last, self.messages[lastIdx].role == .assistant, !self.messages[lastIdx].content.isEmpty {
                        self.messages[lastIdx].interrupted = true
                    }
                }
            }
        } catch {
            let isAborted = (error as? SSEStreamError) == .streamAborted
            let errCode = isAborted ? "stream_aborted" : "network_error"
            self.error = ChatError(code: errCode, message: error.localizedDescription)
            self.status = .interrupted
            self.activeRequest = nil
            self.isExecuting = false
            if let lastIdx = self.messages.indices.last, self.messages[lastIdx].role == .assistant, !self.messages[lastIdx].content.isEmpty {
                self.messages[lastIdx].interrupted = true
            }
        }
    }

    func clear() async -> Bool {
        do {
            let _: EmptyResponse = try await client.send(.delete("/api/coach/chat/thread"))
            self.messages = []
            self.activeRequest = nil
            self.status = .idle
            self.error = nil
            self.hasMore = false
            self.clarifyOptions = nil
            self.proposalStates = [:]
            if let planId = activePlanId {
                store.clearMessages(for: planId)
            }
            return true
        } catch let apiErr as APIError {
            if case .http(409, _, _) = apiErr {
                self.error = ChatError(code: "chat_in_progress", message: L("Cannot clear thread while a turn is active."))
            } else {
                self.error = ChatError(code: "clear_failed", message: apiErr.localizedDescription)
            }
            return false
        } catch {
            self.error = ChatError(code: "network_error", message: error.localizedDescription)
            return false
        }
    }

    func refreshTurn(requestId: String) async {
        guard !requestId.isEmpty else { return }
        do {
            let turn: TurnStatusResponse = try await client.send(.get("/api/coach/chat/turns/\(requestId)"))
            if let resultId = turn.resultMessageId {
                self.messages = self.messages.map { msg in
                    guard msg.requestId == requestId else { return msg }
                    return ChatMessage(
                        id: String(resultId),
                        numericId: resultId,
                        role: msg.role,
                        content: msg.content,
                        createdAt: msg.createdAt,
                        requestId: msg.requestId,
                        citations: msg.citations,
                        evidenceStatus: msg.evidenceStatus,
                        interrupted: msg.interrupted,
                        toolCalls: msg.toolCalls,
                        feedback: msg.feedback
                    )
                }
            }
        } catch {
            // Ignore polling errors
        }
    }

    func fetchMessageSources(messageId: Int) async {
        do {
            let sources: MessageSourcesResponse = try await client.send(.get("/api/coach/chat/messages/\(messageId)/sources"))
            self.selectedMessageSources = sources
        } catch {
            // Tolerate failure
        }
    }

    func clearMessageSources() {
        self.selectedMessageSources = nil
    }

    func dismissClarify() {
        self.clarifyOptions = nil
    }

    func sendFeedback(messageId: Int, value: Int) async {
        guard let idx = messages.firstIndex(where: { $0.numericId == messageId }) else { return }
        let previous = messages[idx].feedback
        messages[idx].feedback = value

        do {
            let body = FeedbackRequestBody(value: value)
            let _: EmptyResponse = try await client.send(.send(.post, "/api/coach/chat/messages/\(messageId)/feedback", body: body))
        } catch {
            // Revert on failure
            if let revertIdx = messages.firstIndex(where: { $0.numericId == messageId }) {
                messages[revertIdx].feedback = previous
            }
        }
    }

    func applyProposal(proposalId: Int, clientToday: String? = nil) async -> Bool {
        do {
            let body = ProposalApplyBody(clientToday: clientToday)
            let _: EmptyResponse = try await client.send(.send(.post, "/api/coach/chat/proposals/\(proposalId)/apply", body: body))
            self.proposalStates[proposalId] = "applied"
            return true
        } catch {
            return false
        }
    }

    func discardProposal(proposalId: Int) async -> Bool {
        do {
            let _: EmptyResponse = try await client.send(.post("/api/coach/chat/proposals/\(proposalId)/discard"))
            self.proposalStates[proposalId] = "discarded"
            return true
        } catch {
            return false
        }
    }

    #if DEBUG
    func loadMessagesDirectlyForScreenshot(_ msgs: [ChatMessage], proposals: [Int: String] = [:], clarify: [String]? = nil) {
        self.messages = msgs
        self.proposalStates = proposals
        self.clarifyOptions = clarify
    }
    #endif

}
