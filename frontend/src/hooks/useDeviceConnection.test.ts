import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useDeviceConnection } from "./useDeviceConnection";
import { WebAuthSession } from "../utils/webAuthSession";

vi.mock("../utils/webAuthSession", () => ({ WebAuthSession: { start: vi.fn() } }));

function jsonResponse(body: unknown, ok = true) {
  return { ok, json: async () => body } as Response;
}

describe("useDeviceConnection", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    localStorage.clear();
    localStorage.setItem("uphill_session_token", "tok-abc");
  });

  it("loads connection status", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ coros: { connected: true, last_sync_at: "2026-09-05T00:00:00Z" } })
    );
    const { result } = renderHook(() => useDeviceConnection());
    await act(async () => { await result.current.refreshStatus(); });
    expect(result.current.status?.coros.connected).toBe(true);
  });

  it("sends the session token on every request", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ coros: { connected: false } }));
    const { result } = renderHook(() => useDeviceConnection());
    await act(async () => { await result.current.refreshStatus(); });
    const headers = fetchMock.mock.calls[0][1].headers;
    expect(headers["Authorization"]).toBe("Bearer tok-abc");
  });

  it("requests the authorize URL with credentials included", async () => {
    // Without credentials:"include" the browser drops the HttpOnly state cookie
    // and every OAuth callback fails its CSRF check.
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ authorize_url: "https://coros/auth?x=1" }));
    const { result } = renderHook(() => useDeviceConnection());
    let url = "";
    await act(async () => { url = await result.current.connectCoros(); });
    expect(fetchMock.mock.calls[0][1].credentials).toBe("include");
    expect(url).toBe("https://coros/auth?x=1");
  });

  it("surfaces a clear message when the integration is not configured", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: "not configured" }, false));
    const { result } = renderHook(() => useDeviceConnection());
    await act(async () => { await result.current.connectCoros(); });
    expect(result.current.error).toBeTruthy();
  });

  it("reports how much was synced", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ activities: 4, daily_metrics: 7 }));
    const { result } = renderHook(() => useDeviceConnection());
    let synced: { activities: number } | null = null;
    await act(async () => { synced = await result.current.syncNow(); });
    expect(synced!.activities).toBe(4);
  });

  it("asks the athlete to reconnect when the backend says the token is gone", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: "reconnect required" }, false));
    const { result } = renderHook(() => useDeviceConnection());
    await act(async () => { await result.current.syncNow(); });
    expect(result.current.error).toMatch(/reconnect/i);
  });

  it("disconnects and clears status", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ status: "disconnected" }));
    fetchMock.mockResolvedValueOnce(jsonResponse({ coros: { connected: false } }));
    const { result } = renderHook(() => useDeviceConnection());
    await act(async () => { await result.current.disconnectCoros(); });
    expect(result.current.status?.coros.connected).toBe(false);
  });

  describe("connectCorosNative", () => {
    const startMock = () => WebAuthSession.start as unknown as ReturnType<typeof vi.fn>;

    it("redeems the one-time token from the app callback with the session", async () => {
      const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
      fetchMock
        .mockResolvedValueOnce(jsonResponse({ authorize_url: "https://coros/auth?state=st1" }))
        .mockResolvedValueOnce(jsonResponse({ connected: true }));
      startMock().mockResolvedValueOnce({ url: "uphillai://coros/callback?state=st1&token=tk1" });
      const { result } = renderHook(() => useDeviceConnection());

      let ok = false;
      await act(async () => { ok = await result.current.connectCorosNative(); });

      expect(ok).toBe(true);
      expect(fetchMock.mock.calls[0][0]).toContain("/api/integrations/coros/connect?platform=native");
      expect(startMock()).toHaveBeenCalledWith({ url: "https://coros/auth?state=st1", callbackScheme: "uphillai" });
      expect(fetchMock.mock.calls[1][0]).toContain("/api/integrations/coros/complete");
      expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toEqual({ state: "st1", token: "tk1" });
      expect(fetchMock.mock.calls[1][1].headers["Authorization"]).toBe("Bearer tok-abc");
      expect(result.current.error).toBe("");
    });

    it("stays quiet when the user closes the consent page", async () => {
      const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(jsonResponse({ authorize_url: "https://coros/auth?x=1" }));
      startMock().mockRejectedValueOnce(Object.assign(new Error("Cancelled"), { code: "CANCELLED" }));
      const { result } = renderHook(() => useDeviceConnection());

      let ok = true;
      await act(async () => { ok = await result.current.connectCorosNative(); });

      expect(ok).toBe(false);
      expect(result.current.error).toBe("");
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it("reports an error callback without calling complete", async () => {
      const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(jsonResponse({ authorize_url: "https://coros/auth?x=1" }));
      startMock().mockResolvedValueOnce({ url: "uphillai://coros/callback?result=error" });
      const { result } = renderHook(() => useDeviceConnection());

      let ok = true;
      await act(async () => { ok = await result.current.connectCorosNative(); });

      expect(ok).toBe(false);
      expect(result.current.error).toBe("COROS connection failed. Please try again.");
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it("surfaces a rejected completion", async () => {
      const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
      fetchMock
        .mockResolvedValueOnce(jsonResponse({ authorize_url: "https://coros/auth?state=st1" }))
        .mockResolvedValueOnce(jsonResponse({ detail: "COROS connection could not be completed." }, false));
      startMock().mockResolvedValueOnce({ url: "uphillai://coros/callback?state=st1&token=tk1" });
      const { result } = renderHook(() => useDeviceConnection());

      let ok = true;
      await act(async () => { ok = await result.current.connectCorosNative(); });

      expect(ok).toBe(false);
      expect(result.current.error).toBe("COROS connection could not be completed.");
    });

    it("rejects a callback for a different attempt without calling complete", async () => {
      const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(jsonResponse({ authorize_url: "https://coros/auth?state=st1" }));
      startMock().mockResolvedValueOnce({ url: "uphillai://coros/callback?state=other&token=tk1" });
      const { result } = renderHook(() => useDeviceConnection());

      let ok = true;
      await act(async () => { ok = await result.current.connectCorosNative(); });

      expect(ok).toBe(false);
      expect(result.current.error).toBe("COROS connection failed. Please try again.");
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });
  });
});
