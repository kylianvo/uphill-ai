import Foundation

enum SSEStreamError: Error, LocalizedError, Sendable, Equatable {
    case prematureClose
    case httpError(status: Int, code: String?, message: String)
    case streamAborted
    case invalidResponse

    var errorDescription: String? {
        switch self {
        case .prematureClose:
            return "Stream closed prematurely without a done or error event."
        case .httpError(let status, _, let message):
            return "HTTP \(status): \(message)"
        case .streamAborted:
            return "Stream aborted by client."
        case .invalidResponse:
            return "Invalid server response."
        }
    }
}

struct SSEStreamParser: Sendable {
    init() {}

    /// Consumes an arbitrary byte AsyncSequence, extracting SSE event blocks and yielding ChatStreamEvent.
    func parse<S: AsyncSequence>(
        bytes: S
    ) -> AsyncThrowingStream<ChatStreamEvent, Error> where S.Element == UInt8, S: Sendable {
        AsyncThrowingStream { continuation in
            let task = Task {
                var buffer = [UInt8]()
                var hasTerminated = false

                do {
                    for try await byte in bytes {
                        try Task.checkCancellation()
                        buffer.append(byte)

                        // Process any complete SSE blocks delimited by \r\n\r\n or \n\n
                        while let (blockBytes, delimiterLength) = Self.findBlock(in: buffer) {
                            buffer.removeSubrange(0..<(blockBytes.count + delimiterLength))
                            if let event = Self.processBlockBytes(blockBytes) {
                                continuation.yield(event)
                                if case .done = event {
                                    hasTerminated = true
                                    continuation.finish()
                                    return
                                } else if case .error = event {
                                    hasTerminated = true
                                    continuation.finish()
                                    return
                                }
                            }
                        }
                    }

                    // End of stream reached. If there is trailing data in buffer, try to parse it.
                    if !buffer.isEmpty {
                        if let event = Self.processBlockBytes(buffer) {
                            continuation.yield(event)
                            if case .done = event { hasTerminated = true }
                            else if case .error = event { hasTerminated = true }
                        }
                    }

                    if !hasTerminated {
                        continuation.finish(throwing: SSEStreamError.prematureClose)
                    } else {
                        continuation.finish()
                    }
                } catch is CancellationError {
                    continuation.finish(throwing: SSEStreamError.streamAborted)
                } catch {
                    continuation.finish(throwing: error)
                }
            }

            continuation.onTermination = { _ in
                task.cancel()
            }
        }
    }

    /// Convenience for URLSession.AsyncBytes
    func parse(
        bytes: URLSession.AsyncBytes
    ) -> AsyncThrowingStream<ChatStreamEvent, Error> {
        parse(bytes: bytes)
    }

    /// Convenience for parsing in-memory bytes
    func parse(bytes: [UInt8]) -> AsyncThrowingStream<ChatStreamEvent, Error> {
        let stream = AsyncStream<UInt8> { continuation in
            for byte in bytes {
                continuation.yield(byte)
            }
            continuation.finish()
        }
        return parse(bytes: stream)
    }

    /// Convenience for parsing in-memory Data
    func parse(data: Data) -> AsyncThrowingStream<ChatStreamEvent, Error> {
        parse(bytes: [UInt8](data))
    }

    /// Convenience for parsing a stream of Data chunks
    func parse<S: AsyncSequence>(
        chunks: S
    ) -> AsyncThrowingStream<ChatStreamEvent, Error> where S.Element == Data, S: Sendable {
        let byteStream = AsyncThrowingStream<UInt8, Error> { continuation in
            let task = Task {
                do {
                    for try await chunk in chunks {
                        try Task.checkCancellation()
                        for byte in chunk {
                            continuation.yield(byte)
                        }
                    }
                    continuation.finish()
                } catch is CancellationError {
                    continuation.finish(throwing: SSEStreamError.streamAborted)
                } catch {
                    continuation.finish(throwing: error)
                }
            }
            continuation.onTermination = { _ in
                task.cancel()
            }
        }
        return parse(bytes: byteStream)
    }

    // MARK: - Block Detection & Parsing

    /// Scans buffer for \r\n\r\n (4 bytes) or \n\n (2 bytes).
    /// Returns the block bytes before the delimiter and the delimiter length.
    static func findBlock(in buffer: [UInt8]) -> ([UInt8], Int)? {
        guard buffer.count >= 2 else { return nil }

        var i = 0
        while i < buffer.count - 1 {
            // Check for \n\n (0x0A, 0x0A)
            if buffer[i] == 0x0A && buffer[i + 1] == 0x0A {
                let block = Array(buffer[0..<i])
                return (block, 2)
            }
            // Check for \r\n\r\n (0x0D, 0x0A, 0x0D, 0x0A)
            if buffer[i] == 0x0D && i + 3 < buffer.count {
                if buffer[i + 1] == 0x0A && buffer[i + 2] == 0x0D && buffer[i + 3] == 0x0A {
                    let block = Array(buffer[0..<i])
                    return (block, 4)
                }
            }
            i += 1
        }
        return nil
    }

    static func processBlockBytes(_ bytes: [UInt8]) -> ChatStreamEvent? {
        guard let text = String(bytes: bytes, encoding: .utf8) else {
            return nil
        }
        return processBlockString(text)
    }

    static func processBlockString(_ block: String) -> ChatStreamEvent? {
        let trimmed = block.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }

        var eventType: String? = nil
        var dataLines: [String] = []

        // Split by newlines (\r\n or \n)
        let lines = block.components(separatedBy: .newlines)
        for line in lines {
            let trimmedLine = line.trimmingCharacters(in: .whitespaces)
            if trimmedLine.hasPrefix(":") {
                // Comment / heartbeat
                continue
            }
            if trimmedLine.hasPrefix("event:") {
                eventType = trimmedLine.dropFirst(6).trimmingCharacters(in: .whitespaces)
            } else if trimmedLine.hasPrefix("data:") {
                dataLines.append(trimmedLine.dropFirst(5).trimmingCharacters(in: .whitespaces))
            }
        }

        guard !dataLines.isEmpty else { return nil }
        let dataString = dataLines.joined(separator: "\n")
        guard let data = dataString.data(using: .utf8) else { return nil }

        return decodeEvent(data: data, overrideType: eventType)
    }

    static func decodeEvent(data: Data, overrideType: String?) -> ChatStreamEvent? {
        guard let jsonObject = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] else {
            return nil
        }
        let rawType = overrideType ?? (jsonObject["type"] as? String)
        guard let rawType else { return nil }

        switch rawType {
        case "status":
            guard let step = jsonObject["step"] as? String else { return nil }
            let requestId = (jsonObject["request_id"] as? String) ?? (jsonObject["requestId"] as? String) ?? ""
            return .status(step: step, requestId: requestId)

        case "token":
            let text = (jsonObject["text"] as? String) ?? ""
            return .token(text: text)

        case "citations":
            let evidenceStatus = (jsonObject["evidence_status"] as? String) ?? (jsonObject["evidenceStatus"] as? String) ?? "unavailable"
            let citationsRaw = jsonObject["citations"] as? [[String: Any]] ?? []
            let citationsData = (try? JSONSerialization.data(withJSONObject: citationsRaw)) ?? Data()
            let citations = (try? JSONCoding.decoder.decode([CitationItem].self, from: citationsData)) ?? []
            return .citations(citations: citations, evidenceStatus: evidenceStatus)

        case "tool_call":
            let toolCallId = (jsonObject["tool_call_id"] as? String) ?? (jsonObject["toolCallId"] as? String) ?? ""
            let name = (jsonObject["name"] as? String) ?? ""
            let argsRaw = jsonObject["args"] as? [String: Any] ?? [:]
            let argsData = (try? JSONSerialization.data(withJSONObject: argsRaw)) ?? Data()
            let args = (try? JSONDecoder().decode([String: JSONValue].self, from: argsData)) ?? [:]
            return .toolCall(id: toolCallId, name: name, args: args)

        case "tool_result":
            let toolCallId = (jsonObject["tool_call_id"] as? String) ?? (jsonObject["toolCallId"] as? String) ?? ""
            let name = (jsonObject["name"] as? String) ?? ""
            let status = (jsonObject["status"] as? String) ?? "success"
            let cardType = (jsonObject["card_type"] as? String) ?? (jsonObject["cardType"] as? String)
            let cardDataRaw = jsonObject["card_data"] as? [String: Any] ?? jsonObject["cardData"] as? [String: Any]
            var cardData: [String: JSONValue]? = nil
            if let cardDataRaw {
                let cdData = (try? JSONSerialization.data(withJSONObject: cardDataRaw)) ?? Data()
                cardData = try? JSONDecoder().decode([String: JSONValue].self, from: cdData)
            }
            return .toolResult(id: toolCallId, name: name, status: status, cardType: cardType, cardData: cardData)

        case "clarify":
            let prompt = (jsonObject["prompt"] as? String) ?? ""
            let options = (jsonObject["options"] as? [String]) ?? []
            return .clarify(prompt: prompt, options: options)

        case "done":
            let requestId = (jsonObject["request_id"] as? String) ?? (jsonObject["requestId"] as? String) ?? ""
            let messageId = (jsonObject["message_id"] as? Int) ?? (jsonObject["messageId"] as? Int)
            let replayed = (jsonObject["replayed"] as? Bool) ?? false
            return .done(requestId: requestId, messageId: messageId, replayed: replayed)

        case "error":
            let code = (jsonObject["code"] as? String) ?? "unknown_error"
            let message = jsonObject["message"] as? String
            return .error(code: code, message: message)

        default:
            return nil
        }
    }
}
