import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useRaceMatch } from "./useRaceMatch";

function jsonResponse(body: unknown, ok = true) {
  return { ok, json: async () => body } as Response;
}

describe("useRaceMatch", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    localStorage.clear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("does not query for names shorter than 3 characters", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    renderHook(() => useRaceMatch("VM"));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("auto-applies a dominant match as selectedMatch with no candidates", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        matched: true,
        auto_apply: true,
        match: {
          race_name: "Vietnam Mountain Marathon",
          distance_label: "50km",
          distance_km: 46.7,
          elevation_gain_m: 2800,
          terrain: ["rice terraces"],
        },
      })
    );

    const { result, rerender } = renderHook(({ name }) => useRaceMatch(name), {
      initialProps: { name: "VM" },
    });
    expect(result.current.selectedMatch).toBeNull();

    rerender({ name: "VMM" });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url] = fetchMock.mock.calls[0];
    expect(url).toContain("/api/kb/match-race");
    expect(url).toContain("name=VMM");
    expect(result.current.selectedMatch?.race_name).toBe("Vietnam Mountain Marathon");
    expect(result.current.candidates).toEqual([]);
  });

  it("surfaces candidates instead of auto-applying when the match is ambiguous", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        matched: true,
        auto_apply: false,
        match: {
          race_name: "Marathon du Mont-Blanc",
          distance_label: null,
          distance_km: null,
          elevation_gain_m: null,
          terrain: [],
        },
        candidates: [
          {
            race_name: "Marathon du Mont-Blanc",
            distance_label: "42km",
            distance_km: 42,
            elevation_gain_m: 2500,
            terrain: [],
            score: 100,
          },
          {
            race_name: "Cross du Mont-Blanc",
            distance_label: "23km",
            distance_km: 23,
            elevation_gain_m: 1400,
            terrain: [],
            score: 100,
          },
        ],
      })
    );

    const { result } = renderHook(() => useRaceMatch("Marathon du Mont Blanc"));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    expect(result.current.selectedMatch).toBeNull();
    expect(result.current.candidates).toHaveLength(2);
  });

  it("selectCandidate applies the chosen candidate and clears the candidate list", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        matched: true,
        auto_apply: false,
        match: {
          race_name: "Marathon du Mont-Blanc",
          distance_label: null,
          distance_km: null,
          elevation_gain_m: null,
          terrain: [],
        },
        candidates: [
          {
            race_name: "Marathon du Mont-Blanc",
            distance_label: "42km",
            distance_km: 42,
            elevation_gain_m: 2500,
            terrain: [],
            score: 100,
          },
          {
            race_name: "Cross du Mont-Blanc",
            distance_label: "23km",
            distance_km: 23,
            elevation_gain_m: 1400,
            terrain: [],
            score: 100,
          },
        ],
      })
    );

    const { result } = renderHook(() => useRaceMatch("Marathon du Mont Blanc"));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    act(() => {
      result.current.selectCandidate(result.current.candidates[1]);
    });

    expect(result.current.selectedMatch?.race_name).toBe("Cross du Mont-Blanc");
    expect(result.current.candidates).toEqual([]);
  });

  it("reopenPicker restores the last candidate set, including a solo auto-applied match", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        matched: true,
        auto_apply: true,
        match: {
          race_name: "Vietnam Mountain Marathon",
          distance_label: "50km",
          distance_km: 46.7,
          elevation_gain_m: 2800,
          terrain: ["rice terraces"],
        },
      })
    );

    const { result } = renderHook(() => useRaceMatch("VMM"));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });
    expect(result.current.candidates).toEqual([]);

    act(() => {
      result.current.reopenPicker();
    });

    expect(result.current.candidates).toHaveLength(1);
    expect(result.current.candidates[0].race_name).toBe("Vietnam Mountain Marathon");
  });

  it("dismissCandidates clears the dropdown without applying a match", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        matched: true,
        auto_apply: false,
        match: {
          race_name: "Marathon du Mont-Blanc",
          distance_label: null,
          distance_km: null,
          elevation_gain_m: null,
          terrain: [],
        },
        candidates: [
          {
            race_name: "Marathon du Mont-Blanc",
            distance_label: "42km",
            distance_km: 42,
            elevation_gain_m: 2500,
            terrain: [],
            score: 100,
          },
          {
            race_name: "Cross du Mont-Blanc",
            distance_label: "23km",
            distance_km: 23,
            elevation_gain_m: 1400,
            terrain: [],
            score: 100,
          },
        ],
      })
    );

    const { result } = renderHook(() => useRaceMatch("Marathon du Mont Blanc"));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    act(() => {
      result.current.dismissCandidates();
    });

    expect(result.current.candidates).toEqual([]);
    expect(result.current.selectedMatch).toBeNull();
  });

  it("returns no match when the backend reports no match", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ matched: false }));

    const { result } = renderHook(() => useRaceMatch("Totally Unknown Race"));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    expect(result.current.selectedMatch).toBeNull();
    expect(result.current.candidates).toEqual([]);
  });

  it("includes distanceKm in the query string when provided", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ matched: false }));

    renderHook(() => useRaceMatch("VMM", { distanceKm: 50 }));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    const [url] = fetchMock.mock.calls[0];
    expect(url).toContain("distance_km=50");
  });

  it("clears a stale match when the name is shortened back below the minimum length", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        matched: true,
        auto_apply: true,
        match: {
          race_name: "Vietnam Mountain Marathon",
          distance_label: "50km",
          distance_km: 46.7,
          elevation_gain_m: 2800,
          terrain: ["rice terraces"],
        },
      })
    );

    const { result, rerender } = renderHook(({ name }) => useRaceMatch(name), {
      initialProps: { name: "VMM" },
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });
    expect(result.current.selectedMatch?.race_name).toBe("Vietnam Mountain Marathon");

    rerender({ name: "VM" });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });
    expect(result.current.selectedMatch).toBeNull();
  });
});
