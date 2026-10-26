// B-races: tune-up races inside a race plan (backend services/b_race.py). The server sends codes; labels live here.

export type Lang = "en" | "vi";
export type BRaceLevel = "good" | "conditions" | "risky" | "not_recommended";
export type BRaceEffort = "race" | "training";

export interface BRaceSuggestion { distance_km: number; effort: BRaceEffort }
export interface BRaceCostRow { week: number; day: string; title_before: string; title_after: string; minutes_before: number; minutes_after: number }
export interface BRaceVerdict {
  level: BRaceLevel;
  reasons: string[];
  numbers: Record<string, number | null>;
  taper_days: number;
  recovery_days: number;
  suggestion: BRaceSuggestion | null;
  cost: { changed: BRaceCostRow[]; peak_week_minutes: { before: number | null; after: number | null } | null } | null;
}
export interface BRace {
  id: number;
  race_name: string;
  race_date: string;
  distance_km: number;
  elevation_gain_m: number | null;
  options_km?: number[];
  effort: BRaceEffort;
  status: "planned" | "done" | "cancelled";
  kept_against: string | null;
  verdict: BRaceVerdict;
  opinion?: string;
  predicted: { low_sec: number; high_sec: number } | null;
  result_seconds: number | null;
  debrief: { text?: string; answers?: Record<string, string> } | null;
  week?: number;
  day?: string;
}
export interface BRaceInput { race_name: string; race_date: string; distance_km?: number | null; elevation_gain_m?: number | null; effort: BRaceEffort }
export interface BRaceAssessment { race: BRaceInput & { options_km: number[] }; verdict: BRaceVerdict; predicted: BRace["predicted"] }

export const LEVELS: Record<BRaceLevel, { en: string; vi: string; fg: string; bg: string; line: string }> = {
  good: { en: "Good test", vi: "Bài test tốt", fg: "#1f5a3e", bg: "#e6f2ea", line: "#b9dcc6" },
  conditions: { en: "OK with conditions", vi: "Được, có điều kiện", fg: "#6b3d00", bg: "#fdf1df", line: "#f0d3a6" },
  risky: { en: "Risky", vi: "Rủi ro", fg: "#7a1a12", bg: "#fde8e6", line: "#f3c1bb" },
  not_recommended: { en: "Not recommended", vi: "Không nên", fg: "#7a1a12", bg: "#fde8e6", line: "#f3c1bb" },
};

export const REASONS: Record<string, { en: string; vi: string }> = {
  longer_than_trained: { en: "Longer than your longest recent run", vi: "Dài hơn buổi chạy dài nhất gần đây" },
  too_close: { en: "Close to your goal race", vi: "Gần race mục tiêu" },
  overlaps_taper: { en: "Recovery runs into your goal-race taper", vi: "Hồi phục lấn vào taper của race mục tiêu" },
  overlaps_peak: { en: "Lands on your peak block", vi: "Rơi vào giai đoạn peak" },
  stacked: { en: "Another race is too close", vi: "Có race khác quá gần" },
  base_phase: { en: "Big for this early in the plan", vi: "Khá lớn so với đầu plan" },
};

export const formatHms = (sec: number): string => {
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = Math.round(sec % 60);
  return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
};

/** "3:11:00" or "3:11" → seconds; null when it isn't a time. */
export const parseHms = (text: string): number | null => {
  const parts = text.trim().split(":").map((p) => Number(p));
  if (parts.length < 2 || parts.length > 3 || parts.some((p) => !Number.isFinite(p) || p < 0)) return null;
  const [h, m, s = 0] = parts;
  if (m >= 60 || s >= 60) return null;
  const total = h * 3600 + m * 60 + s;
  return total > 0 ? total : null;
};

export const suggestionLabel = (s: BRaceSuggestion, lang: Lang): string =>
  `${s.distance_km} km` + (s.effort === "training" ? (lang === "vi" ? " · chạy như buổi tập" : " · as a training run") : "");

/** The race is past and still waiting for a result or a debrief. */
export const needsDebrief = (r: BRace, today: string): boolean =>
  r.status !== "cancelled" && r.race_date <= today && !r.debrief?.text;
