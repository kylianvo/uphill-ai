"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect } from "react";
import { Users, PaperPlaneTilt, ArrowRight, X } from "@phosphor-icons/react";
import { useAppContext } from "../contexts/AppContext";
import { useCoachDashboard } from "../hooks/useCoachDashboard";

export default function CoachDashboardView({ isMobile }: { isMobile: boolean }) {
  const { lang } = useAppContext();
  const {
    roster,
    pendingInvites,
    inviteEmail,
    setInviteEmail,
    rosterLoading,
    inviteLoading,
    inviteErrorMsg,
    fetchRoster,
    fetchMyInvites,
    sendInvite,
    acceptInvite,
    declineInvite,
    removeFromRoster,
    enterAthleteView,
  } = useCoachDashboard();

  useEffect(() => {
    fetchRoster();
    fetchMyInvites();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const activeAthletes = roster.filter((r: any) => r.status === "active");
  const invitedAthletes = roster.filter((r: any) => r.status === "invited");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px", padding: isMobile ? "16px" : "0" }}>
      {/* Pending invites this user (as an athlete) hasn't responded to yet */}
      {pendingInvites.length > 0 && (
        <div className="card" style={{ padding: "20px" }}>
          <h3 style={{ margin: "0 0 12px 0", fontSize: "15px", fontWeight: "800" }}>
            {lang === "en" ? "Coaching invites" : "Lời mời huấn luyện"}
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {pendingInvites.map((inv: any) => (
              <div
                key={inv.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "10px 14px",
                  borderRadius: "10px",
                  background: "rgba(16,185,129,0.06)",
                  border: "1px solid var(--border-color)",
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
        </div>
      )}

      {/* Invite form */}
      <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
          <PaperPlaneTilt size={20} weight="duotone" />
          <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "800" }}>
            {lang === "en" ? "Invite an athlete" : "Mời một vận động viên"}
          </h3>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <input
            type="email"
            className="chat-input"
            style={{ flex: 1, borderRadius: "8px", padding: "10px 14px", fontSize: "13px" }}
            placeholder={lang === "en" ? "athlete@email.com" : "vdv@email.com"}
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
          />
          <button
            className="btn btn-primary"
            disabled={!inviteEmail || inviteLoading}
            onClick={() => sendInvite(inviteEmail)}
            style={{ padding: "10px 18px", fontSize: "13px" }}
          >
            {inviteLoading
              ? lang === "en"
                ? "Sending…"
                : "Đang gửi…"
              : lang === "en"
                ? "Send Invite"
                : "Gửi lời mời"}
          </button>
        </div>
        {inviteErrorMsg && (
          <p style={{ color: "var(--accent-alert)", fontSize: "12px", marginTop: "8px" }}>{inviteErrorMsg}</p>
        )}
        <p style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "8px" }}>
          {lang === "en"
            ? "The athlete must already have an Uphill AI account."
            : "Vận động viên phải đã có tài khoản Uphill AI."}
        </p>
      </div>

      {/* Roster */}
      <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
          <Users size={20} weight="duotone" />
          <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "800" }}>
            {lang === "en" ? "Your athletes" : "Vận động viên của bạn"}
          </h3>
        </div>

        {rosterLoading && roster.length === 0 ? (
          <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            {lang === "en" ? "Loading…" : "Đang tải…"}
          </p>
        ) : roster.length === 0 ? (
          <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            {lang === "en"
              ? "No athletes yet — send an invite above to get started."
              : "Chưa có vận động viên nào — gửi lời mời ở trên để bắt đầu."}
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {[...activeAthletes, ...invitedAthletes].map((row: any) => (
              <div
                key={row.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "12px 14px",
                  borderRadius: "10px",
                  border: "1px solid var(--border-color)",
                  background: "rgba(255,255,255,0.4)",
                }}
              >
                <div>
                  <div style={{ fontSize: "13.5px", fontWeight: "700" }}>{row.athlete_name || row.athlete_email}</div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    {row.status === "active"
                      ? lang === "en"
                        ? "Active"
                        : "Đang huấn luyện"
                      : lang === "en"
                        ? "Invite pending"
                        : "Đang chờ chấp nhận"}
                  </div>
                </div>
                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  {row.status === "active" && (
                    <button
                      onClick={() => enterAthleteView(row.athlete_id, row.athlete_name || row.athlete_email)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "5px",
                        padding: "6px 12px",
                        fontSize: "12px",
                        fontWeight: "700",
                        borderRadius: "8px",
                        border: "none",
                        background: "var(--accent-primary)",
                        color: "#fff",
                        cursor: "pointer",
                      }}
                    >
                      {lang === "en" ? "View plan" : "Xem kế hoạch"} <ArrowRight size={12} weight="bold" />
                    </button>
                  )}
                  <button
                    onClick={() => removeFromRoster(row.id)}
                    title={lang === "en" ? "Remove" : "Xoá"}
                    style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: "4px" }}
                  >
                    <X size={16} weight="bold" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
