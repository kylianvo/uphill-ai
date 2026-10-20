"use client";

import React from "react";
import { Sparkle, WarningCircle } from "@phosphor-icons/react";
import { translations } from "../app/translations";
import type { WeekDiffChip } from "../utils/weekDiff";

export interface WeekBriefData {
  why: string;
  benefits: string[];
  watch: string | null;
}

interface WeekBriefProps {
  chips: WeekDiffChip[];
  brief?: WeekBriefData | null;
  lang: "en" | "vi";
}

const sign = (n: number) => (n > 0 ? `+${n}` : `−${Math.abs(n)}`);

/** Why this week's plan looks the way it does: change chips (always) and the coach's reasons (when written). */
export default function WeekBrief({ chips, brief, lang }: WeekBriefProps) {
  const t = (key: keyof typeof translations.en) => translations[lang]?.[key] || translations.en[key] || key;
  if (!chips.length && !brief) return null;
  const min = t("week_brief_min");
  const chipText = (c: WeekDiffChip) => {
    if (c.kind === "time") return `${sign(c.delta)} ${min}`;
    if (c.kind === "long") return `Long Run ${c.from} → ${c.to} ${min}`;
    return `${c.kind === "added" ? "+" : "−"}${c.count} ${c.type}`;
  };
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }} data-testid="week-brief">
      {chips.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "6px" }}>
          <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>{t("week_brief_vs_last")}</span>
          {chips.map((c, i) => (
            <span
              key={i}
              style={{
                border: "1px solid var(--border-color, rgba(0,0,0,0.12))",
                borderRadius: "999px",
                padding: "2px 9px",
                fontSize: "11.5px",
                fontWeight: 600,
                color: "var(--text-secondary)",
                background: "rgba(0,0,0,0.03)",
              }}
            >
              {chipText(c)}
            </span>
          ))}
        </div>
      )}
      {brief && (
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: "8px" }}>
            <Sparkle size={14} weight="fill" color="var(--accent-primary)" style={{ flexShrink: 0, marginTop: "3px" }} aria-hidden="true" />
            <p style={{ margin: 0, fontSize: "12.5px", lineHeight: 1.55, color: "var(--text-primary)" }}>
              <strong>{t("week_brief_why")}: </strong>
              {brief.why}
            </p>
          </div>
          {brief.benefits.length > 0 && (
            <ul style={{ margin: 0, paddingLeft: "22px", fontSize: "12px", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              {brief.benefits.map((b, i) => (
                <li key={i}>{b}</li>
              ))}
            </ul>
          )}
          {brief.watch && (
            <div style={{ display: "flex", alignItems: "flex-start", gap: "8px" }}>
              <WarningCircle size={14} weight="fill" color="#d97706" style={{ flexShrink: 0, marginTop: "2px" }} aria-hidden="true" />
              <span style={{ fontSize: "12px", color: "var(--text-primary)" }}>
                <strong>{t("week_brief_watch")}: </strong>
                {brief.watch}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
