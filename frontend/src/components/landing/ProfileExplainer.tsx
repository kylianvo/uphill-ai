import React from "react";
import { UserCircle } from "@phosphor-icons/react";

const PROFILE_INPUTS: Record<"en" | "vi", string[]> = {
  en: [
    "AeT / AnT thresholds",
    "Injury history",
    "Active training plan",
    "Body weight",
    "Live race-day weather",
    "Goal race terrain & elevation",
  ],
  vi: [
    "Ngưỡng AeT / AnT",
    "Tiền sử chấn thương",
    "Giáo án đang hoạt động",
    "Cân nặng",
    "Thời tiết thật ngày thi đấu",
    "Địa hình & độ cao giải mục tiêu",
  ],
};

export function ProfileExplainer({ lang }: { lang: "en" | "vi" }) {
  const items = PROFILE_INPUTS[lang];
  return (
    <div className="card" style={{ width: "100%", maxWidth: "680px", textAlign: "left" }}>
      <div className="card-icon">
        <UserCircle size={22} weight="duotone" />
      </div>
      <div className="card-title">{lang === "en" ? "Your Profile" : "Hồ sơ của bạn"}</div>
      <div className="card-description" style={{ marginBottom: "14px" }}>
        {lang === "en"
          ? "The same inputs power every feature below, so you only tell us once."
          : "Cùng một bộ dữ liệu này cung cấp cho mọi tính năng bên dưới — bạn chỉ cần nhập một lần."}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
        {items.map((item) => (
          <span
            key={item}
            style={{
              fontSize: "12px",
              fontWeight: 600,
              padding: "6px 12px",
              borderRadius: "9999px",
              background: "rgba(0, 0, 0, 0.04)",
              color: "var(--text-secondary)",
              border: "1px solid var(--border-color)",
            }}
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
