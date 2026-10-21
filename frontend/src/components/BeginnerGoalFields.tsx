"use client";

import React from "react";
import { ladderPreview, milestoneLabel, minimumWeeks, weeksUntilEvent, type Lang, type MilestoneTarget } from "../lib/beginnerMilestones";

export interface BeginnerGoalValue {
  milestone_target: MilestoneTarget;
  current_jog_min: number;
  event_name: string;
  event_date: string;
}

interface Props {
  value: BeginnerGoalValue;
  onChange: (next: BeginnerGoalValue) => void;
  startDate: string;
  lang: Lang;
}

const JOG_CHOICES = [0, 3, 10, 20];

const T = {
  en: {
    target: "Your goal", t5: "First 5K", t10: "First 10K", jog: "Longest jog without stopping today",
    notYet: "Not yet", min: "min", event: "I have an event in mind", eventName: "Event name (optional)", eventDate: "Event date",
    soon: (n: number) => `Most beginners need about ${n} weeks. Pick a later date, or plan to run/walk the event.`,
    path: "Your path", normal: "Repeating a week is normal. You move on when you're ready.",
  },
  vi: {
    target: "Mục tiêu của bạn", t5: "5K đầu tiên", t10: "10K đầu tiên", jog: "Quãng chạy liên tục dài nhất hiện tại",
    notYet: "Chưa chạy được", min: "phút", event: "Mình có một sự kiện cụ thể", eventName: "Tên sự kiện (không bắt buộc)", eventDate: "Ngày sự kiện",
    soon: (n: number) => `Phần lớn người mới cần khoảng ${n} tuần. Chọn ngày muộn hơn, hoặc chạy/đi bộ ở sự kiện.`,
    path: "Lộ trình của bạn", normal: "Lặp lại một tuần là bình thường. Bạn tiến tiếp khi sẵn sàng.",
  },
} as const;

const label: React.CSSProperties = { display: "block", fontSize: "12px", fontWeight: 600, marginBottom: "6px", color: "var(--text-secondary)" };
const chip = (on: boolean): React.CSSProperties => ({
  padding: "8px 14px", borderRadius: "9999px", fontSize: "13px", fontWeight: 600, cursor: "pointer", minHeight: "40px",
  border: `1.5px solid ${on ? "var(--accent-primary)" : "var(--border-color)"}`,
  background: on ? "rgba(0,0,0,0.04)" : "transparent", color: "var(--text-primary)",
});

/** Target, current jog, optional event and the ladder preview for a start_running plan (web onboarding and planner). */
export default function BeginnerGoalFields({ value, onChange, startDate, lang }: Props) {
  const t = T[lang] ?? T.en;
  const hasEvent = Boolean(value.event_date) || false;
  const [eventOn, setEventOn] = React.useState(hasEvent);
  const weeks = eventOn && value.event_date && startDate ? weeksUntilEvent(startDate, value.event_date) : null;
  const minimum = minimumWeeks(value.milestone_target, value.current_jog_min || null);
  const set = (patch: Partial<BeginnerGoalValue>) => onChange({ ...value, ...patch });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "14px" }} data-testid="beginner-goal-fields">
      <div>
        <span style={label}>{t.target}</span>
        <div style={{ display: "flex", gap: "8px" }}>
          {(["5k", "10k"] as const).map((k) => (
            <button key={k} type="button" aria-pressed={value.milestone_target === k} style={chip(value.milestone_target === k)} onClick={() => set({ milestone_target: k })}>
              {k === "5k" ? t.t5 : t.t10}
            </button>
          ))}
        </div>
      </div>
      <div>
        <span style={label}>{t.jog}</span>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {JOG_CHOICES.map((m) => (
            <button key={m} type="button" aria-pressed={value.current_jog_min === m} style={chip(value.current_jog_min === m)} onClick={() => set({ current_jog_min: m })}>
              {m === 0 ? t.notYet : m === 20 ? `20+ ${t.min}` : `${m === 3 ? "1–5" : m} ${t.min}`}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label style={{ ...label, display: "flex", alignItems: "center", gap: "8px" }}>
          <input
            type="checkbox"
            checked={eventOn}
            onChange={(e) => { setEventOn(e.target.checked); if (!e.target.checked) set({ event_name: "", event_date: "" }); }}
          />
          {t.event}
        </label>
        {eventOn && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
            <input className="chat-input" style={{ borderRadius: "8px", padding: "10px" }} placeholder={t.eventName} aria-label={t.eventName} value={value.event_name} onChange={(e) => set({ event_name: e.target.value })} />
            <input type="date" className="chat-input" style={{ borderRadius: "8px", padding: "10px" }} aria-label={t.eventDate} value={value.event_date} onChange={(e) => set({ event_date: e.target.value })} />
          </div>
        )}
        {eventOn && weeks !== null && weeks < minimum && (
          <div role="note" style={{ marginTop: "8px", fontSize: "12px", color: "var(--accent-alert, #b45309)" }}>{t.soon(minimum)}</div>
        )}
      </div>
      <div>
        <span style={label}>{t.path}</span>
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "3px", fontSize: "12.5px" }}>
          {ladderPreview(value.milestone_target).map((m) => {
            const done = m.jog !== undefined && m.jog <= value.current_jog_min;
            return (
              <li key={m.key} style={{ display: "flex", gap: "8px", color: done ? "var(--text-primary)" : "var(--text-secondary)" }}>
                <span aria-hidden>{done ? "✓" : "○"}</span>
                <span style={{ flex: 1 }}>{milestoneLabel(m.key, lang)}</span>
                <span style={{ color: "var(--text-muted)" }}>{lang === "vi" ? "tuần" : "wk"} {m.weeks[0]}–{m.weeks[1]}</span>
              </li>
            );
          })}
        </ul>
        <div style={{ marginTop: "6px", fontSize: "11.5px", color: "var(--text-muted)" }}>{t.normal}</div>
      </div>
    </div>
  );
}
