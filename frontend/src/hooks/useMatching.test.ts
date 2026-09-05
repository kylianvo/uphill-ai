import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useMatching } from "./useMatching";

function jsonResponse(body: unknown, ok = true) {
  return { ok, json: async () => body } as Response;
}

describe("useMatching", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    localStorage.clear();
    localStorage.setItem("uphill_session_token", "tok-abc");
  });

  it("runs matching and returns the counts", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ matched: 3, suggested: 1, unmatched: 2, skipped_manual: 0 })
    );
    const { result } = renderHook(() => useMatching());
    let counts: { matched: number } | null = null;
    await act(async () => { counts = await result.current.runMatching(30); });
    expect(counts!.matched).toBe(3);
  });

  it("confirms a match by PATCHing the activity", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ status: "ok", workout_id: 42 }));
    const { result } = renderHook(() => useMatching());
    await act(async () => { await result.current.confirmMatch(7, 42); });
    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toContain("/api/integrations/matching/7");
    expect(opts.method).toBe("PATCH");
  });

  it("clears a match by sending a null workout", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ status: "ok", workout_id: null }));
    const { result } = renderHook(() => useMatching());
    await act(async () => { await result.current.clearMatch(7); });
    expect(fetchMock.mock.calls[0][0]).not.toContain("workout_id=4");
  });

  it("surfaces an error message when matching fails", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: "days must be between 1 and 365." }, false));
    const { result } = renderHook(() => useMatching());
    await act(async () => { await result.current.runMatching(9999); });
    expect(result.current.error).toMatch(/days must be/);
  });

  it("treats a 404 from a manual correction as not found, not a crash", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: "Activity not found." }, false));
    const { result } = renderHook(() => useMatching());
    let ok = true;
    await act(async () => { ok = await result.current.confirmMatch(999, 42); });
    expect(ok).toBe(false);
    expect(result.current.error).toMatch(/not found/i);
  });

  it("sends the session token on every request", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ matched: 0, suggested: 0, unmatched: 0, skipped_manual: 0 }));
    const { result } = renderHook(() => useMatching());
    await act(async () => { await result.current.runMatching(30); });
    const headers = fetchMock.mock.calls[0][1].headers;
    expect(headers["Authorization"]).toBe("Bearer tok-abc");
  });
});
