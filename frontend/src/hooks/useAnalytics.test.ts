import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

// eventQueue is a module-level singleton (not exported), so each test resets
// modules and re-imports fresh to avoid queue state leaking across tests.
async function freshUseAnalytics() {
  vi.resetModules();
  const mod = await import("./useAnalytics");
  return mod.useAnalytics;
}

function jsonResponse(ok = true) {
  return { ok } as Response;
}

describe("useAnalytics", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    localStorage.clear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("batches tracked events and sends them on the periodic flush", async () => {
    const useAnalytics = await freshUseAnalytics();
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse(true));

    const { result } = renderHook(() => useAnalytics());

    act(() => {
      result.current.trackEvent("plan_generated", { goal_type: "finish" });
    });

    // flushEvents runs on a 5s interval (see useAnalytics.ts's useEffect).
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toContain("/api/analytics/track_batch");
    const body = JSON.parse(opts.body as string);
    expect(body.events).toHaveLength(1);
    expect(body.events[0]).toMatchObject({ event_name: "plan_generated", properties: { goal_type: "finish" } });
  });

  it("re-queues the batch and resends it after a failed flush", async () => {
    const useAnalytics = await freshUseAnalytics();
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse(false)); // first flush fails
    fetchMock.mockResolvedValueOnce(jsonResponse(true)); // second flush succeeds

    const { result } = renderHook(() => useAnalytics());

    act(() => {
      result.current.trackEvent("workout_logged");
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000); // fails, event goes back into the queue
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000); // succeeds, should resend the same event
    });

    expect(fetchMock).toHaveBeenCalledTimes(2);
    const secondBody = JSON.parse(fetchMock.mock.calls[1][1].body as string);
    expect(secondBody.events).toHaveLength(1);
    expect(secondBody.events[0].event_name).toBe("workout_logged");
  });

  it("includes the auth token in the flush request when a session token is present", async () => {
    const useAnalytics = await freshUseAnalytics();
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse(true));
    localStorage.setItem("uphill_session_token", "tok-xyz");

    const { result } = renderHook(() => useAnalytics());
    act(() => {
      result.current.trackEvent("plan_generated");
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });

    const [, opts] = fetchMock.mock.calls[0];
    const headers = opts.headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer tok-xyz");
  });

  it("does not flush when the event queue is empty", async () => {
    const useAnalytics = await freshUseAnalytics();
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;

    renderHook(() => useAnalytics());
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });

    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("generates and persists a session id on mount", async () => {
    const useAnalytics = await freshUseAnalytics();
    expect(localStorage.getItem("uphill_session_id")).toBeNull();

    renderHook(() => useAnalytics());

    expect(localStorage.getItem("uphill_session_id")).toBeTruthy();
  });
});
