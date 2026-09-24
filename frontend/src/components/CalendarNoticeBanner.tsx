import React from "react";
import type { CalendarNotice } from "../hooks/usePlanner";

export default function CalendarNoticeBanner({ notice, onDismiss }: { notice: CalendarNotice | null; onDismiss: () => void }) {
  React.useEffect(() => {
    if (!notice) return;
    const t = setTimeout(onDismiss, 7000);
    return () => clearTimeout(t);
  }, [notice, onDismiss]);
  if (!notice) return null;
  const isError = notice.kind === "error";
  return (
    <div
      role={isError ? "alert" : "status"}
      onClick={onDismiss}
      style={{
        margin: "8px 0", padding: "10px 12px", borderRadius: "10px", fontSize: "13px", cursor: "pointer",
        background: isError ? "rgba(239, 68, 68, 0.1)" : "rgba(245, 158, 11, 0.12)",
        color: isError ? "#b91c1c" : "#92400e",
        border: `1px solid ${isError ? "rgba(239, 68, 68, 0.25)" : "rgba(245, 158, 11, 0.3)"}`,
      }}
    >
      {notice.text}
    </div>
  );
}
