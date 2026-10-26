"use client";

import { useEffect, useState } from "react";

function apiBase(): string {
  if (typeof window !== "undefined") {
    return localStorage.getItem("UPHILL_API_URL_OVERRIDE") || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

function authHeader(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("uphill_session_token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const ERRORS: Record<string, [string, string]> = {
  GARMIN_not_connected: ["Garmin isn't connected. Reconnect it in your profile.", "Chưa kết nối Garmin. Hãy kết nối lại trong hồ sơ."],
  GARMIN_no_course_permission: [
    "Garmin isn't accepting courses from Uphill AI. Allow course import for Uphill AI in Garmin Connect, then send again.",
    "Garmin chưa cho Uphill AI gửi course. Hãy bật quyền nhập course cho Uphill AI trong Garmin Connect rồi gửi lại.",
  ],
  PUSH_limit: ["You've reached today's sends to Garmin. Try again tomorrow.", "Hôm nay bạn đã hết lượt gửi sang Garmin. Hãy thử lại vào ngày mai."],
  GPX_invalid: ["That file has no route Garmin can use.", "Tệp này không có tuyến đường Garmin dùng được."],
  GPX_too_large: ["That GPX is over 15 MB.", "Tệp GPX lớn hơn 15 MB."],
  GARMIN_unavailable: ["Couldn't reach Garmin. Try again shortly.", "Không kết nối được Garmin. Hãy thử lại sau."],
};

/**
 * Sends the uploaded race GPX to the athlete's Garmin device as a course. Renders
 * nothing unless Garmin is connected (and on for this account).
 */
export default function GarminCourseButton({ file, name, lang }: { file: File; name: string; lang: string }) {
  const vi = lang === "vi";
  const [connected, setConnected] = useState(false);
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => {
    fetch(`${apiBase()}/api/integrations/status`, { headers: authHeader() })
      .then((r) => (r.ok ? r.json() : null))
      .then((s) => setConnected(Boolean(s?.garmin?.enabled && s?.garmin?.connected)))
      .catch(() => setConnected(false));
  }, []);

  if (!connected) return null;

  const send = async () => {
    setSending(true);
    setMessage(null);
    const form = new FormData();
    form.append("file", file);
    form.append("name", name);
    try {
      const res = await fetch(`${apiBase()}/api/integrations/garmin/course`, {
        method: "POST",
        headers: authHeader(),
        body: form,
      });
      const body = await res.json().catch(() => null);
      if (res.ok) {
        setMessage({
          ok: true,
          text: vi
            ? `Đã gửi course ${body.distance_km} km sang Garmin. Course sẽ vào đồng hồ ở lần đồng bộ tới.`
            : `Sent a ${body.distance_km} km course to Garmin. It reaches your watch at its next sync.`,
        });
      } else {
        const pair = ERRORS[body?.detail?.code] || ERRORS.GARMIN_unavailable;
        setMessage({ ok: false, text: vi ? pair[1] : pair[0] });
      }
    } catch {
      setMessage({ ok: false, text: vi ? ERRORS.GARMIN_unavailable[1] : ERRORS.GARMIN_unavailable[0] });
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "4px", marginTop: "6px" }}>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          send();
        }}
        disabled={sending}
        className="btn btn-secondary"
        style={{ height: "30px", fontSize: "12px", borderRadius: "9999px", padding: "0 14px", opacity: sending ? 0.7 : 1 }}
      >
        {sending ? (vi ? "Đang gửi…" : "Sending…") : vi ? "Gửi course sang Garmin" : "Send course to Garmin"}
      </button>
      {message && (
        <span
          role={message.ok ? "status" : "alert"}
          style={{ fontSize: "11px", color: message.ok ? "var(--text-secondary)" : "var(--accent-alert)" }}
        >
          {message.text}
        </span>
      )}
    </div>
  );
}
