import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePaceZones } from "./usePaceZones";

function jsonResponse(body: unknown, ok = true) {
  return { ok, json: async () => body } as Response;
}

describe("usePaceZones", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    localStorage.clear();
  });

  it("fetches and stores the current user's pace zones", async () => {
    localStorage.setItem("uphill_session_token", "tok-abc");
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    const body = {
      zone1_pace: "6:53 - 6:04",
      zone2_pace: "6:30 - 5:45",
      zone3_pace: "5:16 - 4:40",
      zone4_pace: "4:48 - 4:15",
      zone5_pace: "4:14 - 3:45",
    };
    fetchMock.mockResolvedValueOnce(jsonResponse(body));

    const { result } = renderHook(() => usePaceZones());
    expect(result.current.zones).toBeNull();

    await act(async () => {
      await result.current.fetchPaceZones();
    });

    expect(result.current.zones).toEqual(body);
    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toContain("/api/auth/pace-zones");
    expect((opts.headers as Record<string, string>)["Authorization"]).toBe("Bearer tok-abc");
  });

  it("does not call fetch when there is no session token", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    const { result } = renderHook(() => usePaceZones());

    await act(async () => {
      await result.current.fetchPaceZones();
    });

    expect(fetchMock).not.toHaveBeenCalled();
    expect(result.current.zones).toBeNull();
  });

  it("leaves zones unset when the request fails", async () => {
    localStorage.setItem("uphill_session_token", "tok-abc");
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({}, false));

    const { result } = renderHook(() => usePaceZones());
    await act(async () => {
      await result.current.fetchPaceZones();
    });

    expect(result.current.zones).toBeNull();
  });
});
