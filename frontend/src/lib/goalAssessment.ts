// LLM goal estimation client (docs/superpowers/specs/2026-09-26-llm-goal-estimation-design.md).
import { getApiBaseUrl } from "@/lib/apiUrlOverride";
import { RaceBenchmark } from "@/lib/paceStrategy";

export type Lang = "en" | "vi";

export interface GoalAnchor {
  id: string;
  method: string;
  minutes: number;
  source_result_id: number | string | null;
  notes: string[];
}

export interface GoalSource {
  key: string;
  label: string;
  included: boolean;
}

/** The CONTEXT block Gemini saw (services/goal_context.py `prompt`). */
export interface GoalPromptContext {
  race?: {
    name?: string | null;
    date?: string | null;
    distance_km?: number | null;
    gain_m?: number | null;
    terrain?: string[] | null;
    key_climbs?: unknown[] | null;
    profile_source?: "gpx" | "synthetic" | null;
    field?: {
      years?: number[] | null;
      winner_mins?: number | null;
      finishers?: number | null;
      percentile_mins?: Record<string, number> | null;
    } | null;
  };
  athlete?: Record<string, unknown>;
  history?: {
    date: string;
    race: string;
    discipline?: string | null;
    distance_km: number;
    gain_m?: number | null;
    time?: string | null;
    rank?: string;
  }[];
  block?: Record<string, unknown> | null;
  weeks_to_race?: number | null;
  current_target_mins?: number | null;
}

export interface GoalAssessment {
  id: number;
  plan_id: number | null;
  race_name: string | null;
  distance_km: number;
  elevation_gain_m: number;
  goals: { a: number; b: number; c: number } | null;
  confidence: "high" | "medium" | "low" | null;
  reasoning: string[];
  missing: string[];
  anchors: GoalAnchor[];
  sources: GoalSource[];
  context?: GoalPromptContext | null;
  engine: "gemini" | "gemini_retry" | "rules" | "none";
  trigger: "pre_plan" | "manual" | "weekly";
  plan_week: number | null;
  lang?: Lang | null;
  created_at: string;
  benchmarks?: RaceBenchmark[] | null;
  reused?: boolean;
  /** Goals before the plan-support adjustment; `goals` is already pushed later by what the plan cannot deliver. */
  goals_unadjusted?: { a: number; b: number; c: number } | null;
  plan_support?: PlanSupport | null;
}

/** What the plan can deliver of the training improvement the goal times assume (backend plan_adequacy). */
export interface PlanSupport {
  a_supported: boolean;
  shortfall_pct: number;
  improvement_assumed_pct: number;
  improvement_supported_pct: number;
  weeks_assumed: number;
  weeks_supported: number;
  problem_weeks: Record<string, string[]>;
  reasons: string[];
}

export type GoalState = "on_track" | "ahead" | "behind" | "not_assessed" | "no_target";

export type FeasibilityLever =
  | "more_days"
  | "double_sessions"
  | "more_weeks"
  | "shorter_race"
  | "finish_only"
  | "steeper_venue"
  | "mountain_access"
  | "fewer_mountain_minimum";

/** Whether the athlete's week, runway and training venue can hold the goal (services/goal_feasibility.py). */
export interface Feasibility {
  verdict: "supported" | "stretch" | "unsupported";
  capacity_h: number;
  needed_h: number;
  weeks_needed: number | null;
  levers: FeasibilityLever[];
  confidence: "measured" | "estimated";
}

/** Is training on the path to B and A, from measured aerobic speed (services/aerobic_speed.py). */
export interface GoalPath {
  b: "ahead" | "on" | "behind";
  a: "ahead" | "on" | "behind";
  measured_pct: number;
  expected_pct: number;
  weeks: number;
  confidence: "low" | "medium" | "high";
}

export interface PlanGoal {
  assessment: GoalAssessment | null;
  status: { state: GoalState; suggested_mins: number | null; a_supported?: boolean };
  target_time_hours: number | null;
  feasibility?: Feasibility | null;
  path?: GoalPath | null;
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = typeof window !== "undefined" ? localStorage.getItem("uphill_session_token") : null;
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, { ...init, headers: authHeaders() });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(typeof detail?.detail === "string" ? detail.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export function assessGoal(body: Record<string, unknown>, athleteId?: number | null): Promise<GoalAssessment> {
  const path = athleteId ? `/api/coaching/athletes/${athleteId}/goal/assess` : "/api/goal/assess";
  return request(path, { method: "POST", body: JSON.stringify(body) });
}

function planPath(planId: number, athleteId?: number | null): string {
  return athleteId ? `/api/coaching/athletes/${athleteId}/plans/${planId}/goal` : `/api/plans/${planId}/goal`;
}

export function getPlanGoal(planId: number, lang: Lang, athleteId?: number | null): Promise<PlanGoal> {
  return request(`${planPath(planId, athleteId)}?lang=${lang}`);
}

export function reassessPlanGoal(planId: number, lang: Lang, athleteId?: number | null): Promise<PlanGoal> {
  return request(`${planPath(planId, athleteId)}/reassess`, { method: "POST", body: JSON.stringify({ lang }) });
}

export function applyPlanGoal(planId: number, targetMins: number, athleteId?: number | null): Promise<PlanGoal> {
  return request(`${planPath(planId, athleteId)}/apply`, {
    method: "POST",
    body: JSON.stringify({ target_mins: targetMins }),
  });
}

export function formatGoalTime(mins: number): string {
  const total = Math.round(mins);
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}

/** Pill label + dot colour for the plan header. */
export function goalPillLabel(goal: PlanGoal, lang: Lang): { text: string; dot: string } {
  const t = (en: string, vi: string) => (lang === "en" ? en : vi);
  const target = goal.target_time_hours ? formatGoalTime(goal.target_time_hours * 60) : null;
  const head = target ? `${t("Goal", "Mục tiêu")} ${target}` : t("Goal", "Mục tiêu");
  const suggested = goal.status.suggested_mins != null ? formatGoalTime(goal.status.suggested_mins) : "";
  switch (goal.status.state) {
    case "on_track":
      return { text: `${head} · ${t("On track", "Đúng hướng")}`, dot: "#10b981" };
    case "ahead":
      return { text: `${head} · ${t("Ahead, consider", "Nhanh hơn, cân nhắc")} ${suggested}`, dot: "#3b82f6" };
    case "behind":
      return { text: `${head} · ${t("Behind, consider", "Chậm hơn, cân nhắc")} ${suggested}`, dot: "#f59e0b" };
    case "no_target":
      return { text: `${head} · ${t("Suggested", "Gợi ý")} ${suggested}`, dot: "#3b82f6" };
    default:
      return { text: `${head} · ${t("Not assessed", "Chưa đánh giá")}`, dot: "#9ca3af" };
  }
}

const MISSING_HINTS: Record<string, [string, string]> = {
  recent_trail_result: ["Link a past trail race result", "Liên kết kết quả Trail race trước"],
  race_history: ["Link your UTMB or VBM profile", "Liên kết hồ sơ UTMB hoặc VBM"],
  utmb_index: ["Link your UTMB profile for your UTMB index", "Liên kết hồ sơ UTMB để có UTMB index"],
  watch: ["Connect your watch for recent training", "Kết nối đồng hồ để có dữ liệu tập gần đây"],
  vo2max: ["Sync VO2max from your watch", "Đồng bộ VO2max từ đồng hồ"],
};

export function missingHints(keys: string[], lang: Lang): string[] {
  return keys.filter((k) => MISSING_HINTS[k]).map((k) => MISSING_HINTS[k][lang === "en" ? 0 : 1]);
}

export function confidenceLabel(confidence: GoalAssessment["confidence"], lang: Lang): string {
  const t = (en: string, vi: string) => (lang === "en" ? en : vi);
  if (confidence === "high") return t("High confidence", "Độ tin cậy cao");
  if (confidence === "medium") return t("Medium confidence", "Độ tin cậy vừa");
  return t("Low confidence", "Độ tin cậy thấp");
}

/** A short notice when the plan cannot fully back the A goal; null when it can (or without data). */
export function planSupportNotice(assessment: GoalAssessment | null | undefined, lang: Lang): string | null {
  const support = assessment?.plan_support;
  const goals = assessment?.goals;
  const before = assessment?.goals_unadjusted;
  if (!support || support.a_supported || !goals || !before) return null;
  const supported = support.improvement_supported_pct.toFixed(1);
  const assumed = support.improvement_assumed_pct.toFixed(1);
  const later = support.shortfall_pct.toFixed(1);
  const from = formatGoalTime(before.a);
  const to = formatGoalTime(goals.a);
  return lang === "en"
    ? `The plan can't fully back the A goal yet: it delivers ${supported}% of the ${assumed}% improvement the goals assume, so the goal times moved ${later}% later (A ${from} → ${to}). Weeks that follow the plan rules bring it back.`
    : `Plan chưa đỡ hết mục tiêu A: chỉ mang lại ${supported}% trong ${assumed}% cải thiện mà mục tiêu giả định, nên thời gian lùi ${later}% (A ${from} → ${to}). Các tuần đúng nguyên tắc sẽ kéo lại.`;
}

const LEVER_TEXT: Record<FeasibilityLever, [string, string]> = {
  more_days: ["More training days would close the gap.", "Thêm ngày tập sẽ thu hẹp khoảng cách."],
  double_sessions: ["Double sessions would help.", "Có thể thêm buổi tập đôi."],
  more_weeks: ["", ""], // needs the week count; built in feasibilityNotice
  shorter_race: ["A shorter race would fit better.", "Race ngắn hơn sẽ hợp hơn."],
  finish_only: ["Treat it as a finish-only goal.", "Hãy coi đây là mục tiêu về đích."],
  steeper_venue: [
    "Train on a steeper mountain to rehearse the climbing.",
    "Tập ở núi dốc hơn để luyện leo.",
  ],
  mountain_access: [
    "Add mountain trips, or stair and treadmill climbing.",
    "Thêm buổi lên núi, hoặc leo cầu thang và treadmill.",
  ],
  fewer_mountain_minimum: [
    "Your mountain Long Run minimum does not fit your week.",
    "Mức tối thiểu của Long Run trên núi chưa vừa với tuần của bạn.",
  ],
};

const MAX_LEVERS_SHOWN = 2;

/** One short notice when the week cannot (or only just can) hold the goal; null when it can. */
export function feasibilityNotice(f: Feasibility | null | undefined, lang: Lang): string | null {
  if (!f || f.verdict === "supported") return null;
  const en = lang === "en";
  const cap = f.capacity_h.toFixed(1);
  const need = f.needed_h.toFixed(1);
  const head =
    f.verdict === "unsupported"
      ? en
        ? `Your week can hold about ${cap}h; this goal needs about ${need}h.`
        : `Tuần của bạn chứa được khoảng ${cap}h; mục tiêu này cần khoảng ${need}h.`
      : en
        ? `Possible but tight: your week holds about ${cap}h, the goal needs about ${need}h.`
        : `Làm được nhưng sát: tuần chứa khoảng ${cap}h, mục tiêu cần khoảng ${need}h.`;
  const levers = f.levers
    .map((l) => {
      if (l === "more_weeks") {
        if (!f.weeks_needed) return en ? "It needs more weeks before the race." : "Cần thêm tuần trước race.";
        return en
          ? `Reaching the peak week takes about ${f.weeks_needed} weeks.`
          : `Cần khoảng ${f.weeks_needed} tuần để đạt peak week.`;
      }
      return LEVER_TEXT[l]?.[en ? 0 : 1] ?? "";
    })
    .filter(Boolean)
    .slice(0, MAX_LEVERS_SHOWN);
  const tail = f.confidence === "estimated" ? (en ? "(pace estimated)" : "(pace ước tính)") : "";
  return [head, ...levers, tail].filter(Boolean).join(" ");
}

const PATH_WORD: Record<GoalPath["b"], [string, string]> = {
  ahead: ["ahead", "vượt lộ trình"],
  on: ["on track", "đúng lộ trình"],
  behind: ["behind", "chậm lộ trình"],
};

/** One line on whether aerobic speed is on the B and A paths; null until there is data. */
export function pathNotice(path: GoalPath | null | undefined, lang: Lang): string | null {
  if (!path) return null;
  const i = lang === "en" ? 0 : 1;
  const pct = Math.abs(path.measured_pct).toFixed(1);
  const speed =
    lang === "en"
      ? `Aerobic speed is ${pct}% ${path.measured_pct >= 0 ? "faster" : "slower"} than at the start.`
      : `Tốc độ aerobic ${path.measured_pct >= 0 ? "nhanh" : "chậm"} hơn ${pct}% so với lúc bắt đầu.`;
  const early = path.confidence === "low" ? (lang === "en" ? " (early read)" : " (mới đo sơ bộ)") : "";
  return `B ${PATH_WORD[path.b][i]} · A ${PATH_WORD[path.a][i]}. ${speed}${early}`;
}
