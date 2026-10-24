"use client";

import { useState } from "react";
import type { DeviceStatus } from "../hooks/useDeviceConnection";

type Props = {
  lang: "en" | "vi";
  garmin: NonNullable<DeviceStatus["garmin"]>;
  loading: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
};

/**
 * Garmin row in Connected accounts.
 *
 * Garmin Agreement s15.10: the athlete gives explicit consent to AI processing of
 * Garmin data before connecting, and can withdraw it at any time. Every coaching
 * feature is AI, so withdrawing consent is disconnecting (the backend then deletes
 * the Garmin data). Starter access has no history, so data starts at the next watch sync.
 */
export default function GarminConnection({ lang, garmin, loading, onConnect, onDisconnect }: Props) {
  const [consent, setConsent] = useState(false);
  const vi = lang === "vi";

  return (
    <div className="device-row" style={{ alignItems: "flex-start" }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="device-name" style={{ fontWeight: 700, letterSpacing: "0.02em" }}>
          Garmin Connect™
        </div>
        <div className="device-state">
          {garmin.connected
            ? garmin.last_sync_at
              ? `${vi ? "Nhận dữ liệu lần cuối" : "Last data received"} ${new Date(garmin.last_sync_at).toLocaleString()}`
              : vi
                ? "Đã kết nối. Dữ liệu sẽ về sau lần đồng bộ đồng hồ tiếp theo."
                : "Connected. Data arrives after your next watch sync."
            : vi
              ? "Chưa kết nối"
              : "Not connected"}
        </div>
        {garmin.connected && <span className="device-attribution">Garmin</span>}
        {!garmin.connected && (
          <label
            className="device-help"
            // The settings modal styles every <label> as a form caption (uppercase, tracked).
            style={{
              display: "flex",
              gap: "8px",
              marginTop: "8px",
              cursor: "pointer",
              textTransform: "none",
              letterSpacing: "normal",
              fontWeight: 400,
            }}
          >
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              style={{ marginTop: "2px", flexShrink: 0 }}
            />
            <span>
              {vi
                ? "Tôi đồng ý để Coach AI của Uphill AI dùng dữ liệu Garmin của tôi để lên plan và điều chỉnh lịch tập. Rút lại sự đồng ý sẽ ngắt kết nối Garmin và xóa dữ liệu Garmin trong vòng 24 giờ. "
                : "I agree that Uphill AI's AI coach uses my Garmin data to build and adapt my plan. Withdrawing consent disconnects Garmin and deletes its data within 24 hours. "}
              <a href={`${process.env.NEXT_PUBLIC_BASE_PATH || ""}/privacy`} target="_blank" rel="noreferrer">
                {vi ? "Chính sách quyền riêng tư" : "Privacy notice"}
              </a>
            </span>
          </label>
        )}
      </div>

      <div className="device-actions">
        {garmin.connected ? (
          <button type="button" className="device-btn device-btn-danger" onClick={onDisconnect} disabled={loading}>
            {vi ? "Ngắt kết nối" : "Disconnect"}
          </button>
        ) : (
          <button
            type="button"
            className="btn btn-primary"
            style={{ height: "32px", fontSize: "12.5px", padding: "0 14px", opacity: consent ? 1 : 0.45 }}
            onClick={onConnect}
            disabled={loading || !consent}
          >
            {vi ? "Kết nối" : "Connect"}
          </button>
        )}
      </div>
    </div>
  );
}
