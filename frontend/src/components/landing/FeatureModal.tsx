import React from "react";
import { XCircle } from "@phosphor-icons/react";
import { FeatureContent } from "../../data/landingFeatures";
import { renderWithTerms } from "./renderWithTerms";

export function FeatureModal({
  feature,
  lang,
  onClose,
}: {
  feature: FeatureContent;
  lang: "en" | "vi";
  onClose: () => void;
}) {
  const copy = feature[lang];

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(255,255,255,0.35)",
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 1000,
        padding: "20px",
      }}
    >
      <div
        style={{
          background: "var(--bg-card)",
          backdropFilter: "blur(30px)",
          WebkitBackdropFilter: "blur(30px)",
          border: "1px solid var(--border-color)",
          borderRadius: "24px",
          padding: "32px",
          width: "100%",
          maxWidth: "560px",
          maxHeight: "90vh",
          overflowY: "auto",
          boxShadow: "0 20px 60px rgba(0,0,0,0.1)",
          position: "relative",
          color: "var(--text-primary)",
          textAlign: "left",
        }}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          style={{
            position: "absolute",
            top: "20px",
            right: "20px",
            background: "transparent",
            border: "none",
            cursor: "pointer",
            color: "var(--text-muted)",
            padding: "4px",
            display: "flex",
            borderRadius: "50%",
          }}
        >
          <XCircle size={24} weight="duotone" />
        </button>

        <h3
          style={{
            fontFamily: "var(--font-schibsted), sans-serif",
            fontSize: "22px",
            fontWeight: 700,
            marginBottom: "4px",
            paddingRight: "32px",
          }}
        >
          {copy.tagline}
        </h3>

        <p style={{ fontSize: "14px", lineHeight: 1.6, color: "var(--text-secondary)", marginBottom: "20px" }}>
          {renderWithTerms(copy.overview, lang)}
        </p>

        <h4
          style={{
            fontSize: "12px",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            color: "var(--text-muted)",
            marginBottom: "10px",
          }}
        >
          {lang === "en" ? "How it works" : "Cách hoạt động"}
        </h4>
        <ul style={{ listStyle: "none", padding: 0, margin: "0 0 20px 0", display: "flex", flexDirection: "column", gap: "8px" }}>
          {copy.howItWorks.map((line, i) => (
            <li key={i} style={{ fontSize: "13.5px", lineHeight: 1.6, color: "var(--text-primary)", paddingLeft: "16px", position: "relative" }}>
              <span style={{ position: "absolute", left: 0, color: "var(--accent-primary)" }}>&bull;</span>
              {renderWithTerms(line, lang)}
            </li>
          ))}
        </ul>

        <div
          style={{
            background: "rgba(255,255,255,0.4)",
            border: "1px solid var(--border-color)",
            borderRadius: "14px",
            padding: "14px 16px",
            marginBottom: "14px",
          }}
        >
          <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginBottom: "8px" }}>{copy.personalizedNote}</p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
            {copy.personalizedChips.map((chip) => (
              <span
                key={chip}
                style={{
                  fontSize: "11.5px",
                  fontWeight: 600,
                  padding: "4px 10px",
                  borderRadius: "9999px",
                  background: "rgba(25,206,139,0.1)",
                  color: "var(--accent-primary)",
                  border: "1px solid rgba(25,206,139,0.2)",
                }}
              >
                {chip}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
