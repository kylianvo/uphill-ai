import { useCallback, useState } from "react";
import { WebAuthSession } from "../utils/webAuthSession";

function getBackendUrl(): string {
  if (typeof window !== "undefined") {
    const override = localStorage.getItem("UPHILL_API_URL_OVERRIDE");
    if (override) return override;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export type DeviceStatus = {
  coros: { connected: boolean; last_sync_at?: string | null };
};

export type SyncResult = { activities: number; daily_metrics: number };

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("uphill_session_token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export function useDeviceConnection() {
  const [status, setStatus] = useState<DeviceStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const refreshStatus = useCallback(async () => {
    const API_BASE_URL = getBackendUrl();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/integrations/status`, {
        method: "GET",
        headers: authHeaders(),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body?.detail || "Could not load connection status.");
      setStatus(body as DeviceStatus);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load connection status.");
    } finally {
      setLoading(false);
    }
  }, []);

  const connectCoros = useCallback(async (): Promise<string> => {
    const API_BASE_URL = getBackendUrl();
    setLoading(true);
    setError("");
    try {
      // credentials:"include" is set -- the backend sets an HttpOnly state
      // cookie here that the OAuth callback checks for CSRF protection when enabled.
      // We also pass return_url so the callback redirects the athlete back to
      // the exact origin they initiated connect from (e.g. preview, localhost, or prod).
      const returnUrl = typeof window !== "undefined" ? window.location.origin + window.location.pathname : "";
      const query = returnUrl ? `?return_url=${encodeURIComponent(returnUrl)}` : "";
      const res = await fetch(`${API_BASE_URL}/api/integrations/coros/connect${query}`, {
        method: "GET",
        headers: authHeaders(),
        credentials: "include",
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body?.detail || "COROS connection is unavailable.");
      return body.authorize_url as string;
    } catch (e) {
      setError(e instanceof Error ? e.message : "COROS connection is unavailable.");
      return "";
    } finally {
      setLoading(false);
    }
  }, []);

  const syncNow = useCallback(async (days = 30): Promise<SyncResult | null> => {
    const API_BASE_URL = getBackendUrl();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/integrations/coros/sync?days=${days}`, {
        method: "POST",
        headers: authHeaders(),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body?.detail || "Sync failed. Please try again.");
      return body as SyncResult;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sync failed. Please try again.");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const syncFitness = useCallback(async () => {
    const API_BASE_URL = getBackendUrl();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/integrations/coros/sync-fitness`, {
        method: "POST",
        headers: authHeaders(),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body?.detail || "Fitness sync failed. Please try again.");
      return body as {
        status: string;
        threshold_pace?: string;
        coros_vo2max?: number;
        coros_running_level?: number;
        pace_zones?: Record<string, unknown>;
      };
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fitness sync failed. Please try again.");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const disconnectCoros = useCallback(async () => {
    const API_BASE_URL = getBackendUrl();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/integrations/coros`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body?.detail || "Could not disconnect.");
      await refreshStatus();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not disconnect.");
    } finally {
      setLoading(false);
    }
  }, [refreshStatus]);

  // The app's WebView and the system browser showing COROS consent don't share
  // cookies, so the native flow can't use the web redirect. The backend hands a
  // one-time token to the consent page, which returns it via uphillai://, and
  // the app redeems it with its own session. Resolves true once connected.
  const connectCorosNative = useCallback(async (): Promise<boolean> => {
    const API_BASE_URL = getBackendUrl();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/integrations/coros/connect?platform=native`, {
        method: "GET",
        headers: authHeaders(),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body?.detail || "COROS connection is unavailable.");

      let callbackUrl: string;
      try {
        ({ url: callbackUrl } = await WebAuthSession.start({
          url: body.authorize_url,
          callbackScheme: "uphillai",
        }));
      } catch (e) {
        if ((e as { code?: string })?.code === "CANCELLED") return false;
        throw new Error("COROS connection failed. Please try again.");
      }

      const params = new URL(callbackUrl).searchParams;
      const state = params.get("state");
      const token = params.get("token");
      // Ignore a stray uphillai:// link that isn't the answer to this attempt.
      const expectedState = new URL(body.authorize_url).searchParams.get("state");
      if (!state || !token || state !== expectedState) {
        throw new Error("COROS connection failed. Please try again.");
      }

      const completeRes = await fetch(`${API_BASE_URL}/api/integrations/coros/complete`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ state, token }),
      });
      const completeBody = await completeRes.json();
      if (!completeRes.ok) throw new Error(completeBody?.detail || "COROS connection failed. Please try again.");
      return true;
    } catch (e) {
      setError(e instanceof Error ? e.message : "COROS connection failed. Please try again.");
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    status,
    loading,
    error,
    refreshStatus,
    connectCoros,
    connectCorosNative,
    disconnectCoros,
    syncNow,
    syncFitness,
  };
}
