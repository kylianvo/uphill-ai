/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useRef } from "react";
import { useAppContext } from "../contexts/AppContext";
import { useKnowledge } from "../hooks/useKnowledge";
import { translations } from "../app/translations";
import { KnowledgeCard } from "../components/KnowledgeCard";
import { Brain, Lightbulb, Trash } from "@phosphor-icons/react";

export default function KnowledgeView({ isMobile }: { isMobile: boolean }) {
  const ctx = useAppContext();
  const { user, lang, sources, knowledgeTopics, knowledgeTopic, knowledgeCards, extractStatus, ragLoading, ragErrorMsg, linkInput, setLinkInput, dailyCards } = ctx;
  const { handleAddLink, handlePdfFileChange, handleDeleteSource, shuffleDailyCards, filterKnowledgeByTopic } = useKnowledge();
  const t = (key: keyof typeof translations.en) => translations[lang]?.[key] || translations.en[key] || key;
  const pdfInputRef = useRef<HTMLInputElement>(null);
  const triggerPdfUpload = () => pdfInputRef.current?.click();

    const isExtracting = extractStatus.status === "extracting";
    const hasCards = knowledgeCards.length > 0 || dailyCards.length > 0;

    return (
      <div style={{ maxWidth: "860px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>

        {/* Extraction status banner */}
        {isExtracting && (
          <div style={{
            padding: "16px 20px", borderRadius: "12px",
            background: "linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.15))",
            border: "1px solid rgba(139,92,246,0.3)", display: "flex", alignItems: "center", gap: "12px",
          }}>
            <div style={{ fontSize: "20px", animation: "spin 2s linear infinite" }}><Brain weight="bold" /></div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: "700", fontSize: "13px", color: "var(--text-bright)", marginBottom: "4px" }}>
                {lang === "en" ? "Building your Knowledge Hub…" : "Đang tạo Thư viện Kiến thức…"}
              </div>
              <div style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                {extractStatus.current_topic
                  ? `${lang === "en" ? "Extracting:" : "Đang trích xuất:"} ${extractStatus.current_topic} (${extractStatus.progress ?? 0}/${extractStatus.total ?? 8})`
                  : (lang === "en" ? "Querying NotebookLM and structuring knowledge cards…" : "Đang truy vấn NotebookLM và cấu trúc các thẻ kiến thức…")}
              </div>
              <div style={{ marginTop: "6px", height: "4px", borderRadius: "4px", background: "rgba(255,255,255,0.1)", overflow: "hidden" }}>
                <div style={{
                  height: "100%", borderRadius: "4px",
                  background: "linear-gradient(90deg, #34d399, #10b981)",
                  width: `${(((extractStatus.progress ?? 0) / (extractStatus.total ?? 8)) * 100)}%`,
                  transition: "width 0.5s ease",
                }} />
              </div>
            </div>
          </div>
        )}

        {/* ① Daily Knowledge */}
        <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <Lightbulb size={26} color="var(--accent-primary)" weight="duotone" />
              <div>
                <h3 style={{ margin: 0, fontSize: isMobile ? "16px" : "20px", fontWeight: "800" }}>{t("home_daily_insight")}</h3>
                <p style={{ margin: 0, fontSize: "12px", color: "var(--text-secondary)" }}>{t("home_daily_desc")}</p>
              </div>
            </div>
            {hasCards && (
              <button
                className="btn btn-secondary"
                style={{ fontSize: "12px", padding: "6px 14px", borderRadius: "8px", height: "32px", flexShrink: 0 }}
                onClick={shuffleDailyCards}
              >🔀 {t("home_shuffle_btn")}</button>
            )}
          </div>

          {!hasCards && !isExtracting && (
            <div style={{ textAlign: "center", padding: "32px 16px", color: "var(--text-muted)", fontSize: "13px" }}>
              {extractStatus.status === "no_notebooklm"
                ? t("home_connect_notebooklm")
                : t("home_no_cards_yet")}
            </div>
          )}

          {!hasCards && isExtracting && (
            <div style={{ textAlign: "center", padding: "32px 16px", color: "var(--text-muted)", fontSize: "13px" }}>
              ⏳ {t("home_extraction_in_progress")}
            </div>
          )}

          {dailyCards.length > 0 && (
            <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1.3fr 1fr 1.1fr", gap: "14px" }}>
              {dailyCards.map((card: any, i: any) => <KnowledgeCard key={i} card={card} />)}
            </div>
          )}
        </div>



        {/* ③ Sources / Upload (Admin only) */}
        {user?.role === "admin" && (
          <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
              <span style={{ fontSize: "24px" }}>📂</span>
              <h3 style={{ margin: 0, fontSize: isMobile ? "16px" : "18px", fontWeight: "800" }}>{t("know_indexed_files")}</h3>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "20px" }}>
              <label style={{ fontSize: "12.5px", fontWeight: "600", color: "var(--text-secondary)" }}>{t("know_ingest_link")}</label>
              <div style={{ display: "flex", gap: "8px" }}>
                <input type="text" className="chat-input" style={{ borderRadius: "8px", padding: "10px 14px", fontSize: "13px" }}
                  placeholder="https://uphillathlete.com/aerobic-training/" value={linkInput}
                  onChange={(e) => setLinkInput(e.target.value)} disabled={ragLoading} />
                <button className="btn btn-primary" style={{ borderRadius: "8px", padding: "8px 18px", fontSize: "13px", height: "40px", flexShrink: 0 }}
                  onClick={handleAddLink} disabled={ragLoading}>{t("know_submit_url")}</button>
              </div>
            </div>
            <div style={{ marginBottom: "20px" }}>
              <label style={{ display: "block", fontSize: "12.5px", fontWeight: "600", color: "var(--text-secondary)", marginBottom: "8px" }}>{t("know_upload_pdf")}</label>
              <button className="btn btn-secondary" style={{ borderRadius: "8px", padding: "10px 16px", fontSize: "13px", width: "100%", height: "40px", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}
                onClick={triggerPdfUpload} disabled={ragLoading}>
                {lang === "en" ? "📥 Choose & Upload PDF" : "📥 Chọn & Tải lên PDF"}
              </button>
              <input type="file" ref={pdfInputRef} onChange={handlePdfFileChange} style={{ display: "none" }} accept=".pdf" />
            </div>
            {ragLoading && <div style={{ color: "var(--accent-secondary)", fontSize: "13px", marginBottom: "12px" }}>{lang === "en" ? "Indexing contents…" : "Đang lập chỉ mục nội dung…"}</div>}
            {ragErrorMsg && <div style={{ color: "var(--accent-alert)", fontSize: "12px", padding: "10px", background: "rgba(239,68,68,0.08)", borderRadius: "8px", marginBottom: "12px" }}>{ragErrorMsg}</div>}
            <div style={{ borderTop: "1px solid var(--border-color)", paddingTop: "16px" }}>
              <h4 style={{ fontSize: "13px", fontWeight: "700", marginBottom: "10px" }}>{lang === "en" ? "Sources" : "Nguồn"} ({sources.length})</h4>
              <div style={{ maxHeight: "200px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "8px" }}>
                {sources.length === 0
                  ? <div style={{ color: "var(--text-muted)", fontSize: "12.5px", fontStyle: "italic", textAlign: "center", padding: "12px 0" }}>{t("know_no_files")}</div>
                  : sources.map((src: any) => (
                    <div key={src.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "rgba(255,255,255,0.1)", border: "1px solid var(--border-color)", borderRadius: "8px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", overflow: "hidden" }}>
                        <span>{src.type === "pdf" ? "📄" : src.type === "youtube" ? "📺" : "🌐"}</span>
                        <span style={{ fontSize: "13px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: isMobile ? "200px" : "450px" }} title={src.title}>{src.title}</span>
                      </div>
                      <button style={{ background: "none", border: "none", color: "rgba(239,68,68,0.7)", cursor: "pointer", fontSize: "14px", padding: "4px" }} onClick={() => handleDeleteSource(src.id)}><Trash weight="bold" /></button>
                    </div>
                  ))
                }
              </div>
            </div>
          </div>
        )}
      </div>
    );
}
