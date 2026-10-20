"use client";

import React from "react";
import type { MissedReason } from "../types";

const CHIPS: { key: MissedReason; en: string; vi: string }[] = [
  { key: "busy", en: "Busy", vi: "Bận" },
  { key: "sick", en: "Sick", vi: "Ốm" },
  { key: "pain", en: "Pain", vi: "Đau" },
  { key: "tired", en: "Tired", vi: "Mệt" },
  { key: "weather", en: "Weather", vi: "Thời tiết" },
  { key: "other", en: "Other", vi: "Khác" },
];

interface MissedReasonChipsProps {
  reason?: string | null;
  onSelect: (reason: MissedReason) => void;
  lang: string;
}

/** The six "why was it missed" chips; the saved one is highlighted. */
export default function MissedReasonChips({ reason, onSelect, lang }: MissedReasonChipsProps) {
  return (
    <>
      {CHIPS.map(({ key, en, vi }) => {
        const selected = reason === key;
        return (
          <button
            key={key}
            type="button"
            onClick={() => onSelect(key)}
            aria-pressed={selected}
            style={{
              border: `1px solid ${selected ? "#ef4444" : "var(--border-color, rgba(0,0,0,0.12))"}`,
              background: selected ? "rgba(239,68,68,0.12)" : "none",
              color: selected ? "#ef4444" : "var(--text-muted)",
              borderRadius: "999px",
              padding: "3px 10px",
              fontSize: "12px",
              cursor: "pointer",
            }}
          >
            {lang === "en" ? en : vi}
          </button>
        );
      })}
    </>
  );
}
