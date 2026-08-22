export interface WorkoutTypeMixEntry {
  type: string;
  count: number;
  pct: number;
}

export function computeBarLayout(
  mix: { type: string; pct: number }[],
  maxBars = 6
): { type: string; pct: number; widthPct: number }[] {
  const top = mix.slice(0, maxBars);
  const maxPct = Math.max(...top.map((m) => m.pct), 0);
  if (maxPct === 0) return top.map((m) => ({ ...m, widthPct: 0 }));
  return top.map((m) => ({ ...m, widthPct: Math.round((m.pct / maxPct) * 100) }));
}

const TYPE_LABELS: Record<string, { en: string; vi: string }> = {
  long_run: { en: "Long run", vi: "Chạy dài" },
  easy_run: { en: "Easy run", vi: "Chạy nhẹ" },
  tempo: { en: "Tempo", vi: "Tempo" },
  interval: { en: "Interval", vi: "Interval" },
  strength: { en: "Strength", vi: "Sức mạnh" },
  hike: { en: "Hike", vi: "Đi bộ leo núi" },
};

function labelFor(type: string, lang: "en" | "vi"): string {
  return TYPE_LABELS[type]?.[lang] || type;
}

export default function WorkoutTypeMixChart({ mix, lang }: { mix: WorkoutTypeMixEntry[]; lang: "en" | "vi" }) {
  const layout = computeBarLayout(mix);

  if (layout.length === 0) {
    return (
      <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
        {lang === "en" ? "No completed workouts in the last 2 weeks yet." : "Chưa có buổi tập nào hoàn thành trong 2 tuần qua."}
      </p>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
      {layout.map((row) => (
        <div key={row.type} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ width: "110px", fontSize: "12px", color: "var(--text-secondary)", flexShrink: 0 }}>
            {labelFor(row.type, lang)}
          </span>
          <div style={{ flex: 1, background: "var(--border-color)", borderRadius: "6px", height: "10px", overflow: "hidden" }}>
            <div
              style={{
                width: `${row.widthPct}%`,
                background: "var(--accent-primary)",
                height: "100%",
                borderRadius: "6px",
              }}
            />
          </div>
          <span style={{ width: "40px", fontSize: "11px", color: "var(--text-muted)", textAlign: "right", flexShrink: 0 }}>
            {Math.round(row.pct * 100)}%
          </span>
        </div>
      ))}
    </div>
  );
}
