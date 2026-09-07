import React, { useState } from "react";
import { createPortal } from "react-dom";
import { Sparkle, X, Lightning, CheckCircle } from "@phosphor-icons/react";
import { translations } from "../app/translations";

const API_BASE_URL =
  (typeof window !== "undefined" && localStorage.getItem("UPHILL_API_URL_OVERRIDE")) ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

export interface AdaptWeekModalProps {
  isOpen: boolean;
  onClose: () => void;
  planId: number;
  weekNumber: number;
  totalWeeks: number;
  completedWorkoutsCount: number;
  initialSchedule: {
    days_per_week: number;
    long_run_day: string;
    preferred_days: string[];
    has_gym_access: boolean;
    use_treadmill: boolean;
    training_environment: "flat" | "hilly" | "mixed";
    double_session_days: string[];
    athlete_notes?: string;
  };
  lang: string;
  isMobile: boolean;
  onAdaptSuccess: (jobId: string) => void;
  actingAsAthleteId?: number | null;
}

const FULL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const SHORT_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const SHORT_DAYS_VI = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];

import {
  FeelingSelector,
  FeelingId,
  feelingIdToRpe,
} from "./FeelingSelector";

export type FatigueLevel = FeelingId;

export function AdaptWeekModal({
  isOpen,
  onClose,
  planId,
  weekNumber,
  completedWorkoutsCount,
  initialSchedule,
  lang,
  isMobile,
  onAdaptSuccess,
  actingAsAthleteId,
}: AdaptWeekModalProps) {
  const [fatigueLevel, setFatigueLevel] = useState<FatigueLevel>("moderate");
  const [fatigueNotes, setFatigueNotes] = useState<string>("");
  const [coachNotes, setCoachNotes] = useState<string>("");
  const [schedule, setSchedule] = useState({
    ...initialSchedule,
    double_session_days: initialSchedule.double_session_days || [],
  });
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;
  if (typeof document === "undefined") return null;

  const t = (key: keyof typeof translations.en) => {
    const dict = (translations as Record<string, Record<string, string>>)[lang] || translations.en;
    return dict[key] || translations.en[key] || key;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);

    const token = typeof window !== "undefined" ? localStorage.getItem("uphill_session_token") : null;
    if (!token) {
      setErrorMsg(lang === "en" ? "Not authenticated" : "Chưa đăng nhập");
      setLoading(false);
      return;
    }

    try {
      const url = actingAsAthleteId
        ? `${API_BASE_URL}/api/coaching/athletes/${actingAsAthleteId}/adapt-week`
        : `${API_BASE_URL}/api/coach/adapt-week`;

      const rpe = feelingIdToRpe(fatigueLevel);

      const body = {
        plan_id: planId,
        week_number: weekNumber,
        overall_rpe: rpe,
        fatigue_level: fatigueLevel,
        fatigue_notes: fatigueNotes.trim() || null,
        athlete_notes: fatigueNotes.trim() || null,
        coach_notes: actingAsAthleteId ? (coachNotes.trim() || null) : null,
        preferred_days: schedule.preferred_days,
        long_run_day: schedule.long_run_day,
        days_per_week: schedule.days_per_week,
        double_session_days: schedule.double_session_days,
        has_gym_access: schedule.has_gym_access,
        use_treadmill: schedule.use_treadmill,
        training_environment: schedule.training_environment,
        lang,
      };

      const resp = await fetch(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || (lang === "en" ? "Failed to adapt week" : "Không thể tùy chỉnh tuần"));
      }

      onClose();
      onAdaptSuccess(data.job_id);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : (lang === "en" ? "Error updating week" : "Lỗi khi cập nhật tuần");
      setErrorMsg(message);
    } finally {
      setLoading(false);
    }
  };

  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="adapt-week-title"
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0, 0, 0, 0.75)",
        zIndex: 2000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "max(20px, env(safe-area-inset-top)) 20px max(20px, env(safe-area-inset-bottom)) 20px",
      }}
    >
      <div
        style={{
          background: "rgba(255, 255, 255, 0.98)",
          borderRadius: "18px",
          padding: isMobile ? "20px 16px" : "28px 24px",
          maxWidth: "480px",
          width: "100%",
          boxShadow: "0 20px 60px rgba(0, 0, 0, 0.3)",
          maxHeight: "90vh",
          overflowY: "auto",
        }}
      >
        {/* Header */}
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "16px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
              <div
                style={{
                  width: "28px",
                  height: "28px",
                  borderRadius: "8px",
                  background: "rgba(99, 102, 241, 0.12)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--accent-primary)",
                }}
              >
                <Sparkle size={16} />
              </div>
              <h3 id="adapt-week-title" style={{ margin: 0, fontSize: "18px", fontWeight: "800" }}>
                {lang === "en" ? `Adapt Week ${weekNumber}` : `Tùy chỉnh Tuần ${weekNumber}`}
              </h3>
            </div>
            <p style={{ margin: 0, fontSize: "12.5px", color: "var(--text-muted)", lineHeight: 1.4 }}>
              {t("adapt_week_subtitle")}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label={t("adapt_week_cancel")}
            style={{
              border: "none",
              background: "transparent",
              cursor: "pointer",
              padding: "4px",
              color: "var(--text-muted)",
              borderRadius: "6px",
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Preserved Workouts Notice */}
        {completedWorkoutsCount > 0 && (
          <div
            style={{
              background: "linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(6, 182, 212, 0.04) 100%)",
              border: "1px solid rgba(16, 185, 129, 0.25)",
              borderRadius: "10px",
              padding: "10px 12px",
              marginBottom: "16px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "12px",
              color: "#059669",
              fontWeight: "600",
            }}
          >
            <CheckCircle size={16} weight="fill" style={{ flexShrink: 0 }} />
            <span>
              {completedWorkoutsCount} {t("adapt_week_preserved_notice")}
            </span>
          </div>
        )}

        {errorMsg && (
          <div
            style={{
              background: "rgba(239, 68, 68, 0.08)",
              border: "1px solid rgba(239, 68, 68, 0.25)",
              borderRadius: "8px",
              padding: "10px",
              marginBottom: "16px",
              fontSize: "12px",
              color: "#ef4444",
              fontWeight: 600,
            }}
          >
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Feeling / Fatigue Level Selector */}
          <div style={{ marginBottom: "16px" }}>
            <label
              style={{
                display: "block",
                fontSize: "12px",
                fontWeight: "700",
                color: "var(--text-secondary)",
                marginBottom: "8px",
              }}
            >
              {t("adapt_week_rpe_label")}
            </label>
            <FeelingSelector
              selectedId={fatigueLevel}
              onChange={(id) => setFatigueLevel(id)}
              lang={lang === "vi" ? "vi" : "en"}
              isMobile={isMobile}
              variant="cards"
              showDescription={true}
            />
          </div>

          {/* Reason / Fatigue Notes */}
          <div style={{ marginBottom: "16px" }}>
            <label
              style={{
                display: "block",
                fontSize: "12px",
                fontWeight: "700",
                color: "var(--text-secondary)",
                marginBottom: "6px",
              }}
            >
              {lang === "en" ? "Adaptation Notes & Context" : "Ghi chú & Bối cảnh điều chỉnh"}
            </label>
            <textarea
              placeholder={t("adapt_week_fatigue_placeholder")}
              value={fatigueNotes}
              onChange={(e) => setFatigueNotes(e.target.value)}
              style={{
                width: "100%",
                borderRadius: "10px",
                border: "1px solid var(--border-color)",
                padding: "10px",
                fontSize: "13px",
                minHeight: "72px",
                resize: "vertical",
                background: "rgba(0,0,0,0.03)",
                boxSizing: "border-box",
                fontFamily: "inherit",
              }}
            />
          </div>

          {/* Week Constraints */}
          <div
            style={{
              padding: "14px",
              background: "rgba(0,0,0,0.02)",
              border: "1px solid var(--border-color)",
              borderRadius: "12px",
              marginBottom: "16px",
            }}
          >
            <label
              style={{
                display: "block",
                fontSize: "11px",
                fontWeight: "800",
                marginBottom: "10px",
                color: "var(--text-secondary)",
                letterSpacing: "0.04em",
                textTransform: "uppercase",
              }}
            >
              {t("adapt_week_constraints_title")}
            </label>

            {/* Training Days Toggles */}
            <div style={{ marginBottom: "12px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <span style={{ fontSize: "12px", fontWeight: "600", color: "var(--text-secondary)" }}>
                  {t("adapt_week_days_toggle")}
                </span>
                <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "600" }}>
                  {schedule.preferred_days.length} {lang === "en" ? "days" : "ngày"}
                </span>
              </div>
              <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                {SHORT_DAYS.map((short, i) => {
                  const full = FULL_DAYS[i];
                  const selected = schedule.preferred_days.includes(full);
                  const label = lang === "vi" ? SHORT_DAYS_VI[i] : short;
                  return (
                    <button
                      key={full}
                      type="button"
                      onClick={() => {
                        const next = selected
                          ? schedule.preferred_days.filter((d) => d !== full)
                          : [...schedule.preferred_days, full];
                        setSchedule({
                          ...schedule,
                          preferred_days: next,
                          days_per_week: Math.max(3, Math.min(7, next.length || schedule.days_per_week)),
                          double_session_days: (schedule.double_session_days || []).filter((d) => next.includes(d)),
                        });
                      }}
                      style={{
                        padding: "5px 9px",
                        borderRadius: "8px",
                        border: `1.5px solid ${selected ? "var(--accent-primary)" : "var(--border-color)"}`,
                        background: selected ? "rgba(16,185,129,0.12)" : "rgba(255,255,255,0.4)",
                        color: selected ? "var(--accent-primary)" : "var(--text-secondary)",
                        fontWeight: selected ? "700" : "500",
                        fontSize: "12px",
                        cursor: "pointer",
                      }}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Double-Session Days */}
            <div style={{ marginBottom: "12px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <span style={{ fontSize: "12px", fontWeight: "600", color: "var(--text-secondary)" }}>
                  {t("adapt_week_double_session_days")}
                </span>
                <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "600" }}>
                  {(schedule.double_session_days || []).length}/2 {lang === "en" ? "days" : "ngày"}
                </span>
              </div>
              <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                {SHORT_DAYS.map((short, i) => {
                  const full = FULL_DAYS[i];
                  if (!schedule.preferred_days.includes(full)) return null;
                  const currentDouble = schedule.double_session_days || [];
                  const selected = currentDouble.includes(full);
                  const disabled = !selected && currentDouble.length >= 2;
                  const label = lang === "vi" ? SHORT_DAYS_VI[i] : short;
                  return (
                    <button
                      key={full}
                      type="button"
                      disabled={disabled}
                      onClick={() => {
                        const next = selected
                          ? currentDouble.filter((d) => d !== full)
                          : [...currentDouble, full];
                        setSchedule({ ...schedule, double_session_days: next });
                      }}
                      style={{
                        padding: "5px 9px",
                        borderRadius: "8px",
                        border: `1.5px solid ${selected ? "var(--accent-primary)" : "var(--border-color)"}`,
                        background: selected ? "rgba(16,185,129,0.12)" : "rgba(255,255,255,0.4)",
                        color: selected ? "var(--accent-primary)" : disabled ? "var(--text-muted)" : "var(--text-secondary)",
                        fontWeight: selected ? "700" : "500",
                        fontSize: "12px",
                        cursor: disabled ? "not-allowed" : "pointer",
                        opacity: disabled ? 0.5 : 1,
                      }}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>
              <p style={{ fontSize: "11px", color: "var(--text-muted)", margin: "4px 0 0 0" }}>
                {t("plan_double_session_help")}
              </p>
            </div>

            {/* Long Run Day & Days per week */}
            <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: "10px", marginBottom: "10px" }}>
              <div>
                <label style={{ display: "block", fontSize: "11.5px", fontWeight: "600", marginBottom: "4px", color: "var(--text-secondary)" }}>
                  {t("plan_long_run_day")}
                </label>
                <select
                  className="chat-input"
                  style={{ borderRadius: "8px", width: "100%", height: "36px", padding: "0 8px", fontSize: "12.5px" }}
                  value={schedule.long_run_day}
                  onChange={(e) => setSchedule({ ...schedule, long_run_day: e.target.value })}
                >
                  {FULL_DAYS.map((d) => {
                    const label = lang === "vi"
                      ? d.replace("Monday", "Thứ Hai").replace("Tuesday", "Thứ Ba").replace("Wednesday", "Thứ Tư").replace("Thursday", "Thứ Năm").replace("Friday", "Thứ Sáu").replace("Saturday", "Thứ Bảy").replace("Sunday", "Chủ Nhật")
                      : d;
                    return <option key={d} value={d}>{label}</option>;
                  })}
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "11.5px", fontWeight: "600", marginBottom: "4px", color: "var(--text-secondary)" }}>
                  {t("plan_days_per_week")}
                </label>
                <div style={{ display: "flex", gap: "4px" }}>
                  {[3, 4, 5, 6, 7].map((n) => (
                    <button
                      key={n}
                      type="button"
                      onClick={() => setSchedule({ ...schedule, days_per_week: n })}
                      style={{
                        flex: 1,
                        padding: "6px 0",
                        borderRadius: "8px",
                        border: `1.5px solid ${schedule.days_per_week === n ? "var(--accent-primary)" : "var(--border-color)"}`,
                        background: schedule.days_per_week === n ? "rgba(16,185,129,0.12)" : "rgba(255,255,255,0.4)",
                        color: schedule.days_per_week === n ? "var(--accent-primary)" : "var(--text-primary)",
                        fontWeight: "700",
                        fontSize: "12px",
                        cursor: "pointer",
                      }}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Checkbox Constraints */}
            <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: "8px", marginTop: "8px" }}>
              <label style={{ display: "flex", alignItems: "center", gap: "7px", cursor: "pointer", fontSize: "12px", color: "var(--text-primary)" }}>
                <input
                  type="checkbox"
                  checked={schedule.has_gym_access}
                  onChange={(e) => setSchedule({ ...schedule, has_gym_access: e.target.checked })}
                  style={{ width: "15px", height: "15px", accentColor: "var(--accent-primary)" }}
                />
                {t("plan_gym_access")}
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: "7px", cursor: "pointer", fontSize: "12px", color: "var(--text-primary)" }}>
                <input
                  type="checkbox"
                  checked={schedule.use_treadmill}
                  onChange={(e) => setSchedule({ ...schedule, use_treadmill: e.target.checked })}
                  style={{ width: "15px", height: "15px", accentColor: "var(--accent-primary)" }}
                />
                {t("plan_use_treadmill")}
              </label>
            </div>
          </div>

          {/* Coach Notes if coach is acting on behalf of athlete */}
          {actingAsAthleteId && (
            <div style={{ marginBottom: "16px" }}>
              <label
                style={{
                  display: "block",
                  fontSize: "12px",
                  fontWeight: "700",
                  color: "var(--text-secondary)",
                  marginBottom: "6px",
                }}
              >
                {lang === "en" ? "Coach Directive for this week (optional)" : "Chỉ đạo của HLV cho tuần này (tùy chọn)"}
              </label>
              <textarea
                placeholder={
                  lang === "en"
                    ? "e.g. \"Swap tempo with easy recovery run due to achilles tightness\""
                    : "VD: \"Đổi bài tempo thành chạy nhẹ phục hồi do căng gân gót\""
                }
                value={coachNotes}
                onChange={(e) => setCoachNotes(e.target.value)}
                style={{
                  width: "100%",
                  borderRadius: "10px",
                  border: "1px solid var(--border-color)",
                  padding: "10px",
                  fontSize: "13px",
                  minHeight: "60px",
                  resize: "vertical",
                  background: "rgba(0,0,0,0.03)",
                  boxSizing: "border-box",
                  fontFamily: "inherit",
                }}
              />
            </div>
          )}

          {/* Action buttons */}
          <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              style={{
                flex: 1,
                height: "42px",
                borderRadius: "10px",
                border: "1px solid var(--border-color)",
                background: "rgba(0,0,0,0.04)",
                cursor: "pointer",
                fontSize: "13px",
                fontWeight: "600",
              }}
            >
              {t("adapt_week_cancel")}
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{
                flex: 2,
                height: "42px",
                fontSize: "13px",
                fontWeight: "700",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "6px",
              }}
            >
              {loading ? (
                <span>{t("adapt_week_submitting")}</span>
              ) : (
                <>
                  <Lightning size={15} weight="fill" color="#f59e0b" aria-hidden="true" />
                  <span>
                    {lang === "en" ? `Regenerate Week ${weekNumber}` : `Tái tạo Tuần ${weekNumber}`}
                  </span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  );
}
