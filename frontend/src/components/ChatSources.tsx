import React, { useEffect } from "react";
import { CitationItem } from "../lib/coachChatStream";

interface ChatSourcesProps {
  isOpen: boolean;
  onClose: () => void;
  sources: {
    message_id: number;
    citations: CitationItem[];
    evidence: unknown[];
  } | null;
  lang: string;
}

export default function ChatSources({ isOpen, onClose, sources, lang }: ChatSourcesProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const isVi = lang === "vi";
  const citations = sources?.citations || [];
  const evidence = (sources?.evidence || []) as Array<{
    title?: string;
    domain?: string;
    content?: string;
    [key: string]: unknown;
  }>;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="chat-sources-title"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.6)",
        backdropFilter: "blur(4px)",
        zIndex: 9999,
        display: "flex",
        justifyContent: "flex-end",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "480px",
          height: "100%",
          backgroundColor: "rgba(255, 255, 255, 0.96)",
          backdropFilter: "blur(24px)",
          WebkitBackdropFilter: "blur(24px)",
          color: "var(--text-primary)",
          display: "flex",
          flexDirection: "column",
          boxShadow: "-8px 0 32px rgba(0, 0, 0, 0.08)",
          borderLeft: "1px solid rgba(0, 0, 0, 0.1)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: "16px 20px",
            borderBottom: "1px solid rgba(0, 0, 0, 0.08)",
            background: "rgba(0, 0, 0, 0.02)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <h3 id="chat-sources-title" style={{ margin: 0, fontSize: "16px", fontWeight: 600, color: "#111111" }}>
              {isVi ? "Tài liệu & Trích dẫn" : "Evidence & Citations"}
            </h3>
            <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              {isVi ? `Tin nhắn #${sources?.message_id ?? ""}` : `Message #${sources?.message_id ?? ""}`}
            </span>
          </div>
          <button
            onClick={onClose}
            aria-label={isVi ? "Đóng" : "Close"}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-muted)",
              cursor: "pointer",
              padding: "6px",
              borderRadius: "6px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflowY: "auto", padding: "16px 20px" }}>
          {citations.length === 0 && evidence.length === 0 ? (
            <div style={{ textAlign: "center", padding: "40px 20px", color: "var(--text-muted)" }}>
              <p style={{ margin: 0, fontSize: "14px" }}>
                {isVi
                  ? "Không có tài liệu trích dẫn ngoài nào cho câu trả lời này."
                  : "No external citations recorded for this response."}
              </p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {citations.length > 0 && (
                <div>
                  <h4
                    style={{
                      fontSize: "13px",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                      color: "var(--text-muted)",
                      marginBottom: "8px",
                      fontWeight: 600,
                    }}
                  >
                    {isVi ? "Trích dẫn đã dẫn nguồn" : "Referenced Sources"}
                  </h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                    {citations.map((cite, idx) => (
                      <div
                        key={idx}
                        style={{
                          backgroundColor: "rgba(255, 255, 255, 0.9)",
                          border: "1px solid rgba(0, 0, 0, 0.08)",
                          borderRadius: "8px",
                          padding: "12px 14px",
                          boxShadow: "0 1px 3px rgba(0, 0, 0, 0.03)",
                        }}
                      >
                        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                          {/* Top row: [1] index pill & book label */}
                          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "6px" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                              <span
                                style={{
                                  fontSize: "11px",
                                  fontWeight: "700",
                                  backgroundColor: "rgba(2, 132, 199, 0.1)",
                                  color: "#0284c7",
                                  padding: "2px 6px",
                                  borderRadius: "4px",
                                  border: "1px solid rgba(2, 132, 199, 0.25)",
                                }}
                              >
                                [{idx + 1}]
                              </span>
                              <span
                                style={{
                                  fontSize: "11.5px",
                                  fontWeight: "600",
                                  color: "#0369a1",
                                  display: "inline-flex",
                                  alignItems: "center",
                                  gap: "4px",
                                }}
                              >
                                📖 {cite.book || cite.source_label || "Training for the Uphill Athlete"}
                              </span>
                            </div>

                            {cite.domain && (
                              <span
                                style={{
                                  fontSize: "10.5px",
                                  textTransform: "uppercase",
                                  backgroundColor: "rgba(25, 206, 139, 0.12)",
                                  color: "#059669",
                                  padding: "2px 6px",
                                  borderRadius: "4px",
                                  fontWeight: 600,
                                }}
                              >
                                {cite.domain}
                              </span>
                            )}
                          </div>

                          {/* Chapter & Section badge */}
                          {(cite.chapter || cite.section) && (
                            <div
                              style={{
                                fontSize: "12px",
                                color: "#0f766e",
                                fontWeight: 600,
                                backgroundColor: "rgba(15, 118, 110, 0.06)",
                                padding: "4px 8px",
                                borderRadius: "6px",
                                border: "1px solid rgba(15, 118, 110, 0.15)",
                              }}
                            >
                              <span>{cite.chapter || ""}</span>
                              {cite.chapter && cite.section && <span style={{ opacity: 0.6 }}> &bull; </span>}
                              <span style={{ fontWeight: 400, color: "var(--text-muted)" }}>{cite.section || ""}</span>
                            </div>
                          )}

                          {/* Topic / Section Title */}
                          <span style={{ fontSize: "13.5px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
                            {cite.topic || cite.title || cite.source_id || `Source #${idx + 1}`}
                          </span>
                        </div>
                        {cite.quote && (
                          <blockquote
                            style={{
                              margin: "6px 0 0 0",
                              paddingLeft: "10px",
                              borderLeft: "2px solid var(--accent-primary)",
                              color: "var(--text-secondary)",
                              fontSize: "12.5px",
                              fontStyle: "italic",
                            }}
                          >
                            &ldquo;{cite.quote}&rdquo;
                          </blockquote>
                        )}
                        {cite.url && typeof cite.url === "string" && (cite.url.startsWith("https://") || cite.url.startsWith("http://")) && (
                          <div style={{ marginTop: "8px" }}>
                            <a
                              href={cite.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{
                                fontSize: "12px",
                                color: "#0284c7",
                                textDecoration: "none",
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "4px",
                                fontWeight: 500,
                              }}
                            >
                              <span>{isVi ? "Mở tài liệu nguồn" : "View original source"}</span>
                              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                                <polyline points="15 3 21 3 21 9" />
                                <line x1="10" y1="14" x2="21" y2="3" />
                              </svg>
                            </a>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {evidence.length > 0 && (
                <div>
                  <h4
                    style={{
                      fontSize: "13px",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                      color: "var(--text-muted)",
                      marginBottom: "8px",
                      fontWeight: 600,
                    }}
                  >
                    {isVi ? "Đoạn trích đối chiếu" : "Retrieved Context Excerpts"}
                  </h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                    {evidence.map((chunk, idx) => (
                      <div
                        key={idx}
                        style={{
                          backgroundColor: "rgba(249, 250, 251, 0.85)",
                          border: "1px solid rgba(0, 0, 0, 0.06)",
                          borderRadius: "8px",
                          padding: "10px 12px",
                          fontSize: "12px",
                          color: "var(--text-secondary)",
                          lineHeight: "1.5",
                        }}
                      >
                        {chunk.title && (
                          <div style={{ fontWeight: 600, color: "var(--text-primary)", marginBottom: "4px" }}>
                            {chunk.title}
                          </div>
                        )}
                        <div>{chunk.content ? String(chunk.content).slice(0, 300) + (String(chunk.content).length > 300 ? "..." : "") : ""}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
