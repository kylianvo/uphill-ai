import { describe, it, expect, vi, beforeEach } from "vitest";
import { act } from "@testing-library/react";
import { renderHookWithApp } from "../test-utils/renderWithAppContext";
import { useCoachOverview } from "./useCoachOverview";

function jsonResponse(body: unknown, ok = true) {
  return { ok, json: async () => body } as Response;
}

const SAMPLE_OVERVIEW = {
  athletes: [
    {
      athlete_id: 10,
      name: "Jane Runner",
      active_plan: { plan_id: 1, race_name: "VMM 70km", race_date: "2026-11-15", current_week: 9, total_weeks: 16 },
      adherence_pct_14d: 0.83,
      last_completed: { week_number: 9, day_of_week: "Wednesday" },
      missed_streak: 0,
    },
  ],
  action_items: { draft_plans: [], pending_workout_approvals: [] },
  phase_alerts: [{ athlete_id: 10, athlete_name: "Jane Runner", phase: "taper", starts: "this_week" }],
  workout_type_mix: [{ type: "long_run", count: 14, pct: 0.28 }],
};

describe("useCoachOverview", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    localStorage.setItem("uphill_session_token", "test-token");
  });

  it("fetchOverview populates overview state", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse(SAMPLE_OVERVIEW));
    const { result } = renderHookWithApp(() => useCoachOverview());

    await act(async () => {
      await result.current.fetchOverview();
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/coaching/overview"),
      expect.objectContaining({ headers: expect.anything() })
    );
    expect(result.current.overview).toEqual(SAMPLE_OVERVIEW);
    expect(result.current.overviewLoading).toBe(false);
    expect(result.current.overviewError).toBe("");
  });

  it("sets overviewError and leaves overview null when the request fails", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: "Coach access required." }, false));
    const { result } = renderHookWithApp(() => useCoachOverview());

    await act(async () => {
      await result.current.fetchOverview();
    });

    expect(result.current.overview).toBeNull();
    expect(result.current.overviewError).toBe("Coach access required.");
    expect(result.current.overviewLoading).toBe(false);
  });
});
