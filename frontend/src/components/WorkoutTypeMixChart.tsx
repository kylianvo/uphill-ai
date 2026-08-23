import { useState } from "react";

export interface WorkoutTypeMixEntry {
  type: string;
  count: number;
  pct: number;
}

export function computeBarLayout(
  mix: WorkoutTypeMixEntry[],
  maxBars = 6
): (WorkoutTypeMixEntry & { widthPct: number })[] {
  const top = mix.slice(0, maxBars);
  return top.map((m) => ({
    ...m,
    widthPct: m.count > 0 && m.pct > 0 ? Math.max(Math.round(m.pct * 100), 2) : 0,
  }));
}

const CANONICAL_TYPES: Record<string, { en: string; vi: string }> = {
  easy: { en: "Easy", vi: "Easy" },
  easy_run: { en: "Easy", vi: "Easy" },
  "easy run": { en: "Easy", vi: "Easy" },
  strength: { en: "Strength", vi: "Strength" },
  tempo: { en: "Tempo", vi: "Tempo" },
  tempo_run: { en: "Tempo", vi: "Tempo" },
  "tempo run": { en: "Tempo", vi: "Tempo" },
  threshold: { en: "Tempo", vi: "Tempo" },
  long_run: { en: "Long Run", vi: "Long Run" },
  "long run": { en: "Long Run", vi: "Long Run" },
  long: { en: "Long Run", vi: "Long Run" },
  muscular_endurance: { en: "Muscular Endurance", vi: "Muscular Endurance" },
  "muscular endurance": { en: "Muscular Endurance", vi: "Muscular Endurance" },
  me_session: { en: "Muscular Endurance", vi: "Muscular Endurance" },
  me: { en: "Muscular Endurance", vi: "Muscular Endurance" },
  interval: { en: "Interval", vi: "Interval" },
  intervals: { en: "Interval", vi: "Interval" },
  recovery: { en: "Recovery", vi: "Recovery" },
  recovery_run: { en: "Recovery", vi: "Recovery" },
  "recovery run": { en: "Recovery", vi: "Recovery" },
  hike: { en: "Hike", vi: "Hike / Trekking" },
  hiking: { en: "Hike", vi: "Hike / Trekking" },
  trekking: { en: "Hike", vi: "Hike / Trekking" },
  trail_run: { en: "Trail Run", vi: "Trail Run" },
  "trail run": { en: "Trail Run", vi: "Trail Run" },
  hill_repeat: { en: "Hill Repeats", vi: "Hill Repeats" },
  hill_repeats: { en: "Hill Repeats", vi: "Hill Repeats" },
  "hill repeat": { en: "Hill Repeats", vi: "Hill Repeats" },
  "hill repeats": { en: "Hill Repeats", vi: "Hill Repeats" },
  hill_sprint: { en: "Hill Sprints", vi: "Hill Sprints" },
  hill_sprints: { en: "Hill Sprints", vi: "Hill Sprints" },
  "hill sprint": { en: "Hill Sprints", vi: "Hill Sprints" },
  "hill sprints": { en: "Hill Sprints", vi: "Hill Sprints" },
  fartlek: { en: "Fartlek", vi: "Fartlek" },
  cross_training: { en: "Cross-Training", vi: "Cross-Training" },
  "cross-training": { en: "Cross-Training", vi: "Cross-Training" },
  race: { en: "Race", vi: "Race" },
  race_day: { en: "Race", vi: "Race" },
  "race day": { en: "Race", vi: "Race" },
  rest: { en: "Rest", vi: "Rest" },
};

export function labelFor(type: string, lang: "en" | "vi" = "en"): string {
  if (!type) return "Other";
  const normalizedKey = type.toLowerCase().trim();
  if (CANONICAL_TYPES[normalizedKey]) {
    return CANONICAL_TYPES[normalizedKey][lang] || CANONICAL_TYPES[normalizedKey].en;
  }
  return type
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function WorkoutTypeMixChart({ mix, lang }: { mix: WorkoutTypeMixEntry[]; lang: "en" | "vi" }) {
  const [hoveredType, setHoveredType] = useState<string | null>(null);
  const layout = computeBarLayout(mix);

  if (layout.length === 0) {
    return (
      <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
        {lang === "en" ? "No completed workouts in this window yet." : "Chưa có buổi tập nào hoàn thành trong khung thời gian này."}
      </p>
    );
  }

  const activeRow = hoveredType ? layout.find((r) => r.type === hoveredType) : null;

  return (
    <div style={{ position: "relative", width: "100%" }}>
      {activeRow && (
        <div
          role="tooltip"
          data-testid="mix-tooltip"
          style={{
            position: "absolute",
            top: "-26px",
            left: "50%",
            transform: "translateX(-50%)",
            background: "var(--bg-card, #1e293b)",
            border: "1px solid var(--border-color)",
            color: "var(--text-primary)",
            padding: "2px 8px",
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
          <span>{labelFor(activeRow.type, lang)}:</span>
          <span style={{ color: "var(--accent-primary)" }}>
            {lang === "en"
              ? `${activeRow.count} workouts (${Math.round(activeRow.pct * 100)}%)`
              : `${activeRow.count} buổi (${Math.round(activeRow.pct * 100)}%)`}
          </span>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "9px" }}>
        {layout.map((row) => {
          const isHovered = hoveredType === row.type;
          return (
            <div
              key={row.type}
              onMouseEnter={() => setHoveredType(row.type)}
              onMouseLeave={() => setHoveredType(null)}
              onFocus={() => setHoveredType(row.type)}
              onBlur={() => setHoveredType(null)}
              tabIndex={0}
              role="group"
              aria-label={`${labelFor(row.type, lang)}: ${row.count} workouts, ${Math.round(row.pct * 100)}%`}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                padding: "2px 4px",
                borderRadius: "4px",
                background: isHovered ? "var(--bg-hover, rgba(255,255,255,0.04))" : "transparent",
                cursor: "pointer",
                transition: "background-color 0.15s ease",
                outline: "none",
              }}
            >
              <span
                style={{
                  width: "135px",
                  fontSize: "12px",
                  color: isHovered ? "var(--text-primary)" : "var(--text-secondary)",
                  fontWeight: isHovered ? 600 : 400,
                  flexShrink: 0,
                  transition: "color 0.15s ease",
                }}
              >
                {labelFor(row.type, lang)}
              </span>
              <div
                style={{
                  flex: 1,
                  background: isHovered ? "var(--border-color-hover, #475569)" : "var(--border-color)",
                  borderRadius: "6px",
                  height: "10px",
                  overflow: "hidden",
                  transition: "background-color 0.15s ease",
                }}
              >
                <div
                  style={{
                    width: `${row.widthPct}%`,
                    background: isHovered ? "var(--accent-primary-hover, #818cf8)" : "var(--accent-primary)",
                    height: "100%",
                    borderRadius: "6px",
                    transition: "background-color 0.15s ease",
                  }}
                />
              </div>
              <span
                style={{
                  width: "44px",
                  fontSize: "11px",
                  color: isHovered ? "var(--text-primary)" : "var(--text-muted)",
                  fontWeight: isHovered ? 600 : 400,
                  textAlign: "right",
                  flexShrink: 0,
                  transition: "color 0.15s ease",
                }}
              >
                {Math.round(row.pct * 100)}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
