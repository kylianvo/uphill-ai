"use client";

import React from "react";
import { translations } from "../app/translations";
import { triggerHaptic } from "../utils/native";
import { Sparkle } from "@phosphor-icons/react";

export type FeelingId = "very_light" | "light" | "moderate" | "hard" | "max_effort";

export interface FeelingDefinition {
  id: FeelingId;
  labelKey: keyof typeof translations.en;
  subKey: keyof typeof translations.en;
  descKey: keyof typeof translations.en;
  rpe: number;
  color: string;
  badgeBg: string;
  badgeBorder: string;
  badgeText: string;
  activeBg: string;
  activeBorder: string;
}

export const UNIFIED_FEELINGS: FeelingDefinition[] = [
  {
    id: "very_light",
    labelKey: "feeling_very_light",
    subKey: "feeling_very_light_sub",
    descKey: "feeling_very_light_desc",
    rpe: 2,
    color: "#06b6d4",
    badgeBg: "rgba(6, 182, 212, 0.12)",
    badgeBorder: "rgba(6, 182, 212, 0.3)",
    badgeText: "#0891b2",
    activeBg: "rgba(6, 182, 212, 0.14)",
    activeBorder: "#06b6d4",
  },
  {
    id: "light",
    labelKey: "feeling_light",
    subKey: "feeling_light_sub",
    descKey: "feeling_light_desc",
    rpe: 4,
    color: "#10b981",
    badgeBg: "rgba(16, 185, 129, 0.12)",
    badgeBorder: "rgba(16, 185, 129, 0.3)",
    badgeText: "#059669",
    activeBg: "rgba(16, 185, 129, 0.14)",
    activeBorder: "#10b981",
  },
  {
    id: "moderate",
    labelKey: "feeling_moderate",
    subKey: "feeling_moderate_sub",
    descKey: "feeling_moderate_desc",
    rpe: 6,
    color: "#3b82f6",
    badgeBg: "rgba(59, 130, 246, 0.12)",
    badgeBorder: "rgba(59, 130, 246, 0.3)",
    badgeText: "#2563eb",
    activeBg: "rgba(59, 130, 246, 0.14)",
    activeBorder: "#3b82f6",
  },
  {
    id: "hard",
    labelKey: "feeling_hard",
    subKey: "feeling_hard_sub",
    descKey: "feeling_hard_desc",
    rpe: 8,
    color: "#f59e0b",
    badgeBg: "rgba(245, 158, 11, 0.12)",
    badgeBorder: "rgba(245, 158, 11, 0.3)",
    badgeText: "#d97706",
    activeBg: "rgba(245, 158, 11, 0.14)",
    activeBorder: "#f59e0b",
  },
  {
    id: "max_effort",
    labelKey: "feeling_max_effort",
    subKey: "feeling_max_effort_sub",
    descKey: "feeling_max_effort_desc",
    rpe: 10,
    color: "#ef4444",
    badgeBg: "rgba(239, 68, 68, 0.12)",
    badgeBorder: "rgba(239, 68, 68, 0.3)",
    badgeText: "#dc2626",
    activeBg: "rgba(239, 68, 68, 0.14)",
    activeBorder: "#ef4444",
  },
];

export function rpeToFeelingId(rpe: number | null | undefined): FeelingId | null {
  if (rpe === null || rpe === undefined) return null;
  if (rpe <= 2) return "very_light";
  if (rpe <= 4) return "light";
  if (rpe <= 6) return "moderate";
  if (rpe <= 8) return "hard";
  return "max_effort";
}

export function feelingIdToRpe(id: FeelingId): number {
  const match = UNIFIED_FEELINGS.find((f) => f.id === id);
  return match ? match.rpe : 6;
}

interface FeelingSelectorProps {
  selectedId: FeelingId | null;
  onChange: (id: FeelingId, rpe: number) => void;
  lang?: "en" | "vi";
  isMobile?: boolean;
  variant?: "cards" | "pills";
  showDescription?: boolean;
}

export const FeelingSelector: React.FC<FeelingSelectorProps> = ({
  selectedId,
  onChange,
  lang = "en",
  isMobile = false,
  variant = "cards",
  showDescription = false,
}) => {
  const t = (k: keyof typeof translations.en) => {
    const dict = (translations as Record<string, Record<string, string>>)[lang] || translations.en;
    return dict[k] || translations.en[k] || String(k);
  };

  const handleSelect = (feelId: FeelingId, rpeVal: number) => {
    triggerHaptic();
    onChange(feelId, rpeVal);
  };

  if (variant === "pills") {
    return (
      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", alignItems: "center" }}>
        {UNIFIED_FEELINGS.map((feel) => {
          const isSelected = selectedId === feel.id;
          return (
            <button
              key={feel.id}
              type="button"
              onClick={() => handleSelect(feel.id, feel.rpe)}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                padding: "4px 10px",
                borderRadius: "16px",
                fontSize: "12px",
                fontWeight: isSelected ? "700" : "500",
                cursor: "pointer",
                border: `1.5px solid ${isSelected ? feel.activeBorder : "var(--border-color)"}`,
                background: isSelected ? feel.activeBg : "rgba(255, 255, 255, 0.4)",
                color: isSelected ? feel.color : "var(--text-secondary)",
                transition: "all 0.15s ease",
              }}
            >
              <span
                style={{
                  width: "7px",
                  height: "7px",
                  borderRadius: "50%",
                  background: feel.color,
                }}
              />
              <span>{t(feel.labelKey)}</span>
            </button>
          );
        })}
      </div>
    );
  }

  // Biometric Spectrum & Spotlight Card (cards variant)
  const activeOption = UNIFIED_FEELINGS.find((o) => o.id === selectedId) || UNIFIED_FEELINGS[2]; // fallback to moderate

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "10px", width: "100%" }}>
      {/* 5-Step Segmented Spectrum Bar */}
      <div
        role="radiogroup"
        aria-label={t("adapt_week_rpe_label")}
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(5, minmax(0, 1fr))",
          gap: "5px",
          width: "100%",
          padding: "4px",
          borderRadius: "12px",
          background: "rgba(0, 0, 0, 0.03)",
          border: "1px solid var(--border-color)",
          boxSizing: "border-box",
        }}
      >
        {UNIFIED_FEELINGS.map((opt) => {
          const isSelected = selectedId === opt.id;
          return (
            <button
              key={opt.id}
              type="button"
              role="radio"
              aria-checked={isSelected}
              onClick={() => handleSelect(opt.id, opt.rpe)}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                padding: "8px 2px 6px",
                borderRadius: "8px",
                border: `1.5px solid ${isSelected ? opt.activeBorder : "transparent"}`,
                background: isSelected ? opt.activeBg : "transparent",
                cursor: "pointer",
                transition: "all 0.18s cubic-bezier(0.16, 1, 0.3, 1)",
                boxShadow: isSelected ? `0 2px 8px ${opt.badgeBorder}` : "none",
                minWidth: 0,
                outline: "none",
              }}
            >
              {/* Segment Pill Color Bar */}
              <div
                style={{
                  width: isSelected ? "20px" : "12px",
                  height: "4px",
                  borderRadius: "2px",
                  background: isSelected ? opt.color : "rgba(0, 0, 0, 0.15)",
                  marginBottom: "5px",
                  transition: "all 0.18s ease",
                }}
              />
              <span
                style={{
                  fontSize: isMobile ? "9.5px" : "11px",
                  fontWeight: isSelected ? "800" : "600",
                  color: isSelected ? opt.color : "var(--text-secondary)",
                  textAlign: "center",
                  lineHeight: 1.15,
                  letterSpacing: isMobile ? "-0.03em" : "-0.01em",
                  width: "100%",
                  padding: "0 1px",
                }}
              >
                {t(opt.labelKey)}
              </span>
              <span
                style={{
                  fontSize: "9px",
                  fontWeight: "700",
                  color: opt.badgeText,
                  marginTop: "2px",
                  opacity: isSelected ? 1 : 0.65,
                }}
              >
                RPE {opt.rpe}
              </span>
            </button>
          );
        })}
      </div>

      {/* Dynamic Spotlight Card */}
      <div
        style={{
          borderRadius: "14px",
          border: `1.5px solid ${activeOption.badgeBorder}`,
          background: `linear-gradient(135deg, ${activeOption.badgeBg} 0%, rgba(255, 255, 255, 0.85) 100%)`,
          padding: "14px 16px",
          transition: "all 0.25s cubic-bezier(0.16, 1, 0.3, 1)",
          boxShadow: `0 4px 16px ${activeOption.badgeBg}`,
          boxSizing: "border-box",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
            <span
              style={{
                fontSize: "15px",
                fontWeight: "800",
                color: activeOption.color,
                letterSpacing: "-0.01em",
              }}
            >
              {t(activeOption.labelKey)} (RPE {activeOption.rpe})
            </span>
          </div>
          <span
            style={{
              fontSize: "11px",
              fontWeight: "700",
              color: activeOption.badgeText,
              background: activeOption.badgeBg,
              border: `1px solid ${activeOption.badgeBorder}`,
              borderRadius: "6px",
              padding: "2px 7px",
            }}
          >
            RPE {activeOption.rpe} / 10
          </span>
        </div>

        <div
          style={{
            fontSize: "12px",
            color: "var(--text-secondary)",
            fontWeight: "500",
            marginBottom: showDescription ? "10px" : "0",
          }}
        >
          {t(activeOption.subKey)}
        </div>

        {showDescription && (
          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "8px",
              padding: "10px 12px",
              borderRadius: "10px",
              background: "rgba(255, 255, 255, 0.88)",
              border: `1px solid ${activeOption.badgeBorder}`,
              fontSize: "11.5px",
              lineHeight: "1.45",
              color: "var(--text-primary)",
              marginTop: "8px",
            }}
          >
            <Sparkle
              size={15}
              weight="fill"
              style={{ color: activeOption.color, flexShrink: 0, marginTop: "2px" }}
            />
            <div>
              <strong style={{ color: "var(--text-primary)" }}>Coach Adjustment: </strong>
              <span>{t(activeOption.descKey)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
