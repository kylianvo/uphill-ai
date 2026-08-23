import { useState } from "react";

const DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const DAY_LABELS: Record<string, { en: string; vi: string; fullEn: string; fullVi: string }> = {
  Monday: { en: "Mon", vi: "T2", fullEn: "Monday", fullVi: "Thứ Hai" },
  Tuesday: { en: "Tue", vi: "T3", fullEn: "Tuesday", fullVi: "Thứ Ba" },
  Wednesday: { en: "Wed", vi: "T4", fullEn: "Wednesday", fullVi: "Thứ Tư" },
  Thursday: { en: "Thu", vi: "T5", fullEn: "Thursday", fullVi: "Thứ Năm" },
  Friday: { en: "Fri", vi: "T6", fullEn: "Friday", fullVi: "Thứ Sáu" },
  Saturday: { en: "Sat", vi: "T7", fullEn: "Saturday", fullVi: "Thứ Bảy" },
  Sunday: { en: "Sun", vi: "CN", fullEn: "Sunday", fullVi: "Chủ Nhật" },
};

export interface MissedByDayEntry {
  day_of_week: string;
  count: number;
}

export function zeroFillDays(missedByDay: MissedByDayEntry[]): MissedByDayEntry[] {
  const counts = new Map(missedByDay.map((d) => [d.day_of_week, d.count]));
  return DAY_ORDER.map((day) => ({ day_of_week: day, count: counts.get(day) ?? 0 }));
}

export default function MissedByDayChart({
  missedByDay,
  lang,
}: {
  missedByDay: MissedByDayEntry[];
  lang: "en" | "vi";
}) {
  const [hoveredDay, setHoveredDay] = useState<string | null>(null);
  const filled = zeroFillDays(missedByDay);
  const maxCount = Math.max(...filled.map((d) => d.count), 1);

  if (filled.every((d) => d.count === 0)) {
    return (
      <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
        {lang === "en" ? "No missed workouts in this window." : "Không có buổi tập nào bị bỏ trong khung thời gian này."}
      </p>
    );
  }

  const activeEntry = hoveredDay ? filled.find((d) => d.day_of_week === hoveredDay) : null;

  return (
    <div style={{ position: "relative", width: "100%" }}>
      {activeEntry && (
        <div
          role="tooltip"
          data-testid="missed-tooltip"
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
          <span>{lang === "en" ? DAY_LABELS[activeEntry.day_of_week].fullEn : DAY_LABELS[activeEntry.day_of_week].fullVi}:</span>
          <span style={{ color: activeEntry.count > 0 ? "var(--accent-alert, #ef4444)" : "var(--text-muted)" }}>
            {lang === "en"
              ? `${activeEntry.count} missed`
              : `${activeEntry.count} buổi bỏ`}
          </span>
        </div>
      )}

      <div style={{ display: "flex", alignItems: "flex-end", gap: "8px", height: "65px", paddingTop: "6px" }}>
        {filled.map((d) => {
          const isHovered = hoveredDay === d.day_of_week;
          const barHeight = Math.max(d.count > 0 ? (d.count / maxCount) * 42 : 4, 4);

          return (
            <div
              key={d.day_of_week}
              onMouseEnter={() => setHoveredDay(d.day_of_week)}
              onMouseLeave={() => setHoveredDay(null)}
              onFocus={() => setHoveredDay(d.day_of_week)}
              onBlur={() => setHoveredDay(null)}
              tabIndex={0}
              role="group"
              aria-label={`${DAY_LABELS[d.day_of_week].fullEn}: ${d.count} missed`}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "4px",
                flex: 1,
                cursor: "pointer",
                outline: "none",
              }}
            >
              <div
                style={{
                  width: "100%",
                  height: `${barHeight}px`,
                  background: d.count > 0
                    ? isHovered
                      ? "var(--accent-alert-hover, #dc2626)"
                      : "var(--accent-alert, #ef4444)"
                    : isHovered
                    ? "var(--border-color-hover, #475569)"
                    : "var(--border-color, #334155)",
                  borderRadius: "3px",
                  transform: isHovered ? "translateY(-3px)" : "none",
                  transition: "transform 0.15s ease, background-color 0.15s ease",
                  boxShadow: isHovered && d.count > 0 ? "0 2px 8px rgba(239, 68, 68, 0.3)" : "none",
                }}
              />
              <span
                style={{
                  fontSize: "9.5px",
                  color: isHovered ? "var(--text-primary)" : "var(--text-muted)",
                  fontWeight: isHovered ? 600 : 400,
                  transition: "color 0.15s ease",
                }}
              >
                {DAY_LABELS[d.day_of_week][lang]}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
