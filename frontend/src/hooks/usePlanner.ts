/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { useAppContext } from "../contexts/AppContext";
import { ActivePlan, Workout } from "../types";

export function usePlanner() {
  const ctx = useAppContext();
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const { planForm, setPlanForm, setPlanErrorMsg, setPlanLoading, lang, targetTimeH, targetTimeM, targetTimeS, cutoffTimeH, cutoffTimeM, cutoffTimeS, activePlan, selectedWeek, swapDay1, swapDay2, setSwapDay1, setSwapDay2, setActivePlan, setBackupActivePlan, setBackupWorkouts, setSelectedWeek, setWorkouts, workouts, setPlannerGpxLoading, setPlannerGpxFile, setPlannerGpxError, setCourseInputMode, setRecentPlans, actingAsAthleteId } = ctx;
  const trackEvent = (name: string, props?: any) => { if (typeof window !== "undefined" && (window as any).posthog) { (window as any).posthog.capture(name, props); } };
  const plannerGpxInputRef = React.useRef<HTMLInputElement>(null);
  const planJobPollerRef = React.useRef<any>(null);
  const [draftPlan, setDraftPlan] = React.useState<ActivePlan | null>(null);
  const [draftWorkouts, setDraftWorkouts] = React.useState<Workout[]>([]);

  // When acting as a coach browsing an assigned athlete's data, every
  // read/generate/draft/approve/edit call goes through the athlete-scoped
  // /api/coaching/athletes/{id}/... routes instead of /api/coach/... .
  // Deliberately NOT applied to select-plan, modify-calendar, or
  // workouts/log below -- those have no coach-scoped backend equivalent
  // (see the Phase 5 plan's Global Constraints) and stay self-serve-only;
  // the UI disables those specific controls in acting-as-athlete mode
  // instead of pointing them at the wrong data.
  const coachPrefix = actingAsAthleteId ? `/api/coaching/athletes/${actingAsAthleteId}` : "/api/coach";

  const fetchRecentPlansWithToken = async (token: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}${coachPrefix}/recent-plans`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setRecentPlans(data.plans || []);
      }
    } catch (err) {
      console.error("Failed to fetch recent plans:", err);
    }
  };

  // Fetches the acting-as athlete's active plan + workouts into the shared
  // activePlan/workouts context state, mirroring page.tsx's
  // fetchActivePlanWithToken (used for the self-serve login flow) but
  // scoped to the athlete the coach is currently viewing.
  const fetchActivePlanForActing = async (): Promise<boolean> => {
    if (!actingAsAthleteId) return false;
    const token = localStorage.getItem("uphill_session_token");
    let hasActive = false;
    try {
      const res = await fetch(`${API_BASE_URL}/api/coaching/athletes/${actingAsAthleteId}/active-plan`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        if (data.active) {
          setActivePlan(data.plan);
          setWorkouts(data.workouts);
          hasActive = true;
        } else {
          setActivePlan(null);
          setWorkouts([]);
        }
      }
    } catch (err) {
      console.error("Failed to fetch athlete's active plan:", err);
    }
    await fetchRecentPlansWithToken(token!);
    return hasActive;
  };

  // `hasActivePlan` is threaded through explicitly (rather than read back
  // off `activePlan` state) because this always runs right after
  // fetchActivePlanForActing in the same effect, and React state from that
  // call isn't guaranteed to have committed yet when this runs.
  const fetchDraftPlan = async (hasActivePlan: boolean = false) => {
    if (!actingAsAthleteId) return;
    const token = localStorage.getItem("uphill_session_token");
    try {
      const res = await fetch(`${API_BASE_URL}/api/coaching/athletes/${actingAsAthleteId}/plans/draft`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setDraftPlan(data.draft ? data.plan : null);
        setDraftWorkouts(data.draft ? data.workouts : []);
        // No active plan yet at all (first workout not approved) -- render
        // the draft's own workouts through the same active-plan view so the
        // coach can review and approve them one at a time, rather than
        // approving blind from a banner with no workout list underneath it.
        if (data.draft && !hasActivePlan) {
          setActivePlan(data.plan);
          setWorkouts(data.workouts);
        }
      }
    } catch (err) {
      console.error("Failed to fetch draft plan:", err);
    }
  };

  const handleApproveWorkout = async (planId: number, workoutId: number) => {
    if (!actingAsAthleteId) return false;
    const token = localStorage.getItem("uphill_session_token");
    const res = await fetch(
      `${API_BASE_URL}/api/coaching/athletes/${actingAsAthleteId}/plans/${planId}/workouts/${workoutId}/approve`,
      { method: "POST", headers: { Authorization: `Bearer ${token}` } }
    );
    if (res.ok) {
      // Re-fetch from scratch rather than patch state in place: the first
      // approval on a draft plan flips plan_status server-side, and there's
      // no cheap way to know that from this response alone.
      const hasActive = await fetchActivePlanForActing();
      await fetchDraftPlan(hasActive);
    }
    return res.ok;
  };

  const handleRemoveWorkout = async (planId: number, workoutId: number) => {
    if (!actingAsAthleteId) return false;
    const token = localStorage.getItem("uphill_session_token");
    const res = await fetch(
      `${API_BASE_URL}/api/coaching/athletes/${actingAsAthleteId}/plans/${planId}/workouts/${workoutId}/remove`,
      { method: "POST", headers: { Authorization: `Bearer ${token}` } }
    );
    if (res.ok) {
      const updated = await res.json();
      setWorkouts((prev: any) => prev.map((w: any) => (w.id === workoutId ? updated : w)));
      setDraftWorkouts((prev: any) => prev.map((w: any) => (w.id === workoutId ? updated : w)));
    }
    return res.ok;
  };

  const handleAiCreateWorkout = async (
    planId: number,
    fields: {
      week_number: number;
      day_of_week: string;
      workout_type: string;
      duration_minutes: number;
      intent?: string;
      target_zone?: string;
      target_pace?: string;
      interval_reps?: number;
      interval_rep_value?: number;
      interval_rep_unit?: string;
    },
  ) => {
    if (!actingAsAthleteId) return false;
    const token = localStorage.getItem("uphill_session_token");
    const res = await fetch(
      `${API_BASE_URL}/api/coaching/athletes/${actingAsAthleteId}/plans/${planId}/workouts/ai-create`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(fields),
      }
    );
    if (res.ok) {
      // Not an optimistic append: adding to a day that only had a Rest
      // placeholder replaces that row server-side, so the client's prior
      // workouts array is stale (still holds the now-deleted rest row) --
      // a full re-fetch is the only way to stay correct.
      const hasActive = await fetchActivePlanForActing();
      await fetchDraftPlan(hasActive);
    }
    return res.ok;
  };

  const handleCoachEditWorkout = async (planId: number, workoutId: number, fields: Record<string, any>) => {
    if (!actingAsAthleteId) return false;
    const token = localStorage.getItem("uphill_session_token");
    const res = await fetch(
      `${API_BASE_URL}/api/coaching/athletes/${actingAsAthleteId}/plans/${planId}/workouts/${workoutId}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(fields),
      }
    );
    if (res.ok) {
      const updated = await res.json();
      setWorkouts((prev: any) => prev.map((w: any) => (w.id === workoutId ? updated : w)));
      setDraftWorkouts((prev: any) => prev.map((w: any) => (w.id === workoutId ? updated : w)));
    }
    return res.ok;
  };

  const startPlanJobPoller = (jobId: string, token: string) => {
    if (planJobPollerRef.current) {
      clearInterval(planJobPollerRef.current);
    }
    setPlanLoading(true);


    planJobPollerRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/coach/plan-status/${jobId}`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();

          if (data.status === "done") {
            clearInterval(planJobPollerRef.current);
            setPlanLoading(false);
            if (data.plan) setActivePlan(data.plan);
            if (data.workouts) setWorkouts(data.workouts);
            fetchRecentPlansWithToken(token);
          } else if (data.status === "error") {
            clearInterval(planJobPollerRef.current);
            setPlanLoading(false);
            setPlanErrorMsg(data.error || "Plan generation failed");
          }
          // status === "generating" → keep polling
        } else {
          clearInterval(planJobPollerRef.current);
          setPlanLoading(false);
        }
      } catch (err) {
        console.error("Error polling plan job:", err);
        clearInterval(planJobPollerRef.current);
        setPlanLoading(false);
      }
    }, 10000);
  };

  const handlePlannerGpxFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setPlannerGpxLoading(true);
    setPlannerGpxError("");
    setPlannerGpxFile(null);

    const formData = new FormData();
    formData.append("file", file);

    const extension = file.name.split(".").pop()?.toLowerCase();
    if (extension !== "gpx") {
      setPlannerGpxError("Unsupported file format. Please upload a .gpx file.");
      setPlannerGpxLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/parser/gpx`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || "Parsing failed on server");
      }

      const result = await response.json();
      const sum = result.summary;
      const dist = parseFloat(((sum.total_distance_meters || 0) / 1000).toFixed(2));
      const elev = Math.round(sum.total_elevation_gain_meters || 0);

      setPlanForm({
        ...planForm, setPlanForm,
        course_distance_km: dist.toString(),
        course_elevation_gain_m: elev.toString()
      });
      setPlannerGpxFile(file);
    } catch (err: any) {
      setPlannerGpxError(err.message || "An error occurred while uploading/parsing.");
    } finally {
      setPlannerGpxLoading(false);
    }
  };

  const handleGeneratePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    const isRaceOrDistVal = planForm.plan_goal_category === "race" || planForm.plan_goal_category === "distance";
    if (isRaceOrDistVal && (!planForm.race_name || !planForm.race_date)) {
      setPlanErrorMsg("Race Name and Race Date are required for Race/Distance goals.");
      return;
    }
    if (!isRaceOrDistVal && !planForm.plan_start_date) {
      setPlanErrorMsg("Please select a Plan Start Date.");
      return;
    }
    if (!planForm.current_weekly_km) {
      setPlanErrorMsg("Please enter your current weekly mileage.");
      return;
    }
    setPlanLoading(true);
    setPlanErrorMsg("");

    const token = localStorage.getItem("uphill_session_token");
    let pollerStarted = false;
    try {
      const isRaceOrDist = planForm.plan_goal_category === "race" || planForm.plan_goal_category === "distance";
      // Build request body
      const body: Record<string, any> = {
        race_name: isRaceOrDist ? planForm.race_name : planForm.plan_goal_category.replace("_", " "),
        race_date: isRaceOrDist ? planForm.race_date : "",
        goal_type: isRaceOrDist ? planForm.goal_type : planForm.plan_goal_category,
        terrain: planForm.terrain,
        course_distance_km: planForm.course_distance_km ? parseFloat(planForm.course_distance_km) : null,
        course_elevation_gain_m: planForm.course_elevation_gain_m ? parseFloat(planForm.course_elevation_gain_m) : null,
        days_per_week: planForm.days_per_week,
        long_run_day: planForm.long_run_day,
        preferred_days: planForm.preferred_days,
        current_weekly_km: parseFloat(planForm.current_weekly_km),
        has_gym_access: planForm.has_gym_access,
        use_treadmill: planForm.use_treadmill,
        training_environment: planForm.training_environment,
        double_session_days: planForm.double_session_days,
        plan_start_date: planForm.plan_start_date || null,
        plan_duration_weeks: isRaceOrDist ? null : planForm.plan_duration_weeks,
        // non-race context fields
        time_away: planForm.time_away || null,
        fitness_feel: planForm.fitness_feel || null,
        race_distance_completed: planForm.race_distance_completed || null,
        days_since_race: planForm.days_since_race ? parseInt(planForm.days_since_race) : null,
        recovery_feel: planForm.recovery_feel || null,
        lang: lang,
        coach_notes: actingAsAthleteId ? (planForm.coach_notes || null) : null,
      };

      // Combine H/M/S into decimal hours
      if (planForm.goal_type === "time") {
        const h = parseFloat(targetTimeH || "0");
        const m = parseFloat(targetTimeM || "0");
        const s = parseFloat(targetTimeS || "0");
        const total = h + m / 60 + s / 3600;
        if (total > 0) body.target_time_hours = total;
      } else if (planForm.goal_type === "finish") {
        const h = parseFloat(cutoffTimeH || "0");
        const m = parseFloat(cutoffTimeM || "0");
        const s = parseFloat(cutoffTimeS || "0");
        const total = h + m / 60 + s / 3600;
        if (total > 0) body.cutoff_time_hours = total;
      }

      const response = await fetch(`${API_BASE_URL}${coachPrefix}/generate-plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errorText = await response.json();
        throw new Error(errorText.detail || "Plan generation failed.");
      }

      const result = await response.json();

      trackEvent('plan_generated', {
        success: true,
        goal_type: body.goal_type,
        terrain: body.terrain,
        duration_weeks: body.plan_duration_weeks
      });

      // Set plan immediately from the fast response; clear old workouts so
      // stale data doesn't appear under the new plan title while polling
      if (result.plan) {
        setActivePlan(result.plan);
        setWorkouts([]);
        setBackupActivePlan(null);
        setBackupWorkouts([]);
      }
      setSelectedWeek(1);
      // Start background polling — poller owns planLoading until job completes
      if (result.job_id) {
        pollerStarted = true;
        startPlanJobPoller(result.job_id, token!);
      } else {
        // Fallback: synchronous workouts (no job)
        if (result.workouts) setWorkouts(result.workouts);
        if (token) fetchRecentPlansWithToken(token);
      }
    } catch (err: any) {
      setPlanErrorMsg(err.message);
      trackEvent('plan_generated', { success: false, error: err.message });
    } finally {
      // Only clear loading here if the poller isn't taking over
      if (!pollerStarted) setPlanLoading(false);
    }
  };

  const getPlanDistance = (p: ActivePlan) => {
    if (p.course_distance_km !== undefined && p.course_distance_km !== null) return p.course_distance_km;
    if (p.race_name && p.race_name.toUpperCase().includes("SUM30")) return 30;
    return null;
  };

  const getPlanElevation = (p: ActivePlan) => {
    if (p.course_elevation_gain_m !== undefined && p.course_elevation_gain_m !== null) return p.course_elevation_gain_m;
    if (p.race_name && p.race_name.toUpperCase().includes("SUM30")) return 1200;
    return null;
  };

  const formatPlanName = (p: ActivePlan) => {
    const dist = getPlanDistance(p);
    const elev = getPlanElevation(p);
    const kmStr = dist ? `${dist}km` : "0km";
    const gainStr = elev ? `+${elev}m` : "+0m";
    let targetStr = "Finish";
    let dateStr = p.race_date || "No Date";

    if (p.goal_type === "time" && p.target_time_hours) {
      targetStr = `${p.target_time_hours}h`;
    } else if (p.goal_type === "optimal") {
      targetStr = "Optimal";
    } else if (p.goal_type) {
      targetStr = p.goal_type.charAt(0).toUpperCase() + p.goal_type.slice(1).replace("_", " ");
    }

    if (["start_running", "return", "recovery"].includes(p.goal_type || "")) {
      dateStr = `Ends ${p.race_date}`;
      return `${p.race_name || "Untitled Plan"} (${dateStr}) | ${targetStr}`;
    } else {
      dateStr = `Race: ${p.race_date}`;
      return `${p.race_name || "Untitled Plan"} (${dateStr}) | ${kmStr} | +${elev || 0}m | ${targetStr}`;
    }
  };

  const handleSelectPlan = async (planId: number) => {
    const token = localStorage.getItem("uphill_session_token");
    if (!token) return;
    try {
      setPlanLoading(true);
      setPlanErrorMsg("");
      const response = await fetch(`${API_BASE_URL}/api/coach/select-plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ plan_id: planId })
      });
      if (response.ok) {
        const data = await response.json();
        setActivePlan(data.plan);
        setWorkouts(data.workouts);
        setBackupActivePlan(null);
        setBackupWorkouts([]);
        setSelectedWeek(1);
        fetchRecentPlansWithToken(token);
      } else {
        const errorText = await response.json();
        setPlanErrorMsg(errorText.detail || "Failed to select plan.");
      }
    } catch (err: any) {
      setPlanErrorMsg(err.message);
    } finally {
      setPlanLoading(false);
    }
  };

  const handleSwapWorkouts = async () => {
    if (!activePlan) return;
    const token = localStorage.getItem("uphill_session_token");
    try {
      const response = await fetch(`${API_BASE_URL}/api/coach/modify-calendar`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          plan_id: activePlan.id,
          week_number: selectedWeek,
          day_1: swapDay1,
          day_2: swapDay2
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setWorkouts(result.workouts);
      }
    } catch (err) {
      console.error("Failed to swap workouts:", err);
    }
  };

  const swapDays = async (day1: string, day2: string, weekNumberOverride?: number) => {
    if (!activePlan || day1 === day2) return;
    const token = localStorage.getItem("uphill_session_token");
    try {
      const response = await fetch(`${API_BASE_URL}/api/coach/modify-calendar`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ plan_id: activePlan.id, week_number: weekNumberOverride ?? selectedWeek, day_1: day1, day_2: day2 }),
      });
      if (response.ok) {
        const result = await response.json();
        setWorkouts(result.workouts);
      }
    } catch (err) {
      console.error("Failed to swap days:", err);
    }
  };

  const handleToggleComplete = async (woId: number, isCompleted: boolean) => {
    setWorkouts((prev: any) =>
      prev.map((wo: any) =>
        wo.id === woId ? { ...wo, is_completed: isCompleted ? 1 : 0, is_missed: isCompleted ? 0 : wo.is_missed } : wo
      )
    );
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("uphill_session_token") : null;
      if (!token) return;
      await fetch(`${API_BASE_URL}/api/coach/workouts/log`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ workout_id: woId, is_completed: isCompleted ? 1 : 0 }),
      });
    } catch {
      // optimistic update already applied — failure is silent
    }
  };

  const handleMarkMissed = async (woId: number, isMissed: boolean) => {
    setWorkouts((prev: any) =>
      prev.map((wo: any) =>
        wo.id === woId ? { ...wo, is_missed: isMissed ? 1 : 0, is_completed: isMissed ? 0 : wo.is_completed } : wo
      )
    );
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("uphill_session_token") : null;
      if (!token) return;
      await fetch(`${API_BASE_URL}/api/coach/workouts/log`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ workout_id: woId, is_missed: isMissed ? 1 : 0 }),
      });
    } catch {
      // optimistic update already applied — failure is silent
    }
  };

  const handleLogWorkout = async (woId: number, rpe: number | null, notes: string) => {
    setWorkouts((prev: any) =>
      prev.map((wo: any) => (wo.id === woId ? { ...wo, rpe: rpe ?? wo.rpe, notes: notes ?? wo.notes } : wo))
    );
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("uphill_session_token") : null;
      if (!token) return;
      const body: any = { workout_id: woId };
      if (rpe !== null) body.rpe = rpe;
      body.notes = notes;
      await fetch(`${API_BASE_URL}/api/coach/workouts/log`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify(body),
      });
    } catch {
      // optimistic update already applied
    }
  };

  const getWeekWorkouts = (weekNum: number) => {
    return workouts.filter((w: any) => w.week_number === weekNum);
  };

  const DAY_OFFSETS: Record<string, number> = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6,
  };

  const getMondayOf = (d: Date) => {
    const offset = d.getDay() === 0 ? 6 : d.getDay() - 1;
    const m = new Date(d);
    m.setDate(d.getDate() - offset);
    return m;
  };

  // Returns the real calendar Date a workout falls on, or null if it can't be
  // computed (no active plan / malformed dates). Used by getWorkoutDate below
  // and by the calendar grid view, which needs a real Date, not a formatted string.
  const getWorkoutDateObj = (wo: Workout): Date | null => {
    if (!activePlan) return null;
    try {
      let startMonday: Date;

      // Prefer plan_start_date (exact user-inputted date) if stored
      if (activePlan.start_date) {
        const parts = activePlan.start_date.split("-");
        const sd = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
        // Week 1 starts on the Monday on or before the start date
        startMonday = getMondayOf(sd);
      } else if (activePlan.race_date) {
        // Fallback: anchor from race date backward (legacy behaviour)
        const parts = activePlan.race_date.split("-");
        if (parts.length !== 3) return null;
        const raceDate = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
        const raceWo = workouts.find((w: any) => {
          const title = w.title.toUpperCase();
          const type = w.type.toUpperCase();
          return title.includes("TARGET EVENT") || type === "RACE";
        });
        const raceWeek = raceWo ? raceWo.week_number : activePlan.total_weeks;
        const raceWeekMonday = getMondayOf(raceDate);
        startMonday = new Date(raceWeekMonday);
        startMonday.setDate(raceWeekMonday.getDate() - (raceWeek - 1) * 7);
      } else {
        return null;
      }

      const workoutDayOffset = DAY_OFFSETS[wo.day_of_week] ?? 0;
      const workoutDate = new Date(startMonday);
      workoutDate.setDate(startMonday.getDate() + (wo.week_number - 1) * 7 + workoutDayOffset);

      return workoutDate;
    } catch (e) {
      console.error(e);
      return null;
    }
  };

  const getWorkoutDate = (wo: Workout) => {
    const d = getWorkoutDateObj(wo);
    if (!d) return "";
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  return { handleGeneratePlan, getPlanDistance, getPlanElevation, formatPlanName, handleSelectPlan, handleSwapWorkouts, swapDays, handleToggleComplete, handleMarkMissed, handleLogWorkout, getWeekWorkouts, getWorkoutDate, getWorkoutDateObj, handlePlannerGpxFileChange, plannerGpxInputRef, trackEvent, API_BASE_URL, fetchRecentPlansWithToken, startPlanJobPoller, fetchDraftPlan, draftPlan, draftWorkouts, handleApproveWorkout, handleRemoveWorkout, handleAiCreateWorkout, handleCoachEditWorkout, fetchActivePlanForActing };
}
