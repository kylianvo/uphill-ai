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

// Preview of the ladder for onboarding, before a plan exists. Mirrors backend beginner_milestones.LADDER;
// the plan response is the source of truth once a plan is created.
export const LADDER_PREVIEW: { key: string; jog?: number; weeks: [number, number]; stage: "A" | "B" }[] = [
  { key: "first_session", weeks: [1, 1], stage: "A" },
  { key: "jog_5", jog: 5, weeks: [3, 5], stage: "A" },
  { key: "jog_10", jog: 10, weeks: [4, 6], stage: "A" },
  { key: "jog_20", jog: 20, weeks: [5, 8], stage: "A" },
  { key: "jog_30", jog: 30, weeks: [7, 10], stage: "A" },
  { key: "first_5k", weeks: [9, 12], stage: "A" },
  { key: "jog_45", jog: 45, weeks: [13, 17], stage: "B" },
  { key: "jog_60", jog: 60, weeks: [16, 21], stage: "B" },
  { key: "first_10k", weeks: [18, 24], stage: "B" },
];

export const ladderPreview = (target: MilestoneTarget) =>
  LADDER_PREVIEW.slice(0, target === "5k" ? 6 : 9);

/** Whole weeks (Monday-aligned, like the backend) a plan starting on `start` has before `eventIso`. */
export function weeksUntilEvent(startIso: string, eventIso: string): number | null {
  const s = new Date(startIso + "T00:00:00");
  const e = new Date(eventIso + "T00:00:00");
  if (isNaN(s.getTime()) || isNaN(e.getTime()) || e <= s) return null;
  const monday = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate() - ((d.getDay() + 6) % 7));
  return Math.round((monday(e).getTime() - monday(s).getTime()) / (7 * 86400000)) + 1;
}
