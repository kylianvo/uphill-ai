
"use client";

import React, { useState } from "react";
import { PersonSimpleHike, MoonStars } from "@phosphor-icons/react";
import { PacedCheckpoint, parsePaceToMinutes } from "@/lib/paceStrategy";

/** Two stacked panels sharing the distance axis: elevation area, pace steps. */
export function ProfileChart({ paced, lang }: { paced: PacedCheckpoint[]; lang: "en" | "vi" }) {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const width = 720;
  const elevH = 120;
  const paceH = 90;
  const padL = 44;
  const padR = 12;
  const gap = 26;
  const height = elevH + paceH + gap + 30;

  const rows = paced.filter((cp) => cp.distance_km > 0 || paced.indexOf(cp) === 0);
  if (rows.length < 2) return null;

  const maxDist = rows[rows.length - 1].distance_km;
  const elevs = rows.map((r) => r.elevation_m);
  const minElev = Math.min(...elevs);
  const maxElev = Math.max(...elevs, minElev + 10);
  const paces = rows.slice(1).map((r) => parsePaceToMinutes(r.target_pace) ?? 0);
  const maxPace = Math.max(...paces, 1);
  const minPace = Math.min(...paces);

  const x = (km: number) => padL + (km / maxDist) * (width - padL - padR);
  const yElev = (e: number) => 10 + (1 - (e - minElev) / (maxElev - minElev)) * (elevH - 10);
  const paceTop = elevH + gap;
  // faster pace (smaller min/km) sits higher on the panel
  const yPace = (p: number) =>
    paceTop + ((p - minPace * 0.9) / (maxPace - minPace * 0.9 || 1)) * (paceH - 10);

  const elevPath =
    `M ${x(rows[0].distance_km)} ${yElev(rows[0].elevation_m)} ` +
    rows.slice(1).map((r) => `L ${x(r.distance_km)} ${yElev(r.elevation_m)}`).join(" ");
  const elevArea = `${elevPath} L ${x(maxDist)} ${elevH + 10} L ${x(rows[0].distance_km)} ${elevH + 10} Z`;

  // step line: pace of segment i applies from checkpoint i-1 to checkpoint i
  const paceSteps = rows.slice(1).map((r, i) => {
    const x0 = x(rows[i].distance_km);
    const x1 = x(r.distance_km);
    const y = yPace(paces[i]);
    return { x0, x1, y, idx: i + 1 };
  });

  const hover = hoverIdx !== null ? rows[hoverIdx] : null;

  return (
    <div style={{ overflowX: "auto" }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: "100%", minWidth: "480px", display: "block" }}
        onMouseLeave={() => setHoverIdx(null)}
      >
        {/* elevation panel */}
        <text x={padL} y={8} fontSize={9} fill="var(--text-muted)" fontWeight={600}>
          {lang === "en" ? "ELEVATION (m)" : "ĐỘ CAO (m)"}
        </text>
        <path d={elevArea} fill="var(--accent-primary)" opacity={0.14} />
        <path d={elevPath} fill="none" stroke="var(--accent-primary)" strokeWidth={2} />
        <text x={padL - 6} y={yElev(maxElev) + 4} fontSize={9} fill="var(--text-muted)" textAnchor="end">
          {Math.round(maxElev)}
        </text>
        <text x={padL - 6} y={elevH + 8} fontSize={9} fill="var(--text-muted)" textAnchor="end">
          {Math.round(minElev)}
        </text>

        {/* pace panel */}
        <text x={padL} y={paceTop - 6} fontSize={9} fill="var(--text-muted)" fontWeight={600}>
          {lang === "en" ? "TARGET PACE (min/km)" : "PACE MỤC TIÊU (min/km)"}
        </text>
        {paceSteps.map((s) => (
          <line
            key={s.idx}
            x1={s.x0}
            x2={s.x1}
            y1={s.y}
            y2={s.y}
            stroke={rows[s.idx].effort === "hike" ? "var(--text-primary)" : "var(--accent-primary)"}
            strokeWidth={3}
            strokeLinecap="round"
          />
        ))}
        <text x={padL - 6} y={yPace(maxPace) + 4} fontSize={9} fill="var(--text-muted)" textAnchor="end">
          {maxPace.toFixed(1)}
        </text>
        <text x={padL - 6} y={yPace(minPace) + 4} fontSize={9} fill="var(--text-muted)" textAnchor="end">
          {minPace.toFixed(1)}
        </text>

        {/* x axis */}
        <line x1={padL} x2={width - padR} y1={paceTop + paceH} y2={paceTop + paceH} stroke="var(--border-color)" />
        {[0, 0.25, 0.5, 0.75, 1].map((f) => (
          <text
            key={f}
            x={x(maxDist * f)}
            y={paceTop + paceH + 14}
            fontSize={9}
            fill="var(--text-muted)"
            textAnchor="middle"
          >
            {Math.round(maxDist * f)}k
          </text>
        ))}

        {/* hover layer */}
        {hover && hoverIdx !== null && hoverIdx > 0 && (
          <g pointerEvents="none">
            <line
              x1={x(hover.distance_km)}
              x2={x(hover.distance_km)}
              y1={10}
              y2={paceTop + paceH}
              stroke="var(--text-muted)"
              strokeDasharray="3 3"
            />
            <rect
              x={Math.min(x(hover.distance_km) + 8, width - 168)}
              y={14}
              width={160}
              height={44}
              rx={8}
              fill="var(--bg-primary, white)"
              stroke="var(--border-color)"
            />
            <text x={Math.min(x(hover.distance_km) + 16, width - 160)} y={31} fontSize={10} fontWeight={700} fill="var(--text-primary)">
              {hover.name} · {hover.distance_km}k · {hover.elevation_m}m
            </text>
            <text x={Math.min(x(hover.distance_km) + 16, width - 160)} y={48} fontSize={10} fill="var(--text-secondary)">
              {hover.target_pace}/km · {hover.split_time}
              {hover.effort === "hike" ? (lang === "en" ? " · hike" : " · leo bộ") : ""}
            </text>
          </g>
        )}
        {rows.map((r, i) => (
          <rect
            key={i}
            x={i === 0 ? padL : (x(rows[i - 1].distance_km) + x(r.distance_km)) / 2}
            y={0}
            width={
              i === 0
                ? (x(rows[1].distance_km) - padL) / 2
                : (x(rows[Math.min(i + 1, rows.length - 1)].distance_km) - x(rows[i - 1].distance_km)) / 2
            }
            height={paceTop + paceH}
            fill="transparent"
            onMouseEnter={() => setHoverIdx(i)}
          />
        ))}
      </svg>
      <div style={{ display: "flex", gap: "16px", fontSize: "11px", color: "var(--text-secondary)", padding: "4px 0 0 4px" }}>
        <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
          <span style={{ width: 14, height: 3, background: "var(--accent-primary)", borderRadius: 2, display: "inline-block" }} />
          {lang === "en" ? "Run" : "Chạy"}
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
          <span style={{ width: 14, height: 3, background: "var(--text-primary)", borderRadius: 2, display: "inline-block" }} />
          {lang === "en" ? "Hike" : "Leo bộ"}
        </span>
      </div>
    </div>
  );
}

interface PacingSplitsTableProps {
  checkpoints: PacedCheckpoint[];
  lang: "en" | "vi";
  /** Rest minutes keyed by checkpoint index. Only relevant when onRestMinsChange is given. */
  restMins?: Record<number, number>;
  /** When given, the Rest column is shown and editable via this callback. Omit for a read-only table. */
  onRestMinsChange?: (idx: number, mins: number) => void;
  /** ETA per checkpoint index. When omitted, each checkpoint's own split_time is shown instead. */
  etas?: string[];
}

/** Splits table shared between the interactive Pace Strategy modal and read-only chat cards. */
export function PacingSplitsTable({ checkpoints, lang, restMins, onRestMinsChange, etas }: PacingSplitsTableProps) {
  const t = (en: string, vi: string) => (lang === "en" ? en : vi);
  const hasWeather = checkpoints.some((p) => p.temp_c != null);

  return (
    <div style={{ border: "1px solid var(--border-color)", borderRadius: "12px", overflow: "hidden" }}>
      <div style={{ maxHeight: "300px", overflowY: "auto", overflowX: "auto" }}>
        <table style={{ width: "100%", fontSize: "12.5px", borderCollapse: "collapse", textAlign: "left" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-muted)", position: "sticky", top: 0, background: "rgba(255,255,255,0.95)" }}>
              <th style={{ padding: "8px 10px" }}>{t("Waypoint", "Điểm mốc")}</th>
              <th style={{ padding: "8px 10px" }}>{t("Dist", "Cự ly")}</th>
              <th style={{ padding: "8px 10px" }}>{t("Grade", "Dốc")}</th>
              <th style={{ padding: "8px 10px" }}>Pace</th>
              {onRestMinsChange && <th style={{ padding: "8px 10px" }}>{t("Rest (min)", "Nghỉ (phút)")}</th>}
              {hasWeather && <th style={{ padding: "8px 10px" }}>{t("Weather", "Thời tiết")}</th>}
              <th style={{ padding: "8px 10px" }}>ETA</th>
            </tr>
          </thead>
          <tbody>
            {checkpoints.map((cp, idx) => (
              <tr key={idx} style={{ borderBottom: "1px solid rgba(0,0,0,0.04)" }}>
                <td style={{ padding: "8px 10px", fontWeight: 600, display: "flex", alignItems: "center", gap: "4px" }}>
                  {cp.effort === "hike" && <PersonSimpleHike size={14} color="var(--text-primary)" />}
                  {cp.name}
                </td>
                <td style={{ padding: "8px 10px" }}>{cp.distance_km}k</td>
                <td style={{ padding: "8px 10px", color: cp.grade_pct > 0 ? "var(--text-primary)" : "var(--text-muted)" }}>
                  {cp.grade_pct > 0 ? "+" : ""}
                  {cp.grade_pct}%
                </td>
                <td style={{ padding: "8px 10px", fontFamily: "var(--font-mono)" }}>
                  {idx === 0 ? "—" : `${cp.target_pace}/k`}
                </td>
                {onRestMinsChange && (
                  <td style={{ padding: "4px 10px" }}>
                    {idx === 0 || idx === checkpoints.length - 1 ? (
                      "—"
                    ) : (
                      <input
                        type="number"
                        min="0"
                        value={restMins?.[idx] || ""}
                        placeholder="0"
                        onChange={(e) => onRestMinsChange(idx, Math.max(0, parseInt(e.target.value, 10) || 0))}
                        style={{ width: "48px", background: "rgba(0,0,0,0.03)", border: "1px solid var(--border-color)", borderRadius: "6px", padding: "3px 6px", fontSize: "12px", color: "var(--text-primary)" }}
                      />
                    )}
                  </td>
                )}
                {hasWeather && (
                  <td style={{ padding: "8px 10px" }}>
                    {cp.temp_c != null ? `${cp.temp_c}°C` : "—"}
                    {(cp.rain_mm ?? 0) >= 0.1 && (
                      <span style={{ color: "var(--text-muted)" }}> · {cp.rain_mm}mm</span>
                    )}
                    {cp.after_sunset && <MoonStars size={13} style={{ marginLeft: "4px", verticalAlign: "-2px" }} />}
                  </td>
                )}
                <td style={{ padding: "8px 10px", fontFamily: "var(--font-mono)", fontWeight: 700 }}>
                  {etas ? etas[idx] : cp.split_time}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
