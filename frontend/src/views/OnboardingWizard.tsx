/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { useAppContext } from "../contexts/AppContext";
import { usePlanner } from "../hooks/usePlanner";
import { translations } from "../app/translations";
import { Calendar, PersonSimpleRun, Mountains, Watch, Target, CaretRight, CaretLeft, CaretDown, CaretUp, Plus, Info, X, Footprints, Lightning, Heartbeat , Trophy, Sneaker, Bed } from '@phosphor-icons/react';
import { RaceMatch } from "../hooks/useRaceMatch";
import { RaceNameField } from "../components/RaceNameField";
import { parsePaceToMinutes, formatDurationHM } from "../lib/paceStrategy";

export default function OnboardingWizard() {
  const ctx = useAppContext();
  const { startPlanJobPoller, fetchRecentPlansWithToken } = usePlanner();
  const fetchActivePlanWithToken = fetchRecentPlansWithToken; // just alias if needed or handle properly.
  const { activeTab, setActiveTab, lang, setLang, user, setUser, setActivePlan, setAuthErrorMsg, onboardingOpen, setOnboardingOpen, onboardingAnswers, setOnboardingAnswers, onboardingStep, setOnboardingStep, onboardingGenerating, setOnboardingGenerating, setIsGoalDeterminerOpen } = ctx;
  const [showFitnessWarning, setShowFitnessWarning] = React.useState(false);
  const handleRaceMatchChange = (match: RaceMatch | null) => {
    if (match?.elevation_gain_m && !onboardingAnswers.course_elevation_gain_m) {
      setOnboardingAnswers((prev: any) => ({ ...prev, course_elevation_gain_m: String(match.elevation_gain_m) }));
    }
  };
  const trackEvent = (name: string, props?: any) => { if (typeof window !== "undefined" && (window as any).posthog) { (window as any).posthog.capture(name, props); } };
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const t = (key: keyof typeof translations.en) => translations[lang]?.[key] || translations.en[key] || key;

  // ── "Optimal Performance": show (don't auto-apply) a computed target ────
  const [optimalEstimateMins, setOptimalEstimateMins] = React.useState<number | null>(null);
  const optimalEstimateAbortRef = React.useRef<AbortController | null>(null);
  React.useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setOptimalEstimateMins(null);
    if (onboardingAnswers.race_goal !== "optimal") return;
    const distanceKm = parseFloat(onboardingAnswers.course_distance_km) || null;
    if (!distanceKm || !onboardingAnswers.race_date) return;

    const profileZonePace = parsePaceToMinutes(onboardingAnswers.zone2_pace_max || "") ?? parsePaceToMinutes(onboardingAnswers.zone2_pace_min || "") ?? null;
    const profileBasePace = profileZonePace ? Math.round(profileZonePace * 0.95 * 100) / 100 : null;
    if (!profileBasePace) return;

    let weeksToRace: number | null = null;
    try {
      const [y, m, d] = onboardingAnswers.race_date.split("-").map(Number);
      const days = (new Date(y, m - 1, d).getTime() - new Date().getTime()) / 86400000;
      weeksToRace = Math.max(0, Math.round(days / 7));
    } catch { /* ignore */ }

    const timer = setTimeout(() => {
      optimalEstimateAbortRef.current?.abort();
      const controller = new AbortController();
      optimalEstimateAbortRef.current = controller;
      fetch(`${API_BASE_URL}/api/coach/goal-estimate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          race_name: onboardingAnswers.race_name || null,
          distance_km: distanceKm,
          elevation_gain_m: parseFloat(onboardingAnswers.course_elevation_gain_m) || 0,
          weeks_to_race: weeksToRace,
          flat_pace_min_km: profileBasePace,
        }),
        signal: controller.signal,
      })
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => setOptimalEstimateMins(data?.goals?.realistic ?? null))
        .catch((err) => {
          if (err?.name === "AbortError") return; // superseded by a newer request
          setOptimalEstimateMins(null);
        });
    }, 500);
    return () => {
      clearTimeout(timer);
      optimalEstimateAbortRef.current?.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onboardingAnswers.race_goal, onboardingAnswers.course_distance_km, onboardingAnswers.course_elevation_gain_m, onboardingAnswers.race_date, onboardingAnswers.race_name, onboardingAnswers.zone2_pace_min, onboardingAnswers.zone2_pace_max]);

  const handleCompleteOnboarding = async () => {

    const token = localStorage.getItem("uphill_session_token");

    if (!token || !user) return;

    setOnboardingGenerating(true);

    try {

      // Calculate age from DOB if provided

      let age = 30;

      if (onboardingAnswers.dob) {

        const born = new Date(onboardingAnswers.dob);

        age = Math.floor((Date.now() - born.getTime()) / (365.25 * 24 * 3600 * 1000));

      }

      const payload: any = {

        dob: onboardingAnswers.dob || null,

        age,

        goal_type: onboardingAnswers.goal_type,

        injury_history: onboardingAnswers.injury_history || null,

        preferred_run_days: onboardingAnswers.preferred_run_days,

        long_run_day: onboardingAnswers.long_run_day || "Saturday",

        days_per_week: onboardingAnswers.days_per_week || 4,

        current_weekly_km: parseFloat(onboardingAnswers.current_weekly_km) || 30.0,

        has_gym_access: onboardingAnswers.has_gym_access || false,

        training_environment: onboardingAnswers.training_environment || "flat",

        zone2_pace_min: onboardingAnswers.zone2_pace_min || "6:30",

        zone2_pace_max: onboardingAnswers.zone2_pace_max || "5:45",

        terrain: onboardingAnswers.terrain || "trail",

        time_away: onboardingAnswers.time_away || null,

        reason_for_break: onboardingAnswers.reason_for_break || null,

        fitness_feel: onboardingAnswers.fitness_feel || null,

        race_distance_completed: onboardingAnswers.race_distance_completed || null,

        days_since_race: onboardingAnswers.days_since_race ? parseInt(onboardingAnswers.days_since_race) : null,

        recovery_feel: onboardingAnswers.recovery_feel || null,

        next_goal: onboardingAnswers.next_goal || null,

        double_session_days: onboardingAnswers.double_session_days || [],

        lang: lang,

      };

      // HR zones

      if (onboardingAnswers.aet_hr) payload.aet_hr = parseInt(onboardingAnswers.aet_hr);

      if (onboardingAnswers.ant_hr) payload.ant_hr = parseInt(onboardingAnswers.ant_hr);

      if (onboardingAnswers.max_hr) payload.max_hr = parseInt(onboardingAnswers.max_hr);

      if (onboardingAnswers.resting_hr) payload.resting_hr = parseInt(onboardingAnswers.resting_hr);

      // Race/distance targets

      if (onboardingAnswers.race_name) payload.race_name = onboardingAnswers.race_name;

      if (onboardingAnswers.race_date) payload.race_date = onboardingAnswers.race_date;

      if (onboardingAnswers.course_distance_km) payload.course_distance_km = parseFloat(onboardingAnswers.course_distance_km);

      if (onboardingAnswers.course_elevation_gain_m) payload.course_elevation_gain_m = parseFloat(onboardingAnswers.course_elevation_gain_m);

      if (onboardingAnswers.plan_start_date) payload.plan_start_date = onboardingAnswers.plan_start_date;



      // Race goals

      payload.race_goal = onboardingAnswers.race_goal || "time";

      if (onboardingAnswers.race_goal === "time") {

        const hh = String(onboardingAnswers.expected_finish_hours || "0");

        const mm = String(onboardingAnswers.expected_finish_minutes || "0");

        payload.expected_finish_time = `${hh.padStart(2, '0')}:${mm.padStart(2, '0')}:00`;

      } else {

        payload.expected_finish_time = null;

      }



      const response = await fetch(`${API_BASE_URL}/api/auth/onboarding`, {

        method: "POST",

        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },

        body: JSON.stringify(payload),

      });

      if (!response.ok) throw new Error("Failed to complete onboarding.");

      const data = await response.json();

      // Update user immediately so the app is accessible

      if (data.user) setUser(data.user);

      if (data.plan) setActivePlan(data.plan);

      // Close onboarding and let user into the app right away

      setOnboardingOpen(false);

      setActiveTab("planner");

      // Start polling for plan generation in the background

      if (data.job_id) {

        startPlanJobPoller(data.job_id, token);

      }

    } catch (err: any) {

      setAuthErrorMsg(err.message || "Onboarding failed.");

    } finally {

      setOnboardingGenerating(false);

    }

  };


    if (!onboardingOpen || !user) return null;

    const DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];

    const goal = onboardingAnswers.goal_type;

    const isRaceOrDist = goal === "race" || goal === "distance";

    const isStart = goal === "start_running";

    const isReturn = goal === "return";

    const isRecovery = goal === "recovery";



    // Build steps array based on goal

    const steps = ["dob", "goal"];

    if (isRaceOrDist) steps.push("fitness", "injury", "target", "schedule", "double_session");

    else if (isStart) steps.push("fitness_start", "schedule", "double_session");

    else if (isReturn) steps.push("return_questions", "fitness_return", "schedule", "double_session");

    else if (isRecovery) steps.push("recovery_questions", "fitness_return", "schedule", "double_session");

    else if (!goal) { /* no extra steps yet */ }

    else steps.push("schedule", "double_session");

    steps.push("generate");



    const totalSteps = steps.length;

    const currentStepKey = steps[onboardingStep] || "dob";

    const inputS: React.CSSProperties = { borderRadius: "8px", width: "100%", height: "36px", margin: 0, padding: "0 10px", fontSize: "13px", background: "transparent", border: "1px solid var(--border-color)", color: "var(--text-primary)", boxSizing: "border-box" };

    const labelS: React.CSSProperties = { display: "block", fontSize: "12px", fontWeight: "600", color: "var(--text-muted)", marginBottom: "6px" };

    const optBtn = (val: string, label: string, emoji?: string): React.CSSProperties => ({

      padding: "10px 14px", borderRadius: "10px", border: `1.5px solid ${onboardingAnswers[currentStepKey === "goal" ? "goal_type" : currentStepKey] === val ? "var(--accent-primary)" : "var(--border-color)"}`,

      background: onboardingAnswers[currentStepKey === "goal" ? "goal_type" : currentStepKey] === val ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)",

      color: onboardingAnswers[currentStepKey === "goal" ? "goal_type" : currentStepKey] === val ? "var(--accent-primary)" : "var(--text-primary)",

      fontWeight: onboardingAnswers[currentStepKey === "goal" ? "goal_type" : currentStepKey] === val ? "700" : "500",

      fontSize: "13px", cursor: "pointer", textAlign: "center" as const, transition: "all 0.15s"

    });

    const setAns = (key: string, val: any) => setOnboardingAnswers((prev: any) => ({ ...prev, [key]: val }));

    const nextStep = () => setOnboardingStep((s: any) => Math.min(s + 1, totalSteps - 1));

    const prevStep = () => setOnboardingStep((s: any) => Math.max(s - 1, 0));

    // Intercept Next on fitness steps — show disclaimer popup when no real measurement provided.
    // Zone2 pace defaults ("8:30"/"6:30") are auto-set by the app, not user-measured, so they
    // count as "still at default". Only HR fields or a changed pace count as real input.
    const isFitnessStep = currentStepKey === "fitness_start" || currentStepKey === "fitness_return" || currentStepKey === "fitness";
    const DEFAULT_PACES = ["8:30", "7:30", "6:30", "5:45"];
    const fitnessDataIncomplete =
      !onboardingAnswers.aet_hr ||
      !onboardingAnswers.race_time_hours ||
      !onboardingAnswers.resting_hr ||
      !onboardingAnswers.zone2_pace_min || DEFAULT_PACES.includes(onboardingAnswers.zone2_pace_min) ||
      !onboardingAnswers.zone2_pace_max || DEFAULT_PACES.includes(onboardingAnswers.zone2_pace_max);
    const handleNextStep = () => {
      if (isFitnessStep && fitnessDataIncomplete) {
        setShowFitnessWarning(true);
      } else {
        nextStep();
      }
    };



    const toggleDay = (day: string) => {

      setOnboardingAnswers((prev: any) => {

        const days = [...(prev.preferred_run_days || [])];

        if (days.includes(day)) return { ...prev, preferred_run_days: days.filter(d => d !== day) };

        return { ...prev, preferred_run_days: [...days, day] };

      });

    };

    const toggleDoubleDay = (day: string) => {

      setOnboardingAnswers((prev: any) => {

        const days = [...(prev.double_session_days || [])];

        if (days.includes(day)) return { ...prev, double_session_days: days.filter(d => d !== day) };

        if (days.length >= 2) return prev; // max 2 double-session days

        return { ...prev, double_session_days: [...days, day] };

      });

    };



    const renderStep = () => {

      switch (currentStepKey) {

        case "dob":

          return (

            <div>

              <div style={{ fontSize: "22px", fontWeight: "800", marginBottom: "6px" }}>

                {lang === "en" ? `Welcome, ${user.name.split(" ")[0]}! 🎉` : `Chào mừng, ${user.name.split(" ")[0]}! 🎉`}

              </div>

              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "20px" }}>

                {lang === "en" ? "Let's set up your personalised training plan. First, select your language and when you were born." : "Hãy cùng thiết lập kế hoạch tập luyện cá nhân hóa của bạn. Đầu tiên, chọn ngôn ngữ của bạn và nhập ngày sinh."}

              </p>



              <div style={{ marginBottom: "20px" }}>

                <label style={labelS}>{lang === "en" ? "Language" : "Ngôn ngữ"}</label>

                <div style={{ display: "flex", background: "rgba(255,255,255,0.4)", border: "1px solid var(--border-color)", padding: "3px", borderRadius: "10px" }}>

                  {(["en", "vi"] as const).map(l => (

                    <button key={l} type="button" onClick={() => setLang(l)}

                      style={{ flex: 1, height: "30px", fontSize: "12px", borderRadius: "8px", border: "none", background: lang === l ? "var(--accent-primary)" : "transparent", color: lang === l ? "#fff" : "var(--text-secondary)", fontWeight: "600", cursor: "pointer", transition: "all 0.15s" }}>

                      {l === "en" ? "🇬🇧 English" : "🇻🇳 Tiếng Việt"}

                    </button>

                  ))}

                </div>

              </div>



              <div style={{ marginBottom: "10px" }}>

                <label style={labelS}>{t("onboard_dob")}</label>

                <input type="date" style={inputS} className="chat-input"
                  min="1924-01-01" max={new Date(new Date().getFullYear() - 10, 11, 31).toISOString().slice(0, 10)}
                  value={onboardingAnswers.dob}
                  onChange={e => {
                    setAns("dob", e.target.value);
                    setAns("dob_error", "");
                  }}
                  onBlur={e => {
                    const val = e.target.value;
                    const maxYear = new Date().getFullYear() - 10;
                    const year = val ? parseInt(val.slice(0, 4), 10) : 0;
                    if (val && (year < 1924 || year > maxYear)) {
                      setAns("dob_error", lang === "en" ? `Please enter a valid birth year (1924–${maxYear})` : `Vui lòng nhập năm sinh hợp lệ (1924–${maxYear})`);
                    } else {
                      setAns("dob_error", "");
                    }
                  }} />

                {onboardingAnswers.dob_error && (
                  <p style={{ fontSize: "12px", color: "#ef4444", marginTop: "6px", fontWeight: "600" }}>{onboardingAnswers.dob_error}</p>
                )}

                <p style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "8px" }}>

                  {lang === "en" ? "Used to estimate your maximum heart rate (220 − age)" : "Được sử dụng để ước tính nhịp tim tối đa của bạn (220 − số tuổi)"}

                </p>

              </div>

            </div>

          );

        case "goal":

          return (

            <div>

              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>

                {lang === "en" ? "What's your goal?" : "Mục tiêu của bạn là gì?"}

              </div>

              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "20px" }}>

                {lang === "en" ? "Your training plan will be designed specifically around this." : "Kế hoạch tập luyện của bạn sẽ được thiết kế riêng xung quanh mục tiêu này."}

              </p>

              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>

                {[

                  { val: "race", Icon: Trophy, label: lang === "en" ? "Race (target event)" : "Giải chạy (sự kiện mục tiêu)" },

                  { val: "distance", Icon: Target, label: lang === "en" ? "Run a Specific Distance" : "Chạy một cự ly cụ thể" },

                  { val: "start_running", Icon: Sneaker, label: lang === "en" ? "Start Running" : "Bắt đầu chạy bộ" },

                  { val: "return", Icon: PersonSimpleRun, label: lang === "en" ? "Get Back to Running" : "Tập luyện chạy bộ trở lại" },

                  { val: "recovery", Icon: Bed, label: lang === "en" ? "Post-Race Recovery" : "Phục hồi sau cuộc đua" },

                ].map(({ val, Icon, label }) => (

                  <button key={val} type="button"

                    onClick={() => {

                      setAns("goal_type", val);

                      if (val === "start_running") {

                        setAns("zone2_pace_min", "8:30");

                        setAns("zone2_pace_max", "7:30");

                      } else {

                        if (onboardingAnswers.zone2_pace_min === "8:30") setAns("zone2_pace_min", "6:30");

                        if (onboardingAnswers.zone2_pace_max === "7:30") setAns("zone2_pace_max", "5:45");

                      }

                    }}

                    style={{ ...optBtn(val, label), display: "flex", alignItems: "center", gap: "10px", textAlign: "left" as const }}>

                    <Icon size={24} color="var(--accent-primary)" weight="duotone" />

                    <span>{label}</span>

                    {onboardingAnswers.goal_type === val && <span style={{ marginLeft: "auto" }}>✓</span>}

                  </button>

                ))}

              </div>

            </div>

          );

        case "fitness":

          return (

            <div>

              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>

                {lang === "en" ? "Current Fitness 💓" : "Thể trạng hiện tại 💓"}

              </div>

              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "16px" }}>

                {lang === "en" ? "How would you like to input your heart rate zones?" : "Bạn muốn thiết lập các vùng nhịp tim của mình như thế nào?"}

              </p>

              <div style={{ display: "flex", background: "rgba(255,255,255,0.4)", border: "1px solid var(--border-color)", padding: "3px", borderRadius: "10px", marginBottom: "16px" }}>

                {(["estimate", "manual"] as const).map(m => (

                  <button key={m} type="button" onClick={() => setAns("fitness_input_mode", m)}

                    style={{ flex: 1, height: "30px", fontSize: "12px", borderRadius: "8px", border: "none", background: onboardingAnswers.fitness_input_mode === m ? "var(--accent-primary)" : "transparent", color: onboardingAnswers.fitness_input_mode === m ? "#fff" : "var(--text-secondary)", fontWeight: "600", cursor: "pointer" }}>

                    {m === "estimate"

                      ? (lang === "en" ? "⚡ Estimate from race" : "⚡ Ước tính từ giải chạy")

                      : (lang === "en" ? "🧪 I know my zones" : "🧪 Tôi đã biết các vùng nhịp tim")}

                  </button>

                ))}

              </div>

              {onboardingAnswers.fitness_input_mode === "estimate" ? (

                <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 1fr", gap: "8px" }}>

                  <div>

                    <label style={labelS}>{lang === "en" ? "Race Distance" : "Cự ly giải chạy"}</label>

                    <select className="chat-input" style={{ ...inputS }} value={onboardingAnswers.race_distance} onChange={e => setAns("race_distance", e.target.value)}>

                      <option value="5k">5k</option><option value="10k">10k</option><option value="half">Half Marathon</option><option value="marathon">Marathon</option>

                    </select>

                  </div>

                  <div><label style={labelS}>{lang === "en" ? "Hours" : "Giờ"}</label><input type="number" min="0" className="chat-input" style={inputS} value={onboardingAnswers.race_time_hours} onChange={e => setAns("race_time_hours", e.target.value)} /></div>

                  <div><label style={labelS}>{lang === "en" ? "Minutes" : "Phút"}</label><input type="number" min="0" max="59" className="chat-input" style={inputS} value={onboardingAnswers.race_time_minutes} onChange={e => setAns("race_time_minutes", e.target.value)} /></div>

                </div>

              ) : (

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>

                  <div><label style={labelS}>AeT HR (bpm)</label><input type="number" className="chat-input" style={inputS} placeholder="135" value={onboardingAnswers.aet_hr} onChange={e => setAns("aet_hr", e.target.value)} /></div>

                  <div><label style={labelS}>AnT HR (bpm)</label><input type="number" className="chat-input" style={inputS} placeholder="165" value={onboardingAnswers.ant_hr} onChange={e => setAns("ant_hr", e.target.value)} /></div>

                  <div><label style={labelS}>Max HR (bpm)</label><input type="number" className="chat-input" style={inputS} placeholder="185" value={onboardingAnswers.max_hr} onChange={e => setAns("max_hr", e.target.value)} /></div>

                  <div><label style={labelS}>Resting HR (bpm)</label><input type="number" className="chat-input" style={inputS} placeholder="60" value={onboardingAnswers.resting_hr} onChange={e => setAns("resting_hr", e.target.value)} /></div>

                </div>

              )}



              <div style={{ marginTop: "16px", borderTop: "1px solid var(--border-color)", paddingTop: "16px" }}>

                <label style={{ ...labelS, marginBottom: "8px" }}>

                  {lang === "en" ? "Zone 2 Pace Range (Aerobic Pacing)" : "Khoảng tốc độ Zone 2 (Tốc độ hiếu khí)"}

                </label>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>

                  <div>

                    <label style={{ ...labelS, fontSize: "11px", fontWeight: "normal" }}>{lang === "en" ? "Slowest Pace (min/km)" : "Tốc độ chậm nhất (phút/km)"}</label>

                    <input type="text" className="chat-input" style={inputS} placeholder="e.g. 6:30" value={onboardingAnswers.zone2_pace_min} onChange={e => setAns("zone2_pace_min", e.target.value)} />

                  </div>

                  <div>

                    <label style={{ ...labelS, fontSize: "11px", fontWeight: "normal" }}>{lang === "en" ? "Fastest Pace (min/km)" : "Tốc độ nhanh nhất (phút/km)"}</label>

                    <input type="text" className="chat-input" style={inputS} placeholder="e.g. 5:45" value={onboardingAnswers.zone2_pace_max} onChange={e => setAns("zone2_pace_max", e.target.value)} />

                  </div>

                </div>

                <p style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "6px", lineHeight: "1.3" }}>

                  {lang === "en" ? "This is your conversational running pace range." : "Đây là khoảng tốc độ chạy mà bạn vẫn có thể nói chuyện thoải mái."}

                </p>

              </div>

            </div>

          );

        case "injury":

          return (

            <div>

              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>

                {lang === "en" ? "Injury History 🩺" : "Lịch sử chấn thương 🩺"}

              </div>

              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "20px" }}>

                {lang === "en" ? "This helps us pace your plan's load progression carefully." : "Điều này giúp chúng tôi điều chỉnh tiến trình tăng tải của kế hoạch một cách cẩn thận."}

              </p>

              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>

                {[

                  { val: "rarely", label: lang === "en" ? "Rarely or never injured" : "Hiếm khi hoặc không bao giờ chấn thương", sub: lang === "en" ? "I bounce back quickly from hard efforts" : "Tôi phục hồi nhanh chóng sau những nỗ lực nặng" },

                  { val: "minor", label: lang === "en" ? "Minor or past significant injury" : "Chấn thương nhẹ hoặc từng bị chấn thương nặng", sub: lang === "en" ? "Mostly resolved, occasionally careful" : "Hầu như đã khỏi hoàn toàn, thỉnh thoảng cần lưu ý" },

                  { val: "frequent", label: lang === "en" ? "Frequently or recently injured" : "Thường xuyên hoặc mới bị chấn thương", sub: lang === "en" ? "Need careful, conservative buildup" : "Cần tích lũy khối lượng cẩn thận và thận trọng" },

                  { val: "prefer_not", label: lang === "en" ? "Prefer not to say" : "Không muốn chia sẻ", sub: "" },

                ].map(({ val, label, sub }) => (

                  <button key={val} type="button" onClick={() => setAns("injury_history", val)}

                    style={{ padding: "12px 14px", borderRadius: "10px", border: `1.5px solid ${onboardingAnswers.injury_history === val ? "var(--accent-primary)" : "var(--border-color)"}`, background: onboardingAnswers.injury_history === val ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", cursor: "pointer", textAlign: "left" as const }}>

                    <div style={{ fontWeight: "600", fontSize: "13px", color: onboardingAnswers.injury_history === val ? "var(--accent-primary)" : "var(--text-primary)" }}>{label}</div>

                    {sub && <div style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "3px" }}>{sub}</div>}

                  </button>

                ))}

              </div>

            </div>

          );

        case "target":

          return (

            <div>

              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>

                {goal === "race"

                  ? (lang === "en" ? "Race Details 🏁" : "Thông tin giải chạy 🏁")

                  : (lang === "en" ? "Distance Target 📏" : "Mục tiêu cự ly 📏")}

              </div>

              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "16px" }}>

                {goal === "race"

                  ? (lang === "en" ? "Tell us about the race you're training for." : "Hãy chia sẻ về giải chạy mà bạn đang chuẩn bị tham gia.")

                  : (lang === "en" ? "What distance are you aiming to run?" : "Cự ly nào mà bạn đang hướng tới?")}

              </p>

              {goal === "race" && (

                <div style={{ marginBottom: "10px" }}>

                  <label style={labelS}>{lang === "en" ? "Race Name" : "Tên giải chạy"}</label>

                  <RaceNameField
                    className="chat-input"
                    style={inputS}
                    placeholder="e.g. UTMB, Boston Marathon"
                    value={onboardingAnswers.race_name}
                    onChange={(v) => setAns("race_name", v)}
                    distanceKm={onboardingAnswers.course_distance_km}
                    lang={lang}
                    onMatchChange={handleRaceMatchChange}
                  />

                </div>

              )}

              {goal === "race" && (

                <div style={{ marginBottom: "10px" }}>

                  <label style={labelS}>{lang === "en" ? "Race Date" : "Ngày chạy"}</label>

                  <input type="date" className="chat-input" style={inputS} value={onboardingAnswers.race_date} onChange={e => setAns("race_date", e.target.value)} />

                </div>

              )}

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "10px" }}>

                <div><label style={labelS}>{lang === "en" ? "Distance (km)" : "Cự ly (km)"}</label><input type="number" className="chat-input" style={inputS} placeholder="42" value={onboardingAnswers.course_distance_km} onChange={e => setAns("course_distance_km", e.target.value)} /></div>

                <div><label style={labelS}>{lang === "en" ? "Elevation Gain (m)" : "Độ cao lũy kế (mét)"}</label><input type="number" className="chat-input" style={inputS} placeholder="1500" value={onboardingAnswers.course_elevation_gain_m} onChange={e => setAns("course_elevation_gain_m", e.target.value)} /></div>

              </div>

              <div style={{ marginTop: "12px" }}>

                <label style={labelS}>{lang === "en" ? "Terrain" : "Địa hình"}</label>

                <div style={{ display: "flex", gap: "8px" }}>

                  {["trail","road","mixed"].map(t => (

                    <button key={t} type="button" onClick={() => setAns("terrain", t)}

                      style={{ flex: 1, padding: "8px", borderRadius: "8px", border: `1.5px solid ${onboardingAnswers.terrain === t ? "var(--accent-primary)" : "var(--border-color)"}`, background: onboardingAnswers.terrain === t ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", color: onboardingAnswers.terrain === t ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: "600", fontSize: "12px", cursor: "pointer" }}>

                      {t === "trail" ? (lang === "en" ? "Trail" : "Địa hình") :

                       t === "road" ? (lang === "en" ? "Road" : "Đường bằng") :

                       (lang === "en" ? "Mixed" : "Hỗn hợp")}

                    </button>

                  ))}

                </div>

              </div>



              <div style={{ marginTop: "12px" }}>

                <label style={labelS}>{lang === "en" ? "Race Goal" : "Mục tiêu giải chạy"}</label>

                <div style={{ display: "flex", background: "rgba(255,255,255,0.4)", border: "1px solid var(--border-color)", padding: "3px", borderRadius: "10px", marginBottom: "10px" }}>

                  {[

                    { val: "finish", label: lang === "en" ? "Just Finish" : "Hoàn thành" },

                    { val: "time", label: lang === "en" ? "Time Target" : "Đạt mốc thời gian" },

                    { val: "optimal", label: t("plan_goal_optimal") }

                  ].map(({ val, label }) => (

                    <button key={val} type="button" onClick={() => setAns("race_goal", val)}

                      style={{ flex: 1, height: "30px", fontSize: "12px", borderRadius: "8px", border: "none", background: (onboardingAnswers.race_goal || "time") === val ? "var(--accent-primary)" : "transparent", color: (onboardingAnswers.race_goal || "time") === val ? "#fff" : "var(--text-secondary)", fontWeight: "600", cursor: "pointer" }}>

                      {label}

                    </button>

                  ))}

                </div>

              </div>



              {(onboardingAnswers.race_goal === "optimal") && optimalEstimateMins && (

                <div style={{ marginTop: "10px", fontSize: "12px", color: "var(--text-secondary)" }}>
                  {lang === "en"
                    ? `We'll target ~${formatDurationHM(optimalEstimateMins)} based on your current fitness.`
                    : `Chúng tôi sẽ nhắm mục tiêu ~${formatDurationHM(optimalEstimateMins)} dựa trên thể lực hiện tại của bạn.`}{" "}
                  <button type="button" onClick={() => setIsGoalDeterminerOpen(true)}
                    style={{ background: "none", border: "none", padding: 0, fontSize: "12px", fontWeight: 600, color: "var(--accent-primary)", cursor: "pointer", textDecoration: "underline" }}>
                    {lang === "en" ? "Refine in Goal Determiner →" : "Tinh chỉnh trong Xác định Mục tiêu →"}
                  </button>
                </div>

              )}



              {(onboardingAnswers.race_goal === "time") && (

                <div style={{ marginTop: "10px" }}>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "6px" }}>
                    <label style={labelS}>{lang === "en" ? "Expected Finish Time" : "Thời gian hoàn thành mục tiêu"}</label>
                    <button type="button" onClick={() => setIsGoalDeterminerOpen(true)}
                      style={{ background: "none", border: "none", padding: 0, fontSize: "11.5px", fontWeight: "600", color: "var(--accent-primary)", cursor: "pointer", textDecoration: "underline" }}>
                      {lang === "en" ? "Not sure? Use the Goal Determiner →" : "Chưa chắc? Dùng công cụ Xác định Mục tiêu →"}
                    </button>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>

                    <div>

                      <label style={{ ...labelS, fontSize: "11px", fontWeight: "normal" }}>{lang === "en" ? "Hours" : "Giờ"}</label>

                      <input type="number" min="0" className="chat-input" style={inputS} placeholder="4" value={onboardingAnswers.expected_finish_hours} onChange={e => setAns("expected_finish_hours", e.target.value)} />

                    </div>

                    <div>

                      <label style={{ ...labelS, fontSize: "11px", fontWeight: "normal" }}>{lang === "en" ? "Minutes" : "Phút"}</label>

                      <input type="number" min="0" max="59" className="chat-input" style={inputS} placeholder="30" value={onboardingAnswers.expected_finish_minutes} onChange={e => setAns("expected_finish_minutes", e.target.value)} />

                    </div>

                  </div>

                </div>

              )}

            </div>

          );

        case "return_questions":

          return (

            <div>

              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>

                {lang === "en" ? "Getting Back 🔄" : "Tập luyện trở lại 🔄"}

              </div>

              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "16px" }}>

                {lang === "en" ? "Help us understand where you're coming from." : "Giúp chúng tôi hiểu rõ hơn về tình trạng hiện tại của bạn."}

              </p>

              <div style={{ marginBottom: "12px" }}>

                <label style={labelS}>{lang === "en" ? "How long have you been away?" : "Bạn đã dừng chạy trong bao lâu?"}</label>

                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>

                  {["< 2 weeks","2–6 weeks","1–3 months","3–6 months","6+ months"].map(v => {

                    const label = lang === "vi"

                      ? v.replace("< 2 weeks", "< 2 tuần").replace("weeks", "tuần").replace("months", "tháng").replace("months+", "tháng trở lên")

                      : v;

                    return (

                      <button key={v} type="button" onClick={() => setAns("time_away", v)} style={{ padding: "8px 12px", borderRadius: "8px", border: `1.5px solid ${onboardingAnswers.time_away === v ? "var(--accent-primary)" : "var(--border-color)"}`, background: onboardingAnswers.time_away === v ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", color: onboardingAnswers.time_away === v ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: onboardingAnswers.time_away === v ? "700" : "500", fontSize: "12.5px", cursor: "pointer", textAlign: "left" as const }}>{label}</button>

                    );

                  })}

                </div>

              </div>

              <div style={{ marginBottom: "12px" }}>

                <label style={labelS}>{lang === "en" ? "How are you feeling now?" : "Cảm nhận hiện tại của bạn?"}</label>

                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>

                  {[

                    { val: "Feeling good, just need structure", en: "Feeling good, just need structure", vi: "Cảm thấy tốt, chỉ cần lịch trình tập" },

                    { val: "A bit rusty, slightly deconditioned", en: "A bit rusty, slightly deconditioned", vi: "Hơi uể oải, thể lực giảm nhẹ" },

                    { val: "Significant deconditioning — starting nearly fresh", en: "Significant deconditioning — starting nearly fresh", vi: "Giảm thể lực nghiêm trọng — bắt đầu lại gần như từ đầu" }

                  ].map(({ val, en, vi }) => (

                    <button key={val} type="button" onClick={() => setAns("fitness_feel", val)} style={{ padding: "8px 12px", borderRadius: "8px", border: `1.5px solid ${onboardingAnswers.fitness_feel === val ? "var(--accent-primary)" : "var(--border-color)"}`, background: onboardingAnswers.fitness_feel === val ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", color: onboardingAnswers.fitness_feel === val ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: onboardingAnswers.fitness_feel === val ? "700" : "500", fontSize: "12.5px", cursor: "pointer", textAlign: "left" as const }}>

                      {lang === "en" ? en : vi}

                    </button>

                  ))}

                </div>

              </div>

            </div>

          );

        case "recovery_questions":

          return (

            <div>

              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>

                {lang === "en" ? "Post-Race Recovery 💤" : "Phục hồi sau giải chạy 💤"}

              </div>

              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "16px" }}>

                {lang === "en" ? "Let's make sure you recover smart before the next build." : "Đảm bảo bạn phục hồi thông minh trước khi bắt đầu chu kỳ tập tiếp theo."}

              </p>

              <div style={{ marginBottom: "12px" }}>

                <label style={labelS}>{lang === "en" ? "What race did you complete?" : "Cự ly giải chạy bạn vừa hoàn thành?"}</label>

                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>

                  {["5k","10k","Half Marathon","Marathon","Ultra (< 60k)","Ultra (60k+)"].map(v => {

                    const label = lang === "vi" ? v.replace("Half Marathon", "Bán marathon").replace("Marathon", "Chạy marathon") : v;

                    return (

                      <button key={v} type="button" onClick={() => setAns("race_distance_completed", v)} style={{ padding: "7px 12px", borderRadius: "8px", border: `1.5px solid ${onboardingAnswers.race_distance_completed === v ? "var(--accent-primary)" : "var(--border-color)"}`, background: onboardingAnswers.race_distance_completed === v ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", color: onboardingAnswers.race_distance_completed === v ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: onboardingAnswers.race_distance_completed === v ? "700" : "500", fontSize: "12px", cursor: "pointer" }}>{label}</button>

                    );

                  })}

                </div>

              </div>

              <div style={{ marginBottom: "12px" }}>

                <label style={labelS}>{lang === "en" ? "Days since race" : "Số ngày kể từ giải chạy"}</label>

                <input type="number" min="0" className="chat-input" style={inputS} placeholder="e.g. 3" value={onboardingAnswers.days_since_race} onChange={e => setAns("days_since_race", e.target.value)} />

              </div>

              <div>

                <label style={labelS}>{lang === "en" ? "How are you feeling?" : "Bạn cảm thấy như thế nào?"}</label>

                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>

                  {[

                    { val: "Feeling great, minimal soreness", en: "Feeling great, minimal soreness", vi: "Khá tốt, mỏi cơ không đáng kể" },

                    { val: "Moderate fatigue, some soreness", en: "Moderate fatigue, some soreness", vi: "Mệt mỏi vừa phải, đau cơ nhẹ" },

                    { val: "Very fatigued — need real rest", en: "Very fatigued — need real rest", vi: "Rất mệt mỏi — cần nghỉ ngơi thực sự" }

                  ].map(({ val, en, vi }) => (

                    <button key={val} type="button" onClick={() => setAns("recovery_feel", val)} style={{ padding: "8px 12px", borderRadius: "8px", border: `1.5px solid ${onboardingAnswers.recovery_feel === val ? "var(--accent-primary)" : "var(--border-color)"}`, background: onboardingAnswers.recovery_feel === val ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", color: onboardingAnswers.recovery_feel === val ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: onboardingAnswers.recovery_feel === val ? "700" : "500", fontSize: "12.5px", cursor: "pointer", textAlign: "left" as const }}>

                      {lang === "en" ? en : vi}

                    </button>

                  ))}

                </div>

              </div>

            </div>

          );

        case "fitness_start": {

          const dobAge = onboardingAnswers.dob

            ? Math.floor((new Date().getTime() - new Date(onboardingAnswers.dob).getTime()) / (365.25 * 24 * 3600 * 1000))

            : null;

          const estMaxHR = dobAge ? 220 - dobAge : null;

          return (

            <div>

              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>

                {lang === "en" ? "Training Zones 💓" : "Vùng tập luyện 💓"}

              </div>

              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "16px" }}>

                {lang === "en"

                  ? "We'll set your zones from your age. Add your resting heart rate for better accuracy."

                  : "Chúng tôi sẽ thiết lập vùng nhịp tim từ tuổi của bạn. Thêm nhịp tim nghỉ ngơi để tăng độ chính xác."}

              </p>

              <div style={{ background: "rgba(59,130,246,0.08)", border: "1px solid rgba(59,130,246,0.2)", borderRadius: "10px", padding: "12px 14px", marginBottom: "16px" }}>

                <div style={{ fontSize: "11px", fontWeight: "700", color: "#3b82f6", letterSpacing: "0.05em", marginBottom: "4px" }}>

                  {lang === "en" ? "ESTIMATED FROM AGE" : "ƯỚC TÍNH TỪ TUỔI"}

                </div>

                {estMaxHR ? (

                  <div style={{ fontSize: "14px", fontWeight: "600", color: "var(--text-primary)" }}>

                    {lang === "en"

                      ? `Max HR ≈ ${estMaxHR} bpm (220 − ${dobAge})`

                      : `Nhịp tim tối đa ≈ ${estMaxHR} bpm (220 − ${dobAge})`}

                  </div>

                ) : (

                  <div style={{ fontSize: "12.5px", color: "var(--text-muted)" }}>

                    {lang === "en"

                      ? "Add your date of birth in step 1 to get a personalised estimate."

                      : "Thêm ngày sinh ở bước 1 để có ước tính cá nhân hóa."}

                  </div>

                )}

              </div>

              <div style={{ marginBottom: "14px" }}>

                <label style={labelS}>{lang === "en" ? "Resting Heart Rate (optional)" : "Nhịp tim nghỉ ngơi (tùy chọn)"}</label>

                <input type="number" className="chat-input" style={inputS} placeholder={lang === "en" ? "e.g. 55" : "ví dụ 55"} value={onboardingAnswers.resting_hr || ""} onChange={e => setAns("resting_hr", e.target.value)} />

                <p style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "5px", margin: "5px 0 0 0" }}>

                  {lang === "en"

                    ? "Check your watch's morning HR reading. Improves zone accuracy."

                    : "Kiểm tra đồng hồ sau khi thức dậy. Cải thiện độ chính xác của vùng nhịp tim."}

                </p>

              </div>

              <div style={{ borderTop: "1px solid var(--border-color)", paddingTop: "14px" }}>

                <label style={{ ...labelS, marginBottom: "8px" }}>

                  {lang === "en" ? "Easy Run Pace (optional)" : "Tốc độ chạy dễ (tùy chọn)"}

                </label>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>

                  <div>

                    <label style={{ ...labelS, fontSize: "11px", fontWeight: "normal" }}>{lang === "en" ? "Slowest (min/km)" : "Chậm nhất (phút/km)"}</label>

                    <input type="text" className="chat-input" style={inputS} placeholder="8:30" value={onboardingAnswers.zone2_pace_min || ""} onChange={e => setAns("zone2_pace_min", e.target.value)} />

                  </div>

                  <div>

                    <label style={{ ...labelS, fontSize: "11px", fontWeight: "normal" }}>{lang === "en" ? "Fastest (min/km)" : "Nhanh nhất (phút/km)"}</label>

                    <input type="text" className="chat-input" style={inputS} placeholder="7:30" value={onboardingAnswers.zone2_pace_max || ""} onChange={e => setAns("zone2_pace_max", e.target.value)} />

                  </div>

                </div>

              </div>

            </div>

          );

        }

        case "fitness_return": {

          return (

            <div>

              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>

                {lang === "en" ? "Current Fitness 💓" : "Thể trạng hiện tại 💓"}

              </div>

              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "2px" }}>

                {lang === "en"

                  ? "Helps us set your training zones accurately."

                  : "Giúp chúng tôi thiết lập vùng tập luyện của bạn chính xác hơn."}

              </p>

              <p style={{ color: "var(--text-muted)", fontSize: "12px", fontStyle: "italic", marginBottom: "16px" }}>

                {lang === "en" ? "Optional — tap Next to skip and add this later." : "Tùy chọn — nhấn Tiếp theo để bỏ qua và thêm sau."}

              </p>

              <div style={{ display: "flex", background: "rgba(255,255,255,0.4)", border: "1px solid var(--border-color)", padding: "3px", borderRadius: "10px", marginBottom: "16px" }}>

                {(["estimate", "manual"] as const).map(m => (

                  <button key={m} type="button" onClick={() => setAns("fitness_input_mode", m)}

                    style={{ flex: 1, height: "30px", fontSize: "12px", borderRadius: "8px", border: "none", background: onboardingAnswers.fitness_input_mode === m ? "var(--accent-primary)" : "transparent", color: onboardingAnswers.fitness_input_mode === m ? "#fff" : "var(--text-secondary)", fontWeight: "600", cursor: "pointer" }}>

                    {m === "estimate"

                      ? (lang === "en" ? "⚡ Estimate from race" : "⚡ Ước tính từ giải chạy")

                      : (lang === "en" ? "🧪 I know my zones" : "🧪 Tôi đã biết vùng nhịp tim")}

                  </button>

                ))}

              </div>

              {onboardingAnswers.fitness_input_mode === "estimate" && (

                <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 1fr", gap: "8px", marginBottom: "14px" }}>

                  <div>

                    <label style={labelS}>{lang === "en" ? "Race Distance" : "Cự ly giải chạy"}</label>

                    <select className="chat-input" style={{ ...inputS }} value={onboardingAnswers.race_distance || "10k"} onChange={e => setAns("race_distance", e.target.value)}>

                      <option value="5k">5k</option>

                      <option value="10k">10k</option>

                      <option value="half">Half Marathon</option>

                      <option value="marathon">Marathon</option>

                    </select>

                  </div>

                  <div><label style={labelS}>{lang === "en" ? "Hours" : "Giờ"}</label><input type="number" min="0" className="chat-input" style={inputS} value={onboardingAnswers.race_time_hours || ""} onChange={e => setAns("race_time_hours", e.target.value)} /></div>

                  <div><label style={labelS}>{lang === "en" ? "Minutes" : "Phút"}</label><input type="number" min="0" max="59" className="chat-input" style={inputS} value={onboardingAnswers.race_time_minutes || ""} onChange={e => setAns("race_time_minutes", e.target.value)} /></div>

                </div>

              )}

              {onboardingAnswers.fitness_input_mode === "manual" && (

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "14px" }}>

                  <div><label style={labelS}>AeT HR (bpm)</label><input type="number" className="chat-input" style={inputS} placeholder="135" value={onboardingAnswers.aet_hr || ""} onChange={e => setAns("aet_hr", e.target.value)} /></div>

                  <div><label style={labelS}>AnT HR (bpm)</label><input type="number" className="chat-input" style={inputS} placeholder="165" value={onboardingAnswers.ant_hr || ""} onChange={e => setAns("ant_hr", e.target.value)} /></div>

                  <div><label style={labelS}>Max HR (bpm)</label><input type="number" className="chat-input" style={inputS} placeholder="185" value={onboardingAnswers.max_hr || ""} onChange={e => setAns("max_hr", e.target.value)} /></div>

                  <div><label style={labelS}>Resting HR (bpm)</label><input type="number" className="chat-input" style={inputS} placeholder="60" value={onboardingAnswers.resting_hr || ""} onChange={e => setAns("resting_hr", e.target.value)} /></div>

                </div>

              )}

              {onboardingAnswers.fitness_input_mode && (

                <div style={{ borderTop: "1px solid var(--border-color)", paddingTop: "14px" }}>

                  <label style={{ ...labelS, marginBottom: "8px" }}>

                    {lang === "en" ? "Zone 2 Pace Range" : "Khoảng tốc độ Zone 2"}

                  </label>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>

                    <div>

                      <label style={{ ...labelS, fontSize: "11px", fontWeight: "normal" }}>{lang === "en" ? "Slowest (min/km)" : "Chậm nhất (phút/km)"}</label>

                      <input type="text" className="chat-input" style={inputS} placeholder="6:30" value={onboardingAnswers.zone2_pace_min || ""} onChange={e => setAns("zone2_pace_min", e.target.value)} />

                    </div>

                    <div>

                      <label style={{ ...labelS, fontSize: "11px", fontWeight: "normal" }}>{lang === "en" ? "Fastest (min/km)" : "Nhanh nhất (phút/km)"}</label>

                      <input type="text" className="chat-input" style={inputS} placeholder="5:45" value={onboardingAnswers.zone2_pace_max || ""} onChange={e => setAns("zone2_pace_max", e.target.value)} />

                    </div>

                  </div>

                </div>

              )}

            </div>

          );

        }

        case "schedule":

          return (

            <div>

              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>

                {lang === "en" ? "Your Schedule 📅" : "Lịch tập của bạn 📅"}

              </div>

              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "16px" }}>

                {lang === "en" ? "We'll build your plan around your availability." : "Chúng tôi sẽ xây dựng kế hoạch quanh thời gian rảnh của bạn."}

              </p>

              <div style={{ marginBottom: "14px" }}>

                <label style={labelS}>{lang === "en" ? "Days per week" : "Số ngày mỗi tuần"}</label>

                <div style={{ display: "flex", gap: "6px" }}>

                  {[3,4,5,6,7].map(n => (

                    <button key={n} type="button" onClick={() => setAns("days_per_week", n)} style={{ flex: 1, padding: "8px", borderRadius: "8px", border: `1.5px solid ${onboardingAnswers.days_per_week === n ? "var(--accent-primary)" : "var(--border-color)"}`, background: onboardingAnswers.days_per_week === n ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", color: onboardingAnswers.days_per_week === n ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: "600", fontSize: "14px", cursor: "pointer" }}>{n}</button>

                  ))}

                </div>

              </div>

              <div style={{ marginBottom: "14px" }}>

                <label style={labelS}>Which days can you run?</label>

                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>

                  {DAYS.map(day => {

                    const sel = (onboardingAnswers.preferred_run_days || []).includes(day);

                    return (

                      <button key={day} type="button" onClick={() => toggleDay(day)} style={{ padding: "6px 10px", borderRadius: "8px", border: `1.5px solid ${sel ? "var(--accent-primary)" : "var(--border-color)"}`, background: sel ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", color: sel ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: sel ? "700" : "500", fontSize: "12px", cursor: "pointer" }}>{day.slice(0,3)}</button>

                    );

                  })}

                </div>

              </div>

              <div style={{ marginBottom: "14px" }}>

                <label style={labelS}>Long run day</label>

                <select className="chat-input" style={inputS} value={onboardingAnswers.long_run_day} onChange={e => setAns("long_run_day", e.target.value)}>

                  {DAYS.map(d => <option key={d} value={d}>{d}</option>)}

                </select>

              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "14px" }}>

                <div><label style={labelS}>Current weekly km</label><input type="number" className="chat-input" style={inputS} placeholder="30" value={onboardingAnswers.current_weekly_km} onChange={e => setAns("current_weekly_km", e.target.value)} /></div>

                <div style={{ display: "flex", flexDirection: "column", justifyContent: "flex-end" }}>

                  <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", fontSize: "12.5px", color: "var(--text-primary)", paddingBottom: "4px" }}>

                    <input type="checkbox" checked={onboardingAnswers.has_gym_access} onChange={e => setAns("has_gym_access", e.target.checked)} style={{ width: "16px", height: "16px", accentColor: "var(--accent-primary)" }} />

                    Gym / Treadmill access?

                  </label>

                </div>

              </div>

              <div style={{ marginBottom: "14px" }}>

                <label style={labelS}>{lang === "en" ? "Training environment" : "Môi trường tập luyện"}</label>

                <div style={{ display: "flex", gap: "6px" }}>

                  {(["flat", "hilly", "mixed"] as const).map(env => {

                    const selected = onboardingAnswers.training_environment === env;

                    const envLabel = lang === "en"
                      ? { flat: "Flat", hilly: "Hilly", mixed: "Mixed" }[env]
                      : { flat: "Bằng phẳng", hilly: "Nhiều đồi dốc", mixed: "Kết hợp" }[env];

                    return (
                      <button key={env} type="button" onClick={() => setAns("training_environment", env)}
                        style={{ flex: 1, padding: "8px 0", borderRadius: "8px", border: `1.5px solid ${selected ? "var(--accent-primary)" : "var(--border-color)"}`, background: selected ? "rgba(16,185,129,0.1)" : "transparent", color: selected ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: selected ? "700" : "500", fontSize: "12.5px", cursor: "pointer" }}
                      >{envLabel}</button>
                    );

                  })}

                </div>

                <p style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "5px", margin: "5px 0 0 0" }}>

                  {lang === "en"
                    ? "Whether Hill Sprint sessions can be prescribed depends on this and your treadmill access."
                    : "Việc có được xếp bài Hill Sprint (chạy dốc) hay không phụ thuộc vào lựa chọn này và việc bạn có máy chạy bộ hay không."}

                </p>

              </div>

              <div>

                <label style={labelS}>{lang === "en" ? "Plan Start Date" : "Ngày bắt đầu kế hoạch"}</label>

                <input type="date" className="chat-input" style={inputS} value={onboardingAnswers.plan_start_date} onChange={e => setAns("plan_start_date", e.target.value)} />

                <p style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "5px", margin: "5px 0 0 0" }}>

                  {lang === "en" ? "Week 1 of your plan will begin from this date." : "Tuần 1 của kế hoạch sẽ bắt đầu từ ngày này."}

                </p>

              </div>

            </div>

          );

        case "double_session": {

          const preferredDays = onboardingAnswers.preferred_run_days || DAYS;

          const selectedDouble = onboardingAnswers.double_session_days || [];

          return (

            <div>

              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>

                {lang === "en" ? "Double Session Days ⚡" : "Ngày tập hai buổi ⚡"}

              </div>

              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "4px" }}>

                {lang === "en"

                  ? "On double-session days, Coach Uphill can schedule a short morning activation + an afternoon quality session."

                  : "Vào ngày tập hai buổi, Coach Uphill sẽ xếp buổi sáng ngắn + buổi chiều chất lượng cao."}

              </p>

              <p style={{ color: "var(--text-muted)", fontSize: "12px", fontStyle: "italic", marginBottom: "20px" }}>

                {lang === "en" ? "Optional — skip if you prefer one session per day." : "Tùy chọn — bỏ qua nếu bạn chỉ muốn một buổi mỗi ngày."}

              </p>

              <div style={{ marginBottom: "16px" }}>

                <label style={{ ...labelS, marginBottom: "10px" }}>

                  {lang === "en" ? "Pick up to 2 days (from your available days)" : "Chọn tối đa 2 ngày (từ ngày bạn có thể chạy)"}

                </label>

                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>

                  {preferredDays.map((day: string) => {

                    const sel = selectedDouble.includes(day);

                    const disabled = !sel && selectedDouble.length >= 2;

                    return (

                      <button

                        key={day}

                        type="button"

                        onClick={() => !disabled && toggleDoubleDay(day)}

                        style={{

                          padding: "8px 14px",

                          borderRadius: "8px",

                          border: `1.5px solid ${sel ? "var(--accent-primary)" : "var(--border-color)"}`,

                          background: sel ? "rgba(16,185,129,0.12)" : disabled ? "rgba(255,255,255,0.1)" : "rgba(255,255,255,0.3)",

                          color: sel ? "var(--accent-primary)" : disabled ? "var(--text-muted)" : "var(--text-primary)",

                          fontWeight: sel ? "700" : "500",

                          fontSize: "13px",

                          cursor: disabled ? "not-allowed" : "pointer",

                          opacity: disabled ? 0.5 : 1,

                        }}

                      >

                        {day.slice(0, 3)}

                        {sel && <span style={{ marginLeft: "4px", fontSize: "11px" }}>⚡</span>}

                      </button>

                    );

                  })}

                </div>

              </div>

              {selectedDouble.length > 0 && (

                <div style={{ background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.3)", borderRadius: "10px", padding: "12px 14px", fontSize: "12.5px", color: "var(--text-muted)" }}>

                  {lang === "en"

                    ? `Double sessions on: ${selectedDouble.join(", ")}. Coach will add a short morning activation (20–30 min) + main session in afternoon.`

                    : `Tập hai buổi vào: ${selectedDouble.join(", ")}. Coach sẽ thêm buổi sáng ngắn (20–30 phút) + buổi chiều chính.`}

                </div>

              )}

            </div>

          );

        }

        case "generate":

          return (

            <div style={{ textAlign: "center", padding: "20px 0" }}>

              {onboardingGenerating ? (

                <>

                  <div style={{ fontSize: "40px", marginBottom: "16px", animation: "spin 2s linear infinite" }}>⚙️</div>

                  <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "8px" }}>

                    {lang === "en" ? "Building your plan..." : "Đang tạo kế hoạch..."}

                  </div>

                  <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>

                    {lang === "en"

                      ? "Coach Uphill is crafting a personalised training plan based on your profile. This may take 30–60 seconds."

                      : "Coach Uphill đang chuẩn bị kế hoạch tập luyện cá nhân hóa của bạn. Quá trình này có thể mất 30–60 giây."}

                  </p>

                </>

              ) : (

                <>

                  <div style={{ fontSize: "40px", marginBottom: "16px" }}>✨</div>

                  <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "8px" }}>

                    {lang === "en" ? "You're all set!" : "Tất cả đã sẵn sàng!"}

                  </div>

                  <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "16px" }}>

                    {lang === "en"

                      ? `Ready to generate your personalised ${onboardingAnswers.goal_type?.replace("_"," ")} training plan?`

                      : `Bạn đã sẵn sàng khởi tạo kế hoạch tập luyện ${onboardingAnswers.goal_type?.replace("_"," ")} cá nhân hóa chưa?`}

                  </p>

                  <div style={{ background: "rgba(16,185,129,0.06)", border: "1px solid rgba(16,185,129,0.15)", borderRadius: "12px", padding: "14px", marginBottom: "20px", textAlign: "left" }}>

                    <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "6px", fontWeight: "600" }}>

                      {lang === "en" ? "SUMMARY" : "BẢN TỔNG HỢP"}

                    </div>

                    <div style={{ fontSize: "13px", display: "flex", flexDirection: "column", gap: "4px" }}>

                      <div>{lang === "en" ? "Goal:" : "Mục tiêu:"} <strong>{onboardingAnswers.goal_type?.replace("_"," ")}</strong></div>

                      <div>{lang === "en" ? "Starts:" : "Bắt đầu:"} <strong>{onboardingAnswers.plan_start_date || "Today"}</strong> · {onboardingAnswers.days_per_week || 4} {lang === "en" ? "days/week" : "ngày/tuần"}</div>

                      <div>🌙 {lang === "en" ? "Long run:" : "Chạy dài:"} <strong>{onboardingAnswers.long_run_day}</strong> · {lang === "en" ? "Volume:" : "Thể tích:"} <strong>{onboardingAnswers.current_weekly_km || 30} km/{lang === "en" ? "wk" : "tuần"}</strong></div>

                      {onboardingAnswers.race_name && <div>🏁 {lang === "en" ? "Race:" : "Giải chạy:"} <strong>{onboardingAnswers.race_name}</strong></div>}

                    </div>

                  </div>

                  <button className="btn btn-primary" style={{ width: "100%", height: "44px", fontSize: "14px", fontWeight: "700" }} onClick={handleCompleteOnboarding}>

                    🚀 {lang === "en" ? "Generate My Training Plan" : "Khởi tạo Kế hoạch Tập luyện Của Tôi"}

                  </button>

                </>

              )}

            </div>

          );

        default:

          return null;

      }

    };



    return (

      <>

      {/* Fitness disclaimer popup — rendered outside the modal card so backdrop-filter/overflow don't clip it */}

      {showFitnessWarning && (

        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.80)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1200, padding: "24px" }}>

              <div style={{ background: "var(--bg-card)", borderRadius: "16px", padding: "24px", width: "100%", maxWidth: "360px", textAlign: "center", boxShadow: "0 8px 32px rgba(0,0,0,0.2)" }}>

                <div style={{ fontSize: "32px", marginBottom: "12px" }}>⌚</div>

                <div style={{ fontSize: "16px", fontWeight: "800", marginBottom: "10px", color: "var(--text-primary)" }}>

                  {lang === "en" ? "Fitness zones will be estimated" : "Vùng tập luyện sẽ được ước tính"}

                </div>

                <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6", marginBottom: "20px" }}>

                  {isStart

                    ? (lang === "en"

                        ? "Your training zones will be estimated from your age. Once you have heart rate data from your watch, update them in Profile for a more accurate plan."

                        : "Vùng tập luyện sẽ được ước tính từ tuổi của bạn. Khi có dữ liệu nhịp tim từ đồng hồ, hãy cập nhật trong Hồ sơ để kế hoạch chính xác hơn.")

                    : (lang === "en"

                        ? "Your training zones will be estimated. Once you have a recent race result or heart rate zones from your watch, update them in Profile for a more accurate plan."

                        : "Vùng tập luyện sẽ được ước tính. Khi có kết quả giải chạy gần nhất hoặc vùng nhịp tim từ đồng hồ, hãy cập nhật trong Hồ sơ.")}

                </p>

                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>

                  <button

                    type="button"

                    onClick={() => { setShowFitnessWarning(false); nextStep(); }}

                    className="btn btn-primary"

                    style={{ height: "42px", fontSize: "13px", fontWeight: "700" }}

                  >

                    {lang === "en" ? "Got it, continue →" : "Đã hiểu, tiếp tục →"}

                  </button>

                  <button

                    type="button"

                    onClick={() => setShowFitnessWarning(false)}

                    style={{ height: "38px", background: "transparent", border: "1.5px solid var(--border-color)", borderRadius: "10px", cursor: "pointer", fontSize: "13px", color: "var(--text-secondary)", fontWeight: "600" }}

                  >

                    {lang === "en" ? "← Add fitness data" : "← Thêm dữ liệu thể trạng"}

                  </button>

                </div>

              </div>

            </div>

      )}

      <div style={{ position: "fixed", inset: 0, background: "rgba(255,255,255,0.35)", backdropFilter: "blur(16px)", display: "flex", justifyContent: "center", alignItems: "center", zIndex: 1001, padding: "20px" }}>

        <div style={{ position: "relative", background: "var(--bg-card)", backdropFilter: "blur(30px)", border: "1px solid var(--border-color)", borderRadius: "24px", padding: "32px", width: "100%", maxWidth: "500px", maxHeight: "90vh", overflowY: "auto", boxShadow: "0 20px 60px rgba(0,0,0,0.1)", color: "var(--text-primary)" }}>

          {/* Progress bar */}

          <div style={{ marginBottom: "24px" }}>

            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-muted)", marginBottom: "6px" }}>

              <span>{lang === "en" ? "Step" : "Bước"} {onboardingStep + 1} {lang === "en" ? "of" : "trên"} {totalSteps}</span>

              <span>{Math.round(((onboardingStep + 1) / totalSteps) * 100)}%</span>

            </div>

            <div style={{ height: "4px", background: "rgba(0,0,0,0.06)", borderRadius: "4px", overflow: "hidden" }}>

              <div style={{ height: "100%", width: `${((onboardingStep + 1) / totalSteps) * 100}%`, background: "var(--accent-primary)", borderRadius: "4px", transition: "width 0.3s ease" }} />

            </div>

          </div>



          {/* Step content */}

          {renderStep()}



          {/* Navigation */}

          {!onboardingGenerating && (

            <div style={{ display: "flex", gap: "10px", marginTop: "24px" }}>

              {onboardingStep > 0 && (

                <button type="button" onClick={prevStep} style={{ flex: 1, height: "40px", borderRadius: "10px", border: "1px solid var(--border-color)", background: "transparent", color: "var(--text-secondary)", fontWeight: "600", fontSize: "13px", cursor: "pointer" }}>

                  ← {lang === "en" ? "Back" : "Quay lại"}

                </button>

              )}

              {currentStepKey !== "generate" && (

                <button type="button" onClick={handleNextStep}

                  disabled={(currentStepKey === "goal" && !onboardingAnswers.goal_type) || (currentStepKey === "dob" && !!onboardingAnswers.dob_error)}

                  className="btn btn-primary" style={{ flex: 2, height: "40px", fontSize: "13px" }}>

                  {onboardingStep === totalSteps - 2

                    ? (lang === "en" ? "Review →" : "Xem lại →")

                    : (lang === "en" ? "Next →" : "Tiếp theo →")}

                </button>

              )}

            </div>

          )}

        </div>

      </div>

      </>

    );

  };
