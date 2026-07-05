/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useRef } from "react";
import {
  CheckCircle,
  Circle,
  CaretDown,
  CaretUp,
  Footprints,
  Timer,
  MapPin,
  Heart,
  Lightning,
  BowlFood,
  ArrowsCounterClockwise,
  Info,
  FloppyDisk,
  Gauge,
  ArrowUp,
  Play,
  Wind,
  Warning,
  Leaf,
} from "@phosphor-icons/react";
import { getZoneColor, RPE_DESCRIPTORS } from "../data/workoutLibrary";
import { useWorkoutTypes, resolveWorkoutInfo } from "../hooks/useWorkoutTypes";
import {
  parseExecutionSteps,
  extractDescriptionSections,
  selectMainSetText,
  buildCoachNotesContent,
  mainDurationMinutes,
} from "../utils/workoutDescription";

interface WorkoutCardProps {
  wo: any;
  isMobile: boolean;
  lang: string;
  onToggleComplete: (id: number, completed: boolean) => void;
  onLogWorkout: (id: number, rpe: number | null, notes: string) => Promise<void>;
  getWorkoutDate: (wo: any) => string;
}

const RACE_COACH_MESSAGES: Record<string, string[]> = {
  en: [
    "All those early mornings, all those hard sessions — today is why. Trust your training. You're ready.",
    "Today isn't about fitness anymore — it's about execution. Start slow, stay calm, find your finish.",
    "Your body knows what to do. You've done this in training. Today, just race.",
  ],
  vi: [
    "Tất cả những buổi sáng sớm, những buổi tập cực — là vì ngày hôm nay. Tin vào quá trình. Bạn đã sẵn sàng.",
    "Hôm nay không còn là về thể lực — mà là chiến thuật. Xuất phát chậm, bình tĩnh, về đích mạnh.",
    "Cơ thể bạn đã biết phải làm gì. Bạn đã luyện tập điều này. Hôm nay, cứ chạy thôi.",
  ],
};

const RACE_STRATEGY_TIPS: Record<string, string[]> = {
  en: [
    "Start conservatively — your first km should feel almost too easy. Adrenaline will try to pull you faster.",
    "Fuel early and often. Don't wait until you're hungry. Every 40–50 min.",
    "Hike steep climbs by effort, not ego. Walking the climbs is often faster when legs are tired.",
    "The race truly begins in the second half — manage the first half well.",
    "Your only competitor is the course. Run your plan, not anyone else's pace.",
  ],
  vi: [
    "Xuất phát chậm — km đầu phải cảm thấy gần như quá dễ. Adrenaline sẽ cố kéo bạn nhanh hơn.",
    "Nạp năng lượng sớm và thường xuyên. Đừng đợi đến khi đói. Cứ 40–50 phút một lần.",
    "Đi bộ lên dốc dựng khi cần — đó thường là chiến thuật nhanh hơn khi chân mỏi.",
    "Cuộc đua thực sự bắt đầu ở nửa sau — hãy tiết kiệm ở nửa đầu.",
    "Đối thủ duy nhất của bạn là địa hình. Chạy theo kế hoạch của mình, không phải của ai khác.",
  ],
};

const ZONE_LABELS: Record<string, string> = {
  easy: "Zone 1–2",
  moderate: "Zone 2–3",
  tempo: "Zone 3–4",
  hard: "Zone 4–5",
  strength: "Strength",
  cross: "Cross",
  rest: "Rest",
};

export default function WorkoutCard({
  wo,
  isMobile,
  lang,
  onToggleComplete,
  onLogWorkout,
  getWorkoutDate,
}: WorkoutCardProps) {
  const isRest = wo.type === "Rest";
  const isRaceDay = wo.type?.toLowerCase() === "race";
  const dbTypes = useWorkoutTypes(lang);
  const libraryInfo = resolveWorkoutInfo(wo.title || "", wo.type || "", dbTypes);
  const zoneColor = libraryInfo?.color || getZoneColor(wo.target_zone || "", wo.title || "", wo.type || "");

  const defaultSurface = wo.treadmill_incline > 0 ? "treadmill" : "outdoor";
  const [surface, setSurface] = useState<"outdoor" | "treadmill">(defaultSurface);
  const [expanded, setExpanded] = useState(false);
  const [rpe, setRpe] = useState<number | null>(wo.rpe ?? null);
  const [notes, setNotes] = useState<string>(wo.notes ?? "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [showRpeInfo, setShowRpeInfo] = useState(false);
  const saveTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const dayShort =
    lang === "vi"
      ? wo.day_of_week
          .replace("Monday", "T2")
          .replace("Tuesday", "T3")
          .replace("Wednesday", "T4")
          .replace("Thursday", "T5")
          .replace("Friday", "T6")
          .replace("Saturday", "T7")
          .replace("Sunday", "CN")
      : wo.day_of_week.slice(0, 3);

  const woTypeLabel = wo.type === "Rest" ? (lang === "en" ? "Rest" : "Nghỉ") : wo.type;
  const workoutDate = getWorkoutDate(wo);

  const handleSave = async () => {
    setSaving(true);
    await onLogWorkout(wo.id, rpe, notes);
    setSaving(false);
    setSaved(true);
    if (saveTimeout.current) clearTimeout(saveTimeout.current);
    saveTimeout.current = setTimeout(() => setSaved(false), 2000);
  };

  const zoneInfo = libraryInfo ? ZONE_LABELS[libraryInfo.zone] : wo.target_zone || "";
  const hasLog = rpe !== null || notes.trim().length > 0;
  const isDirty = rpe !== (wo.rpe ?? null) || notes !== (wo.notes ?? "");

  return (
    <div
      style={{
        position: "relative",
        borderRadius: "12px",
        overflow: "hidden",
        border: `1px solid ${isRest ? "rgba(0,0,0,0.06)" : "rgba(0,0,0,0.1)"}`,
        background: isRest
          ? "rgba(255,255,255,0.35)"
          : `linear-gradient(135deg, ${zoneColor}08 0%, rgba(255,255,255,0.7) 40%)`,
        boxShadow: isRest
          ? "none"
          : "0 1px 3px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.6)",
        opacity: isRest ? 0.6 : 1,
      }}
    >
      {/* Zone color left stripe */}
      {!isRest && (
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            bottom: 0,
            width: "4px",
            background: zoneColor,
            borderRadius: "12px 0 0 12px",
          }}
        />
      )}

      <div style={{ padding: isMobile ? "14px 14px 14px 18px" : "16px 20px 16px 24px" }}>
        {/* ── Row 1: Day / Title / Badge / Checkbox ── */}
        <div style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
          {/* Day + date column */}
          <div style={{ flexShrink: 0, minWidth: "42px", textAlign: "center" }}>
            <div style={{ fontSize: "13px", fontWeight: "800", color: "var(--text-primary)", lineHeight: 1 }}>
              {dayShort}
            </div>
            {workoutDate && (
              <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px", fontWeight: "500" }}>
                {workoutDate}
              </div>
            )}
          </div>

          {/* Title + type badge */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
              <h4
                style={{
                  fontSize: isMobile ? "14px" : "15px",
                  fontWeight: "700",
                  margin: 0,
                  color: wo.is_completed ? "var(--text-muted)" : "var(--text-primary)",
                  textDecoration: wo.is_completed ? "line-through" : "none",
                  lineHeight: 1.3,
                }}
              >
                {wo.title}
              </h4>
              {!isRest && (
                <span
                  style={{
                    fontSize: "9px",
                    fontWeight: "700",
                    padding: "2px 7px",
                    borderRadius: "20px",
                    letterSpacing: "0.04em",
                    background: `${zoneColor}22`,
                    color: zoneColor,
                    flexShrink: 0,
                  }}
                >
                  {woTypeLabel}
                </span>
              )}
            </div>
            {/* Metric chips */}
            {!isRest && (
              <div
                style={{
                  display: "flex",
                  gap: "10px",
                  marginTop: "6px",
                  flexWrap: "wrap",
                  alignItems: "center",
                }}
              >
                {wo.duration_minutes > 0 && (
                  <span
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "3px",
                      fontSize: "11px",
                      color: "var(--text-secondary)",
                      fontWeight: "600",
                    }}
                  >
                    <Timer size={11} weight="bold" />
                    {wo.duration_minutes}m
                  </span>
                )}
                {wo.distance_km > 0 && (
                  <span
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "3px",
                      fontSize: "11px",
                      color: "var(--text-secondary)",
                      fontWeight: "600",
                    }}
                  >
                    <MapPin size={11} weight="bold" />
                    {wo.distance_km}km
                  </span>
                )}
                {wo.target_pace && wo.target_pace.trim() && (
                  <span
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "3px",
                      fontSize: "11px",
                      color: zoneColor,
                      fontWeight: "700",
                    }}
                  >
                    <Footprints size={11} weight="bold" />
                    {wo.target_pace}
                  </span>
                )}
                {wo.target_hr_range && (
                  <span
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "3px",
                      fontSize: "11px",
                      color: "#ef4444",
                      fontWeight: "600",
                    }}
                  >
                    <Heart size={11} weight="bold" />
                    {wo.target_hr_range}
                  </span>
                )}
                {zoneInfo && (
                  <span style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: "500" }}>
                    {zoneInfo}
                  </span>
                )}
                {hasLog && !expanded && (
                  <span
                    style={{
                      fontSize: "9px",
                      padding: "1px 5px",
                      borderRadius: "8px",
                      background: "rgba(16,185,129,0.12)",
                      color: "#10b981",
                      fontWeight: "700",
                    }}
                  >
                    {rpe !== null ? `RPE ${rpe}` : ""}
                    {rpe !== null && notes.trim() ? " · " : ""}
                    {notes.trim() ? "note" : ""}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Completion + expand */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexShrink: 0 }}>
            {!isRest && (
              <button
                onClick={() => onToggleComplete(wo.id, !wo.is_completed)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: "2px",
                  display: "flex",
                  alignItems: "center",
                }}
                title={wo.is_completed ? "Mark incomplete" : "Mark complete"}
              >
                {wo.is_completed ? (
                  <CheckCircle size={22} weight="fill" color="#10b981" />
                ) : (
                  <Circle size={22} weight="regular" color="var(--text-muted)" />
                )}
              </button>
            )}
            {!isRest && (
              <button
                onClick={() => setExpanded(!expanded)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: "2px",
                  display: "flex",
                  alignItems: "center",
                  color: "var(--text-muted)",
                }}
              >
                {expanded ? <CaretUp size={16} weight="bold" /> : <CaretDown size={16} weight="bold" />}
              </button>
            )}
          </div>
        </div>

        {/* ── Expanded content ── */}
        {expanded && !isRest && (
          <div style={{ marginTop: "16px", paddingTop: "14px", borderTop: "1px solid rgba(0,0,0,0.06)" }}>
            {/* Outdoor / Treadmill toggle */}
            <div style={{ display: "flex", gap: "6px", marginBottom: "14px" }}>
              {(["outdoor", "treadmill"] as const).map((s) => (
                <button
                  key={s}
                  onClick={() => setSurface(s)}
                  style={{
                    padding: "4px 12px",
                    borderRadius: "20px",
                    border: "1.5px solid",
                    borderColor: surface === s ? zoneColor : "var(--border-color)",
                    background: surface === s ? `${zoneColor}18` : "transparent",
                    color: surface === s ? zoneColor : "var(--text-muted)",
                    fontSize: "11px",
                    fontWeight: "700",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                  }}
                >
                  {s === "outdoor" ? (
                    <Footprints size={12} weight="bold" />
                  ) : (
                    <ArrowsCounterClockwise size={12} weight="bold" />
                  )}
                  {s === "outdoor"
                    ? lang === "en"
                      ? "Outdoor"
                      : "Ngoài trời"
                    : lang === "en"
                    ? "Treadmill"
                    : "Máy chạy"}
                </button>
              ))}
            </div>

            {/* Surface-specific metrics */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(90px, 1fr))",
                gap: "8px",
                marginBottom: "16px",
              }}
            >
              {surface === "outdoor" && wo.target_pace && (
                <MetricPill
                  label={lang === "en" ? "Pace" : "Pace"}
                  value={wo.target_pace}
                  color={zoneColor}
                  icon={<Footprints size={12} />}
                />
              )}
              {surface === "treadmill" && wo.treadmill_speed > 0 && (
                <MetricPill
                  label={lang === "en" ? "Speed" : "Tốc độ"}
                  value={`${wo.treadmill_speed} kph`}
                  color={zoneColor}
                  icon={<Lightning size={12} />}
                />
              )}
              {surface === "treadmill" && wo.treadmill_incline > 0 && (
                <MetricPill
                  label={lang === "en" ? "Grade" : "Độ dốc"}
                  value={`${wo.treadmill_incline}%`}
                  color={zoneColor}
                  icon={<Gauge size={12} />}
                />
              )}
              {surface === "treadmill" && wo.target_pace && (
                <MetricPill
                  label={lang === "en" ? "Pace" : "Pace"}
                  value={wo.target_pace}
                  color="#6b7280"
                  icon={<Footprints size={12} />}
                />
              )}
              {wo.target_hr_range && (
                <MetricPill label="HR" value={wo.target_hr_range} color="#ef4444" icon={<Heart size={12} />} />
              )}
            </div>

            {/* Race day coach message */}
            {isRaceDay && (
              <div
                style={{
                  background: "linear-gradient(135deg, rgba(234,179,8,0.12) 0%, rgba(234,179,8,0.04) 100%)",
                  border: "1.5px solid rgba(234,179,8,0.35)",
                  borderRadius: "10px",
                  padding: "12px 14px",
                  marginBottom: "16px",
                  display: "flex",
                  gap: "10px",
                  alignItems: "flex-start",
                }}
              >
                <span style={{ fontSize: "18px", flexShrink: 0 }}>🏁</span>
                <div>
                  <div style={{ fontSize: "9px", fontWeight: "800", letterSpacing: "0.08em", color: "#d97706", textTransform: "uppercase", marginBottom: "4px" }}>
                    {lang === "en" ? "Coach Uphill" : "Coach Uphill"}
                  </div>
                  <p style={{ fontSize: "13px", color: "var(--text-primary)", margin: 0, lineHeight: "1.6", fontStyle: "italic", fontWeight: "500" }}>
                    &ldquo;{(RACE_COACH_MESSAGES[lang] || RACE_COACH_MESSAGES.en)[wo.id % 3]}&rdquo;
                  </p>
                </div>
              </div>
            )}

            {/* Workout info: tabbed (library) or raw fallback */}
            {libraryInfo ? (
              <WorkoutLibrarySection
                info={libraryInfo}
                title={wo.title}
                zoneColor={zoneColor}
                lang={lang}
                rawDescription={wo.description}
                wo={wo}
                isRaceDay={isRaceDay}
              />
            ) : wo.description ? (
              <RawDescription description={wo.description} />
            ) : null}

            {/* Fueling tip */}
            {wo.fueling_tip && (
              <div
                style={{
                  display: "flex",
                  gap: "8px",
                  alignItems: "flex-start",
                  background: "rgba(16,185,129,0.06)",
                  borderLeft: "3px solid #10b981",
                  padding: "8px 12px",
                  borderRadius: "6px",
                  marginTop: "12px",
                }}
              >
                <BowlFood size={14} weight="fill" color="#10b981" style={{ flexShrink: 0, marginTop: "1px" }} />
                <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: 0, lineHeight: "1.5" }}>
                  {wo.fueling_tip}
                </p>
              </div>
            )}

            {/* ── RPE + Notes ── */}
            <div style={{ marginTop: "16px", paddingTop: "14px", borderTop: "1px solid rgba(0,0,0,0.06)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: "700",
                    color: "var(--text-secondary)",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  {lang === "en" ? "How did it feel?" : "Cảm giác thế nào?"}
                </span>
                <button
                  onClick={() => setShowRpeInfo(!showRpeInfo)}
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    padding: "0",
                    display: "flex",
                    alignItems: "center",
                    color: "var(--text-muted)",
                  }}
                  title="What is RPE?"
                >
                  <Info size={13} weight="regular" />
                </button>
              </div>
              {showRpeInfo && (
                <p
                  style={{
                    fontSize: "11.5px",
                    color: "var(--text-muted)",
                    margin: "0 0 10px 0",
                    lineHeight: "1.6",
                    background: "rgba(0,0,0,0.03)",
                    padding: "8px",
                    borderRadius: "6px",
                  }}
                >
                  <strong>RPE</strong> (Rate of Perceived Exertion) is a 1–10 scale for how hard an effort felt.
                  Kilian Jornet uses RPE alongside heart rate to track training load over time. Logging it helps the
                  coach understand how your body is responding week-to-week.
                </p>
              )}
              {/* RPE scale */}
              <div style={{ display: "flex", gap: "4px", marginBottom: "6px", flexWrap: "wrap" }}>
                {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => {
                  const desc = RPE_DESCRIPTORS[n];
                  const selected = rpe === n;
                  return (
                    <button
                      key={n}
                      onClick={() => setRpe(selected ? null : n)}
                      title={desc.label}
                      style={{
                        width: "28px",
                        height: "28px",
                        borderRadius: "6px",
                        border: `1.5px solid ${selected ? desc.color : "rgba(0,0,0,0.1)"}`,
                        background: selected ? desc.color : "rgba(255,255,255,0.5)",
                        color: selected ? "#fff" : "var(--text-muted)",
                        fontSize: "11px",
                        fontWeight: "700",
                        cursor: "pointer",
                        flexShrink: 0,
                      }}
                    >
                      {n}
                    </button>
                  );
                })}
              </div>
              {rpe !== null && (
                <p
                  style={{
                    fontSize: "11px",
                    color: RPE_DESCRIPTORS[rpe].color,
                    margin: "0 0 10px 0",
                    fontWeight: "600",
                  }}
                >
                  {rpe} — {RPE_DESCRIPTORS[rpe].label}
                </p>
              )}

              {/* Notes */}
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder={
                  lang === "en"
                    ? "Add a note — how your legs felt, what surprised you, what to remember next time…"
                    : "Ghi chú — cảm giác chân ra sao, điều gì bất ngờ, cần nhớ gì lần sau…"
                }
                rows={2}
                style={{
                  width: "100%",
                  padding: "8px 10px",
                  borderRadius: "8px",
                  border: "1.5px solid rgba(0,0,0,0.1)",
                  background: "rgba(255,255,255,0.6)",
                  fontSize: "12.5px",
                  color: "var(--text-primary)",
                  resize: "vertical",
                  fontFamily: "inherit",
                  lineHeight: "1.5",
                  boxSizing: "border-box",
                  outline: "none",
                }}
              />

              {isDirty && (
                <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "8px" }}>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "5px",
                      padding: "6px 14px",
                      borderRadius: "8px",
                      background: saved ? "#10b981" : zoneColor,
                      color: "#fff",
                      border: "none",
                      cursor: saving ? "default" : "pointer",
                      fontSize: "12px",
                      fontWeight: "700",
                      opacity: saving ? 0.7 : 1,
                      transition: "background 0.2s",
                    }}
                  >
                    <FloppyDisk size={13} weight="bold" />
                    {saved
                      ? lang === "en"
                        ? "Saved"
                        : "Đã lưu"
                      : saving
                      ? lang === "en"
                        ? "Saving…"
                        : "Đang lưu…"
                      : lang === "en"
                      ? "Save"
                      : "Lưu"}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Metric pill ────────────────────────────────────────────────────────────────
function MetricPill({
  label,
  value,
  color,
  icon,
}: {
  label: string;
  value: string;
  color: string;
  icon: React.ReactNode;
}) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "2px",
        padding: "6px 10px",
        borderRadius: "8px",
        background: `${color}10`,
        border: `1px solid ${color}30`,
      }}
    >
      <span
        style={{
          display: "flex",
          alignItems: "center",
          gap: "3px",
          fontSize: "9px",
          color: "var(--text-muted)",
          fontWeight: "700",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
        }}
      >
        {icon}
        {label}
      </span>
      <span style={{ fontSize: "13px", fontWeight: "800", color }}>{value}</span>
    </div>
  );
}

// ── Execution timeline (3-phase visual) ───────────────────────────────────────
function ExecutionTimeline({
  execution,
  zoneColor,
  lang,
  targets,
}: {
  execution: string;
  zoneColor: string;
  lang: string;
  targets?: Array<{ label: string; value: string; color: string; icon: React.ReactNode }>;
}) {
  const parsed = parseExecutionSteps(execution);
  const [mainExpanded, setMainExpanded] = useState(false);

  const phases: Array<{
    key: string;
    label: string;
    hint: string;
    steps: string[];
    color: string;
    icon: React.ReactNode;
    found: boolean;
  }> = [
    {
      key: "warmup",
      label: lang === "en" ? "Warm-Up" : "Khởi động",
      hint: lang === "en" ? "standard" : "tiêu chuẩn",
      steps: parsed.warmup
        ? [parsed.warmup]
        : [
            lang === "en"
              ? "10–15 min easy jog or walk — heart rate below Zone 2."
              : "10–15 phút chạy nhẹ — nhịp tim dưới Zone 2.",
          ],
      color: "#3b82f6",
      icon: <ArrowUp size={10} weight="bold" />,
      found: !!parsed.warmup,
    },
    {
      key: "main",
      label: lang === "en" ? "Main Set" : "Bài chính",
      hint: "",
      steps: parsed.mainSteps,
      color: zoneColor,
      icon: <Play size={10} weight="fill" />,
      found: true,
    },
    {
      key: "cooldown",
      label: lang === "en" ? "Cool-Down" : "Thả lỏng",
      hint: lang === "en" ? "standard" : "tiêu chuẩn",
      steps: parsed.cooldown
        ? [parsed.cooldown]
        : [
            lang === "en"
              ? "10–15 min easy jog + light stretching. HR back below 120 bpm."
              : "10–15 phút chạy nhẹ + giãn cơ. Nhịp tim về dưới 120 bpm.",
          ],
      color: "#6b7280",
      icon: <Wind size={10} weight="bold" />,
      found: !!parsed.cooldown,
    },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      {phases.map((phase, i) => (
        <div key={phase.key} style={{ display: "flex", gap: "12px", alignItems: "flex-start" }}>
          {/* Timeline track */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              flexShrink: 0,
              width: "24px",
            }}
          >
            <div
              style={{
                width: "22px",
                height: "22px",
                borderRadius: "50%",
                background: phase.found ? phase.color : "transparent",
                border: `2px solid ${phase.color}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: phase.found ? "#fff" : phase.color,
                flexShrink: 0,
              }}
            >
              {phase.icon}
            </div>
            {i < phases.length - 1 && (
              <div
                style={{
                  width: "2px",
                  flex: "1",
                  minHeight: "18px",
                  background: `linear-gradient(to bottom, ${phase.color}50, ${phases[i + 1].color}30)`,
                  margin: "3px 0",
                }}
              />
            )}
          </div>

          {/* Phase content */}
          <div style={{ flex: 1, paddingBottom: i < phases.length - 1 ? "14px" : "0" }}>
            {/* Phase label */}
            <div style={{ display: "flex", alignItems: "center", gap: "5px", marginBottom: "5px" }}>
              <span
                style={{
                  fontSize: "10px",
                  fontWeight: "800",
                  color: phase.color,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                }}
              >
                {phase.label}
              </span>
              {!phase.found && (
                <span
                  style={{
                    fontSize: "9px",
                    color: "var(--text-muted)",
                    fontStyle: "italic",
                    background: "rgba(0,0,0,0.04)",
                    padding: "1px 5px",
                    borderRadius: "4px",
                  }}
                >
                  {phase.hint}
                </span>
              )}
            </div>

            {/* Main Set: target chips + collapsible description */}
            {phase.key === "main" ? (
              <div>
                {/* Target chips row */}
                {targets && targets.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "5px", marginBottom: "6px" }}>
                    {targets.map((t, ti) => (
                      <span
                        key={ti}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "3px",
                          padding: "2px 8px",
                          borderRadius: "20px",
                          background: `${t.color}14`,
                          border: `1px solid ${t.color}30`,
                          fontSize: "11px",
                          fontWeight: "700",
                          color: t.color,
                        }}
                      >
                        {t.icon}
                        {t.value}
                        <span style={{ fontSize: "9px", fontWeight: "500", opacity: 0.7 }}>{t.label}</span>
                      </span>
                    ))}
                  </div>
                )}

                {/* Chevron toggle for description */}
                <button
                  onClick={() => setMainExpanded(!mainExpanded)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    padding: "2px 0",
                    color: "var(--text-muted)",
                    fontSize: "11px",
                    fontWeight: "600",
                  }}
                >
                  {mainExpanded ? <CaretUp size={11} weight="bold" /> : <CaretDown size={11} weight="bold" />}
                  {mainExpanded
                    ? (lang === "en" ? "Hide guide" : "Ẩn hướng dẫn")
                    : (lang === "en" ? "How to execute" : "Cách thực hiện")}
                </button>

                {mainExpanded && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "4px", marginTop: "6px" }}>
                    {phase.steps.map((step, si) => (
                      <div key={si} style={{ display: "flex", alignItems: "flex-start", gap: "6px" }}>
                        {phase.steps.length > 1 && (
                          <span style={{ fontSize: "10px", color: phase.color, flexShrink: 0, marginTop: "3px", fontWeight: "700" }}>›</span>
                        )}
                        <span style={{ fontSize: "12.5px", color: "var(--text-secondary)", lineHeight: "1.55" }}>
                          {step}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              /* Warm-up / Cool-down: always visible */
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                {phase.steps.map((step, si) => (
                  <div key={si} style={{ display: "flex", alignItems: "flex-start", gap: "6px" }}>
                    {phase.steps.length > 1 && (
                      <span style={{ fontSize: "10px", color: phase.found ? phase.color : "var(--text-muted)", flexShrink: 0, marginTop: "3px", fontWeight: "700" }}>›</span>
                    )}
                    <span style={{ fontSize: "12.5px", color: phase.found ? "var(--text-secondary)" : "var(--text-muted)", lineHeight: "1.55", fontStyle: phase.found ? "normal" : "italic" }}>
                      {step}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Tabbed library section ────────────────────────────────────────────────────
function WorkoutLibrarySection({
  info,
  title,
  zoneColor,
  lang,
  rawDescription,
  wo,
  isRaceDay,
}: {
  info: NonNullable<ReturnType<typeof resolveWorkoutInfo>>;
  title: string;
  zoneColor: string;
  lang: string;
  rawDescription?: string;
  wo: any;
  isRaceDay?: boolean;
}) {
  const [tab, setTab] = useState<"execution" | "about">("execution");

  const tabs = [
    {
      key: "execution" as const,
      label: lang === "en" ? "Execution" : "Thực hiện",
      icon: <Play size={11} weight="fill" />,
    },
    {
      key: "about" as const,
      label: lang === "en" ? "About" : "Chi tiết",
      icon: <Leaf size={11} weight="bold" />,
    },
  ];

  const { executionText, overviewText } = selectMainSetText(
    { execution: info.execution, overview: info.overview },
    rawDescription
  );

  // Main Set shows only the main portion's duration, not warm-up+main+cool-down.
  const mainMinutes = mainDurationMinutes(wo.duration_minutes, parseExecutionSteps(executionText));

  // Build the "today's target" chips from actual planner values
  const targets: Array<{ label: string; value: string; color: string; icon: React.ReactNode }> = [];
  if (wo.target_zone) targets.push({ label: lang === "en" ? "Zone" : "Vùng", value: wo.target_zone, color: zoneColor, icon: <Lightning size={10} /> });
  if (wo.target_pace?.trim()) targets.push({ label: lang === "en" ? "Pace" : "Pace", value: wo.target_pace, color: zoneColor, icon: <Footprints size={10} /> });
  if (wo.target_hr_range) targets.push({ label: "HR", value: wo.target_hr_range, color: "#ef4444", icon: <Heart size={10} /> });
  if (mainMinutes > 0) targets.push({ label: lang === "en" ? "Duration" : "Thời gian", value: `${mainMinutes} min`, color: "var(--text-secondary)", icon: <Timer size={10} /> });
  if (wo.distance_km > 0) targets.push({ label: lang === "en" ? "Distance" : "Khoảng cách", value: `${wo.distance_km} km`, color: "var(--text-secondary)", icon: <MapPin size={10} /> });

  return (
    <div style={{ marginBottom: "14px" }}>
      {/* Tab switcher */}
      <div style={{ display: "flex", gap: "6px", marginBottom: "14px" }}>
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              padding: "4px 12px",
              borderRadius: "20px",
              border: "1.5px solid",
              borderColor: tab === t.key ? zoneColor : "var(--border-color)",
              background: tab === t.key ? `${zoneColor}18` : "transparent",
              color: tab === t.key ? zoneColor : "var(--text-muted)",
              fontSize: "11px",
              fontWeight: "700",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {/* Execution tab: overview + visual step timeline */}
      {tab === "execution" && (
        <div>
          <p
            style={{
              fontSize: "13px",
              color: "var(--text-secondary)",
              margin: "0 0 16px 0",
              lineHeight: "1.65",
            }}
          >
            {overviewText}
          </p>
          <ExecutionTimeline execution={executionText} zoneColor={zoneColor} lang={lang} targets={targets} />
        </div>
      )}

      {/* About tab: benefit + warning + optional AI description */}
      {tab === "about" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div
            style={{
              padding: "10px 14px",
              borderRadius: "8px",
              background: "rgba(16,185,129,0.06)",
              borderLeft: "3px solid #10b981",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "5px",
                fontSize: "9px",
                fontWeight: "800",
                textTransform: "uppercase",
                letterSpacing: "0.1em",
                color: "#10b981",
                marginBottom: "5px",
              }}
            >
              <Leaf size={10} weight="bold" />
              {lang === "en" ? "What it builds" : "Tác dụng"}
            </div>
            <p
              style={{
                fontSize: "12.5px",
                color: "var(--text-secondary)",
                margin: 0,
                lineHeight: "1.65",
              }}
            >
              {info.benefit}
            </p>
          </div>

          <div
            style={{
              padding: "10px 14px",
              borderRadius: "8px",
              background: "rgba(239,68,68,0.05)",
              borderLeft: "3px solid #ef4444",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "5px",
                fontSize: "9px",
                fontWeight: "800",
                textTransform: "uppercase",
                letterSpacing: "0.1em",
                color: "#ef4444",
                marginBottom: "5px",
              }}
            >
              <Warning size={10} weight="bold" />
              {lang === "en" ? "Common mistake" : "Lỗi thường gặp"}
            </div>
            <p
              style={{
                fontSize: "12.5px",
                color: "var(--text-secondary)",
                margin: 0,
                lineHeight: "1.65",
              }}
            >
              {info.warning}
            </p>
          </div>

          {/* Race strategy tips */}
          {isRaceDay && (
            <div
              style={{
                padding: "10px 14px",
                borderRadius: "8px",
                background: "rgba(234,179,8,0.06)",
                borderLeft: "3px solid #eab308",
              }}
            >
              <div
                style={{
                  fontSize: "9px",
                  fontWeight: "800",
                  textTransform: "uppercase" as const,
                  letterSpacing: "0.1em",
                  color: "#d97706",
                  marginBottom: "8px",
                }}
              >
                {lang === "en" ? "Race Strategy" : "Chiến thuật đua"}
              </div>
              <ul style={{ margin: 0, padding: "0 0 0 14px", display: "flex", flexDirection: "column" as const, gap: "5px" }}>
                {(RACE_STRATEGY_TIPS[lang] || RACE_STRATEGY_TIPS.en).map((tip, i) => (
                  <li key={i} style={{ fontSize: "12.5px", color: "var(--text-secondary)", lineHeight: "1.55" }}>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* AI-generated coach notes: Overall/Reason/Benefit/Warning (Process lives in Main Set) */}
          {rawDescription && (
            <div
              style={{
                padding: "10px 14px",
                borderRadius: "8px",
                background: "rgba(0,0,0,0.03)",
                border: "1px solid rgba(0,0,0,0.06)",
              }}
            >
              <div
                style={{
                  fontSize: "9px",
                  fontWeight: "800",
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                  color: "var(--text-muted)",
                  marginBottom: "6px",
                }}
              >
                {lang === "en" ? "Coach notes" : "Ghi chú từ Coach"}
              </div>
              <CoachNotesSections description={rawDescription} />
            </div>
          )}

          {/* About this workout type label */}
          <p
            style={{
              fontSize: "10px",
              color: "var(--text-muted)",
              margin: "2px 0 0 0",
              fontStyle: "italic",
            }}
          >
            {lang === "en" ? `About: ${title}` : `Về bài: ${title}`}
          </p>
        </div>
      )}
    </div>
  );
}

// ── Coach notes: AI-generated sections, excluding Process (shown in Main Set) ──
function CoachNotesSections({ description }: { description: string }) {
  const content = buildCoachNotesContent(description);

  if (!content.hasSections) {
    return (
      <p style={{ fontSize: "12.5px", color: "var(--text-secondary)", margin: 0, lineHeight: "1.65" }}>
        {content.fallbackText}
      </p>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
      {content.overall && (
        <p style={{ fontSize: "13px", color: "var(--text-primary)", margin: 0, lineHeight: "1.65" }}>
          {content.overall}
        </p>
      )}
      {content.reason && (
        <p style={{ fontSize: "12.5px", color: "var(--text-secondary)", margin: 0, lineHeight: "1.65" }}>
          {content.reason}
        </p>
      )}
      {content.benefit && (
        <p style={{ fontSize: "12.5px", color: "#10b981", margin: 0, lineHeight: "1.65" }}>{content.benefit}</p>
      )}
      {content.warning && (
        <p style={{ fontSize: "12.5px", color: "#ef4444", margin: 0, lineHeight: "1.65" }}>{content.warning}</p>
      )}
    </div>
  );
}

// ── Raw AI description (fallback) ─────────────────────────────────────────────
function RawDescription({ description }: { description: string }) {
  const sections = extractDescriptionSections(description);
  const overall = sections.overall;
  const process = sections.process;
  const benefit = sections.benefit;
  const warning = sections.warning;
  const hasSections = overall || process || benefit || warning;

  if (!hasSections) {
    return (
      <p
        style={{
          fontSize: "12.5px",
          color: "var(--text-secondary)",
          margin: 0,
          lineHeight: "1.65",
        }}
      >
        {description}
      </p>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
      {overall && (
        <p style={{ fontSize: "13px", color: "var(--text-primary)", margin: 0, lineHeight: "1.65" }}>{overall}</p>
      )}
      {process && (
        <p style={{ fontSize: "12.5px", color: "var(--text-secondary)", margin: 0, lineHeight: "1.65" }}>
          {process}
        </p>
      )}
      {benefit && (
        <p style={{ fontSize: "12.5px", color: "#10b981", margin: 0, lineHeight: "1.65" }}>{benefit}</p>
      )}
      {warning && (
        <p style={{ fontSize: "12.5px", color: "#ef4444", margin: 0, lineHeight: "1.65" }}>{warning}</p>
      )}
    </div>
  );
}
