import Foundation
import Testing
@testable import UphillAI

struct ChatMessageTests {
    @Test func decodesChatThreadFixture() throws {
        let thread = try Fixture.decode(ChatThreadResponse.self, "chat_thread.json")

        #expect(thread.messages.count == 2)
        #expect(thread.summary?.contains("tempo") == true)
        #expect(thread.hasMore == false)
        #expect(thread.oldestId == 101)
        #expect(thread.proposals?["7"] == "proposed")

        let userMsg = thread.messages[0]
        #expect(userMsg.id == "101")
        #expect(userMsg.numericId == 101)
        #expect(userMsg.role == .user)
        #expect(userMsg.content.contains("tempo run"))

        let coachMsg = thread.messages[1]
        #expect(coachMsg.id == "102")
        #expect(coachMsg.numericId == 102)
        #expect(coachMsg.role == .assistant)
        #expect(coachMsg.feedback == 1)
        #expect(coachMsg.evidenceStatus == "available")
        #expect(coachMsg.citations?.count == 1)
        #expect(coachMsg.citations?[0].sourceId == "cite-1")

        let toolCalls = try #require(coachMsg.toolCalls)
        #expect(toolCalls.count == 1)
        #expect(toolCalls[0].name == "propose_schedule_change")
        #expect(toolCalls[0].cardType == "schedule_proposal")

        let proposal = try #require(toolCalls[0].decodeScheduleProposal())
        #expect(proposal.proposalId == 7)
        #expect(proposal.status == "proposed")
        #expect(proposal.rationale?.contains("Tuesday Tempo") == true)
    }

    @Test func decodesChatSourcesFixture() throws {
        let sources = try Fixture.decode(MessageSourcesResponse.self, "chat_sources.json")

        #expect(sources.messageId == 102)
        #expect(sources.evidenceStatus == "available")
        #expect(sources.citations.count == 1)
        #expect(sources.citations[0].book == "Training for the Uphill Athlete")
        #expect(sources.citations[0].chapterNum == 5)
        #expect(sources.citations[0].quote?.contains("48 hours") == true)
        #expect(sources.citations[0].url == "https://uphillathlete.com/training-principles")

        #expect(sources.evidence.count == 1)
        #expect(sources.evidence[0]["title"]?.stringValue == "Microcycle Recovery Guidelines")
    }

    @Test func roundTripEncodeDecode() throws {
        let msg = ChatMessage(
            id: "msg-test-123",
            numericId: 456,
            role: .assistant,
            content: "You should rest today.",
            createdAt: "2026-10-05T09:00:00Z",
            requestId: "req-abc",
            citations: [
                CitationItem(
                    sourceId: "c-1",
                    title: "Recovery Rules",
                    book: "TFUA",
                    quote: "Rest is when adaptation occurs."
                )
            ],
            evidenceStatus: "available",
            interrupted: false,
            toolCalls: [
                ToolResultPayload(
                    toolCallId: "call-xyz",
                    name: "get_week",
                    status: "success",
                    cardType: "week_schedule",
                    cardData: ["week_number": .int(3)]
                )
            ],
            feedback: 1
        )

        let encoded = try JSONCoding.encoder.encode(msg)
        let decoded = try JSONCoding.decoder.decode(ChatMessage.self, from: encoded)

        #expect(decoded.id == msg.id)
        #expect(decoded.numericId == msg.numericId)
        #expect(decoded.role == msg.role)
        #expect(decoded.content == msg.content)
        #expect(decoded.feedback == msg.feedback)
        #expect(decoded.evidenceStatus == msg.evidenceStatus)
        #expect(decoded.citations?.count == 1)
        #expect(decoded.citations?[0].quote == msg.citations?[0].quote)
        #expect(decoded.toolCalls?.count == 1)
        #expect(decoded.toolCalls?[0].cardData?["week_number"]?.intValue == 3)
    }

    @Test func userDefaultsChatStorePersistsAndClears() {
        let testDefaults = UserDefaults(suiteName: "ChatMessageTestsSuite")!
        testDefaults.removePersistentDomain(forName: "ChatMessageTestsSuite")
        let store = UserDefaultsChatStore(defaults: testDefaults, keyPrefix: "test_chat_")

        let planId = 99
        #expect(store.loadMessages(for: planId).isEmpty)

        let messages = [
            ChatMessage(role: .user, content: "Hello"),
            ChatMessage(role: .assistant, content: "Hi athlete!")
        ]
        store.saveMessages(messages, for: planId)

        let loaded = store.loadMessages(for: planId)
        #expect(loaded.count == 2)
        #expect(loaded[0].content == "Hello")
        #expect(loaded[1].content == "Hi athlete!")

        store.clearMessages(for: planId)
        #expect(store.loadMessages(for: planId).isEmpty)
    }

    @Test func decodesAllCardDataTypes() {
        let schedulePayload = ToolResultPayload(
            toolCallId: "s-1",
            name: "schedule",
            cardType: "week_schedule",
            cardData: [
                "week_number": .int(2),
                "total_distance_km": .double(45.5),
                "total_elevation_gain_m": .double(1200)
            ]
        )
        let schedule = schedulePayload.decodeWeekSchedule()
        #expect(schedule?.weekNumber == 2)
        #expect(schedule?.totalDistanceKm == 45.5)
        #expect(schedule?.totalElevationGainM == 1200)

        let reviewPayload = ToolResultPayload(
            toolCallId: "r-1",
            name: "review",
            cardType: "week_review",
            cardData: [
                "week_number": .int(1),
                "planned_distance_km": .double(40.0),
                "actual_distance_km": .double(42.5),
                "compliance_percent": .double(106.0),
                "summary": .string("Great week!")
            ]
        )
        let review = reviewPayload.decodeWeekReview()
        #expect(review?.weekNumber == 1)
        #expect(review?.plannedDistanceKm == 40.0)
        #expect(review?.actualDistanceKm == 42.5)
        #expect(review?.compliancePercent == 106.0)
        #expect(review?.summary == "Great week!")

        let pacingPayload = ToolResultPayload(
            toolCallId: "p-1",
            name: "pacing",
            cardType: "pacing_splits",
            cardData: [
                "race_name": .string("UTMB 100M"),
                "distance_label": .string("100M"),
                "total_distance_km": .double(171.0)
            ]
        )
        let pacing = pacingPayload.decodePacingSplits()
        #expect(pacing?.raceName == "UTMB 100M")
        #expect(pacing?.distanceLabel == "100M")
        #expect(pacing?.totalDistanceKm == 171.0)
    }
}
