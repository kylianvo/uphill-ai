import React from "react";
import { ShieldCheck } from "@phosphor-icons/react";

export function TrustBanner({ lang }: { lang: "en" | "vi" }) {
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "10px",
        padding: "10px 20px",
        borderRadius: "9999px",
        background: "rgba(255, 255, 255, 0.5)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        border: "1px solid rgba(255, 255, 255, 0.6)",
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.06)",
      }}
    >
      <ShieldCheck size={18} weight="duotone" color="var(--accent-primary)" />
      <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)" }}>
        {lang === "en"
          ? "No hallucinated advice — every answer traces back to a real, curated source."
          : "Không có lời khuyên bịa đặt — mọi câu trả lời đều truy được về nguồn thật, đã tuyển chọn."}
      </span>
    </div>
  );
}
