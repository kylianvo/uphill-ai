import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AdaptWeekModal } from "./AdaptWeekModal";

describe("AdaptWeekModal", () => {
  const defaultSchedule = {
    days_per_week: 4,
    long_run_day: "Saturday",
    preferred_days: ["Tuesday", "Thursday", "Saturday", "Sunday"],
    has_gym_access: false,
    use_treadmill: false,
    training_environment: "flat" as const,
    double_session_days: [],
    athlete_notes: "",
  };

  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.setItem("uphill_session_token", "test-token");
  });

  it("does not render when isOpen is false", () => {
    const { container } = render(
      <AdaptWeekModal
        isOpen={false}
        onClose={vi.fn()}
        planId={10}
        weekNumber={2}
        totalWeeks={12}
        completedWorkoutsCount={0}
        initialSchedule={defaultSchedule}
        lang="en"
        isMobile={false}
        onAdaptSuccess={vi.fn()}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders header, feeling cards, and preserved notice when completedWorkoutsCount > 0", () => {
    render(
      <AdaptWeekModal
        isOpen={true}
        onClose={vi.fn()}
        planId={10}
        weekNumber={2}
        totalWeeks={12}
        completedWorkoutsCount={2}
        initialSchedule={defaultSchedule}
        lang="en"
        isMobile={false}
        onAdaptSuccess={vi.fn()}
      />
    );

    expect(screen.getByText("Adapt Week 2")).toBeInTheDocument();
    expect(screen.getByText(/2 completed\/recorded session\(s\) in this week will be strictly preserved/)).toBeInTheDocument();
    expect(screen.getByText("How are your legs & energy feeling?")).toBeInTheDocument();
    expect(screen.getByText("Very Light")).toBeInTheDocument();
    expect(screen.getByText("Light")).toBeInTheDocument();
    expect(screen.getByText("Moderate")).toBeInTheDocument();
    expect(screen.getByText("Hard")).toBeInTheDocument();
    expect(screen.getByText("Max Effort")).toBeInTheDocument();
    expect(screen.getByText("Double Session Days (Optional)")).toBeInTheDocument();
    expect(screen.getByText("Regenerate Week 2")).toBeInTheDocument();
  });

  it("posts to self-serve endpoint with selected feeling and calls onAdaptSuccess on submit", async () => {
    const onAdaptSuccess = vi.fn();
    const onClose = vi.fn();

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ job_id: "adapt-job-123", plan_id: 10, week_number: 2 }),
    } as Response);

    render(
      <AdaptWeekModal
        isOpen={true}
        onClose={onClose}
        planId={10}
        weekNumber={2}
        totalWeeks={12}
        completedWorkoutsCount={1}
        initialSchedule={defaultSchedule}
        lang="en"
        isMobile={false}
        onAdaptSuccess={onAdaptSuccess}
      />
    );

    // Select "Hard" feeling
    fireEvent.click(screen.getByText("Hard"));

    // Fill fatigue notes
    const textarea = screen.getByPlaceholderText(/Why are you adapting this week/i);
    fireEvent.change(textarea, { target: { value: "Hamstring stiffness after long run" } });

    // Submit
    const submitBtn = screen.getByRole("button", { name: /Regenerate Week 2/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledTimes(1);
    });

    const [url, options] = fetchSpy.mock.calls[0];
    expect(url).toContain("/api/coach/adapt-week");
    const body = JSON.parse(options?.body as string);
    expect(body.plan_id).toBe(10);
    expect(body.week_number).toBe(2);
    expect(body.fatigue_level).toBe("hard");
    expect(body.overall_rpe).toBe(8);
    expect(body.fatigue_notes).toBe("Hamstring stiffness after long run");
    expect(body.preferred_days).toEqual(["Tuesday", "Thursday", "Saturday", "Sunday"]);

    expect(onClose).toHaveBeenCalled();
    expect(onAdaptSuccess).toHaveBeenCalledWith("adapt-job-123");
  });

  it("allows selecting double session days from preferred days", async () => {
    const onAdaptSuccess = vi.fn();
    const onClose = vi.fn();

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ job_id: "adapt-job-789", plan_id: 10, week_number: 2 }),
    } as Response);

    render(
      <AdaptWeekModal
        isOpen={true}
        onClose={onClose}
        planId={10}
        weekNumber={2}
        totalWeeks={12}
        completedWorkoutsCount={0}
        initialSchedule={defaultSchedule}
        lang="en"
        isMobile={false}
        onAdaptSuccess={onAdaptSuccess}
      />
    );

    // Find double session container
    const doubleSessionHeader = screen.getByText("Double Session Days (Optional)");
    const doubleSessionContainer = doubleSessionHeader.closest("div")!.parentElement!;
    // Click Tuesday button in the double session container
    const tueBtn = Array.from(doubleSessionContainer.querySelectorAll("button")).find(
      (b) => b.textContent?.trim() === "Tue"
    );
    expect(tueBtn).toBeDefined();
    fireEvent.click(tueBtn!);

    const submitBtn = screen.getByRole("button", { name: /Regenerate Week 2/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledTimes(1);
    });

    const [, options] = fetchSpy.mock.calls[0];
    const body = JSON.parse(options?.body as string);
    expect(body.double_session_days).toEqual(["Tuesday"]);
  });

  it("posts to coach-scoped endpoint when actingAsAthleteId is set", async () => {
    const onAdaptSuccess = vi.fn();
    const onClose = vi.fn();

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({ job_id: "coach-adapt-456", plan_id: 10, week_number: 3 }),
    } as Response);

    render(
      <AdaptWeekModal
        isOpen={true}
        onClose={onClose}
        planId={10}
        weekNumber={3}
        totalWeeks={12}
        completedWorkoutsCount={0}
        initialSchedule={defaultSchedule}
        lang="en"
        isMobile={false}
        onAdaptSuccess={onAdaptSuccess}
        actingAsAthleteId={99}
      />
    );

    expect(screen.getByText(/Coach Directive for this week/i)).toBeInTheDocument();

    const submitBtn = screen.getByRole("button", { name: /Regenerate Week 3/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledTimes(1);
    });

    const [url] = fetchSpy.mock.calls[0];
    expect(url).toContain("/api/coaching/athletes/99/adapt-week");
  });
});
