"use client";
import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Crosshair,
  Gauge,
  Sneaker,
  BowlFood,
  MapPin,
  CalendarBlank,
  ArrowsClockwise,
  Trophy,
  ShieldCheck,
  ChartLineUp,
  Mountains,
  CheckCircle,
  Robot,
  ArrowRight,
  DownloadSimple,
} from "@phosphor-icons/react";
import { useAppContext } from "@/contexts/AppContext";
import { translations } from "./translations";
import { isNativePlatform } from "@/utils/native";
import { TrustBanner } from "@/components/landing/TrustBanner";
import { LANDING_FEATURES } from "@/data/landingFeatures";
import { BetaDownloadModal } from "@/components/landing/BetaDownloadModal";

// Whether the Proof section renders real numbers/testimonials yet.
// TODO(proof-section): flip on once we have plans-generated counts,
// athletes' completed goal races, or named testimonials with outcome
// labels to show. Never fabricate these to fill the slot early.
const SHOW_PROOF_CONTENT = false;

const TOOLING_ICONS = { Crosshair, Gauge, Sneaker, BowlFood };
const TOOLING_FEATURE_IDS = ["pace", "goal", "gear", "nutrition"] as const;

type Step = {
  icon: React.ElementType;
  titleKey: keyof typeof translations.en;
  descKey: keyof typeof translations.en;
  altKey: keyof typeof translations.en;
  image: string;
  anchor: string;
};

const STEPS: Step[] = [
  {
    icon: MapPin,
    titleKey: "landing_step1_title",
    descKey: "landing_step1_desc",
    altKey: "landing_step1_alt",
    image: "/screenshots/tell-us-where-you-are.png",
    anchor: "/science#thresholds",
  },
  {
    icon: CalendarBlank,
    titleKey: "landing_step2_title",
    descKey: "landing_step2_desc",
    altKey: "landing_step2_alt",
    image: "/screenshots/current-planner-view.png",
    anchor: "/science#thresholds",
  },
  {
    icon: ArrowsClockwise,
    titleKey: "landing_step3_title",
    descKey: "landing_step3_desc",
    altKey: "landing_step3_alt",
    image: "/screenshots/adapt-week-feeling-selector.png",
    anchor: "/science#adaptation",
  },
  {
    icon: Trophy,
    titleKey: "landing_step4_title",
    descKey: "landing_step4_desc",
    altKey: "landing_step4_alt",
    image: "/screenshots/block-review-coach-feedback.png",
    anchor: "/science#block-evaluation",
  },
];

const TOOL_CONFIG: Record<
  "pace" | "goal" | "gear" | "nutrition",
  {
    image: string;
    anchor: string;
    alt: string;
  }
> = {
  pace: {
    image: "/screenshots/tool-pace-strategy.png",
    anchor: "/science#pace-physics",
    alt: "Pace Strategy splits table and elevation breakdown",
  },
  goal: {
    image: "/screenshots/tool-goal-determiner.png",
    anchor: "/science#goal-prediction",
    alt: "Goal Determiner finish time predictor and A/B/C goals",
  },
  gear: {
    image: "/screenshots/tool-gear-finder.png",
    anchor: "/science#gear-grounding",
    alt: "Gear Finder technical trail shoe match and verified specs",
  },
  nutrition: {
    image: "/screenshots/tool-nutrition-lab.png",
    anchor: "/science#nutrition-grounding",
    alt: "Nutrition Lab metabolic hour-by-hour race fuel plan",
  },
};

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
  useEffect(() => {
    if (isNativePlatform()) {
      router.replace("/app");
    } else {
      const timer = setTimeout(() => setShowMarketing(true), 0);
      return () => clearTimeout(timer);
    }
  }, [router]);

  // Scroll reveal observer for landing page elements (ui-ux-pro-max standard)
  useEffect(() => {
    if (!showMarketing || typeof window === "undefined") return;
    const isReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (isReducedMotion) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("revealed");
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.08,
        rootMargin: "0px 0px -40px 0px",
      }
    );

    const elements = document.querySelectorAll(".scroll-reveal");
    elements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, [showMarketing]);

  // Video background refs — dual-video crossfade engine
  const videoARef = useRef<HTMLVideoElement>(null);
  const videoBRef = useRef<HTMLVideoElement>(null);
  const activeVideoRef = useRef<"A" | "B">("A");
  const crossfadeRafARef = useRef<number | null>(null);
  const crossfadeRafBRef = useRef<number | null>(null);
  const crossfadingRef = useRef(false);

  useEffect(() => {
    const vidA = videoARef.current;
    const vidB = videoBRef.current;
    if (!vidA || !vidB) return;
    const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";
    const SRC = basePath + "/bg.mp4";
    const FADE_MS = 250;
    const FADE_THRESHOLD = 0.55;
    vidA.src = SRC;
    vidB.src = SRC;
    vidA.muted = true;
    vidB.muted = true;

    const animateFade = (
      el: HTMLVideoElement,
      rafRef: React.MutableRefObject<number | null>,
      from: number,
      to: number,
      onDone?: () => void,
    ) => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
      const t0 = performance.now();
      const d = to - from;
      const tick = (now: number) => {
        const p = Math.min((now - t0) / FADE_MS, 1);
        el.style.opacity = String(from + d * p);
        if (p < 1) {
          rafRef.current = requestAnimationFrame(tick);
        } else {
          rafRef.current = null;
          onDone?.();
        }
      };
      rafRef.current = requestAnimationFrame(tick);
    };

    const triggerCrossfade = () => {
      if (crossfadingRef.current) return;
      crossfadingRef.current = true;
      const outVid = activeVideoRef.current === "A" ? vidA : vidB;
      const inVid = activeVideoRef.current === "A" ? vidB : vidA;
      const outRaf =
        activeVideoRef.current === "A" ? crossfadeRafARef : crossfadeRafBRef;
      const inRaf =
        activeVideoRef.current === "A" ? crossfadeRafBRef : crossfadeRafARef;

      inVid.currentTime = 0;
      inVid.style.opacity = "0";
      inVid.style.zIndex = "2";
      outVid.style.zIndex = "1";
      inVid.play().catch(() => {});

      animateFade(outVid, outRaf, 1, 0, () => {
        outVid.pause();
        crossfadingRef.current = false;
        activeVideoRef.current = activeVideoRef.current === "A" ? "B" : "A";
      });
      animateFade(inVid, inRaf, 0, 1);
    };

    const handleTimeUpdateA = () => {
      if (!vidA.duration || activeVideoRef.current !== "A") return;
      if (vidA.duration - vidA.currentTime <= FADE_THRESHOLD) triggerCrossfade();
    };
    const handleTimeUpdateB = () => {
      if (!vidB.duration || activeVideoRef.current !== "B") return;
      if (vidB.duration - vidB.currentTime <= FADE_THRESHOLD) triggerCrossfade();
    };

    vidA.addEventListener("timeupdate", handleTimeUpdateA);
    vidB.addEventListener("timeupdate", handleTimeUpdateB);
    vidA.style.opacity = "1";
    vidA.play().catch(() => {});

    return () => {
      vidA.removeEventListener("timeupdate", handleTimeUpdateA);
      vidB.removeEventListener("timeupdate", handleTimeUpdateB);
      if (crossfadeRafARef.current !== null)
        cancelAnimationFrame(crossfadeRafARef.current);
      if (crossfadeRafBRef.current !== null)
        cancelAnimationFrame(crossfadeRafBRef.current);
    };
  }, [showMarketing]);


  if (!showMarketing) return null;

  const toolingFeatures = TOOLING_FEATURE_IDS.map((id) =>
    LANDING_FEATURES.find((f) => f.id === id),
  ).filter((f): f is (typeof LANDING_FEATURES)[number] => !!f);

  return (
    <div style={{ position: "relative", minHeight: "100dvh", color: "#111827" }}>
      {/* ── Fixed Video Background Layer ─────────────────────────────── */}
      <div
        className="video-bg-container"
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 0,
          overflow: "hidden",
          pointerEvents: "none",
          background: "#0d1117",
        }}
      >
        <video
          ref={videoARef}
          autoPlay
          muted
          playsInline
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            width: "115%",
            height: "115%",
            transform: "translate(-50%, -50%)",
            objectFit: "cover",
            objectPosition: "center top",
            opacity: 0,
            willChange: "opacity",
            zIndex: 2,
            pointerEvents: "none",
          }}
        />
        <video
          ref={videoBRef}
          autoPlay
          muted
          playsInline
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            width: "115%",
            height: "115%",
            transform: "translate(-50%, -50%)",
            objectFit: "cover",
            objectPosition: "center top",
            opacity: 0,
            willChange: "opacity",
            zIndex: 1,
            pointerEvents: "none",
          }}
        />
        {/* Soft light vignette overlay keeping video atmospheric while ensuring text legibility */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "radial-gradient(ellipse at 50% 15%, rgba(255, 255, 255, 0.48) 0%, rgba(255, 255, 255, 0.75) 60%, rgba(255, 255, 255, 0.88) 100%)",
            pointerEvents: "none",
            zIndex: 3,
          }}
        />
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
                  fontFamily: "var(--font-schibsted), sans-serif",
                  fontSize: "22px",
                  fontWeight: 700,
                  letterSpacing: "-0.8px",
                }}
              >
                Uphill<span style={{ color: "var(--accent-primary)" }}>.AI</span>
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
          {/* ── Hero Section (Product-Led Presentation over Video) ───── */}
          <section
            style={{
              position: "relative",
              padding: "64px 24px 72px",
            }}
          >
            <div
              className="motion-fade-up"
              style={{
                maxWidth: "960px",
                margin: "0 auto",
                textAlign: "center",
              }}
            >
              {/* Eyebrow badge */}
              <div
                className="hero-anim-badge"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "6px 14px",
                  borderRadius: "9999px",
                  background: "rgba(25, 206, 139, 0.12)",
                  backdropFilter: "blur(12px)",
                  border: "1px solid rgba(25, 206, 139, 0.3)",
                  color: "var(--accent-primary)",
                  fontSize: "13px",
                  fontWeight: 700,
                  marginBottom: "20px",
                }}
              >
                <ShieldCheck size={16} weight="bold" />
                <span>
                  {lang === "vi"
                    ? "KHOA HỌC CHẠY TRAIL"
                    : "GROUNDED IN EXERCISE PHYSIOLOGY"}
                </span>
              </div>

              {/* H1 Headline: strictly max 2 lines */}
              <h1
                className="hero-anim-title"
                style={{
                  fontFamily: "var(--font-schibsted), sans-serif",
                  fontSize: "clamp(38px, 5.5vw, 62px)",
                  fontWeight: 800,
                  lineHeight: 1.08,
                  letterSpacing: "-1.8px",
                  color: "#111827",
                  marginBottom: "18px",
                  textShadow: "0 2px 20px rgba(255, 255, 255, 0.8)",
                }}
              >
                {lang === "vi"
                  ? "Tập Luyện Thông Minh, Chinh Phục Đỉnh Cao"
                  : "Train Smarter, Go Higher"}
              </h1>

              {/* Subtext: under 20 words */}
              <p
                className="hero-anim-sub"
                style={{
                  fontSize: "clamp(16px, 2vw, 19px)",
                  lineHeight: 1.5,
                  color: "#0f172a",
                  maxWidth: "640px",
                  margin: "0 auto 32px",
                  fontWeight: 500,
                  textShadow: "0 1px 16px rgba(255, 255, 255, 0.95), 0 0 2px rgba(255, 255, 255, 0.8)",
                }}
              >
                {t("landing_subtitle")}
              </p>

              {/* Primary & Secondary Action Cluster */}
              <div
                className="hero-anim-cta"
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "16px",
                  marginBottom: "36px",
                  flexWrap: "wrap",
                }}
              >
                <Link
                  href="/app"
                  className="btn-primary-motion"
                  style={{
                    background: "#111827",
                    color: "#ffffff",
                    padding: "16px 36px",
                    borderRadius: "9999px",
                    fontSize: "16.5px",
                    fontWeight: 700,
                    textDecoration: "none",
                    boxShadow: "0 8px 24px rgba(0, 0, 0, 0.18)",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "10px",
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
                    padding: "16px 30px",
                    borderRadius: "9999px",
                    fontSize: "16.5px",
                    fontWeight: 700,
                    cursor: "pointer",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "8px",
                    boxShadow: "0 4px 16px rgba(16, 185, 129, 0.12)",
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
                  <span>{t("landing_hero_beta_download")}</span>
                </button>

                <Link
                  href="/science"
                  className="btn-secondary-motion"
                  style={{
                    background: "rgba(255, 255, 255, 0.75)",
                    backdropFilter: "blur(16px)",
                    color: "#111827",
                    border: "1px solid rgba(255, 255, 255, 0.9)",
                    padding: "16px 28px",
                    borderRadius: "9999px",
                    fontSize: "16.5px",
                    fontWeight: 600,
                    textDecoration: "none",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "8px",
                    boxShadow: "0 4px 16px rgba(0, 0, 0, 0.04)",
                  }}
                >
                  <span>{t("landing_nav_science")}</span>
                </Link>
              </div>

              {/* Trust Statement (Hero Integration) */}
              <div className="hero-anim-trust" style={{ display: "flex", justifyContent: "center" }}>
                <TrustBanner lang={lang} />
              </div>
            </div>
          </section>



          {/* ── 4 Sequential Product Steps (Real App Walkthrough) ─────── */}
          <section
            id="how-it-works"
            className="landing-section-how-it-works"
          >
            <div style={{ textAlign: "center", marginBottom: "48px" }}>
              <h2
                style={{
                  fontFamily: "var(--font-schibsted), sans-serif",
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

            {/* Steps alternating layout */}
            <div className="landing-steps-container">
              {STEPS.map((step, i) => {
                const Icon = step.icon;
                const isEven = i % 2 === 1;
                return (
                  <div
                    key={step.titleKey}
                    className={`card-interactive-lift landing-step-card scroll-reveal ${isEven ? "step-even" : "step-odd"}`}
                  >
                    {/* Left Column (or Right Column if isEven on desktop; always top on mobile) */}
                    <div className="landing-step-text-col">
                      <div
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "8px",
                          padding: "6px 12px",
                          borderRadius: "8px",
                          background: "rgba(25, 206, 139, 0.12)",
                          color: "var(--accent-primary)",
                          fontSize: "12.5px",
                          fontWeight: 700,
                          marginBottom: "16px",
                        }}
                      >
                        <Icon size={16} weight="bold" />
                        <span>{lang === "en" ? `Step 0${i + 1}` : `Bước 0${i + 1}`}</span>
                      </div>

                      <h3
                        style={{
                          fontFamily: "var(--font-schibsted), sans-serif",
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
                          color: "var(--accent-primary)",
                          textDecoration: "none",
                        }}
                      >
                        <span>{t("landing_step_science_link")}</span>
                      </Link>
                    </div>

                    {/* Screenshot Card Container */}
                    <div className="landing-step-img-col">
                      <img
                        src={step.image}
                        alt={t(step.altKey)}
                        width={1280}
                        height={720}
                        loading="lazy"
                        className="landing-step-img"
                      />
                    </div>
                  </div>
                );
              })}
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
            <div style={{ textAlign: "center", marginBottom: "56px" }}>
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "4px 14px",
                  borderRadius: "999px",
                  background: "rgba(25, 206, 139, 0.12)",
                  border: "1px solid rgba(25, 206, 139, 0.28)",
                  color: "var(--accent-primary)",
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
              <h2
                style={{
                  fontFamily: "var(--font-schibsted), sans-serif",
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
                        color: "var(--accent-primary)",
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
                      fontFamily: "var(--font-schibsted), sans-serif",
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
                      borderLeft: "4px solid var(--accent-primary)",
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
                        color: "var(--accent-primary)",
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
                    color: "var(--accent-primary)",
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
                        color: "var(--accent-primary)",
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
                          color: "var(--accent-primary)",
                          display: "block",
                        }}
                      >
                        {t("landing_ack_scott_role")}
                      </span>
                      <h4
                        style={{
                          fontFamily: "var(--font-schibsted), sans-serif",
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
                        color: "var(--accent-primary)",
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
                          color: "var(--accent-primary)",
                          display: "block",
                        }}
                      >
                        {t("landing_ack_kilian_role")}
                      </span>
                      <h4
                        style={{
                          fontFamily: "var(--font-schibsted), sans-serif",
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
                        color: "var(--accent-primary)",
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
                          color: "var(--accent-primary)",
                          display: "block",
                        }}
                      >
                        {t("landing_ack_steve_role")}
                      </span>
                      <h4
                        style={{
                          fontFamily: "var(--font-schibsted), sans-serif",
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

          {/* ── Coach Uphill (AI Chat Agent) Feature Spotlight ──────── */}
          <section
            id="coach"
            className="landing-coach-section"
          >
            <div
              className="card-interactive-lift landing-coach-card scroll-reveal"
            >
              <div>
                <div
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "8px",
                    padding: "6px 14px",
                    borderRadius: "9999px",
                    background: "rgba(25, 206, 139, 0.12)",
                    color: "var(--accent-primary)",
                    fontSize: "12.5px",
                    fontWeight: 700,
                    marginBottom: "16px",
                  }}
                >
                  <Robot size={18} weight="bold" />
                  <span>{t("landing_coach_eyebrow")}</span>
                </div>

                <h2
                  style={{
                    fontFamily: "var(--font-schibsted), sans-serif",
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
                    color: "var(--accent-primary)",
                    textDecoration: "none",
                  }}
                >
                  <span>{t("landing_coach_science_link")}</span>
                  <ArrowRight size={16} weight="bold" />
                </Link>
              </div>

              {/* Tight screenshot of chat exchange demonstrating refusal & citation */}
              <div className="landing-coach-img-col">
                <img
                  src="/screenshots/coach-uphill-chat-exchange.png"
                  alt="Coach Uphill chat exchange demonstrating source citation and refusal to recommend unverified supplements"
                  width={1360}
                  height={1200}
                  loading="lazy"
                  className="landing-coach-img"
                />
              </div>
            </div>
          </section>

          {/* ── Specialized Mountain Tools Strip ─────────────────────── */}
          <section
            id="tools"
            className="landing-tools-section"
          >
            <div style={{ maxWidth: "1140px", margin: "0 auto" }}>
              <div style={{ textAlign: "center", marginBottom: "48px" }}>
                <h2
                  style={{
                    fontFamily: "var(--font-schibsted), sans-serif",
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

              {/* 4 Tool Cards with Tight Screenshots (KoopAI-Style 2x2 Grid) */}
              <div className="landing-tools-grid">
                {toolingFeatures.map((feature, i) => {
                  const Icon = TOOLING_ICONS[feature.icon as keyof typeof TOOLING_ICONS];
                  const copy = feature[lang];
                  const config = TOOL_CONFIG[feature.id as keyof typeof TOOL_CONFIG];
                  return (
                    <div
                      key={feature.id}
                      className={`card-interactive-lift landing-tool-card scroll-reveal stagger-${i + 1}`}
                    >
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "14px",
                          marginBottom: "14px",
                        }}
                      >
                        <div
                          style={{
                            width: "44px",
                            height: "44px",
                            borderRadius: "12px",
                            background: "rgba(25, 206, 139, 0.12)",
                            color: "var(--accent-primary)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            flexShrink: 0,
                          }}
                        >
                          <Icon size={24} weight="duotone" />
                        </div>
                        <div>
                          <h3
                            style={{
                              fontFamily: "var(--font-schibsted), sans-serif",
                              fontSize: "19px",
                              fontWeight: 700,
                              color: "#111827",
                              margin: 0,
                            }}
                          >
                            {copy.tagline}
                          </h3>
                        </div>
                      </div>

                      <p
                        style={{
                          fontSize: "14px",
                          lineHeight: 1.55,
                          color: "#4b5563",
                          margin: "0 0 18px",
                        }}
                      >
                        {copy.cardBlurb}
                      </p>

                      {/* Tight Cropped Module Screenshot */}
                      <div className="landing-tool-img-box">
                        <img
                          src={config.image}
                          alt={config.alt}
                          width={1360}
                          height={800}
                          className="landing-tool-img"
                        />
                      </div>

                      <div style={{ marginTop: "auto" }}>
                        <Link
                          href={config.anchor}
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "6px",
                            fontSize: "14px",
                            fontWeight: 700,
                            color: "var(--accent-primary)",
                            textDecoration: "none",
                          }}
                        >
                          <span>{t("landing_step_science_link")}</span>
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div style={{ textAlign: "center", marginTop: "40px" }}>
                <Link
                  href="/science"
                  style={{
                    fontSize: "15px",
                    fontWeight: 700,
                    color: "var(--accent-primary)",
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
          <section style={{ padding: "64px 24px" }}>
            <div
              className="scroll-reveal"
              style={{
                maxWidth: "840px",
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
              <h3
                style={{
                  fontFamily: "var(--font-schibsted), sans-serif",
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
                  <span>COROS</span>
                  <span
                    style={{
                      fontSize: "10.5px",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.5px",
                      color: "var(--accent-primary)",
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
                      opacity: 0.55,
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
          </section>

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
                  fontFamily: "var(--font-schibsted), sans-serif",
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
              className="scroll-reveal"
              style={{
                maxWidth: "680px",
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
                  fontFamily: "var(--font-schibsted), sans-serif",
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
                  fontFamily: "var(--font-schibsted), sans-serif",
                  fontSize: "18px",
                  fontWeight: 700,
                  color: "#111827",
                  marginBottom: "4px",
                }}
              >
                Uphill<span style={{ color: "var(--accent-primary)" }}>.AI</span>
              </div>
              <p style={{ color: "#6b7280", fontSize: "13px", margin: 0 }}>
                {t("landing_footer_tagline")}
              </p>
            </div>

            {/* Footer Links & Copyright */}
            <div
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
              <span style={{ color: "#9ca3af" }}>
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
