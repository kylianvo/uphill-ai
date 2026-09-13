"use client";

import React, { useCallback } from "react";
import { CheckCircle, WarningCircle, Sneaker, Mountains, Timer } from "@phosphor-icons/react";
import { translations } from "../app/translations";

export interface WeekReviewPerWorkout {
  workout_id: number;
  day_of_week: string;
  title: string;
  type: string;
  planned: { duration_minutes: number | null; distance_km: number | null; elevation_gain_m: number | null };
  actual: {
    state: "matched" | "checkbox_only" | "missed" | "pending";
    duration_minutes: number | null;
    distance_km: number | null;
    elevation_gain_m: number | null;
  };
}

export interface WeekReviewData {
  week_number: number;
  planned: { duration_minutes: number; distance_km: number; elevation_gain_m: number; workout_count: number };
  actual: {
    total_actual_km: number;
    total_actual_minutes: number;
    total_actual_vert_m: number;
    matched_km: number;
    matched_vert_m: number;
    matched_count: number;
    unplanned_km: number;
    unplanned_hours: number;
    unplanned_vert_m: number;
    unplanned_count: number;
  };
  completion_pct: number;
  checkbox_completion_pct: number;
  per_workout: WeekReviewPerWorkout[];
  unplanned: Array<{ activity_id: number; distance_km: number | null; duration_seconds: number | null; activity_type?: string | null }>;
  missed: Array<{ day_of_week: string; title: string }>;
  coverage: { completed_count: number; matched_count: number; checkbox_only_count: number };
  narrative?: { summary: string; highlights: string[]; watch: string[] };
}

export interface WeeklyReviewProps {
  data: WeekReviewData | null;
  lang: "en" | "vi";
}

/**
 * "Actual", credited: real recorded minutes/km/vert for a matched workout,
 * or its planned figures as the best available estimate for a workout that
 * was ticked complete but never synced from a watch. Missed and pending
 * workouts contribute nothing. Unplanned activities (real volume with no
 * matching workout) are added on top, same as the backend's total_actual_*.
 */
export function computeCreditedActual(data: WeekReviewData): { minutes: number; km: number; vertM: number; pct: number } {
  let minutes = 0;
  let km = 0;
  let vertM = 0;
  for (const w of data.per_workout) {
    if (w.actual.state === "matched") {
      minutes += w.actual.duration_minutes ?? 0;
      km += w.actual.distance_km ?? 0;
      vertM += w.actual.elevation_gain_m ?? 0;
    } else if (w.actual.state === "checkbox_only") {
      minutes += w.planned.duration_minutes ?? 0;
      km += w.planned.distance_km ?? 0;
      vertM += w.planned.elevation_gain_m ?? 0;
    }
  }
  minutes += data.actual.unplanned_hours * 60;
  km += data.actual.unplanned_km;
  vertM += data.actual.unplanned_vert_m;
  const pct = data.planned.duration_minutes > 0 ? Math.round((minutes / data.planned.duration_minutes) * 100) : 0;
  return { minutes, km, vertM, pct };
}

export function ringColor(pct: number): string {
  if (pct >= 80) return "var(--accent-primary)";
  if (pct >= 50) return "#d97706";
  return "var(--accent-alert)";
}

export function CompletionRing({ pct, size = 88 }: { pct: number; size?: number }) {
  const strokeWidth = Math.max(5, Math.round(size * 0.1));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, pct));
  const offset = circumference * (1 - clamped / 100);
  const color = ringColor(pct);
  const fontSize = Math.max(10, Math.round(size * 0.2));
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`${Math.round(pct)}%`}>
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(0,0,0,0.08)" strokeWidth={strokeWidth} />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: "stroke-dashoffset 0.4s ease" }}
      />
      <text x="50%" y="50%" textAnchor="middle" dominantBaseline="central" fontSize={fontSize} fontWeight="800" fill="var(--text-primary)">
        {Math.round(pct)}%
      </text>
    </svg>
  );
}

function StatePill({ state, t }: { state: WeekReviewPerWorkout["actual"]["state"]; t: (k: keyof typeof translations.en) => string }) {
  if (state === "matched") {
    return (
      <span
        style={{
          display: "inline-flex", alignItems: "center", gap: "4px", padding: "2px 8px", borderRadius: "999px",
          background: "rgba(25, 206, 139, 0.15)", color: "var(--accent-primary)", border: "1px solid rgba(25, 206, 139, 0.3)",
          fontSize: "10.5px", fontWeight: 700, whiteSpace: "nowrap",
        }}
      >
        <CheckCircle size={12} weight="fill" aria-hidden="true" />
        {t("week_review_state_matched")}
      </span>
    );
  }
  if (state === "checkbox_only") {
    return (
      <span
        style={{
          display: "inline-flex", alignItems: "center", gap: "4px", padding: "2px 8px", borderRadius: "999px",
          background: "rgba(245, 158, 11, 0.12)", color: "#d97706", border: "1px solid rgba(245, 158, 11, 0.35)",
          fontSize: "10.5px", fontWeight: 700, whiteSpace: "nowrap",
        }}
      >
        <WarningCircle size={12} weight="fill" aria-hidden="true" />
        {t("week_review_state_checkbox")}
      </span>
    );
  }
  if (state === "missed") {
    return <span style={{ fontSize: "10.5px", fontWeight: 700, color: "var(--accent-alert)" }}>{t("week_review_state_missed")}</span>;
  }
  return <span style={{ fontSize: "10.5px", fontWeight: 600, color: "var(--text-muted)" }}>{t("week_review_state_pending")}</span>;
}

/**
 * Detail body for the weekly planned-vs-actual review. Deliberately has no
 * card wrapper, header, or toggle of its own -- it renders inside the parent
 * Weekly Volume card's "Show details" disclosure, which owns the small
 * at-a-glance ring/summary row and the expand/collapse state.
 */
export default function WeeklyReview({ data, lang }: WeeklyReviewProps) {
  const t = useCallback((key: keyof typeof translations.en) => translations[lang]?.[key] || translations.en[key] || key, [lang]);

  if (!data) return null;

  const { planned, checkbox_completion_pct, per_workout, unplanned, narrative } = data;
  const credited = computeCreditedActual(data);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginTop: "12px", paddingTop: "12px", borderTop: "1px solid rgba(0,0,0,0.06)" }}>
      {checkbox_completion_pct !== credited.pct && (
        <span style={{ fontSize: "10.5px", color: "var(--text-muted)" }}>
          {t("week_review_logged_as_complete")}: {checkbox_completion_pct}% · {t("week_review_completion")}: {credited.pct}%
        </span>
      )}

      {/* Time / Distance / Vert actual-vs-planned breakdown */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "12px" }}>
        <div
          style={{
            padding: "10px 12px", borderRadius: "10px", background: "rgba(0, 0, 0, 0.02)", border: "1px solid rgba(0, 0, 0, 0.05)",
            minWidth: "110px", flex: 1,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "10.5px", color: "var(--text-muted)", fontWeight: 700 }}>
            <Timer size={13} weight="bold" aria-hidden="true" />
            <span>{t("week_review_time")}</span>
          </div>
          <div style={{ fontSize: "15px", fontWeight: 700, color: "var(--text-primary)", marginTop: "2px" }}>
            {(credited.minutes / 60).toFixed(1)} / {(planned.duration_minutes / 60).toFixed(1)} {t("week_review_hrs_short")}
          </div>
          <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "1px" }}>
            {t("week_review_actual")} / {t("week_review_planned")}
          </div>
        </div>

        <div
          style={{
            padding: "10px 12px", borderRadius: "10px", background: "rgba(0, 0, 0, 0.02)", border: "1px solid rgba(0, 0, 0, 0.05)",
            minWidth: "110px", flex: 1,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "10.5px", color: "var(--text-muted)", fontWeight: 700 }}>
            <Sneaker size={13} weight="bold" aria-hidden="true" />
            <span>{t("week_review_distance")}</span>
          </div>
          <div style={{ fontSize: "15px", fontWeight: 700, color: "var(--text-primary)", marginTop: "2px" }}>
            {credited.km.toFixed(1)} / {planned.distance_km.toFixed(1)} km
          </div>
          <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "1px" }}>
            {t("week_review_actual")} / {t("week_review_planned")}
          </div>
        </div>

        <div
          style={{
            padding: "10px 12px", borderRadius: "10px", background: "rgba(0, 0, 0, 0.02)", border: "1px solid rgba(0, 0, 0, 0.05)",
            minWidth: "110px", flex: 1,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "10.5px", color: "var(--text-muted)", fontWeight: 700 }}>
            <Mountains size={13} weight="bold" aria-hidden="true" />
            <span>{t("week_review_vert")}</span>
          </div>
          <div style={{ fontSize: "15px", fontWeight: 700, color: "var(--text-primary)", marginTop: "2px" }}>
            {Math.round(credited.vertM)} / {Math.round(planned.elevation_gain_m)} m
          </div>
          <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "1px" }}>
            {t("week_review_actual")} / {t("week_review_planned")}
          </div>
        </div>
      </div>

      {/* Per-workout state list */}
      {per_workout.length > 0 && (
        <div>
          <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
            {t("week_review_per_workout")}
          </span>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "8px" }}>
            {per_workout.map((w) => (
              <div
                key={w.workout_id}
                style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px",
                  padding: "8px 10px", borderRadius: "8px", background: "rgba(0,0,0,0.02)", border: "1px solid rgba(0,0,0,0.05)",
                }}
              >
                <div style={{ display: "flex", flexDirection: "column", gap: "1px", minWidth: 0 }}>
                  <span style={{ fontSize: "12.5px", fontWeight: 600, color: "var(--text-primary)" }}>{w.day_of_week}: {w.title}</span>
                  <span style={{ fontSize: "10.5px", color: "var(--text-muted)" }}>
                    {w.planned.duration_minutes ?? 0}min · {(w.planned.distance_km ?? 0).toFixed(1)}km
                  </span>
                </div>
                <StatePill state={w.actual.state} t={t} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Unplanned activities */}
      {unplanned.length > 0 && (
        <div>
          <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
            {t("week_review_unplanned_activities")}
          </span>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "8px" }}>
            {unplanned.map((a) => (
              <div
                key={a.activity_id}
                style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px",
                  padding: "8px 10px", borderRadius: "8px", background: "rgba(0,0,0,0.02)", border: "1px dashed rgba(0,0,0,0.2)",
                }}
              >
                <span style={{ fontSize: "12.5px", color: "var(--text-primary)" }}>
                  {(a.distance_km ?? 0).toFixed(1)} km · {Math.round((a.duration_seconds ?? 0) / 60)} min
                </span>
                <span
                  style={{
                    fontSize: "10.5px", fontWeight: 600, color: "var(--text-secondary)",
                    background: "rgba(0,0,0,0.04)", border: "1px solid var(--border-color)", borderRadius: "999px", padding: "2px 8px",
                  }}
                >
                  {t("week_review_state_unplanned")}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Narrative: Highlights / Areas to Watch */}
      {narrative && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "16px" }}>
          {narrative.highlights.length > 0 && (
            <div style={{ flex: 1, minWidth: "180px" }}>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--accent-primary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                {t("week_review_highlights")}
              </span>
              <ul style={{ margin: "8px 0 0", padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "6px" }}>
                {narrative.highlights.map((h, i) => (
                  <li key={i} style={{ display: "flex", alignItems: "flex-start", gap: "6px", fontSize: "12px", color: "var(--text-primary)" }}>
                    <CheckCircle size={13} weight="fill" color="var(--accent-primary)" style={{ marginTop: "2px", flexShrink: 0 }} aria-hidden="true" />
                    <span>{h}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {narrative.watch.length > 0 && (
            <div style={{ flex: 1, minWidth: "180px" }}>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "#d97706", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                {t("week_review_watch")}
              </span>
              <ul style={{ margin: "8px 0 0", padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "6px" }}>
                {narrative.watch.map((wtxt, i) => (
                  <li key={i} style={{ display: "flex", alignItems: "flex-start", gap: "6px", fontSize: "12px", color: "var(--text-primary)" }}>
                    <WarningCircle size={13} weight="fill" color="#d97706" style={{ marginTop: "2px", flexShrink: 0 }} aria-hidden="true" />
                    <span>{wtxt}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
