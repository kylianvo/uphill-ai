const DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const DAY_LABELS: Record<string, { en: string; vi: string }> = {
  Monday: { en: "Mon", vi: "T2" },
  Tuesday: { en: "Tue", vi: "T3" },
  Wednesday: { en: "Wed", vi: "T4" },
  Thursday: { en: "Thu", vi: "T5" },
  Friday: { en: "Fri", vi: "T6" },
  Saturday: { en: "Sat", vi: "T7" },
  Sunday: { en: "Sun", vi: "CN" },
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
  const filled = zeroFillDays(missedByDay);
  const maxCount = Math.max(...filled.map((d) => d.count), 1);

  if (filled.every((d) => d.count === 0)) {
    return (
      <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
        {lang === "en" ? "No missed workouts in this window." : "Không có buổi tập nào bị bỏ lỡ trong khoảng này."}
      </p>
    );
  }

  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: "8px", height: "60px" }}>
      {filled.map((d) => (
        <div
          key={d.day_of_week}
          style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "4px", flex: 1 }}
        >
          <div
            style={{
              width: "100%",
              height: `${(d.count / maxCount) * 40}px`,
              background: d.count > 0 ? "var(--accent-alert)" : "var(--border-color)",
              borderRadius: "3px",
            }}
          />
          <span style={{ fontSize: "9.5px", color: "var(--text-muted)" }}>{DAY_LABELS[d.day_of_week][lang]}</span>
        </div>
      ))}
    </div>
  );
}
