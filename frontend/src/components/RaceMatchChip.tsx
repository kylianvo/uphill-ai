import React from "react";
import { MapPin } from "@phosphor-icons/react";
import { RaceMatch } from "../hooks/useRaceMatch";

export function RaceMatchChip({
  match,
  lang,
  onChangeClick,
}: {
  match: RaceMatch | null;
  lang: "en" | "vi";
  onChangeClick?: () => void;
}) {
  if (!match) return null;

  const distancePart = match.distance_label
    ? `${match.distance_label}${match.elevation_gain_m ? `, ${match.elevation_gain_m}m D+` : ""}`
    : null;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "6px",
        marginTop: "6px",
        padding: "6px 10px",
        background: "rgba(16,185,129,0.08)",
        border: "1px solid var(--border-color)",
        borderRadius: "8px",
        fontSize: "12px",
        color: "var(--text-secondary)",
      }}
    >
      <MapPin size={14} weight="fill" />
      <span>
        {lang === "en" ? "Using " : "Đang dùng "}
        <strong>{match.race_name}</strong>
        {lang === "en" ? " as context" : " làm ngữ cảnh"}
        {distancePart ? ` — ${distancePart}` : ""}
        {onChangeClick && (
          <>
            {" · "}
            <button
              type="button"
              onClick={onChangeClick}
              style={{
                background: "none",
                border: "none",
                padding: 0,
                font: "inherit",
                color: "var(--accent-primary)",
                textDecoration: "underline",
                cursor: "pointer",
              }}
            >
              {lang === "en" ? "Change" : "Đổi"}
            </button>
          </>
        )}
      </span>
    </div>
  );
}
