import { describe, it, expect, vi } from "vitest";
import {
  consumeCoachChatStream,
  ChatStreamEvent,
  CoachChatStreamError,
} from "./coachChatStream";

function createMockReadableStream(chunks: Uint8Array[]): ReadableStream<Uint8Array> {
  let index = 0;
  return new ReadableStream<Uint8Array>({
    pull(controller) {
      if (index < chunks.length) {
        controller.enqueue(chunks[index++]);
      } else {
        controller.close();
      }
    },
  });
}

function createMockResponse(chunks: Uint8Array[], status = 200, statusText = "OK"): Response {
  const stream = createMockReadableStream(chunks);
  return new Response(stream, {
    status,
    statusText,
    headers: { "Content-Type": "text/event-stream" },
  });
}

describe("coachChatStream", () => {
  const encoder = new TextEncoder();

  it("parses individual and multiple SSE events in a single chunk", async () => {
    const raw =
      'event: status\ndata: {"type":"status","step":"retrieving","request_id":"uuid-1"}\n\n' +
      'event: token\ndata: {"type":"token","text":"Hello "}\n\n' +
      'event: token\ndata: {"type":"token","text":"runner!"}\n\n' +
      'event: done\ndata: {"type":"done","request_id":"uuid-1","message_id":42,"replayed":false}\n\n';

    const response = createMockResponse([encoder.encode(raw)]);
    const events: ChatStreamEvent[] = [];

    await consumeCoachChatStream(response, (ev) => events.push(ev));

    expect(events).toEqual([
      { type: "status", step: "retrieving", request_id: "uuid-1" },
      { type: "token", text: "Hello " },
      { type: "token", text: "runner!" },
      { type: "done", request_id: "uuid-1", message_id: 42, replayed: false },
    ]);
  });

  it("handles Vietnamese multi-byte UTF-8 codepoints split mid-character across chunks", async () => {
    // "Chào bạn, đây là bài tập chạy bộ!" contains multi-byte characters:
    // à (0xC3 0xA0), ạ (0xE1 0xBA 0xA1), đ (0xC4 0x91), â (0xC3 0xA2), ộ (0xE1 0xBB 0x99)
    const part1Str = 'event: token\ndata: {"type":"token","text":"Ch';
    const charAWithGrave = "à"; // 2 bytes: 0xC3, 0xA0
    const part2Str = ' bạn"}\n\n' +
      'event: done\ndata: {"type":"done","request_id":"uuid-vi","message_id":100,"replayed":false}\n\n';

    const part1Bytes = encoder.encode(part1Str);
    const graveBytes = encoder.encode(charAWithGrave);
    const part2Bytes = encoder.encode(part2Str);

    // Split 'à' between chunk 1 (0xC3) and chunk 2 (0xA0)
    const chunk1 = new Uint8Array(part1Bytes.length + 1);
    chunk1.set(part1Bytes, 0);
    chunk1.set([graveBytes[0]], part1Bytes.length);

    const chunk2 = new Uint8Array(1 + part2Bytes.length);
    chunk2.set([graveBytes[1]], 0);
    chunk2.set(part2Bytes, 1);

    const response = createMockResponse([chunk1, chunk2]);
    const events: ChatStreamEvent[] = [];

    await consumeCoachChatStream(response, (ev) => events.push(ev));

    // Must NOT contain Unicode replacement character \uFFFD
    const tokenEvents = events.filter((e) => e.type === "token");
    expect(tokenEvents).toHaveLength(1);
    if (tokenEvents[0].type === "token") {
      expect(tokenEvents[0].text).toBe("Chào bạn");
      expect(tokenEvents[0].text).not.toContain("\uFFFD");
    }
  });

  it("handles CRLF (\\r\\n) line separators transparently", async () => {
    const raw =
      'event: status\r\ndata: {"type":"status","step":"generating","request_id":"req-crlf"}\r\n\r\n' +
      'event: done\r\ndata: {"type":"done","request_id":"req-crlf","message_id":1,"replayed":false}\r\n\r\n';

    const response = createMockResponse([encoder.encode(raw)]);
    const events: ChatStreamEvent[] = [];

    await consumeCoachChatStream(response, (ev) => events.push(ev));

    expect(events).toEqual([
      { type: "status", step: "generating", request_id: "req-crlf" },
      { type: "done", request_id: "req-crlf", message_id: 1, replayed: false },
    ]);
  });

  it("ignores SSE comments (e.g. idle heartbeat framing) without emitting events", async () => {
    const raw =
      ": heartbeat\n\n" +
      ": ping comment\n\n" +
      'event: token\ndata: {"type":"token","text":"Alive"}\n\n' +
      ": heartbeat\n\n" +
      'event: done\ndata: {"type":"done","request_id":"req-hb","message_id":2,"replayed":false}\n\n';

    const response = createMockResponse([encoder.encode(raw)]);
    const events: ChatStreamEvent[] = [];

    await consumeCoachChatStream(response, (ev) => events.push(ev));

    expect(events).toEqual([
      { type: "token", text: "Alive" },
      { type: "done", request_id: "req-hb", message_id: 2, replayed: false },
    ]);
  });

  it("parses citations events with evidence status", async () => {
    const raw =
      'event: citations\ndata: {"type":"citations","evidence_status":"available","citations":[{"source_id":"sched-1","title":"Zone 2 Aerobic Base","domain":"scheduler","url":"https://uphillathlete.com"}]}\n\n' +
      'event: done\ndata: {"type":"done","request_id":"req-cite","message_id":3,"replayed":false}\n\n';

    const response = createMockResponse([encoder.encode(raw)]);
    const events: ChatStreamEvent[] = [];

    await consumeCoachChatStream(response, (ev) => events.push(ev));

    expect(events).toEqual([
      {
        type: "citations",
        evidence_status: "available",
        citations: [
          {
            source_id: "sched-1",
            title: "Zone 2 Aerobic Base",
            domain: "scheduler",
            url: "https://uphillathlete.com",
          },
        ],
      },
      { type: "done", request_id: "req-cite", message_id: 3, replayed: false },
    ]);
  });

  it("dispatches error event when emitted by server", async () => {
    const raw =
      'event: status\ndata: {"type":"status","step":"retrieving","request_id":"req-err"}\n\n' +
      'event: error\ndata: {"type":"error","code":"coach_turn_quota_exceeded","message":"Daily quota reached"}\n\n';

    const response = createMockResponse([encoder.encode(raw)]);
    const events: ChatStreamEvent[] = [];

    await consumeCoachChatStream(response, (ev) => events.push(ev));

    expect(events).toEqual([
      { type: "status", step: "retrieving", request_id: "req-err" },
      {
        type: "error",
        code: "coach_turn_quota_exceeded",
        message: "Daily quota reached",
      },
    ]);
  });

  it("throws CoachChatStreamError on non-200 HTTP response with parsed error detail", async () => {
    const errorBody = JSON.stringify({ detail: "Message exceeds maximum allowed length" });
    const response = new Response(errorBody, {
      status: 400,
      statusText: "Bad Request",
      headers: { "Content-Type": "application/json" },
    });

    await expect(consumeCoachChatStream(response, () => {})).rejects.toThrow(
      "Message exceeds maximum allowed length"
    );
  });

  it("throws CoachChatStreamError when stream closes prematurely without terminal event", async () => {
    const raw =
      'event: status\ndata: {"type":"status","step":"generating","request_id":"req-eof"}\n\n' +
      'event: token\ndata: {"type":"token","text":"Partial answer..."}\n\n';

    const response = createMockResponse([encoder.encode(raw)]);
    const events: ChatStreamEvent[] = [];

    await expect(
      consumeCoachChatStream(response, (ev) => events.push(ev))
    ).rejects.toThrow(CoachChatStreamError);

    // Initial tokens were received before EOF
    expect(events).toHaveLength(2);
  });

  it("safely ignores malformed JSON in event data without terminating stream", async () => {
    const raw =
      'event: token\ndata: {bad json\n\n' +
      'event: token\ndata: {"type":"token","text":"Recovered"}\n\n' +
      'event: done\ndata: {"type":"done","request_id":"req-json","message_id":5,"replayed":false}\n\n';

    const response = createMockResponse([encoder.encode(raw)]);
    const events: ChatStreamEvent[] = [];

    await consumeCoachChatStream(response, (ev) => events.push(ev));

    expect(events).toEqual([
      { type: "token", text: "Recovered" },
      { type: "done", request_id: "req-json", message_id: 5, replayed: false },
    ]);
  });
});
