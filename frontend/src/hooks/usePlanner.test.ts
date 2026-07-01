import { describe, it, expect, vi, beforeEach } from "vitest";
import { act } from "@testing-library/react";
import { renderHookWithApp } from "../test-utils/renderWithAppContext";
import { useAppContext } from "../contexts/AppContext";
import { usePlanner } from "./usePlanner";

function jsonResponse(body: unknown, ok = true) {
  return { ok, json: async () => body } as Response;
}

describe("usePlanner.handleGeneratePlan", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    localStorage.setItem("uphill_session_token", "tok-abc");
  });

  it("sends the user-chosen plan_start_date in the request body for a race goal", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ job_id: "job-1", plan: { id: 1, race_name: "Test Race" } })
    );

    const { result } = renderHookWithApp(() => {
      const ctx = useAppContext();
      const planner = usePlanner();
      return { ctx, planner };
    });

    act(() => {
      result.current.ctx.setPlanForm({
        ...result.current.ctx.planForm,
        plan_goal_category: "race",
        race_name: "Test 50K",
        race_date: "2027-05-01",
        goal_type: "finish",
        plan_start_date: "2027-03-15",
      });
    });

    await act(async () => {
      await result.current.planner.handleGeneratePlan({ preventDefault: () => {} } as React.FormEvent);
    });

    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toContain("/api/coach/generate-plan");
    const body = JSON.parse(opts.body);
    expect(body.plan_start_date).toBe("2027-03-15");
  });

  it("rejects submission for a non-race goal when plan_start_date is missing, without calling fetch", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;

    const { result } = renderHookWithApp(() => {
      const ctx = useAppContext();
      const planner = usePlanner();
      return { ctx, planner };
    });

    act(() => {
      result.current.ctx.setPlanForm({
        ...result.current.ctx.planForm,
        plan_goal_category: "start_running",
        plan_start_date: "",
      });
    });

    await act(async () => {
      await result.current.planner.handleGeneratePlan({ preventDefault: () => {} } as React.FormEvent);
    });

    expect(fetchMock).not.toHaveBeenCalled();
    expect(result.current.ctx.planErrorMsg).toMatch(/plan start date/i);
  });
});

describe("usePlanner.getWorkoutDate", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  it("anchors week 1 on the Monday on or before activePlan.start_date, not the race date", () => {
    const { result } = renderHookWithApp(() => {
      const ctx = useAppContext();
      const planner = usePlanner();
      return { ctx, planner };
    });

    // 2026-08-23 is a Sunday; the Monday on/before it is 2026-08-17.
    act(() => {
      result.current.ctx.setActivePlan({
        id: 1,
        start_date: "2026-08-23",
        race_date: "2026-12-06",
        total_weeks: 17,
      });
    });

    const week1Monday = result.current.planner.getWorkoutDate({
      week_number: 1,
      day_of_week: "Monday",
    } as never);

    expect(week1Monday).toBe("Aug 17");
  });

  it("falls back to anchoring from race_date when start_date is absent (legacy plans)", () => {
    const { result } = renderHookWithApp(() => {
      const ctx = useAppContext();
      const planner = usePlanner();
      return { ctx, planner };
    });

    act(() => {
      result.current.ctx.setActivePlan({
        id: 1,
        start_date: null,
        race_date: "2026-12-06",
        total_weeks: 2,
      });
      result.current.ctx.setWorkouts([
        { id: 1, week_number: 2, day_of_week: "Sunday", title: "Target Event", type: "race" },
      ]);
    });

    const date = result.current.planner.getWorkoutDate({
      week_number: 2,
      day_of_week: "Sunday",
    } as never);

    // Race is week 2, so week 2's Sunday should land exactly on race_date.
    expect(date).toBe("Dec 6");
  });
});
