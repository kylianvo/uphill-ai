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
    mountain_days: [] as string[],
    stair_access: false,
    treadmill_max_incline: 15,
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
    expect(screen.getByRole("radio", { name: "Very Light" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Light" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Moderate" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Hard" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Max Effort" })).toBeInTheDocument();
    expect(screen.getByText("Double Session Days (Optional)")).toBeInTheDocument();
    expect(screen.getByText("Regenerate Week 2")).toBeInTheDocument();
  });

  it("posts to self-serve endpoint with selected feeling and calls onAdaptSuccess on submit", async () => {
    const onAdaptSuccess = vi.fn();
    const onClose = vi.fn();

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({ ok: true, json: async () => [] } as unknown as Response).mockResolvedValueOnce({
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

    // Submit and confirm
    const submitBtn = screen.getByRole("button", { name: /Regenerate Week 2/i });
    fireEvent.click(submitBtn);
    fireEvent.click(screen.getByRole("button", { name: /^Regenerate Week$/i }));

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledTimes(2);
    });

    const [url, options] = fetchSpy.mock.calls[1];
    expect(url).toContain("/api/coach/adapt-week");
    const body = JSON.parse(options?.body as string);
    expect(body.plan_id).toBe(10);
    expect(body.week_number).toBe(2);
    expect(body.fatigue_level).toBe("hard");
    // One feeling and one note: RPE is derived by the backend, and the text goes only as athlete_notes.
    expect(body).not.toHaveProperty("overall_rpe");
    expect(body).not.toHaveProperty("fatigue_notes");
    expect(body.athlete_notes).toBe("Hamstring stiffness after long run");
    expect(body.health_issue).toBeNull();
    expect(body.preferred_days).toEqual(["Tuesday", "Thursday", "Saturday", "Sunday"]);

    expect(onClose).toHaveBeenCalled();
    expect(onAdaptSuccess).toHaveBeenCalledWith("adapt-job-123");
  });

  it("lists last week's missed sessions with reason chips and reports the chosen reason", () => {
    const onSetMissedReason = vi.fn();
    render(
      <AdaptWeekModal
        isOpen={true}
        onClose={vi.fn()}
        planId={10}
        weekNumber={2}
        totalWeeks={12}
        completedWorkoutsCount={0}
        initialSchedule={defaultSchedule}
        lang="en"
        isMobile={false}
        onAdaptSuccess={vi.fn()}
        missedLastWeek={[
          { id: 7, day_of_week: "Wednesday", title: "Recovery Run", missed_reason: "busy" },
          { id: 8, day_of_week: "Thursday", title: "Gym ME" },
        ]}
        onSetMissedReason={onSetMissedReason}
      />
    );
    const list = screen.getByTestId("adapt-missed-sessions");
    expect(list).toHaveTextContent("Wednesday · Recovery Run");
    expect(list).toHaveTextContent("Thursday · Gym ME");
    const sickButtons = screen.getAllByRole("button", { name: "Sick" });
    // the first "Sick" belongs to Wednesday's chips, the second to Thursday's
    fireEvent.click(sickButtons[1]);
    expect(onSetMissedReason).toHaveBeenCalledWith(8, "sick");
  });

  it("hides the missed-sessions section when nothing was missed", () => {
    render(
      <AdaptWeekModal
        isOpen={true}
        onClose={vi.fn()}
        planId={10}
        weekNumber={2}
        totalWeeks={12}
        completedWorkoutsCount={0}
        initialSchedule={defaultSchedule}
        lang="en"
        isMobile={false}
        onAdaptSuccess={vi.fn()}
        missedLastWeek={[]}
        onSetMissedReason={vi.fn()}
      />
    );
    expect(screen.queryByTestId("adapt-missed-sessions")).not.toBeInTheDocument();
  });

  it("sends the illness or pain the athlete reports and shows Vietnamese labels", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({ ok: true, json: async () => [] } as unknown as Response) // mountain list on mount
      .mockResolvedValueOnce({ ok: true, json: async () => ({ job_id: "j", plan_id: 10, week_number: 2 }) } as Response);
    render(
      <AdaptWeekModal
        isOpen={true}
        onClose={vi.fn()}
        planId={10}
        weekNumber={2}
        totalWeeks={12}
        completedWorkoutsCount={0}
        initialSchedule={defaultSchedule}
        lang="vi"
        isMobile={false}
        onAdaptSuccess={vi.fn()}
      />
    );
    expect(screen.getByText("Đang ốm hoặc đau")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Đau" }));
    expect(screen.getByRole("button", { name: "Đau" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Không" })).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(screen.getByRole("button", { name: /Tái tạo Tuần 2/ }));
    fireEvent.click(screen.getByRole("button", { name: /^Tái tạo tuần$/ }));
    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(2));
    const body = JSON.parse(fetchSpy.mock.calls[1][1]?.body as string);
    expect(body.health_issue).toBe("pain");
  });

  it("allows selecting double session days from preferred days", async () => {
    const onAdaptSuccess = vi.fn();
    const onClose = vi.fn();

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({ ok: true, json: async () => [] } as unknown as Response).mockResolvedValueOnce({
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
    fireEvent.click(screen.getByRole("button", { name: /^Regenerate Week$/i }));

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledTimes(2);
    });

    const [, options] = fetchSpy.mock.calls[1];
    const body = JSON.parse(options?.body as string);
    expect(body.double_session_days).toEqual(["Tuesday"]);
  });

  it("posts to coach-scoped endpoint when actingAsAthleteId is set", async () => {
    const onAdaptSuccess = vi.fn();
    const onClose = vi.fn();

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({ ok: true, json: async () => [] } as unknown as Response).mockResolvedValueOnce({
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
    fireEvent.click(screen.getByRole("button", { name: /^Regenerate Week$/i }));

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledTimes(2);
    });

    const [url] = fetchSpy.mock.calls[1];
    expect(url).toContain("/api/coaching/athletes/99/adapt-week");
  });

  it("explains a refused adapt with the guard code", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({ ok: true, json: async () => [] } as unknown as Response).mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: async () => ({ detail: { code: "G3_past_target", params: { week: 2 } } }),
    } as Response);
    render(
      <AdaptWeekModal
        isOpen={true}
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
    fireEvent.click(screen.getByText("Regenerate Week 2"));
    fireEvent.click(screen.getByRole("button", { name: /^Regenerate Week$/i }));
    expect(await screen.findByText("That week is already over.")).toBeInTheDocument();
    const body = JSON.parse(((globalThis.fetch as unknown as { mock: { calls: [string, RequestInit][] } }).mock.calls[1][1].body) as string);
    expect(body.client_today).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});
