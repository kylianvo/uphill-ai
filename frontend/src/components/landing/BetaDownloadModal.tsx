"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  X,
  AppleLogo,
  AndroidLogo,
  DownloadSimple,
  ArrowRight,
  CheckCircle,
  WarningCircle,
  CircleNotch,
  Sparkle,
} from "@phosphor-icons/react";
import { translations } from "@/app/translations";
import { getApiBaseUrl } from "@/lib/apiUrlOverride";

interface BetaDownloadModalProps {
  isOpen: boolean;
  onClose: () => void;
  lang: "en" | "vi";
}

const IOS_TESTFLIGHT_URL = "https://testflight.apple.com/join/T9WarWaS";
const ANDROID_APK_URL = "https://drive.google.com/file/d/17lt8-S1eeyAbUbyR-QSlkr_kBilNnTKB/view?usp=sharing";

export function BetaDownloadModal({ isOpen, onClose, lang }: BetaDownloadModalProps) {
  const [step, setStep] = useState<1 | 2>(1);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [referralSource, setReferralSource] = useState("");
  const [usageIntent, setUsageIntent] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const modalRef = useRef<HTMLDivElement>(null);

  const t = (key: keyof typeof translations.en) =>
    translations[lang]?.[key] || translations.en[key] || key;

  // Handle ESC key to close
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Prevent background body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");

    const trimmedName = name.trim();
    const trimmedEmail = email.trim();

    if (!trimmedName || !trimmedEmail || !referralSource || !usageIntent) {
      setErrorMessage(t("beta_error_required"));
      return;
    }

    if (!trimmedEmail.includes("@") || !trimmedEmail.includes(".")) {
      setErrorMessage(t("beta_error_email"));
      return;
    }

    setIsSubmitting(true);

    try {
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/api/marketing/beta-signup`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: trimmedName,
          email: trimmedEmail,
          referral_source: referralSource,
          usage_intent: usageIntent,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || t("beta_error_submit"));
      }

      // Transition to Step 2: Download Links
      setStep(2);
    } catch (err: unknown) {
      // If endpoint fails (e.g. offline dev or network drop), log and advance so the user is never blocked from downloading
      console.warn("Beta registration network fallback:", err);
      setStep(2);
    } finally {
      setIsSubmitting(false);
    }
  };

  const referralOptions = [
    { value: "From Kilomet", label: t("beta_referral_kilomet") },
    { value: "Friends / Referral", label: t("beta_referral_friends") },
    { value: "Facebook / Social Media", label: t("beta_referral_facebook") },
    { value: "Strava / Running Club", label: t("beta_referral_strava") },
    { value: "Search / Google", label: t("beta_referral_search") },
    { value: "Other", label: t("beta_referral_other") },
  ];

  const intentOptions = [
    { value: "Browsing and exploring features", label: t("beta_intent_browsing") },
    { value: "Training for a goal race", label: t("beta_intent_race") },
    { value: "Daily trail and road running", label: t("beta_intent_daily") },
    { value: "Coaching other athletes", label: t("beta_intent_coach") },
    { value: "Other", label: t("beta_intent_other") },
  ];

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "16px",
        background: "rgba(15, 23, 42, 0.65)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        animation: "fadeIn 0.2s ease-out",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={modalRef}
        style={{
          position: "relative",
          width: "100%",
          maxWidth: "520px",
          background: "rgba(255, 255, 255, 0.96)",
          border: "1px solid rgba(255, 255, 255, 0.8)",
          borderRadius: "24px",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(0, 0, 0, 0.05)",
          padding: "32px",
          color: "#0f172a",
          maxHeight: "90vh",
          overflowY: "auto",
        }}
      >
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          aria-label={t("beta_close_btn")}
          style={{
            position: "absolute",
            top: "20px",
            right: "20px",
            background: "rgba(241, 245, 249, 0.8)",
            border: "1px solid rgba(226, 232, 240, 0.8)",
            borderRadius: "50%",
            width: "36px",
            height: "36px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#64748b",
            cursor: "pointer",
            transition: "all 0.15s ease",
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.color = "#0f172a";
            e.currentTarget.style.background = "#e2e8f0";
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.color = "#64748b";
            e.currentTarget.style.background = "rgba(241, 245, 249, 0.8)";
          }}
        >
          <X size={18} weight="bold" />
        </button>

        {step === 1 ? (
          <div>
            {/* Step 1: Header */}
            <div style={{ marginBottom: "24px", paddingRight: "36px" }}>
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "4px 12px",
                  borderRadius: "9999px",
                  background: "rgba(16, 185, 129, 0.1)",
                  border: "1px solid rgba(16, 185, 129, 0.25)",
                  color: "#059669",
                  fontSize: "12px",
                  fontWeight: 600,
                  marginBottom: "12px",
                }}
              >
                <Sparkle size={14} weight="fill" />
                <span>Early Access</span>
              </div>
              <h3
                style={{
                  fontFamily: "var(--font-schibsted), sans-serif",
                  fontSize: "24px",
                  fontWeight: 800,
                  letterSpacing: "-0.5px",
                  margin: "0 0 6px 0",
                  color: "#0f172a",
                }}
              >
                {t("beta_modal_title")}
              </h3>
              <p
                style={{
                  fontSize: "14px",
                  color: "#64748b",
                  lineHeight: 1.5,
                  margin: 0,
                }}
              >
                {t("beta_modal_subtitle")}
              </p>
            </div>

            {/* Error Message */}
            {errorMessage && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "10px 14px",
                  borderRadius: "10px",
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  color: "#b91c1c",
                  fontSize: "13px",
                  marginBottom: "18px",
                }}
              >
                <WarningCircle size={18} weight="fill" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
              {/* Field: Name */}
              <div>
                <label
                  htmlFor="beta-name"
                  style={{
                    display: "block",
                    fontSize: "13px",
                    fontWeight: 600,
                    color: "#334155",
                    marginBottom: "6px",
                  }}
                >
                  {t("beta_field_name")} <span style={{ color: "#ef4444" }}>*</span>
                </label>
                <input
                  id="beta-name"
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder={t("beta_field_name_placeholder")}
                  style={{
                    width: "100%",
                    height: "44px",
                    padding: "0 14px",
                    borderRadius: "10px",
                    border: "1px solid #cbd5e1",
                    background: "#ffffff",
                    color: "#0f172a",
                    fontSize: "14px",
                    outline: "none",
                    transition: "border-color 0.15s ease, box-shadow 0.15s ease",
                    boxSizing: "border-box",
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = "#10b981";
                    e.currentTarget.style.boxShadow = "0 0 0 3px rgba(16, 185, 129, 0.15)";
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = "#cbd5e1";
                    e.currentTarget.style.boxShadow = "none";
                  }}
                />
              </div>

              {/* Field: Email */}
              <div>
                <label
                  htmlFor="beta-email"
                  style={{
                    display: "block",
                    fontSize: "13px",
                    fontWeight: 600,
                    color: "#334155",
                    marginBottom: "6px",
                  }}
                >
                  {t("beta_field_email")} <span style={{ color: "#ef4444" }}>*</span>
                </label>
                <input
                  id="beta-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t("beta_field_email_placeholder")}
                  style={{
                    width: "100%",
                    height: "44px",
                    padding: "0 14px",
                    borderRadius: "10px",
                    border: "1px solid #cbd5e1",
                    background: "#ffffff",
                    color: "#0f172a",
                    fontSize: "14px",
                    outline: "none",
                    transition: "border-color 0.15s ease, box-shadow 0.15s ease",
                    boxSizing: "border-box",
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = "#10b981";
                    e.currentTarget.style.boxShadow = "0 0 0 3px rgba(16, 185, 129, 0.15)";
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = "#cbd5e1";
                    e.currentTarget.style.boxShadow = "none";
                  }}
                />
              </div>

              {/* Field: Referral Source */}
              <div>
                <label
                  htmlFor="beta-referral"
                  style={{
                    display: "block",
                    fontSize: "13px",
                    fontWeight: 600,
                    color: "#334155",
                    marginBottom: "6px",
                  }}
                >
                  {t("beta_field_referral")} <span style={{ color: "#ef4444" }}>*</span>
                </label>
                <select
                  id="beta-referral"
                  required
                  value={referralSource}
                  onChange={(e) => setReferralSource(e.target.value)}
                  style={{
                    width: "100%",
                    height: "44px",
                    padding: "0 14px",
                    borderRadius: "10px",
                    border: "1px solid #cbd5e1",
                    background: "#ffffff",
                    color: referralSource ? "#0f172a" : "#94a3b8",
                    fontSize: "14px",
                    outline: "none",
                    cursor: "pointer",
                    transition: "border-color 0.15s ease, box-shadow 0.15s ease",
                    boxSizing: "border-box",
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = "#10b981";
                    e.currentTarget.style.boxShadow = "0 0 0 3px rgba(16, 185, 129, 0.15)";
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = "#cbd5e1";
                    e.currentTarget.style.boxShadow = "none";
                  }}
                >
                  <option value="" disabled>
                    {t("beta_field_referral_placeholder")}
                  </option>
                  {referralOptions.map((opt) => (
                    <option key={opt.value} value={opt.value} style={{ color: "#0f172a" }}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Field: Usage Intent */}
              <div>
                <label
                  htmlFor="beta-intent"
                  style={{
                    display: "block",
                    fontSize: "13px",
                    fontWeight: 600,
                    color: "#334155",
                    marginBottom: "6px",
                  }}
                >
                  {t("beta_field_intent")} <span style={{ color: "#ef4444" }}>*</span>
                </label>
                <select
                  id="beta-intent"
                  required
                  value={usageIntent}
                  onChange={(e) => setUsageIntent(e.target.value)}
                  style={{
                    width: "100%",
                    height: "44px",
                    padding: "0 14px",
                    borderRadius: "10px",
                    border: "1px solid #cbd5e1",
                    background: "#ffffff",
                    color: usageIntent ? "#0f172a" : "#94a3b8",
                    fontSize: "14px",
                    outline: "none",
                    cursor: "pointer",
                    transition: "border-color 0.15s ease, box-shadow 0.15s ease",
                    boxSizing: "border-box",
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = "#10b981";
                    e.currentTarget.style.boxShadow = "0 0 0 3px rgba(16, 185, 129, 0.15)";
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = "#cbd5e1";
                    e.currentTarget.style.boxShadow = "none";
                  }}
                >
                  <option value="" disabled>
                    {t("beta_field_intent_placeholder")}
                  </option>
                  {intentOptions.map((opt) => (
                    <option key={opt.value} value={opt.value} style={{ color: "#0f172a" }}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Submit Action */}
              <button
                type="submit"
                disabled={isSubmitting}
                style={{
                  marginTop: "6px",
                  height: "48px",
                  width: "100%",
                  borderRadius: "12px",
                  border: "none",
                  background: "#0f172a",
                  color: "#ffffff",
                  fontSize: "15px",
                  fontWeight: 700,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                  cursor: isSubmitting ? "not-allowed" : "pointer",
                  boxShadow: "0 4px 12px rgba(15, 23, 42, 0.18)",
                  transition: "all 0.15s ease",
                }}
                onMouseOver={(e) => {
                  if (!isSubmitting) e.currentTarget.style.background = "#1e293b";
                }}
                onMouseOut={(e) => {
                  if (!isSubmitting) e.currentTarget.style.background = "#0f172a";
                }}
              >
                {isSubmitting ? (
                  <>
                    <CircleNotch size={18} className="animate-spin" />
                    <span>{t("beta_submitting_btn")}</span>
                  </>
                ) : (
                  <>
                    <span>{t("beta_submit_btn")}</span>
                    <ArrowRight size={16} weight="bold" />
                  </>
                )}
              </button>
            </form>
          </div>
        ) : (
          <div>
            {/* Step 2: Download Links Hub */}
            <div style={{ textAlign: "center", marginBottom: "28px" }}>
              <div
                style={{
                  width: "56px",
                  height: "56px",
                  borderRadius: "50%",
                  background: "rgba(16, 185, 129, 0.12)",
                  color: "#10b981",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  margin: "0 auto 16px",
                }}
              >
                <CheckCircle size={32} weight="fill" />
              </div>
              <h3
                style={{
                  fontFamily: "var(--font-schibsted), sans-serif",
                  fontSize: "24px",
                  fontWeight: 800,
                  letterSpacing: "-0.5px",
                  margin: "0 0 8px 0",
                  color: "#0f172a",
                }}
              >
                {t("beta_step2_title")}
              </h3>
              <p
                style={{
                  fontSize: "14px",
                  color: "#64748b",
                  lineHeight: 1.5,
                  margin: 0,
                }}
              >
                {t("beta_step2_subtitle")}
              </p>
            </div>

            {/* Platform Download Cards */}
            <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginBottom: "24px" }}>
              {/* Apple TestFlight Card */}
              <div
                style={{
                  background: "#ffffff",
                  border: "1px solid #e2e8f0",
                  borderRadius: "16px",
                  padding: "18px",
                  boxShadow: "0 4px 12px rgba(0, 0, 0, 0.03)",
                  transition: "border-color 0.15s ease",
                }}
              >
                <div style={{ display: "flex", alignItems: "flex-start", gap: "14px", marginBottom: "14px" }}>
                  <div
                    style={{
                      width: "44px",
                      height: "44px",
                      borderRadius: "12px",
                      background: "#0f172a",
                      color: "#ffffff",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    <AppleLogo size={24} weight="fill" />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "3px" }}>
                      <span style={{ fontWeight: 700, fontSize: "16px", color: "#0f172a" }}>
                        {t("beta_ios_title")}
                      </span>
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 600,
                          padding: "2px 8px",
                          borderRadius: "9999px",
                          background: "#f1f5f9",
                          color: "#475569",
                        }}
                      >
                        {t("beta_ios_badge")}
                      </span>
                    </div>
                    <p style={{ fontSize: "13px", color: "#64748b", margin: 0, lineHeight: 1.4 }}>
                      {t("beta_ios_desc")}
                    </p>
                  </div>
                </div>

                <a
                  href={IOS_TESTFLIGHT_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "8px",
                    width: "100%",
                    height: "42px",
                    borderRadius: "10px",
                    background: "#0f172a",
                    color: "#ffffff",
                    fontSize: "14px",
                    fontWeight: 600,
                    textDecoration: "none",
                    transition: "background 0.15s ease",
                    boxSizing: "border-box",
                  }}
                  onMouseOver={(e) => (e.currentTarget.style.background = "#1e293b")}
                  onMouseOut={(e) => (e.currentTarget.style.background = "#0f172a")}
                >
                  <span>{t("beta_ios_action")}</span>
                  <ArrowRight size={15} weight="bold" />
                </a>
                <p style={{ fontSize: "11.5px", color: "#94a3b8", margin: "8px 0 0 0", textAlign: "center" }}>
                  {t("beta_ios_hint")}
                </p>
              </div>

              {/* Android APK Card */}
              <div
                style={{
                  background: "#ffffff",
                  border: "1px solid #e2e8f0",
                  borderRadius: "16px",
                  padding: "18px",
                  boxShadow: "0 4px 12px rgba(0, 0, 0, 0.03)",
                  transition: "border-color 0.15s ease",
                }}
              >
                <div style={{ display: "flex", alignItems: "flex-start", gap: "14px", marginBottom: "14px" }}>
                  <div
                    style={{
                      width: "44px",
                      height: "44px",
                      borderRadius: "12px",
                      background: "#059669",
                      color: "#ffffff",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    <AndroidLogo size={24} weight="fill" />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "3px" }}>
                      <span style={{ fontWeight: 700, fontSize: "16px", color: "#0f172a" }}>
                        {t("beta_android_title")}
                      </span>
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 600,
                          padding: "2px 8px",
                          borderRadius: "9999px",
                          background: "#ecfdf5",
                          color: "#059669",
                        }}
                      >
                        {t("beta_android_badge")}
                      </span>
                    </div>
                    <p style={{ fontSize: "13px", color: "#64748b", margin: 0, lineHeight: 1.4 }}>
                      {t("beta_android_desc")}
                    </p>
                  </div>
                </div>

                <a
                  href={ANDROID_APK_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "8px",
                    width: "100%",
                    height: "42px",
                    borderRadius: "10px",
                    background: "#059669",
                    color: "#ffffff",
                    fontSize: "14px",
                    fontWeight: 600,
                    textDecoration: "none",
                    transition: "background 0.15s ease",
                    boxSizing: "border-box",
                  }}
                  onMouseOver={(e) => (e.currentTarget.style.background = "#047857")}
                  onMouseOut={(e) => (e.currentTarget.style.background = "#059669")}
                >
                  <DownloadSimple size={17} weight="bold" />
                  <span>{t("beta_android_action")}</span>
                </a>
                <p style={{ fontSize: "11.5px", color: "#94a3b8", margin: "8px 0 0 0", textAlign: "center" }}>
                  {t("beta_android_hint")}
                </p>
              </div>
            </div>

            {/* Back or Close Action */}
            <div style={{ display: "flex", justifyContent: "center" }}>
              <button
                type="button"
                onClick={onClose}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#64748b",
                  fontSize: "13px",
                  fontWeight: 600,
                  cursor: "pointer",
                  padding: "6px 12px",
                }}
                onMouseOver={(e) => (e.currentTarget.style.color = "#0f172a")}
                onMouseOut={(e) => (e.currentTarget.style.color = "#64748b")}
              >
                {t("beta_close_btn")}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
