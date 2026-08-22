"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useState } from "react";
import { Users, PaperPlaneTilt, ArrowRight, X, ChartBar, Warning, ClipboardText } from "@phosphor-icons/react";
import { useAppContext } from "../contexts/AppContext";
import { useCoachDashboard } from "../hooks/useCoachDashboard";
import { useCoachOverview } from "../hooks/useCoachOverview";
import WorkoutTypeMixChart from "../components/WorkoutTypeMixChart";

export default function CoachDashboardView({ isMobile }: { isMobile: boolean }) {
  const { lang } = useAppContext();
  const [activeSection, setActiveSection] = useState<"overview" | "roster">("overview");
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
  const { overview, overviewLoading, overviewError, fetchOverview } = useCoachOverview();

  useEffect(() => {
    fetchRoster();
    fetchMyInvites();
    fetchOverview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const activeAthletes = roster.filter((r: any) => r.status === "active");
  const invitedAthletes = roster.filter((r: any) => r.status === "invited");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px", padding: isMobile ? "16px" : "0" }}>
      <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid var(--border-color)" }}>
        {(["overview", "roster"] as const).map((section) => (
          <button
            key={section}
            onClick={() => setActiveSection(section)}
            style={{
              padding: "10px 16px",
              fontSize: "13px",
              fontWeight: 700,
              border: "none",
              borderBottom: activeSection === section ? "2px solid var(--accent-primary)" : "2px solid transparent",
              background: "transparent",
              color: activeSection === section ? "var(--text-primary)" : "var(--text-muted)",
              cursor: "pointer",
            }}
          >
            {section === "overview"
              ? lang === "en" ? "Overview" : "Tổng quan"
              : lang === "en" ? "Roster" : "Danh sách"}
          </button>
        ))}
      </div>

      {activeSection === "roster" && (
        <>
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
        </>
      )}

      {activeSection === "overview" && (
        <>
          {overviewLoading && !overview && (
            <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
              {lang === "en" ? "Loading…" : "Đang tải…"}
            </p>
          )}
          {overviewError && (
            <p style={{ color: "var(--accent-alert)", fontSize: "13px" }}>{overviewError}</p>
          )}
          {overview && overview.athletes.length === 0 && (
            <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
              <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                {lang === "en"
                  ? "No athletes yet — invite one from the Roster tab to get started."
                  : "Chưa có vận động viên nào — mời một người từ tab Danh sách để bắt đầu."}
              </p>
            </div>
          )}

          {overview && overview.phase_alerts.length > 0 && (
            <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
                <Warning size={20} weight="duotone" />
                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "800" }}>
                  {lang === "en" ? "Phase alerts" : "Cảnh báo giai đoạn"}
                </h3>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {overview.phase_alerts.map((alert, i) => (
                  <div
                    key={`${alert.athlete_id}-${alert.phase}-${i}`}
                    onClick={() => enterAthleteView(alert.athlete_id, alert.athlete_name)}
                    style={{
                      padding: "10px 14px",
                      borderRadius: "10px",
                      background: "rgba(245,158,11,0.08)",
                      border: "1px solid var(--border-color)",
                      fontSize: "13px",
                      cursor: "pointer",
                    }}
                  >
                    {lang === "en"
                      ? `${alert.athlete_name} enters ${alert.phase} ${alert.starts === "this_week" ? "this week" : "next week"}`
                      : `${alert.athlete_name} bước vào giai đoạn ${alert.phase} ${alert.starts === "this_week" ? "tuần này" : "tuần tới"}`}
                  </div>
                ))}
              </div>
            </div>
          )}

          {overview && (
            <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
                <ClipboardText size={20} weight="duotone" />
                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "800" }}>
                  {lang === "en" ? "Action items" : "Việc cần làm"}
                </h3>
              </div>
              <div style={{ display: "flex", gap: "24px", marginBottom: overview.action_items.draft_plans.length || overview.action_items.pending_workout_approvals.length ? "12px" : 0 }}>
                <div>
                  <div style={{ fontSize: "22px", fontWeight: "800" }}>{overview.action_items.draft_plans.length}</div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    {lang === "en" ? "draft plans to finish" : "kế hoạch nháp cần hoàn thiện"}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "22px", fontWeight: "800" }}>{overview.action_items.pending_workout_approvals.length}</div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    {lang === "en" ? "workouts pending approval" : "buổi tập chờ duyệt"}
                  </div>
                </div>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {overview.action_items.draft_plans.map((item) => (
                  <div
                    key={`draft-${item.plan_id}`}
                    onClick={() => enterAthleteView(item.athlete_id, item.athlete_name)}
                    style={{ fontSize: "12.5px", cursor: "pointer", color: "var(--text-secondary)" }}
                  >
                    {lang === "en"
                      ? `${item.athlete_name}: "${item.race_name}" is still a draft`
                      : `${item.athlete_name}: "${item.race_name}" vẫn đang là bản nháp`}
                  </div>
                ))}
                {overview.action_items.pending_workout_approvals.map((item) => (
                  <div
                    key={`pending-${item.workout_id}`}
                    onClick={() => enterAthleteView(item.athlete_id, item.athlete_name)}
                    style={{ fontSize: "12.5px", cursor: "pointer", color: "var(--text-secondary)" }}
                  >
                    {lang === "en"
                      ? `${item.athlete_name}: "${item.title}" needs your approval`
                      : `${item.athlete_name}: "${item.title}" cần bạn duyệt`}
                  </div>
                ))}
              </div>
            </div>
          )}

          {overview && overview.athletes.length > 0 && (
            <div className="card" style={{ padding: isMobile ? "20px" : "28px", overflowX: "auto" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
                <Users size={20} weight="duotone" />
                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "800" }}>
                  {lang === "en" ? "Roster progress" : "Tiến độ vận động viên"}
                </h3>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {overview.athletes.map((athlete) => (
                  <div
                    key={athlete.athlete_id}
                    onClick={() => enterAthleteView(athlete.athlete_id, athlete.name)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "12px 14px",
                      borderRadius: "10px",
                      border: "1px solid var(--border-color)",
                      background: "rgba(255,255,255,0.4)",
                      cursor: "pointer",
                      gap: "12px",
                    }}
                  >
                    <div>
                      <div style={{ fontSize: "13.5px", fontWeight: "700" }}>{athlete.name}</div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                        {athlete.active_plan
                          ? `${athlete.active_plan.race_name} — ${lang === "en" ? "Week" : "Tuần"} ${athlete.active_plan.current_week}/${athlete.active_plan.total_weeks}`
                          : lang === "en" ? "No active plan" : "Chưa có kế hoạch"}
                      </div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                      {athlete.adherence_pct_14d !== null && (
                        <span style={{ fontSize: "12px", fontWeight: 700 }}>
                          {Math.round(athlete.adherence_pct_14d * 100)}%
                        </span>
                      )}
                      {athlete.missed_streak > 0 && (
                        <span style={{ fontSize: "11px", color: "var(--accent-alert)", fontWeight: 700 }}>
                          {athlete.missed_streak} {lang === "en" ? "missed in a row" : "buổi bỏ lỡ liên tiếp"}
                        </span>
                      )}
                      <ArrowRight size={14} weight="bold" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {overview && (
            <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
                <ChartBar size={20} weight="duotone" />
                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "800" }}>
                  {lang === "en" ? "Workout type mix (last 2 weeks)" : "Loại buổi tập (2 tuần qua)"}
                </h3>
              </div>
              <WorkoutTypeMixChart mix={overview.workout_type_mix} lang={lang} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
