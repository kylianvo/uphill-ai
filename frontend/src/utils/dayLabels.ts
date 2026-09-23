export const DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export const DAY_LABELS: Record<string, { en: string; vi: string }> = {
  Monday: { en: "Monday", vi: "Thứ Hai" },
  Tuesday: { en: "Tuesday", vi: "Thứ Ba" },
  Wednesday: { en: "Wednesday", vi: "Thứ Tư" },
  Thursday: { en: "Thursday", vi: "Thứ Năm" },
  Friday: { en: "Friday", vi: "Thứ Sáu" },
  Saturday: { en: "Saturday", vi: "Thứ Bảy" },
  Sunday: { en: "Sunday", vi: "Chủ Nhật" },
};

export function dayLabel(day: string, lang: string): string {
  return DAY_LABELS[day]?.[lang === "vi" ? "vi" : "en"] || day;
}
