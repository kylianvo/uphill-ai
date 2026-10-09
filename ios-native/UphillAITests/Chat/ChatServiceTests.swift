import Foundation
import Synchronization
import Testing
@testable import UphillAI

@MainActor
struct ChatServiceTests {
    @Test func loadInitialLoadsCachedThenServerThread() async throws {
        let testDefaults = UserDefaults(suiteName: "ChatServiceTests_LoadInitial")!
        testDefaults.removePersistentDomain(forName: "ChatServiceTests_LoadInitial")
        let store = UserDefaultsChatStore(
            defaults: testDefaults,
            keyPrefix: "test_"
        )
        store.clearMessages(for: 1)
        store.saveMessages([ChatMessage(role: .assistant, content: "Cached message")], for: 1)

        let client = makeStubClient { request in
            #expect(request.url?.path() == "/api/coach/chat/thread")
            let payload: [String: Any] = [
                "messages": [
                    [
                        "id": 1,
                        "role": "assistant",
                        "content": "Server message",
                        "created_at": "2026-10-05T10:00:00Z"
                    ]
                ],
                "has_more": false,
                "oldest_id": 1,
                "proposals": ["10": "proposed"]
            ]
            return (200, json(payload))
        }

        let service = ChatService(client: client, store: store)
        await service.loadInitial(planId: 1)

        #expect(service.messages.count == 1)
        #expect(service.messages[0].content == "Server message")
        #expect(service.proposalStates[10] == "proposed")
        #expect(service.hasMore == false)
    }

    @Test func clearCallsEndpointAndResetsState() async throws {
        let testDefaults = UserDefaults(suiteName: "ChatServiceTests_Clear")!
        testDefaults.removePersistentDomain(forName: "ChatServiceTests_Clear")
        let store = UserDefaultsChatStore(
            defaults: testDefaults,
            keyPrefix: "test_"
        )
        let client = makeStubClient { request in
            #expect(request.httpMethod == "DELETE")
            #expect(request.url?.path() == "/api/coach/chat/thread")
            return (200, json(["status": "cleared"]))
        }

        let service = ChatService(client: client, store: store)
        let cleared = await service.clear()

        #expect(cleared == true)
        #expect(service.messages.isEmpty)
        #expect(service.status == .idle)
        #expect(service.error == nil)
    }

    @Test func sendFeedbackOptimisticallyUpdatesAndRevertsOnFailure() async throws {
        let shouldFail = Mutex(true)
        let client = makeStubClient { request in
            if request.url?.path() == "/api/coach/chat/thread" {
                return (200, json([
                    "messages": [
                        [
                            "id": 50,
                            "role": "assistant",
                            "content": "Good advice"
                        ]
                    ],
                    "has_more": false
                ]))
            }
            if request.url?.path() == "/api/coach/chat/messages/50/feedback" {
                #expect(request.httpMethod == "POST")
                if shouldFail.withLock({ $0 }) {
                    return (500, json(["detail": "Internal error"]))
                } else {
                    return (200, json(["message_id": 50, "feedback": 1]))
                }
            }
            return (404, json([:]))
        }

        let testDefaults = UserDefaults(suiteName: "ChatServiceTests_Feedback")!
        testDefaults.removePersistentDomain(forName: "ChatServiceTests_Feedback")
        let store = UserDefaultsChatStore(
            defaults: testDefaults,
            keyPrefix: "test_"
        )
        store.clearMessages(for: 1)

        let service = ChatService(client: client, store: store)
        await service.loadInitial(planId: 1)
        #expect(service.messages.count == 1)

        // Attempt feedback with failure -> reverts
        shouldFail.withLock { $0 = true }
        await service.sendFeedback(messageId: 50, value: 1)
        #expect(service.messages.first?.feedback == nil)

        // Attempt feedback with success -> stays
        shouldFail.withLock { $0 = false }
        await service.sendFeedback(messageId: 50, value: 1)
        #expect(service.messages.first?.feedback == 1)
    }

    @Test func applyAndDiscardProposalsUpdateStates() async throws {
        let client = makeStubClient { request in
            if request.url?.path() == "/api/coach/chat/proposals/99/apply" {
                return (200, json(["status": "applied"]))
            } else if request.url?.path() == "/api/coach/chat/proposals/99/discard" {
                return (200, json(["status": "discarded"]))
            }
            return (404, json([:]))
        }

        let service = ChatService(client: client)
        let applied = await service.applyProposal(proposalId: 99)
        #expect(applied == true)
        #expect(service.proposalStates[99] == "applied")

        let discarded = await service.discardProposal(proposalId: 99)
        #expect(discarded == true)
        #expect(service.proposalStates[99] == "discarded")
    }

    @Test func dismissClarifyClearsOptions() {
        let service = ChatService(client: makeStubClient { _ in (200, json([:])) })
        service.dismissClarify()
        #expect(service.clarifyOptions == nil)
    }

    @Test func streamedCardArrivingBeforeTokensIsKept() async throws {
        let card: [String: Any] = [
            "type": "tool_result", "tool_call_id": "t1", "name": "propose_schedule_change",
            "status": "success", "card_type": "schedule_proposal",
            "card_data": ["proposal_id": 7, "status": "proposed"]
        ]
        let sse = [card, ["type": "token", "text": "Swapped."], ["type": "done", "request_id": "r", "message_id": 12]]
            .map { "data: " + String(data: json($0), encoding: .utf8)! + "\n\n" }
            .joined()
        let client = makeStubClient { _ in (200, Data(sse.utf8)) }

        let service = ChatService(client: client)
        await service.send(text: "I am busy Saturday")

        let reply = try #require(service.messages.last)
        #expect(reply.role == .assistant)
        #expect(reply.content == "Swapped.")
        #expect(reply.toolCalls?.first?.cardType == "schedule_proposal")
        #expect(service.proposalStates[7] == "proposed")
    }

    @Test func threadHistoryDecodesStoredToolCalls() async throws {
        let client = makeStubClient { _ in
            (200, json([
                "messages": [[
                    "id": 3, "role": "assistant", "content": "See the card.",
                    "tool_calls_json": [[
                        "tool_call_id": "t1", "name": "propose_schedule_change", "status": "success",
                        "card_type": "schedule_proposal", "card_data": ["proposal_id": 7]
                    ]]
                ]],
                "has_more": false
            ]))
        }

        let service = ChatService(client: client)
        await service.loadInitial(planId: 1)

        let payload = try #require(service.messages.first?.toolCalls?.first)
        #expect(payload.cardType == "schedule_proposal")
        #expect(payload.decodeScheduleProposal()?.proposalId == 7)
    }
}
