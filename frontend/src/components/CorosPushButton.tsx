"use client";

import { useEffect, useState } from "react";
import { fetchPushStatus, pushCopy, pushToCoros, type PushOutcome, type PushStatus } from "../lib/corosPush";

const MARK_SRC = `${process.env.NEXT_PUBLIC_BASE_PATH || ""}/brand/coros-mark.webp`;

/**
 * "Send to COROS" for the Scheduler header (COROS push, phase 1). Owns its own
 * status fetch; renders nothing unless the athlete has an active COROS
 * connection. `refreshKey` should change whenever the plan's workouts change,
 * so the "not on your watch yet" nudge stays current. `onReconnect` (optional)
 * opens wherever the athlete can reconnect COROS.
 */
export default function CorosPushButton({
  lang,
  refreshKey,
  onReconnect,
}: {
  lang: string;
  refreshKey: unknown;
  onReconnect?: () => void;
}) {
  const [status, setStatus] = useState<PushStatus | null>(null);
  const [sending, setSending] = useState(false);
  const [outcome, setOutcome] = useState<PushOutcome | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchPushStatus().then((s) => {
      if (!cancelled && s) setStatus(s);
    });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  if (!status?.connected) return null;

  const handleSend = async () => {
    setSending(true);
    setOutcome(null);
    const result = await pushToCoros(lang);
    setOutcome(result);
    setSending(false);
    const s = await fetchPushStatus();
    if (s) setStatus(s);
  };

  const when = status.last_pushed_at
    ? new Date(status.last_pushed_at).toLocaleString(lang === "vi" ? "vi-VN" : "en-GB", {
        weekday: "short",
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  return (
    // flex-basis 40px = the sibling header buttons' horizontal padding, so this
    // unpadded wrapper gets the same width as they do.
    <div style={{ flex: "1 1 40px", minWidth: "120px", display: "flex", flexDirection: "column", gap: "4px" }}>
      <button
        type="button"
        className="btn btn-secondary"
        onClick={handleSend}
        disabled={sending}
        style={{
          height: "36px",
          fontSize: "12px",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "6px",
          borderRadius: "9999px",
          border: "1px solid var(--border-color)",
          background: "rgba(0, 0, 0, 0.04)",
          color: "var(--text-primary)",
          cursor: sending ? "default" : "pointer",
          opacity: sending ? 0.7 : 1,
        }}
      >
        <img src={MARK_SRC} alt="COROS" width={14} height={14} style={{ objectFit: "contain" }} />
        <span>{pushCopy(lang, sending ? "sending" : "button")}</span>
      </button>
      {status.partial ? (
        <span style={{ fontSize: "11px", color: "var(--accent-alert)" }}>{pushCopy(lang, "partial")}</span>
      ) : status.out_of_date ? (
        <span style={{ fontSize: "11px", color: "#d97706" }}>{pushCopy(lang, "out_of_date")}</span>
      ) : when ? (
        <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>{pushCopy(lang, "sent_at", { when })}</span>
      ) : null}
      {outcome?.kind === "ok" && (
        <span role="status" style={{ fontSize: "11px", color: "var(--text-secondary)" }}>
          {pushCopy(lang, "result", {
            n: outcome.summary.workouts_sent,
            end: new Date(`${outcome.summary.window_end}T00:00:00`).toLocaleDateString(lang === "vi" ? "vi-VN" : "en-GB", {
              day: "numeric",
              month: "short",
            }),
          })}
          {outcome.summary.left_in_uphill > 0 && ` ${pushCopy(lang, "left", { n: outcome.summary.left_in_uphill })}`}
          {outcome.summary.locked_days > 0 && ` ${pushCopy(lang, "locked")}`}
        </span>
      )}
      {outcome?.kind === "error" && (
        <span role="alert" style={{ fontSize: "11px", color: "var(--accent-alert)" }}>
          {pushCopy(lang, outcome.code, outcome.params)}
          {outcome.code === "COROS_not_connected" && (
            <>
              {" "}
              {onReconnect ? (
                <button
                  type="button"
                  onClick={onReconnect}
                  style={{
                    background: "none",
                    border: "none",
                    padding: 0,
                    font: "inherit",
                    color: "inherit",
                    textDecoration: "underline",
                    cursor: "pointer",
                  }}
                >
                  {pushCopy(lang, "reconnect")}
                </button>
              ) : (
                <span style={{ textDecoration: "underline" }}>{pushCopy(lang, "reconnect")}</span>
              )}
            </>
          )}
        </span>
      )}
    </div>
  );
}
