import React, { useState } from "react";
import { Calendar, Robot, Crosshair, Gauge, Sneaker, BowlFood } from "@phosphor-icons/react";
import { LANDING_FEATURES } from "../../data/landingFeatures";
import { FeatureModal } from "./FeatureModal";

const FEATURE_ICONS = { Calendar, Robot, Crosshair, Gauge, Sneaker, BowlFood };

export function FeatureGrid({ lang, isMobile }: { lang: "en" | "vi"; isMobile: boolean }) {
  const [openId, setOpenId] = useState<string | null>(null);
  const openFeature = LANDING_FEATURES.find((f) => f.id === openId) || null;

  return (
    <div style={{ width: "100%", maxWidth: "1040px", padding: isMobile ? "0 16px" : "0 32px", boxSizing: "border-box" }}>
      <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "repeat(3, 1fr)", gap: "20px" }}>
        {LANDING_FEATURES.map((feature) => {
          const Icon = FEATURE_ICONS[feature.icon];
          const copy = feature[lang];
          return (
            <button
              key={feature.id}
              type="button"
              className="card"
              onClick={() => setOpenId(feature.id)}
              style={{ textAlign: "left", cursor: "pointer", font: "inherit" }}
            >
              <div className="card-icon">
                <Icon size={22} weight="duotone" />
              </div>
              <div className="card-title">{copy.tagline}</div>
              <div className="card-description">{copy.cardBlurb}</div>
              <span style={{ marginTop: "14px", fontSize: "13px", fontWeight: 700, color: "var(--accent-primary)" }}>
                {lang === "en" ? "Learn more →" : "Xem thêm →"}
              </span>
            </button>
          );
        })}
      </div>
      {openFeature && <FeatureModal feature={openFeature} lang={lang} onClose={() => setOpenId(null)} />}
    </div>
  );
}
