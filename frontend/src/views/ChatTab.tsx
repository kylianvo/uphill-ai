import React, { useEffect, useRef, useState } from "react";
import { useAppContext } from "../contexts/AppContext";
import { parseMarkdown } from "../utils/markdown";
import { translations } from "../app/translations";
import { useCoachChat } from "../hooks/useCoachChat";
import ChatSources from "../components/ChatSources";

export default function ChatTab({ isMobile }: { isMobile: boolean }) {
  const { lang } = useAppContext();
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const [inputText, setInputText] = useState("");
  const [isSourcesOpen, setIsSourcesOpen] = useState(false);

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
  } = useCoachChat();

  const t = (key: keyof typeof translations.en) =>
    translations[lang as keyof typeof translations]?.[key] || translations.en[key] || key;

  const isBusy = status === "admitting" || status === "retrieving" || status === "generating";

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
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

  const handleOpenSources = async (messageId?: number) => {
    if (!messageId) return;
    await fetchMessageSources(messageId);
    setIsSourcesOpen(true);
  };

  const handleCloseSources = () => {
    setIsSourcesOpen(false);
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
            backgroundColor: "#181b20",
            borderRadius: "12px",
            border: "1px solid #2d333b",
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
              borderBottom: "1px solid #2d333b",
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
              <span className="chat-header-title" style={{ fontSize: isMobile ? "13px" : "15px", fontWeight: 600 }}>
                {lang === "en" ? "Coach Uphill (AI)" : "Huấn luyện viên Uphill (AI)"}
              </span>
              <span
                style={{
                  fontSize: isMobile ? "11px" : "12px",
                  color: isBusy ? "#f59e0b" : "#9ca3af",
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
                  background: "transparent",
                  border: "1px solid #373e47",
                  color: "#9ca3af",
                  borderRadius: "6px",
                  padding: isMobile ? "3px 8px" : "4px 10px",
                  fontSize: isMobile ? "11px" : "12px",
                  cursor: isBusy ? "not-allowed" : "pointer",
                  opacity: isBusy ? 0.5 : 1,
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
                    backgroundColor: "#22272e",
                    border: "1px solid #373e47",
                    color: "#9ca3af",
                    borderRadius: "6px",
                    padding: "4px 12px",
                    fontSize: "12px",
                    cursor: isLoadingOlder ? "not-allowed" : "pointer",
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
                  color: "#9ca3af",
                }}
              >
                <div
                  style={{
                    width: isMobile ? "40px" : "50px",
                    height: isMobile ? "40px" : "50px",
                    borderRadius: "50%",
                    backgroundColor: "#22272e",
                    border: "1px solid #373e47",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    marginBottom: "12px",
                    color: "#10b981",
                  }}
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2L2 7l10 5 10-5-10-5z" />
                    <path d="M2 17l10 5 10-5" />
                    <path d="M2 12l10 5 10-5" />
                  </svg>
                </div>
                <h4 style={{ margin: "0 0 8px 0", color: "#f3f4f6", fontSize: isMobile ? "15px" : "18px" }}>
                  {t("chat_empty_title")}
                </h4>
                <p style={{ margin: "0 0 16px 0", maxWidth: "480px", fontSize: isMobile ? "12.5px" : "14px", lineHeight: "1.5" }}>
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
                  <span style={{ fontSize: "11.5px", backgroundColor: "#22272e", border: "1px solid #373e47", padding: "4px 10px", borderRadius: "16px", color: "#d1d5db" }}>
                    {t("chat_empty_cap_1")}
                  </span>
                  <span style={{ fontSize: "11.5px", backgroundColor: "#22272e", border: "1px solid #373e47", padding: "4px 10px", borderRadius: "16px", color: "#d1d5db" }}>
                    {t("chat_empty_cap_2")}
                  </span>
                  <span style={{ fontSize: "11.5px", backgroundColor: "#22272e", border: "1px solid #373e47", padding: "4px 10px", borderRadius: "16px", color: "#d1d5db" }}>
                    {t("chat_empty_cap_3")}
                  </span>
                  <span style={{ fontSize: "11.5px", backgroundColor: "#22272e", border: "1px solid #373e47", padding: "4px 10px", borderRadius: "16px", color: "#d1d5db" }}>
                    {t("chat_empty_cap_4")}
                  </span>
                </div>

                {/* Boundary notice */}
                <p style={{ margin: 0, fontSize: "11.5px", color: "#6b7280", maxWidth: "440px", fontStyle: "italic" }}>
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
                  maxWidth: isMobile ? "90%" : "80%",
                  fontSize: isMobile ? "13px" : "14.5px",
                  padding: isMobile ? "8px 12px" : "12px 18px",
                  borderRadius: "12px",
                  backgroundColor: msg.role === "user" ? "#2563eb" : "#22272e",
                  color: "#f3f4f6",
                  border: msg.role === "user" ? "none" : "1px solid #373e47",
                }}
              >
                <div>
                  {msg.role === "assistant" ? parseMarkdown(msg.content) : msg.content}
                </div>

                {/* Assistant footer: interrupted badge, retry button, sources button */}
                {msg.role === "assistant" && (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      marginTop: "8px",
                      paddingTop: "6px",
                      borderTop: "1px solid #2d333b",
                      fontSize: "11px",
                    }}
                  >
                    {msg.interrupted && (
                      <span
                        style={{
                          backgroundColor: "rgba(239, 68, 68, 0.15)",
                          color: "#f87171",
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
                          background: "#373e47",
                          border: "none",
                          color: "#e5e7eb",
                          borderRadius: "4px",
                          padding: "2px 8px",
                          cursor: isBusy ? "not-allowed" : "pointer",
                          fontWeight: 500,
                        }}
                      >
                        {t("chat_retry_btn")}
                      </button>
                    )}

                    {msg.id && (
                      <button
                        onClick={() => handleOpenSources(msg.id)}
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "#60a5fa",
                          padding: "2px 4px",
                          cursor: "pointer",
                          textDecoration: "underline",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "3px",
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
                  backgroundColor: "#22272e",
                  border: "1px solid #373e47",
                  padding: "10px 16px",
                  borderRadius: "12px",
                  fontSize: "13px",
                  color: "#9ca3af",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                <span
                  style={{
                    display: "inline-block",
                    width: "12px",
                    height: "12px",
                    border: "2px solid #60a5fa",
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
                  backgroundColor: "#22272e",
                  border: "1px solid #373e47",
                  padding: "10px 16px",
                  borderRadius: "12px",
                  fontSize: "13px",
                  color: "#9ca3af",
                  fontStyle: "italic",
                }}
              >
                {t("chat_status_generating")}
              </div>
            )}

            {/* Error Banner */}
            {error && (
              <div
                style={{
                  backgroundColor: "rgba(239, 68, 68, 0.12)",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  fontSize: "13px",
                  color: "#fca5a5",
                }}
              >
                {getErrorMessage()}
              </div>
            )}

            <div ref={chatBottomRef} />
          </div>

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
                backgroundColor: "#22272e",
                border: "1px solid #373e47",
                borderRadius: "14px",
                color: "#d1d5db",
                cursor: isBusy ? "not-allowed" : "pointer",
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
                backgroundColor: "#22272e",
                border: "1px solid #373e47",
                borderRadius: "14px",
                color: "#d1d5db",
                cursor: isBusy ? "not-allowed" : "pointer",
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
              borderTop: "1px solid #2d333b",
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
                backgroundColor: "#22272e",
                border: "1px solid #373e47",
                borderRadius: "8px",
                color: "#f3f4f6",
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
                backgroundColor: !inputText.trim() || isBusy ? "#2d333b" : "#2563eb",
                color: "#ffffff",
                border: "none",
                borderRadius: "8px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: !inputText.trim() || isBusy ? "not-allowed" : "pointer",
                opacity: !inputText.trim() || isBusy ? 0.6 : 1,
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
        sources={selectedMessageSources}
        lang={lang}
      />
    </div>
  );
}
