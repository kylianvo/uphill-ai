/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect, useRef } from "react";
import { useAppContext } from "../contexts/AppContext";
import { translations } from "../app/translations";
import { WarningCircle, Trophy, Barbell, Clock, Lightning, Sneaker, Target, Calendar, House, Plant, Code, Plus, Trash } from "@phosphor-icons/react";
import { FeatureGrid } from "../components/landing/FeatureGrid";

export default function HomeTab({ isMobile }: { isMobile: boolean }) {
  const ctx = useAppContext();
  const { lang, user, activePlan, setAuthModalOpen, activeTab, handleTabSwitch } = ctx as any;
  const t = (key: keyof typeof translations.en) => translations[lang as keyof typeof translations]?.[key] || translations.en[key] || key;

  const [startBtnHovered, setStartBtnHovered] = useState(false);

  const renderBody = () => {

    return (

      <>

      <div style={{

        maxWidth: '720px',

        margin: '0 auto',

        display: 'flex',

        flexDirection: 'column',

        alignItems: 'center',

        textAlign: 'center',

        gap: '24px',

        padding: isMobile ? '24px 16px' : '40px 32px',

        width: '100%',

        boxSizing: 'border-box'

      }}>

        {/* Header group */}

        <div className="hero-header-group" style={{ marginBottom: 0, background: "rgba(255, 255, 255, 0.4)", backdropFilter: "blur(16px)", WebkitBackdropFilter: "blur(16px)", padding: "24px 32px", borderRadius: "24px", border: "1px solid rgba(255, 255, 255, 0.5)" }}>

          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "10px", marginBottom: "16px", color: "var(--text-primary)" }}>

            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">

              <path d="M3 15l5-5 4 4 9-9" />

              <polyline points="16 5 21 5 21 10" />

            </svg>

            <span style={{ fontSize: "40px", fontWeight: "700", letterSpacing: "-1.5px", fontFamily: "var(--font-schibsted)" }}>

              Uphill<span style={{ color: "var(--accent-primary)" }}>.AI</span>

            </span>

          </div>

          <h1 className="hero-headline">

            {lang === "en" ? "Train Smarter, Go Higher" : "Tập Luyện Thông Minh, Chinh Phục Đỉnh Cao."}

          </h1>

          <p className="hero-subtitle" style={{ maxWidth: "600px", margin: "0 auto" }}>

            {lang === "en"

              ? "Science-backed trail coaching powered by AI."

              : "Nền tảng huấn luyện chạy trail chuẩn khoa học đột phá bởi AI."}

          </p>

        </div>



        {/* Big Start training plan button */}

        <div style={{ marginTop: "12px" }}>

          <button

            className="btn btn-secondary"

            onMouseEnter={() => setStartBtnHovered(true)}

            onMouseLeave={() => setStartBtnHovered(false)}

            style={{

              padding: isMobile ? '14px 32px' : '18px 48px',

              fontSize: isMobile ? '15px' : '18px',

              height: 'auto',

              borderRadius: '9999px',

              fontWeight: '700',

              display: 'inline-flex',

              alignItems: 'center',

              justifyContent: 'center',

              gap: '12px',

              cursor: 'pointer',

              boxShadow: startBtnHovered ? '0 12px 40px rgba(0, 0, 0, 0.12)' : '0 8px 32px rgba(0, 0, 0, 0.05)',

              background: startBtnHovered ? 'rgba(255, 255, 255, 0.85)' : 'rgba(255, 255, 255, 0.65)',

              backdropFilter: 'blur(20px)',

              WebkitBackdropFilter: 'blur(20px)',

              border: startBtnHovered ? '1px solid rgba(255, 255, 255, 0.95)' : '1px solid rgba(255, 255, 255, 0.8)',

              color: '#000000',

              transform: startBtnHovered ? 'translateY(-2px) scale(1.02)' : 'none',

              transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',

            }}

            onClick={() => handleTabSwitch('planner')}

          >

            {t("home_cta_plan")}

          </button>

        </div>

      </div>

      <FeatureGrid lang={lang as "en" | "vi"} isMobile={isMobile} />

      </>

    );

  };

  return renderBody();
}
