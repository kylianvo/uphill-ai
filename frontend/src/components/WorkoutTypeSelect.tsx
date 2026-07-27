"use client";
import React from "react";
import { COACH_WORKOUT_TYPE_OPTIONS } from "../data/workoutLibrary";

export function WorkoutTypeSelect({
  value,
  onChange,
  lang,
  style,
}: {
  value: string;
  onChange: (value: string) => void;
  lang: string;
  style?: React.CSSProperties;
}) {
  const current = COACH_WORKOUT_TYPE_OPTIONS.find((o) => o.value === value);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "8px", ...style }}>
      <span
        aria-hidden="true"
        style={{
          width: "10px",
          height: "10px",
          borderRadius: "50%",
          background: current?.color || "#6b7280",
          flexShrink: 0,
        }}
      />
      <select
        className="chat-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{ flex: 1, borderRadius: "8px", padding: "8px 10px", fontSize: "13px" }}
      >
        {COACH_WORKOUT_TYPE_OPTIONS.map((o) => (
          <option key={o.value} value={o.value} style={{ color: o.color }}>
            {lang === "en" ? o.labelEn : o.labelVi}
          </option>
        ))}
      </select>
    </div>
  );
}
