import React, { useEffect, useRef, useState } from "react";
import { useAppContext } from "../contexts/AppContext";
import { parseMarkdown } from "../utils/markdown";
import { translations } from "../app/translations";
import { useCoachChat } from "../hooks/useCoachChat";
import ChatSources from "../components/ChatSources";
import { CitationItem } from "../lib/coachChatStream";
import RichCardRenderer from "../components/RichCardRenderer";
import ToolExecutionPill from "../components/ToolExecutionPill";
import ClarificationChipsBar from "../components/ClarificationChipsBar";

export default function ChatTab({ isMobile }: { isMobile: boolean }) {
  const { lang, setPaceHandoff, setIsPaceStrategyOpen, handleTabSwitch } = useAppContext();
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const [inputText, setInputText] = useState("");
  const [isSourcesOpen, setIsSourcesOpen] = useState(false);
  const [fallbackSources, setFallbackSources] = useState<{
    message_id: number;
    citations: CitationItem[];
    evidence: unknown[];
  } | null>(null);

  const {
    messages,
    status,
    error,
    hasMore,
    isLoadingOlder,
    send,
    retry,
    clear,
    loadOlder,
    selectedMessageSources,
    fetchMessageSources,
    clearMessageSources,
    clarifyOptions,
    dismissClarify,
  } = useCoachChat();

  const t = (key: keyof typeof translations.en) =>
    translations[lang as keyof typeof translations]?.[key] || translations.en[key] || key;

  const isBusy = status === "admitting" || status === "retrieving" || status === "generating";

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [messages, status]);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || inputText;
    if (!text.trim() || isBusy) return;

    if (!textToSend) {
      setInputText("");
    }
    await send(text);
  };

  const handleClear = async () => {
    if (isBusy) return;
    const confirmed = window.confirm(t("chat_clear_confirm"));
    if (confirmed) {
      await clear();
    }
  };

  const handleOpenSources = async (messageId?: number, fallbackCitations?: CitationItem[]) => {
    if (messageId) {
      setFallbackSources(null);
      await fetchMessageSources(messageId);
      setIsSourcesOpen(true);
    } else if (fallbackCitations && fallbackCitations.length > 0) {
      setFallbackSources({
        message_id: 0,
        citations: fallbackCitations,
        evidence: [],
      });
      setIsSourcesOpen(true);
    }
  };

  const handleCloseSources = () => {
    setIsSourcesOpen(false);
    setFallbackSources(null);
    clearMessageSources();
  };

  const getErrorMessage = () => {
    if (!error) return null;
    switch (error.code) {
      case "coach_turn_quota_exceeded":
        return t("chat_error_quota_turns");
      case "coach_retry_quota_exceeded":
        return t("chat_error_quota_retries");
      case "chat_in_progress":
        return t("chat_error_in_progress");
      case "coach_chat_disabled":
        return t("chat_error_disabled");
      case "network_error":
        return t("chat_error_network");
      default:
        return error.message || t("chat_status_error");
    }
  };

  const getStatusLabel = () => {
    switch (status) {
      case "admitting":
      case "retrieving":
        return t("chat_status_retrieving");
      case "generating":
        return t("chat_status_generating");
      case "interrupted":
        return t("chat_status_interrupted");
      case "error":
        return t("chat_status_error");
      default:
        return t("chat_status_ready");
    }
  };

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div style={{ display: "flex", flexDirection: "column", flex: 1, width: "100%", minHeight: 0 }}>
        {!isMobile && (
          <h3 style={{ marginBottom: "12px", fontSize: "20px" }}>
            {lang === "en" ? "Chat Workspace" : "Không gian Trò chuyện"}
          </h3>
        )}

        <div
          className="chat-pane"
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            width: "100%",
            minHeight: isMobile ? "0px" : "350px",
            backgroundColor: "rgba(255, 255, 255, 0.85)",
            backdropFilter: "blur(32px)",
            WebkitBackdropFilter: "blur(32px)",
            borderRadius: "16px",
            border: "1px solid rgba(0, 0, 0, 0.1)",
            boxShadow: "0 10px 30px rgba(0, 0, 0, 0.04)",
            overflow: "hidden",
          }}
        >
          {/* Header */}
          <div
            className="chat-header"
            style={{
              padding: isMobile ? "8px 12px" : "14px 20px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              borderBottom: "1px solid rgba(0, 0, 0, 0.08)",
              background: "rgba(0, 0, 0, 0.02)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span
                className="coach-status-dot"
                style={{
                  width: "9px",
                  height: "9px",
                  borderRadius: "50%",
                  display: "inline-block",
                  backgroundColor:
                    status === "error" || status === "interrupted"
                      ? "#ef4444"
                      : isBusy
                      ? "#f59e0b"
                      : "#10b981",
                  boxShadow: isBusy ? "0 0 8px #f59e0b" : undefined,
                }}
              />
              <span className="chat-header-title" style={{ fontSize: isMobile ? "13px" : "15px", fontWeight: 600, color: "#111111" }}>
                {lang === "en" ? "Coach Uphill (AI)" : "Huấn luyện viên Uphill (AI)"}
              </span>
              <span
                style={{
                  fontSize: isMobile ? "11px" : "12px",
                  color: isBusy ? "#d97706" : "var(--text-muted)",
                  marginLeft: "4px",
                }}
              >
                ({getStatusLabel()})
              </span>
            </div>

            {messages.length > 0 && (
              <button
                onClick={handleClear}
                disabled={isBusy}
                style={{
                  background: "rgba(0, 0, 0, 0.04)",
                  border: "1px solid rgba(0, 0, 0, 0.1)",
                  color: "var(--text-secondary)",
                  borderRadius: "6px",
                  padding: isMobile ? "3px 8px" : "4px 10px",
                  fontSize: isMobile ? "11px" : "12px",
                  cursor: isBusy ? "not-allowed" : "pointer",
                  opacity: isBusy ? 0.5 : 1,
                  transition: "background 0.2s ease",
                }}
              >
                {t("chat_clear_btn")}
              </button>
            )}
          </div>

          {/* History */}
          <div
            className="chat-history"
            style={{
              padding: isMobile ? "10px" : "20px",
              gap: isMobile ? "10px" : "16px",
              minHeight: 0,
              flex: 1,
              display: "flex",
              flexDirection: "column",
              overflowY: "auto",
            }}
          >
            {/* Pagination Load Older Button */}
            {hasMore && (
              <div style={{ textAlign: "center", margin: "4px 0" }}>
                <button
                  onClick={loadOlder}
                  disabled={isLoadingOlder}
                  style={{
                    backgroundColor: "rgba(255, 255, 255, 0.9)",
                    border: "1px solid rgba(0, 0, 0, 0.1)",
                    color: "var(--text-secondary)",
                    borderRadius: "6px",
                    padding: "4px 12px",
                    fontSize: "12px",
                    cursor: isLoadingOlder ? "not-allowed" : "pointer",
                    boxShadow: "0 1px 2px rgba(0, 0, 0, 0.03)",
                  }}
                >
                  {isLoadingOlder ? t("loading") : t("chat_load_older")}
                </button>
              </div>
            )}

            {/* Empty State */}
            {messages.length === 0 && (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  textAlign: "center",
                  padding: isMobile ? "24px 12px" : "48px 24px",
                  margin: "auto 0",
                  color: "var(--text-muted)",
                }}
              >
                <div
                  style={{
                    width: isMobile ? "44px" : "54px",
                    height: isMobile ? "44px" : "54px",
                    borderRadius: "50%",
                    backgroundColor: "rgba(25, 206, 139, 0.12)",
                    border: "1px solid rgba(25, 206, 139, 0.25)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    marginBottom: "12px",
                    color: "var(--accent-primary)",
                  }}
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2L2 7l10 5 10-5-10-5z" />
                    <path d="M2 17l10 5 10-5" />
                    <path d="M2 12l10 5 10-5" />
                  </svg>
                </div>
                <h4 style={{ margin: "0 0 8px 0", color: "var(--text-primary)", fontSize: isMobile ? "15px" : "18px", fontWeight: 700 }}>
                  {t("chat_empty_title")}
                </h4>
                <p style={{ margin: "0 0 16px 0", maxWidth: "480px", fontSize: isMobile ? "12.5px" : "14px", lineHeight: "1.5", color: "var(--text-secondary)" }}>
                  {t("chat_empty_desc")}
                </p>

                {/* Capabilities pills */}
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "8px",
                    justifyContent: "center",
                    maxWidth: "520px",
                    marginBottom: "16px",
                  }}
                >
                  <span style={{ fontSize: "12px", backgroundColor: "rgba(255, 255, 255, 0.75)", border: "1px solid rgba(0, 0, 0, 0.08)", padding: "4px 12px", borderRadius: "16px", color: "var(--text-primary)", boxShadow: "0 1px 2px rgba(0, 0, 0, 0.03)" }}>
                    {t("chat_empty_cap_1")}
                  </span>
                  <span style={{ fontSize: "12px", backgroundColor: "rgba(255, 255, 255, 0.75)", border: "1px solid rgba(0, 0, 0, 0.08)", padding: "4px 12px", borderRadius: "16px", color: "var(--text-primary)", boxShadow: "0 1px 2px rgba(0, 0, 0, 0.03)" }}>
                    {t("chat_empty_cap_2")}
                  </span>
                  <span style={{ fontSize: "12px", backgroundColor: "rgba(255, 255, 255, 0.75)", border: "1px solid rgba(0, 0, 0, 0.08)", padding: "4px 12px", borderRadius: "16px", color: "var(--text-primary)", boxShadow: "0 1px 2px rgba(0, 0, 0, 0.03)" }}>
                    {t("chat_empty_cap_3")}
                  </span>
                  <span style={{ fontSize: "12px", backgroundColor: "rgba(255, 255, 255, 0.75)", border: "1px solid rgba(0, 0, 0, 0.08)", padding: "4px 12px", borderRadius: "16px", color: "var(--text-primary)", boxShadow: "0 1px 2px rgba(0, 0, 0, 0.03)" }}>
                    {t("chat_empty_cap_4")}
                  </span>
                </div>

                {/* Boundary notice */}
                <p style={{ margin: 0, fontSize: "11.5px", color: "var(--text-muted)", maxWidth: "440px", fontStyle: "italic" }}>
                  {t("chat_empty_boundary")}
                </p>
              </div>
            )}

            {/* Messages */}
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`chat-bubble ${msg.role === "user" ? "chat-bubble-user" : "chat-bubble-assistant"}`}
                style={{
                  alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                  maxWidth: isMobile ? "90%" : "82%",
                  fontSize: isMobile ? "13px" : "14.5px",
                  lineHeight: "1.55",
                  padding: isMobile ? "8px 12px" : "12px 18px",
                  borderRadius: msg.role === "user" ? "14px 14px 3px 14px" : "14px 14px 14px 3px",
                  backgroundColor: msg.role === "user" ? "var(--accent-primary)" : "rgba(255, 255, 255, 0.95)",
                  color: msg.role === "user" ? "#ffffff" : "var(--text-primary)",
                  border: msg.role === "user" ? "none" : "1px solid rgba(0, 0, 0, 0.08)",
                  boxShadow: msg.role === "user" ? "0 2px 8px rgba(25, 206, 139, 0.25)" : "0 2px 8px rgba(0, 0, 0, 0.03)",
                }}
              >
                <div>
                  {msg.role === "assistant"
                    ? parseMarkdown(msg.content, {
                        citations: msg.citations,
                        onCitationClick: () => handleOpenSources(msg.id, msg.citations),
                      })
                    : msg.content}
                </div>

                {msg.role === "assistant" &&
                  msg.toolCalls?.map((tc) => (
                    <RichCardRenderer
                      key={tc.tool_call_id}
                      result={tc}
                      lang={lang}
                      onOpenPaceStrategy={(payload) => {
                        setPaceHandoff(payload);
                        setIsPaceStrategyOpen(true);
                        handleTabSwitch("tools");
                      }}
                    />
                  ))}

                {/* Assistant footer: interrupted badge, retry button, sources button */}
                {msg.role === "assistant" && (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      marginTop: "8px",
                      paddingTop: "6px",
                      borderTop: "1px solid rgba(0, 0, 0, 0.06)",
                      fontSize: "11.5px",
                    }}
                  >
                    {msg.interrupted && (
                      <span
                        style={{
                          backgroundColor: "rgba(239, 68, 68, 0.1)",
                          color: "#dc2626",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          fontWeight: 600,
                        }}
                      >
                        {t("chat_status_interrupted")}
                      </span>
                    )}

                    {msg.interrupted && msg.request_id && (
                      <button
                        onClick={() => retry(msg.request_id!)}
                        disabled={isBusy}
                        style={{
                          background: "rgba(0, 0, 0, 0.06)",
                          border: "1px solid rgba(0, 0, 0, 0.1)",
                          color: "var(--text-primary)",
                          borderRadius: "4px",
                          padding: "2px 8px",
                          cursor: isBusy ? "not-allowed" : "pointer",
                          fontWeight: 600,
                        }}
                      >
                        {t("chat_retry_btn")}
                      </button>
                    )}

                    {(msg.id || (msg.citations && msg.citations.length > 0)) && (
                      <button
                        onClick={() => handleOpenSources(msg.id, msg.citations)}
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "#0284c7",
                          padding: "2px 4px",
                          cursor: "pointer",
                          textDecoration: "underline",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "3px",
                          fontWeight: 500,
                        }}
                      >
                        <span>{t("chat_view_sources")}</span>
                        {msg.citations && msg.citations.length > 0 && ` (${msg.citations.length})`}
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}

            {/* In-flight status bubble */}
            {isBusy && status === "retrieving" && (
              <div
                className="chat-bubble chat-bubble-assistant"
                style={{
                  alignSelf: "flex-start",
                  backgroundColor: "rgba(255, 255, 255, 0.9)",
                  border: "1px solid rgba(0, 0, 0, 0.08)",
                  padding: "10px 16px",
                  borderRadius: "14px",
                  fontSize: "13px",
                  color: "var(--text-secondary)",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  boxShadow: "0 2px 8px rgba(0, 0, 0, 0.03)",
                }}
              >
                <span
                  style={{
                    display: "inline-block",
                    width: "12px",
                    height: "12px",
                    border: "2px solid var(--accent-primary)",
                    borderTopColor: "transparent",
                    borderRadius: "50%",
                    animation: "spin 1s linear infinite",
                  }}
                />
                <span>{t("chat_status_retrieving")}</span>
              </div>
            )}

            {isBusy && status === "generating" && messages[messages.length - 1]?.role !== "assistant" && (
              <div
                className="chat-bubble chat-bubble-assistant"
                style={{
                  alignSelf: "flex-start",
                  backgroundColor: "rgba(255, 255, 255, 0.9)",
                  border: "1px solid rgba(0, 0, 0, 0.08)",
                  padding: "10px 16px",
                  borderRadius: "14px",
                  fontSize: "13px",
                  color: "var(--text-secondary)",
                  fontStyle: "italic",
                  boxShadow: "0 2px 8px rgba(0, 0, 0, 0.03)",
                }}
              >
                {t("chat_status_generating")}
              </div>
            )}

            {/* Error Banner */}
            {error && (
              <div
                style={{
                  backgroundColor: "rgba(239, 68, 68, 0.08)",
                  border: "1px solid rgba(239, 68, 68, 0.25)",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  fontSize: "13px",
                  color: "#dc2626",
                }}
              >
                {getErrorMessage()}
              </div>
            )}

            <div ref={chatBottomRef} />
          </div>

          <ClarificationChipsBar
            options={clarifyOptions || []}
            onSelect={(option) => {
              dismissClarify();
              send(option);
            }}
          />

          {/* Quick preset prompts */}
          <div
            className="preset-prompt-list"
            style={{
              padding: isMobile ? "0 8px" : "0 20px",
              gap: "6px",
              marginBottom: isMobile ? "4px" : "8px",
              display: "flex",
              flexWrap: "wrap",
            }}
          >
            <button
              className="preset-prompt-btn"
              style={{
                fontSize: isMobile ? "11px" : "12px",
                padding: isMobile ? "3px 8px" : "4px 10px",
                backgroundColor: "rgba(255, 255, 255, 0.8)",
                border: "1px solid rgba(0, 0, 0, 0.08)",
                borderRadius: "14px",
                color: "var(--text-primary)",
                cursor: isBusy ? "not-allowed" : "pointer",
                boxShadow: "0 1px 2px rgba(0, 0, 0, 0.03)",
              }}
              disabled={isBusy}
              onClick={() => handleSend(t("chat_preset_me"))}
            >
              {lang === "en" ? "ME Workout" : "Bài tập ME"}
            </button>
            <button
              className="preset-prompt-btn"
              style={{
                fontSize: isMobile ? "11px" : "12px",
                padding: isMobile ? "3px 8px" : "4px 10px",
                backgroundColor: "rgba(255, 255, 255, 0.8)",
                border: "1px solid rgba(0, 0, 0, 0.08)",
                borderRadius: "14px",
                color: "var(--text-primary)",
                cursor: isBusy ? "not-allowed" : "pointer",
                boxShadow: "0 1px 2px rgba(0, 0, 0, 0.03)",
              }}
              disabled={isBusy}
              onClick={() => handleSend(t("chat_preset_8020"))}
            >
              {lang === "en" ? "80/20 Rule" : "Quy tắc 80/20"}
            </button>
          </div>

          {/* Input Bar */}
          <div
            className="chat-input-bar"
            style={{
              padding: isMobile ? "10px 12px" : "14px 18px",
              borderTop: "1px solid rgba(0, 0, 0, 0.06)",
              backgroundColor: "rgba(255, 255, 255, 0.5)",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <input
              type="text"
              className="chat-input"
              style={{
                flex: 1,
                padding: isMobile ? "9px 14px" : "12px 16px",
                fontSize: "14px",
                backgroundColor: "rgba(255, 255, 255, 0.9)",
                border: "1px solid rgba(0, 0, 0, 0.12)",
                borderRadius: "8px",
                color: "var(--text-primary)",
                outline: "none",
              }}
              placeholder={t("chat_input_placeholder")}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              disabled={isBusy}
            />
            <button
              className="chat-send-btn"
              style={{
                width: isMobile ? "38px" : "42px",
                height: isMobile ? "38px" : "42px",
                backgroundColor: !inputText.trim() || isBusy ? "rgba(0, 0, 0, 0.06)" : "var(--accent-primary)",
                color: !inputText.trim() || isBusy ? "var(--text-muted)" : "#ffffff",
                border: "none",
                borderRadius: "8px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: !inputText.trim() || isBusy ? "not-allowed" : "pointer",
                opacity: !inputText.trim() || isBusy ? 0.6 : 1,
                boxShadow: !inputText.trim() || isBusy ? "none" : "0 2px 8px rgba(25, 206, 139, 0.3)",
              }}
              onClick={() => handleSend()}
              disabled={!inputText.trim() || isBusy}
            >
              <svg width={isMobile ? "15" : "17"} height={isMobile ? "15" : "17"} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Sources Drawer */}
      <ChatSources
        isOpen={isSourcesOpen}
        onClose={handleCloseSources}
        sources={selectedMessageSources || fallbackSources}
        lang={lang}
      />
    </div>
  );
}
