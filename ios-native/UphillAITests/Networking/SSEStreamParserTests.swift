import Foundation
import Testing
@testable import UphillAI

struct SSEStreamParserTests {
    let parser = SSEStreamParser()

    @Test func parsesMultipleSSEEvents() async throws {
        let raw = """
        event: status
        data: {"type":"status","step":"retrieving","request_id":"req-1"}

        event: token
        data: {"type":"token","text":"Hello "}

        event: token
        data: {"type":"token","text":"athlete!"}

        event: done
        data: {"type":"done","request_id":"req-1","message_id":42,"replayed":false}

        """

        var events: [ChatStreamEvent] = []
        for try await event in parser.parse(data: Data(raw.utf8)) {
            events.append(event)
        }

        #expect(events.count == 4)
        #expect(events[0] == .status(step: "retrieving", requestId: "req-1"))
        #expect(events[1] == .token(text: "Hello "))
        #expect(events[2] == .token(text: "athlete!"))
        #expect(events[3] == .done(requestId: "req-1", messageId: 42, replayed: false))
    }

    @Test func handlesUTF8MultiByteSplitAcrossChunks() async throws {
        // "Chào bạn": "à" is [0xC3, 0xA0]
        let part1Str = "event: token\ndata: {\"type\":\"token\",\"text\":\"Ch"
        let part2Str = "o bạn\"}\n\nevent: done\ndata: {\"type\":\"done\",\"request_id\":\"u-1\",\"message_id\":100,\"replayed\":false}\n\n"

        var part1 = [UInt8](part1Str.utf8)
        part1.append(0xC3) // First byte of "à"

        var part2 = [UInt8]()
        part2.append(0xA0) // Second byte of "à"
        part2.append(contentsOf: part2Str.utf8)

        let chunkStream = AsyncStream<Data> { continuation in
            continuation.yield(Data(part1))
            continuation.yield(Data(part2))
            continuation.finish()
        }

        var events: [ChatStreamEvent] = []
        for try await event in parser.parse(chunks: chunkStream) {
            events.append(event)
        }

        #expect(events.count == 2)
        if case .token(let text) = events[0] {
            #expect(text == "Chào bạn")
            #expect(!text.contains("\u{FFFD}"))
        } else {
            Issue.record("Expected token event")
        }
        #expect(events[1] == .done(requestId: "u-1", messageId: 100, replayed: false))
    }

    @Test func handlesCRLFLineSeparators() async throws {
        let raw = "event: status\r\ndata: {\"type\":\"status\",\"step\":\"generating\",\"request_id\":\"req-crlf\"}\r\n\r\nevent: done\r\ndata: {\"type\":\"done\",\"request_id\":\"req-crlf\",\"message_id\":1,\"replayed\":false}\r\n\r\n"

        var events: [ChatStreamEvent] = []
        for try await event in parser.parse(data: Data(raw.utf8)) {
            events.append(event)
        }

        #expect(events.count == 2)
        #expect(events[0] == .status(step: "generating", requestId: "req-crlf"))
        #expect(events[1] == .done(requestId: "req-crlf", messageId: 1, replayed: false))
    }

    @Test func ignoresCommentsAndHeartbeats() async throws {
        let raw = """
        : heartbeat

        : ping comment

        event: token
        data: {"type":"token","text":"Alive"}

        : heartbeat

        event: done
        data: {"type":"done","request_id":"req-hb","message_id":2,"replayed":false}

        """

        var events: [ChatStreamEvent] = []
        for try await event in parser.parse(data: Data(raw.utf8)) {
            events.append(event)
        }

        #expect(events.count == 2)
        #expect(events[0] == .token(text: "Alive"))
        #expect(events[1] == .done(requestId: "req-hb", messageId: 2, replayed: false))
    }

    @Test func parsesCitationsAndEvidenceStatus() async throws {
        let raw = """
        event: citations
        data: {"type":"citations","evidence_status":"available","citations":[{"source_id":"sched-1","title":"Zone 2 Aerobic Base","domain":"scheduler","url":"https://uphillathlete.com"}]}

        event: done
        data: {"type":"done","request_id":"req-cite","message_id":3,"replayed":false}

        """

        var events: [ChatStreamEvent] = []
        for try await event in parser.parse(data: Data(raw.utf8)) {
            events.append(event)
        }

        #expect(events.count == 2)
        guard case .citations(let citations, let evidenceStatus) = events[0] else {
            Issue.record("Expected citations event")
            return
        }
        #expect(evidenceStatus == "available")
        #expect(citations.count == 1)
        #expect(citations[0].sourceId == "sched-1")
        #expect(citations[0].title == "Zone 2 Aerobic Base")
        #expect(citations[0].domain == "scheduler")
        #expect(citations[0].url == "https://uphillathlete.com")
    }

    @Test func dispatchesErrorEvent() async throws {
        let raw = """
        event: status
        data: {"type":"status","step":"retrieving","request_id":"req-err"}

        event: error
        data: {"type":"error","code":"coach_turn_quota_exceeded","message":"Daily quota reached"}

        """

        var events: [ChatStreamEvent] = []
        for try await event in parser.parse(data: Data(raw.utf8)) {
            events.append(event)
        }

        #expect(events.count == 2)
        #expect(events[0] == .status(step: "retrieving", requestId: "req-err"))
        #expect(events[1] == .error(code: "coach_turn_quota_exceeded", message: "Daily quota reached"))
    }

    @Test func throwsPrematureCloseWhenNoTerminalEvent() async throws {
        let raw = """
        event: status
        data: {"type":"status","step":"generating","request_id":"req-eof"}

        event: token
        data: {"type":"token","text":"Partial answer..."}

        """

        var events: [ChatStreamEvent] = []
        await #expect(throws: SSEStreamError.prematureClose) {
            for try await event in parser.parse(data: Data(raw.utf8)) {
                events.append(event)
            }
        }
        #expect(events.count == 2)
    }

    @Test func ignoresMalformedJSONWithoutTerminatingStream() async throws {
        let raw = """
        event: token
        data: {bad json

        event: token
        data: {"type":"token","text":"Recovered"}

        event: done
        data: {"type":"done","request_id":"req-json","message_id":5,"replayed":false}

        """

        var events: [ChatStreamEvent] = []
        for try await event in parser.parse(data: Data(raw.utf8)) {
            events.append(event)
        }

        #expect(events.count == 2)
        #expect(events[0] == .token(text: "Recovered"))
        #expect(events[1] == .done(requestId: "req-json", messageId: 5, replayed: false))
    }

    @Test func dispatchesToolCallAndToolResult() async throws {
        let raw = """
        event: tool_call
        data: {"tool_call_id":"call_1","name":"get_week","args":{"week_number":3}}

        event: tool_result
        data: {"tool_call_id":"call_1","name":"get_week","status":"success","card_type":"week_schedule","card_data":{"week_number":3}}

        event: done
        data: {"request_id":"r1","message_id":1,"replayed":false}

        """

        var events: [ChatStreamEvent] = []
        for try await event in parser.parse(data: Data(raw.utf8)) {
            events.append(event)
        }

        #expect(events.count == 3)
        guard case .toolCall(let id, let name, let args) = events[0] else {
            Issue.record("Expected tool_call event")
            return
        }
        #expect(id == "call_1")
        #expect(name == "get_week")
        #expect(args["week_number"]?.intValue == 3)

        guard case .toolResult(let trId, let trName, let status, let cardType, let cardData) = events[1] else {
            Issue.record("Expected tool_result event")
            return
        }
        #expect(trId == "call_1")
        #expect(trName == "get_week")
        #expect(status == "success")
        #expect(cardType == "week_schedule")
        #expect(cardData?["week_number"]?.intValue == 3)
    }

    @Test func dispatchesClarifyEvent() async throws {
        let raw = """
        event: clarify
        data: {"prompt":"Which race?","options":["Dalat Ultra Trail","VMM"]}

        event: done
        data: {"request_id":"r1","message_id":1,"replayed":false}

        """

        var events: [ChatStreamEvent] = []
        for try await event in parser.parse(data: Data(raw.utf8)) {
            events.append(event)
        }

        #expect(events.count == 2)
        guard case .clarify(let prompt, let options) = events[0] else {
            Issue.record("Expected clarify event")
            return
        }
        #expect(prompt == "Which race?")
        #expect(options == ["Dalat Ultra Trail", "VMM"])
    }
}
