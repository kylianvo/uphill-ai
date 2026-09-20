import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { act } from "@testing-library/react";
import { renderHookWithApp } from "../test-utils/renderWithAppContext";
import { useCoachChat } from "./useCoachChat";

function createMockReadableStream(rawSSE: string): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  const bytes = encoder.encode(rawSSE);
  return new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(bytes);
      controller.close();
    },
  });
}

function sseResponse(rawSSE: string, status = 200) {
  const stream = createMockReadableStream(rawSSE);
  return new Response(stream, {
    status,
    headers: { "Content-Type": "text/event-stream" },
  });
}

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("useCoachChat", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    localStorage.setItem("uphill_session_token", "test-auth-token");
    localStorage.removeItem("UPHILL_API_URL_OVERRIDE");
  });

  afterEach(() => {
    global.fetch = originalFetch;
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("loads initial paginated messages on mount", async () => {
    const mockInitialData = {
      messages: [
        { id: 10, role: "user", content: "Previous question" },
        { id: 11, role: "assistant", content: "Previous answer" },
      ],
      has_more: true,
      oldest_id: 10,
    };

    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse(mockInitialData));
    global.fetch = fetchMock;

    const { result } = renderHookWithApp(() => useCoachChat());

    // Allow initial useEffect to resolve
    await act(async () => {
      await Promise.resolve();
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/coach/chat/thread"),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-auth-token",
        }),
      })
    );

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].content).toBe("Previous question");
    expect(result.current.hasMore).toBe(true);
  });

  it("sends message and streams tokens to assistant bubble", async () => {
    // Initial mount fetch
    const fetchMock = vi.fn().mockResolvedValueOnce(
      jsonResponse({ messages: [], has_more: false, oldest_id: null })
    );
    global.fetch = fetchMock;

    const { result } = renderHookWithApp(() => useCoachChat());
    await act(async () => {
      await Promise.resolve();
    });

    const sseBody =
      'event: status\ndata: {"type":"status","step":"retrieving","request_id":"test-uuid"}\n\n' +
      'event: status\ndata: {"type":"status","step":"generating","request_id":"test-uuid"}\n\n' +
      'event: token\ndata: {"type":"token","text":"Keep running "}\n\n' +
      'event: token\ndata: {"type":"token","text":"in Zone 2."}\n\n' +
      'event: done\ndata: {"type":"done","request_id":"test-uuid","message_id":50,"replayed":false}\n\n';

    fetchMock.mockResolvedValueOnce(sseResponse(sseBody));

    await act(async () => {
      await result.current.send("What is my target pace?");
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].role).toBe("user");
    expect(result.current.messages[0].content).toBe("What is my target pace?");
    expect(result.current.messages[1].role).toBe("assistant");
    expect(result.current.messages[1].content).toBe("Keep running in Zone 2.");
    expect(result.current.messages[1].id).toBe(50);
    expect(result.current.status).toBe("done");
    expect(result.current.activeRequest).toBeNull();
  });

  it("prevents ambiguous resubmission while an active turn is in-flight", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(
      jsonResponse({ messages: [], has_more: false, oldest_id: null })
    );
    global.fetch = fetchMock;

    const { result } = renderHookWithApp(() => useCoachChat());
    await act(async () => {
      await Promise.resolve();
    });

    const sseBody =
      'event: token\ndata: {"type":"token","text":"Working..."}\n\n' +
      'event: done\ndata: {"type":"done","request_id":"u-1","message_id":1,"replayed":false}\n\n';
    fetchMock.mockResolvedValueOnce(sseResponse(sseBody));

    // First send
    let p1: Promise<void>;
    act(() => {
      p1 = result.current.send("Question 1");
    });

    // Immediate second send before p1 finishes should be ignored
    await act(async () => {
      await result.current.send("Question 2 concurrent");
    });

    await act(async () => {
      await p1;
    });

    // Only first send went through
    expect(fetchMock).toHaveBeenCalledTimes(2); // 1 initial load + 1 send
  });

  it("sends explicit retry with retry_of and distinct UUID", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(
      jsonResponse({ messages: [], has_more: false, oldest_id: null })
    );
    global.fetch = fetchMock;

    const { result } = renderHookWithApp(() => useCoachChat());
    await act(async () => {
      await Promise.resolve();
    });

    const retrySse =
      'event: token\ndata: {"type":"token","text":"Retried answer"}\n\n' +
      'event: done\ndata: {"type":"done","request_id":"retry-uuid","message_id":99,"replayed":false}\n\n';
    fetchMock.mockResolvedValueOnce(sseResponse(retrySse));

    await act(async () => {
      await result.current.retry("root-turn-uuid");
    });

    const postCall = fetchMock.mock.calls[1];
    expect(postCall[0]).toContain("/api/coach/chat/stream");
    const sentBody = JSON.parse(postCall[1].body);
    expect(sentBody.retry_of).toBe("root-turn-uuid");
    expect(sentBody.message).toBeNull();
    expect(sentBody.request_id).toBeDefined();
    expect(sentBody.request_id).not.toBe("root-turn-uuid");
  });

  it("preserves partial tokens as interrupted if stream throws or disconnects", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(
      jsonResponse({ messages: [], has_more: false, oldest_id: null })
    );
    global.fetch = fetchMock;

    const { result } = renderHookWithApp(() => useCoachChat());
    await act(async () => {
      await Promise.resolve();
    });

    // Stream closes abruptly after partial token
    const incompleteSse =
      'event: token\ndata: {"type":"token","text":"Partial sentence before cut..."}\n\n';
    fetchMock.mockResolvedValueOnce(sseResponse(incompleteSse));

    await act(async () => {
      await result.current.send("Explain Zone 2");
    });

    expect(result.current.messages).toHaveLength(2);
    const assistantMsg = result.current.messages[1];
    expect(assistantMsg.role).toBe("assistant");
    expect(assistantMsg.content).toBe("Partial sentence before cut...");
    expect(assistantMsg.interrupted).toBe(true);
    expect(result.current.status).toBe("interrupted");
    expect(result.current.error).not.toBeNull();
  });

  it("handles thread clear successfully and manages 409 conflict during active turn", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(
      jsonResponse({
        messages: [{ id: 1, role: "user", content: "hi" }],
        has_more: false,
        oldest_id: 1,
      })
    );
    global.fetch = fetchMock;

    const { result } = renderHookWithApp(() => useCoachChat());
    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.messages).toHaveLength(1);

    // 1. Successful clear
    fetchMock.mockResolvedValueOnce(jsonResponse({ status: "cleared" }, 200));

    let success: boolean = false;
    await act(async () => {
      success = await result.current.clear();
    });

    expect(success).toBe(true);
    expect(result.current.messages).toHaveLength(0);

    // 2. 409 Conflict error
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ detail: "Cannot clear thread while a turn is active." }, 409)
    );

    let failSuccess: boolean = true;
    await act(async () => {
      failSuccess = await result.current.clear();
    });

    expect(failSuccess).toBe(false);
    expect(result.current.error?.code).toBe("chat_in_progress");
  });

  it("fetches message sources on demand and clears them", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(
      jsonResponse({ messages: [], has_more: false, oldest_id: null })
    );
    global.fetch = fetchMock;

    const { result } = renderHookWithApp(() => useCoachChat());
    await act(async () => {
      await Promise.resolve();
    });

    const mockSources = {
      message_id: 42,
      citations: [{ source_id: "kb-1", title: "Aerobic Capacity", domain: "scheduler" }],
      evidence: [],
    };
    fetchMock.mockResolvedValueOnce(jsonResponse(mockSources));

    await act(async () => {
      await result.current.fetchMessageSources(42);
    });

    expect(result.current.selectedMessageSources).toEqual(mockSources);

    act(() => {
      result.current.clearMessageSources();
    });

    expect(result.current.selectedMessageSources).toBeNull();
  });
});
