import { useCallback, useEffect, useRef, useState } from "react";
import { useAppContext } from "../contexts/AppContext";
import {
  consumeCoachChatStream,
  CitationItem,
  CoachChatStreamError,
  ToolResultEvent,
} from "../lib/coachChatStream";
import { localToday, ProposalState } from "../lib/scheduleProposals";

export interface ChatMessageItem {
  id?: number;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
  request_id?: string;
  citations?: CitationItem[];
  evidence_status?: "available" | "empty" | "unavailable";
  interrupted?: boolean;
  toolCalls?: ToolResultEvent[];
}

export type ChatTurnStatus =
  | "idle"
  | "admitting"
  | "retrieving"
  | "generating"
  | "interrupted"
  | "error"
  | "done";

export interface ActiveRequestState {
  requestId: string;
  retryOf?: string | null;
}

export interface ChatErrorState {
  code: string;
  message?: string;
}

export interface UseCoachChatReturn {
  messages: ChatMessageItem[];
  activeRequest: ActiveRequestState | null;
  status: ChatTurnStatus;
  error: ChatErrorState | null;
  hasMore: boolean;
  isLoadingOlder: boolean;
  send: (text: string) => Promise<void>;
  retry: (rootRequestId: string) => Promise<void>;
  clear: () => Promise<boolean>;
  loadOlder: () => Promise<void>;
  refreshTurn: (requestId: string) => Promise<void>;
  selectedMessageSources: {
    message_id: number;
    citations: CitationItem[];
    evidence: unknown[];
  } | null;
  fetchMessageSources: (messageId: number) => Promise<void>;
  clearMessageSources: () => void;
  clarifyOptions: string[] | null;
  dismissClarify: () => void;
  proposalStates: Record<number, ProposalState>;
}

function hydrateToolCalls(
  rawMessages: Array<Record<string, unknown>>
): ChatMessageItem[] {
  return rawMessages.map((m) => ({
    ...m,
    toolCalls: Array.isArray(m.tool_calls_json)
      ? (m.tool_calls_json as Record<string, unknown>[]).map((tc) => ({
          type: "tool_result" as const,
          ...tc,
        }))
      : undefined,
  })) as ChatMessageItem[];
}

function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    return (
      localStorage.getItem("UPHILL_API_URL_OVERRIDE") ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:8000"
    );
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

function getAuthToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("uphill_session_token");
  }
  return null;
}

function toProposalStates(raw: unknown): Record<number, ProposalState> {
  const out: Record<number, ProposalState> = {};
  if (raw && typeof raw === "object") {
    for (const [k, v] of Object.entries(raw as Record<string, ProposalState>)) out[Number(k)] = v;
  }
  return out;
}

export function useCoachChat(): UseCoachChatReturn {
  const { lang } = useAppContext();

  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [activeRequest, setActiveRequest] = useState<ActiveRequestState | null>(null);
  const [status, setStatus] = useState<ChatTurnStatus>("idle");
  const [error, setError] = useState<ChatErrorState | null>(null);
  const [hasMore, setHasMore] = useState<boolean>(false);
  const [isLoadingOlder, setIsLoadingOlder] = useState<boolean>(false);
  const [selectedMessageSources, setSelectedMessageSources] = useState<{
    message_id: number;
    citations: CitationItem[];
    evidence: unknown[];
  } | null>(null);
  const [clarifyOptions, setClarifyOptions] = useState<string[] | null>(null);
  const [proposalStates, setProposalStates] = useState<Record<number, ProposalState>>({});

  const abortControllerRef = useRef<AbortController | null>(null);
  const isExecutingRef = useRef<boolean>(false);

  // Initial load of paginated message history
  useEffect(() => {
    let cancelled = false;
    const token = getAuthToken();
    if (!token) return;

    async function loadInitial() {
      try {
        const apiBase = getApiBaseUrl();
        const res = await fetch(`${apiBase}/api/coach/chat/thread?limit=50`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (!res.ok) return;
        const data = await res.json();
        if (!cancelled && data && Array.isArray(data.messages)) {
          setMessages(hydrateToolCalls(data.messages));
          setHasMore(Boolean(data.has_more));
          setProposalStates(toProposalStates(data.proposals));
        }
      } catch {
        // Silently tolerate initial fetch failures (e.g. offline/starting)
      }
    }

    loadInitial();

    return () => {
      cancelled = true;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const loadOlder = useCallback(async () => {
    if (!hasMore || isLoadingOlder || messages.length === 0) return;
    const token = getAuthToken();
    if (!token) return;

    const oldestId = messages[0]?.id;
    if (!oldestId) return;

    setIsLoadingOlder(true);
    try {
      const apiBase = getApiBaseUrl();
      const res = await fetch(
        `${apiBase}/api/coach/chat/thread?before_id=${oldestId}&limit=50`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      if (!res.ok) return;
      const data = await res.json();
      if (data && Array.isArray(data.messages)) {
        setMessages((prev) => [...hydrateToolCalls(data.messages), ...prev]);
        setHasMore(Boolean(data.has_more));
        setProposalStates((prev) => ({ ...toProposalStates(data.proposals), ...prev }));
      }
    } finally {
      setIsLoadingOlder(false);
    }
  }, [hasMore, isLoadingOlder, messages]);

  const runStream = useCallback(
    async (requestId: string, message: string | null, retryOf: string | null) => {
      if (isExecutingRef.current) return;
      isExecutingRef.current = true;

      const token = getAuthToken();
      if (!token) {
        setError({ code: "unauthenticated", message: "User is not logged in." });
        setStatus("error");
        isExecutingRef.current = false;
        return;
      }

      const activeState: ActiveRequestState = {
        requestId,
        retryOf: retryOf || null,
      };
      setActiveRequest(activeState);
      setStatus("admitting");
      setError(null);
      setClarifyOptions(null);

      const abortCtrl = new AbortController();
      abortControllerRef.current = abortCtrl;

      const apiBase = getApiBaseUrl();
      let assistantMsgCreated = false;

      try {
        const response = await fetch(`${apiBase}/api/coach/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            request_id: requestId,
            message: message ?? null,
            retry_of: retryOf ?? null,
            lang: lang || "en",
            client_today: localToday(),
          }),
          signal: abortCtrl.signal,
        });

        await consumeCoachChatStream(
          response,
          (event) => {
            if (event.type === "status") {
              if (event.step === "retrieving") {
                setStatus("retrieving");
              } else if (event.step === "generating") {
                setStatus("generating");
                if (!assistantMsgCreated) {
                  assistantMsgCreated = true;
                  setMessages((prev) => [
                    ...prev,
                    {
                      role: "assistant",
                      content: "",
                      request_id: requestId,
                    },
                  ]);
                }
              }
            } else if (event.type === "token") {
              if (!assistantMsgCreated) {
                assistantMsgCreated = true;
                setMessages((prev) => [
                  ...prev,
                  {
                    role: "assistant",
                    content: event.text,
                    request_id: requestId,
                  },
                ]);
              } else {
                setMessages((prev) => {
                  const copy = [...prev];
                  const lastIdx = copy.length - 1;
                  if (lastIdx >= 0 && copy[lastIdx].role === "assistant") {
                    copy[lastIdx] = {
                      ...copy[lastIdx],
                      content: copy[lastIdx].content + event.text,
                    };
                  }
                  return copy;
                });
              }
            } else if (event.type === "citations") {
              setMessages((prev) => {
                const copy = [...prev];
                const lastIdx = copy.length - 1;
                if (lastIdx >= 0 && copy[lastIdx].role === "assistant") {
                  copy[lastIdx] = {
                    ...copy[lastIdx],
                    citations: event.citations,
                    evidence_status: event.evidence_status,
                  };
                }
                return copy;
              });
            } else if (event.type === "tool_result") {
              setMessages((prev) => {
                const copy = [...prev];
                const lastIdx = copy.length - 1;
                if (lastIdx >= 0 && copy[lastIdx].role === "assistant") {
                  const existing = copy[lastIdx].toolCalls || [];
                  copy[lastIdx] = { ...copy[lastIdx], toolCalls: [...existing, event] };
                }
                return copy;
              });
            } else if (event.type === "clarify") {
              setClarifyOptions(event.options);
            } else if (event.type === "done") {
              setMessages((prev) => {
                const copy = [...prev];
                const lastIdx = copy.length - 1;
                if (lastIdx >= 0 && copy[lastIdx].role === "assistant") {
                  copy[lastIdx] = {
                    ...copy[lastIdx],
                    id: event.message_id ?? undefined,
                  };
                }
                return copy;
              });
              setStatus("done");
              setActiveRequest(null);
            } else if (event.type === "error") {
              // Server emitted error event
              setStatus("error");
              setError({ code: event.code, message: event.message ?? undefined });
              setActiveRequest(null);

              // Mark assistant message as interrupted if partial text exists
              setMessages((prev) => {
                const copy = [...prev];
                const lastIdx = copy.length - 1;
                if (
                  lastIdx >= 0 &&
                  copy[lastIdx].role === "assistant" &&
                  copy[lastIdx].content.length > 0
                ) {
                  copy[lastIdx] = {
                    ...copy[lastIdx],
                    interrupted: true,
                  };
                }
                return copy;
              });
            }
          },
          abortCtrl.signal
        );
      } catch (err: unknown) {
        const isAbort =
          abortCtrl.signal.aborted ||
          (err instanceof Error && err.name === "AbortError");
        const streamErr = err instanceof CoachChatStreamError ? err : null;

        const errorCode = streamErr?.code || (isAbort ? "stream_aborted" : "network_error");
        const errorMessage = streamErr?.message || (err instanceof Error ? err.message : String(err));

        setError({ code: errorCode, message: errorMessage });
        setStatus("interrupted");
        setActiveRequest(null);

        // Mark partial message as interrupted
        setMessages((prev) => {
          const copy = [...prev];
          const lastIdx = copy.length - 1;
          if (
            lastIdx >= 0 &&
            copy[lastIdx].role === "assistant" &&
            copy[lastIdx].content.length > 0
          ) {
            copy[lastIdx] = {
              ...copy[lastIdx],
              interrupted: true,
            };
          }
          return copy;
        });
      } finally {
        isExecutingRef.current = false;
        abortControllerRef.current = null;
      }
    },
    [lang]
  );

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isExecutingRef.current) return;

      const requestId = crypto.randomUUID();

      // Append user message immediately
      setMessages((prev) => [
        ...prev,
        {
          role: "user",
          content: trimmed,
          request_id: requestId,
        },
      ]);

      await runStream(requestId, trimmed, null);
    },
    [runStream]
  );

  const retry = useCallback(
    async (rootRequestId: string) => {
      if (!rootRequestId || isExecutingRef.current) return;

      const newRequestId = crypto.randomUUID();
      await runStream(newRequestId, null, rootRequestId);
    },
    [runStream]
  );

  const clear = useCallback(async (): Promise<boolean> => {
    const token = getAuthToken();
    if (!token) return false;

    try {
      const apiBase = getApiBaseUrl();
      const res = await fetch(`${apiBase}/api/coach/chat/thread`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.status === 409) {
        setError({
          code: "chat_in_progress",
          message: "Cannot clear thread while a turn is active.",
        });
        return false;
      }

      if (!res.ok) {
        setError({
          code: "clear_failed",
          message: "Failed to clear conversation thread.",
        });
        return false;
      }

      setMessages([]);
      setActiveRequest(null);
      setStatus("idle");
      setError(null);
      setHasMore(false);
      return true;
    } catch (err: unknown) {
      setError({
        code: "network_error",
        message: err instanceof Error ? err.message : String(err),
      });
      return false;
    }
  }, []);

  const refreshTurn = useCallback(async (requestId: string) => {
    const token = getAuthToken();
    if (!token || !requestId) return;

    try {
      const apiBase = getApiBaseUrl();
      const res = await fetch(`${apiBase}/api/coach/chat/turns/${requestId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) return;
      const turn = await res.json();
      if (turn && turn.result_message_id) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.request_id === requestId
              ? { ...msg, id: turn.result_message_id }
              : msg
          )
        );
      }
    } catch {
      // Tolerate failure
    }
  }, []);

  const fetchMessageSources = useCallback(async (messageId: number) => {
    const token = getAuthToken();
    if (!token || !messageId) return;

    try {
      const apiBase = getApiBaseUrl();
      const res = await fetch(
        `${apiBase}/api/coach/chat/messages/${messageId}/sources`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      if (!res.ok) return;
      const sources = await res.json();
      setSelectedMessageSources(sources);
    } catch {
      // Tolerate failure
    }
  }, []);

  const clearMessageSources = useCallback(() => {
    setSelectedMessageSources(null);
  }, []);

  const dismissClarify = useCallback(() => {
    setClarifyOptions(null);
  }, []);

  return {
    messages,
    activeRequest,
    status,
    error,
    hasMore,
    isLoadingOlder,
    send,
    retry,
    clear,
    loadOlder,
    refreshTurn,
    selectedMessageSources,
    fetchMessageSources,
    clearMessageSources,
    clarifyOptions,
    dismissClarify,
    proposalStates,
  };
}
