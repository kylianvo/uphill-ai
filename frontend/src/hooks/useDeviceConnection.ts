import { useCallback, useState } from "react";

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
      // credentials:"include" is REQUIRED -- the backend sets an HttpOnly state
      // cookie here that the OAuth callback checks for CSRF protection. The
      // frontend (uphill-ai.io.vn) and API (api.uphill-ai.io.vn) are cross-origin,
      // so without this flag the browser silently drops the Set-Cookie and every
      // connect attempt dies later at the callback with ?coros=error (backend logs
      // `callback_state_cookie_absent` in exactly that case).
      const res = await fetch(`${API_BASE_URL}/api/integrations/coros/connect`, {
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

  return { status, loading, error, refreshStatus, connectCoros, disconnectCoros, syncNow, syncFitness };
}
