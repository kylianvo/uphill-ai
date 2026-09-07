"use client";

import React from "react";
import { createPortal } from "react-dom";
import { ArrowsLeftRight, ArrowRight, X, Moon, CalendarBlank } from "@phosphor-icons/react";

interface ModalWorkout {
  id?: number;
  day_of_week: string;
  title?: string;
  duration_minutes?: number;
  distance_km?: number;
  type?: string;
}

interface MoveWorkoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  sourceDay: string;
  weekNumber: number;
  weekWos: ModalWorkout[];
  lang: string;
  onSwapDays: (day1: string, day2: string, weekNumberOverride?: number) => void;
}

const DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const DAY_LABELS: Record<string, { en: string; vi: string }> = {
  Monday: { en: "Monday", vi: "Thứ Hai" },
  Tuesday: { en: "Tuesday", vi: "Thứ Ba" },
  Wednesday: { en: "Wednesday", vi: "Thứ Tư" },
  Thursday: { en: "Thursday", vi: "Thứ Năm" },
  Friday: { en: "Friday", vi: "Thứ Sáu" },
  Saturday: { en: "Saturday", vi: "Thứ Bảy" },
  Sunday: { en: "Sunday", vi: "Chủ Nhật" },
};

export function MoveWorkoutModal({
  isOpen,
  onClose,
  sourceDay,
  weekNumber,
  weekWos,
  lang,
  onSwapDays,
}: MoveWorkoutModalProps) {
  if (!isOpen) return null;
  if (typeof document === "undefined") return null;

  const isVi = lang === "vi";
  const sourceWos = weekWos.filter((w) => w.day_of_week === sourceDay);
  const sourceIsRest = sourceWos.length === 0;

  const handleSelectTarget = (targetDay: string) => {
    onSwapDays(sourceDay, targetDay, weekNumber);
    onClose();
  };

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

        {/* Day selection list */}
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
