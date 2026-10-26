"use client";

import React, { useEffect, useState } from "react";
import { headerText, milestoneLabel, typicalWeeksText, type Lang, type PlanMilestones } from "../lib/beginnerMilestones";

interface Props {
  milestones: PlanMilestones;
  lang: Lang;
  planId: number;
  weeksToEvent: number | null;
  onMark: (key: string) => void;
  onUndo: (key: string) => void;
  onUpgrade: () => void;
}

const T = {
  en: { done: "I did it", confirm: "Yes, mark it", cancel: "Not yet", undo: "Undo", reached: "Milestone reached", next: "Next", upgrade: "Next: First 10K", normal: "Repeating a week is normal. You move on when you're ready.", dismiss: "Nice", all: "All milestones", fewer: "Hide list" },
  vi: { done: "Mình làm được rồi", confirm: "Đúng, đánh dấu", cancel: "Chưa", undo: "Hoàn tác", reached: "Đã đạt cột mốc", next: "Tiếp theo", upgrade: "Tiếp: 10K đầu tiên", normal: "Lặp lại một tuần là bình thường. Bạn tiến tiếp khi sẵn sàng.", dismiss: "Tuyệt", all: "Tất cả cột mốc", fewer: "Ẩn danh sách" },
} as const;

const seenKey = (planId: number) => `uphill.milestonesSeen.${planId}`;
const readSeen = (planId: number): string[] | null => {
  try {
    const raw = localStorage.getItem(seenKey(planId));
    return raw ? (JSON.parse(raw) as string[]) : null;
  } catch {
    return null;
  }
};
const writeSeen = (planId: number, keys: string[]) => {
  try {
    localStorage.setItem(seenKey(planId), JSON.stringify(keys));
  } catch {
    /* storage unavailable: the celebration may repeat, nothing else breaks */
  }
};

/** The beginner's path to First 5K / First 10K: reached rows, the next one, and a one-time celebration. */
export default function MilestonePath({ milestones, lang, planId, weeksToEvent, onMark, onUndo, onUpgrade }: Props) {
  const t = T[lang] ?? T.en;
  const [confirming, setConfirming] = useState(false);
  // seen is read once; the toast shows the latest reached milestone the athlete has not been shown yet
  const [seen, setSeen] = useState<string[]>(() => readSeen(planId) ?? []);
  const [dismissed, setDismissed] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const achieved = milestones.items.filter((i) => i.achieved_at);
  const earned = achieved.filter((i) => i.source !== "baseline");
  const achievedKeys = achieved.map((i) => i.key).join(",");

  const fresh = earned.filter((i) => !seen.includes(i.key));
  const celebrate = !dismissed && fresh.length ? fresh[fresh.length - 1].key : null;

  useEffect(() => {
    writeSeen(planId, Array.from(new Set([...(readSeen(planId) ?? []), ...achievedKeys.split(",").filter(Boolean)])));
  }, [planId, achievedKeys]);

  const next = milestones.items.find((i) => i.key === milestones.next_key);
  const canUpgrade = milestones.target === "5k" && milestones.items.some((i) => i.key === "first_5k" && i.achieved_at);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }} data-testid="milestone-path">
      <span style={{ fontSize: "15px", fontWeight: 700 }}>{headerText(milestones, lang, weeksToEvent)}</span>
      {next && !showAll && (
        <div style={{ display: "flex", flexDirection: "column", gap: "2px", fontSize: "12.5px" }}>
          <span style={{ fontWeight: 700 }}>→ {milestoneLabel(next.key, lang)}</span>
          <span style={{ color: "var(--text-secondary)" }}>{typicalWeeksText(next, lang)}</span>
        </div>
      )}
      {showAll && (
      <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "4px", maxHeight: "96px", overflowY: "auto" }}>
        {milestones.items.map((i) => (
          <li key={i.key} style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12.5px", color: i.achieved_at ? "var(--text-primary)" : i.key === milestones.next_key ? "var(--text-primary)" : "var(--text-muted)", fontWeight: i.key === milestones.next_key ? 700 : 500 }}>
            <span aria-hidden>{i.achieved_at ? "✓" : i.key === milestones.next_key ? "→" : "○"}</span>
            <span style={{ flex: 1 }}>{milestoneLabel(i.key, lang)}</span>
            {i.key === milestones.next_key && <span style={{ fontWeight: 500, color: "var(--text-secondary)" }}>{typicalWeeksText(i, lang)}</span>}
            {i.achieved_at && (
              <button type="button" aria-label={`${t.undo} ${milestoneLabel(i.key, lang)}`} onClick={() => onUndo(i.key)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: "11px", color: "var(--text-muted)" }}>↺</button>
            )}
          </li>
        ))}
      </ul>
      )}
      {next && !confirming && (
        <button type="button" onClick={() => setConfirming(true)} style={{ alignSelf: "flex-start", background: "none", border: "none", padding: "4px 0", cursor: "pointer", fontSize: "12px", fontWeight: 600, color: "var(--accent-primary)" }}>{t.done}</button>
      )}
      {next && confirming && (
        <div style={{ display: "flex", gap: "12px", alignItems: "center", fontSize: "12px" }}>
          <button type="button" onClick={() => { setConfirming(false); onMark(next.key); }} style={{ fontWeight: 700, color: "var(--accent-primary)", background: "none", border: "none", cursor: "pointer" }}>{t.confirm}</button>
          <button type="button" onClick={() => setConfirming(false)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)" }}>{t.cancel}</button>
        </div>
      )}
      {canUpgrade && (
        <button type="button" className="btn btn-secondary" onClick={onUpgrade} style={{ alignSelf: "flex-start", minHeight: "36px", padding: "0 14px", borderRadius: "9999px", fontSize: "12px", fontWeight: 600 }}>{t.upgrade}</button>
      )}
      <button type="button" onClick={() => setShowAll((v) => !v)} style={{ alignSelf: "flex-start", background: "none", border: "none", padding: 0, cursor: "pointer", fontSize: "11.5px", color: "var(--text-muted)" }}>{showAll ? t.fewer : t.all}</button>
      {showAll && <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>{t.normal}</span>}
      {celebrate && (
        <div role="status" style={{ position: "fixed", left: "16px", right: "16px", bottom: "96px", zIndex: 1000, background: "#fff", border: "1px solid var(--accent-primary)", borderRadius: "16px", padding: "16px", boxShadow: "0 8px 30px rgba(0,0,0,0.18)", display: "flex", flexDirection: "column", gap: "6px" }}>
          <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--accent-primary)" }}>{t.reached}</span>
          <span style={{ fontSize: "17px", fontWeight: 800 }}>{milestoneLabel(celebrate, lang)}</span>
          {next && <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>{t.next}: {milestoneLabel(next.key, lang)}</span>}
          <button type="button" onClick={() => { setDismissed(true); setSeen(achieved.map((i) => i.key)); }} style={{ alignSelf: "flex-end", background: "none", border: "none", cursor: "pointer", fontWeight: 700, color: "var(--accent-primary)" }}>{t.dismiss}</button>
        </div>
      )}
    </div>
  );
}
