/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { useAppContext } from "../contexts/AppContext";
import { usePlanner } from "../hooks/usePlanner";
import { translations } from "../app/translations";
import WorkoutDescription from "../components/WorkoutDescription";
import ToolsView from "./ToolsView";
import { UploadSimple, FileArrowUp, Heart, Clock, Mountains, MapPin, Footprints, ArrowsMerge, PlayCircle, CheckCircle, Fire, Path, RoadHorizon, Info, Check, Question, WarningCircle, Plus, Trash, Archive, LockKey, LockKeyOpen, Trophy, Target, Sneaker, PersonSimpleRun, Bed, XCircle, DownloadSimple } from '@phosphor-icons/react';

export default function PlannerView({ isMobile }: { isMobile: boolean }) {
  const ctx = useAppContext();
  const { handleGeneratePlan, getPlanDistance, getPlanElevation, formatPlanName, handleSelectPlan, handleSwapWorkouts, handleToggleComplete, getWeekWorkouts, getWorkoutDate, handlePlannerGpxFileChange, plannerGpxInputRef, trackEvent, API_BASE_URL, fetchRecentPlansWithToken, startPlanJobPoller } = usePlanner();
  const { lang, activePlan, planLoading, planErrorMsg, planForm, setPlanForm, targetTimeH, setTargetTimeH, targetTimeM, setTargetTimeM, targetTimeS, setTargetTimeS, cutoffTimeH, setCutoffTimeH, cutoffTimeM, setCutoffTimeM, cutoffTimeS, setCutoffTimeS, recentPlans, selectedWeek, setSelectedWeek, swapDay1, setSwapDay1, swapDay2, setSwapDay2, setWorkouts, setBackupWorkouts, setActivePlan, workouts, backupWorkouts, backupActivePlan, setBackupActivePlan, courseInputMode, setCourseInputMode, plannerGpxLoading, plannerGpxFile, plannerGpxError, showExportOptions, setShowExportOptions, exportTimePref, setExportTimePref } = ctx;
  const t = (key: keyof typeof translations.en) => translations[lang]?.[key] || translations.en[key] || key;
  const totalWeeks = activePlan ? (activePlan.plan_duration_weeks || 1) : 0;
    return (
      <div>
        {!activePlan ? (
          <form onSubmit={handleGeneratePlan} style={{ background: "rgba(255, 255, 255, 0.95)", border: "1px solid var(--border-color)", padding: isMobile ? "20px" : "32px", borderRadius: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "8px" }}>
              <h3 style={{ fontSize: isMobile ? "18px" : "22px", margin: 0, color: "var(--accent-primary)" }}>
                {lang === "en" ? "Plan Settings" : "Cài đặt Kế hoạch"}
              </h3>
            </div>

            {/* ── Step 1: Plan Goal Category ────────────────────── */}
            <div style={{ marginBottom: "20px" }}>
              <label style={{ display: "block", fontSize: "12px", fontWeight: "700", marginBottom: "10px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                {t("goal_category")}
              </label>
              <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr 1fr" : "repeat(5, 1fr)", gap: "8px" }}>
                {([
                  { val: "race",          Icon: Trophy, label: t("goal_race").replace(" 🏆", "") },
                  { val: "distance",      Icon: Target, label: t("goal_distance").replace(" 📏", "") },
                  { val: "start_running", Icon: Sneaker, label: t("goal_start").replace(" 🌱", "") },
                  { val: "return",        Icon: PersonSimpleRun, label: t("goal_return").replace(" 🔄", "") },
                  { val: "recovery",      Icon: Bed, label: t("goal_recovery").replace(" 💤", "") },
                ] as const).map(({ val, Icon, label }) => {
                  const active = planForm.plan_goal_category === val;
                  return (
                    <button key={val} type="button"
                      onClick={() => setPlanForm({ ...planForm, plan_goal_category: val })}
                      style={{ padding: "10px 6px", borderRadius: "10px", border: `1.5px solid ${active ? "var(--accent-primary)" : "var(--border-color)"}`, background: active ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: active ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: active ? "700" : "500", fontSize: "12px", cursor: "pointer", textAlign: "center" as const, display: "flex", flexDirection: "column" as const, alignItems: "center", gap: "4px" }}>
                      <Icon size={24} weight="duotone" />
                      <span>{label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* ── Race / Distance fields ────────────────────────── */}
            {(planForm.plan_goal_category === "race" || planForm.plan_goal_category === "distance") && (<>

              <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: isMobile ? "12px" : "16px", marginBottom: "12px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                    {planForm.plan_goal_category === "race" ? t("plan_race_name") : (lang === "en" ? "Distance Goal Name" : "Tên Mục tiêu Cự ly")}
                  </label>
                  <input type="text" className="chat-input"
                    style={{ borderRadius: "8px", width: "100%", padding: "10px" }}
                    placeholder={planForm.plan_goal_category === "race" ? "e.g. UTMB, SUM30" : "e.g. My First Marathon"}
                    value={planForm.race_name}
                    onChange={(e) => setPlanForm({ ...planForm, race_name: e.target.value })} />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                    {planForm.plan_goal_category === "race" ? t("plan_race_date") : (lang === "en" ? "Target Date" : "Ngày Mục tiêu")}
                  </label>
                  <input type="date" className="chat-input"
                    style={{ borderRadius: "8px", width: "100%", padding: "10px" }}
                    value={planForm.race_date}
                    onChange={(e) => setPlanForm({ ...planForm, race_date: e.target.value })} />
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: isMobile ? "12px" : "16px", marginBottom: "16px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>{t("plan_terrain")}</label>
                  <select className="chat-input" style={{ borderRadius: "8px", width: "100%", height: "38px", padding: "0 8px", fontSize: "13px" }}
                    value={planForm.terrain} onChange={(e) => setPlanForm({ ...planForm, terrain: e.target.value })}>
                    <option value="trail">{t("plan_trail")}</option>
                    <option value="road">{t("plan_road")}</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>{t("plan_goal_type")}</label>
                  <select className="chat-input" style={{ borderRadius: "8px", width: "100%", height: "38px", padding: "0 8px", fontSize: "13px" }}
                    value={planForm.goal_type} onChange={(e) => setPlanForm({ ...planForm, goal_type: e.target.value })}>
                    <option value="finish">{t("plan_goal_finish")}</option>
                    <option value="time">{t("plan_goal_time")}</option>
                    <option value="optimal">{t("plan_goal_optimal")}</option>
                  </select>
                </div>
              </div>

              {/* Target time */}
              {planForm.goal_type === "time" && (
                <div style={{ marginBottom: "16px" }}>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>{t("plan_target_time")}</label>
                  <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr 1.1fr", gap: "8px" }}>
                    <div><label style={{ display: "block", fontSize: "11px", color: "var(--text-secondary)", marginBottom: "4px" }}>{lang === "en" ? "Hours" : "Giờ"}</label><input type="number" min="0" max="99" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "8px", textAlign: "center" }} placeholder="0" value={targetTimeH} onChange={(e) => setTargetTimeH(e.target.value)} /></div>
                    <div><label style={{ display: "block", fontSize: "11px", color: "var(--text-secondary)", marginBottom: "4px" }}>{lang === "en" ? "Minutes" : "Phút"}</label><input type="number" min="0" max="59" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "8px", textAlign: "center" }} placeholder="0" value={targetTimeM} onChange={(e) => setTargetTimeM(e.target.value)} /></div>
                    <div><label style={{ display: "block", fontSize: "11px", color: "var(--text-secondary)", marginBottom: "4px" }}>{lang === "en" ? "Seconds" : "Giây"}</label><input type="number" min="0" max="59" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "8px", textAlign: "center" }} placeholder="0" value={targetTimeS} onChange={(e) => setTargetTimeS(e.target.value)} /></div>
                  </div>
                </div>
              )}

              {/* Cutoff time */}
              {planForm.goal_type === "finish" && (
                <div style={{ marginBottom: "16px" }}>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "2px", color: "var(--text-secondary)" }}>{t("plan_cutoff_time")} <span style={{ fontWeight: 400, opacity: 0.7 }}>{lang === "en" ? "(optional — we'll target 85% of cutoff)" : "(tùy chọn — mục tiêu đạt 85% cutoff)"}</span></label>
                  <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr 1.1fr", gap: "8px", marginTop: "6px" }}>
                    <div><label style={{ display: "block", fontSize: "11px", color: "var(--text-secondary)", marginBottom: "4px" }}>{lang === "en" ? "Hours" : "Giờ"}</label><input type="number" min="0" max="99" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "8px", textAlign: "center" }} placeholder="0" value={cutoffTimeH} onChange={(e) => setCutoffTimeH(e.target.value)} /></div>
                    <div><label style={{ display: "block", fontSize: "11px", color: "var(--text-secondary)", marginBottom: "4px" }}>{lang === "en" ? "Minutes" : "Phút"}</label><input type="number" min="0" max="59" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "8px", textAlign: "center" }} placeholder="0" value={cutoffTimeM} onChange={(e) => setCutoffTimeM(e.target.value)} /></div>
                    <div><label style={{ display: "block", fontSize: "11px", color: "var(--text-secondary)", marginBottom: "4px" }}>{lang === "en" ? "Seconds" : "Giây"}</label><input type="number" min="0" max="59" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "8px", textAlign: "center" }} placeholder="0" value={cutoffTimeS} onChange={(e) => setCutoffTimeS(e.target.value)} /></div>
                  </div>
                </div>
              )}

              {/* Course profile */}
              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>{t("plan_course_mode")}</label>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button type="button" className={`btn ${courseInputMode === "manual" ? "btn-primary" : "btn-secondary"}`} style={{ padding: "6px 12px", fontSize: "12px", borderRadius: "8px", height: "32px", flex: 1 }} onClick={() => setCourseInputMode("manual")}>
                    {lang === "en" ? "✍️ Manual" : "✍️ Thủ công"}
                  </button>
                  <button type="button" className={`btn ${courseInputMode === "gpx" ? "btn-primary" : "btn-secondary"}`} style={{ padding: "6px 12px", fontSize: "12px", borderRadius: "8px", height: "32px", flex: 1 }} onClick={() => setCourseInputMode("gpx")}>
                    {lang === "en" ? "📂 GPX Route" : "📂 Tệp GPX"}
                  </button>
                </div>
              </div>

              {courseInputMode === "manual" ? (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: isMobile ? "12px" : "16px", marginBottom: "20px" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Distance (km)" : "Cự ly (km)"}
                    </label>
                    <input type="number" step="0.1" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "10px" }} placeholder="e.g. 50" value={planForm.course_distance_km} onChange={(e) => setPlanForm({ ...planForm, course_distance_km: e.target.value })} />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Elevation Gain (m)" : "Độ cao lũy kế (m)"}
                    </label>
                    <input type="number" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "10px" }} placeholder="e.g. 1500" value={planForm.course_elevation_gain_m} onChange={(e) => setPlanForm({ ...planForm, course_elevation_gain_m: e.target.value })} />
                  </div>
                </div>
              ) : (
                <div style={{ marginBottom: "20px", padding: "16px", background: "rgba(255,255,255,0.1)", border: "1px dashed var(--border-color)", borderRadius: "12px", textAlign: "center" }}>
                  <input type="file" accept=".gpx" style={{ display: "none" }} ref={plannerGpxInputRef} onChange={handlePlannerGpxFileChange} />
                  <button type="button" className="btn btn-secondary" style={{ fontSize: "12px", padding: "6px 12px", height: "32px", margin: "0 auto 8px auto" }} onClick={() => plannerGpxInputRef.current?.click()} disabled={plannerGpxLoading}>
                    {plannerGpxLoading ? (lang === "en" ? "Parsing..." : "Đang đọc...") : (lang === "en" ? "Select GPX" : "Chọn tệp GPX")}
                  </button>
                  {plannerGpxFile && <div style={{ marginTop: "6px", padding: "6px", background: "rgba(16, 185, 129, 0.05)", border: "1px solid var(--border-color)", borderRadius: "6px", fontSize: "11.5px" }}>✅ {planForm.course_distance_km}km, {planForm.course_elevation_gain_m}m</div>}
                  {plannerGpxError && <div style={{ marginTop: "6px", fontSize: "11px", color: "var(--accent-alert)" }}><XCircle weight="fill" style={{marginRight: "4px", verticalAlign: "middle"}}/> {plannerGpxError}</div>}
                </div>
              )}
            </>)}

            {/* ── Start Running fields ───────────────────────────── */}
            {planForm.plan_goal_category === "start_running" && (
              <div style={{ marginBottom: "16px", padding: "16px", border: "1px solid var(--border-color)", borderRadius: "12px", display: "flex", flexDirection: "column", gap: "12px" }}>
                <h4 style={{ margin: 0, fontSize: "14px", fontWeight: "700", color: "var(--text-bright)", borderBottom: "1px solid var(--border-color)", paddingBottom: "8px" }}>
                  {lang === "en" ? "Start Running Program" : "Lộ trình Bắt đầu Chạy bộ"}
                </h4>
                <div style={{ fontSize: "12.5px", color: "var(--text-muted)" }}>
                  {lang === "en" ? "We'll build a gentle walk-to-run programme starting from your plan start date." : "Chúng tôi sẽ xây dựng một lộ trình chạy kết hợp đi bộ nhẹ nhàng bắt đầu từ ngày bạn chọn."}
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Plan Start Date" : "Ngày bắt đầu kế hoạch"}
                    </label>
                    <input type="date" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "10px" }} value={planForm.plan_start_date} onChange={e => setPlanForm({ ...planForm, plan_start_date: e.target.value })} />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Duration (weeks)" : "Thời lượng (tuần)"}
                    </label>
                    <select className="chat-input" style={{ borderRadius: "8px", width: "100%", height: "38px", padding: "0 8px", fontSize: "13px" }} value={planForm.plan_duration_weeks} onChange={e => setPlanForm({ ...planForm, plan_duration_weeks: parseInt(e.target.value) })}>
                      {[6,8,10,12,16].map(w => <option key={w} value={w}>{w} {lang === "en" ? "weeks" : "tuần"}</option>)}
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* ── Return to Running fields ───────────────────────── */}
            {planForm.plan_goal_category === "return" && (
              <div style={{ marginBottom: "16px", padding: "16px", border: "1px solid var(--border-color)", borderRadius: "12px", display: "flex", flexDirection: "column", gap: "12px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border-color)", paddingBottom: "8px", flexWrap: "wrap", gap: "8px" }}>
                  <h4 style={{ margin: 0, fontSize: "14px", fontWeight: "700", color: "var(--text-bright)" }}>
                    {lang === "en" ? "🔄 Return to Running" : "🔄 Tập luyện trở lại"}
                  </h4>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px" }}>
                    <select
                      className="btn btn-secondary"
                      style={{
                        fontSize: "12px",
                        height: "36px",
                        padding: "0 16px",
                        cursor: "pointer",
                        outline: "none",
                        border: "1px solid rgba(0, 0, 0, 0.1)",
                        background: "rgba(0, 0, 0, 0.06)",
                        color: "#111111",
                        textAlignLast: "center",
                        WebkitAppearance: "none",
                        MozAppearance: "none",
                        appearance: "none",
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        borderRadius: "9999px",
                        width: "auto",
                        maxWidth: "220px"
                      }}
                      value=""
                      onChange={(e) => {
                        const val = e.target.value;
                        if (val) handleSelectPlan(Number(val));
                      }}
                    >
                      <option value="" style={{ color: "var(--text-primary)" }}>
                        {lang === "en" ? "Load Recent Plan..." : "Tải lịch tập gần đây..."}
                      </option>
                      {recentPlans.length === 0 ? (
                        <option value="" disabled style={{ color: "var(--text-muted)" }}>
                          {lang === "en" ? "— No plans available —" : "— Không có lịch tập —"}
                        </option>
                      ) : (
                        recentPlans.slice(0, 3).map((p: any) => (
                          <option key={p.id} value={p.id} style={{ color: "var(--text-primary)" }}>
                            {formatPlanName(p)}
                          </option>
                        ))
                      )}
                    </select>
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Plan Start Date" : "Ngày bắt đầu kế hoạch"}
                    </label>
                    <input type="date" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "10px" }} value={planForm.plan_start_date} onChange={e => setPlanForm({ ...planForm, plan_start_date: e.target.value })} />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Duration (weeks)" : "Thời lượng (tuần)"}
                    </label>
                    <select className="chat-input" style={{ borderRadius: "8px", width: "100%", height: "38px", padding: "0 8px", fontSize: "13px" }} value={planForm.plan_duration_weeks} onChange={e => setPlanForm({ ...planForm, plan_duration_weeks: parseInt(e.target.value) })}>
                      {[6,8,10,12,16].map(w => <option key={w} value={w}>{w} {lang === "en" ? "weeks" : "tuần"}</option>)}
                    </select>
                  </div>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "12.5px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                    {lang === "en" ? "How long have you been away?" : "Bạn đã dừng chạy trong bao lâu?"}
                  </label>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                    {["< 2 weeks","2–6 weeks","1–3 months","3–6 months","6+ months"].map(v => {
                      const label = lang === "vi"
                        ? v.replace("< 2 weeks", "< 2 tuần").replace("weeks", "tuần").replace("months", "tháng").replace("months+", "tháng trở lên")
                        : v;
                      return (
                        <button key={v} type="button" onClick={() => setPlanForm({ ...planForm, time_away: v })}
                          style={{ padding: "6px 10px", borderRadius: "8px", border: `1.5px solid ${planForm.time_away === v ? "var(--accent-primary)" : "var(--border-color)"}`, background: planForm.time_away === v ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: planForm.time_away === v ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: planForm.time_away === v ? "700" : "500", fontSize: "12px", cursor: "pointer" }}>
                          {label}
                        </button>
                      );
                    })}
                  </div>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "12.5px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                    {lang === "en" ? "How are you feeling now?" : "Hiện tại bạn cảm thấy thế nào?"}
                  </label>
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    {["Feeling good, just need structure","A bit rusty, slightly deconditioned","Significant deconditioning — starting nearly fresh"].map(v => {
                      const label = lang === "vi"
                        ? v.replace("Feeling good, just need structure", "Cảm thấy tốt, chỉ cần lộ trình bài bản")
                           .replace("A bit rusty, slightly deconditioned", "Hơi oải, giảm thể lực nhẹ")
                           .replace("Significant deconditioning — starting nearly fresh", "Giảm thể lực nhiều — bắt đầu gần như mới")
                        : v;
                      return (
                        <button key={v} type="button" onClick={() => setPlanForm({ ...planForm, fitness_feel: v })}
                          style={{ padding: "8px 12px", borderRadius: "8px", border: `1.5px solid ${planForm.fitness_feel === v ? "var(--accent-primary)" : "var(--border-color)"}`, background: planForm.fitness_feel === v ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: planForm.fitness_feel === v ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: planForm.fitness_feel === v ? "700" : "500", fontSize: "12.5px", cursor: "pointer", textAlign: "left" as const }}>
                          {label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {/* ── Post-Race Recovery fields ──────────────────────── */}
            {planForm.plan_goal_category === "recovery" && (
              <div style={{ marginBottom: "16px", padding: "16px", border: "1px solid var(--border-color)", borderRadius: "12px", display: "flex", flexDirection: "column", gap: "12px" }}>
                <h4 style={{ margin: 0, fontSize: "14px", fontWeight: "700", color: "var(--text-bright)", borderBottom: "1px solid var(--border-color)", paddingBottom: "8px" }}>
                  {lang === "en" ? "💤 Post-Race Recovery Program" : "💤 Lộ trình Phục hồi sau Giải chạy"}
                </h4>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Plan Start Date" : "Ngày bắt đầu kế hoạch"}
                    </label>
                    <input type="date" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "10px" }} value={planForm.plan_start_date} onChange={e => setPlanForm({ ...planForm, plan_start_date: e.target.value })} />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Duration (weeks)" : "Thời lượng (tuần)"}
                    </label>
                    <select className="chat-input" style={{ borderRadius: "8px", width: "100%", height: "38px", padding: "0 8px", fontSize: "13px" }} value={planForm.plan_duration_weeks} onChange={e => setPlanForm({ ...planForm, plan_duration_weeks: parseInt(e.target.value) })}>
                      {[4,6,8,10,12].map(w => <option key={w} value={w}>{w} {lang === "en" ? "weeks" : "tuần"}</option>)}
                    </select>
                  </div>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "12.5px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                    {lang === "en" ? "Race you completed" : "Giải chạy bạn đã hoàn thành"}
                  </label>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                    {["5k","10k","Half Marathon","Marathon","Ultra (< 60k)","Ultra (60k+)"].map(v => (
                      <button key={v} type="button" onClick={() => setPlanForm({ ...planForm, race_distance_completed: v })}
                        style={{ padding: "6px 10px", borderRadius: "8px", border: `1.5px solid ${planForm.race_distance_completed === v ? "var(--accent-primary)" : "var(--border-color)"}`, background: planForm.race_distance_completed === v ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: planForm.race_distance_completed === v ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: planForm.race_distance_completed === v ? "700" : "500", fontSize: "12px", cursor: "pointer" }}>
                        {v}
                      </button>
                    ))}
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Days since race" : "Số ngày kể từ giải chạy"}
                    </label>
                    <input type="number" min="0" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "10px" }} placeholder="e.g. 3" value={planForm.days_since_race} onChange={e => setPlanForm({ ...planForm, days_since_race: e.target.value })} />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "How are you feeling?" : "Bạn cảm thấy như thế nào?"}
                    </label>
                    <select className="chat-input" style={{ borderRadius: "8px", width: "100%", height: "38px", padding: "0 8px", fontSize: "13px" }} value={planForm.recovery_feel} onChange={e => setPlanForm({ ...planForm, recovery_feel: e.target.value })}>
                      <option value="">{lang === "en" ? "Select..." : "Chọn..."}</option>
                      <option value="Feeling great, minimal soreness">{lang === "en" ? "Great, minimal soreness" : "Rất tốt, mỏi cơ tối thiểu"}</option>
                      <option value="Moderate fatigue, some soreness">{lang === "en" ? "Moderate fatigue" : "Mệt mỏi vừa phải"}</option>
                      <option value="Very fatigued — need real rest">{lang === "en" ? "Very fatigued" : "Rất mệt mỏi"}</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* ── Plan Start Date for Race/Distance ─────────────── */}
            {(planForm.plan_goal_category === "race" || planForm.plan_goal_category === "distance") && (
              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>{t("plan_start_date")}</label>
                <input type="date" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "10px" }} value={planForm.plan_start_date} onChange={e => setPlanForm({ ...planForm, plan_start_date: e.target.value })} />
                <p style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "5px", margin: "5px 0 0 0" }}>
                  {lang === "en"
                    ? "Week 1 of your plan will begin from this date (defaults to today)."
                    : "Tuần 1 trong kế hoạch của bạn sẽ bắt đầu từ ngày này (mặc định là hôm nay)."}
                </p>
              </div>
            )}

            {/* ── Schedule Preferences (shared) ─────────────────── */}
            <div style={{ marginBottom: "16px", padding: "14px", background: "rgba(255,255,255,0.15)", border: "1px solid var(--border-color)", borderRadius: "12px" }}>
              <label style={{ display: "block", fontSize: "12px", fontWeight: "700", marginBottom: "10px", color: "var(--text-secondary)", letterSpacing: "0.04em", textTransform: "uppercase" }}>
                {t("plan_schedule_prefs")}
              </label>

              <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                    {t("plan_days_per_week")}
                  </label>
                  <div style={{ display: "flex", gap: "6px" }}>
                    {[3, 4, 5, 6, 7].map(n => (
                      <button key={n} type="button" onClick={() => setPlanForm({ ...planForm, days_per_week: n })}
                        style={{ flex: 1, padding: "7px 0", borderRadius: "8px", border: `1.5px solid ${planForm.days_per_week === n ? "var(--accent-primary)" : "var(--border-color)"}`, background: planForm.days_per_week === n ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: planForm.days_per_week === n ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: "700", fontSize: "13px", cursor: "pointer" }}
                      >{n}</button>
                    ))}
                  </div>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                    {t("plan_long_run_day")}
                  </label>
                  <select className="chat-input" style={{ borderRadius: "8px", width: "100%", height: "38px", padding: "0 8px", fontSize: "13px" }}
                    value={planForm.long_run_day} onChange={e => setPlanForm({ ...planForm, long_run_day: e.target.value })}>
                    {["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].map(d => {
                      const label = lang === "vi"
                        ? d.replace("Monday", "Thứ Hai").replace("Tuesday", "Thứ Ba").replace("Wednesday", "Thứ Tư").replace("Thursday", "Thứ Năm").replace("Friday", "Thứ Sáu").replace("Saturday", "Thứ Bảy").replace("Sunday", "Chủ Nhật")
                        : d;
                      return (
                        <option key={d} value={d}>{label}</option>
                      );
                    })}
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                  {t("plan_preferred_days")}
                </label>
                <div style={{ display: "flex", gap: "5px", flexWrap: "wrap" }}>
                  {["Mon","Tue","Wed","Thu","Fri","Sat","Sun"].map((short, i) => {
                    const full = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][i];
                    const selected = planForm.preferred_days.includes(full);
                    const label = lang === "vi"
                      ? ["T2","T3","T4","T5","T6","T7","CN"][i]
                      : short;
                    return (
                      <button key={full} type="button"
                        onClick={() => {
                          const next = selected ? planForm.preferred_days.filter((d: any) => d !== full) : [...planForm.preferred_days, full];
                          setPlanForm({ ...planForm, preferred_days: next });
                        }}
                        style={{ padding: "5px 10px", borderRadius: "8px", border: `1.5px solid ${selected ? "var(--accent-primary)" : "var(--border-color)"}`, background: selected ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: selected ? "var(--accent-primary)" : "var(--text-secondary)", fontWeight: selected ? "700" : "500", fontSize: "12px", cursor: "pointer" }}
                      >{label}</button>
                    );
                  })}
                </div>
                <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "5px", margin: "5px 0 0 0" }}>
                  {lang === "en"
                    ? "The AI will prioritise these days when building your weekly schedule."
                    : "Trí tuệ nhân tạo (AI) sẽ ưu tiên xếp lịch tập vào các ngày này."}
                </p>
              </div>
            </div>

            {planErrorMsg && (
              <div style={{ color: "var(--accent-alert)", fontSize: "12px", padding: "10px", background: "rgba(239, 68, 68, 0.08)", borderRadius: "6px", marginBottom: "16px" }}>
                {planErrorMsg}
              </div>
            )}

            {backupActivePlan ? (
              <div style={{ display: "flex", gap: "10px", width: "100%" }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ flex: 1, height: "42px", fontSize: "13.5px" }}
                  onClick={() => {
                    setActivePlan(backupActivePlan);
                    setWorkouts(backupWorkouts);
                    setBackupActivePlan(null);
                    setBackupWorkouts([]);
                  }}
                >
                  {lang === "en" ? "◀ Go Back" : "◀ Quay lại"}
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ flex: 2, height: "42px", fontSize: "13.5px" }}
                  disabled={planLoading}
                >
                  {planLoading ? (lang === "en" ? "Building Plan..." : "Đang tạo Kế hoạch...") : (lang === "en" ? "🛠️ Build Custom Calendar" : "🛠️ Thiết lập Lịch tập tùy chỉnh")}
                </button>
              </div>
            ) : (
              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: "100%", height: "42px", fontSize: "13.5px" }}
                disabled={planLoading}
              >
                {planLoading ? (lang === "en" ? "Building Plan..." : "Đang tạo Kế hoạch...") : (lang === "en" ? "🛠️ Build Custom Calendar" : "🛠️ Thiết lập Lịch tập tùy chỉnh")}
              </button>
            )}
          </form>
        ) : (
          <div style={{ background: "rgba(255, 255, 255, 0.95)", border: "1px solid var(--border-color)", padding: isMobile ? "20px" : "32px", borderRadius: "16px" }}>
            {/* Header info */}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "16px" }}>
              <div>
                <h3 style={{ fontSize: isMobile ? "18px" : "22px", margin: 0 }}>
                  {activePlan.race_name}
                  {(getPlanDistance(activePlan) || getPlanElevation(activePlan)) && (
                    <span style={{ fontWeight: "normal", opacity: 0.85, fontSize: isMobile ? "14px" : "17px", marginLeft: "8px" }}>
                      ({getPlanDistance(activePlan) ? `${getPlanDistance(activePlan)}km` : ""}{getPlanDistance(activePlan) && getPlanElevation(activePlan) ? ", " : ""}{getPlanElevation(activePlan) ? `+${getPlanElevation(activePlan)}m` : ""})
                    </span>
                  )}
                </h3>
                <p style={{ color: "var(--text-secondary)", fontSize: "12px", marginTop: "2px", fontWeight: "500" }}>
                  {(() => {
                    const goal = activePlan.goal_type || "";
                    if (["start_running", "return", "recovery"].includes(goal)) {
                      return lang === "en" ? `Block ends: ${activePlan.race_date}` : `Kết thúc: ${activePlan.race_date}`;
                    } else {
                      return lang === "en" ? `Race Day: ${activePlan.race_date}` : `Ngày đua: ${activePlan.race_date}`;
                    }
                  })()} | {activePlan.goal_type === "finish"
                    ? (lang === "en" ? "Simply Finish" : "Chỉ cần Hoàn thành")
                    : activePlan.goal_type === "time"
                      ? (lang === "en" ? "Time Target" : "Mục tiêu Thời gian")
                      : activePlan.goal_type === "optimal"
                        ? (lang === "en" ? "Optimal Performance" : "Hiệu suất Tối ưu")
                        : activePlan.goal_type.toUpperCase().replace("_", " ")}
                </p>
              </div>

              {!showExportOptions ? (
                <div style={{ display: "flex", gap: "10px", width: "100%", flexWrap: "wrap" }}>
                  <button
                    className="btn btn-primary"
                    style={{ flex: 1, minWidth: "120px", fontSize: "12px", height: "36px", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}
                    onClick={() => setShowExportOptions(true)}
                  >
                    {lang === "en" ? "Export Calendar" : "Xuất lịch tập"}
                  </button>

                  <select
                    className="btn btn-secondary"
                    style={{
                      flex: 1,
                      minWidth: "120px",
                      fontSize: "12px",
                      height: "36px",
                      padding: "0 8px",
                      cursor: "pointer",
                      outline: "none",
                      border: "1px solid rgba(0, 0, 0, 0.1)",
                      background: "rgba(0, 0, 0, 0.06)",
                      color: "#111111",
                      textAlignLast: "center",
                      WebkitAppearance: "none",
                      MozAppearance: "none",
                      appearance: "none",
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                      borderRadius: "9999px",
                    }}
                    value=""
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val) handleSelectPlan(Number(val));
                    }}
                  >
                    <option value="" style={{ color: "var(--text-primary)" }}>
                      {lang === "en" ? "Load Recent Plan..." : "Tải lịch tập gần đây..."}
                    </option>
                    {recentPlans.length === 0 ? (
                      <option value="" disabled style={{ color: "var(--text-muted)" }}>
                        {lang === "en" ? "— No plans available —" : "— Không có lịch tập —"}
                      </option>
                    ) : (
                      recentPlans.map((p: any) => (
                        <option key={p.id} value={p.id} style={{ color: "var(--text-primary)" }}>
                          {formatPlanName(p)}
                        </option>
                      ))
                    )}
                  </select>

                  <button
                    className="btn btn-primary"
                    style={{ flex: 1, minWidth: "120px", fontSize: "13px", fontWeight: "600", height: "38px", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px", boxShadow: "0 4px 12px rgba(25, 206, 139, 0.2)" }}
                    onClick={() => {
                      trackEvent('create_new_plan', { previous_plan_id: activePlan?.id });
                      setBackupActivePlan(activePlan);
                      setBackupWorkouts(workouts);
                      setActivePlan(null);
                    }}
                  >
                    <Plus size={16} weight="bold" />
                    {lang === "en" ? "New Plan" : "Kế hoạch mới"}
                  </button>
                </div>
              ) : (
                <div style={{
                  background: "rgba(255, 255, 255, 0.95)",
                  border: "1px solid var(--border-color)",
                  padding: "12px",
                  borderRadius: "10px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px",
                  width: "100%",
                  boxShadow: "0 4px 12px rgba(0,0,0,0.05)"
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "12px", fontWeight: "600", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Select Preferred Workout Time:" : "Chọn thời gian tập ưa thích:"}
                    </span>
                    <button
                      type="button"
                      style={{ background: "none", border: "none", cursor: "pointer", fontSize: "12px", color: "var(--text-muted)" }}
                      onClick={() => setShowExportOptions(false)}
                    >✕</button>
                  </div>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <select
                      className="chat-input"
                      style={{ flex: 1, borderRadius: "6px", padding: "6px", height: "32px", fontSize: "12px" }}
                      value={exportTimePref}
                      onChange={(e) => setExportTimePref(e.target.value)}
                    >
                      <option value="all_day">{lang === "en" ? "All Day" : "Cả ngày"}</option>
                      <option value="morning">{lang === "en" ? "Morning" : "Buổi sáng"}</option>
                      <option value="afternoon">{lang === "en" ? "Afternoon" : "Buổi chiều"}</option>
                      <option value="evening">{lang === "en" ? "Evening" : "Buổi tối"}</option>
                    </select>
                    <a
                      href={`${API_BASE_URL}/api/coach/export-ics?plan_id=${activePlan.id}&race_date=${activePlan.race_date}&time_pref=${exportTimePref}&token=${typeof window !== 'undefined' ? localStorage.getItem('uphill_session_token') || '' : ''}`}
                      className="btn btn-primary"
                      style={{ fontSize: "12px", padding: "0 14px", height: "32px", display: "flex", alignItems: "center", textDecoration: "none", justifyContent: "center" }}
                      onClick={() => {
                        trackEvent('plan_exported', { plan_id: activePlan.id, export_format: 'ics', time_pref: exportTimePref });
                        setShowExportOptions(false);
                      }}
                    >
                      {lang === "en" ? "Add to Calendar (.ics)" : "Thêm vào Lịch (.ics)"}
                    </a>
                  </div>
                </div>
              )}
            </div>

            {/* Week Selector Tabs */}
            <div style={{ display: "flex", gap: "6px", overflowX: "auto", paddingBottom: "8px", marginBottom: "16px" }}>
              {Array.from({ length: activePlan.total_weeks }).map((_, i) => {
                const w = i + 1;
                const firstWo = workouts.find((wo: any) => wo.week_number === w);
                const phase = firstWo ? firstWo.phase : "Training";
                const active = selectedWeek === w;
                const phaseDisplay = lang === "vi"
                  ? phase.replace("Base", "Base").replace("Build", "Build").replace("Taper", "Taper").replace("Peak", "Peak").replace("Recovery", "Phục hồi").replace("Transition", "Chuyển đổi")
                  : phase;
                return (
                  <button
                    key={w}
                    className={`btn ${active ? "btn-primary" : "btn-secondary"}`}
                    style={{
                      padding: "6px 12px",
                      borderRadius: "8px",
                      flexShrink: 0,
                      fontSize: "12px",
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      gap: "1px",
                      minWidth: "60px",
                      height: "44px",
                      background: active ? "var(--accent-primary)" : "rgba(255,255,255,0.25)",
                      borderColor: active ? "var(--accent-primary)" : "var(--border-color)",
                      color: active ? "#ffffff" : "var(--text-primary)"
                    }}
                    onClick={() => setSelectedWeek(w)}
                  >
                    <span>{lang === "en" ? `Wk ${w}` : `Tuần ${w}`}</span>
                    <span style={{ fontSize: "9px", opacity: 0.7 }}>{phaseDisplay}</span>
                  </button>
                );
              })}
            </div>

            {/* Weekly Volume Stats */}
            {(() => {
              const weekWorkouts = getWeekWorkouts(selectedWeek);
              const weeklyKm = weekWorkouts.reduce((sum: any, wo: any) => sum + (wo.distance_km || 0), 0);
              const weeklyMins = weekWorkouts.reduce((sum: any, wo: any) => sum + (wo.duration_minutes || 0), 0);
              const weeklyHours = parseFloat((weeklyMins / 60).toFixed(1));

              return (
                <div style={{ marginBottom: "16px" }}>
                  <div className="card" style={{
                    padding: "12px 16px",
                    background: "rgba(255, 255, 255, 0.45)",
                    border: "1px solid var(--border-color)",
                    borderRadius: "12px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "4px"
                  }}>
                    <span style={{ fontSize: "10px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: "700" }}>
                      {lang === "en" ? `Weekly Volume (Wk ${selectedWeek})` : `Thể tích tuần (Tuần ${selectedWeek})`}
                    </span>
                    <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                      <span style={{ fontSize: "18px", fontWeight: "800", color: "var(--accent-primary)" }}>{weeklyKm.toFixed(1)} km</span>
                      <span style={{ fontSize: "13px", color: "var(--text-muted)", fontWeight: "600" }}>/ {weeklyHours} {lang === "en" ? "hrs" : "giờ"}</span>
                    </div>
                  </div>
                </div>
              );
            })()}



            {/* Week Workouts Grid */}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {getWeekWorkouts(selectedWeek).map((wo: any) => {
                const rest = wo.type === "Rest";
                const dayOfWeekShort = lang === "vi"
                  ? wo.day_of_week.replace("Monday", "T2").replace("Tuesday", "T3").replace("Wednesday", "T4").replace("Thursday", "T5").replace("Friday", "T6").replace("Saturday", "T7").replace("Sunday", "CN")
                  : wo.day_of_week.slice(0, 3);
                const woTypeTranslated = wo.type === "Rest" ? (lang === "en" ? "Rest" : "Nghỉ ngơi") : wo.type;

                return (
                  <div
                    key={wo.id}
                    style={{
                      background: rest ? "rgba(255,255,255,0.05)" : "var(--bg-card)",
                      backdropFilter: "blur(20px)",
                      WebkitBackdropFilter: "blur(20px)",
                      boxShadow: "inset 0 1px 0 rgba(255,255,255,0.4), 0 8px 24px rgba(0,0,0,0.05)",
                      border: "1px solid",
                      borderColor: wo.is_completed ? "var(--accent-success)" : "var(--border-color)",
                      borderRadius: "12px",
                      padding: isMobile ? "14px" : "20px",
                      opacity: rest ? 0.75 : 1,
                      display: "grid",
                      gridTemplateColumns: isMobile ? "1fr" : "70px 1.6fr 1.1fr",
                      gap: isMobile ? "10px" : "16px",
                      alignItems: "start",
                    }}
                  >
                    {/* Day name & Status Checkbox */}
                    <div style={{
                      display: "flex",
                      flexDirection: isMobile ? "row" : "column",
                      alignItems: "center",
                      justifyContent: isMobile ? "space-between" : "center",
                      textAlign: "center",
                      borderBottom: isMobile ? "1px solid rgba(0,0,0,0.05)" : "none",
                      paddingBottom: isMobile ? "8px" : 0,
                    }}>
                      <div style={{ display: "flex", gap: "8px", alignItems: "baseline" }}>
                        <span style={{ fontWeight: "700", fontSize: "15px" }}>{dayOfWeekShort}</span>
                        <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>{getWorkoutDate(wo)}</span>
                      </div>
                      {!rest && (
                        <input
                          type="checkbox"
                          style={{ width: "18px", height: "18px", accentColor: "var(--accent-success)", cursor: "pointer", margin: 0 }}
                          checked={wo.is_completed === 1}
                          onChange={(e) => handleToggleComplete(wo.id, e.target.checked)}
                        />
                      )}
                    </div>

                    {/* Workout Details */}
                    <div>
                      <div style={{ display: "flex", gap: "6px", alignItems: "center", flexWrap: "wrap", marginBottom: "6px" }}>
                        <h4 style={{ fontSize: isMobile ? "15px" : "17px", margin: 0 }}>{wo.title}</h4>
                        <span className="badge" style={{ margin: 0, fontSize: "9px", padding: "2px 6px" }}>{woTypeTranslated}</span>
                      </div>
                      <WorkoutDescription description={wo.description || ""} />
                      {wo.fueling_tip && (
                        <div style={{ background: "rgba(16, 185, 129, 0.03)", borderLeft: "2px solid var(--accent-primary)", padding: "6px 10px", borderRadius: "4px", fontSize: "12px" }}>
                          {wo.fueling_tip}
                        </div>
                      )}
                    </div>

                    {/* Target Metrics Column */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "12.5px" }}>
                      {wo.duration_minutes > 0 && (
                        <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(0,0,0,0.04)", paddingBottom: "4px" }}>
                          <span style={{ color: "var(--text-muted)", fontWeight: "600" }}>
                            {lang === "en" ? "Target Time:" : "Thời gian mục tiêu:"}
                          </span>
                          <span style={{ fontWeight: "700" }}>{wo.duration_minutes}m</span>
                        </div>
                      )}
                      {wo.distance_km !== undefined && wo.distance_km > 0 && (
                        <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(0,0,0,0.04)", paddingBottom: "4px" }}>
                          <span style={{ color: "var(--text-muted)", fontWeight: "600" }}>
                            {lang === "en" ? "Est. Dist:" : "Cự ly ước tính:"}
                          </span>
                          <span style={{ fontWeight: "700", color: "var(--accent-primary)" }}>{wo.distance_km}km</span>
                        </div>
                      )}
                      {wo.target_pace && wo.target_pace.trim() !== "" && (
                        <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(0,0,0,0.04)", paddingBottom: "4px" }}>
                          <span style={{ color: "var(--text-muted)", fontWeight: "600" }}>
                            {lang === "en" ? "Target Pace:" : "Pace mục tiêu:"}
                          </span>
                          <span style={{ fontWeight: "700", color: "var(--accent-success)" }}>{wo.target_pace}</span>
                        </div>
                      )}
                      {wo.target_hr_range && (
                        <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(0,0,0,0.04)", paddingBottom: "4px" }}>
                          <span style={{ color: "var(--text-muted)", fontWeight: "600" }}>
                            {lang === "en" ? "HR Limit:" : "Giới hạn HR:"}
                          </span>
                          <span style={{ fontWeight: "700", color: "var(--accent-secondary)" }}>{wo.target_hr_range}</span>
                        </div>
                      )}
                      {wo.treadmill_incline > 0 && (
                        <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                          <div style={{ display: "flex", justifyContent: "space-between" }}>
                            <span style={{ color: "var(--text-muted)", fontWeight: "600" }}>
                              {lang === "en" ? "Incline:" : "Độ dốc (Incline):"}
                            </span>
                            <span style={{ fontWeight: "700" }}>{wo.treadmill_incline}%</span>
                          </div>
                          <div style={{ display: "flex", justifyContent: "space-between" }}>
                            <span style={{ color: "var(--text-muted)", fontWeight: "600" }}>
                              {lang === "en" ? "Speed:" : "Tốc độ (Speed):"}
                            </span>
                            <span style={{ fontWeight: "700" }}>{wo.treadmill_speed}kph</span>
                          </div>
                        </div>
                      )}
                      {rest && (
                        <div style={{ display: "flex", justifyContent: "center", padding: "6px", background: "rgba(0,0,0,0.02)", borderRadius: "6px" }}>
                          <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                            {lang === "en" ? "Rest Day" : "Ngày nghỉ ngơi"}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderTools = (isMobile: boolean) => <ToolsView isMobile={isMobile} />;
