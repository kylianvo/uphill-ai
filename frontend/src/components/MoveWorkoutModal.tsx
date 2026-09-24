"use client";

import React from "react";
import { createPortal } from "react-dom";
import { ArrowsLeftRight, ArrowRight, X, Moon, CalendarBlank } from "@phosphor-icons/react";
import { DAY_ORDER, DAY_LABELS, dayLabel } from "../utils/dayLabels";
import { computeWorkoutDate, getMondayOfDate } from "../utils/planDate";
import { tr } from "../lib/scheduleProposals";

// Mirrors backend/services/calendar_rules.py's current_week: the same Monday-
// aligned, UTC-date-diff calculation computeCurrentWeek (utils/planDate) uses,
// but WITHOUT its [1, total_weeks] clamp. For a plan that hasn't started yet
// (start_date in the future) this can be 0 or negative -- the backend's guard
// rejects a move into a week outside [1, total_weeks] regardless, so the modal
// must not offer a week that a clamped "current week" would wrongly suggest is
// valid (e.g. offering "week 2" as next week when the plan hasn't started).
function unclampedCurrentWeek(startDateStr: string, now: Date): number {
  const cleanStr = startDateStr.slice(0, 10);
  const parts = cleanStr.split("-").map(Number);
  const parsed = new Date(parts[0], parts[1] - 1, parts[2]);
  const startMonday = getMondayOfDate(parsed);
  const startUtc = Date.UTC(startMonday.getFullYear(), startMonday.getMonth(), startMonday.getDate());
  const todayUtc = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
  const diffDays = Math.floor((todayUtc - startUtc) / 86400000);
  return Math.floor(diffDays / 7) + 1;
}

interface ModalWorkout {
  id?: number;
  day_of_week: string;
  title?: string;
  duration_minutes?: number;
  distance_km?: number;
  type?: string;
  week_number?: number;
}

interface MoveWorkoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  sourceDay: string;
  weekNumber: number;
  weekWos: ModalWorkout[];
  lang: string;
  onSwapDays: (day1: string, day2: string, weekNumberOverride?: number) => void;
  allWorkouts?: ModalWorkout[];
  plan?: { start_date?: string | null; total_weeks?: number | null; race_date?: string | null };
  onMoveWorkout?: (workoutId: number, targetWeek: number, targetDay: string) => void;
  today?: Date;
}

export function MoveWorkoutModal({
  isOpen,
  onClose,
  sourceDay,
  weekNumber,
  weekWos,
  lang,
  onSwapDays,
  allWorkouts,
  plan,
  onMoveWorkout,
  today,
}: MoveWorkoutModalProps) {
  // React hooks must be declared before any early return below.
  const [mode, setMode] = React.useState<"swap" | "move">("swap");
  const [pickedId, setPickedId] = React.useState<number | null>(null);
  const [targetWeek, setTargetWeek] = React.useState<number | null>(null);

  if (!isOpen) return null;
  if (typeof document === "undefined") return null;

  const isVi = lang === "vi";
  const sourceWos = weekWos.filter((w) => w.day_of_week === sourceDay);
  const sourceIsRest = sourceWos.length === 0;

  const handleSelectTarget = (targetDay: string) => {
    onSwapDays(sourceDay, targetDay, weekNumber);
    onClose();
  };

  const canMove = !!onMoveWorkout && !!plan?.start_date && !sourceIsRest;
  const now = today ?? new Date();
  const curWeek = plan?.start_date ? unclampedCurrentWeek(plan.start_date, now) : weekNumber;
  const showWeekTabs = canMove && Math.abs(weekNumber - curWeek) <= 1;
  const weekTabs = showWeekTabs
    ? [curWeek, curWeek + 1].filter((wk) => wk >= 1 && (!plan?.total_weeks || wk <= plan.total_weeks))
    : [];
  const defaultTargetWeek = weekTabs.length
    ? (weekTabs.includes(weekNumber) ? weekNumber : weekTabs[0])
    : weekNumber;
  const effectiveTargetWeek = targetWeek ?? defaultTargetWeek;
  const selectedId = pickedId ?? (sourceWos.length === 1 ? sourceWos[0].id ?? null : null);
  const pool = allWorkouts ?? weekWos;
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const poolForDate = pool.map((w) => ({ title: w.title ?? "", type: w.type ?? "", week_number: w.week_number ?? weekNumber }));
  const isPastDay = (day: string) => {
    if (!plan) return false;
    const d = computeWorkoutDate(plan, poolForDate, { day_of_week: day, week_number: effectiveTargetWeek });
    return !!d && d < startOfToday;
  };
  const occupied = (day: string) =>
    pool.some((w) => (w.week_number ?? weekNumber) === effectiveTargetWeek && w.day_of_week === day && w.id !== selectedId);

  return createPortal(
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(10, 15, 12, 0.45)",
        backdropFilter: "blur(4px)",
        zIndex: 2000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "max(16px, env(safe-area-inset-top)) 16px max(16px, env(safe-area-inset-bottom)) 16px",
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "var(--bg-card, #ffffff)",
          color: "var(--text-primary, #111827)",
          borderRadius: "18px",
          width: "100%",
          maxWidth: "460px",
          boxShadow: "0 20px 50px rgba(0,0,0,0.22)",
          border: "1px solid var(--border-color, rgba(0,0,0,0.08))",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          maxHeight: "90vh",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: "18px 20px 14px",
            borderBottom: "1px solid var(--border-color, rgba(0,0,0,0.08))",
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "10px",
                background: "rgba(16, 185, 129, 0.12)",
                color: "var(--accent-primary, #10b981)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <ArrowsLeftRight size={20} weight="bold" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700 }}>
                {isVi ? "Di chuyển hoặc Đổi ngày tập" : "Move or Swap Workout"}
              </h3>
              <p style={{ margin: "3px 0 0", fontSize: "12px", color: "var(--text-secondary, #6b7280)" }}>
                {isVi ? `Tuần ${weekNumber}` : `Week ${weekNumber}`} •{" "}
                <span style={{ fontWeight: 600, color: "var(--text-primary, #111827)" }}>
                  {DAY_LABELS[sourceDay]?.[isVi ? "vi" : "en"] || sourceDay}
                </span>{" "}
                ({sourceIsRest
                  ? (isVi ? "Nghỉ ngơi" : "Rest Day")
                  : sourceWos.map((w) => `${w.title || w.type} (${w.duration_minutes || 0}m)`).join(", ")})
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label={isVi ? "Đóng" : "Close"}
            style={{
              background: "transparent",
              border: "none",
              cursor: "pointer",
              padding: "6px",
              borderRadius: "8px",
              color: "var(--text-muted, #9ca3af)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <X size={18} weight="bold" />
          </button>
        </div>

        {canMove && (
          <div style={{ display: "flex", gap: "6px", padding: "12px 16px 0" }}>
            {(["swap", "move"] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                style={{
                  flex: 1, padding: "8px", borderRadius: "10px", fontSize: "12.5px", fontWeight: 700, cursor: "pointer",
                  border: "1px solid var(--border-color, rgba(0,0,0,0.08))",
                  background: mode === m ? "rgba(16, 185, 129, 0.12)" : "transparent",
                  color: mode === m ? "var(--accent-primary, #10b981)" : "inherit",
                }}
              >
                {tr(lang, m === "swap" ? "sched_mode_swap_day" : "sched_mode_move_one")}
              </button>
            ))}
          </div>
        )}
        {canMove && mode === "move" && (
          <div style={{ padding: "12px 16px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "10px" }}>
            {sourceWos.length > 1 && (
              <div>
                <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-muted, #9ca3af)", textTransform: "uppercase", marginBottom: "6px" }}>
                  {tr(lang, "sched_pick_session")}
                </div>
                <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                  {sourceWos.map((w) => (
                    <button
                      key={w.id}
                      type="button"
                      onClick={() => setPickedId(w.id ?? null)}
                      style={{
                        padding: "6px 10px", borderRadius: "8px", fontSize: "12.5px", cursor: "pointer",
                        border: selectedId === w.id ? "1px solid var(--accent-primary, #10b981)" : "1px solid var(--border-color, rgba(0,0,0,0.08))",
                        background: selectedId === w.id ? "rgba(16, 185, 129, 0.08)" : "transparent",
                      }}
                    >
                      {w.title || w.type} ({w.duration_minutes || 0}m)
                    </button>
                  ))}
                </div>
              </div>
            )}
            {weekTabs.length > 0 && (
              <div style={{ display: "flex", gap: "6px" }}>
                {weekTabs.map((wk) => (
                  <button
                    key={wk}
                    type="button"
                    onClick={() => setTargetWeek(wk)}
                    style={{
                      padding: "6px 12px", borderRadius: "8px", fontSize: "12.5px", fontWeight: 600, cursor: "pointer",
                      border: "1px solid var(--border-color, rgba(0,0,0,0.08))",
                      background: effectiveTargetWeek === wk ? "rgba(16, 185, 129, 0.12)" : "transparent",
                    }}
                  >
                    {tr(lang, wk === curWeek ? "sched_this_week" : "sched_next_week")}
                  </button>
                ))}
              </div>
            )}
            {DAY_ORDER.map((day) => {
              const isSelf = effectiveTargetWeek === weekNumber && day === sourceDay;
              if (isSelf) return null;
              const past = isPastDay(day);
              const disabled = past || selectedId == null;
              return (
                <button
                  key={day}
                  type="button"
                  disabled={disabled}
                  title={past ? tr(lang, "sched_past_day") : undefined}
                  onClick={() => {
                    if (selectedId == null) return;
                    onMoveWorkout!(selectedId, effectiveTargetWeek, day);
                    onClose();
                  }}
                  style={{
                    display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 14px",
                    borderRadius: "12px", minHeight: "48px", textAlign: "left", fontSize: "13px", fontWeight: 700,
                    border: "1px solid var(--border-color, rgba(0,0,0,0.08))", background: "var(--bg-secondary, rgba(0,0,0,0.02))",
                    cursor: disabled ? "not-allowed" : "pointer", opacity: disabled ? 0.45 : 1, color: "inherit",
                  }}
                >
                  <span>{dayLabel(day, lang)}</span>
                  <span style={{ fontSize: "11.5px", fontWeight: 600, color: "var(--text-muted, #9ca3af)" }}>
                    {past ? tr(lang, "sched_past_day") : occupied(day) ? tr(lang, "sched_double_day_hint") : ""}
                  </span>
                </button>
              );
            })}
          </div>
        )}

        {/* Day selection list */}
        {(!canMove || mode === "swap") && (
        <div style={{ padding: "12px 16px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-muted, #9ca3af)", textTransform: "uppercase", letterSpacing: "0.04em", padding: "4px 4px 2px" }}>
            {isVi ? "Chọn ngày đích:" : "Select target day:"}
          </div>

          {DAY_ORDER.map((targetDay) => {
            const isSelf = targetDay === sourceDay;
            const targetWos = weekWos.filter((w) => w.day_of_week === targetDay);
            const targetIsRest = targetWos.length === 0;

            if (isSelf) return null;

            return (
              <div
                key={targetDay}
                onClick={() => handleSelectTarget(targetDay)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "12px 14px",
                  borderRadius: "12px",
                  border: "1px solid var(--border-color, rgba(0,0,0,0.08))",
                  background: "var(--bg-secondary, rgba(0,0,0,0.02))",
                  cursor: "pointer",
                  transition: "all 120ms ease",
                  minHeight: "48px",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "var(--accent-primary, #10b981)";
                  e.currentTarget.style.background = "rgba(16, 185, 129, 0.05)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--border-color, rgba(0,0,0,0.08))";
                  e.currentTarget.style.background = "var(--bg-secondary, rgba(0,0,0,0.02))";
                }}
              >
                <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <CalendarBlank size={14} weight="bold" color="var(--text-muted, #9ca3af)" />
                    <span style={{ fontSize: "13px", fontWeight: 700 }}>
                      {DAY_LABELS[targetDay]?.[isVi ? "vi" : "en"] || targetDay}
                    </span>
                  </div>

                  {targetIsRest ? (
                    <div style={{ display: "flex", alignItems: "center", gap: "5px", marginTop: "2px" }}>
                      <Moon size={12} weight="fill" color="#9ca3af" />
                      <span style={{ fontSize: "11.5px", color: "var(--text-muted, #9ca3af)", fontWeight: 500 }}>
                        {isVi ? "Ngày nghỉ" : "Rest Day"}
                      </span>
                    </div>
                  ) : (
                    <div style={{ fontSize: "11.5px", color: "var(--text-secondary, #4b5563)", marginTop: "2px" }}>
                      {targetWos.map((w, idx) => (
                        <span key={w.id || idx}>
                          {idx > 0 && " • "}
                          {w.title || w.type} ({w.duration_minutes || 0}m{w.distance_km ? ` · ${w.distance_km}km` : ""})
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "5px",
                    padding: "6px 12px",
                    borderRadius: "8px",
                    fontSize: "12px",
                    fontWeight: 700,
                    background: targetIsRest ? "var(--accent-primary, #10b981)" : "rgba(0,0,0,0.06)",
                    color: targetIsRest ? "#ffffff" : "var(--text-primary, #111827)",
                    flexShrink: 0,
                  }}
                >
                  {targetIsRest ? (
                    <>
                      <ArrowRight size={13} weight="bold" />
                      <span>{isVi ? "Chuyển sang đây" : "Move here"}</span>
                    </>
                  ) : (
                    <>
                      <ArrowsLeftRight size={13} weight="bold" />
                      <span>{isVi ? "Đổi ngày" : "Swap"}</span>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
        )}

        {/* Footer info */}
        <div
          style={{
            padding: "10px 18px",
            background: "rgba(0,0,0,0.02)",
            borderTop: "1px solid var(--border-color, rgba(0,0,0,0.06))",
            fontSize: "11.5px",
            color: "var(--text-muted, #9ca3af)",
            textAlign: "center",
          }}
        >
          {isVi
            ? "Chạm vào một ngày để chuyển bài tập ngay lập tức mà không cần kéo thả."
            : "Tap a day to relocate workouts instantly without drag-and-drop."}
        </div>
      </div>
    </div>,
    document.body
  );
}
