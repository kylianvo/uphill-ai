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

  it("debounces and fetches a match for a valid name", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        matched: true,
        race_name: "Vietnam Mountain Marathon",
        distance_label: "50km",
        distance_km: 46.7,
        elevation_gain_m: 2800,
        terrain: ["rice terraces"],
      })
    );

    const { result, rerender } = renderHook(({ name }) => useRaceMatch(name), {
      initialProps: { name: "VM" },
    });
    expect(result.current).toBeNull();

    rerender({ name: "VMM" });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url] = fetchMock.mock.calls[0];
    expect(url).toContain("/api/kb/match-race");
    expect(url).toContain("name=VMM");
    expect(result.current?.race_name).toBe("Vietnam Mountain Marathon");
  });

  it("returns null when the backend reports no match", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ matched: false }));

    const { result } = renderHook(() => useRaceMatch("Totally Unknown Race"));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    expect(result.current).toBeNull();
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
});
