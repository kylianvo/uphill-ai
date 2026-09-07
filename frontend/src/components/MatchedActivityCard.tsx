"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Watch,
  Sneaker,
  Timer,
  Heart,
  Mountains,
  Lightning,
  CheckCircle,
  WarningCircle,
  LinkBreak,
  Clock,
  Barbell,
  Sparkle,
  CaretDown,
  CaretUp,
  Flame,
} from "@phosphor-icons/react";
import { triggerHaptic } from "../utils/native";
import CorosAttribution from "./CorosAttribution";
import { RawMatchActivity } from "../hooks/useMatching";

export interface MatchedActivityCardProps {
  activity: RawMatchActivity;
  plannedWorkout?: {
    id: number;
    title?: string;
    distance_km?: number | null;
    duration_minutes?: number | null;
    target_hr_range?: string | null;
    target_pace?: string | null;
    elevation_gain_m?: number | null;
  };
  lang: "en" | "vi";
  isMobile: boolean;
  onConfirmMatch?: (activityId: number, workoutId: number) => Promise<boolean>;
  onUnlinkMatch?: (activityId: number) => Promise<boolean>;
}

const CONFIRM_ARM_TIMEOUT_MS = 4000;

function formatDuration(totalSeconds: number): string {
  const total = Math.max(0, Math.round(totalSeconds));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;
  const ss = String(seconds).padStart(2, "0");
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, "0")}:${ss}`;
  }
  return `${minutes}:${ss}`;
}

function formatPace(durationSeconds: number, distanceKm: number | null): string | null {
  if (!distanceKm || distanceKm <= 0 || durationSeconds <= 0) return null;
  const paceSecondsPerKm = durationSeconds / distanceKm;
  const mins = Math.floor(paceSecondsPerKm / 60);
  const secs = Math.floor(paceSecondsPerKm % 60);
  return `${mins}:${String(secs).padStart(2, "0")} /km`;
}

function formatActivityTime(startTime: string): string {
  try {
    const d = new Date(startTime);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
  } catch {
    return "";
  }
}

export default function MatchedActivityCard({
  activity,
  plannedWorkout,
  lang,
  isMobile,
  onConfirmMatch,
  onUnlinkMatch,
}: MatchedActivityCardProps) {
  const [unlinkArmed, setUnlinkArmed] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [showQualityDetails, setShowQualityDetails] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const isAuto = activity.match_method === "auto" || activity.match_method === "manual";
  const isSuggest = activity.match_method === "suggest";
  const confidencePct = activity.match_confidence != null ? Math.round(activity.match_confidence * 100) : null;

  // Detect strength training session
  const isStrength =
    activity.activity_type === "strength" ||
    activity.activity_type === "indoor_strength" ||
    activity.activity_type === "gym_cardio" ||
    (!activity.distance_km && (activity.sets != null || (plannedWorkout?.title || "").toLowerCase().includes("strength") || (plannedWorkout?.title || "").toLowerCase().includes("gym")));

  // Multi-fragment / combined session support
  const fragments = activity.match_details?.fragments ?? 1;
  const isCombinedSession = fragments > 1;
  const displayDistance = activity.match_details?.bundle_distance_km ?? activity.distance_km;
  const displayDuration = activity.match_details?.bundle_duration_seconds ?? activity.duration_seconds;
  const displayElevation = activity.match_details?.bundle_elevation_gain_m ?? activity.elevation_gain_m;
  const displayHr = activity.match_details?.bundle_avg_hr ?? activity.avg_hr;

  const actualPace = !isStrength ? formatPace(displayDuration, displayDistance) : null;
  const formattedTime = formatActivityTime(activity.start_time);

  // Bundled warm-up detection
  const warmupKm = activity.match_details?.warmup_distance_km || 0;

  // Quality scoring
  const hasQuality = activity.quality_score != null || activity.quality_grade != null;
  const qualityScore = activity.quality_score != null ? Math.round(activity.quality_score) : null;
  const qualityGrade = activity.quality_grade || "A";
  const qualityDetails = activity.quality_details;

  const getQualityColor = (grade: string) => {
    switch (grade.toUpperCase()) {
      case "A":
        return {
          bg: "rgba(16, 185, 129, 0.12)",
          border: "rgba(16, 185, 129, 0.35)",
          text: "#059669",
        };
      case "B":
        return {
          bg: "rgba(6, 182, 212, 0.12)",
          border: "rgba(6, 182, 212, 0.35)",
          text: "#0891b2",
        };
      case "C":
        return {
          bg: "rgba(245, 158, 11, 0.12)",
          border: "rgba(245, 158, 11, 0.35)",
          text: "#d97706",
        };
      default:
        return {
          bg: "rgba(239, 68, 68, 0.12)",
          border: "rgba(239, 68, 68, 0.35)",
          text: "#dc2626",
        };
    }
  };

  const handleConfirm = async () => {
    if (!plannedWorkout || !onConfirmMatch || actionLoading) return;
    setActionLoading(true);
    triggerHaptic();
    try {
      await onConfirmMatch(activity.activity_id, plannedWorkout.id);
    } finally {
      setActionLoading(false);
    }
  };

  const handleUnlink = async () => {
    if (!onUnlinkMatch || actionLoading) return;
    if (!unlinkArmed) {
      setUnlinkArmed(true);
      triggerHaptic();
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setUnlinkArmed(false), CONFIRM_ARM_TIMEOUT_MS);
      return;
    }
    // Second tap: execute unlink
    if (timerRef.current) clearTimeout(timerRef.current);
    setUnlinkArmed(false);
    setActionLoading(true);
    triggerHaptic();
    try {
      await onUnlinkMatch(activity.activity_id);
    } finally {
      setActionLoading(false);
    }
  };

  // Delta computations
  let distanceDeltaKm: number | null = null;
  if (!isStrength && displayDistance != null && plannedWorkout?.distance_km != null && plannedWorkout.distance_km > 0) {
    distanceDeltaKm = displayDistance - plannedWorkout.distance_km;
  }

  let durationDeltaMin: number | null = null;
  if (displayDuration > 0 && plannedWorkout?.duration_minutes != null && plannedWorkout.duration_minutes > 0) {
    durationDeltaMin = Math.round(displayDuration / 60 - plannedWorkout.duration_minutes);
  }

  const qStyle = getQualityColor(qualityGrade);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        padding: isMobile ? "12px" : "14px",
        borderRadius: "14px",
        background: "var(--bg-card)",
        border: isSuggest
          ? "1px solid rgba(245, 158, 11, 0.4)"
          : "1px solid rgba(25, 206, 139, 0.35)",
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
        position: "relative",
      }}
    >
      {/* Header bar: Watch device, sport type, start time, confidence badge & quality pill */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "6px",
          paddingBottom: "8px",
          borderBottom: "1px solid rgba(0, 0, 0, 0.06)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          {isStrength ? (
            <Barbell size={16} weight="bold" color="var(--accent-primary)" aria-hidden="true" />
          ) : (
            <Watch size={15} weight="bold" color="var(--accent-primary)" aria-hidden="true" />
          )}
          <span style={{ fontSize: "12px", fontWeight: "700", color: "var(--text-primary)" }}>
            {activity.device_model || (activity.source_provider?.toUpperCase() ?? "WATCH")}
          </span>
          {isStrength && (
            <span
              style={{
                fontSize: "10.5px",
                padding: "1px 6px",
                borderRadius: "4px",
                background: "rgba(124, 58, 237, 0.12)",
                color: "#7c3aed",
                fontWeight: "700",
              }}
            >
              {lang === "vi" ? "Sức bền cơ bắp" : "Strength"}
            </span>
          )}
          {formattedTime && (
            <span style={{ fontSize: "11px", color: "var(--text-muted)", display: "inline-flex", alignItems: "center", gap: "3px" }}>
              <Clock size={11} aria-hidden="true" />
              {formattedTime}
            </span>
          )}
        </div>

        {/* Badges: Match Status & Coach Insights Pill */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          {/* Coach Insights Pill */}
          {hasQuality && (
            <button
              type="button"
              onClick={() => {
                triggerHaptic();
                setShowQualityDetails((prev) => !prev);
              }}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                padding: "3px 8px",
                borderRadius: "999px",
                background: qStyle.bg,
                color: qStyle.text,
                border: `1px solid ${qStyle.border}`,
                fontSize: "11px",
                fontWeight: "700",
                cursor: "pointer",
                transition: "opacity 0.15s ease",
              }}
              aria-label={lang === "vi" ? "Xem nhận xét từ HLV" : "View coach insights"}
            >
              <Sparkle size={12} weight="fill" aria-hidden="true" />
              <span>
                {qualityDetails?.rating
                  ? qualityDetails.rating
                  : (lang === "vi" ? "Nhận xét HLV" : "Coach Insights")}
              </span>
              {showQualityDetails ? <CaretUp size={10} weight="bold" /> : <CaretDown size={10} weight="bold" />}
            </button>
          )}

          {/* Confidence Badge */}
          {isAuto ? (
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                padding: "2px 8px",
                borderRadius: "999px",
                background: "rgba(25, 206, 139, 0.15)",
                color: "var(--accent-primary)",
                border: "1px solid rgba(25, 206, 139, 0.3)",
                fontSize: "11px",
                fontWeight: "700",
              }}
            >
              <CheckCircle size={13} weight="fill" aria-hidden="true" />
              <span>{lang === "vi" ? "Đã khớp" : "Matched"}</span>
              {confidencePct != null && (
                <span style={{ opacity: 0.85, fontWeight: "600" }}>{confidencePct}%</span>
              )}
            </span>
          ) : isSuggest ? (
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                padding: "2px 8px",
                borderRadius: "999px",
                background: "rgba(245, 158, 11, 0.12)",
                color: "#d97706",
                border: "1px solid rgba(245, 158, 11, 0.35)",
                fontSize: "11px",
                fontWeight: "700",
              }}
            >
              <WarningCircle size={13} weight="fill" aria-hidden="true" />
              <span>{lang === "vi" ? "Cần xác nhận" : "Needs confirming"}</span>
              {confidencePct != null && (
                <span style={{ opacity: 0.85, fontWeight: "600" }}>{confidencePct}%</span>
              )}
            </span>
          ) : null}
        </div>
      </div>

      {/* Bundled multi-activity combined session banner */}
      {isCombinedSession && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            padding: "6px 10px",
            borderRadius: "8px",
            background: "rgba(59, 130, 246, 0.08)",
            border: "1px solid rgba(59, 130, 246, 0.25)",
            color: "#2563eb",
            fontSize: "12px",
            fontWeight: "600",
          }}
        >
          <Sparkle size={14} weight="bold" aria-hidden="true" />
          <span>
            {lang === "vi"
              ? `Buổi tập kết hợp (${fragments} hoạt động, tổng cộng ${displayDistance?.toFixed(1)} km)`
              : `Combined session (${fragments} activities, ${displayDistance?.toFixed(1)} km total)`}
          </span>
        </div>
      )}

      {/* Bundled warm-up fragment banner */}
      {!isCombinedSession && warmupKm > 0 && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            padding: "4px 8px",
            borderRadius: "6px",
            background: "rgba(59, 130, 246, 0.08)",
            border: "1px solid rgba(59, 130, 246, 0.2)",
            color: "#2563eb",
            fontSize: "11px",
            fontWeight: "600",
          }}
        >
          <Sneaker size={13} weight="bold" aria-hidden="true" />
          <span>
            {lang === "vi"
              ? `Bao gồm ${warmupKm.toFixed(1)} km chạy khởi động vào tổng khối lượng`
              : `Includes ${warmupKm.toFixed(1)} km warm-up jog in total volume`}
          </span>
        </div>
      )}

      {/* Metrics Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: isMobile ? "repeat(2, 1fr)" : isStrength ? "repeat(3, 1fr)" : "repeat(3, 1fr)",
          gap: "8px",
        }}
      >
        {/* Distance (Hidden for pure strength) */}
        {!isStrength && displayDistance != null && (
          <div
            style={{
              padding: "8px 10px",
              borderRadius: "8px",
              background: "rgba(0, 0, 0, 0.02)",
              border: "1px solid rgba(0, 0, 0, 0.05)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "10.5px", color: "var(--text-muted)", fontWeight: "600" }}>
              <Sneaker size={13} weight="bold" aria-hidden="true" />
              <span>{lang === "vi" ? "QUÃNG ĐƯỜNG" : "DISTANCE"}</span>
            </div>
            <div style={{ fontSize: "14px", fontWeight: "700", color: "var(--text-primary)", marginTop: "2px" }}>
              {displayDistance.toFixed(1)} km
            </div>
            {distanceDeltaKm != null && (
              <div
                style={{
                  fontSize: "10px",
                  fontWeight: "600",
                  marginTop: "1px",
                  color: Math.abs(distanceDeltaKm) <= 0.5 ? "var(--accent-primary)" : "var(--text-muted)",
                }}
              >
                {distanceDeltaKm >= 0 ? `+${distanceDeltaKm.toFixed(1)} km` : `${distanceDeltaKm.toFixed(1)} km`}
                <span style={{ opacity: 0.75, marginLeft: "3px" }}>{lang === "vi" ? "so với kế hoạch" : "vs plan"}</span>
              </div>
            )}
          </div>
        )}

        {/* Duration */}
        <div
          style={{
            padding: "8px 10px",
            borderRadius: "8px",
            background: "rgba(0, 0, 0, 0.02)",
            border: "1px solid rgba(0, 0, 0, 0.05)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "10.5px", color: "var(--text-muted)", fontWeight: "600" }}>
            <Timer size={13} weight="bold" aria-hidden="true" />
            <span>{lang === "vi" ? "THỜI GIAN" : "DURATION"}</span>
          </div>
          <div style={{ fontSize: "14px", fontWeight: "700", color: "var(--text-primary)", marginTop: "2px" }}>
            {formatDuration(displayDuration)}
          </div>
          {durationDeltaMin != null && (
            <div
              style={{
                fontSize: "10px",
                fontWeight: "600",
                marginTop: "1px",
                color: Math.abs(durationDeltaMin) <= 5 ? "var(--accent-primary)" : "var(--text-muted)",
              }}
            >
              {durationDeltaMin >= 0 ? `+${durationDeltaMin}m` : `${durationDeltaMin}m`}
              <span style={{ opacity: 0.75, marginLeft: "3px" }}>{lang === "vi" ? "so với kế hoạch" : "vs plan"}</span>
            </div>
          )}
        </div>

        {/* Sets (For Strength Workouts) */}
        {isStrength && activity.sets != null && activity.sets > 0 && (
          <div
            style={{
              padding: "8px 10px",
              borderRadius: "8px",
              background: "rgba(0, 0, 0, 0.02)",
              border: "1px solid rgba(0, 0, 0, 0.05)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "10.5px", color: "var(--text-muted)", fontWeight: "600" }}>
              <Barbell size={13} weight="bold" aria-hidden="true" />
              <span>{lang === "vi" ? "SỐ HIỆP TẬP" : "SETS"}</span>
            </div>
            <div style={{ fontSize: "14px", fontWeight: "700", color: "var(--text-primary)", marginTop: "2px" }}>
              {activity.sets} {lang === "vi" ? "hiệp" : "sets"}
            </div>
          </div>
        )}

        {/* Avg Pace (Only for running) */}
        {!isStrength && actualPace && (
          <div
            style={{
              padding: "8px 10px",
              borderRadius: "8px",
              background: "rgba(0, 0, 0, 0.02)",
              border: "1px solid rgba(0, 0, 0, 0.05)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "10.5px", color: "var(--text-muted)", fontWeight: "600" }}>
              <Lightning size={13} weight="bold" aria-hidden="true" />
              <span>{lang === "vi" ? "PACE TB" : "AVG PACE"}</span>
            </div>
            <div style={{ fontSize: "14px", fontWeight: "700", color: "var(--text-primary)", marginTop: "2px" }}>
              {actualPace}
            </div>
            {plannedWorkout?.target_pace && (
              <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "1px" }}>
                {lang === "vi" ? `Mục tiêu: ${plannedWorkout.target_pace}` : `Target: ${plannedWorkout.target_pace}`}
              </div>
            )}
          </div>
        )}

        {/* Heart Rate */}
        {displayHr != null && (
          <div
            style={{
              padding: "8px 10px",
              borderRadius: "8px",
              background: "rgba(0, 0, 0, 0.02)",
              border: "1px solid rgba(0, 0, 0, 0.05)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "10.5px", color: "var(--text-muted)", fontWeight: "600" }}>
              <Heart size={13} weight="bold" color="#ef4444" aria-hidden="true" />
              <span>{lang === "vi" ? "NHỊP TIM TB" : "AVG HR"}</span>
            </div>
            <div style={{ fontSize: "14px", fontWeight: "700", color: "var(--text-primary)", marginTop: "2px" }}>
              {displayHr} bpm
            </div>
            {plannedWorkout?.target_hr_range && (
              <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "1px" }}>
                {lang === "vi" ? `Vùng: ${plannedWorkout.target_hr_range}` : `Zone: ${plannedWorkout.target_hr_range}`}
              </div>
            )}
          </div>
        )}

        {/* Elevation Gain */}
        {!isStrength && displayElevation != null && displayElevation > 0 && (
          <div
            style={{
              padding: "8px 10px",
              borderRadius: "8px",
              background: "rgba(0, 0, 0, 0.02)",
              border: "1px solid rgba(0, 0, 0, 0.05)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "10.5px", color: "var(--text-muted)", fontWeight: "600" }}>
              <Mountains size={13} weight="bold" aria-hidden="true" />
              <span>{lang === "vi" ? "ĐỘ DỐC" : "ELEVATION"}</span>
            </div>
            <div style={{ fontSize: "14px", fontWeight: "700", color: "var(--text-primary)", marginTop: "2px" }}>
              +{Math.round(displayElevation)} m
            </div>
          </div>
        )}
      </div>

      {/* Expandable Workout Quality Breakdown */}
      {hasQuality && showQualityDetails && (
        <div
          style={{
            marginTop: "2px",
            padding: "10px 12px",
            borderRadius: "10px",
            background: "rgba(0, 0, 0, 0.03)",
            border: `1px solid ${qStyle.border}`,
            display: "flex",
            flexDirection: "column",
            gap: "8px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "5px", fontWeight: "700", fontSize: "12px", color: qStyle.text }}>
              <Sparkle size={14} weight="fill" />
              <span>{qualityDetails?.rating || (lang === "vi" ? "Đánh giá thực thi" : "Execution Feedback")}</span>
            </div>
          </div>

          {/* Subscores as Process Adherence */}
          {qualityDetails?.subscores && (
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", fontSize: "11px", color: "var(--text-secondary)" }}>
              {qualityDetails.subscores.volume != null && (
                <span>
                  {lang === "vi" ? "Khối lượng: " : "Volume: "}
                  <strong style={{ color: "var(--text-primary)" }}>
                    {qualityDetails.subscores.volume >= 0.9
                      ? (lang === "vi" ? "Đạt mục tiêu" : "On target")
                      : `${Math.round(qualityDetails.subscores.volume * 100)}%`}
                  </strong>
                </span>
              )}
              {qualityDetails.subscores.intensity != null && (
                <span>
                  {lang === "vi" ? "Kỷ luật nhịp tim: " : "HR Discipline: "}
                  <strong style={{ color: "var(--text-primary)" }}>
                    {qualityDetails.subscores.intensity >= 0.85
                      ? (lang === "vi" ? "Chuẩn vùng" : "In Zone")
                      : (lang === "vi" ? "Cần điều chỉnh" : "Adjust pace")}
                  </strong>
                </span>
              )}
              {qualityDetails.subscores.elevation != null && (
                <span>
                  {lang === "vi" ? "Độ cao: " : "Elevation: "}
                  <strong style={{ color: "var(--text-primary)" }}>
                    {qualityDetails.subscores.elevation >= 0.85
                      ? (lang === "vi" ? "Đạt" : "Hit")
                      : `${Math.round(qualityDetails.subscores.elevation * 100)}%`}
                  </strong>
                </span>
              )}
            </div>
          )}

          {/* Coaching Takeaways */}
          {qualityDetails?.takeaways && qualityDetails.takeaways.length > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "4px", marginTop: "2px" }}>
              <span style={{ fontSize: "10.5px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>
                {lang === "vi" ? "Ghi chú từ Huấn luyện viên" : "Coach Insights"}
              </span>
              {qualityDetails.takeaways.map((note: string, idx: number) => (
                <div key={idx} style={{ display: "flex", alignItems: "flex-start", gap: "5px", fontSize: "11.5px", color: "var(--text-primary)" }}>
                  <CheckCircle size={13} weight="fill" color={qStyle.text} style={{ marginTop: "2px", flexShrink: 0 }} />
                  <span>{note}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Footer bar: Actions and mandatory legal attribution */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "8px",
          marginTop: "4px",
          paddingTop: "6px",
          borderTop: "1px solid rgba(0, 0, 0, 0.06)",
        }}
      >
        <div style={{ fontSize: "11px", color: "var(--text-secondary)" }}>
          <CorosAttribution deviceModel={activity.device_model} provider={activity.source_provider} />
        </div>

        {/* Action buttons (Touch target minimum 44px on mobile) */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {isSuggest && onConfirmMatch && (
            <button
              type="button"
              onClick={handleConfirm}
              disabled={actionLoading}
              aria-label={lang === "vi" ? "Xác nhận khớp bài tập" : "Confirm workout match"}
              style={{
                minHeight: "44px",
                padding: "8px 14px",
                borderRadius: "999px",
                background: "var(--accent-primary)",
                color: "#ffffff",
                border: "none",
                fontSize: "12px",
                fontWeight: "700",
                cursor: actionLoading ? "default" : "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                transition: "opacity 0.15s ease",
                opacity: actionLoading ? 0.6 : 1,
              }}
            >
              <CheckCircle size={15} weight="bold" aria-hidden="true" />
              <span>{lang === "vi" ? "Xác nhận khớp" : "Confirm Match"}</span>
            </button>
          )}

          {onUnlinkMatch && (
            <button
              type="button"
              onClick={handleUnlink}
              disabled={actionLoading}
              aria-label={
                unlinkArmed
                  ? lang === "vi"
                    ? "Nhấn lần nữa để gỡ liên kết"
                    : "Tap again to confirm unlinking"
                  : lang === "vi"
                  ? "Gỡ liên kết bài tập"
                  : "Unlink workout"
              }
              style={{
                minHeight: "44px",
                padding: "8px 12px",
                borderRadius: "999px",
                background: unlinkArmed ? "var(--accent-alert)" : "transparent",
                color: unlinkArmed ? "#ffffff" : "var(--text-secondary)",
                border: unlinkArmed ? "1px solid var(--accent-alert)" : "1px solid var(--border-color)",
                fontSize: "11.5px",
                fontWeight: "600",
                cursor: actionLoading ? "default" : "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                transition: "background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease",
              }}
            >
              <LinkBreak size={14} weight="bold" aria-hidden="true" />
              <span>
                {unlinkArmed
                  ? lang === "vi"
                    ? "Chắc chắn gỡ?"
                    : "Tap to unlink"
                  : lang === "vi"
                  ? "Gỡ khớp"
                  : "Unlink"}
              </span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
