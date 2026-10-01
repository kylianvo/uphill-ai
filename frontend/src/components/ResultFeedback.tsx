"use client";

import React, { useState } from "react";
import { ThumbsDown, ThumbsUp } from "@phosphor-icons/react";
import { getApiBaseUrl } from "../lib/apiUrlOverride";

// Thumbs on a Gear Finder / Nutrition Lab result. The server signs `token` into each
// fresh result, so feedback lands on that result's Langfuse trace even signed-out.
export default function ResultFeedback({ token, lang }: { token?: string | null; lang: "en" | "vi" }) {
  const [vote, setVote] = useState<1 | -1 | null>(null);
  if (!token) return null;

  const send = async (value: 1 | -1) => {
    const previous = vote;
    setVote(value);
    try {
      const res = await fetch(`${getApiBaseUrl()}/api/feedback/result`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, value }),
      });
      if (!res.ok) throw new Error(String(res.status));
    } catch {
      setVote(previous);
    }
  };

  const labels = lang === "vi" ? { q: "Kết quả này có hữu ích?", up: "Hữu ích", down: "Chưa hữu ích" } : { q: "Was this helpful?", up: "Helpful", down: "Not helpful" };
  const button = (value: 1 | -1, label: string, Icon: typeof ThumbsUp) => (
    <button
      type="button"
      aria-label={label}
      aria-pressed={vote === value}
      title={label}
      onClick={() => send(value)}
      style={{
        background: vote === value ? "rgba(25, 206, 139, 0.14)" : "transparent",
        border: "none",
        borderRadius: "6px",
        padding: "4px",
        cursor: "pointer",
        color: vote === value ? "var(--accent-primary)" : "var(--text-muted)",
        display: "inline-flex",
      }}
    >
      <Icon size={16} weight={vote === value ? "fill" : "regular"} />
    </button>
  );

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: "4px", marginTop: "16px", fontSize: "12px", color: "var(--text-muted)" }}>
      <span style={{ marginRight: "4px" }}>{labels.q}</span>
      {button(1, labels.up, ThumbsUp)}
      {button(-1, labels.down, ThumbsDown)}
    </div>
  );
}
