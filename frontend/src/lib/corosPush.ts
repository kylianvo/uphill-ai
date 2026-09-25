import { localToday } from "./scheduleProposals";

export interface PushSummary {
  days_sent: number;
  workouts_sent: number;
  left_in_uphill: number;
  locked_days: number;
  invalid: number;
  window_end: string;
}
export interface PushStatus {
  connected: boolean;
  last_pushed_at?: string | null;
  out_of_date?: boolean;
  partial?: boolean;
  last_summary?: PushSummary | null;
}
export type PushOutcome =
  | { kind: "ok"; status: "sent" | "partial"; summary: PushSummary; last_pushed_at: string | null }
  | { kind: "error"; code: string; params: Record<string, unknown> };

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

export async function fetchPushStatus(): Promise<PushStatus | null> {
  try {
    const res = await fetch(`${apiBase()}/api/integrations/coros/push-status?client_today=${localToday()}`, {
      headers: authHeaders(),
    });
    if (!res.ok) return null;
    return (await res.json()) as PushStatus;
  } catch {
    return null;
  }
}

export async function pushToCoros(lang: string): Promise<PushOutcome> {
  try {
    const res = await fetch(`${apiBase()}/api/integrations/coros/push`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ client_today: localToday(), lang: lang === "vi" ? "vi" : "en" }),
    });
    const body = await res.json().catch(() => null);
    if (res.ok && body?.summary) {
      return { kind: "ok", status: body.status, summary: body.summary, last_pushed_at: body.last_pushed_at ?? null };
    }
    const detail = body?.detail;
    if (detail && typeof detail === "object" && typeof detail.code === "string") {
      return { kind: "error", code: detail.code, params: detail.params || {} };
    }
    return { kind: "error", code: "COROS_unavailable", params: {} };
  } catch {
    return { kind: "error", code: "COROS_unavailable", params: {} };
  }
}

const COPY: Record<string, Record<string, string>> = {
  en: {
    button: "Send to COROS",
    sending: "Sending…",
    sent_at: "Sent to COROS · {when}",
    out_of_date: "Changes not on your watch yet",
    partial: "Partly sent. Try again.",
    result: "Sent {n} workouts to COROS, through {end}.",
    left: "{n} strength session(s) stay in Uphill only.",
    locked: "Days you already completed were left as they are.",
    reconnect: "Reconnect COROS",
    COROS_not_connected: "COROS isn't connected. Reconnect it in your profile.",
    NOTHING_to_push: "Nothing to send: there are no upcoming runs in your plan.",
    PLAN_too_short: "COROS plans need at least 4 weeks, and your plan ends sooner.",
    PUSH_in_progress: "A send is already running. Try again in a moment.",
    PUSH_limit: "You've sent to COROS {limit} times today. Try again tomorrow.",
    COROS_rejected: "COROS didn't accept the plan. Nothing changed on your watch.",
    COROS_unavailable: "Couldn't reach COROS. Nothing changed. Try again shortly.",
  },
  vi: {
    button: "Gửi sang COROS",
    sending: "Đang gửi…",
    sent_at: "Đã gửi sang COROS · {when}",
    out_of_date: "Thay đổi chưa có trên đồng hồ",
    partial: "Mới gửi được một phần. Hãy thử lại.",
    result: "Đã gửi {n} buổi tập sang COROS, đến hết {end}.",
    left: "{n} buổi Strength chỉ có trong Uphill.",
    locked: "Những ngày bạn đã tập xong được giữ nguyên.",
    reconnect: "Kết nối lại COROS",
    COROS_not_connected: "Chưa kết nối COROS. Hãy kết nối lại trong hồ sơ.",
    NOTHING_to_push: "Không có gì để gửi: plan không còn buổi chạy sắp tới.",
    PLAN_too_short: "Plan trên COROS cần ít nhất 4 tuần, còn plan của bạn kết thúc sớm hơn.",
    PUSH_in_progress: "Đang có một lần gửi. Hãy thử lại sau giây lát.",
    PUSH_limit: "Hôm nay bạn đã gửi sang COROS {limit} lần. Hãy thử lại vào ngày mai.",
    COROS_rejected: "COROS không nhận plan. Đồng hồ không có thay đổi nào.",
    COROS_unavailable: "Không kết nối được COROS. Chưa có gì thay đổi. Hãy thử lại sau.",
  },
};

export function pushCopy(lang: string, key: string, params: Record<string, unknown> = {}): string {
  const table = COPY[lang] || COPY.en;
  const template = table[key] ?? COPY.en[key] ?? COPY.en.COROS_unavailable;
  return template.replace(/\{(\w+)\}/g, (_, k) => (params[k] == null ? "" : String(params[k])));
}
