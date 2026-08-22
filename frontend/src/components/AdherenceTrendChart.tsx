export interface AdherenceTrendPoint {
  week_number: number;
  adherence_pct: number;
}

export function computeSparklinePoints(
  trend: AdherenceTrendPoint[],
  { width, height }: { width: number; height: number }
): { x: number; y: number }[] {
  if (trend.length === 0) return [];
  if (trend.length === 1) {
    return [{ x: width, y: (1 - trend[0].adherence_pct) * height }];
  }
  return trend.map((point, i) => ({
    x: (i / (trend.length - 1)) * width,
    y: (1 - point.adherence_pct) * height,
  }));
}

export default function AdherenceTrendChart({ trend, lang }: { trend: AdherenceTrendPoint[]; lang: "en" | "vi" }) {
  const width = 280;
  const height = 50;
  const points = computeSparklinePoints(trend, { width, height });

  if (points.length === 0) {
    return (
      <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
        {lang === "en" ? "Not enough data yet." : "Chưa đủ dữ liệu."}
      </p>
    );
  }

  const path = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", maxWidth: `${width}px`, display: "block" }}>
      <path d={path} fill="none" stroke="var(--accent-primary)" strokeWidth={2} />
      {points.map((p, i) => (
        <circle key={trend[i].week_number} cx={p.x} cy={p.y} r={2.5} fill="var(--accent-primary)" />
      ))}
    </svg>
  );
}
