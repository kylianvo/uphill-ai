"use client";
import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Trophy,
  ChartLineUp,
  Mountains,
  CheckCircle,
  ArrowRight,
  DownloadSimple,
} from "@phosphor-icons/react";
import { useAppContext } from "@/contexts/AppContext";
import { translations } from "./translations";
import { isNativePlatform } from "@/utils/native";
import { TrustBanner } from "@/components/landing/TrustBanner";
import { LANDING_FEATURES } from "@/data/landingFeatures";
import { BetaDownloadModal } from "@/components/landing/BetaDownloadModal";
import { ComparisonSection } from "@/components/landing/ComparisonSection";
import { ProductDevice, CorosWatchPhoto } from "@/components/landing/ProductDevices";
import landingStyles from "./LandingPage.module.css";

// Whether the Proof section renders real numbers/testimonials yet.
// TODO(proof-section): flip on once we have plans-generated counts,
// athletes' completed goal races, or named testimonials with outcome
// labels to show. Never fabricate these to fill the slot early.
const SHOW_PROOF_CONTENT = false;

const TOOLING_FEATURE_IDS = ["pace", "goal", "gear", "nutrition"] as const;

type Step = {
  titleKey: keyof typeof translations.en;
  descKey: keyof typeof translations.en;
  altKey: keyof typeof translations.en;
  image: Parameters<typeof ProductDevice>[0]["shot"];
  device: "laptop" | "phone" | "closeup";
  anchor: string;
};

const STEPS: Step[] = [
  {
    titleKey: "landing_step1_title",
    descKey: "landing_step1_desc",
    altKey: "landing_step1_alt",
    image: "ios-plan-builder",
    device: "phone",
    anchor: "/science#thresholds",
  },
  {
    titleKey: "landing_step2_title",
    descKey: "landing_step2_desc",
    altKey: "landing_step2_alt",
    image: "ios-plan-week2",
    device: "phone",
    anchor: "/science#thresholds",
  },
  {
    titleKey: "landing_step3_title",
    descKey: "landing_step3_desc",
    altKey: "landing_step3_alt",
    image: "ios-adapt-week",
    device: "phone",
    anchor: "/science#adaptation",
  },
  {
    titleKey: "landing_step4_title",
    descKey: "landing_step4_desc",
    altKey: "landing_step4_alt",
    image: "web-calendar-month",
    device: "laptop",
    anchor: "/science#block-evaluation",
  },
];

const TOOL_CONFIG = {
  pace: { anchor: "/science#pace-physics", shot: "ios-pace-strategy", label: "Pace Strategy", alt: "landing_preview_pace_alt" },
  goal: { anchor: "/science#goal-prediction", shot: "ios-goal-determiner", label: "Goal Determiner", alt: "landing_preview_goal_alt" },
  gear: { anchor: "/science#gear-grounding", shot: "ios-gear-vault", label: "Gear Vault", alt: "landing_preview_gear_alt" },
  nutrition: { anchor: "/science#nutrition-grounding", shot: "ios-nutrition-lab", label: "Nutrition Lab", alt: "landing_preview_nutrition_alt" },
} as const;

export default function MarketingHome() {
  const router = useRouter();
  const { lang, setLang } = useAppContext() as {
    lang: "en" | "vi";
    setLang: (l: "en" | "vi") => void;
  };
  const t = (key: keyof typeof translations.en) =>
    translations[lang]?.[key] || translations.en[key] || key;

  // The iOS/Android shells are the same static export loaded from its root
  // index.html (see MOBILE.md) — someone who already installed the app
  // should never see a marketing pitch, so skip straight to /app there.
  const [showMarketing, setShowMarketing] = useState(false);
  const [betaModalOpen, setBetaModalOpen] = useState(false);
  // Guards the redirect below to fire at most once per mount. Without it,
  // anything that re-runs this effect (e.g. `router` not being referentially
  // stable across renders) re-issues both navigations below, and WKWebView
  // logs a genuine infinite loop -- repeated `didStartProvisionalNavigation`/
  // `setMainDocumentError(code=-999)` pairs, dozens per second, forever. That
  // showed up as the app "blinking" and never becoming usable (the "build 8"
  // bug). A one-shot ref makes that structurally impossible regardless of
  // why the effect re-fires.
  const hasRedirectedToAppRef = useRef(false);
  useEffect(() => {
    if (hasRedirectedToAppRef.current) return;
    if (isNativePlatform()) {
      hasRedirectedToAppRef.current = true;
      // router.replace first so Next's client router has a consistent route
      // state; it gets immediately superseded by the hard nav below (visible
      // in WKWebView logs as one cancelled navigation), which is expected.
      router.replace("/app");
      // Hard nav to the *exact file*, not the extensionless "/app" path:
      // this static export produces BOTH out/app.html (the real page) and
      // an out/app/ directory (RSC prefetch fragments only, no index.html)
      // -- the same ambiguity that once broke `/app` under local `serve`
      // (see frontend/Dockerfile history). Capacitor's WKWebView asset
      // server resolves the extensionless path against that directory,
      // finds no index.html, and falls back to index.html -- which
      // remounts this component and (absent the ref guard above) fires
      // this effect again. Requesting the exact file removes that
      // ambiguity entirely.
      window.location.replace("/app.html");
    } else {
      const timer = setTimeout(() => setShowMarketing(true), 0);
      return () => clearTimeout(timer);
    }
  }, [router]);

  // Scroll reveal observer for landing page elements (ui-ux-pro-max standard)
  useEffect(() => {
    if (!showMarketing || typeof window === "undefined") return;
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const elements = document.querySelectorAll<HTMLElement>(".landing-page .scroll-reveal");
    let observer: IntersectionObserver | undefined;
    const setup = () => {
      observer?.disconnect();
      if (preference.matches) {
        elements.forEach((el) => { delete el.dataset.revealPending; el.classList.add("revealed"); });
        return;
      }
      observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add("revealed");
              delete (entry.target as HTMLElement).dataset.revealPending;
              observer?.unobserve(entry.target);
            }
          });
        },
        {
          threshold: 0.08,
          rootMargin: "0px 0px -40px 0px",
        }
      );

      elements.forEach((el) => {
        if (!el.classList.contains("revealed")) {
          el.dataset.revealPending = "true";
          observer?.observe(el);
        }
      });
    };
    setup();
    preference.addEventListener("change", setup);
    return () => {
      observer?.disconnect();
      preference.removeEventListener("change", setup);
      elements.forEach((el) => { delete el.dataset.revealPending; });
    };
  }, [showMarketing]);

  useEffect(() => {
    if (!showMarketing) return;
    const previous = document.documentElement.lang;
    document.documentElement.lang = lang;
    return () => { document.documentElement.lang = previous; };
  }, [showMarketing, lang]);

  const videoRef = useRef<HTMLVideoElement>(null);
  useEffect(() => {
    if (!showMarketing) return;
    const video = videoRef.current;
    if (!video) return;
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = () => {
      if (motion.matches || document.hidden) {
        video.pause();
      } else {
        if (!video.getAttribute("src")) video.src = `${process.env.NEXT_PUBLIC_BASE_PATH || ""}/bg.mp4`;
        video.play().catch(() => {});
      }
    };
    // Product imagery gets the network first; reduced motion loads only the poster.
    const timer = window.setTimeout(apply, 1800);
    motion.addEventListener("change", apply);
    document.addEventListener("visibilitychange", apply);
    return () => {
      clearTimeout(timer);
      motion.removeEventListener("change", apply);
      document.removeEventListener("visibilitychange", apply);
      video.pause();
    };
  }, [showMarketing]);

  if (!showMarketing) return null;

  const toolingFeatures = TOOLING_FEATURE_IDS.map((id) =>
    LANDING_FEATURES.find((f) => f.id === id),
  ).filter((f): f is (typeof LANDING_FEATURES)[number] => !!f);

  return (
    <div className={`landing-page ${landingStyles.page}`} style={{ position: "relative", minHeight: "100dvh", color: "#111827" }}>
      <div className={landingStyles.backdrop} aria-hidden="true">
        <video ref={videoRef} muted playsInline loop preload="none"
          poster={`${process.env.NEXT_PUBLIC_BASE_PATH || ""}/landing/mountain-poster.webp`} />
      </div>

      {/* ── Content Wrapper (Relative above video) ───────────────────── */}
      <div style={{ position: "relative", zIndex: 10 }}>
        {/* ── Top Navigation Bar (Product-Led & Clean Glass) ──────────── */}
        <header
          style={{
            position: "sticky",
            top: 0,
            zIndex: 50,
            background: "rgba(255, 255, 255, 0.75)",
            backdropFilter: "blur(20px)",
            WebkitBackdropFilter: "blur(20px)",
            borderBottom: "1px solid rgba(255, 255, 255, 0.7)",
            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.03)",
          }}
        >
          <div
            style={{
              maxWidth: "1200px",
              margin: "0 auto",
              padding: "0 24px",
              height: "70px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            {/* Brand Logo */}
            <Link
              href="/"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                textDecoration: "none",
                color: "#111827",
              }}
            >
              <div
                style={{
                  width: "36px",
                  height: "36px",
                  borderRadius: "10px",
                  background: "linear-gradient(135deg, #19ce8b, #10b981)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "0 4px 12px rgba(25, 206, 139, 0.3)",
                }}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#ffffff"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M3 15l5-5 4 4 9-9" />
                  <polyline points="16 5 21 5 21 10" />
                </svg>
              </div>
              <span
                style={{
                  fontFamily: "var(--font-outfit), sans-serif",
                  fontSize: "22px",
                  fontWeight: 700,
                  letterSpacing: "-0.8px",
                }}
              >
                Uphill<span style={{ color: "var(--landing-accent)" }}>.AI</span>
              </span>
            </Link>

            {/* Nav Actions: Language Switcher + CTA */}
            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
              {/* Segmented Language Selector */}
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  background: "rgba(255, 255, 255, 0.75)",
                  backdropFilter: "blur(12px)",
                  WebkitBackdropFilter: "blur(12px)",
                  border: "1px solid rgba(0, 0, 0, 0.1)",
                  borderRadius: "9999px",
                  padding: "3px",
                  boxShadow: "0 1px 3px rgba(0, 0, 0, 0.04)",
                }}
              >
                <button
                  type="button"
                  onClick={() => setLang("en")}
                  style={{
                    border: "none",
                    background: lang === "en" ? "#ffffff" : "transparent",
                    color: lang === "en" ? "#111827" : "#6b7280",
                    fontWeight: lang === "en" ? 700 : 500,
                    fontSize: "12px",
                    padding: "4px 10px",
                    borderRadius: "9999px",
                    cursor: "pointer",
                    boxShadow: lang === "en" ? "0 1px 3px rgba(0, 0, 0, 0.1)" : "none",
                    transition: "all 0.15s ease",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                  }}
                  aria-pressed={lang === "en"}
                  aria-label="Switch to English"
                >
                  <span>🇺🇸</span>
                  <span>EN</span>
                </button>
                <button
                  type="button"
                  onClick={() => setLang("vi")}
                  style={{
                    border: "none",
                    background: lang === "vi" ? "#ffffff" : "transparent",
                    color: lang === "vi" ? "#111827" : "#6b7280",
                    fontWeight: lang === "vi" ? 700 : 500,
                    fontSize: "12px",
                    padding: "4px 10px",
                    borderRadius: "9999px",
                    cursor: "pointer",
                    boxShadow: lang === "vi" ? "0 1px 3px rgba(0, 0, 0, 0.1)" : "none",
                    transition: "all 0.15s ease",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                  }}
                  aria-pressed={lang === "vi"}
                  aria-label="Switch to Vietnamese"
                >
                  <span>🇻🇳</span>
                  <span>VI</span>
                </button>
              </div>

              <button
                type="button"
                onClick={() => setBetaModalOpen(true)}
                className="desktop-only-cta"
                style={{
                  background: "rgba(16, 185, 129, 0.1)",
                  border: "1px solid rgba(16, 185, 129, 0.35)",
                  color: "#059669",
                  padding: "9px 18px",
                  borderRadius: "9999px",
                  fontSize: "13.5px",
                  fontWeight: 700,
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  boxShadow: "0 2px 8px rgba(16, 185, 129, 0.12)",
                  transition: "all 0.15s ease",
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.background = "rgba(16, 185, 129, 0.18)";
                  e.currentTarget.style.borderColor = "rgba(16, 185, 129, 0.6)";
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.background = "rgba(16, 185, 129, 0.1)";
                  e.currentTarget.style.borderColor = "rgba(16, 185, 129, 0.35)";
                }}
              >
                <DownloadSimple size={15} weight="bold" />
                <span>{t("landing_nav_beta_download")}</span>
              </button>

              <Link
                href="/app"
                className="desktop-only-cta"
                style={{
                  background: "#111827",
                  color: "#ffffff",
                  padding: "10px 20px",
                  borderRadius: "9999px",
                  fontSize: "14px",
                  fontWeight: 600,
                  textDecoration: "none",
                  boxShadow: "0 4px 14px rgba(0, 0, 0, 0.12)",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  transition: "transform 0.15s ease, background 0.15s ease",
                }}
              >
                <span>{t("landing_nav_cta")}</span>
                <ArrowRight size={15} weight="bold" />
              </Link>
            </div>
          </div>
        </header>

        {/* ── Main Marketing Body ────────────────────────────────────── */}
        <main>
          <section className={landingStyles.hero}>
            <div className={landingStyles.heroInner}>
              <div className={landingStyles.heroCopy}>
                <h1 className={landingStyles.heroTitle}>
                  <span>{t("landing_hero_line1")}</span>
                  <span>{t("landing_hero_line2")}</span>
                </h1>
                <p className={landingStyles.heroSubtitle}>{t("landing_subtitle")}</p>
                <div className={landingStyles.heroActions}>
                  <button type="button" onClick={() => setBetaModalOpen(true)} className={landingStyles.primaryAction}>
                    <DownloadSimple size={19} weight="bold" aria-hidden="true" />{t("landing_preview_download")}
                  </button>
                  <Link href="/app" className={landingStyles.webAction}>{t("landing_preview_web")}<ArrowRight size={18} aria-hidden="true" /></Link>
                </div>
              </div>

            </div>
          </section>

          {/* ── 4 Sequential Product Steps (Real App Walkthrough) ─────── */}
          <section
            id="how-it-works"
            className="landing-section-how-it-works"
          >
            <div className={landingStyles.sectionHeading}>
              <h2
                style={{
                  fontFamily: "var(--font-outfit), sans-serif",
                  fontSize: "clamp(26px, 4vw, 40px)",
                  fontWeight: 800,
                  color: "#111827",
                  letterSpacing: "-1px",
                  marginBottom: "12px",
                  textShadow: "0 2px 16px rgba(255, 255, 255, 0.8)",
                }}
              >
                {t("landing_steps_title")}
              </h2>
              <p
                style={{
                  fontSize: "17px",
                  color: "#374151",
                  maxWidth: "600px",
                  margin: "0 auto",
                  fontWeight: 500,
                }}
              >
                {t("landing_steps_subtitle")}
              </p>
            </div>

            <div className={landingStyles.trust}><TrustBanner lang={lang} /></div>
            {/* Real product views, captioned as example data. */}
            <div className="landing-steps-container">
              {STEPS.map((step, i) => {
                const isEven = i % 2 === 1;
                return (
                  <div
                    key={step.titleKey}
                    className={`landing-step-card scroll-reveal ${isEven ? "step-even" : "step-odd"} ${i === 3 ? landingStyles.reviewStep : ""}`}
                  >
                    {/* Left Column (or Right Column if isEven on desktop; always top on mobile) */}
                    <div className="landing-step-text-col">
                      <h3
                        style={{
                          fontFamily: "var(--font-outfit), sans-serif",
                          fontSize: "clamp(20px, 2.5vw, 26px)",
                          fontWeight: 700,
                          color: "#111827",
                          letterSpacing: "-0.6px",
                          marginBottom: "12px",
                          lineHeight: 1.25,
                        }}
                      >
                        {t(step.titleKey)}
                      </h3>

                      <p
                        style={{
                          fontSize: "15.5px",
                          lineHeight: 1.65,
                          color: "#4b5563",
                          marginBottom: "20px",
                        }}
                      >
                        {t(step.descKey)}
                      </p>

                      <Link
                        href={step.anchor}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "6px",
                          fontSize: "14.5px",
                          fontWeight: 600,
                          color: "var(--landing-accent-ink)",
                          textDecoration: "none",
                        }}
                      >
                        <span>{t("landing_step_science_link")}</span>
                      </Link>
                    </div>

                    {/* Screenshot Card Container */}
                    <div className="landing-step-img-col">
                      <ProductDevice shot={step.image} alt={t(step.altKey)} device={step.device} />
                      </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* ── Coach Uphill (AI Chat Agent) Feature Spotlight ──────── */}
          <section
            id="coach"
            className="landing-coach-section"
          >
            <div
              className="card-interactive-lift landing-coach-card scroll-reveal"
            >
              <div>
                <h2
                  style={{
                    fontFamily: "var(--font-outfit), sans-serif",
                    fontSize: "clamp(26px, 3.5vw, 36px)",
                    fontWeight: 800,
                    color: "#111827",
                    letterSpacing: "-0.8px",
                    lineHeight: 1.2,
                    marginBottom: "14px",
                  }}
                >
                  {t("landing_coach_title")}
                </h2>
                <p
                  style={{
                    fontSize: "16px",
                    lineHeight: 1.65,
                    color: "#4b5563",
                    marginBottom: "24px",
                  }}
                >
                  {t("landing_coach_subtitle")}
                </p>

                <Link
                  href="/science#coach-grounding"
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "8px",
                    fontSize: "15px",
                    fontWeight: 700,
                    color: "var(--landing-accent-ink)",
                    textDecoration: "none",
                  }}
                >
                  <span>{t("landing_coach_science_link")}</span>
                  <ArrowRight size={16} weight="bold" />
                </Link>
              </div>

              <div className="landing-coach-img-col">
                <ProductDevice shot="ios-coach-saturday" device="phone" alt={t("landing_preview_coach_alt")} />
              </div>
            </div>
          </section>

          {/* ── Specialized Mountain Tools Strip ─────────────────────── */}
          <section
            id="tools"
            className="landing-tools-section"
          >
            <div style={{ maxWidth: "1140px", margin: "0 auto" }}>
              <div className={landingStyles.sectionHeading}>
                <h2
                  style={{
                    fontFamily: "var(--font-outfit), sans-serif",
                    fontSize: "clamp(26px, 3.5vw, 36px)",
                    fontWeight: 800,
                    color: "#111827",
                    letterSpacing: "-0.8px",
                    marginBottom: "10px",
                  }}
                >
                  {t("landing_tooling_title")}
                </h2>
                <p
                  style={{
                    fontSize: "16px",
                    color: "#4b5563",
                    maxWidth: "580px",
                    margin: "0 auto",
                    fontWeight: 500,
                  }}
                >
                  {t("landing_tooling_subtitle")}
                </p>
              </div>

              <div className="landing-tools-grid">
                {toolingFeatures.map((feature) => {
                  const copy = feature[lang];
                  const config = TOOL_CONFIG[feature.id as keyof typeof TOOL_CONFIG];
                  return (
                    <article key={feature.id} className="landing-tool-card scroll-reveal">
                      <div className={landingStyles.toolCopy}>
                        <h3>{config.label}</h3>
                        <p>{copy.cardBlurb}</p>
                        <Link href={config.anchor}>{t("landing_step_science_link")}</Link>
                      </div>
                      <ProductDevice shot={config.shot} device="phone" alt={t(config.alt)} />
                    </article>
                  );
                })}
              </div>

              <div style={{ textAlign: "center", marginTop: "40px" }}>
                <Link
                  href="/science"
                  style={{
                    fontSize: "15px",
                    fontWeight: 700,
                    color: "var(--landing-accent-ink)",
                    textDecoration: "none",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <span>{t("landing_tooling_cta")}</span>
                </Link>
              </div>
            </div>
          </section>

          {/* ── Connected Mountain Trail Ecosystem Strip ─────────────── */}
          <section id="sync" className={landingStyles.syncSection}>
            <div
              className={`scroll-reveal ${landingStyles.syncInner}`}
              style={{
                maxWidth: "1140px",
                margin: "0 auto",
                textAlign: "center",
                background: "rgba(255, 255, 255, 0.78)",
                backdropFilter: "blur(20px)",
                WebkitBackdropFilter: "blur(20px)",
                borderRadius: "24px",
                padding: "36px 28px",
                border: "1px solid rgba(255, 255, 255, 0.85)",
                boxShadow: "0 12px 32px rgba(0, 0, 0, 0.04)",
              }}
            >
              <div className={landingStyles.syncDevices}>
                <ProductDevice shot="ios-coros-workout" device="phone" alt={t("landing_preview_coros_alt")} />
                <div><CorosWatchPhoto lang={lang} /></div>
              </div>
              <div className={landingStyles.syncCopy}>
              <h3
                style={{
                  fontFamily: "var(--font-outfit), sans-serif",
                  fontSize: "20px",
                  fontWeight: 700,
                  color: "#111827",
                  marginBottom: "8px",
                }}
              >
                {t("landing_sync_title")}
              </h3>
              <p
                style={{
                  fontSize: "14.5px",
                  color: "#4b5563",
                  marginBottom: "24px",
                }}
              >
                {t("landing_sync_subtitle")}
              </p>

              {/* Platform Badges: COROS Live, others clearly Coming soon */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "28px",
                  flexWrap: "wrap",
                }}
              >
                {/* COROS - Active Integration */}
                <div
                  className="card-interactive-lift"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    color: "#111827",
                    fontSize: "15px",
                    fontWeight: 700,
                    padding: "8px 16px",
                    borderRadius: "9999px",
                    background: "rgba(25, 206, 139, 0.12)",
                    border: "1px solid rgba(25, 206, 139, 0.35)",
                  }}
                >
                  <span className="live-beacon-dot" />
                  <CheckCircle size={18} weight="fill" color="#19ce8b" />
                  <img src={`${process.env.NEXT_PUBLIC_BASE_PATH || ""}/brand/coros-logo.webp`} alt="COROS" width={92} height={24} style={{ width: 92, height: "auto" }} loading="lazy" />
                  <span
                    style={{
                      fontSize: "10.5px",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.5px",
                      color: "var(--landing-accent-ink)",
                      background: "rgba(25, 206, 139, 0.2)",
                      padding: "2px 7px",
                      borderRadius: "4px",
                      marginLeft: "4px",
                    }}
                  >
                    {t("landing_sync_live")}
                  </span>
                </div>

                {/* Coming Soon Platforms */}
                {[
                  { name: "Garmin Connect" },
                  { name: "Strava" },
                  { name: "Apple Watch" },
                ].map((item) => (
                  <div
                    key={item.name}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      color: "#6b7280",
                      fontSize: "14.5px",
                      fontWeight: 500,
                      opacity: 1,
                    }}
                  >
                    <span>{item.name}</span>
                    <span
                      style={{
                        fontSize: "10.5px",
                        fontWeight: 600,
                        color: "#6b7280",
                        background: "rgba(0, 0, 0, 0.05)",
                        padding: "2px 6px",
                        borderRadius: "4px",
                      }}
                    >
                      {t("landing_sync_coming_soon")}
                    </span>
                  </div>
                ))}
              </div>
              </div>
            </div>
          </section>

          {/* ── Foundational Methodology & Acknowledgement (The Legends Behind Uphill AI) ── */}
          <section
            id="methodology"
            className="motion-fade-up"
            style={{
              padding: "96px 24px",
              maxWidth: "1140px",
              margin: "0 auto",
              boxSizing: "border-box",
            }}
          >
            {/* Header */}
            <div className={landingStyles.sectionHeading}>
              <h2
                style={{
                  fontFamily: "var(--font-outfit), sans-serif",
                  fontSize: "clamp(28px, 4vw, 40px)",
                  fontWeight: 800,
                  color: "#111827",
                  letterSpacing: "-1px",
                  marginBottom: "16px",
                  textShadow: "0 2px 16px rgba(255, 255, 255, 0.8)",
                }}
              >
                {t("landing_ack_title")}
              </h2>
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "4px 14px",
                  borderRadius: "999px",
                  background: "rgba(25, 206, 139, 0.12)",
                  border: "1px solid rgba(25, 206, 139, 0.28)",
                  color: "var(--landing-accent-ink)",
                  fontSize: "11px",
                  fontWeight: 700,
                  letterSpacing: "0.12em",
                  textTransform: "uppercase",
                  marginBottom: "14px",
                }}
              >
                <Mountains size={14} weight="bold" />
                <span>{t("landing_ack_eyebrow")}</span>
              </div>

              <p
                style={{
                  fontSize: "17px",
                  lineHeight: "1.65",
                  color: "#374151",
                  maxWidth: "760px",
                  margin: "0 auto",
                  fontWeight: 500,
                }}
              >
                {t("landing_ack_subtitle")}
              </p>
            </div>

            {/* Unified Master Showcase Card: The Definitive Textbook + 3 Co-Founders & Authors */}
            <div
              className="methodology-unified-card scroll-reveal"
              style={{
                background: "rgba(255, 255, 255, 0.88)",
                backdropFilter: "blur(28px)",
                WebkitBackdropFilter: "blur(28px)",
                borderRadius: "32px",
                border: "1px solid rgba(255, 255, 255, 0.95)",
                boxShadow: "0 24px 60px rgba(0, 0, 0, 0.06), 0 2px 6px rgba(0, 0, 0, 0.02)",
                padding: "clamp(28px, 4vw, 44px)",
                display: "flex",
                flexDirection: "column",
                gap: "32px",
                position: "relative",
                overflow: "hidden",
              }}
            >
              {/* Subtle top-right ambient glow */}
              <div
                className="ambient-aura-breathing"
                style={{
                  position: "absolute",
                  top: "-100px",
                  right: "-80px",
                  width: "360px",
                  height: "360px",
                  borderRadius: "50%",
                  background: "radial-gradient(circle, rgba(25, 206, 139, 0.07) 0%, rgba(25, 206, 139, 0) 70%)",
                  pointerEvents: "none",
                }}
              />

              {/* ── Upper Section: The Definitive Textbook (3D Book + Description + Pull Quote) ── */}
              <div className="methodology-book-grid">
                {/* Left Column: 3D Book Mockup with floating motion */}
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    position: "relative",
                    padding: "8px 0",
                  }}
                >
                  <div
                    style={{
                      position: "relative",
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      width: "100%",
                      maxWidth: "320px",
                    }}
                  >
                    <a
                      href="https://www.amazon.com.au/Training-Uphill-Athlete-Mountain-Mountaineers/dp/1938340841"
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ display: "block", textDecoration: "none" }}
                      aria-label="Training for the Uphill Athlete on Amazon"
                    >
                      <img
                        src="/training-for-the-uphill-athlete.png"
                        alt="Training for the Uphill Athlete by Steve House, Scott Johnston, and Kilian Jornet"
                        width={360}
                        height={460}
                        className="book-mockup-floating"
                        style={{
                          width: "100%",
                          maxWidth: "280px",
                          height: "auto",
                          display: "block",
                          filter: "drop-shadow(0 20px 28px rgba(0, 0, 0, 0.18))",
                          cursor: "pointer",
                        }}
                      />
                    </a>
                  </div>
                  {/* Soft shadow accent below book */}
                  <div
                    style={{
                      width: "180px",
                      height: "16px",
                      background: "radial-gradient(ellipse at center, rgba(0,0,0,0.18) 0%, rgba(0,0,0,0) 70%)",
                      marginTop: "6px",
                    }}
                  />
                </div>

                {/* Right Column: Textbook Details & Direct Buy Link */}
                <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                    <span
                      style={{
                        fontSize: "11px",
                        fontWeight: 700,
                        letterSpacing: "0.1em",
                        textTransform: "uppercase",
                        color: "var(--landing-accent-ink)",
                        background: "rgba(25, 206, 139, 0.12)",
                        padding: "3px 10px",
                        borderRadius: "6px",
                      }}
                    >
                      {t("landing_ack_book_role")}
                    </span>
                    <span
                      style={{
                        fontSize: "12px",
                        fontWeight: 600,
                        color: "#6B7280",
                      }}
                    >
                      Patagonia Books
                    </span>
                  </div>

                  <h3
                    style={{
                      fontFamily: "var(--font-outfit), sans-serif",
                      fontSize: "clamp(24px, 2.8vw, 30px)",
                      fontWeight: 800,
                      color: "#111827",
                      letterSpacing: "-0.8px",
                      margin: 0,
                      lineHeight: 1.2,
                    }}
                  >
                    {t("landing_ack_book_name")}
                  </h3>

                  <p
                    style={{
                      fontSize: "14px",
                      fontWeight: 600,
                      color: "#4B5563",
                      margin: 0,
                    }}
                  >
                    {t("landing_ack_book_sub")}
                  </p>

                  <p
                    style={{
                      fontSize: "15px",
                      lineHeight: "1.6",
                      color: "#374151",
                      margin: 0,
                    }}
                  >
                    {t("landing_ack_book_desc")}
                  </p>

                  {/* Pull Quote */}
                  <blockquote
                    style={{
                      margin: "8px 0 4px",
                      padding: "14px 18px",
                      background: "rgba(240, 253, 244, 0.85)",
                      borderLeft: "1px solid var(--landing-accent-ink)",
                      borderRadius: "0 12px 12px 0",
                    }}
                  >
                    <p
                      style={{
                        fontSize: "14.5px",
                        fontStyle: "italic",
                        color: "#1F2937",
                        lineHeight: "1.55",
                        margin: "0 0 6px",
                      }}
                    >
                      {t("landing_ack_quote")}
                    </p>
                    <footer
                      style={{
                        fontSize: "12.5px",
                        fontWeight: 600,
                        color: "var(--landing-accent-ink)",
                      }}
                    >
                      {t("landing_ack_quote_author")}
                    </footer>
                  </blockquote>

                  {/* Action Links */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "14px",
                      marginTop: "6px",
                      flexWrap: "wrap",
                    }}
                  >
                    <a
                      href="https://www.amazon.com.au/Training-Uphill-Athlete-Mountain-Mountaineers/dp/1938340841"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-cta-motion"
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "8px",
                        padding: "11px 22px",
                        borderRadius: "12px",
                        background: "var(--accent-primary)",
                        color: "#ffffff",
                        fontSize: "14px",
                        fontWeight: 700,
                        textDecoration: "none",
                        boxShadow: "0 4px 14px rgba(25, 206, 139, 0.35)",
                      }}
                    >
                      <span>{t("landing_ack_amazon_btn")}</span>
                      <span className="cta-arrow">→</span>
                    </a>

                    <Link
                      href="/science"
                      style={{
                        fontSize: "13.5px",
                        fontWeight: 600,
                        color: "#1F2937",
                        textDecoration: "none",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "4px",
                      }}
                    >
                      <span>{t("landing_ack_science_link")}</span>
                    </Link>
                  </div>
                </div>
              </div>

              {/* ── Sleek Inset Divider with Pill Label ── */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "14px",
                  margin: "4px 0 0",
                }}
              >
                <div style={{ flex: 1, height: "1px", background: "linear-gradient(90deg, rgba(0,0,0,0.01), rgba(0,0,0,0.08))" }} />
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                    color: "var(--landing-accent-ink)",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                    background: "rgba(25, 206, 139, 0.08)",
                    border: "1px solid rgba(25, 206, 139, 0.2)",
                    padding: "4px 14px",
                    borderRadius: "999px",
                  }}
                >
                  <Mountains size={13} weight="bold" />
                  <span>{t("landing_ack_authors_divider")}</span>
                </span>
                <div style={{ flex: 1, height: "1px", background: "linear-gradient(90deg, rgba(0,0,0,0.08), rgba(0,0,0,0.01))" }} />
              </div>

              {/* ── Lower Section: Three Authors Inset Shelf (Scott, Kilian & Steve) ── */}
              <div className="landing-authors-grid">
                {/* Scott Johnston Card */}
                <div
                  className="card-interactive-lift scroll-reveal stagger-1"
                  style={{
                    background: "rgba(249, 250, 251, 0.8)",
                    backdropFilter: "blur(16px)",
                    WebkitBackdropFilter: "blur(16px)",
                    borderRadius: "16px",
                    border: "1px solid rgba(229, 231, 235, 0.85)",
                    boxShadow: "0 2px 10px rgba(0, 0, 0, 0.02)",
                    padding: "18px 20px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "10px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <div
                      style={{
                        width: "38px",
                        height: "38px",
                        borderRadius: "10px",
                        background: "rgba(25, 206, 139, 0.12)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "var(--landing-accent-ink)",
                        flexShrink: 0,
                      }}
                    >
                      <ChartLineUp size={20} weight="bold" />
                    </div>
                    <div>
                      <span
                        style={{
                          fontSize: "10.5px",
                          fontWeight: 700,
                          letterSpacing: "0.08em",
                          textTransform: "uppercase",
                          color: "var(--landing-accent-ink)",
                          display: "block",
                        }}
                      >
                        {t("landing_ack_scott_role")}
                      </span>
                      <h4
                        style={{
                          fontFamily: "var(--font-outfit), sans-serif",
                          fontSize: "18.5px",
                          fontWeight: 800,
                          color: "#111827",
                          margin: "2px 0 0",
                        }}
                      >
                        {t("landing_ack_scott_name")}
                      </h4>
                    </div>
                  </div>

                  <div
                    style={{
                      fontSize: "12px",
                      fontWeight: 600,
                      color: "#374151",
                      background: "rgba(0, 0, 0, 0.03)",
                      padding: "5px 10px",
                      borderRadius: "8px",
                      alignSelf: "flex-start",
                    }}
                  >
                    {t("landing_ack_scott_sub")}
                  </div>
                </div>

                {/* Kilian Jornet Card */}
                <div
                  className="card-interactive-lift scroll-reveal stagger-2"
                  style={{
                    background: "rgba(249, 250, 251, 0.8)",
                    backdropFilter: "blur(16px)",
                    WebkitBackdropFilter: "blur(16px)",
                    borderRadius: "16px",
                    border: "1px solid rgba(229, 231, 235, 0.85)",
                    boxShadow: "0 2px 10px rgba(0, 0, 0, 0.02)",
                    padding: "18px 20px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "10px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <div
                      style={{
                        width: "38px",
                        height: "38px",
                        borderRadius: "10px",
                        background: "rgba(25, 206, 139, 0.12)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "var(--landing-accent-ink)",
                        flexShrink: 0,
                      }}
                    >
                      <Trophy size={20} weight="bold" />
                    </div>
                    <div>
                      <span
                        style={{
                          fontSize: "10.5px",
                          fontWeight: 700,
                          letterSpacing: "0.08em",
                          textTransform: "uppercase",
                          color: "var(--landing-accent-ink)",
                          display: "block",
                        }}
                      >
                        {t("landing_ack_kilian_role")}
                      </span>
                      <h4
                        style={{
                          fontFamily: "var(--font-outfit), sans-serif",
                          fontSize: "18.5px",
                          fontWeight: 800,
                          color: "#111827",
                          margin: "2px 0 0",
                        }}
                      >
                        {t("landing_ack_kilian_name")}
                      </h4>
                    </div>
                  </div>

                  <div
                    style={{
                      fontSize: "12px",
                      fontWeight: 600,
                      color: "#374151",
                      background: "rgba(0, 0, 0, 0.03)",
                      padding: "5px 10px",
                      borderRadius: "8px",
                      alignSelf: "flex-start",
                    }}
                  >
                    {t("landing_ack_kilian_sub")}
                  </div>
                </div>

                {/* Steve House Card */}
                <div
                  className="card-interactive-lift scroll-reveal stagger-3"
                  style={{
                    background: "rgba(249, 250, 251, 0.8)",
                    backdropFilter: "blur(16px)",
                    WebkitBackdropFilter: "blur(16px)",
                    borderRadius: "16px",
                    border: "1px solid rgba(229, 231, 235, 0.85)",
                    boxShadow: "0 2px 10px rgba(0, 0, 0, 0.02)",
                    padding: "18px 20px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "10px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <div
                      style={{
                        width: "38px",
                        height: "38px",
                        borderRadius: "10px",
                        background: "rgba(25, 206, 139, 0.12)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "var(--landing-accent-ink)",
                        flexShrink: 0,
                      }}
                    >
                      <Mountains size={20} weight="bold" />
                    </div>
                    <div>
                      <span
                        style={{
                          fontSize: "10.5px",
                          fontWeight: 700,
                          letterSpacing: "0.08em",
                          textTransform: "uppercase",
                          color: "var(--landing-accent-ink)",
                          display: "block",
                        }}
                      >
                        {t("landing_ack_steve_role")}
                      </span>
                      <h4
                        style={{
                          fontFamily: "var(--font-outfit), sans-serif",
                          fontSize: "18.5px",
                          fontWeight: 800,
                          color: "#111827",
                          margin: "2px 0 0",
                        }}
                      >
                        {t("landing_ack_steve_name")}
                      </h4>
                    </div>
                  </div>

                  <div
                    style={{
                      fontSize: "12px",
                      fontWeight: 600,
                      color: "#374151",
                      background: "rgba(0, 0, 0, 0.03)",
                      padding: "5px 10px",
                      borderRadius: "8px",
                      alignSelf: "flex-start",
                    }}
                  >
                    {t("landing_ack_steve_sub")}
                  </div>
                </div>
              </div>
            </div>
          </section>

          <div id="comparison" style={{ padding: "0 24px", display: "flex", justifyContent: "center", scrollMarginTop: "96px" }}>
            <ComparisonSection lang={lang} />
          </div>

          {/* ── Proof Slot (Empty behind a flag per brief) ───────────── */}
          {SHOW_PROOF_CONTENT ? (
            <section
              style={{
                padding: "32px 24px",
                textAlign: "center",
              }}
            >
              <h3
                style={{
                  fontFamily: "var(--font-outfit), sans-serif",
                  fontSize: "18px",
                  fontWeight: 600,
                  color: "#9ca3af",
                  marginBottom: "6px",
                }}
              >
                {t("landing_proof_title")}
              </h3>
              <p style={{ color: "#9ca3af", fontSize: "13.5px", margin: 0 }}>
                {t("landing_proof_placeholder")}
              </p>
            </section>
          ) : null}

          {/* ── Closing Call to Action Section ────────────────────────── */}
          <section
            style={{
              padding: "72px 24px 96px",
              textAlign: "center",
            }}
          >
            <div
              className={`scroll-reveal ${landingStyles.closing}`}
              style={{
                maxWidth: "1120px",
                margin: "0 auto",
                background: "rgba(255, 255, 255, 0.82)",
                backdropFilter: "blur(24px)",
                WebkitBackdropFilter: "blur(24px)",
                padding: "48px 32px",
                borderRadius: "28px",
                border: "1px solid rgba(255, 255, 255, 0.9)",
                boxShadow: "0 20px 48px rgba(0, 0, 0, 0.08)",
              }}
            >
              <h2
                style={{
                  fontFamily: "var(--font-outfit), sans-serif",
                  fontSize: "clamp(28px, 4vw, 40px)",
                  fontWeight: 800,
                  color: "#111827",
                  letterSpacing: "-1px",
                  marginBottom: "14px",
                }}
              >
                {t("landing_closing_title")}
              </h2>
              <p
                style={{
                  color: "#4b5563",
                  fontSize: "17px",
                  lineHeight: 1.5,
                  marginBottom: "32px",
                }}
              >
                {t("landing_closing_subtitle")}
              </p>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "14px",
                  flexWrap: "wrap",
                }}
              >
                <Link
                  href="/app"
                  className="btn-primary-motion"
                  style={{
                    background: "#111827",
                    color: "#ffffff",
                    padding: "18px 44px",
                    fontSize: "17px",
                    borderRadius: "9999px",
                    fontWeight: 700,
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "10px",
                    textDecoration: "none",
                    boxShadow: "0 8px 28px rgba(0, 0, 0, 0.2)",
                  }}
                >
                  <span>{t("landing_cta_primary")}</span>
                  <ArrowRight size={18} weight="bold" className="cta-arrow" />
                </Link>

                <button
                  type="button"
                  onClick={() => setBetaModalOpen(true)}
                  className="btn-secondary-motion"
                  style={{
                    background: "rgba(16, 185, 129, 0.12)",
                    backdropFilter: "blur(16px)",
                    WebkitBackdropFilter: "blur(16px)",
                    color: "#047857",
                    border: "1px solid rgba(16, 185, 129, 0.35)",
                    padding: "18px 36px",
                    borderRadius: "9999px",
                    fontSize: "17px",
                    fontWeight: 700,
                    cursor: "pointer",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "8px",
                    boxShadow: "0 4px 20px rgba(16, 185, 129, 0.1)",
                    transition: "all 0.15s ease",
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.background = "rgba(16, 185, 129, 0.2)";
                    e.currentTarget.style.borderColor = "rgba(16, 185, 129, 0.6)";
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.background = "rgba(16, 185, 129, 0.12)";
                    e.currentTarget.style.borderColor = "rgba(16, 185, 129, 0.35)";
                  }}
                >
                  <DownloadSimple size={18} weight="bold" />
                  <span>{t("landing_closing_beta_download")}</span>
                </button>
              </div>
            </div>
          </section>
        </main>

        {/* ── Minimalist Clean Frosted Footer ─────────────────────────── */}
        <footer
          style={{
            borderTop: "1px solid rgba(255, 255, 255, 0.7)",
            padding: "40px 24px",
            background: "rgba(255, 255, 255, 0.75)",
            backdropFilter: "blur(20px)",
            WebkitBackdropFilter: "blur(20px)",
          }}
        >
          <div
            style={{
              maxWidth: "1140px",
              margin: "0 auto",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "20px",
            }}
          >
            {/* Logo & Tagline */}
            <div>
              <div
                style={{
                  fontFamily: "var(--font-outfit), sans-serif",
                  fontSize: "18px",
                  fontWeight: 700,
                  color: "#111827",
                  marginBottom: "4px",
                }}
              >
                Uphill<span style={{ color: "var(--landing-accent)" }}>.AI</span>
              </div>
              <p style={{ color: "#6b7280", fontSize: "13px", margin: 0 }}>
                {t("landing_footer_tagline")}
              </p>
            </div>

            {/* Footer Links & Copyright */}
            <div
              className={landingStyles.footerLinks}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "24px",
                fontSize: "13.5px",
                color: "#4b5563",
              }}
            >
              <Link
                href="/science"
                style={{ color: "#4b5563", textDecoration: "none" }}
              >
                {t("landing_nav_science")}
              </Link>
              <Link
                href="/app"
                style={{ color: "#4b5563", textDecoration: "none" }}
              >
                {t("landing_nav_signin")}
              </Link>
              <button
                onClick={() => setLang(lang === "en" ? "vi" : "en")}
                style={{
                  background: "none",
                  border: "none",
                  color: "#4b5563",
                  cursor: "pointer",
                  padding: 0,
                  fontSize: "13.5px",
                }}
              >
                {lang === "en" ? "Tiếng Việt" : "English"}
              </button>
              <span className={landingStyles.copyright}>
                © {new Date().getFullYear()} Uphill.AI. {t("landing_footer_rights")}
              </span>
            </div>
          </div>
        </footer>

        {/* ── Beta Download Lead Capture & Distribution Modal ─────────── */}
        <BetaDownloadModal
          isOpen={betaModalOpen}
          onClose={() => setBetaModalOpen(false)}
          lang={lang}
        />
      </div>
    </div>
  );
}
