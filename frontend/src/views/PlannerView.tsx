/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect } from "react";
import { useAppContext } from "../contexts/AppContext";
import { usePlanner } from "../hooks/usePlanner";
import { translations } from "../app/translations";
import WorkoutCard from "../components/WorkoutCard";
import { KnowledgeCard } from "../components/KnowledgeCard";
import { DndContext, DragEndEvent, DragOverEvent, useDraggable, useDroppable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import ToolsView from "./ToolsView";
import { UploadSimple, FileArrowUp, Heart, Clock, Mountains, MapPin, Footprints, ArrowsMerge, PlayCircle, CheckCircle, Fire, Path, RoadHorizon, Info, Check, Question, WarningCircle, Plus, Trash, Archive, LockKey, LockKeyOpen, Trophy, Target, Sneaker, PersonSimpleRun, Bed, XCircle, DownloadSimple } from '@phosphor-icons/react';

export default function PlannerView({ isMobile }: { isMobile: boolean }) {
  const ctx = useAppContext();
  const { handleGeneratePlan, getPlanDistance, getPlanElevation, formatPlanName, handleSelectPlan, handleSwapWorkouts, swapDays, handleToggleComplete, handleLogWorkout, getWeekWorkouts, getWorkoutDate, handlePlannerGpxFileChange, plannerGpxInputRef, trackEvent, API_BASE_URL, fetchRecentPlansWithToken, startPlanJobPoller } = usePlanner();
  const { lang, activePlan, planLoading, planErrorMsg, planForm, setPlanForm, targetTimeH, setTargetTimeH, targetTimeM, setTargetTimeM, targetTimeS, setTargetTimeS, cutoffTimeH, setCutoffTimeH, cutoffTimeM, setCutoffTimeM, cutoffTimeS, setCutoffTimeS, recentPlans, selectedWeek, setSelectedWeek, swapDay1, setSwapDay1, swapDay2, setSwapDay2, setWorkouts, setBackupWorkouts, setActivePlan, workouts, backupWorkouts, backupActivePlan, setBackupActivePlan, courseInputMode, setCourseInputMode, plannerGpxLoading, plannerGpxFile, plannerGpxError, showExportOptions, setShowExportOptions, exportTimePref, setExportTimePref } = ctx;
  const t = (key: keyof typeof translations.en) => translations[lang]?.[key] || translations.en[key] || key;
  const totalWeeks = activePlan ? (activePlan.total_weeks || activePlan.plan_duration_weeks || 1) : 0;

  // ── Phase → knowledge card topic mapping ────────────────────────────────
  const phaseToTopic = (phase: string, daysToRace: number | null): string | null => {
    const p = phase.toLowerCase();
    if (daysToRace !== null && daysToRace < 0 && daysToRace >= -14) return "Recovery";
    if (daysToRace !== null && daysToRace >= 0 && daysToRace <= 14) return "Nutrition";
    if (p.includes("peak")) return "Mindset";
    if (p.includes("taper")) return "Pacing";
    if (p.includes("build")) return "Training";
    if (p.includes("base")) return "Training";
    if (p.includes("recovery")) return "Recovery";
    return null;
  };

  // ── Fetch a contextual knowledge card for this week's phase ─────────────
  const [contextCard, setContextCard] = useState<any>(null);
  useEffect(() => {
    if (!activePlan) { Promise.resolve().then(() => setContextCard(null)); return; }
    const weekWorkouts = getWeekWorkouts(selectedWeek);
    const phase = weekWorkouts[0]?.phase || "";
    let daysToRace: number | null = null;
    try {
      const [y, m, d] = activePlan.race_date.split("-").map(Number);
      const race = new Date(y, m - 1, d);
      daysToRace = Math.round((race.getTime() - new Date().getTime()) / 86400000);
    } catch { /* ignore */ }

    const topic = phaseToTopic(phase, daysToRace);
    if (!topic) { Promise.resolve().then(() => setContextCard(null)); return; }

    const token = typeof window !== "undefined" ? localStorage.getItem("uphill_session_token") : null;
    if (!token) return;
    fetch(`${API_BASE_URL}/api/knowledge/cards?topic=${topic}&lang=${lang}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        const cards: any[] = data?.cards || [];
        if (cards.length > 0) {
          setContextCard(cards[Math.floor(selectedWeek % cards.length)]);
        } else {
          setContextCard(null);
        }
      })
      .catch(() => setContextCard(null));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedWeek, activePlan?.id, lang]);

  // ── Coach contextual message ─────────────────────────────────────────────
  const getCoachMessage = () => {
    if (!activePlan) return null;
    const weekWorkouts = getWeekWorkouts(selectedWeek);
    const phase = (weekWorkouts[0]?.phase || "").toLowerCase();
    const raceName = activePlan.race_name || "your race";

    let daysToRace: number | null = null;
    try {
      const [y, m, d] = activePlan.race_date.split("-").map(Number);
      daysToRace = Math.round((new Date(y, m - 1, d).getTime() - new Date().getTime()) / 86400000);
    } catch { /* ignore */ }

    const v = selectedWeek % 3; // variant picker — cycles through message variants

    // Race-date-driven messages (highest priority)
    if (daysToRace !== null && daysToRace < 0 && daysToRace >= -14) {
      const msgs = lang === "en" ? [
        `You did it — ${raceName} is done. Rest, reflect, and let your body absorb everything you put into this block.`,
        `Race complete. Whatever the result, you showed up and crossed the line. Take the next two weeks easy — recovery is training.`,
        `${raceName} is behind you now. Celebrate properly, sleep deeply, and eat well. The next chapter starts after real recovery.`,
      ] : [
        `Bạn đã làm được — ${raceName} xong rồi. Nghỉ ngơi, suy ngẫm, và để cơ thể hấp thụ tất cả những gì bạn đã đầu tư.`,
        `Đua xong rồi. Dù kết quả thế nào, bạn đã xuất hiện và về đích. Hãy nhẹ nhàng hai tuần tới — hồi phục là huấn luyện.`,
      ];
      return { icon: "🎉", color: "#10b981", text: msgs[v % msgs.length] };
    }

    if (daysToRace !== null && daysToRace === 0) {
      const msgs = lang === "en" ? [
        `Race day. Everything you've done in training is already inside you. Go run your race.`,
        `Today is ${raceName}. Trust your preparation, run your own race, and enjoy every kilometre of it.`,
      ] : [
        `Ngày thi đấu rồi. Tất cả những gì bạn đã tập luyện đã ở trong bạn rồi. Hãy ra đường chạy đua.`,
      ];
      return { icon: "⚡", color: "#f59e0b", text: msgs[v % msgs.length] };
    }

    if (daysToRace !== null && daysToRace > 0 && daysToRace <= 7) {
      const msgs = lang === "en" ? [
        `Race week for ${raceName}. The hay is in the barn — your job now is to stay loose, sleep well, and trust the process.`,
        `${raceName} is ${daysToRace} day${daysToRace > 1 ? "s" : ""} away. Short, easy sessions only. Let your legs fill with spring.`,
        `You've put in the work for ${raceName}. This week: sleep, eat, stay calm. The fitness is already there.`,
      ] : [
        `Tuần đua ${raceName}. Công sức đã xong — giờ chỉ cần giữ người nhẹ nhàng, ngủ ngon, và tin vào quá trình.`,
        `${raceName} còn ${daysToRace} ngày nữa. Bài tập ngắn và nhẹ thôi. Để chân đầy lực.`,
      ];
      return { icon: "🏁", color: "#f59e0b", text: msgs[v % msgs.length] };
    }

    if (daysToRace !== null && daysToRace > 7 && daysToRace <= 14) {
      const msgs = lang === "en" ? [
        `Two weeks to ${raceName}. The taper is working — trust the lighter load even when your legs feel restless.`,
        `${raceName} is close. Resist the urge to cram in extra sessions. Your body is peaking right now.`,
      ] : [
        `Còn hai tuần đến ${raceName}. Giai đoạn taper đang có tác dụng — hãy tin vào lịch nhẹ hơn dù chân bứt rứt.`,
      ];
      return { icon: "🌊", color: "#3b82f6", text: msgs[v % msgs.length] };
    }

    // Phase-based messages
    if (phase.includes("peak")) {
      const msgs = lang === "en" ? [
        `Peak week. This is where fitness is forged under pressure. Go all in — then rest hard.`,
        `Your hardest week of the block. Every session counts. Run hard, sleep harder.`,
        `Peak training week for ${raceName}. What you do here is what you'll feel on race day.`,
      ] : [
        `Tuần đỉnh điểm. Đây là lúc thể lực được tôi luyện. Hết mình — rồi nghỉ thật sâu.`,
        `Tuần khó nhất của block. Mỗi buổi tập đều quan trọng. Tập mạnh, ngủ nhiều hơn.`,
      ];
      return { icon: "🔥", color: "#ef4444", text: msgs[v % msgs.length] };
    }

    if (phase.includes("taper")) {
      const msgs = lang === "en" ? [
        `Taper week. The hard work is banked — adding more now only hurts you. Trust the process.`,
        `Your body is absorbing everything you built. Resist the urge to run extra. Rest IS the training right now.`,
      ] : [
        `Tuần taper. Công sức đã tích lũy — thêm bài tập bây giờ chỉ gây hại. Hãy tin vào quá trình.`,
      ];
      return { icon: "🌊", color: "#3b82f6", text: msgs[v % msgs.length] };
    }

    if (phase.includes("build")) {
      const msgs = lang === "en" ? [
        `Build phase — the aerobic base is laid, now you're adding race-specific fitness on top. Quality over quantity.`,
        `You're in the build. Intensity is rising. Make your hard days hard and your easy days truly easy.`,
        `Build phase, week ${selectedWeek}. The gap between easy and hard sessions matters more than ever now.`,
      ] : [
        `Giai đoạn Build — nền tảng hiếu khí đã có, giờ thêm thể lực đặc thù. Chất lượng hơn số lượng.`,
      ];
      return { icon: "📈", color: "#8b5cf6", text: msgs[v % msgs.length] };
    }

    if (phase.includes("base")) {
      if (selectedWeek === 1) {
        const text = lang === "en"
          ? `Welcome to your ${activePlan.total_weeks}-week plan for ${raceName}. These first weeks build the aerobic foundation everything else sits on. Run easy, run often, and resist the urge to push.`
          : `Chào mừng bạn đến với kế hoạch ${activePlan.total_weeks} tuần cho ${raceName}. Những tuần đầu xây nền tảng hiếu khí. Chạy nhẹ, chạy đều, và đừng ép bản thân.`;
        return { icon: "🌱", color: "#10b981", text };
      }
      const msgs = lang === "en" ? [
        `Base phase — consistency beats intensity right now. Show up, run easy, let the aerobic engine grow.`,
        `You're building the engine. Zone 2 miles now mean faster miles later. Trust the boring work.`,
      ] : [
        `Giai đoạn Base — sự đều đặn quan trọng hơn cường độ. Xuất hiện, chạy nhẹ, để động cơ hiếu khí lớn lên.`,
      ];
      return { icon: "🌱", color: "#10b981", text: msgs[v % msgs.length] };
    }

    if (phase.includes("recovery")) {
      const msgs = lang === "en" ? [
        `Recovery week. Adaptation happens during rest, not training. Honor the lighter load — it's doing real work.`,
        `Deload week. Your body is consolidating the fitness from last block. Don't add extra — let it happen.`,
      ] : [
        `Tuần phục hồi. Thích nghi xảy ra khi nghỉ ngơi, không phải khi tập. Tôn trọng lịch nhẹ hơn.`,
      ];
      return { icon: "💧", color: "#6b7280", text: msgs[v % msgs.length] };
    }

    return null;
  };
  const coachMessage = getCoachMessage();

  // ── Block completion state ───────────────────────────────────────────────
  const [blockData, setBlockData] = useState<{ blocks: any[]; max_generated_week: number } | null>(null);
  const [showBlockReview, setShowBlockReview] = useState(false);
  const [blockReviewRpe, setBlockReviewRpe] = useState(5);
  const [blockReviewNotes, setBlockReviewNotes] = useState("");
  const [nextBlockLoading, setNextBlockLoading] = useState(false);

  const fetchBlockCompletion = React.useCallback(() => {
    if (!activePlan) return;
    const token = typeof window !== "undefined" ? localStorage.getItem("uphill_session_token") : null;
    if (!token) return;
    fetch(`${API_BASE_URL}/api/coach/block-completion/${activePlan.id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setBlockData(data); })
      .catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePlan?.id, API_BASE_URL]);

  useEffect(() => {
    if (!activePlan) { Promise.resolve().then(() => setBlockData(null)); return; }
    fetchBlockCompletion();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePlan?.id, fetchBlockCompletion]);

  // Derive directly from workouts so it updates immediately when setWorkouts() fires
  const maxGeneratedWeek = workouts.length > 0
    ? Math.max(...workouts.map((w: any) => w.week_number || 0))
    : 0;
  const currentBlockNum = maxGeneratedWeek > 0 ? Math.ceil(maxGeneratedWeek / 2) : 1;
  const currentBlockCompletion = blockData?.blocks?.find((b: any) => b.block_number === currentBlockNum);
  const blockUnlocked = currentBlockCompletion?.unlocked ?? false;
  const nextBlockNum = currentBlockNum + 1;
  const nextBlockStartWeek = nextBlockNum * 2 - 1;
  const allBlocksGenerated = maxGeneratedWeek >= totalWeeks && totalWeeks > 0;

  // Re-check block completion % whenever a workout is toggled
  const handleToggleCompleteWithRefresh = async (id: number, completed: boolean) => {
    await handleToggleComplete(id, completed);
    fetchBlockCompletion();
  };

  const handleGenerateNextBlock = async () => {
    if (!activePlan) return;
    setNextBlockLoading(true);
    const token = typeof window !== "undefined" ? localStorage.getItem("uphill_session_token") : null;
    if (!token) { setNextBlockLoading(false); return; }
    try {
      const resp = await fetch(`${API_BASE_URL}/api/coach/generate-next-block`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          plan_id: activePlan.id,
          block_number: nextBlockNum,
          overall_rpe: blockReviewRpe || null,
          notes: blockReviewNotes || null,
        }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "Failed to start next block generation");
      setShowBlockReview(false);
      setBlockReviewNotes("");
      setBlockReviewRpe(5);
      // Poll for completion
      startPlanJobPoller(data.job_id, token);
      // Re-fetch block data after poller finishes (via a small delay + re-fetch)
      const repoll = setInterval(() => {
        const tkn = localStorage.getItem("uphill_session_token");
        if (!tkn) { clearInterval(repoll); return; }
        fetch(`${API_BASE_URL}/api/coach/plan-status/${data.job_id}`, { headers: { Authorization: `Bearer ${tkn}` } })
          .then(r => r.ok ? r.json() : null)
          .then(d => { if (d?.status === "done" || d?.status === "error") { clearInterval(repoll); fetchBlockCompletion(); } })
          .catch(() => clearInterval(repoll));
      }, 5000);
    } catch (err: any) {
      alert(err.message || "Failed to generate next block");
    }
    setNextBlockLoading(false);
  };

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
                const isLocked = w > maxGeneratedWeek;
                const firstWo = workouts.find((wo: any) => wo.week_number === w);
                const phase = firstWo ? firstWo.phase : (isLocked ? "Locked" : "Training");
                const active = selectedWeek === w && !isLocked;
                const phaseDisplay = lang === "vi"
                  ? phase.replace("Base", "Base").replace("Build", "Build").replace("Taper", "Taper").replace("Peak", "Peak").replace("Recovery", "Phục hồi").replace("Transition", "Chuyển đổi").replace("Locked", "Chưa mở")
                  : phase;
                if (isLocked) {
                  return (
                    <div
                      key={w}
                      title={lang === "en" ? "Complete the current block to unlock" : "Hoàn thành block hiện tại để mở khóa"}
                      style={{
                        padding: "6px 12px", borderRadius: "8px", flexShrink: 0,
                        fontSize: "12px", display: "flex", flexDirection: "column",
                        alignItems: "center", gap: "1px", minWidth: "60px", height: "44px",
                        background: "rgba(0,0,0,0.04)", border: "1px dashed rgba(0,0,0,0.15)",
                        color: "var(--text-muted)", opacity: 0.55, cursor: "not-allowed",
                        userSelect: "none",
                      }}
                    >
                      <span style={{ fontSize: "11px" }}>🔒</span>
                      <span style={{ fontSize: "9px" }}>{lang === "en" ? `Week ${w}` : `Tuần ${w}`}</span>
                    </div>
                  );
                }
                return (
                  <button
                    key={w}
                    className={`btn ${active ? "btn-primary" : "btn-secondary"}`}
                    style={{
                      padding: "6px 12px", borderRadius: "8px", flexShrink: 0,
                      fontSize: "12px", display: "flex", flexDirection: "column",
                      alignItems: "center", gap: "1px", minWidth: "60px", height: "44px",
                      background: active ? "var(--accent-primary)" : "rgba(255,255,255,0.25)",
                      borderColor: active ? "var(--accent-primary)" : "var(--border-color)",
                      color: active ? "#ffffff" : "var(--text-primary)"
                    }}
                    onClick={() => setSelectedWeek(w)}
                  >
                    <span>{lang === "en" ? `Week ${w}` : `Tuần ${w}`}</span>
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
                      {lang === "en" ? `Weekly Volume (Week ${selectedWeek})` : `Thể tích tuần (Tuần ${selectedWeek})`}
                    </span>
                    <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                      <span style={{ fontSize: "18px", fontWeight: "800", color: "var(--accent-primary)" }}>{weeklyKm.toFixed(1)} km</span>
                      <span style={{ fontSize: "13px", color: "var(--text-muted)", fontWeight: "600" }}>/ {weeklyHours} {lang === "en" ? "hrs" : "giờ"}</span>
                    </div>
                  </div>
                </div>
              );
            })()}



            {/* Coach message for this week */}
            {coachMessage && (
              <div style={{
                display: "flex", alignItems: "flex-start", gap: "10px",
                padding: "12px 16px", borderRadius: "10px", marginBottom: "12px",
                background: `${coachMessage.color}10`,
                border: `1px solid ${coachMessage.color}30`,
              }}>
                <span style={{ fontSize: "18px", flexShrink: 0 }}>{coachMessage.icon}</span>
                <p style={{ fontSize: "13px", color: "var(--text-secondary)", margin: 0, lineHeight: "1.6", fontStyle: "italic" }}>
                  {coachMessage.text}
                </p>
              </div>
            )}

            {/* Generating plan skeleton */}
            {planLoading && workouts.length === 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <div style={{
                  display: "flex", alignItems: "center", gap: "14px",
                  padding: "20px 24px", borderRadius: "12px",
                  background: "linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.08))",
                  border: "1px solid rgba(139,92,246,0.2)",
                }}>
                  <div style={{ fontSize: "24px", animation: "spin 2s linear infinite", flexShrink: 0 }}>⚙️</div>
                  <div>
                    <div style={{ fontSize: "14px", fontWeight: "700", color: "var(--text-primary)", marginBottom: "3px" }}>
                      {lang === "en" ? "Generating your plan…" : "Đang tạo kế hoạch…"}
                    </div>
                    <div style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Coach Uphill is designing your workouts. This takes about 30–60 seconds." : "Coach Uphill đang thiết kế bài tập. Mất khoảng 30–60 giây."}
                    </div>
                  </div>
                </div>
                {/* Skeleton cards */}
                {[1, 2, 3].map((i) => (
                  <div key={i} style={{
                    height: "68px", borderRadius: "12px",
                    background: "rgba(0,0,0,0.04)",
                    border: "1px solid rgba(0,0,0,0.06)",
                    animation: `pulse 1.5s ease-in-out ${i * 0.2}s infinite`,
                  }} />
                ))}
              </div>
            ) : (
              /* Week Workouts — grouped by day with drag-and-drop swap */
              <WeekDayList
                weekWos={getWeekWorkouts(selectedWeek)}
                lang={lang}
                isMobile={isMobile}
                onSwapDays={swapDays}
                onToggleComplete={handleToggleCompleteWithRefresh}
                onLogWorkout={handleLogWorkout}
                getWorkoutDate={getWorkoutDate}
              />
            )}

            {/* Coach's pick — contextual knowledge card for this phase */}
            {contextCard && (
              <div style={{ marginTop: "20px", paddingTop: "16px", borderTop: "1px solid rgba(0,0,0,0.06)" }}>
                <p style={{ fontSize: "10px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 8px 2px" }}>
                  {lang === "en" ? "Coach's pick this week" : "Bài đọc Coach chọn tuần này"}
                </p>
                <KnowledgeCard card={contextCard} />
              </div>
            )}

            {/* Block Complete Banner */}
            {blockUnlocked && !allBlocksGenerated && !planLoading && (
              <div style={{
                marginTop: "20px",
                padding: "16px 20px",
                borderRadius: "14px",
                background: "linear-gradient(135deg, rgba(16,185,129,0.12), rgba(5,150,105,0.08))",
                border: "1.5px solid rgba(16,185,129,0.35)",
                display: "flex",
                flexDirection: "column",
                gap: "10px",
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{ fontSize: "22px" }}>🎉</span>
                  <div>
                    <div style={{ fontWeight: "800", fontSize: "14px", color: "var(--accent-primary)" }}>
                      {lang === "en"
                        ? `Block ${currentBlockNum} Complete! (${currentBlockCompletion?.completion_pct ?? 0}% done)`
                        : `Block ${currentBlockNum} hoàn thành! (${currentBlockCompletion?.completion_pct ?? 0}% xong)`}
                    </div>
                    <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "2px" }}>
                      {lang === "en"
                        ? `Weeks ${nextBlockStartWeek}–${Math.min(nextBlockStartWeek + 1, totalWeeks)} are ready to generate.`
                        : `Tuần ${nextBlockStartWeek}–${Math.min(nextBlockStartWeek + 1, totalWeeks)} sẵn sàng để tạo.`}
                    </div>
                  </div>
                </div>
                <button
                  className="btn btn-primary"
                  style={{ alignSelf: "flex-start", fontSize: "13px", height: "38px", paddingLeft: "20px", paddingRight: "20px", display: "flex", alignItems: "center", gap: "6px" }}
                  onClick={() => setShowBlockReview(true)}
                  disabled={nextBlockLoading}
                >
                  <span>⚡</span>
                  {nextBlockLoading
                    ? (lang === "en" ? "Generating..." : "Đang tạo...")
                    : (lang === "en" ? `Generate Block ${nextBlockNum}` : `Tạo Block ${nextBlockNum}`)}
                </button>
              </div>
            )}

            {/* All blocks generated message */}
            {allBlocksGenerated && !planLoading && totalWeeks > 0 && (
              <div style={{
                marginTop: "20px", padding: "14px 18px", borderRadius: "12px",
                background: "rgba(99,102,241,0.07)", border: "1px solid rgba(99,102,241,0.2)",
                fontSize: "13px", color: "var(--text-secondary)", display: "flex", gap: "10px", alignItems: "center",
              }}>
                <span style={{ fontSize: "20px" }}>✅</span>
                <span>
                  {lang === "en"
                    ? `All ${totalWeeks} weeks generated. Your full plan is ready — go get it!`
                    : `Đã tạo đủ ${totalWeeks} tuần. Kế hoạch của bạn đã sẵn sàng!`}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Block Review Modal */}
        {showBlockReview && (
          <div style={{
            position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)",
            zIndex: 1200, display: "flex", alignItems: "center", justifyContent: "center", padding: "24px",
          }}>
            <div style={{
              background: "rgba(255,255,255,0.97)", borderRadius: "18px",
              padding: "28px 24px", maxWidth: "420px", width: "100%",
              boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
            }}>
              <h3 style={{ margin: "0 0 4px", fontSize: "18px", fontWeight: "800" }}>
                {lang === "en" ? `How was Block ${currentBlockNum}?` : `Block ${currentBlockNum} như thế nào?`}
              </h3>
              <p style={{ fontSize: "13px", color: "var(--text-muted)", margin: "0 0 20px" }}>
                {lang === "en"
                  ? "Your feedback shapes the next 2 weeks of training."
                  : "Phản hồi của bạn sẽ định hình 2 tuần tập tiếp theo."}
              </p>

              <label style={{ display: "block", fontSize: "12px", fontWeight: "700", color: "var(--text-secondary)", marginBottom: "8px" }}>
                {lang === "en" ? `Overall Effort (RPE ${blockReviewRpe}/10)` : `Cảm giác chung (RPE ${blockReviewRpe}/10)`}
              </label>
              <div style={{ marginBottom: "6px" }}>
                <input
                  type="range" min={1} max={10} value={blockReviewRpe}
                  onChange={e => setBlockReviewRpe(Number(e.target.value))}
                  style={{ width: "100%", accentColor: "var(--accent-primary)" }}
                />
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>
                  <span>{lang === "en" ? "Very easy" : "Rất nhẹ"}</span>
                  <span>{lang === "en" ? "Max effort" : "Cực kỳ nặng"}</span>
                </div>
              </div>
              <div style={{
                textAlign: "center", fontSize: "12px", fontWeight: "600",
                color: blockReviewRpe >= 8 ? "#ef4444" : blockReviewRpe >= 6 ? "#f59e0b" : "#10b981",
                marginBottom: "18px",
              }}>
                {blockReviewRpe >= 9 ? (lang === "en" ? "Very hard — consider reducing next block" : "Rất nặng — cân nhắc giảm block tiếp")
                  : blockReviewRpe >= 7 ? (lang === "en" ? "Hard — coach will ease off slightly" : "Nặng — coach sẽ giảm nhẹ")
                  : blockReviewRpe >= 5 ? (lang === "en" ? "Manageable — good progression" : "Vừa phải — tiến độ tốt")
                  : (lang === "en" ? "Easy — coach can increase load" : "Nhẹ — coach có thể tăng tải")}
              </div>

              <label style={{ display: "block", fontSize: "12px", fontWeight: "700", color: "var(--text-secondary)", marginBottom: "6px" }}>
                {lang === "en" ? "Notes (optional)" : "Ghi chú (tùy chọn)"}
              </label>
              <textarea
                placeholder={lang === "en" ? "Any injuries, what worked, what didn't..." : "Chấn thương, điều hiệu quả, điều chưa tốt..."}
                value={blockReviewNotes}
                onChange={e => setBlockReviewNotes(e.target.value)}
                style={{
                  width: "100%", borderRadius: "10px", border: "1px solid var(--border-color)",
                  padding: "10px", fontSize: "13px", minHeight: "80px", resize: "vertical",
                  background: "rgba(0,0,0,0.03)", boxSizing: "border-box",
                  fontFamily: "inherit",
                }}
              />

              <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
                <button
                  type="button"
                  onClick={() => setShowBlockReview(false)}
                  style={{ flex: 1, height: "42px", borderRadius: "10px", border: "1px solid var(--border-color)", background: "rgba(0,0,0,0.04)", cursor: "pointer", fontSize: "13px" }}
                >
                  {lang === "en" ? "Cancel" : "Hủy"}
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  style={{ flex: 2, height: "42px", fontSize: "13px", fontWeight: "700" }}
                  onClick={handleGenerateNextBlock}
                  disabled={nextBlockLoading}
                >
                  {nextBlockLoading
                    ? (lang === "en" ? "Starting..." : "Đang bắt đầu...")
                    : (lang === "en" ? `⚡ Generate Block ${nextBlockNum}` : `⚡ Tạo Block ${nextBlockNum}`)}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderTools = (isMobile: boolean) => <ToolsView isMobile={isMobile} />;

// ─── Drag-and-drop day components ─────────────────────────────────────────────

const DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const DAY_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"];
const SLOT_ORDER: Record<string, number> = { morning: 0, main: 1, afternoon: 2 };

interface DayGroupProps {
  day: string;
  dayIndex: number;
  dayWos: any[];
  lang: string;
  isMobile: boolean;
  isOver: boolean;
  onToggleComplete: (id: number, completed: boolean) => void;
  onLogWorkout: (id: number, rpe: number | null, notes: string) => Promise<void>;
  getWorkoutDate: (wo: any) => string;
}

function DayGroup({ day, dayIndex, dayWos, lang, isMobile, isOver, onToggleComplete, onLogWorkout, getWorkoutDate }: DayGroupProps) {
  const { attributes, listeners, setNodeRef: setDragRef, transform, isDragging } = useDraggable({ id: day });
  const { setNodeRef: setDropRef } = useDroppable({ id: day });

  const style: React.CSSProperties = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.45 : 1,
    transition: isDragging ? undefined : "transform 150ms ease",
  };

  const containerStyle: React.CSSProperties = {
    borderRadius: "10px",
    padding: isOver ? "8px" : "0",
    background: isOver ? "rgba(16,185,129,0.06)" : "transparent",
    border: isOver ? "1.5px dashed rgba(16,185,129,0.4)" : "1.5px solid transparent",
    transition: "background 120ms, border 120ms, padding 120ms",
  };

  const isDoubleDay = dayWos.length >= 2;
  const dayKm = dayWos.reduce((s: number, w: any) => s + (w.distance_km || 0), 0);
  const dayMins = dayWos.reduce((s: number, w: any) => s + (w.duration_minutes || 0), 0);
  const dayHrs = (dayMins / 60).toFixed(1);
  const allRest = dayWos.every((w: any) => w.type === "Rest" || w.duration_minutes === 0);
  const dayLabel = lang === "vi" ? DAY_VI[dayIndex] : day;

  // Combine refs
  const setRef = (node: HTMLElement | null) => { setDragRef(node); setDropRef(node); };

  return (
    <div ref={setRef} style={{ ...style, ...containerStyle }}>
      {/* Day header — drag handle */}
      <div
        {...listeners}
        {...attributes}
        style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          marginBottom: "6px", paddingBottom: "5px",
          borderBottom: "1px solid rgba(0,0,0,0.06)",
          cursor: "grab", userSelect: "none",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "7px" }}>
          <span style={{ fontSize: "14px", color: "rgba(0,0,0,0.2)", flexShrink: 0, lineHeight: 1 }}>⠿</span>
          <span style={{ fontSize: "12px", fontWeight: "700", color: "var(--text-secondary)", letterSpacing: "0.02em" }}>
            {dayLabel.toUpperCase()}
          </span>
          {isDoubleDay && (
            <span style={{
              fontSize: "9px", fontWeight: "700", padding: "2px 6px", borderRadius: "99px",
              background: "rgba(16,185,129,0.12)", color: "var(--accent-primary)",
              border: "1px solid rgba(16,185,129,0.25)", letterSpacing: "0.03em",
            }}>
              {lang === "en" ? "2×" : "2 BUỔI"}
            </span>
          )}
        </div>
        {!allRest && (
          <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "500" }}>
            {dayKm > 0 ? `${dayKm.toFixed(1)} km · ` : ""}{dayHrs} {lang === "en" ? "h" : "giờ"}
          </span>
        )}
      </div>

      {/* Session cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {dayWos.map((wo: any) => {
          const slot = wo.session_slot ?? "main";
          const showSlotBadge = isDoubleDay && slot !== "main";
          return (
            <div key={wo.id}>
              {showSlotBadge && (
                <div style={{
                  fontSize: "10px", fontWeight: "700", marginBottom: "3px",
                  paddingLeft: "2px", color: slot === "morning" ? "#f59e0b" : "#6366f1",
                  display: "flex", alignItems: "center", gap: "4px",
                }}>
                  <span>{slot === "morning" ? "☀️" : "🌙"}</span>
                  <span>{slot === "morning"
                    ? (lang === "en" ? "MORNING SESSION" : "BUỔI SÁNG")
                    : (lang === "en" ? "AFTERNOON SESSION" : "BUỔI CHIỀU")
                  }</span>
                </div>
              )}
              <WorkoutCard
                wo={wo}
                isMobile={isMobile}
                lang={lang}
                onToggleComplete={onToggleComplete}
                onLogWorkout={onLogWorkout}
                getWorkoutDate={getWorkoutDate}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface WeekDayListProps {
  weekWos: any[];
  lang: string;
  isMobile: boolean;
  onSwapDays: (day1: string, day2: string) => void;
  onToggleComplete: (id: number, completed: boolean) => void;
  onLogWorkout: (id: number, rpe: number | null, notes: string) => Promise<void>;
  getWorkoutDate: (wo: any) => string;
}

function WeekDayList({ weekWos, lang, isMobile, onSwapDays, onToggleComplete, onLogWorkout, getWorkoutDate }: WeekDayListProps) {
  const [overId, setOverId] = React.useState<string | null>(null);

  const byDay: Record<string, any[]> = {};
  DAY_ORDER.forEach(d => { byDay[d] = []; });
  weekWos.forEach((wo: any) => {
    const d = wo.day_of_week || "Monday";
    if (!byDay[d]) byDay[d] = [];
    byDay[d].push(wo);
  });
  DAY_ORDER.forEach(d => {
    byDay[d].sort((a: any, b: any) => (SLOT_ORDER[a.session_slot ?? "main"] ?? 1) - (SLOT_ORDER[b.session_slot ?? "main"] ?? 1));
  });

  const handleDragOver = (event: DragOverEvent) => {
    setOverId(event.over ? String(event.over.id) : null);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    setOverId(null);
    const { active, over } = event;
    if (over && active.id !== over.id) {
      onSwapDays(String(active.id), String(over.id));
    }
  };

  return (
    <DndContext onDragOver={handleDragOver} onDragEnd={handleDragEnd}>
      <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        {DAY_ORDER.map((day, di) => {
          const dayWos = byDay[day];
          if (!dayWos || dayWos.length === 0) return null;
          return (
            <DayGroup
              key={day}
              day={day}
              dayIndex={di}
              dayWos={dayWos}
              lang={lang}
              isMobile={isMobile}
              isOver={overId === day}
              onToggleComplete={onToggleComplete}
              onLogWorkout={onLogWorkout}
              getWorkoutDate={getWorkoutDate}
            />
          );
        })}
      </div>
    </DndContext>
  );
}
