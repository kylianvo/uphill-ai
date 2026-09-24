import { translations } from "../app/translations";
import { dayLabel } from "../utils/dayLabels";

export type ProposalStatus = "generating" | "proposed" | "applied" | "discarded" | "stale" | "failed";
export interface ScheduleWarning {
  code: string;
  params: Record<string, unknown>;
}
export interface ProposalState {
  status: ProposalStatus;
  stale_reason?: string | null;
  result?: { warnings?: ScheduleWarning[] } | null;
}
export type ApplyOutcome =
  | { kind: "applied"; state: ProposalState; workouts: unknown[] }
  | { kind: "stale"; state: ProposalState }
  | { kind: "failed" };

export function localToday(now: Date = new Date()): string {
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${m}-${d}`;
}

export function tr(lang: string, key: string): string {
  const table = translations as unknown as Record<string, Record<string, string>>;
  return table[lang]?.[key] || table.en[key] || key;
}

function fill(template: string, params: Record<string, unknown>, lang: string): string {
  return template.replace(/\{(\w+)\}/g, (_, k) => {
    const v = params[k];
    if (k === "day" && typeof v === "string") return dayLabel(v, lang);
    return v == null ? "" : String(v);
  });
}

export function describeGuard(lang: string, code: string, params: Record<string, unknown> = {}): string {
  const key = `guard_${code}`;
  const text = tr(lang, key);
  return fill(text === key ? tr(lang, "guard_unknown") : text, params, lang);
}

export function describeWarning(lang: string, w: ScheduleWarning): string {
  const params = w.params || {};
  if (w.code === "W1_hard_stacking") {
    return fill(tr(lang, params.kind === "before_long_run" ? "warn_W1_before_long_run" : "warn_W1_same_day"), params, lang);
  }
  if (w.code === "W2_volume_shift") {
    return fill(tr(lang, "warn_W2_volume_shift"), { ...params, before: params.before_minutes, after: params.after_minutes }, lang);
  }
  if (w.code === "W3_pending_draft") return fill(tr(lang, "warn_W3_pending_draft"), params, lang);
  return w.code;
}

function apiBase(): string {
  if (typeof window !== "undefined") {
    return localStorage.getItem("UPHILL_API_URL_OVERRIDE") || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

function authHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("uphill_session_token") : null;
  return { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) };
}

export async function applyProposal(id: number): Promise<ApplyOutcome> {
  try {
    const res = await fetch(`${apiBase()}/api/coach/chat/proposals/${id}/apply`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ client_today: localToday() }),
    });
    const body = await res.json().catch(() => null);
    if (res.ok && body?.status === "applied") {
      return { kind: "applied", state: { status: "applied", result: body.result }, workouts: body.workouts || [] };
    }
    if (res.status === 409 && body?.status) {
      return { kind: "stale", state: { status: body.status, stale_reason: body.stale_reason } };
    }
    return { kind: "failed" };
  } catch {
    return { kind: "failed" };
  }
}

export async function discardProposal(id: number): Promise<ProposalStatus | null> {
  try {
    const res = await fetch(`${apiBase()}/api/coach/chat/proposals/${id}/discard`, {
      method: "POST",
      headers: authHeaders(),
    });
    if (!res.ok) return null;
    const body = await res.json();
    return body?.status ?? null;
  } catch {
    return null;
  }
}

export interface RebuildTotals {
  min: number;
  km: number;
  vert: number;
}
export interface RebuildDay {
  day: string;
  kept: Record<string, unknown>[];
  before: Record<string, unknown>[];
  after: Record<string, unknown>[];
}
export interface RebuildDiff {
  week: number;
  from_day: string;
  days: RebuildDay[];
  totals: { before: RebuildTotals; after: RebuildTotals };
}
export interface ProposalDetail {
  id: number;
  kind: "schedule" | "rebuild";
  status: ProposalStatus;
  diff: RebuildDiff | Record<string, never>;
  warnings: ScheduleWarning[];
  stale_reason?: string | null;
}

export async function fetchProposal(id: number): Promise<ProposalDetail | null> {
  try {
    const res = await fetch(`${apiBase()}/api/coach/chat/proposals/${id}`, { headers: authHeaders() });
    if (!res.ok) return null;
    return (await res.json()) as ProposalDetail;
  } catch {
    return null;
  }
}
