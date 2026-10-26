"use client";
import React from "react";
import { LEVELS, needsDebrief, type BRace, type Lang } from "../lib/bRace";

interface Props {
  plan: { race_name: string; race_date: string; b_races?: BRace[] | null };
  lang: Lang;
  today: string; // YYYY-MM-DD
  onAdd: () => void;
  onOpen: (race: BRace) => void;
  onDebrief: (race: BRace) => void;
}

const T = {
  en: { title: "NEXT RACES", add: "+ Add race", goal: "Goal", b: "B-race", a: "A-race", debrief: (n: string) => `How did ${n} go?`, training: "training run" },
  vi: { title: "CÁC RACE SẮP TỚI", add: "+ Thêm race", goal: "Mục tiêu", b: "B-race", a: "A-race", debrief: (n: string) => `${n} thế nào?`, training: "chạy như buổi tập" },
} as const;

const dateBadge = (iso: string, lang: Lang) => {
  const d = new Date(`${iso}T00:00:00`);
  return { month: d.toLocaleDateString(lang === "vi" ? "vi-VN" : "en-GB", { month: "short" }).toUpperCase(), day: d.getDate() };
};

/** The plan's B-races and the A-race, by date, each with its badge. */
export default function NextRaces({ plan, lang, today, onAdd, onOpen, onDebrief }: Props) {
  const t = T[lang] ?? T.en;
  const races = (plan.b_races ?? []).filter((r) => r.status !== "cancelled");
  type Row = { kind: "b"; race: BRace; date: string } | { kind: "a"; date: string };
  const rows: Row[] = [...races.map((race) => ({ kind: "b" as const, race, date: race.race_date })), { kind: "a" as const, date: plan.race_date }]
    .sort((x, y) => x.date.localeCompare(y.date));

  return (
    <section aria-label={t.title} style={{ background: "var(--bg-card, #fff)", border: "1px solid var(--border-color, #dfe5e0)", borderRadius: "14px", padding: "12px 14px", display: "flex", flexDirection: "column", gap: "8px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "0.5px", color: "var(--text-secondary, #5b6b63)" }}>{t.title}</span>
        <button type="button" onClick={onAdd} style={{ border: "none", background: "none", color: "var(--accent-primary, #2f7a55)", fontWeight: 600, fontSize: "13px", minHeight: 44, cursor: "pointer" }}>{t.add}</button>
      </div>
      {rows.map((row) => {
        const b = row.kind === "b" ? row.race : null;
        const { month, day } = dateBadge(row.date, lang);
        const level = b ? LEVELS[b.verdict.level] : null;
        const name = b ? b.race_name : plan.race_name;
        const sub = b ? `${t.b} · ${b.distance_km} km${b.effort === "training" ? ` · ${t.training}` : ""}` : t.a;
        const body = (
          <>
            <span aria-hidden="true" style={{ width: 44, height: 44, borderRadius: 10, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 700, flexShrink: 0,
              background: b ? "#e6f2ea" : "#17231d", color: b ? "#1f5a3e" : "#fff" }}>
              <span>{month}</span><span style={{ fontSize: 15 }}>{day}</span>
            </span>
            <span style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: 2, textAlign: "left" }}>
              <span data-testid="next-race-name" style={{ fontSize: 14, fontWeight: 600 }}>{name}</span>
              <span style={{ fontSize: 12, color: "var(--text-secondary, #5b6b63)" }}>{sub}</span>
            </span>
            <span style={{ fontSize: 11, fontWeight: 700, padding: "3px 9px", borderRadius: 999, whiteSpace: "nowrap",
              background: level ? level.bg : "#17231d", color: level ? level.fg : "#fff" }}>
              {level ? level[lang] : t.goal}
            </span>
          </>
        );
        return (
          <div key={b ? `b-${b.id}` : "a"} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {b ? (
              <button type="button" onClick={() => onOpen(b)} style={{ display: "flex", gap: 10, alignItems: "center", border: "none", background: "none", padding: 0, cursor: "pointer", color: "inherit", minHeight: 44 }}>{body}</button>
            ) : (
              <div style={{ display: "flex", gap: 10, alignItems: "center", minHeight: 44 }}>{body}</div>
            )}
            {b && needsDebrief(b, today) && (
              <button type="button" onClick={() => onDebrief(b)} className="btn btn-secondary" style={{ alignSelf: "flex-start", minHeight: 40, padding: "0 14px", borderRadius: 999, fontSize: 13 }}>
                {t.debrief(b.race_name)}
              </button>
            )}
          </div>
        );
      })}
    </section>
  );
}
