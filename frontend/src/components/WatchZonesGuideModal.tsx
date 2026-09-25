import React, { useState } from "react";
import { createPortal } from "react-dom";
import { X, Sparkle, Copy, Check, Watch, Heartbeat } from "@phosphor-icons/react";

export interface WatchZonesGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
  lang: string;
}

export default function WatchZonesGuideModal({
  isOpen,
  onClose,
  lang,
}: WatchZonesGuideModalProps) {
  const [copied, setCopied] = useState(false);
  const [activePlatform, setActivePlatform] = useState<"garmin" | "coros" | "apple" | "others">("garmin");

  if (!isOpen) return null;

  const isVi = lang === "vi";

  const aiPrompt = isVi
    ? "Tôi là vận động viên chạy bộ bền bỉ. Đây là ảnh chụp màn hình các Vùng Nhịp Tim (Heart Rate Zones) và nhịp tim nghỉ/tối đa từ đồng hồ của tôi. Hãy trích xuất giúp tôi: 1) AeT (Ngưỡng hiếu khí - giới hạn trên của Zone 2), 2) AnT (Ngưỡng kỵ khí / lactate threshold - giới hạn trên của Zone 4), 3) Nhịp tim nghỉ ngơi (Resting HR), 4) Nhịp tim tối đa (Max HR)."
    : "I am an endurance runner. Here is a screenshot of my Heart Rate Zones and resting/max HR from my watch. Please extract: 1) AeT (Aerobic Threshold - upper edge of Zone 2), 2) AnT (Anaerobic / Lactate Threshold - upper edge of Zone 4), 3) Resting HR, and 4) Max HR.";

  const handleCopyPrompt = async () => {
    try {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(aiPrompt);
        setCopied(true);
        setTimeout(() => setCopied(false), 2500);
      }
    } catch (err) {
      console.error("Clipboard copy failed:", err);
    }
  };

  const platforms = [
    {
      id: "garmin" as const,
      name: "Garmin",
      stepsEn: [
        "Open Garmin Connect app on your phone.",
        "Tap More (...) > Settings > User Settings.",
        "Select Heart Rate & Power Zones > Heart Rate > Zones.",
        "Note your Zone 2 upper limit (AeT) and Zone 4 upper limit / Lactate Threshold (AnT).",
      ],
      stepsVi: [
        "Mở ứng dụng Garmin Connect trên điện thoại.",
        "Nhấn vào Thêm (...) > Cài đặt > Cài đặt người dùng.",
        "Chọn Vùng nhịp tim & công suất > Nhịp tim > Các vùng (Zones).",
        "Ghi lại ngưỡng trên Zone 2 (AeT) và ngưỡng trên Zone 4 / Ngưỡng Lactate (AnT).",
      ],
    },
    {
      id: "coros" as const,
      name: "COROS",
      stepsEn: [
        "Open the COROS app on your phone.",
        "Go to Profile tab (bottom right) > Settings > Heart Rate Zone.",
        "Select Threshold Heart Rate Zone (or Max HR Zone).",
        "Your Aerobic Endurance upper limit is AeT; your Threshold zone limit is AnT.",
      ],
      stepsVi: [
        "Mở ứng dụng COROS trên điện thoại.",
        "Vào tab Hồ sơ (dưới cùng bên phải) > Cài đặt > Vùng nhịp tim.",
        "Chọn Vùng nhịp tim ngưỡng (Threshold Heart Rate Zone).",
        "Giới hạn trên của vùng Bền hiếu khí (Aerobic) là AeT; giới hạn vùng Ngưỡng là AnT.",
      ],
    },
    {
      id: "apple" as const,
      name: "Apple Watch",
      stepsEn: [
        "Open the Apple Watch app on your iPhone.",
        "Scroll down and tap Workout.",
        "Tap Heart Rate Zones (calculated automatically or manual).",
        "Zone 2 upper limit is AeT; Zone 4 upper limit is AnT.",
      ],
      stepsVi: [
        "Mở ứng dụng Watch trên iPhone.",
        "Cuộn xuống và chọn Bài tập (Workout).",
        "Chọn Vùng nhịp tim (Heart Rate Zones).",
        "Giới hạn trên Zone 2 là AeT; giới hạn trên Zone 4 là AnT.",
      ],
    },
    {
      id: "others" as const,
      name: "Suunto / Polar / Strava",
      stepsEn: [
        "Suunto: Suunto App > Profile > Watch Settings > Intensity Zones.",
        "Polar: Polar Flow App > Sport Profiles > Heart Rate Zones.",
        "Strava: You > Settings > Heart Rate > Max & Custom Zones.",
      ],
      stepsVi: [
        "Suunto: Ứng dụng Suunto > Hồ sơ > Cài đặt đồng hồ > Vùng cường độ.",
        "Polar: Ứng dụng Polar Flow > Hồ sơ thể thao > Vùng nhịp tim.",
        "Strava: Bạn (You) > Cài đặt > Nhịp tim > Vùng tùy chỉnh.",
      ],
    },
  ];

  const currentPlatform = platforms.find((p) => p.id === activePlatform) || platforms[0];

  return createPortal(
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0, 0, 0, 0.55)",
        backdropFilter: "blur(12px)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 2000,
        padding: "16px",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          background: "var(--bg-card, #ffffff)",
          border: "1px solid var(--border-color, rgba(0,0,0,0.1))",
          borderRadius: "20px",
          padding: "24px",
          width: "100%",
          maxWidth: "580px",
          maxHeight: "90vh",
          overflowY: "auto",
          boxShadow: "0 24px 60px rgba(0, 0, 0, 0.18)",
          position: "relative",
          color: "var(--text-primary, #111111)",
        }}
      >
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          aria-label={isVi ? "Đóng" : "Close"}
          style={{
            position: "absolute",
            top: "16px",
            right: "16px",
            background: "none",
            border: "none",
            fontSize: "20px",
            cursor: "pointer",
            color: "var(--text-muted, #666666)",
            padding: "4px",
            borderRadius: "6px",
          }}
        >
          <X size={20} />
        </button>

        {/* Modal Header */}
        <div style={{ display: "flex", alignItems: "flex-start", gap: "12px", marginBottom: "18px" }}>
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "12px",
              background: "rgba(59, 130, 246, 0.12)",
              color: "#3b82f6",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <Watch size={22} weight="duotone" />
          </div>
          <div>
            <h2 style={{ fontSize: "18px", fontWeight: 800, margin: 0, letterSpacing: "-0.01em" }}>
              {isVi ? "Cách tìm Zone nhịp tim & Ngưỡng thể chất" : "How to Find Your Heart Rate Zones & Thresholds"}
            </h2>
            <p style={{ fontSize: "12.5px", color: "var(--text-muted, #666666)", margin: "4px 0 0 0" }}>
              {isVi
                ? "Hướng dẫn lấy từ đồng hồ hoặc dùng AI trích xuất nhanh từ ảnh chụp màn hình."
                : "Guide to retrieve your zones from your watch or extract them automatically with AI."}
            </p>
          </div>
        </div>

        {/* Threshold Concepts Summary */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "10px",
            marginBottom: "18px",
          }}
        >
          <div
            style={{
              background: "rgba(59, 130, 246, 0.06)",
              border: "1px solid rgba(59, 130, 246, 0.2)",
              borderRadius: "12px",
              padding: "12px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#2563eb", fontWeight: 700, fontSize: "12px", marginBottom: "4px" }}>
              <Heartbeat size={15} weight="bold" />
              <span>{isVi ? "Ngưỡng hiếu khí (AeT)" : "Aerobic Threshold (AeT)"}</span>
            </div>
            <p style={{ fontSize: "11.5px", color: "var(--text-secondary, #444)", margin: 0, lineHeight: 1.45 }}>
              {isVi
                ? "Giới hạn trên của Zone 2 (Easy). Nỗ lực duy trì nói chuyện trôi chảy, đốt mỡ tối ưu cho Ultra Trail."
                : "Upper limit of Zone 2 (Easy). Conversational effort, key aerobic base for ultra trail endurance."}
            </p>
          </div>

          <div
            style={{
              background: "rgba(239, 68, 68, 0.06)",
              border: "1px solid rgba(239, 68, 68, 0.2)",
              borderRadius: "12px",
              padding: "12px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#dc2626", fontWeight: 700, fontSize: "12px", marginBottom: "4px" }}>
              <Heartbeat size={15} weight="bold" />
              <span>{isVi ? "Ngưỡng kỵ khí (AnT)" : "Anaerobic Threshold (AnT)"}</span>
            </div>
            <p style={{ fontSize: "11.5px", color: "var(--text-secondary, #444)", margin: 0, lineHeight: 1.45 }}>
              {isVi
                ? "Giới hạn trên của Zone 4 / Ngưỡng Lactate (LTHR). Nỗ lực tối đa có thể duy trì trong ~1 giờ."
                : "Upper limit of Zone 4 / Lactate Threshold (LTHR). Maximum effort sustainable for ~1 hour."}
            </p>
          </div>
        </div>

        {/* AI Screenshot Extraction Box */}
        <div
          style={{
            background: "linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(217, 119, 6, 0.04) 100%)",
            border: "1.5px solid rgba(245, 158, 11, 0.35)",
            borderRadius: "14px",
            padding: "14px",
            marginBottom: "20px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#d97706", fontWeight: 800, fontSize: "12.5px" }}>
              <Sparkle size={16} weight="fill" />
              <span>{isVi ? "Mẹo AI: Trích xuất tự động bằng Gemini / ChatGPT" : "AI Tip: Extract automatically with Gemini / ChatGPT"}</span>
            </div>
            <button
              type="button"
              onClick={handleCopyPrompt}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                fontSize: "11.5px",
                fontWeight: 700,
                color: copied ? "#059669" : "#d97706",
                background: copied ? "rgba(16, 185, 129, 0.12)" : "rgba(245, 158, 11, 0.15)",
                border: "1px solid",
                borderColor: copied ? "#10b981" : "rgba(245, 158, 11, 0.4)",
                borderRadius: "8px",
                padding: "4px 10px",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              {copied ? <Check size={13} weight="bold" /> : <Copy size={13} weight="bold" />}
              <span>{copied ? (isVi ? "Đã chép!" : "Copied!") : (isVi ? "Sao chép câu lệnh" : "Copy Prompt")}</span>
            </button>
          </div>
          <p style={{ fontSize: "12px", color: "var(--text-secondary, #444)", margin: "0 0 8px 0", lineHeight: 1.45 }}>
            {isVi
              ? "Chỉ cần chụp ảnh màn hình màn hình Vùng nhịp tim trên app đồng hồ của bạn, sau đó gửi ảnh vào ChatGPT hoặc Gemini cùng câu lệnh bên dưới:"
              : "Simply take a screenshot of your Heart Rate Zones in your watch app, then upload the image to ChatGPT or Gemini with this prompt:"}
          </p>
          <div
            style={{
              background: "rgba(0, 0, 0, 0.04)",
              border: "1px solid rgba(0, 0, 0, 0.08)",
              borderRadius: "8px",
              padding: "10px 12px",
              fontSize: "12px",
              fontFamily: "monospace",
              color: "var(--text-primary, #222)",
              lineHeight: 1.5,
              wordBreak: "break-word",
            }}
          >
            &ldquo;{aiPrompt}&rdquo;
          </div>
        </div>

        {/* Watch Navigation Instructions */}
        <div>
          <div style={{ fontSize: "13px", fontWeight: 700, marginBottom: "8px" }}>
            {isVi ? "Xem vị trí cài đặt trên ứng dụng đồng hồ:" : "Find it manually in your watch app:"}
          </div>

          {/* Platform Tab Buttons */}
          <div style={{ display: "flex", gap: "6px", marginBottom: "12px", flexWrap: "wrap" }}>
            {platforms.map((p) => {
              const active = p.id === activePlatform;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setActivePlatform(p.id)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "20px",
                    fontSize: "12px",
                    fontWeight: active ? 700 : 500,
                    cursor: "pointer",
                    border: "1px solid",
                    borderColor: active ? "var(--accent-primary, #10b981)" : "var(--border-color, rgba(0,0,0,0.1))",
                    background: active ? "rgba(16, 185, 129, 0.12)" : "transparent",
                    color: active ? "var(--accent-primary, #059669)" : "var(--text-secondary, #555)",
                  }}
                >
                  {p.name}
                </button>
              );
            })}
          </div>

          {/* Platform Steps */}
          <div
            style={{
              background: "rgba(0, 0, 0, 0.03)",
              border: "1px solid var(--border-color, rgba(0,0,0,0.08))",
              borderRadius: "12px",
              padding: "14px 16px",
            }}
          >
            <ol style={{ margin: 0, paddingLeft: "18px", fontSize: "12.5px", lineHeight: 1.6, color: "var(--text-secondary, #333)" }}>
              {(isVi ? currentPlatform.stepsVi : currentPlatform.stepsEn).map((step, idx) => (
                <li key={idx} style={{ marginBottom: idx === currentPlatform.stepsEn.length - 1 ? 0 : "6px" }}>
                  {step}
                </li>
              ))}
            </ol>
          </div>
        </div>

        {/* Modal Footer */}
        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "20px" }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={onClose}
            style={{ height: "38px", padding: "0 24px", fontSize: "13px", fontWeight: 700 }}
          >
            {isVi ? "Đã hiểu" : "Got it"}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
