/**
 * Coach Chat SSE Stream client with UTF-8 chunk safety and typed event dispatching.
 */

export interface CitationItem {
  source_id?: string;
  title?: string;
  url?: string;
  domain?: string;
  quote?: string;
  [key: string]: unknown;
}

export interface StatusEvent {
  type: "status";
  step: "retrieving" | "generating";
  request_id: string;
}

export interface TokenEvent {
  type: "token";
  text: string;
}

export interface CitationsEvent {
  type: "citations";
  citations: CitationItem[];
  evidence_status: "available" | "empty" | "unavailable";
}

export interface DoneEvent {
  type: "done";
  request_id: string;
  message_id: number | null;
  replayed: boolean;
}

export interface ErrorEvent {
  type: "error";
  code: string;
  message?: string | null;
}

export type ChatStreamEvent =
  | StatusEvent
  | TokenEvent
  | CitationsEvent
  | DoneEvent
  | ErrorEvent;

export class CoachChatStreamError extends Error {
  statusCode?: number;
  code?: string;

  constructor(message: string, options?: { statusCode?: number; code?: string }) {
    super(message);
    this.name = "CoachChatStreamError";
    this.statusCode = options?.statusCode;
    this.code = options?.code;
  }
}

/**
 * Consumes an SSE response from the Coach Chat stream endpoint.
 *
 * Ensures multi-byte UTF-8 codepoints split across chunks decode without replacement characters,
 * parses CRLF and LF event blocks, ignores comments, and safely surfaces typed events.
 */
export async function consumeCoachChatStream(
  response: Response,
  onEvent: (event: ChatStreamEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  if (!response.ok) {
    let errorDetail = `HTTP ${response.status} ${response.statusText}`;
    let errorCode: string | undefined;
    try {
      const errorJson = await response.json();
      if (errorJson && typeof errorJson === "object") {
        if ("detail" in errorJson && typeof errorJson.detail === "string") {
          errorDetail = errorJson.detail;
        } else if ("message" in errorJson && typeof errorJson.message === "string") {
          errorDetail = errorJson.message;
        }
        if ("code" in errorJson && typeof errorJson.code === "string") {
          errorCode = errorJson.code;
        }
      }
    } catch {
      // Body not JSON or unreadable
    }
    throw new CoachChatStreamError(errorDetail, { statusCode: response.status, code: errorCode });
  }

  if (!response.body) {
    throw new CoachChatStreamError("Response body is null");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let hasTerminated = false;

  const processBlock = (block: string) => {
    if (!block.trim()) return;

    let eventType: string | null = null;
    const dataLines: string[] = [];

    const lines = block.split(/\r?\n/);
    for (const line of lines) {
      if (line.startsWith(":")) {
        // SSE comment (e.g. heartbeat)
        continue;
      }
      if (line.startsWith("event:")) {
        eventType = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trim());
      }
    }

    if (dataLines.length > 0) {
      const dataStr = dataLines.join("\n");
      try {
        const parsed = JSON.parse(dataStr);
        if (parsed && typeof parsed === "object") {
          const type = eventType || parsed.type;
          const fullEvent = { ...parsed, type } as ChatStreamEvent;

          onEvent(fullEvent);

          if (fullEvent.type === "done" || fullEvent.type === "error") {
            hasTerminated = true;
          }
        }
      } catch {
        // Ignore unparseable data blocks without crashing
      }
    }
  };

  try {
    while (true) {
      if (signal?.aborted) {
        reader.cancel();
        throw new CoachChatStreamError("Stream aborted by client");
      }

      const { done, value } = await reader.read();

      if (done) {
        // Flush remaining decoded text
        buffer += decoder.decode();
        const remainingBlocks = buffer.split(/\r?\n\r?\n/);
        for (const block of remainingBlocks) {
          processBlock(block);
        }

        if (!hasTerminated) {
          throw new CoachChatStreamError(
            "Stream closed prematurely without a done or error event"
          );
        }
        break;
      }

      if (value) {
        buffer += decoder.decode(value, { stream: true });

        // Event boundaries are marked by double newline (\r\n\r\n or \n\n)
        const parts = buffer.split(/\r?\n\r?\n/);
        // The last part is incomplete (or empty if buffer ended on boundary)
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          processBlock(part);
          if (hasTerminated) {
            // Cancel stream read once terminal event received
            reader.cancel().catch(() => {});
            return;
          }
        }
      }
    }
  } catch (err: unknown) {
    if (err instanceof CoachChatStreamError) {
      throw err;
    }
    const message = err instanceof Error ? err.message : String(err);
    throw new CoachChatStreamError(message);
  } finally {
    reader.releaseLock();
  }
}
