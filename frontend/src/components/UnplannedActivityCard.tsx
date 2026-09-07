"use client";

import React, { useState } from "react";
import {
  Watch,
  Sneaker,
  Timer,
  Heart,
  Mountains,
  Lightning,
  LinkSimple,
  Clock,
  Check,
  Barbell,
} from "@phosphor-icons/react";
import { triggerHaptic } from "../utils/native";
import CorosAttribution from "./CorosAttribution";
import { RawMatchActivity } from "../hooks/useMatching";

export interface UnplannedActivityCardProps {
  activity: RawMatchActivity;
  availableWorkouts?: Array<{ id: number; title: string; type: string }>;
  lang: "en" | "vi";
  isMobile: boolean;
  onLinkToWorkout?: (activityId: number, workoutId: number) => Promise<boolean>;
}

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

export default function UnplannedActivityCard({
  activity,
  availableWorkouts = [],
  lang,
  isMobile,
  onLinkToWorkout,
}: UnplannedActivityCardProps) {
  const [selectingWorkout, setSelectingWorkout] = useState(false);
  const [linkingLoading, setLinkingLoading] = useState(false);

  const actualPace = formatPace(activity.duration_seconds, activity.distance_km);
  const formattedTime = formatActivityTime(activity.start_time);

  const handleSelectWorkout = async (workoutId: number) => {
    if (!onLinkToWorkout || linkingLoading) return;
    setLinkingLoading(true);
    triggerHaptic();
    try {
      const ok = await onLinkToWorkout(activity.activity_id, workoutId);
      if (ok) {
        setSelectingWorkout(false);
      }
    } finally {
      setLinkingLoading(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        padding: isMobile ? "12px" : "14px",
        borderRadius: "14px",
        background: "var(--bg-card)",
        border: "1px dashed rgba(0, 0, 0, 0.2)",
        boxShadow: "0 2px 6px rgba(0, 0, 0, 0.02)",
      }}
    >
      {/* Header: Device & Unplanned Badge */}
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
          <Watch size={15} weight="bold" color="var(--text-secondary)" aria-hidden="true" />
          <span style={{ fontSize: "12px", fontWeight: "700", color: "var(--text-primary)" }}>
            {activity.device_model || (activity.source_provider?.toUpperCase() ?? "WATCH")}
          </span>
          {formattedTime && (
            <span style={{ fontSize: "11px", color: "var(--text-muted)", display: "inline-flex", alignItems: "center", gap: "3px" }}>
              <Clock size={11} aria-hidden="true" />
              {formattedTime}
            </span>
          )}
        </div>

        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            padding: "2px 8px",
            borderRadius: "999px",
            background: "rgba(0, 0, 0, 0.04)",
            color: "var(--text-secondary)",
            border: "1px solid var(--border-color)",
            fontSize: "11px",
            fontWeight: "600",
          }}
        >
          {lang === "vi" ? "Hoạt động ngoài kế hoạch" : "Unplanned Activity"}
        </span>
      </div>

      {/* Metrics Row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: isMobile ? "repeat(2, 1fr)" : "repeat(4, 1fr)",
          gap: "8px",
        }}
      >
        {activity.distance_km != null && (
          <div
            style={{
              padding: "6px 8px",
              borderRadius: "8px",
              background: "rgba(0, 0, 0, 0.02)",
              border: "1px solid rgba(0, 0, 0, 0.04)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "10px", color: "var(--text-muted)", fontWeight: "600" }}>
              <Sneaker size={12} weight="bold" aria-hidden="true" />
              <span>{lang === "vi" ? "QUÃNG ĐƯỜNG" : "DISTANCE"}</span>
            </div>
            <div style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-primary)", marginTop: "2px" }}>
              {activity.distance_km.toFixed(1)} km
            </div>
          </div>
        )}

        <div
          style={{
            padding: "6px 8px",
            borderRadius: "8px",
            background: "rgba(0, 0, 0, 0.02)",
            border: "1px solid rgba(0, 0, 0, 0.04)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "10px", color: "var(--text-muted)", fontWeight: "600" }}>
            <Timer size={12} weight="bold" aria-hidden="true" />
            <span>{lang === "vi" ? "THỜI GIAN" : "DURATION"}</span>
          </div>
          <div style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-primary)", marginTop: "2px" }}>
            {formatDuration(activity.duration_seconds)}
          </div>
        </div>

        {activity.sets != null && activity.sets > 0 && (
          <div
            style={{
              padding: "6px 8px",
              borderRadius: "8px",
              background: "rgba(0, 0, 0, 0.02)",
              border: "1px solid rgba(0, 0, 0, 0.04)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "10px", color: "var(--text-muted)", fontWeight: "600" }}>
              <Barbell size={12} weight="bold" aria-hidden="true" />
              <span>{lang === "vi" ? "HIỆP TẬP" : "SETS"}</span>
            </div>
            <div style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-primary)", marginTop: "2px" }}>
              {activity.sets} {lang === "vi" ? "hiệp" : "sets"}
            </div>
          </div>
        )}

        {actualPace && (
          <div
            style={{
              padding: "6px 8px",
              borderRadius: "8px",
              background: "rgba(0, 0, 0, 0.02)",
              border: "1px solid rgba(0, 0, 0, 0.04)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "10px", color: "var(--text-muted)", fontWeight: "600" }}>
              <Lightning size={12} weight="bold" aria-hidden="true" />
              <span>{lang === "vi" ? "PACE" : "PACE"}</span>
            </div>
            <div style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-primary)", marginTop: "2px" }}>
              {actualPace}
            </div>
          </div>
        )}

        {activity.avg_hr != null && (
          <div
            style={{
              padding: "6px 8px",
              borderRadius: "8px",
              background: "rgba(0, 0, 0, 0.02)",
              border: "1px solid rgba(0, 0, 0, 0.04)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "10px", color: "var(--text-muted)", fontWeight: "600" }}>
              <Heart size={12} weight="bold" color="#ef4444" aria-hidden="true" />
              <span>{lang === "vi" ? "NHỊP TIM" : "HR"}</span>
            </div>
            <div style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-primary)", marginTop: "2px" }}>
              {activity.avg_hr} bpm
            </div>
          </div>
        )}

        {activity.elevation_gain_m != null && activity.elevation_gain_m > 0 && (
          <div
            style={{
              padding: "6px 8px",
              borderRadius: "8px",
              background: "rgba(0, 0, 0, 0.02)",
              border: "1px solid rgba(0, 0, 0, 0.04)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "10px", color: "var(--text-muted)", fontWeight: "600" }}>
              <Mountains size={12} weight="bold" aria-hidden="true" />
              <span>{lang === "vi" ? "ĐỘ DỐC" : "ELEVATION"}</span>
            </div>
            <div style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-primary)", marginTop: "2px" }}>
              +{Math.round(activity.elevation_gain_m)} m
            </div>
          </div>
        )}
      </div>

      {/* Linking section */}
      {availableWorkouts.length > 0 && onLinkToWorkout && (
        <div style={{ marginTop: "4px" }}>
          {!selectingWorkout ? (
            <button
              type="button"
              onClick={() => {
                setSelectingWorkout(true);
                triggerHaptic();
              }}
              style={{
                minHeight: "44px",
                padding: "8px 14px",
                borderRadius: "999px",
                background: "transparent",
                color: "var(--accent-primary)",
                border: "1px solid var(--accent-primary)",
                fontSize: "12px",
                fontWeight: "600",
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              <LinkSimple size={15} weight="bold" aria-hidden="true" />
              <span>{lang === "vi" ? "Gán vào bài tập của ngày này" : "Link to workout"}</span>
            </button>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <div style={{ fontSize: "11px", fontWeight: "700", color: "var(--text-secondary)" }}>
                {lang === "vi" ? "Chọn bài tập cần gán:" : "Select workout to link:"}
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                {availableWorkouts.map((wo) => (
                  <button
                    key={wo.id}
                    type="button"
                    disabled={linkingLoading}
                    onClick={() => handleSelectWorkout(wo.id)}
                    style={{
                      minHeight: "44px",
                      padding: "8px 12px",
                      borderRadius: "8px",
                      background: "rgba(25, 206, 139, 0.1)",
                      border: "1px solid rgba(25, 206, 139, 0.3)",
                      color: "var(--text-primary)",
                      fontSize: "12px",
                      fontWeight: "600",
                      cursor: linkingLoading ? "default" : "pointer",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    <Check size={13} weight="bold" aria-hidden="true" />
                    <span>{wo.title || wo.type}</span>
                  </button>
                ))}
                <button
                  type="button"
                  onClick={() => setSelectingWorkout(false)}
                  style={{
                    minHeight: "44px",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    background: "transparent",
                    border: "1px solid var(--border-color)",
                    color: "var(--text-muted)",
                    fontSize: "12px",
                    cursor: "pointer",
                  }}
                >
                  {lang === "vi" ? "Hủy" : "Cancel"}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Attribution footer */}
      <div style={{ paddingTop: "4px", borderTop: "1px solid rgba(0, 0, 0, 0.04)" }}>
        <CorosAttribution deviceModel={activity.device_model} provider={activity.source_provider} />
      </div>
    </div>
  );
}
