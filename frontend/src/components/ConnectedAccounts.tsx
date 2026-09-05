"use client";

import { useEffect, useState } from "react";
import { Watch, CheckCircle, Warning } from "@phosphor-icons/react";
import { useDeviceConnection } from "../hooks/useDeviceConnection";
import CorosAttribution from "./CorosAttribution";

export default function ConnectedAccounts() {
  const { status, loading, error, refreshStatus, connectCoros, disconnectCoros, syncNow } =
    useDeviceConnection();
  // Read the OAuth-callback redirect params (?coros=connected|error) during
  // the initial render rather than in an effect -- setState calls in an
  // effect body run as an extra, avoidable re-render pass.
  const [notice, setNotice] = useState(() => {
    if (typeof window === "undefined") return "";
    const result = new URLSearchParams(window.location.search).get("coros");
    if (result === "connected") return "COROS connected.";
    if (result === "error") return "COROS connection failed. Please try again.";
    return "";
  });

  useEffect(() => {
    refreshStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const connected = Boolean(status?.coros?.connected);
  // The first fetch on mount: status is still null and a request is in
  // flight. Rendering "Not connected" here would flash the wrong state for
  // anyone who is actually connected, so this gets its own row instead of
  // falling through to the disconnected branch.
  const checkingConnection = status === null && loading;

  const handleConnect = async () => {
    // connectCoros() does NOT throw on failure -- it records the problem in
    // `error` and resolves to "". Navigating unconditionally would send the
    // browser to "" (i.e. reload the current page), silently swallowing the
    // error this component is supposed to show. Only navigate on a real URL.
    const url = await connectCoros();
    if (url) {
      window.location.href = url;
    }
  };

  const handleSync = async () => {
    const result = await syncNow();
    if (result) {
      setNotice(`Synced ${result.activities} activities and ${result.daily_metrics} days of health data.`);
      await refreshStatus();
    }
  };

  const handleDisconnect = async () => {
    await disconnectCoros();
    setNotice("");
  };

  return (
    <div className="device-section">
      <h3 className="device-heading">
        <Watch size={16} weight="duotone" style={{ color: "var(--accent-primary)" }} />
        Connected accounts
      </h3>
      <p className="device-help">
        Connect your watch so completed runs are matched to your plan automatically.
      </p>

      <div className="device-row">
        <div>
          <strong className="device-name">COROS</strong>
          <div className="device-state">
            {checkingConnection
              ? "Checking connection..."
              : connected
                ? status?.coros?.last_sync_at
                  ? `Last synced ${new Date(status.coros.last_sync_at).toLocaleString()}`
                  : "Connected"
                : "Not connected"}
          </div>
          {connected && (
            <div style={{ marginTop: "4px" }}>
              <CorosAttribution deviceModel={null} />
            </div>
          )}
        </div>

        {checkingConnection ? (
          <div className="device-actions">
            <span className="device-skeleton" aria-hidden="true" />
          </div>
        ) : (
          <div className="device-actions">
            {connected ? (
              <>
                <button type="button" className="device-btn" onClick={handleSync} disabled={loading}>
                  {loading ? "Syncing..." : "Sync now"}
                </button>
                <button
                  type="button"
                  className="device-btn device-btn-danger"
                  onClick={handleDisconnect}
                  disabled={loading}
                >
                  Disconnect
                </button>
              </>
            ) : (
              <button
                type="button"
                className="btn btn-primary"
                style={{ height: "32px", fontSize: "12.5px", padding: "0 14px" }}
                onClick={handleConnect}
                disabled={loading}
              >
                Connect
              </button>
            )}
          </div>
        )}
      </div>

      {notice && (
        <p className="device-notice">
          <CheckCircle size={14} weight="fill" />
          {notice}
        </p>
      )}
      {error && (
        <p className="device-error">
          <Warning size={14} weight="fill" />
          {error}
        </p>
      )}

      <p className="device-help">
        Disconnecting deletes the data we received from COROS within 24 hours.
      </p>
    </div>
  );
}
