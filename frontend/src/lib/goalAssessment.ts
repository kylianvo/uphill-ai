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
}

export type GoalState = "on_track" | "ahead" | "behind" | "not_assessed" | "no_target";

export interface PlanGoal {
  assessment: GoalAssessment | null;
  status: { state: GoalState; suggested_mins: number | null };
  target_time_hours: number | null;
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
