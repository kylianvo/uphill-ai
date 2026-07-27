"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect } from "react";
import { useAppContext } from "../contexts/AppContext";
import { useCoachDashboard } from "../hooks/useCoachDashboard";

/**
 * Global surface for coaching invites: any logged-in user can be invited
 * as an athlete, whether or not they themselves are a coach (is_coach
 * gates the Coach tab, not eligibility to be coached). Rendered once,
 * outside the responsive tab layouts, so it isn't tied to any one tab.
 */
export default function PendingInviteBanner() {
  const { user, lang, activeTab } = useAppContext();
  const { pendingInvites, fetchMyInvites, acceptInvite, declineInvite } = useCoachDashboard();

  useEffect(() => {
    if (user) fetchMyInvites();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  // Coaches already see this list inside the Coach tab — avoid showing it twice there.
  if (!user || pendingInvites.length === 0 || activeTab === "coach") return null;

  return (
    <div
      style={{
        position: "fixed",
        top: "70px",
        right: "16px",
        zIndex: 500,
        width: "min(340px, calc(100vw - 32px))",
        display: "flex",
        flexDirection: "column",
        gap: "8px",
      }}
    >
      {pendingInvites.map((inv: any) => (
        <div
          key={inv.id}
          className="card"
          style={{
            padding: "14px 16px",
            display: "flex",
            flexDirection: "column",
            gap: "10px",
            boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
          }}
        >
          <span style={{ fontSize: "13px" }}>
            {lang === "en"
              ? `${inv.coach_name || inv.coach_email} invited you to be coached`
              : `${inv.coach_name || inv.coach_email} đã mời bạn tham gia huấn luyện`}
          </span>
          <div style={{ display: "flex", gap: "8px" }}>
            <button
              className="btn btn-primary"
              style={{ padding: "6px 14px", fontSize: "12px" }}
              onClick={() => acceptInvite(inv.id)}
            >
              {lang === "en" ? "Accept" : "Chấp nhận"}
            </button>
            <button
              style={{
                padding: "6px 14px",
                fontSize: "12px",
                borderRadius: "8px",
                border: "1px solid var(--border-color)",
                background: "transparent",
                cursor: "pointer",
              }}
              onClick={() => declineInvite(inv.id)}
            >
              {lang === "en" ? "Decline" : "Từ chối"}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
