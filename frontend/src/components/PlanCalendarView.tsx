/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useMemo, useState } from "react";
import { DndContext, DragEndEvent, useDraggable, useDroppable, useSensor, useSensors, PointerSensor, KeyboardSensor } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { CaretLeft, CaretRight, CheckCircle, Circle, X } from "@phosphor-icons/react";
import WorkoutCard from "./WorkoutCard";
import { getZoneColor } from "../data/workoutLibrary";
import { useWorkoutTypes, resolveWorkoutInfo } from "../hooks/useWorkoutTypes";

const DAY_SHORT_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const DAY_SHORT_VI = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];
const SLOT_ORDER: Record<string, number> = { morning: 0, main: 1, afternoon: 2 };

function isoDate(d: Date) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
// `new Date("YYYY-MM-DD")` parses as UTC midnight, which renders as the previous
// day in any timezone behind UTC — parse the parts into a local-time Date instead.
function parseIsoDateLocal(key: string) {
  const [y, m, d] = key.split("-").map(Number);
  return new Date(y, m - 1, d);
}
function isSameDay(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}
function mondayOf(d: Date) {
  const offset = d.getDay() === 0 ? 6 : d.getDay() - 1;
  const m = new Date(d);
  m.setDate(d.getDate() - offset);
  m.setHours(0, 0, 0, 0);
  return m;
}

interface PlanCalendarViewProps {
  workouts: any[];
  lang: string;
  isMobile: boolean;
  getWorkoutDateObj: (wo: any) => Date | null;
  getWorkoutDate: (wo: any) => string;
  onSwapDays: (day1: string, day2: string, weekNumberOverride?: number) => void;
  onToggleComplete: (id: number, completed: boolean) => void;
  onLogWorkout: (id: number, rpe: number | null, notes: string) => Promise<void>;
}

export default function PlanCalendarView({
  workouts, lang, isMobile, getWorkoutDateObj, getWorkoutDate,
  onSwapDays, onToggleComplete, onLogWorkout,
}: PlanCalendarViewProps) {
  const dbTypes = useWorkoutTypes(lang);
  const zoneColorOf = (wo: any) =>
    resolveWorkoutInfo(wo.title || "", wo.type || "", dbTypes)?.color ||
    getZoneColor(wo.target_zone || "", wo.title || "", wo.type || "");

  const byDate = useMemo(() => {
    const map = new Map<string, any[]>();
    workouts.forEach((wo: any) => {
      const d = getWorkoutDateObj(wo);
      if (!d) return;
      const key = isoDate(d);
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(wo);
    });
    map.forEach((list) =>
      list.sort((a: any, b: any) => (SLOT_ORDER[a.session_slot ?? "main"] ?? 1) - (SLOT_ORDER[b.session_slot ?? "main"] ?? 1))
    );
    return map;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workouts]);

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const [viewMonth, setViewMonth] = useState(() => new Date(today.getFullYear(), today.getMonth(), 1));
  const monthLabel = viewMonth.toLocaleDateString(lang === "vi" ? "vi-VN" : "en-US", { month: "long", year: "numeric" });

  const gridStart = mondayOf(new Date(viewMonth.getFullYear(), viewMonth.getMonth(), 1));
  const monthEnd = new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 0);
  const lastRowStart = mondayOf(monthEnd);
  const weekCount = Math.round((lastRowStart.getTime() - gridStart.getTime()) / 86400000 / 7) + 1;

  const weeks: Date[][] = [];
  for (let w = 0; w < weekCount; w++) {
    const row: Date[] = [];
    for (let d = 0; d < 7; d++) {
      const dt = new Date(gridStart);
      dt.setDate(gridStart.getDate() + w * 7 + d);
      row.push(dt);
    }
    weeks.push(row);
  }

  // Exclude the leading/trailing days from adjacent months that fill out the
  // Monday-start grid — otherwise "This month" silently includes their volume.
  const monthWorkouts = weeks.flat()
    .filter((d) => d.getMonth() === viewMonth.getMonth() && d.getFullYear() === viewMonth.getFullYear())
    .flatMap((d) => byDate.get(isoDate(d)) || []);
  const monthKm = monthWorkouts.reduce((s, w) => s + (w.distance_km || 0), 0);
  const monthMins = monthWorkouts.reduce((s, w) => s + (w.duration_minutes || 0), 0);

  const [openDayKey, setOpenDayKey] = useState<string | null>(null);
  const openWorkouts = openDayKey ? byDate.get(openDayKey) || [] : [];

  const phaseLabel = (phase: string) => {
    if (lang !== "vi") return phase;
    return phase.replace("Recovery", "Phục hồi").replace("Transition", "Chuyển đổi");
  };

  const zoneLegend = [
    { label: lang === "en" ? "Easy" : "Nhẹ", color: "#3b82f6" },
    { label: lang === "en" ? "Moderate" : "Vừa", color: "#10b981" },
    { label: lang === "en" ? "Tempo" : "Tempo", color: "#f59e0b" },
    { label: lang === "en" ? "Hard" : "Nặng", color: "#ef4444" },
    { label: lang === "en" ? "Strength" : "Sức mạnh", color: "#8b5cf6" },
    { label: lang === "en" ? "Cross" : "Cross", color: "#14b8a6" },
    { label: lang === "en" ? "Rest" : "Nghỉ", color: "#94a3b8" },
  ];

  return (
    <div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "12px", fontSize: "11px", color: "var(--text-muted)", marginBottom: "14px", alignItems: "center" }}>
        {zoneLegend.map((z) => (
          <span key={z.label} style={{ display: "flex", alignItems: "center", gap: "5px" }}>
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: z.color, display: "inline-block", flexShrink: 0 }} />
            {z.label}
          </span>
        ))}
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "10px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <button
            type="button"
            onClick={() => setViewMonth(new Date(viewMonth.getFullYear(), viewMonth.getMonth() - 1, 1))}
            style={{ width: "30px", height: "30px", borderRadius: "50%", border: "1px solid var(--border-color)", background: "var(--bg-card)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
            aria-label={lang === "en" ? "Previous month" : "Tháng trước"}
          >
            <CaretLeft size={13} weight="bold" />
          </button>
          <h4 style={{ margin: 0, fontSize: "16px", fontWeight: 700, minWidth: "150px", textAlign: "center" }}>{monthLabel}</h4>
          <button
            type="button"
            onClick={() => setViewMonth(new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 1))}
            style={{ width: "30px", height: "30px", borderRadius: "50%", border: "1px solid var(--border-color)", background: "var(--bg-card)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
            aria-label={lang === "en" ? "Next month" : "Tháng sau"}
          >
            <CaretRight size={13} weight="bold" />
          </button>
        </div>
        <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-secondary)", background: "var(--bg-card)", border: "1px solid var(--border-color)", padding: "6px 12px", borderRadius: "999px" }}>
          {lang === "en" ? "This month" : "Tháng này"}: <span style={{ color: "var(--accent-primary)" }}>~{monthKm.toFixed(0)} km</span> · {(monthMins / 60).toFixed(1)}{lang === "en" ? "h" : "g"}
        </div>
      </div>

      <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: "16px", padding: isMobile ? "8px" : "14px", backdropFilter: "blur(24px)" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(7,1fr)", gap: isMobile ? "4px" : "8px", padding: "0 2px 8px" }}>
          {(lang === "vi" ? DAY_SHORT_VI : DAY_SHORT_EN).map((d) => (
            <span key={d} style={{ fontSize: "10px", fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--text-muted)" }}>
              {d}
            </span>
          ))}
        </div>

        {weeks.map((row, ri) => (
          <CalendarWeekRow
            key={ri}
            row={row}
            byDate={byDate}
            today={today}
            viewMonth={viewMonth}
            lang={lang}
            isMobile={isMobile}
            onSwapDays={onSwapDays}
            onOpenDay={setOpenDayKey}
            onToggleComplete={onToggleComplete}
            phaseLabel={phaseLabel}
            zoneColorOf={zoneColorOf}
          />
        ))}
      </div>

      {openDayKey && (
        <>
          <div
            onClick={() => setOpenDayKey(null)}
            style={{ position: "fixed", inset: 0, background: "rgba(10,15,12,0.28)", zIndex: 1150 }}
          />
          <div
            style={{
              position: "fixed", top: 0, right: 0, height: "100%", width: isMobile ? "100%" : "min(420px, 100%)",
              background: "rgba(255,255,255,0.97)", backdropFilter: "blur(30px)", borderLeft: "1px solid var(--border-color)",
              boxShadow: "-16px 0 40px rgba(15,23,42,0.18)", zIndex: 1151, padding: "20px", overflowY: "auto",
            }}
          >
            <button
              type="button"
              onClick={() => setOpenDayKey(null)}
              style={{ position: "absolute", top: "16px", right: "16px", width: "30px", height: "30px", borderRadius: "50%", border: "1px solid var(--border-color)", background: "var(--bg-card)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
              aria-label={lang === "en" ? "Close" : "Đóng"}
            >
              <X size={13} weight="bold" />
            </button>
            <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: "14px" }}>
              {openDayKey && parseIsoDateLocal(openDayKey).toLocaleDateString(lang === "vi" ? "vi-VN" : "en-US", { weekday: "long", month: "long", day: "numeric" })}
            </div>
            {openWorkouts.length === 0 ? (
              <div style={{ color: "var(--text-muted)", fontSize: "13px" }}>{lang === "en" ? "No workout scheduled." : "Không có buổi tập."}</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {openWorkouts.map((wo: any) => (
                  <WorkoutCard
                    key={wo.id}
                    wo={wo}
                    isMobile={isMobile}
                    lang={lang}
                    onToggleComplete={onToggleComplete}
                    onLogWorkout={onLogWorkout}
                    getWorkoutDate={getWorkoutDate}
                    defaultExpanded
                  />
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function CalendarWeekRow({
  row, byDate, today, viewMonth, lang, isMobile, onSwapDays, onOpenDay, onToggleComplete, phaseLabel, zoneColorOf,
}: {
  row: Date[];
  byDate: Map<string, any[]>;
  today: Date;
  viewMonth: Date;
  lang: string;
  isMobile: boolean;
  onSwapDays: (day1: string, day2: string, weekNumberOverride?: number) => void;
  onOpenDay: (key: string) => void;
  onToggleComplete: (id: number, completed: boolean) => void;
  phaseLabel: (p: string) => string;
  zoneColorOf: (wo: any) => string;
}) {
  const dayEntries = row.map((d) => ({ date: d, key: isoDate(d), wos: byDate.get(isoDate(d)) || [] }));
  const anchorWo = dayEntries.find((e) => e.wos.length > 0)?.wos[0];
  const weekNumber = anchorWo?.week_number;

  // A small pointer-move threshold before a drag "activates" — below it, the
  // gesture is a plain click (opens the day panel); a real drag still starts
  // from anywhere on the cell instead of requiring a tiny dedicated handle.
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor),
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id && weekNumber != null) {
      // dnd-kit ids are the ISO date keys (unique per row); the swap API needs day-of-week names.
      const dayOfWeek = (key: string) => dayEntries.find((e) => e.key === key)?.wos[0]?.day_of_week;
      const day1 = dayOfWeek(String(active.id));
      const day2 = dayOfWeek(String(over.id));
      if (day1 && day2) onSwapDays(day1, day2, weekNumber);
    }
  };

  const weekMins = dayEntries.reduce((s, e) => s + e.wos.reduce((s2: number, w: any) => s2 + (w.duration_minutes || 0), 0), 0);
  const weekKm = dayEntries.reduce((s, e) => s + e.wos.reduce((s2: number, w: any) => s2 + (w.distance_km || 0), 0), 0);
  const maxDayMins = Math.max(1, ...dayEntries.map((e) => e.wos.reduce((s: number, w: any) => s + (w.duration_minutes || 0), 0)));
  const hasRaceInRow = dayEntries.some((e) => e.wos.some((w: any) => w.type?.toLowerCase() === "race"));

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(7,1fr)", gap: isMobile ? "4px" : "8px", marginBottom: "6px" }}>
        {dayEntries.map(({ date, key, wos }) => (
          <CalendarDayCell
            key={key}
            date={date}
            dayKey={key}
            wos={wos}
            today={today}
            viewMonth={viewMonth}
            lang={lang}
            isMobile={isMobile}
            onOpenDay={onOpenDay}
            onToggleComplete={onToggleComplete}
            zoneColorOf={zoneColorOf}
          />
        ))}
      </div>
      {weekNumber != null && (
        <div style={{ padding: "2px 2px 14px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
            <span
              style={{
                fontSize: "9.5px", fontWeight: 700, letterSpacing: "0.03em", textTransform: "uppercase",
                padding: "2px 9px", borderRadius: "999px", color: "#04241a",
                background: anchorWo?.phase?.toLowerCase().includes("recovery")
                  ? "#94a3b8"
                  : anchorWo?.phase?.toLowerCase().includes("taper")
                  ? "#f59e0b"
                  : "var(--accent-primary)",
              }}
            >
              {anchorWo?.phase ? phaseLabel(anchorWo.phase) : ""}
            </span>
            <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-muted)" }}>
              <b style={{ color: "var(--text-secondary)" }}>~{weekKm.toFixed(0)} km</b> · {(weekMins / 60).toFixed(1)}{lang === "en" ? "h" : "g"}
            </span>
          </div>
          {!hasRaceInRow && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(7,1fr)", gap: isMobile ? "4px" : "8px", height: "16px" }}>
              {dayEntries.map(({ key, wos }) => {
                const mins = wos.reduce((s: number, w: any) => s + (w.duration_minutes || 0), 0);
                const h = wos.length === 0 ? 0 : Math.max(8, Math.round((mins / maxDayMins) * 100));
                const primary = wos.find((w: any) => w.type !== "Rest") || wos[0];
                const color = primary ? zoneColorOf(primary) : "transparent";
                return (
                  <div key={key} style={{ height: "100%", display: "flex", alignItems: "flex-end" }}>
                    <div style={{ width: "100%", height: `${h}%`, minHeight: wos.length ? "3px" : 0, borderRadius: "3px 3px 1px 1px", background: color, opacity: 0.85 }} />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </DndContext>
  );
}

function CalendarDayCell({
  date, dayKey, wos, today, viewMonth, lang, isMobile, onOpenDay, onToggleComplete, zoneColorOf,
}: {
  date: Date;
  dayKey: string;
  wos: any[];
  today: Date;
  viewMonth: Date;
  lang: string;
  isMobile: boolean;
  onOpenDay: (key: string) => void;
  onToggleComplete: (id: number, completed: boolean) => void;
  zoneColorOf: (wo: any) => string;
}) {
  const inMonth = date.getMonth() === viewMonth.getMonth();
  const isToday = isSameDay(date, today);
  const hasData = wos.length > 0;
  const isRace = wos.some((w: any) => w.type?.toLowerCase() === "race");
  const isDraggable = hasData && !isRace;

  // The whole cell is both the drag source and the click target. A distance
  // activation constraint on the row's DndContext (see CalendarWeekRow) means
  // a plain click (near-zero pointer movement) still reaches this cell's
  // onClick and each chip's complete-toggle button normally — only a real
  // drag (movement past the threshold) is captured as a drag gesture.
  const { attributes, listeners, setNodeRef: setDragRef, transform, isDragging } = useDraggable({ id: dayKey, disabled: !isDraggable });
  const { setNodeRef: setDropRef, isOver } = useDroppable({ id: dayKey, disabled: !isDraggable });
  const setRef = (node: HTMLElement | null) => {
    setDragRef(node);
    setDropRef(node);
  };

  if (!hasData) {
    return (
      <div style={{ minHeight: isMobile ? "48px" : "100px", opacity: inMonth ? 0.35 : 0.15, padding: "6px" }}>
        <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--text-muted)", fontVariantNumeric: "tabular-nums" }}>{date.getDate()}</span>
      </div>
    );
  }

  const isRestOnly = wos.every((w: any) => w.type === "Rest");
  const isDone = wos.every((w: any) => w.is_completed === 1 || w.type === "Rest") && !isRestOnly;

  const style: React.CSSProperties = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.4 : 1,
  };

  return (
    <div
      ref={setRef}
      {...(isDraggable ? { ...listeners, ...attributes } : {})}
      onClick={() => onOpenDay(dayKey)}
      title={isDraggable ? (lang === "en" ? "Click to view, drag to reschedule" : "Nhấn để xem, kéo để đổi lịch") : undefined}
      style={{
        ...style,
        position: "relative",
        minHeight: isMobile ? "50px" : "100px",
        borderRadius: "10px",
        border: `1px solid ${isToday ? "var(--accent-primary)" : "var(--border-color)"}`,
        background: isOver
          ? "rgba(16,185,129,0.12)"
          : isRace
          ? "linear-gradient(155deg, rgba(25,206,139,0.18), rgba(162,209,60,0.14))"
          : "var(--bg-card)",
        outline: isOver ? "2px dashed var(--accent-primary)" : "none",
        outlineOffset: "-2px",
        padding: "7px",
        cursor: isDraggable ? "grab" : "pointer",
        display: "flex",
        flexDirection: "column",
        gap: "5px",
      }}
    >
      <span
        style={{
          fontSize: "12px", fontWeight: 700, fontVariantNumeric: "tabular-nums",
          color: isToday ? "#04241a" : "var(--text-secondary)",
          background: isToday ? "var(--accent-primary)" : "transparent",
          width: isToday ? "20px" : "auto", height: isToday ? "20px" : "auto",
          borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
        }}
      >
        {date.getDate()}
      </span>

      {!isMobile && isRestOnly && (
        <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>{lang === "en" ? "Rest" : "Nghỉ"}</span>
      )}

      {!isMobile &&
        !isRestOnly &&
        wos
          .filter((w: any) => w.type !== "Rest")
          .map((w: any) => {
            const color = zoneColorOf(w);
            const isRaceWo = w.type?.toLowerCase() === "race";
            return (
              <div key={w.id} style={{ display: "flex", alignItems: "center", gap: "4px", borderRadius: "7px", padding: "4px 6px", background: `${color}22`, borderLeft: `3px solid ${color}` }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-primary)" }}>
                    {isRaceWo ? `🏁 ${lang === "en" ? "Race Day" : "Ngày đua"}` : w.title}
                  </div>
                  <div style={{ fontSize: "9.5px", color: "var(--text-secondary)", fontVariantNumeric: "tabular-nums" }}>
                    {isRaceWo
                      ? w.distance_km
                        ? `${w.distance_km}km`
                        : ""
                      : `${w.duration_minutes}m${w.distance_km ? ` · ~${Math.round(w.distance_km)}km` : ""}`}
                  </div>
                </div>
                {/* Quick finish tick — toggle this workout's completion without opening the day panel */}
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); onToggleComplete(w.id, !w.is_completed); }}
                  onPointerDown={(e) => e.stopPropagation()}
                  title={w.is_completed ? (lang === "en" ? "Mark incomplete" : "Đánh dấu chưa xong") : (lang === "en" ? "Mark complete" : "Đánh dấu hoàn thành")}
                  style={{ background: "none", border: "none", cursor: "pointer", padding: "1px", display: "flex", flexShrink: 0 }}
                >
                  {w.is_completed ? (
                    <CheckCircle size={15} weight="fill" color="#10b981" />
                  ) : (
                    <Circle size={15} weight="regular" color="var(--text-muted)" />
                  )}
                </button>
              </div>
            );
          })}

      {isMobile && (
        <div style={{ display: "flex", gap: "3px", flexWrap: "wrap" }}>
          {wos
            .filter((w: any) => w.type !== "Rest")
            .map((w: any) => (
              <span key={w.id} style={{ width: "6px", height: "6px", borderRadius: "50%", background: zoneColorOf(w), display: "block" }} />
            ))}
        </div>
      )}

      {isDone && (
        <span
          style={{
            position: "absolute", top: "5px", right: "5px", width: "14px", height: "14px", borderRadius: "50%",
            background: "var(--accent-primary)", display: "flex", alignItems: "center", justifyContent: "center",
          }}
        >
          <CheckCircle size={9} weight="bold" color="#04241a" />
        </span>
      )}

      {isDraggable && !isMobile && (
        <span
          aria-hidden="true"
          style={{
            position: "absolute", bottom: "4px", right: "5px", fontSize: "11px", lineHeight: 1,
            color: "rgba(0,0,0,0.22)", pointerEvents: "none",
          }}
        >
          ⠿
        </span>
      )}
    </div>
  );
}
