// First 5K / First 10K milestones for start_running plans. The server (services/beginner_milestones.py)
// owns the ladder and achievement; this file only labels and formats what it sends.

export type Lang = "en" | "vi";
export type MilestoneTarget = "5k" | "10k";

export interface MilestoneItem {
  key: string;
  kind: "sessions" | "jog_min" | "distance_km";
  threshold: number;
  stage: "A" | "B";
  typical_weeks: [number, number];
  achieved_at: string | null;
  source: "auto" | "manual" | "baseline" | "revoked" | null;
}

export interface PlanMilestones {
  target: MilestoneTarget;
  has_event: boolean;
  items: MilestoneItem[];
  next_key: string | null;
}

const LABELS: Record<string, [string, string]> = {
  first_session: ["First run/walk session", "Buổi chạy/đi bộ đầu tiên"],
  jog_5: ["5 min unbroken jog", "Chạy liên tục 5 phút"],
  jog_10: ["10 min unbroken jog", "Chạy liên tục 10 phút"],
  jog_20: ["20 min unbroken jog", "Chạy liên tục 20 phút"],
  jog_30: ["30 min non-stop", "Chạy không nghỉ 30 phút"],
  first_5k: ["First 5 km", "5 km đầu tiên"],
  jog_45: ["45 min non-stop", "Chạy không nghỉ 45 phút"],
  jog_60: ["60 min non-stop", "Chạy không nghỉ 60 phút"],
  first_10k: ["First 10 km", "10 km đầu tiên"],
};

export const MILESTONE_KEYS = Object.keys(LABELS);

export const milestoneLabel = (key: string, lang: Lang) => LABELS[key]?.[lang === "vi" ? 1 : 0] ?? key;

// Mirrors backend beginner_milestones.minimum_weeks: no reduction without a baseline.
const BASE_MIN = { "5k": 9, "10k": 17 } as const;
const JOG_STEPS: [number, number][] = [[5, 3], [10, 4], [20, 5], [30, 7]]; // [minutes, first typical week]
const AFTER_JOG_30: Record<MilestoneTarget, number> = { "5k": 9, "10k": 9 }; // first_5k opens at week 9

export function minimumWeeks(target: MilestoneTarget, currentJogMin: number | null): number {
  const base = BASE_MIN[target];
  if (!currentJogMin) return base;
  const done = JOG_STEPS.filter(([m]) => m <= currentJogMin);
  if (!done.length) return base;
  const nextJog = JOG_STEPS.find(([m]) => m > currentJogMin);
  const firstOpen = nextJog ? nextJog[1] : AFTER_JOG_30[target];
  return Math.max(3, base - (firstOpen - 1));
}

export function headerText(ms: PlanMilestones, lang: Lang, weeksToEvent: number | null): string {
  const reached = ms.items.filter((i) => i.achieved_at).length;
  const goal = lang === "vi" ? `${ms.target.toUpperCase()} đầu tiên` : `First ${ms.target.toUpperCase()}`;
  const count = lang === "vi" ? `${reached}/${ms.items.length} cột mốc` : `${reached} of ${ms.items.length} milestones`;
  const event = ms.has_event && weeksToEvent !== null ? (lang === "vi" ? ` · còn ${weeksToEvent} tuần tới sự kiện` : ` · ${weeksToEvent} weeks to event`) : "";
  return `${goal} · ${count}${event}`;
}

export const typicalWeeksText = (i: MilestoneItem, lang: Lang) =>
  lang === "vi" ? `thường quanh tuần ${i.typical_weeks[0]}–${i.typical_weeks[1]}` : `usually around week ${i.typical_weeks[0]}–${i.typical_weeks[1]}`;
