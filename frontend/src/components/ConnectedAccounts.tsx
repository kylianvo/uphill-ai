"use client";

import { useEffect, useState } from "react";
import { Watch, CheckCircle, Warning, Lightning } from "@phosphor-icons/react";
import { useAppContext } from "../contexts/AppContext";
import { useDeviceConnection } from "../hooks/useDeviceConnection";
import CorosAttribution from "./CorosAttribution";

// The hook's own fallback error strings (used when the backend response has
// no `detail`, e.g. a network failure). Arbitrary backend `detail` text
// (e.g. "reconnect required") is passed through untranslated -- the backend
// does not yet return bilingual error detail, so that stays English-only
// until it does.
const ERROR_TRANSLATIONS_VI: Record<string, string> = {
  "Could not load connection status.": "Không thể tải trạng thái kết nối. Vui lòng thử lại.",
  "COROS connection is unavailable.": "Không thể kết nối COROS lúc này. Vui lòng thử lại sau.",
  "Sync failed. Please try again.": "Đồng bộ thất bại. Vui lòng thử lại.",
  "Could not disconnect.": "Không thể ngắt kết nối. Vui lòng thử lại.",
};

export default function ConnectedAccounts() {
  const { lang } = useAppContext();
  const { status, loading, error, refreshStatus, connectCoros, disconnectCoros, syncNow, syncFitness } =
    useDeviceConnection();
  const [syncingFitness, setSyncingFitness] = useState(false);
  // Read the OAuth-callback redirect params (?coros=connected|error) during
  // the initial render rather than in an effect -- setState calls in an
  // effect body run as an extra, avoidable re-render pass.
  const [notice, setNotice] = useState(() => {
    if (typeof window === "undefined") return "";
    const result = new URLSearchParams(window.location.search).get("coros");
    if (result === "connected") {
      return lang === "vi" ? "Đã kết nối COROS." : "COROS connected.";
    }
    if (result === "error") {
      return lang === "vi"
        ? "Kết nối COROS thất bại. Vui lòng thử lại."
        : "COROS connection failed. Please try again.";
    }
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

  const displayError = error ? (lang === "vi" ? ERROR_TRANSLATIONS_VI[error] ?? error : error) : "";

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
      setNotice(
        lang === "vi"
          ? `Đã đồng bộ ${result.activities} hoạt động và ${result.daily_metrics} ngày dữ liệu sức khỏe.`
          : `Synced ${result.activities} activities and ${result.daily_metrics} days of health data.`
      );
      await refreshStatus();
    }
  };

  const handleSyncFitness = async () => {
    setSyncingFitness(true);
    try {
      const result = await syncFitness();
      if (result) {
        setNotice(
          lang === "vi"
            ? `Đã đồng bộ EvoLab: Ngưỡng pace ${result.threshold_pace || "—"}/km, VO2max ${result.coros_vo2max || "—"}.`
            : `Synced EvoLab: Threshold pace ${result.threshold_pace || "—"}/km, VO2max ${result.coros_vo2max || "—"}.`
        );
        await refreshStatus();
      }
    } finally {
      setSyncingFitness(false);
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
        {lang === "vi" ? "Tài khoản đã kết nối" : "Connected accounts"}
      </h3>
      <p className="device-help">
        {lang === "vi"
          ? "Kết nối đồng hồ của bạn để các buổi chạy đã hoàn thành được tự động khớp với kế hoạch tập luyện."
          : "Connect your watch so completed runs are matched to your plan automatically."}
      </p>

      <div className="device-row">
        <div>
          <strong className="device-name">COROS</strong>
          <div className="device-state">
            {checkingConnection
              ? lang === "vi"
                ? "Đang kiểm tra kết nối..."
                : "Checking connection..."
              : connected
                ? status?.coros?.last_sync_at
                  ? `${lang === "vi" ? "Đồng bộ lần cuối" : "Last synced"} ${new Date(status.coros.last_sync_at).toLocaleString()}`
                  : lang === "vi"
                    ? "Đã kết nối"
                    : "Connected"
                : lang === "vi"
                  ? "Chưa kết nối"
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
                <button
                  type="button"
                  className="device-btn"
                  onClick={handleSyncFitness}
                  disabled={loading || syncingFitness}
                  style={{ display: "inline-flex", alignItems: "center", gap: "5px" }}
                  aria-label={lang === "vi" ? "Đồng bộ chỉ số EvoLab và pace zones" : "Sync EvoLab fitness metrics and pace zones"}
                >
                  <Lightning size={13} weight="bold" style={{ color: "var(--accent-primary)" }} aria-hidden="true" />
                  <span>
                    {syncingFitness
                      ? lang === "vi"
                        ? "Đang đồng bộ..."
                        : "Syncing..."
                      : lang === "vi"
                        ? "Đồng bộ EvoLab"
                        : "Sync EvoLab"}
                  </span>
                </button>
                <button type="button" className="device-btn" onClick={handleSync} disabled={loading || syncingFitness}>
                  {loading
                    ? lang === "vi"
                      ? "Đang đồng bộ..."
                      : "Syncing..."
                    : lang === "vi"
                      ? "Đồng bộ ngay"
                      : "Sync now"}
                </button>
                <button
                  type="button"
                  className="device-btn device-btn-danger"
                  onClick={handleDisconnect}
                  disabled={loading || syncingFitness}
                >
                  {lang === "vi" ? "Ngắt kết nối" : "Disconnect"}
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
                {lang === "vi" ? "Kết nối" : "Connect"}
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
      {displayError && (
        <p className="device-error">
          <Warning size={14} weight="fill" />
          {displayError}
        </p>
      )}

      <p className="device-help">
        {lang === "vi"
          ? "Khi ngắt kết nối, dữ liệu chúng tôi nhận được từ COROS sẽ được xóa trong vòng 24 giờ."
          : "Disconnecting deletes the data we received from COROS within 24 hours."}
      </p>
    </div>
  );
}
