import { describe, it, expect, vi, beforeEach } from "vitest";
import { act } from "@testing-library/react";
import { renderHookWithApp } from "../test-utils/renderWithAppContext";
import { useCoachDashboard } from "./useCoachDashboard";

function jsonResponse(body: unknown, ok = true) {
  return { ok, json: async () => body } as Response;
}

describe("useCoachDashboard", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    localStorage.setItem("uphill_session_token", "test-token");
  });

  it("fetchRoster populates roster state", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse([{ id: 1, athlete_id: 10, status: "active", athlete_email: "a@x.com", athlete_name: "A" }])
    );
    const { result } = renderHookWithApp(() => useCoachDashboard());

    await act(async () => {
      await result.current.fetchRoster();
    });

    expect(result.current.roster).toHaveLength(1);
    expect(result.current.roster[0].athlete_email).toBe("a@x.com");
  });

  it("sendInvite posts to the invite endpoint and refetches the roster", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ id: 2, status: "invited" })) // POST invite
      .mockResolvedValueOnce(jsonResponse([{ id: 2, athlete_id: 11, status: "invited" }])); // GET roster refetch
    const { result } = renderHookWithApp(() => useCoachDashboard());

    await act(async () => {
      await result.current.sendInvite("athlete@x.com");
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/coaching/invite"),
      expect.objectContaining({ method: "POST" })
    );
    expect(result.current.roster).toHaveLength(1);
  });

  it("fetchMyInvites populates pendingInvites state", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse([{ id: 3, coach_id: 5, coach_name: "Coach K", status: "invited" }])
    );
    const { result } = renderHookWithApp(() => useCoachDashboard());

    await act(async () => {
      await result.current.fetchMyInvites();
    });

    expect(result.current.pendingInvites).toHaveLength(1);
    expect(result.current.pendingInvites[0].coach_name).toBe("Coach K");
  });

  it("acceptInvite calls the accept endpoint and clears it from pendingInvites", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ status: "active" }));
    const { result } = renderHookWithApp(() => useCoachDashboard());

    act(() => {
      result.current.setPendingInvites([{ id: 3, coach_id: 5, coach_name: "Coach K", status: "invited" }]);
    });

    await act(async () => {
      await result.current.acceptInvite(3);
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/coaching/invites/3/accept"),
      expect.objectContaining({ method: "POST" })
    );
    expect(result.current.pendingInvites).toHaveLength(0);
  });
});
