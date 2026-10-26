"use client";
import React from "react";
import type { BRaceInput, Lang } from "../lib/bRace";

export interface SetupRace { race_name: string; race_date: string; distance_km: number | null }

const MAX = 3;
const T = {
  en: { title: "Other races before your goal (optional)", hint: "Coach Uphill checks each one and plans the taper and recovery around it.",
    add: "+ Add a tune-up race", race: "Race", date: "Date", km: "km", remove: "Remove" },
  vi: { title: "Các race khác trước race mục tiêu (không bắt buộc)", hint: "Coach Uphill sẽ xem từng race và sắp xếp taper, hồi phục quanh nó.",
    add: "+ Thêm race tập dượt", race: "Race", date: "Ngày", km: "km", remove: "Xoá" },
} as const;

/** The rows a plan request sends as `b_races`: a name and a date at least (the race list can fill the distance). */
export const completeRaces = (rows: SetupRace[] | undefined): BRaceInput[] =>
  (rows ?? [])
    .filter((r) => r.race_name.trim() && r.race_date)
    .map((r) => ({ race_name: r.race_name.trim(), race_date: r.race_date, distance_km: r.distance_km, effort: "race" as const }));

export default function BRaceSetupFields({ lang, value, onChange }: { lang: Lang; value: SetupRace[]; onChange: (v: SetupRace[]) => void }) {
  const t = T[lang] ?? T.en;
  const rows = value ?? [];
  const edit = (i: number, patch: Partial<SetupRace>) => onChange(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  const input: React.CSSProperties = { width: "100%", minHeight: 44, padding: "8px 10px", borderRadius: 8, border: "1px solid var(--border-color, #dfe5e0)", boxSizing: "border-box" };

  return (
    <fieldset style={{ border: "none", padding: 0, margin: "0 0 14px", display: "flex", flexDirection: "column", gap: 8 }}>
      <legend style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 4 }}>{t.title}</legend>
      <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{t.hint}</span>
      {rows.map((r, i) => (
        <div key={i} style={{ display: "grid", gridTemplateColumns: "minmax(0, 2fr) minmax(0, 1.4fr) minmax(0, 0.8fr) auto", gap: 6, alignItems: "end" }}>
          <label style={{ fontSize: 11 }}>{t.race}<input style={input} value={r.race_name} onChange={(e) => edit(i, { race_name: e.target.value })} /></label>
          <label style={{ fontSize: 11 }}>{t.date}<input type="date" style={input} value={r.race_date} onChange={(e) => edit(i, { race_date: e.target.value })} /></label>
          <label style={{ fontSize: 11 }}>{t.km}<input type="number" inputMode="decimal" style={input} value={r.distance_km ?? ""}
            onChange={(e) => edit(i, { distance_km: e.target.value === "" ? null : Number(e.target.value) })} /></label>
          <button type="button" aria-label={`${t.remove} ${r.race_name || i + 1}`} onClick={() => onChange(rows.filter((_, j) => j !== i))}
            style={{ minHeight: 44, minWidth: 44, border: "none", background: "none", cursor: "pointer", color: "var(--text-secondary)" }}>×</button>
        </div>
      ))}
      {rows.length < MAX && (
        <button type="button" onClick={() => onChange([...rows, { race_name: "", race_date: "", distance_km: null }])}
          style={{ alignSelf: "flex-start", minHeight: 44, border: "none", background: "none", color: "var(--accent-primary)", fontWeight: 600, cursor: "pointer", padding: 0 }}>
          {t.add}
        </button>
      )}
    </fieldset>
  );
}
