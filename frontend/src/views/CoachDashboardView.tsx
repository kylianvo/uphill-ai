"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useState } from "react";
import {
  Users,
  PaperPlaneTilt,
  ArrowRight,
  X,
  ChartBar,
  Warning,
  ClipboardText,
  MagnifyingGlass,
  Funnel,
  ArrowCounterClockwise,
  TrendUp,
  CalendarCheck,
  Heartbeat,
} from "@phosphor-icons/react";
import { useAppContext } from "../contexts/AppContext";
import { useCoachDashboard } from "../hooks/useCoachDashboard";
import { useCoachOverview } from "../hooks/useCoachOverview";
import WorkoutTypeMixChart from "../components/WorkoutTypeMixChart";
import AdherenceTrendChart from "../components/AdherenceTrendChart";
import MissedByDayChart from "../components/MissedByDayChart";
import RaceBreakdownCard from "../components/RaceBreakdownCard";
import { matchesFilters, type RosterFilters } from "../utils/coachRosterFilters";

export default function CoachDashboardView({ isMobile }: { isMobile: boolean }) {
  const { lang } = useAppContext();
  const [activeSection, setActiveSection] = useState<"overview" | "roster">("overview");
  const [rosterFilters, setRosterFilters] = useState<RosterFilters>({
    search: "",
    level: "all",
    needsAttentionOnly: false,
    raceSearch: "",
  });
  const [insightsDays, setInsightsDays] = useState(14);
  const [insightsAthleteId, setInsightsAthleteId] = useState<number | null>(null);
  const [insightsLevel, setInsightsLevel] = useState<string>("all");
  const [selectedRace, setSelectedRace] = useState<string | null>(null);

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
    fetchOverview(insightsDays, insightsAthleteId, insightsLevel);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    fetchOverview(insightsDays, insightsAthleteId, insightsLevel);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [insightsDays, insightsAthleteId, insightsLevel]);

  const activeAthletes = roster.filter((r: any) => r.status === "active");
  const invitedAthletes = roster.filter((r: any) => r.status === "invited");

  const hasActiveInsightsFilter = insightsDays !== 14 || insightsAthleteId !== null || insightsLevel !== "all";

  const handleResetInsightsFilters = () => {
    setInsightsDays(14);
    setInsightsAthleteId(null);
    setInsightsLevel("all");
    setSelectedRace(null);
  };

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
              : lang === "en" ? "Roster" : "Danh sách VĐV"}
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
                        onClick={() => acceptInvite(inv.id)}
                        style={{ padding: "6px 14px", fontSize: "12px" }}
                      >
                        {lang === "en" ? "Accept" : "Chấp nhận"}
                      </button>
                      <button
                        className="btn"
                        onClick={() => declineInvite(inv.id)}
                        style={{ padding: "6px 14px", fontSize: "12px" }}
                      >
                        {lang === "en" ? "Decline" : "Từ chối"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Add athlete */}
          <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
              <PaperPlaneTilt size={20} weight="duotone" />
              <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "800" }}>
                {lang === "en" ? "Add an athlete" : "Thêm vận động viên"}
              </h3>
            </div>
            <div style={{ display: "flex", gap: "8px", flexWrap: isMobile ? "wrap" : "nowrap" }}>
              <input
                type="email"
                className="chat-input"
                style={{ flex: 1, minWidth: "220px", borderRadius: "8px" }}
                placeholder={lang === "en" ? "Athlete's account email" : "Email tài khoản VĐV"}
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
                : "VĐV cần có sẵn tài khoản Uphill AI."}
            </p>
          </div>

          {/* Roster */}
          <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
              <Users size={20} weight="duotone" />
              <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "800" }}>
                {lang === "en" ? "Your athletes" : "Danh sách học viên"}
              </h3>
            </div>

            {rosterLoading && roster.length === 0 ? (
              <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                {lang === "en" ? "Loading…" : "Đang tải…"}
              </p>
            ) : roster.length === 0 ? (
              <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                {lang === "en"
                  ? "No athletes yet - send an invite above to get started."
                  : "Chưa có VĐV nào - gửi lời mời ở trên để bắt đầu."}
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
                      background: "rgba(255,255,255,0.02)",
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
                            : "Chờ chấp nhận"}
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
                          {lang === "en" ? "View plan" : "Xem giáo án"} <ArrowRight size={12} weight="bold" />
                        </button>
                      )}
                      <button
                        onClick={() => removeFromRoster(row.id)}
                        title={lang === "en" ? "Remove" : "Gỡ bỏ"}
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
                  ? "No athletes yet - invite one from the Roster tab to get started."
                  : "Chưa có VĐV nào - mời một người từ tab Danh sách để bắt đầu."}
              </p>
            </div>
          )}

          {overview && overview.phase_alerts.length > 0 && (
            <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
                <Warning size={20} weight="duotone" />
                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "800" }}>
                  {lang === "en" ? "Phase alerts" : "Cảnh báo giai đoạn tập"}
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
                      : `${alert.athlete_name} bắt đầu phase ${alert.phase} ${alert.starts === "this_week" ? "tuần này" : "tuần tới"}`}
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
                  {lang === "en" ? "Action items" : "Việc cần xử lý"}
                </h3>
              </div>
              <div style={{ display: "flex", gap: "24px", marginBottom: overview.action_items.draft_plans.length || overview.action_items.pending_workout_approvals.length ? "12px" : 0 }}>
                <div>
                  <div style={{ fontSize: "22px", fontWeight: "800" }}>{overview.action_items.draft_plans.length}</div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    {lang === "en" ? "draft plans to finish" : "giáo án nháp cần hoàn thiện"}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "22px", fontWeight: "800" }}>{overview.action_items.pending_workout_approvals.length}</div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    {lang === "en" ? "workouts pending approval" : "bài tập chờ duyệt"}
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
                      : `${item.athlete_name}: "${item.race_name}" vẫn là bản nháp`}
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
                      : `${item.athlete_name}: "${item.title}" cần duyệt`}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Roster progress card */}
          {overview && (
            <div className="card" style={{ padding: isMobile ? "20px" : "28px", overflowX: "auto" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
                <Users size={20} weight="duotone" />
                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "800" }}>
                  {lang === "en" ? "Roster progress" : "Tiến độ học viên"}
                </h3>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "14px" }}>
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                  <div style={{ position: "relative", flex: "1 1 180px" }}>
                    <MagnifyingGlass
                      size={14}
                      style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }}
                    />
                    <input
                      type="text"
                      className="chat-input"
                      style={{ width: "100%", borderRadius: "8px", padding: "8px 10px 8px 30px", fontSize: "12.5px" }}
                      placeholder={lang === "en" ? "Search by name" : "Tìm theo tên VĐV"}
                      value={rosterFilters.search}
                      onChange={(e) => setRosterFilters((f) => ({ ...f, search: e.target.value }))}
                    />
                  </div>
                  <input
                    type="text"
                    className="chat-input"
                    style={{ flex: "1 1 180px", borderRadius: "8px", padding: "8px 10px", fontSize: "12.5px" }}
                    placeholder={lang === "en" ? "Search by race" : "Tìm theo race"}
                    value={rosterFilters.raceSearch}
                    onChange={(e) => setRosterFilters((f) => ({ ...f, raceSearch: e.target.value }))}
                  />
                </div>
              </div>
              {(() => {
                const filteredAthletes = overview.athletes.filter((a) => matchesFilters(a, rosterFilters));
                if (overview.athletes.length === 0) {
                  return null;
                }
                if (filteredAthletes.length === 0) {
                  return (
                    <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "No runners match your filters." : "Không có VĐV nào khớp bộ lọc."}
                    </p>
                  );
                }
                return (
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {filteredAthletes.map((athlete) => (
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
                          background: "rgba(255,255,255,0.02)",
                          cursor: "pointer",
                          gap: "12px",
                        }}
                      >
                        <div>
                          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ fontSize: "13.5px", fontWeight: "700" }}>{athlete.name}</span>
                            <span
                              style={{
                                fontSize: "9.5px",
                                fontWeight: 700,
                                padding: "1px 6px",
                                borderRadius: "999px",
                                background: "var(--border-color)",
                                color: "var(--text-secondary)",
                                textTransform: "capitalize",
                              }}
                            >
                              {athlete.runner_level}
                            </span>
                          </div>
                          <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                            {athlete.active_plan
                              ? `${athlete.active_plan.race_name} - ${lang === "en" ? "Week" : "Tuần"} ${athlete.active_plan.current_week}/${athlete.active_plan.total_weeks}`
                              : lang === "en" ? "No active plan" : "Chưa có giáo án"}
                          </div>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                          {athlete.adherence_pct !== null && (
                            <span style={{ fontSize: "12px", fontWeight: 700 }}>
                              {Math.round(athlete.adherence_pct * 100)}%
                            </span>
                          )}
                          <ArrowRight size={14} weight="bold" />
                        </div>
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>
          )}

          {/* Prominent Insights Control Bar */}
          {overview && (
            <div
              className="card"
              style={{
                padding: "16px 20px",
                background: "var(--bg-surface)",
                border: "1px solid var(--border-color)",
                borderRadius: "12px",
                display: "flex",
                flexDirection: "column",
                gap: "12px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "10px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <Funnel size={16} weight="bold" style={{ color: "var(--accent-primary)" }} />
                  <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>
                    {lang === "en" ? "Insights & Analytics Controls" : "Bộ lọc & Thống kê"}
                  </span>
                </div>

                {hasActiveInsightsFilter && (
                  <button
                    onClick={handleResetInsightsFilters}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "4px",
                      padding: "4px 10px",
                      fontSize: "11.5px",
                      fontWeight: 600,
                      borderRadius: "6px",
                      border: "1px solid var(--border-color)",
                      background: "transparent",
                      color: "var(--text-muted)",
                      cursor: "pointer",
                    }}
                  >
                    <ArrowCounterClockwise size={13} />
                    {lang === "en" ? "Reset filters" : "Đặt lại"}
                  </button>
                )}
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  flexWrap: "wrap",
                  gap: "14px",
                }}
              >
                {/* Time Window Segmented Control */}
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "11.5px", fontWeight: 600, color: "var(--text-secondary)" }}>
                    {lang === "en" ? "Window:" : "Thời gian:"}
                  </span>
                  <div
                    style={{
                      display: "inline-flex",
                      padding: "3px",
                      borderRadius: "8px",
                      background: "var(--bg-secondary, rgba(255,255,255,0.05))",
                      border: "1px solid var(--border-color)",
                      gap: "3px",
                    }}
                  >
                    {[
                      { days: 7, label: "7D" },
                      { days: 14, label: "14D" },
                      { days: 30, label: "30D" },
                      { days: 90, label: "90D" },
                    ].map((btn) => {
                      const isActive = insightsDays === btn.days;
                      return (
                        <button
                          key={btn.days}
                          onClick={() => setInsightsDays(btn.days)}
                          style={{
                            padding: "4px 12px",
                            fontSize: "11.5px",
                            fontWeight: isActive ? 700 : 500,
                            borderRadius: "6px",
                            border: "none",
                            background: isActive ? "var(--accent-primary)" : "transparent",
                            color: isActive ? "#ffffff" : "var(--text-secondary)",
                            cursor: "pointer",
                            transition: "all 0.15s ease",
                            boxShadow: isActive ? "0 2px 6px rgba(99, 102, 241, 0.25)" : "none",
                          }}
                        >
                          {btn.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Runner Selector Dropdown */}
                <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: "1 1 200px" }}>
                  <span style={{ fontSize: "11.5px", fontWeight: 600, color: "var(--text-secondary)" }}>
                    {lang === "en" ? "Athlete:" : "VĐV:"}
                  </span>
                  <select
                    value={insightsAthleteId ?? ""}
                    onChange={(e) => setInsightsAthleteId(e.target.value ? Number(e.target.value) : null)}
                    style={{
                      flex: 1,
                      padding: "6px 10px",
                      fontSize: "12px",
                      fontWeight: 500,
                      borderRadius: "8px",
                      border: "1px solid var(--border-color)",
                      background: "var(--bg-card, rgba(255,255,255,0.03))",
                      color: "var(--text-primary)",
                      cursor: "pointer",
                    }}
                  >
                    <option value="">
                      {lang === "en"
                        ? `All athletes (${activeAthletes.length})`
                        : `Tất cả VĐV (${activeAthletes.length})`}
                    </option>
                    {activeAthletes.map((ath: any) => (
                      <option key={ath.athlete_id} value={ath.athlete_id}>
                        {ath.athlete_name || ath.athlete_email}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Level Filter Chips */}
                <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
                  <span style={{ fontSize: "11.5px", fontWeight: 600, color: "var(--text-secondary)" }}>
                    {lang === "en" ? "Level:" : "Trình độ:"}
                  </span>
                  {(["all", "beginner", "intermediate", "advanced", "elite"] as const).map((lvl) => {
                    const isActive = insightsLevel === lvl;
                    return (
                      <button
                        key={lvl}
                        onClick={() => setInsightsLevel(lvl)}
                        style={{
                          padding: "3px 9px",
                          fontSize: "11px",
                          fontWeight: isActive ? 700 : 500,
                          borderRadius: "6px",
                          border: isActive ? "1px solid var(--accent-primary)" : "1px solid var(--border-color)",
                          background: isActive ? "var(--accent-primary-subtle, rgba(99, 102, 241, 0.15))" : "transparent",
                          color: isActive ? "var(--accent-primary)" : "var(--text-secondary)",
                          cursor: "pointer",
                          textTransform: "capitalize",
                          transition: "all 0.15s ease",
                        }}
                      >
                        {lvl === "all" ? (lang === "en" ? "All" : "Tất cả") : lvl}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Race Target Breakdown */}
          {overview && (
            <RaceBreakdownCard
              races={overview.races || []}
              athletesWithoutRace={overview.athletes_without_race || 0}
              selectedRace={selectedRace}
              onSelectRace={(race) => {
                setSelectedRace(race);
                setRosterFilters((f) => ({ ...f, raceSearch: race || "" }));
              }}
              lang={lang}
            />
          )}

          {/* Charts Grid */}
          {overview && (
            <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "repeat(auto-fit, minmax(320px, 1fr))", gap: "16px" }}>
              {/* Workout Type Mix */}
              <div className="card" style={{ padding: isMobile ? "20px" : "24px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
                  <ChartBar size={18} weight="duotone" style={{ color: "var(--accent-primary)" }} />
                  <h3 style={{ margin: 0, fontSize: "15px", fontWeight: "800" }}>
                    {lang === "en" ? "Workout type mix" : "Phân bổ loại bài tập"}
                  </h3>
                </div>
                <WorkoutTypeMixChart mix={overview.workout_type_mix} lang={lang} />
              </div>

              {/* Adherence Trend */}
              <div className="card" style={{ padding: isMobile ? "20px" : "24px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
                  <TrendUp size={18} weight="duotone" style={{ color: "var(--accent-primary)" }} />
                  <h3 style={{ margin: 0, fontSize: "15px", fontWeight: "800" }}>
                    {lang === "en" ? "Adherence trend" : "Tỷ lệ tuân thủ giáo án"}
                  </h3>
                </div>
                <AdherenceTrendChart trend={overview.adherence_trend} lang={lang} />
              </div>

              {/* Missed Workouts by Day */}
              <div className="card" style={{ padding: isMobile ? "20px" : "24px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
                  <CalendarCheck size={18} weight="duotone" style={{ color: "var(--accent-alert, #ef4444)" }} />
                  <h3 style={{ margin: 0, fontSize: "15px", fontWeight: "800" }}>
                    {lang === "en" ? "Missed workouts by day" : "Buổi tập bị bỏ theo thứ"}
                  </h3>
                </div>
                <MissedByDayChart missedByDay={overview.missed_by_day} lang={lang} />
              </div>

              {/* Effort (RPE) */}
              <div className="card" style={{ padding: isMobile ? "20px" : "24px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
                  <Heartbeat size={18} weight="duotone" style={{ color: "#e11d48" }} />
                  <h3 style={{ margin: 0, fontSize: "15px", fontWeight: "800" }}>
                    {lang === "en" ? "Effort (RPE)" : "Mức độ gắng sức (RPE)"}
                  </h3>
                </div>
                {overview.rpe_distribution.avg_rpe === null ? (
                  <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                    {lang === "en" ? "No block reviews in this window." : "Chưa có đánh giá khối tập nào trong khung thời gian này."}
                  </p>
                ) : (
                  <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
                    <span style={{ fontSize: "28px", fontWeight: 800 }}>{overview.rpe_distribution.avg_rpe.toFixed(1)}</span>
                    <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                      {lang === "en" ? "average RPE" : "RPE trung bình"}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Bottom Overview Cards */}
          {overview && (
            <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
              {/* Race Readiness */}
              <div className="card" style={{ padding: isMobile ? "20px" : "24px" }}>
                <h3 style={{ margin: "0 0 14px 0", fontSize: "15px", fontWeight: "800" }}>
                  {lang === "en" ? "Race readiness" : "Độ sẵn sàng thi đấu"}
                </h3>
                <div style={{ display: "flex", gap: "16px" }}>
                  <div>
                    <div style={{ fontSize: "22px", fontWeight: 800, color: "#16a34a" }}>{overview.race_readiness.on_track}</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{lang === "en" ? "on track" : "đúng tiến độ"}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: "22px", fontWeight: 800, color: "#d97706" }}>{overview.race_readiness.at_risk}</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{lang === "en" ? "at risk" : "cần lưu ý"}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: "22px", fontWeight: 800, color: "var(--accent-alert)" }}>{overview.race_readiness.behind}</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{lang === "en" ? "behind" : "chậm tiến độ"}</div>
                  </div>
                </div>
              </div>

              {/* Roster Totals */}
              <div className="card" style={{ padding: isMobile ? "20px" : "24px" }}>
                <h3 style={{ margin: "0 0 14px 0", fontSize: "15px", fontWeight: "800" }}>
                  {lang === "en" ? "Roster totals" : "Tổng khối lượng toàn đội"}
                </h3>
                <div style={{ display: "flex", gap: "18px", flexWrap: "wrap" }}>
                  <div>
                    <div style={{ fontSize: "19px", fontWeight: 800 }}>{overview.roster_totals.distance_km.toFixed(0)} km</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{lang === "en" ? "distance" : "quãng đường"}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: "19px", fontWeight: 800 }}>{overview.roster_totals.duration_hours.toFixed(1)}h</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{lang === "en" ? "training time" : "thời gian tập"}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: "19px", fontWeight: 800 }}>{Math.round(overview.roster_totals.elevation_gain_m)} m</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{lang === "en" ? "elevation" : "độ dốc (gain)"}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: "19px", fontWeight: 800 }}>{overview.roster_totals.workout_count}</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{lang === "en" ? "workouts" : "buổi tập"}</div>
                  </div>
                </div>
              </div>

              {/* Most Consistent */}
              {overview.most_consistent.length > 0 && (
                <div className="card" style={{ padding: isMobile ? "20px" : "24px" }}>
                  <h3 style={{ margin: "0 0 14px 0", fontSize: "15px", fontWeight: "800" }}>
                    {lang === "en" ? "Most consistent" : "Chăm chỉ nhất"}
                  </h3>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {overview.most_consistent.map((a, i) => (
                      <div key={a.athlete_id} style={{ display: "flex", justifyContent: "space-between", fontSize: "12.5px" }}>
                        <span>{i + 1}. {a.name}</span>
                        <span style={{ fontWeight: 700, color: "#16a34a" }}>{Math.round(a.adherence_pct * 100)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
