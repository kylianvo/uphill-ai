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
          backgroundColor: "#181b20",
          color: "#f3f4f6",
          display: "flex",
          flexDirection: "column",
          boxShadow: "-8px 0 24px rgba(0,0,0,0.5)",
          borderLeft: "1px solid #2d333b",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: "16px 20px",
            borderBottom: "1px solid #2d333b",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <h3 id="chat-sources-title" style={{ margin: 0, fontSize: "16px", fontWeight: 600 }}>
              {isVi ? "Tài liệu & Trích dẫn" : "Evidence & Citations"}
            </h3>
            <span style={{ fontSize: "12px", color: "#9ca3af" }}>
              {isVi ? `Tin nhắn #${sources?.message_id ?? ""}` : `Message #${sources?.message_id ?? ""}`}
            </span>
          </div>
          <button
            onClick={onClose}
            aria-label={isVi ? "Đóng" : "Close"}
            style={{
              background: "transparent",
              border: "none",
              color: "#9ca3af",
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
            <div style={{ textAlign: "center", padding: "40px 20px", color: "#9ca3af" }}>
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
                      color: "#6b7280",
                      marginBottom: "8px",
                    }}
                  >
                    {isVi ? "Trích dẫn đã dẫn nguồn" : "Referenced Sources"}
                  </h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                    {citations.map((cite, idx) => (
                      <div
                        key={idx}
                        style={{
                          backgroundColor: "#22272e",
                          border: "1px solid #373e47",
                          borderRadius: "8px",
                          padding: "12px 14px",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                          {cite.domain && (
                            <span
                              style={{
                                fontSize: "11px",
                                textTransform: "uppercase",
                                backgroundColor: "#2d333b",
                                color: "#60a5fa",
                                padding: "2px 6px",
                                borderRadius: "4px",
                                fontWeight: 600,
                              }}
                            >
                              {cite.domain}
                            </span>
                          )}
                          <span style={{ fontSize: "14px", fontWeight: 600, color: "#e5e7eb" }}>
                            {cite.title || cite.source_id || `Source #${idx + 1}`}
                          </span>
                        </div>
                        {cite.quote && (
                          <blockquote
                            style={{
                              margin: "6px 0 0 0",
                              paddingLeft: "10px",
                              borderLeft: "2px solid #4b5563",
                              color: "#9ca3af",
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
                                color: "#38bdf8",
                                textDecoration: "none",
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "4px",
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
                      color: "#6b7280",
                      marginBottom: "8px",
                    }}
                  >
                    {isVi ? "Đoạn trích đối chiếu" : "Retrieved Context Excerpts"}
                  </h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                    {evidence.map((chunk, idx) => (
                      <div
                        key={idx}
                        style={{
                          backgroundColor: "#1c2128",
                          border: "1px solid #2d333b",
                          borderRadius: "8px",
                          padding: "10px 12px",
                          fontSize: "12px",
                          color: "#d1d5db",
                          lineHeight: "1.5",
                        }}
                      >
                        {chunk.title && (
                          <div style={{ fontWeight: 600, color: "#9ca3af", marginBottom: "4px" }}>
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
