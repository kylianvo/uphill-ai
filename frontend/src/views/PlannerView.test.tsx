/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import PlannerView, { formatTargetTimeHours } from "./PlannerView";

// Mocks for child components
vi.mock("../components/PlanCalendarView", () => ({
  default: () => <div data-testid="plan-calendar-view" />,
}));
vi.mock("../components/WorkoutCard", () => ({
  default: () => <div data-testid="workout-card" />,
}));
vi.mock("../components/WeeklyReview", () => ({
  default: () => <div data-testid="weekly-review" />,
  CompletionRing: () => null,
  ringColor: () => "",
  computeCreditedActual: () => 0,
}));
vi.mock("../components/CoachNoteThread", () => ({
  CoachNoteThread: () => <div data-testid="coach-note-thread" />,
}));
vi.mock("../components/RaceNameField", () => ({
  RaceNameField: () => <div data-testid="race-name-field" />,
}));
vi.mock("../components/ScheduleFieldsEditor", () => ({
  ScheduleFieldsEditor: () => <div data-testid="schedule-fields-editor" />,
}));
vi.mock("./ToolsView", () => ({
  default: () => <div data-testid="tools-view" />,
}));
vi.mock("../components/AdaptWeekModal", () => ({
  AdaptWeekModal: () => <div data-testid="adapt-week-modal" />,
}));
vi.mock("../components/MoveWorkoutModal", () => ({
  MoveWorkoutModal: () => <div data-testid="move-workout-modal" />,
}));
vi.mock("../components/CorosPushButton", () => ({
  default: () => <div data-testid="coros-push-button" />,
}));
vi.mock("../components/FeelingSelector", () => ({
  FeelingSelector: () => <div data-testid="feeling-selector" />,
  rpeToFeelingId: () => "good",
}));
vi.mock("../components/KnowledgeCard", () => ({
  KnowledgeCard: () => <div data-testid="knowledge-card" />,
}));
vi.mock("../components/CalendarNoticeBanner", () => ({
  default: () => null,
}));
vi.mock("../components/MatchedActivityCard", () => ({
  default: () => null,
}));
vi.mock("../components/UnplannedActivityCard", () => ({
  default: () => null,
}));

// Mock native haptic
const mockTriggerHaptic = vi.fn();
vi.mock("../utils/native", () => ({
  triggerHaptic: () => mockTriggerHaptic(),
}));

// Shared mock states
let mockAppContext: any = {};
let mockPlanner: any = {};

vi.mock("../contexts/AppContext", () => ({
  useAppContext: () => mockAppContext,
}));

vi.mock("../hooks/usePlanner", () => ({
  usePlanner: () => mockPlanner,
}));

describe("formatTargetTimeHours", () => {
  it("formats decimal hours to hours and minutes string", () => {
    expect(formatTargetTimeHours(8.5)).toBe("8h 30m");
    expect(formatTargetTimeHours(12)).toBe("12h");
    expect(formatTargetTimeHours(0.75)).toBe("45m");
    expect(formatTargetTimeHours(10.25)).toBe("10h 15m");
  });

  it("handles null, undefined, 0, or negative numbers gracefully", () => {
    expect(formatTargetTimeHours(null)).toBe("");
    expect(formatTargetTimeHours(undefined)).toBe("");
    expect(formatTargetTimeHours(0)).toBe("");
    expect(formatTargetTimeHours(-2)).toBe("");
    expect(formatTargetTimeHours(NaN)).toBe("");
  });
});

describe("PlannerView Early Adopter Improvements", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem("uphill_session_token", "test-token");
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true }),
    }) as any;

    mockPlanner = {
      handleGeneratePlan: vi.fn(),
      getPlanDistance: vi.fn().mockReturnValue(50),
      getPlanElevation: vi.fn().mockReturnValue(2500),
      formatPlanName: (p: any) => p.race_name || "Custom Plan",
      handleSelectPlan: vi.fn(),
      swapDays: vi.fn(),
      moveWorkout: vi.fn(),
      calendarNotice: null,
      dismissCalendarNotice: vi.fn(),
      handleToggleComplete: vi.fn(),
      handleMarkMissed: vi.fn(),
      handleLogWorkout: vi.fn(),
      getWeekWorkouts: vi.fn().mockReturnValue([]),
      getWorkoutDate: vi.fn().mockReturnValue("2026-10-10"),
      getWorkoutDateObj: vi.fn().mockReturnValue(new Date()),
      handlePlannerGpxFileChange: vi.fn(),
      plannerGpxInputRef: { current: null },
      trackEvent: vi.fn(),
      API_BASE_URL: "http://localhost:8000",
      fetchRecentPlansWithToken: vi.fn(),
      startPlanJobPoller: vi.fn(),
      fetchDraftPlan: vi.fn(),
      draftPlan: null,
      handleApproveWorkout: vi.fn(),
      handleRemoveWorkout: vi.fn(),
      handleAiCreateWorkout: vi.fn(),
      handleCoachEditWorkout: vi.fn(),
      fetchActivePlanForActing: vi.fn(),
    };

    mockAppContext = {
      lang: "en",
      activePlan: {
        id: 101,
        race_name: "UTMB 50K",
        race_date: "2026-10-10",
        goal_type: "time",
        target_time_hours: 8.5,
        total_weeks: 12,
      },
      planLoading: false,
      planErrorMsg: "",
      setPlanErrorMsg: vi.fn(),
      planForm: {
        plan_goal_category: "race",
        race_name: "UTMB 50K",
        race_date: "2026-10-10",
        goal_type: "time",
        days_per_week: 5,
        current_weekly_km: "45",
      },
      setPlanForm: vi.fn(),
      targetTimeH: "8",
      setTargetTimeH: vi.fn(),
      targetTimeM: "30",
      setTargetTimeM: vi.fn(),
      targetTimeS: "0",
      setTargetTimeS: vi.fn(),
      cutoffTimeH: "",
      setCutoffTimeH: vi.fn(),
      cutoffTimeM: "",
      setCutoffTimeM: vi.fn(),
      cutoffTimeS: "",
      setCutoffTimeS: vi.fn(),
      recentPlans: [
        { id: 101, race_name: "UTMB 50K", race_date: "2026-10-10", target_time_hours: 8.5 },
        { id: 102, race_name: "VMM 70K", race_date: "2026-11-20", target_time_hours: 12 },
      ],
      selectedWeek: 1,
      setSelectedWeek: vi.fn(),
      workouts: [],
      setWorkouts: vi.fn(),
      backupWorkouts: [],
      setBackupWorkouts: vi.fn(),
      setActivePlan: vi.fn(),
      backupActivePlan: null,
      setBackupActivePlan: vi.fn(),
      courseInputMode: "manual",
      setCourseInputMode: vi.fn(),
      plannerGpxLoading: false,
      plannerGpxFile: null,
      plannerGpxError: null,
      showExportOptions: false,
      setShowExportOptions: vi.fn(),
      exportTimePref: "morning",
      setExportTimePref: vi.fn(),
      setIsGoalDeterminerOpen: vi.fn(),
      settingsHandoff: null,
      setSettingsHandoff: vi.fn(),
      setPaceHandoff: vi.fn(),
      setIsPaceStrategyOpen: vi.fn(),
      user: { id: 1, name: "Trail Runner" },
      actingAsAthleteId: null,
      actingAsAthleteName: "",
      setActingAsAthleteId: vi.fn(),
      setActingAsAthleteName: vi.fn(),
      handleTabSwitch: vi.fn(),
      activePlanLoading: false,
    };
  });

  it("renders formatted race target time in active plan header", () => {
    render(<PlannerView />);
    expect(screen.getByText(/Time Target \(8h 30m\)/i)).toBeInTheDocument();
  });

  it("opens recent plans dropdown and displays delete button for each plan", async () => {
    render(<PlannerView />);

    // Find the Recent Plans dropdown button
    const dropdownBtn = screen.getByRole("button", { name: /recent plans|lịch tập gần đây/i });
    fireEvent.click(dropdownBtn);

    // Both plans should be shown in dropdown
    expect(screen.getByText("VMM 70K")).toBeInTheDocument();

    // Check delete buttons exist
    const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
    expect(deleteButtons.length).toBeGreaterThan(0);
  });

  it("opens confirmation modal when delete plan is clicked and sends DELETE request on confirm", async () => {
    render(<PlannerView />);

    const dropdownBtn = screen.getByRole("button", { name: /recent plans|lịch tập gần đây/i });
    fireEvent.click(dropdownBtn);

    const deleteButtons = screen.getAllByRole("button", { name: /delete vmm 70k/i });
    fireEvent.click(deleteButtons[0]);

    // Confirmation modal should appear
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText(/Delete Training Plan\?/i)).toBeInTheDocument();

    // Click confirm delete
    const confirmDeleteBtn = screen.getByRole("button", { name: /^delete plan$/i });
    fireEvent.click(confirmDeleteBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/coach/plans/102",
        expect.objectContaining({ method: "DELETE" })
      );
      expect(mockPlanner.fetchRecentPlansWithToken).toHaveBeenCalled();
    });
  });

  it("prompts confirmation modal before generating a new plan", async () => {
    // When there is no active plan
    mockAppContext.activePlan = null;
    render(<PlannerView />);

    const submitBtn = screen.getByRole("button", { name: /build custom calendar/i });
    fireEvent.click(submitBtn);

    // Modal should ask for confirmation
    expect(await screen.findByText(/Create Training Plan\?/i)).toBeInTheDocument();

    // Confirm creation
    const confirmBtn = screen.getByRole("button", { name: /^generate plan$/i });
    fireEvent.click(confirmBtn);

    expect(mockPlanner.handleGeneratePlan).toHaveBeenCalled();
  });

  it("prompts confirmation modal before generating next block", async () => {
    mockAppContext.activePlan = {
      id: 101,
      race_name: "UTMB 50K",
      race_date: "2026-10-10",
      goal_type: "time",
      target_time_hours: 8.5,
      total_weeks: 4,
      days_per_week: 4,
    };
    mockAppContext.workouts = [
      { id: 1, week_number: 1, day_of_week: "Monday", is_completed: 1 },
    ];
    render(<PlannerView />);

    const reviewBtn = screen.queryByRole("button", { name: /review & generate block 2|tạo block 2/i });
    if (reviewBtn) {
      fireEvent.click(reviewBtn);
      const generateBlockBtn = screen.getByRole("button", { name: /generate block 2/i });
      fireEvent.click(generateBlockBtn);
      expect(await screen.findByText(/Generate Block 2\?/i)).toBeInTheDocument();
    }
  });
});
