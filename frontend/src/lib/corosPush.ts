import { localToday } from "./scheduleProposals";

export interface PushSummary {
  mode?: "plan" | "standalone";
  days_sent: number;
  workouts_sent: number;
  left_in_uphill: number;
  locked_days: number;
  invalid: number;
  stale?: number;
  window_end: string;
  plan_start?: string | null;
}
export interface PushStatus {
  connected: boolean;
  last_pushed_at?: string | null;
  out_of_date?: boolean;
  partial?: boolean;
  last_summary?: PushSummary | null;
}
/** The watch a push goes to; both backends share one response shape. */
export type PushProvider = "coros" | "garmin";

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

export async function fetchPushStatus(provider: PushProvider = "coros"): Promise<PushStatus | null> {
  try {
    const res = await fetch(`${apiBase()}/api/integrations/${provider}/push-status?client_today=${localToday()}`, {
      headers: authHeaders(),
    });
    if (!res.ok) return null;
    return (await res.json()) as PushStatus;
  } catch {
    return null;
  }
}

export async function pushToCoros(lang: string, provider: PushProvider = "coros"): Promise<PushOutcome> {
  const unavailable = `${provider.toUpperCase()}_unavailable`;
  try {
    const res = await fetch(`${apiBase()}/api/integrations/${provider}/push`, {
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
    return { kind: "error", code: unavailable, params: {} };
  } catch {
    return { kind: "error", code: unavailable, params: {} };
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
    plan_start: "Your COROS plan starts on {date}.",
    stale: "{n} workouts that changed in Uphill are still on COROS on their old day. Delete them in the COROS app.",
    RACE_too_far: "COROS plans cover up to 16 weeks. Send to COROS opens on {date}.",
    RACE_too_close: "COROS plans must be at least 4 weeks long, and your race is in {weeks} weeks.",
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
    plan_start: "Plan trên COROS bắt đầu từ {date}.",
    stale: "{n} buổi tập đã đổi trong Uphill vẫn còn trên COROS ở ngày cũ. Hãy xoá chúng trong app COROS.",
    RACE_too_far: "Plan trên COROS dài tối đa 16 tuần. Bạn có thể gửi sang COROS từ {date}.",
    RACE_too_close: "Plan trên COROS phải dài ít nhất 4 tuần, còn race của bạn chỉ còn {weeks} tuần.",
    PUSH_in_progress: "Đang có một lần gửi. Hãy thử lại sau giây lát.",
    PUSH_limit: "Hôm nay bạn đã gửi sang COROS {limit} lần. Hãy thử lại vào ngày mai.",
    COROS_rejected: "COROS không nhận plan. Đồng hồ không có thay đổi nào.",
    COROS_unavailable: "Không kết nối được COROS. Chưa có gì thay đổi. Hãy thử lại sau.",
  },
};

// Garmin wording where it differs: the brand, and Garmin's own refusals.
const GARMIN_COPY: Record<string, Record<string, string>> = {
  en: {
    button: "Send to Garmin",
    sent_at: "Sent to Garmin · {when}",
    result: "Sent {n} workouts to Garmin, through {end}.",
    reconnect: "Reconnect Garmin",
    GARMIN_not_connected: "Garmin isn't connected. Reconnect it in your profile.",
    GARMIN_no_workout_permission:
      "Garmin isn't accepting workouts from Uphill AI. Allow workout import for Uphill AI in Garmin Connect, then send again.",
    PUSH_limit: "You've sent to Garmin {limit} times today. Try again tomorrow.",
    GARMIN_unavailable: "Couldn't reach Garmin. Nothing changed. Try again shortly.",
  },
  vi: {
    button: "Gửi sang Garmin",
    sent_at: "Đã gửi sang Garmin · {when}",
    result: "Đã gửi {n} buổi tập sang Garmin, đến hết {end}.",
    reconnect: "Kết nối lại Garmin",
    GARMIN_not_connected: "Chưa kết nối Garmin. Hãy kết nối lại trong hồ sơ.",
    GARMIN_no_workout_permission:
      "Garmin chưa cho Uphill AI gửi buổi tập. Hãy bật quyền nhập buổi tập cho Uphill AI trong Garmin Connect rồi gửi lại.",
    PUSH_limit: "Hôm nay bạn đã gửi sang Garmin {limit} lần. Hãy thử lại vào ngày mai.",
    GARMIN_unavailable: "Không kết nối được Garmin. Chưa có gì thay đổi. Hãy thử lại sau.",
  },
};

export function pushCopy(
  lang: string,
  key: string,
  params: Record<string, unknown> = {},
  provider: PushProvider = "coros"
): string {
  const table = { ...(COPY[lang] || COPY.en), ...(provider === "garmin" ? GARMIN_COPY[lang] || GARMIN_COPY.en : {}) };
  const fallback = provider === "garmin" ? GARMIN_COPY.en.GARMIN_unavailable : COPY.en.COROS_unavailable;
  const template = table[key] ?? COPY.en[key] ?? fallback;
  return template.replace(/\{(\w+)\}/g, (_, k) => (params[k] == null ? "" : String(params[k])));
}
