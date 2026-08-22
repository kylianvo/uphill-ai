import { useState } from "react";

export interface AdherenceTrendPoint {
  week_number: number;
  adherence_pct: number;
}

export function computeSparklinePoints(
  trend: AdherenceTrendPoint[],
  { width, height, padding = 8 }: { width: number; height: number; padding?: number }
): { x: number; y: number }[] {
  if (trend.length === 0) return [];
  const innerHeight = height - padding * 2;
  if (trend.length === 1) {
    return [{ x: width - padding, y: padding + (1 - trend[0].adherence_pct) * innerHeight }];
  }
  const innerWidth = width - padding * 2;
  return trend.map((point, i) => ({
    x: padding + (i / (trend.length - 1)) * innerWidth,
    y: padding + (1 - point.adherence_pct) * innerHeight,
  }));
}

export default function AdherenceTrendChart({
  trend,
  lang,
}: {
  trend: AdherenceTrendPoint[];
  lang: "en" | "vi";
}) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const width = 280;
  const height = 55;
  const points = computeSparklinePoints(trend, { width, height, padding: 8 });

  if (points.length === 0) {
    return (
      <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
        {lang === "en" ? "Not enough data yet." : "Chưa đủ dữ liệu."}
      </p>
    );
  }

  const path = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
  const activePoint = hoveredIdx !== null ? points[hoveredIdx] : null;
  const activeData = hoveredIdx !== null ? trend[hoveredIdx] : null;

  return (
    <div style={{ position: "relative", width: "100%", maxWidth: `${width}px` }}>
      {activePoint && activeData && (
        <div
          role="tooltip"
          data-testid="trend-tooltip"
          style={{
            position: "absolute",
            top: "-26px",
            left: `${(activePoint.x / width) * 100}%`,
            transform: "translateX(-50%)",
            background: "var(--bg-card, #1e293b)",
            border: "1px solid var(--border-color)",
            color: "var(--text-primary)",
            padding: "2px 7px",
            borderRadius: "6px",
            fontSize: "11px",
            fontWeight: 600,
            whiteSpace: "nowrap",
            pointerEvents: "none",
            boxShadow: "0 4px 12px rgba(0,0,0,0.18)",
            zIndex: 10,
            display: "flex",
            alignItems: "center",
            gap: "5px",
          }}
        >
          <span>{lang === "en" ? `Wk ${activeData.week_number}` : `T${activeData.week_number}`}</span>
          <span style={{ color: "var(--accent-primary)" }}>{Math.round(activeData.adherence_pct * 100)}%</span>
        </div>
      )}

      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: "100%", height: "auto", display: "block", overflow: "visible" }}
      >
        <path d={path} fill="none" stroke="var(--accent-primary)" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />

        {activePoint && (
          <line
            x1={activePoint.x}
            y1={0}
            x2={activePoint.x}
            y2={height}
            stroke="var(--accent-primary)"
            strokeDasharray="2 2"
            strokeWidth={1}
            opacity={0.6}
          />
        )}

        {points.map((p, i) => {
          const isHovered = hoveredIdx === i;
          return (
            <g key={trend[i].week_number}>
              <circle
                cx={p.x}
                cy={p.y}
                r={isHovered ? 4.5 : 2.5}
                fill={isHovered ? "var(--bg-primary, #0f172a)" : "var(--accent-primary)"}
                stroke="var(--accent-primary)"
                strokeWidth={isHovered ? 2 : 0}
                style={{ transition: "r 0.15s ease, stroke-width 0.15s ease" }}
              />
              {/* Invisible large hit area for touch/hover */}
              <circle
                cx={p.x}
                cy={p.y}
                r={14}
                fill="transparent"
                style={{ cursor: "pointer" }}
                onMouseEnter={() => setHoveredIdx(i)}
                onMouseLeave={() => setHoveredIdx(null)}
                aria-label={`Week ${trend[i].week_number}: ${Math.round(trend[i].adherence_pct * 100)}% adherence`}
                tabIndex={0}
                onFocus={() => setHoveredIdx(i)}
                onBlur={() => setHoveredIdx(null)}
              />
            </g>
          );
        })}
      </svg>
    </div>
  );
}
