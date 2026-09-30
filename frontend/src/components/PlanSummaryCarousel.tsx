"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useRef, useState } from "react";
import BottomSheet from "./BottomSheet";
import styles from "./PlanSummaryCarousel.module.css";
import { daysToRace, planWeeklyVolumes, weekDayStates } from "../utils/planSummary";

const CARDS = ["Volume", "Race & goal", "This week", "Phase"] as const;
const DOT_LABELS = ["Show volume", "Show race and goal", "Show this week", "Show phase"];

const PHASE_PURPOSE: [string, string][] = [
  ["base", "Build aerobic endurance with easy, consistent running."],
  ["build", "Add race-specific fitness on top of your aerobic base."],
  ["peak", "Sharpen with your hardest, most race-like sessions."],
  ["taper", "Cut volume to arrive at the start line fresh."],
  ["recovery", "Absorb the work; rest is the training."],
  ["transition", "Ease back into structured training."],
];


interface Props {
  activePlan: any;
  workouts: any[];
  selectedWeek: number;
  maxGeneratedWeek: number;
  distanceKm: number;
  elevationM: number;
  goalPill: React.ReactNode;
  onAdaptWeek?: () => void;
  reviewContent?: React.ReactNode;
  onOpenPaceStrategy: () => void;
  onOpenGoalDeterminer: () => void;
  onOpenNutrition: () => void;
}

export default function PlanSummaryCarousel(p: Props) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(0);
  const [toolsOpen, setToolsOpen] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);

  useEffect(() => {
    const track = trackRef.current;
    if (!track || typeof IntersectionObserver === "undefined") return;
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting && e.intersectionRatio >= 0.6) {
            setActive(Number((e.target as HTMLElement).dataset.idx));
          }
        }
      },
      { root: track, threshold: 0.6 },
    );
    Array.from(track.children).forEach((c) => io.observe(c));
    return () => io.disconnect();
  }, []);

  const goTo = (i: number) => {
    const card = trackRef.current?.children[i] as HTMLElement | undefined;
    if (!card || !card.scrollIntoView) return;
    const reduce = typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    card.scrollIntoView({ behavior: reduce ? "auto" : "smooth", inline: "start", block: "nearest" });
    setActive(i);
  };

  const weeks = planWeeklyVolumes(p.workouts, p.activePlan.total_weeks);
  const generated = weeks.filter((w) => w.generated);
  const totalHours = generated.reduce((s, w) => s + w.mins, 0) / 60;
  const totalGain = generated.reduce((s, w) => s + w.gainM, 0);
  const maxMins = Math.max(1, ...weeks.map((w) => w.mins));
  const volumeHeader = `${totalHours.toFixed(1)} h${totalGain > 0 ? ` · +${Math.round(totalGain).toLocaleString("en-US")} m` : ""} planned`;

  const days = daysToRace(p.activePlan.race_date);
  const isToday = days === 0;
  const weekWos = p.workouts.filter((w: any) => w.week_number === p.selectedWeek);
  const dayStates = weekDayStates(weekWos);
  const trainingDays = dayStates.filter((d) => d.state !== "rest");
  const doneCount = trainingDays.filter((d) => d.state === "done").length;

  const phaseName: string = weekWos[0]?.phase || "";
  const phaseWeeks = Array.from(new Set(p.workouts.filter((w: any) => w.phase === phaseName).map((w: any) => w.week_number))).sort((a: any, b: any) => a - b);
  const weekInPhase = phaseWeeks.indexOf(p.selectedWeek) + 1;
  const purpose = PHASE_PURPOSE.find(([k]) => phaseName.toLowerCase().includes(k))?.[1] || "";

  const label: React.CSSProperties = { fontSize: "10px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 700 };
  const big: React.CSSProperties = { fontSize: "16px", fontWeight: 800, color: "var(--accent-primary)" };
  const textBtn: React.CSSProperties = { background: "none", border: "none", padding: "4px 0", cursor: "pointer", fontSize: "12px", fontWeight: 600, color: "var(--accent-primary)" };
  const rowBtn: React.CSSProperties = { display: "block", width: "100%", minHeight: "48px", textAlign: "left", padding: "0 12px", border: "1px solid var(--border-color)", borderRadius: "10px", background: "transparent", fontSize: "14px", fontWeight: 600, cursor: "pointer", marginBottom: "8px", color: "var(--text-primary)" };
  const pick = (fn: () => void) => () => { setToolsOpen(false); fn(); };

  return (
    <section aria-label="Plan summary" style={{ margin: "8px 0 12px" }}>
      <div className={styles.track} ref={trackRef}>
        <section className={styles.card} data-idx={0} aria-label={CARDS[0]}>
          <span style={label}>Volume</span>
          <span style={big}>{volumeHeader}</span>
          <div style={{ display: "flex", alignItems: "flex-end", gap: "3px", flex: 1, minHeight: 0 }}>
            {weeks.map((w) => (
              <div
                key={w.week}
                title={`Week ${w.week}${w.generated ? `: ${w.hours} h` : ""}`}
                data-testid={`vol-bar-${w.week}`}
                style={{
                  flex: 1,
                  height: w.generated ? `${Math.max(8, (w.mins / maxMins) * 100)}%` : "30%",
                  borderRadius: "3px",
                  background: !w.generated ? "transparent" : w.week === p.selectedWeek ? "var(--accent-primary)" : "rgba(0,0,0,0.18)",
                  border: w.generated ? "none" : "1px dashed rgba(0,0,0,0.3)",
                }}
              />
            ))}
          </div>
        </section>

        <section className={styles.card} data-idx={1} aria-label="Race and goal">
          <span style={label}>Race &amp; goal</span>
          <span style={{ fontSize: "15px", fontWeight: 700, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{p.activePlan.race_name}</span>
          <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
            {[p.distanceKm ? `${p.distanceKm} km` : "", p.elevationM ? `+${p.elevationM} m` : "", p.activePlan.race_date].filter(Boolean).join(" · ")}
          </span>
          {days !== null && <span style={big}>{isToday ? "Race day" : `${days} days to go`}</span>}
          <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
            {p.goalPill}
            <button type="button" onClick={() => setToolsOpen(true)} style={{ background: "none", border: "none", padding: "4px 0", cursor: "pointer", fontSize: "12px", fontWeight: 600, color: "var(--accent-primary)" }}>Race tools</button>
          </div>
        </section>

        <section className={styles.card} data-idx={2} aria-label={CARDS[2]}>
          <span style={label}>This week</span>
          <span style={big}>{doneCount} of {trainingDays.length} done</span>
          <div style={{ display: "flex", gap: "8px" }}>
            {dayStates.map((d) => (
              <span
                key={d.day}
                role="img"
                aria-label={`${d.day}: ${d.state}`}
                style={{ width: "18px", height: "18px", display: "inline-flex", alignItems: "center", justifyContent: "center", boxSizing: "border-box", borderRadius: "50%", fontSize: "11px", fontWeight: 800, lineHeight: 1,
                  background: d.state === "done" ? "var(--accent-primary)" : "transparent",
                  color: d.state === "done" ? "#fff" : d.state === "missed" ? "var(--accent-alert, #d9534f)" : "var(--text-muted)",
                  border: d.state === "done" || d.state === "rest" ? "none" : `1.5px solid ${d.state === "missed" ? "var(--accent-alert, #d9534f)" : "rgba(0,0,0,0.35)"}` }}
              >
                {d.state === "done" ? "✓" : d.state === "missed" ? "×" : d.state === "rest" ? "–" : ""}
              </span>
            ))}
          </div>
          <div style={{ display: "flex", gap: "16px" }}>
            {p.reviewContent && (
              <button type="button" onClick={() => setReviewOpen(true)} style={textBtn}>Review week</button>
            )}
            {p.onAdaptWeek && p.selectedWeek <= p.maxGeneratedWeek && (
              <button type="button" onClick={p.onAdaptWeek} style={textBtn}>Adapt Week {p.selectedWeek}</button>
            )}
          </div>
        </section>

        <section className={styles.card} data-idx={3} aria-label={CARDS[3]}>
          <span style={label}>Phase</span>
          <span style={big}>{phaseName || "Training"}</span>
          {weekInPhase > 0 && <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>Week {weekInPhase} of {phaseWeeks.length} in {phaseName}</span>}
          {purpose && <span style={{ fontSize: "12.5px", lineHeight: 1.4 }}>{purpose}</span>}
        </section>
      </div>

      <div className={styles.dots}>
        {DOT_LABELS.map((l, i) => (
          <button key={l} type="button" className={styles.dot} aria-label={l} aria-current={active === i ? "true" : undefined} onClick={() => goTo(i)}>
            <span className={`${styles.dotMark} ${active === i ? styles.dotActive : ""}`} />
          </button>
        ))}
      </div>

      <BottomSheet isOpen={toolsOpen} onClose={() => setToolsOpen(false)} title="Race tools">
        <button type="button" style={rowBtn} onClick={pick(p.onOpenPaceStrategy)}>Pace Strategy</button>
        <button type="button" style={rowBtn} onClick={pick(p.onOpenGoalDeterminer)}>Goal Determiner</button>
        <button type="button" style={rowBtn} onClick={pick(p.onOpenNutrition)}>Nutrition Lab</button>
      </BottomSheet>
      <BottomSheet isOpen={reviewOpen} onClose={() => setReviewOpen(false)} title={`Week ${p.selectedWeek} review`}>
        {p.reviewContent}
      </BottomSheet>
    </section>
  );
}
