"use client";

import React from "react";
import { Lightning, ShieldCheck, TrendUp } from "@phosphor-icons/react";
import {
  confidenceLabel,
  formatGoalTime,
  GoalAssessment,
  Lang,
  missingHints,
} from "@/lib/goalAssessment";

const METHOD_LABELS: Record<string, [string, string]> = {
  physics: ["Course physics from this result", "Mô hình cung đường từ kết quả này"],
  field_rank: ["Your finishing rank on this field", "Thứ hạng của bạn áp vào giải này"],
  percentile_transfer: ["Field percentile transfer", "Quy đổi theo percentile"],
  field_prior: ["Field position from weekly volume", "Vị trí trong đoàn theo khối lượng tuần"],
  easy_pace: ["Course physics from your easy pace", "Mô hình cung đường từ pace Easy"],
  base_pace: ["Course physics from your flat pace", "Mô hình cung đường từ pace đường bằng"],
};

export type GoalKey = "a" | "b" | "c";

export function GoalResult({
  assessment,
  lang,
  highlight,
  compact = false,
  renderActions,
}: {
  assessment: GoalAssessment;
  lang: Lang;
  highlight?: GoalKey | null;
  compact?: boolean;
  renderActions?: (mins: number, label: string) => React.ReactNode;
}) {
  const t = (en: string, vi: string) => (lang === "en" ? en : vi);
  const goals = assessment.goals;
  if (!goals) {
    return (
      <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
        {t(
          "Not enough data to estimate this race yet.",
          "Chưa đủ dữ liệu để ước tính race này.",
        )}
        <Hints assessment={assessment} lang={lang} />
      </div>
    );
  }
  const cards: { key: GoalKey; icon: React.ReactNode; label: string; note: string; mins: number }[] = [
    { key: "a", icon: <Lightning size={16} weight="duotone" />, label: t("Ambitious", "Tham vọng"), note: t("A great day", "Ngày thuận lợi"), mins: goals.a },
    { key: "b", icon: <TrendUp size={16} weight="duotone" />, label: t("Realistic", "Thực tế"), note: t("Your most likely day", "Khả năng cao nhất"), mins: goals.b },
    { key: "c", icon: <ShieldCheck size={16} weight="duotone" />, label: t("Safe", "An toàn"), note: t("Margin for problems", "Dự phòng sự cố"), mins: goals.c },
  ];
  const isAi = assessment.engine === "gemini" || assessment.engine === "gemini_retry";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: compact ? "8px" : "12px" }}>
        {cards.map((card) => {
          const on = highlight === card.key;
          return (
            <div
              key={card.key}
              style={{
                borderRadius: "12px",
                padding: compact ? "10px" : "14px",
                border: on ? "2px solid var(--accent-primary)" : "1px solid var(--border-color)",
                background: on ? "rgba(16,185,129,0.06)" : "rgba(255,255,255,0.6)",
                minWidth: 0,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "5px", color: "var(--accent-primary)", fontWeight: 700, fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.4px" }}>
                {card.icon} {card.label}
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: compact ? "20px" : "26px", fontWeight: 700, color: "var(--text-primary)", margin: "6px 0 2px" }}>
                {formatGoalTime(card.mins)}
              </div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{card.note}</div>
              {renderActions && <div style={{ marginTop: "10px" }}>{renderActions(card.mins, card.label)}</div>}
            </div>
          );
        })}
      </div>

      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center", fontSize: "11.5px" }}>
        <span style={{ padding: "2px 8px", borderRadius: "999px", background: "rgba(0,0,0,0.05)", fontWeight: 600, color: "var(--text-secondary)" }}>
          {confidenceLabel(assessment.confidence, lang)}
        </span>
        <span style={{ color: "var(--text-muted)" }}>
          {isAi
            ? t("Coach Uphill's judgement over the numbers below", "Đánh giá của Coach Uphill dựa trên các con số bên dưới")
            : t("Calculated estimate from the numbers below", "Ước tính tính toán từ các con số bên dưới")}
        </span>
      </div>

      {assessment.reasoning.length > 0 && assessment.lang && assessment.lang !== lang && (
        <div style={{ fontSize: "11.5px", color: "var(--text-muted)" }}>
          {t(
            "This reasoning was written in Vietnamese. Re-assess to get it in English.",
            "Phần giải thích này đang bằng tiếng Anh. Đánh giá lại để có bản tiếng Việt.",
          )}
        </div>
      )}

      {assessment.reasoning.length > 0 && (
        <ul style={{ margin: 0, paddingLeft: "18px", display: "flex", flexDirection: "column", gap: "4px", fontSize: "12.5px", color: "var(--text-primary)", lineHeight: 1.5 }}>
          {assessment.reasoning.map((line, i) => <li key={i}>{line}</li>)}
        </ul>
      )}

      <Hints assessment={assessment} lang={lang} />

      {assessment.anchors.length > 0 && (
        <details style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
          <summary style={{ cursor: "pointer", fontWeight: 600 }}>
            {t(`Numbers behind this (${assessment.anchors.length})`, `Các con số tham chiếu (${assessment.anchors.length})`)}
          </summary>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "8px" }}>
            {assessment.anchors.map((anchor) => (
              <div key={anchor.id} style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
                <span>
                  {(METHOD_LABELS[anchor.method] || [anchor.method, anchor.method])[lang === "en" ? 0 : 1]}
                  {anchor.notes.length > 0 && <span style={{ color: "var(--text-muted)" }}> · {anchor.notes.join(" · ")}</span>}
                </span>
                <strong style={{ fontFamily: "var(--font-mono)", color: "var(--text-primary)" }}>{formatGoalTime(anchor.minutes)}</strong>
              </div>
            ))}
          </div>
        </details>
      )}

      <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
        {t(
          "Goals are estimates from your data, not a guarantee of a finish time.",
          "Mục tiêu là ước tính từ dữ liệu của bạn, không đảm bảo thời gian về đích.",
        )}
      </div>
    </div>
  );
}

function Hints({ assessment, lang }: { assessment: GoalAssessment; lang: Lang }) {
  const hints = missingHints(assessment.missing, lang);
  if (!hints.length) return null;
  return (
    <div style={{ fontSize: "12px", color: "#b45309", display: "flex", flexDirection: "column", gap: "2px", marginTop: "6px" }}>
      <span style={{ fontWeight: 600 }}>{lang === "en" ? "To sharpen this:" : "Để chính xác hơn:"}</span>
      {hints.map((hint) => <span key={hint}>· {hint}</span>)}
    </div>
  );
}
