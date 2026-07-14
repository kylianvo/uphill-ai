/* eslint-disable */
"use client";
import { useState, useEffect, useRef } from "react";
import { useAppContext } from "@/contexts/AppContext";
import HomeTab from "@/views/HomeTab";
import ChatTab from "@/views/ChatTab";
import AboutTab from "@/views/AboutTab";
import AuthModal from "@/views/AuthModal";
import OnboardingWizard from "@/views/OnboardingWizard";
import ProfileSettingsModal from "@/views/ProfileSettingsModal";
import PlannerView from "@/views/PlannerView";
import ToolsView from "@/views/ToolsView";
import KnowledgeView from "@/views/KnowledgeView";
import { NutritionLab } from "../components/NutritionLab";
import { GearVault } from "../components/GearVault";
import { PaceStrategy } from "../components/PaceStrategy";
import { translations } from "./translations";
import { useAnalytics } from "@/hooks/useAnalytics";
import {
  Robot,
  CalendarBlank,
  BookOpen,
  Calculator,
  Mountains,
  Warning,
  BowlFood,
  Bed,
  Timer,
  Brain,
  Backpack,
  CaretDown,
  CaretUp,
  Book,
  House,
} from "@phosphor-icons/react";
if (typeof window !== "undefined") {
  // Check for api query parameter to override API URL
  const params = new URLSearchParams(window.location.search);
  const apiParam = params.get("api");
  if (apiParam) {
    let cleanParam = apiParam.trim();
    if (
      (cleanParam.startsWith('"') && cleanParam.endsWith('"')) ||
      (cleanParam.startsWith("'") && cleanParam.endsWith("'"))
    ) {
      cleanParam = cleanParam.slice(1, -1).trim();
    }
    if (
      cleanParam === "default" ||
      cleanParam === "reset" ||
      cleanParam === "clear"
    ) {
      localStorage.removeItem("UPHILL_API_URL_OVERRIDE");
    } else {
      localStorage.setItem("UPHILL_API_URL_OVERRIDE", cleanParam);
    }
    // Remove query param from URL to keep it clean
    const cleanUrl = new URL(window.location.href);
    cleanUrl.searchParams.delete("api");
    window.history.replaceState(null, "", cleanUrl.pathname + cleanUrl.search);
  }
}
const getApiBaseUrl = (): string => {
  if (typeof window !== "undefined") {
    const override = localStorage.getItem("UPHILL_API_URL_OVERRIDE");
    if (override) return override;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
};
const API_BASE_URL = getApiBaseUrl();
if (typeof window !== "undefined") {
  const originalFetch = window.fetch;
  window.fetch = async (input, init) => {
    let url =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.toString()
          : input.url;
    if (url.startsWith(API_BASE_URL)) {
      const apiBase =
        localStorage.getItem("UPHILL_API_URL_OVERRIDE") ||
        process.env.NEXT_PUBLIC_API_URL ||
        API_BASE_URL;
      url = url.replace(API_BASE_URL, apiBase);
    }
    return originalFetch(url, init);
  };
}
interface Message {
  role: "user" | "assistant";
  content: string;
}
interface ParsedSummary {
  distance_km: number;
  duration_mins: number;
  elevation_gain_m: number;
  avg_hr?: number;
  avg_speed?: string;
  source_type: "FIT" | "GPX" | null;
}
interface RagSource {
  id: number;
  title: string;
  type: "pdf" | "url" | "youtube";
  url_path?: string;
  summary?: string;
  created_at: string;
}
interface Workout {
  id: number;
  plan_id: number;
  week_number: number;
  day_of_week: string;
  phase: string;
  title: string;
  type: string;
  duration_minutes: number;
  distance_km?: number;
  target_zone: string;
  target_hr_range?: string;
  target_pace?: string;
  treadmill_incline: number | string;
  treadmill_speed: number | string;
  description?: string;
  fueling_tip?: string;
  is_completed: number;
}
interface ActivePlan {
  id: number;
  race_name: string;
  race_date: string;
  goal_type: string;
  target_time_hours?: number;
  total_weeks: number;
  course_distance_km?: number;
  course_elevation_gain_m?: number;
}
interface PacedCheckpoint {
  name: string;
  distance_km: number;
  elevation_m: number;
  target_pace: string;
  split_time: string;
  cumulative_time_mins: number;
  flat_equivalent_km: number;
  grade_pct: number;
}
interface FuelStrategy {
  targets: {
    carbs_grams_per_hour: number;
    sodium_mg_per_hour: number;
    fluid_ml_per_hour: number;
    carb_complexity: string;
  };
  recommended_hourly_recipe: Array<{
    product: string;
    qty: number;
    type: string;
  }>;
  recipe_totals: {
    carbs_grams: number;
    sodium_mg: number;
    caffeine_mg: number;
    fluid_ml: number;
  };
  warnings: string[];
}
interface Shoe {
  id: number;
  brand: string;
  model: string;
  surface: string;
  cushioning: string;
  drop_mm: number;
  plate: string;
  width: string;
  review_summary: string;
}
// Simple Markdown Parser to format Assistant messages
const parseMarkdown = (text: string) => {
  if (!text) return null;
  const lines = text.split("\n");
  return lines.map((line, lineIdx) => {
    const trimmed = line.trim();
    if (trimmed.startsWith("### ")) {
      return (
        <h4
          key={lineIdx}
          style={{
            fontSize: "15px",
            fontWeight: "700",
            marginTop: "12px",
            marginBottom: "6px",
            color: "var(--accent-secondary)",
          }}
        >
          {parseInlineStyles(trimmed.substring(4))}
        </h4>
      );
    }
    if (trimmed.startsWith("## ")) {
      return (
        <h3
          key={lineIdx}
          style={{
            fontSize: "16px",
            fontWeight: "700",
            marginTop: "16px",
            marginBottom: "8px",
            color: "var(--accent-secondary)",
          }}
        >
          {parseInlineStyles(trimmed.substring(3))}
        </h3>
      );
    }
    if (trimmed.startsWith("# ")) {
      return (
        <h2
          key={lineIdx}
          style={{
            fontSize: "18px",
            fontWeight: "700",
            marginTop: "20px",
            marginBottom: "10px",
            color: "var(--accent-secondary)",
          }}
        >
          {parseInlineStyles(trimmed.substring(2))}
        </h2>
      );
    }
    const isBullet =
      trimmed.startsWith("* ") ||
      trimmed.startsWith("- ") ||
      trimmed.startsWith("• ");
    if (isBullet) {
      return (
        <li
          key={lineIdx}
          style={{
            marginLeft: "16px",
            marginBottom: "4px",
            listStyleType: "disc",
          }}
        >
          {parseInlineStyles(trimmed.substring(2))}
        </li>
      );
    }
    const numMatch = trimmed.match(/^(\d+)\.\s(.*)/);
    if (numMatch) {
      return (
        <li
          key={lineIdx}
          style={{
            marginLeft: "16px",
            marginBottom: "4px",
            listStyleType: "decimal",
          }}
        >
          {parseInlineStyles(numMatch[2])}
        </li>
      );
    }
    if (trimmed === "") {
      return <div key={lineIdx} style={{ height: "8px" }} />;
    }
    return (
      <p key={lineIdx} style={{ marginBottom: "6px", lineHeight: "1.4" }}>
        {parseInlineStyles(line)}
      </p>
    );
  });
};
const parseInlineStyles = (text: string): React.ReactNode[] => {
  const parts = text.split("**");
  return parts.map((part, index) => {
    if (index % 2 === 1) {
      return (
        <strong
          key={index}
          style={{ fontWeight: "700", color: "var(--text-bright)" }}
        >
          {part}
        </strong>
      );
    }
    return part;
  });
};
const topicColors: Record<string, string> = {
  Training: "#3b82f6",
  Nutrition: "#10b981",
  Recovery: "#8b5cf6",
  Pacing: "#f59e0b",
  Mindset: "#ec4899",
  Gear: "#14b8a6",
};
const topicIcons: Record<string, React.ReactNode> = {
  Training: <Mountains weight="fill" />,
  Nutrition: <BowlFood weight="fill" />,
  Recovery: <Bed weight="fill" />,
  Pacing: <Timer weight="fill" />,
  Mindset: <Brain weight="fill" />,
  Gear: <Backpack weight="fill" />,
};
const KnowledgeCard = ({
  card,
  expanded = false,
}: {
  card: any;
  expanded?: boolean;
}) => {
  const [open, setOpen] = useState(expanded);
  const { trackEvent } = useAnalytics();
  const color = topicColors[card.topic] || "#6366f1";
  const icon = topicIcons[card.topic] || <Book weight="fill" />;
  const handleToggle = () => {
    if (!open) {
      trackEvent("knowledge_card_clicked", {
        topic: card.topic,
        chapter_title: card.chapter_title,
      });
    }
    setOpen(!open);
  };
  return (
    <div
      style={{
        background: "var(--bg-card)",
        border: `1px solid var(--border-color)`,
        borderRadius: "14px",
        padding: "16px",
        cursor: "pointer",
        transition: "all 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
        backdropFilter: "blur(8px)",
        boxShadow: "inset 0 1px 0 rgba(255,255,255,0.05)",
      }}
      onClick={handleToggle}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "var(--bg-card-hover)";
        e.currentTarget.style.transform = "translateY(-1px)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "var(--bg-card)";
        e.currentTarget.style.transform = "translateY(0)";
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: "8px",
          marginBottom: "8px",
        }}
      >
        <span
          style={{
            display: "flex",
            alignItems: "center",
            gap: "4px",
            fontSize: "10px",
            fontWeight: "700",
            padding: "4px 8px",
            borderRadius: "20px",
            background: `${color}22`,
            color: color,
            letterSpacing: "0.5px",
            flexShrink: 0,
          }}
        >
          {icon} {card.topic?.toUpperCase()}
        </span>
        <span
          style={{
            fontSize: "14px",
            color: "var(--text-muted)",
            flexShrink: 0,
          }}
        >
          {open ? <CaretUp weight="bold" /> : <CaretDown weight="bold" />}
        </span>
      </div>
      <div
        style={{
          fontWeight: "700",
          fontSize: "14px",
          color: "var(--text-bright)",
          marginBottom: "8px",
          lineHeight: "1.4",
        }}
      >
        {card.chapter_title}
      </div>
      <p
        style={{
          fontSize: "13px",
          color: "var(--text-secondary)",
          lineHeight: "1.6",
          margin: 0,
        }}
      >
        {card.summary}
      </p>
      {open && card.key_points?.length > 0 && (
        <ul
          style={{
            marginTop: "12px",
            paddingLeft: "16px",
            display: "flex",
            flexDirection: "column",
            gap: "6px",
          }}
        >
          {card.key_points.map((pt: string, i: number) => (
            <li
              key={i}
              style={{
                fontSize: "12.5px",
                color: "var(--text-secondary)",
                lineHeight: "1.5",
              }}
            >
              {pt}
            </li>
          ))}
        </ul>
      )}
      {open && card.tags?.length > 0 && (
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "4px",
            marginTop: "10px",
          }}
        >
          {card.tags.map((tag: string, i: number) => (
            <span
              key={i}
              style={{
                fontSize: "10px",
                padding: "2px 6px",
                borderRadius: "10px",
                background: "rgba(255,255,255,0.1)",
                color: "var(--text-muted)",
              }}
            >
              #{tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
export default function Home() {
  const { trackEvent } = useAnalytics();
  // Navigation active tab
  const {
    isNutritionLabOpen,
    isGearVaultOpen,
    isPaceStrategyOpen,
    activeTab,
    lang,
    setIsNutritionLabOpen,
    setIsGearVaultOpen,
    setIsPaceStrategyOpen,
    setActiveTab,
    setLang,
    startBtnHovered,
    viewportWidth,
    selectedDeviceView,
    viewMode,
    setStartBtnHovered,
    setViewportWidth,
    setSelectedDeviceView,
    setViewMode,
    heroInput,
    backendConnected,
    chatMessages,
    chatInput,
    setHeroInput,
    setBackendConnected,
    setChatMessages,
    setChatInput,
    chatLoading,
    parsedSummary,
    parserLoading,
    uploadedFileName,
    setChatLoading,
    setParsedSummary,
    setParserLoading,
    setUploadedFileName,
    parserErrorMsg,
    gpxCheckpoints,
    sources,
    linkInput,
    setParserErrorMsg,
    setGpxCheckpoints,
    setSources,
    setLinkInput,
    ragLoading,
    ragErrorMsg,
    knowledgeCards,
    dailyCards,
    setRagLoading,
    setRagErrorMsg,
    setKnowledgeCards,
    setDailyCards,
    knowledgeTopics,
    knowledgeTopic,
    extractStatus,
    planJobId,
    setKnowledgeTopics,
    setKnowledgeTopic,
    setExtractStatus,
    setPlanJobId,
    planJobStatus,
    planJobMessage,
    activePlan,
    backupActivePlan,
    setPlanJobStatus,
    setPlanJobMessage,
    setActivePlan,
    setBackupActivePlan,
    backupWorkouts,
    recentPlans,
    workouts,
    selectedWeek,
    setBackupWorkouts,
    setRecentPlans,
    setWorkouts,
    setSelectedWeek,
    exportTimePref,
    showExportOptions,
    planForm,
    targetTimeH,
    setExportTimePref,
    setShowExportOptions,
    setPlanForm,
    setTargetTimeH,
    targetTimeM,
    targetTimeS,
    cutoffTimeH,
    cutoffTimeM,
    setTargetTimeM,
    setTargetTimeS,
    setCutoffTimeH,
    setCutoffTimeM,
    cutoffTimeS,
    planLoading,
    planErrorMsg,
    courseInputMode,
    setCutoffTimeS,
    setPlanLoading,
    setPlanErrorMsg,
    setCourseInputMode,
    plannerGpxFile,
    plannerGpxLoading,
    plannerGpxError,
    swapDay1,
    setPlannerGpxFile,
    setPlannerGpxLoading,
    setPlannerGpxError,
    setSwapDay1,
    swapDay2,
    targetFlatPace,
    pacedCheckpoints,
    pacingLoading,
    setSwapDay2,
    setTargetFlatPace,
    setPacedCheckpoints,
    setPacingLoading,
    fuelDuration,
    fuelSweatRate,
    fuelTemp,
    fuelStrategy,
    setFuelDuration,
    setFuelSweatRate,
    setFuelTemp,
    setFuelStrategy,
    fuelLoading,
    shoeSurface,
    shoeCushion,
    shoeWidth,
    setFuelLoading,
    setShoeSurface,
    setShoeCushion,
    setShoeWidth,
    recommendedShoes,
    shoesLoading,
    user,
    authModalOpen,
    setRecommendedShoes,
    setShoesLoading,
    setUser,
    setAuthModalOpen,
    mockEmailInput,
    authLoading,
    authErrorMsg,
    showApiKey,
    setMockEmailInput,
    setAuthLoading,
    setAuthErrorMsg,
    setShowApiKey,
    onboardingOpen,
    profileSettingsOpen,
    passwordFormOpen,
    newPassword,
    setOnboardingOpen,
    setProfileSettingsOpen,
    setPasswordFormOpen,
    setNewPassword,
    confirmNewPassword,
    passwordMsg,
    passwordError,
    authTab,
    setConfirmNewPassword,
    setPasswordMsg,
    setPasswordError,
    setAuthTab,
    emailInput,
    passwordInput,
    nameInput,
    confirmPasswordInput,
    setEmailInput,
    setPasswordInput,
    setNameInput,
    setConfirmPasswordInput,
    showPassword,
    onboardingStep,
    onboardingAnswers,
    onboardingGenerating,
    setShowPassword,
    setOnboardingStep,
    setOnboardingAnswers,
    setOnboardingGenerating,
    profileForm,
    onboardingMode,
    raceDistance,
    raceTimeHours,
    setProfileForm,
    setOnboardingMode,
    setRaceDistance,
    setRaceTimeHours,
    raceTimeMinutes,
    easyPaceMin,
    easyPaceSec,
    zone2Min,
    setRaceTimeMinutes,
    setEasyPaceMin,
    setEasyPaceSec,
    setZone2Min,
    zone2Max,
    setZone2Max,
  } = useAppContext();
  const handleTabSwitch = (
    tab: "home" | "about" | "chat" | "planner" | "tools" | "knowledge",
  ) => {
    if ((tab === "chat" || tab === "planner") && !user) {
      setAuthModalOpen(true);
      return;
    }
    setActiveTab(tab);
    if (tab === "planner") {
      setPlanJobStatus("idle");
    }
  };
  // Language State & Persistence
  // State for homepage CTA button hover effect
  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedLang = window.localStorage.getItem("uphill_lang");
      if (storedLang === "vi" || storedLang === "en") {
        setLang(storedLang);
      }
    }
  }, []);
  const handleSetLang = (newLang: "en" | "vi") => {
    setLang(newLang);
    if (typeof window !== "undefined") {
      window.localStorage.setItem("uphill_lang", newLang);
    }
  };
  const t = (key: keyof typeof translations.en) => {
    return translations[lang]?.[key] || translations.en[key] || key;
  };
  // Showcase state
  const isDesktopMode = viewMode === "desktop";
  const isMobileMode = viewMode === "mobile";
  const isShowcaseMode = viewMode === "showcase";
  const isViewportMobile = viewportWidth <= 900;
  // Video background refs — dual-video crossfade engine
  const videoARef = useRef<HTMLVideoElement>(null);
  const videoBRef = useRef<HTMLVideoElement>(null);
  const activeVideoRef = useRef<"A" | "B">("A");
  const crossfadeRafARef = useRef<number | null>(null);
  const crossfadeRafBRef = useRef<number | null>(null);
  const crossfadingRef = useRef(false);
  // Hero search state
  useEffect(() => {
    if (typeof window !== "undefined") {
      setViewportWidth(window.innerWidth);
      const handleResize = () => setViewportWidth(window.innerWidth);
      window.addEventListener("resize", handleResize);
      const params = new URLSearchParams(window.location.search);
      const mode = params.get("mode");
      if (mode === "desktop" || mode === "mobile" || mode === "showcase") {
        setViewMode(mode as any);
      }
      return () => window.removeEventListener("resize", handleResize);
    }
  }, []);
  // ─── Dual-Video Seamless Crossfade Engine ──────────────────────────────────
  // Uses two stacked <video> elements that crossfade at the loop point.
  // This eliminates the black-screen gap that appears with a single video reset.
  useEffect(() => {
    const vidA = videoARef.current;
    const vidB = videoBRef.current;
    if (!vidA || !vidB) return;
    const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";
    const SRC = basePath + "/bg.mp4";
    const FADE_MS = 250;
    const FADE_THRESHOLD = 0.55; // seconds before end — begin crossfade
    vidA.src = SRC;
    vidB.src = SRC;
    vidA.muted = true;
    vidB.muted = true;
    /** Linear opacity fade via RAF. Returns cancel fn. */
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
      // Pre-position the incoming video and start playing it silently at opacity 0
      inVid.currentTime = 0;
      inVid.style.opacity = "0";
      inVid.style.zIndex = "2";
      outVid.style.zIndex = "1";
      inVid.play().catch(() => {});
      // Crossfade: out fades to 0, in fades to 1
      animateFade(outVid, outRaf, 1, 0, () => {
        outVid.pause();
        crossfadingRef.current = false;
        activeVideoRef.current = activeVideoRef.current === "A" ? "B" : "A";
      });
      animateFade(inVid, inRaf, 0, 1);
    };
    const handleTimeUpdateA = () => {
      if (!vidA.duration || activeVideoRef.current !== "A") return;
      if (vidA.duration - vidA.currentTime <= FADE_THRESHOLD)
        triggerCrossfade();
    };
    const handleTimeUpdateB = () => {
      if (!vidB.duration || activeVideoRef.current !== "B") return;
      if (vidB.duration - vidB.currentTime <= FADE_THRESHOLD)
        triggerCrossfade();
    };
    // Initial startup: fade vidA in
    vidA.style.opacity = "0";
    vidB.style.opacity = "0";
    vidA.style.zIndex = "2";
    vidB.style.zIndex = "1";
    const startUp = () => {
      vidA.play().catch(() => {});
      animateFade(vidA, crossfadeRafARef, 0, 1);
    };
    if (vidA.readyState >= 3) {
      startUp();
    } else {
      vidA.addEventListener("canplay", startUp, { once: true });
    }
    vidA.addEventListener("timeupdate", handleTimeUpdateA);
    vidB.addEventListener("timeupdate", handleTimeUpdateB);
    return () => {
      vidA.removeEventListener("timeupdate", handleTimeUpdateA);
      vidB.removeEventListener("timeupdate", handleTimeUpdateB);
      if (crossfadeRafARef.current)
        cancelAnimationFrame(crossfadeRafARef.current);
      if (crossfadeRafBRef.current)
        cancelAnimationFrame(crossfadeRafBRef.current);
    };
  }, []);
  // Knowledge Hub: auto-load and auto-extract when tab opens
  useEffect(() => {
    if (activeTab !== "knowledge" && activeTab !== "home") {
      // Stop polling when leaving the tab
      if (knowledgePollerRef.current) {
        clearInterval(knowledgePollerRef.current);
        knowledgePollerRef.current = null;
      }
      return;
    }
    const token = localStorage.getItem("uphill_session_token");
    if (!token) return;
    const headers = { Authorization: `Bearer ${token}` };
    const loadCards = async (topic?: string) => {
      try {
        const url =
          topic && topic !== "All"
            ? `${API_BASE_URL}/api/knowledge/cards?topic=${encodeURIComponent(topic)}&lang=${lang}`
            : `${API_BASE_URL}/api/knowledge/cards?lang=${lang}`;
        const [cardsRes, dailyRes, topicsRes] = await Promise.all([
          fetch(url, { headers }),
          fetch(`${API_BASE_URL}/api/knowledge/cards/random?n=3&lang=${lang}`, {
            headers,
          }),
          fetch(`${API_BASE_URL}/api/knowledge/topics`, { headers }),
        ]);
        if (cardsRes.ok) {
          const d = await cardsRes.json();
          setKnowledgeCards(d.cards || []);
        }
        if (dailyRes.ok) {
          const d = await dailyRes.json();
          setDailyCards(d.cards || []);
        }
        if (topicsRes.ok) {
          const d = await topicsRes.json();
          setKnowledgeTopics(d.topics || []);
        }
      } catch (e) {
        console.error("Knowledge load error", e);
      }
    };
    const checkStatus = async () => {
      try {
        const res = await fetch(
          `${API_BASE_URL}/api/knowledge/extract/status`,
          { headers },
        );
        if (res.ok) {
          const s = await res.json();
          setExtractStatus(s);
          if (s.status === "done" && (s.card_count || 0) > 0) {
            // Done — load cards and stop polling
            await loadCards();
            if (knowledgePollerRef.current) {
              clearInterval(knowledgePollerRef.current);
              knowledgePollerRef.current = null;
            }
          }
        }
      } catch (e) {}
    };
    const init = async () => {
      await loadCards();
      if (activeTab === "knowledge") {
        // Check if we need to auto-trigger extraction
        const statusRes = await fetch(
          `${API_BASE_URL}/api/knowledge/extract/status`,
          { headers },
        );
        if (statusRes.ok) {
          const s = await statusRes.json();
          setExtractStatus(s);
          if ((s.card_count || 0) === 0 && s.status !== "extracting") {
            // Auto-trigger background extraction
            await fetch(`${API_BASE_URL}/api/knowledge/trigger`, {
              method: "POST",
              headers,
            });
            setExtractStatus((prev: any) => ({
              ...prev,
              status: "extracting",
            }));
          }
          if (s.status === "extracting" && !knowledgePollerRef.current) {
            knowledgePollerRef.current = setInterval(checkStatus, 4000);
          }
        }
      }
    };
    init();
    return () => {
      if (knowledgePollerRef.current) {
        clearInterval(knowledgePollerRef.current);
        knowledgePollerRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, lang]);
  const shuffleDailyCards = async () => {
    const token = localStorage.getItem("uphill_session_token");
    if (!token) return;
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/knowledge/cards/random?n=3&lang=${lang}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      if (res.ok) {
        const d = await res.json();
        setDailyCards(d.cards || []);
      }
    } catch (e) {}
  };
  const filterKnowledgeByTopic = async (topic: string) => {
    setKnowledgeTopic(topic);
    const token = localStorage.getItem("uphill_session_token");
    if (!token) return;
    try {
      const url =
        topic !== "All"
          ? `${API_BASE_URL}/api/knowledge/cards?topic=${encodeURIComponent(topic)}&lang=${lang}`
          : `${API_BASE_URL}/api/knowledge/cards?lang=${lang}`;
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const d = await res.json();
        setKnowledgeCards(d.cards || []);
      }
    } catch (e) {}
  };
  // Backend connection status
  // Chat sandbox state
  const chatBottomRef = useRef<HTMLDivElement>(null);
  // File parser sandbox state
  const fileInputRef = useRef<HTMLInputElement>(null);
  // RAG sandbox state
  const pdfInputRef = useRef<HTMLInputElement>(null);
  // Knowledge Hub state
  const knowledgePollerRef = useRef<ReturnType<typeof setInterval> | null>(
    null,
  );
  // Async plan generation job tracking
  const planJobPollerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  // Active Training Plan state
  // Target time fields (H/M/S)
  // Cutoff time fields (H/M/S) — for "Just to Finish" goal
  const plannerGpxInputRef = useRef<HTMLInputElement>(null);
  // Swap State
  // Phase 3 States
  // Pacing
  // Fueling
  // Shoes
  // User Auth State
  interface User {
    id: number;
    email: string;
    name: string;
    role: "admin" | "user";
    age?: number;
    current_weekly_km?: number;
    max_hr?: number;
    resting_hr?: number;
    aet_hr?: number;
    ant_hr?: number;
    gemini_api_key?: string;
    notebooklm_notebook_id?: string;
    notebooklm_auth_json?: string;
    zone2_pace_min?: string;
    zone2_pace_max?: string;
    provider?: string;
    has_password?: boolean;
  }
  // Onboarding / Profile Settings State
  // New auth modal state
  // Onboarding wizard state
  useEffect(() => {
    if (onboardingMode === "estimate") {
      const ageNum = parseInt(profileForm.age) || 30;
      const zone2MaxNum = parseInt(zone2Max) || 140;
      const maxHrEst = 220 - ageNum;
      const aetHrEst = zone2MaxNum;
      const antHrEst = Math.round(zone2MaxNum * 1.18);
      setProfileForm((prev: any) => {
        if (
          prev.max_hr === String(maxHrEst) &&
          prev.aet_hr === String(aetHrEst) &&
          prev.ant_hr === String(antHrEst)
        ) {
          return prev;
        }
        return {
          ...prev,
          max_hr: String(maxHrEst),
          aet_hr: String(aetHrEst),
          ant_hr: String(antHrEst),
        };
      });
    }
  }, [profileForm.age, onboardingMode, zone2Max]);
  // Load backend health, active session, and training plans on mount
  useEffect(() => {
    checkHealth();
    // Check local session storage
    const token = localStorage.getItem("uphill_session_token");
    if (token) {
      setAuthLoading(true);
      fetch(`${API_BASE_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((res) => {
          if (res.ok) return res.json();
          throw new Error("Session invalid");
        })
        .then((userData) => {
          setUser(userData);
          setProfileForm({
            age: String(userData.age ?? 30),
            current_weekly_km: String(userData.current_weekly_km ?? 30.0),
            max_hr: String(userData.max_hr ?? 185),
            resting_hr: String(userData.resting_hr ?? 60),
            aet_hr: String(userData.aet_hr ?? 135),
            ant_hr: String(userData.ant_hr ?? 165),
            gemini_api_key: userData.gemini_api_key ?? "",
            zone2_pace_min: userData.zone2_pace_min ?? "6:30",
            zone2_pace_max: userData.zone2_pace_max ?? "5:45",
          });
          fetchSourcesWithToken(userData, token);
          fetchActivePlanWithToken(token);
        })
        .catch(() => {
          localStorage.removeItem("uphill_session_token");
          setUser(null);
        })
        .finally(() => {
          setAuthLoading(false);
        });
    } else {
      // Lazy auth
    }
  }, []);
  // Listen to postMessage OAuth popup channels
  useEffect(() => {
    const handleOAuthMessage = (event: MessageEvent) => {
      if (event.data && event.data.provider && event.data.email) {
        handleMockLogin(event.data.email);
      }
    };
    window.addEventListener("message", handleOAuthMessage);
    return () => window.removeEventListener("message", handleOAuthMessage);
  }, []);
  // Initialize Google Sign-In when AuthModal is open
  useEffect(() => {
    if (!authModalOpen) return;
    let retryCount = 0;
    const initGoogleSignIn = () => {
      const g = (window as any).google;
      if (g && g.accounts && g.accounts.id) {
        const client_id =
          process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ||
          "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com";
        g.accounts.id.initialize({
          client_id: client_id,
          callback: (response: any) => {
            if (response && response.credential) {
              handleGoogleLogin(response.credential);
            }
          },
        });
        const btnContainer = document.getElementById("google-signin-btn");
        if (btnContainer) {
          g.accounts.id.renderButton(btnContainer, {
            theme: "outline",
            size: "large",
            width: btnContainer.clientWidth || 416,
            text: "continue_with",
            shape: "rectangular",
          });
        }
        // Optionally prompt Google One Tap
        g.accounts.id.prompt();
      } else if (retryCount < 20) {
        retryCount++;
        setTimeout(initGoogleSignIn, 200);
      }
    };
    setTimeout(initGoogleSignIn, 50);
  }, [authModalOpen]);
  const checkHealth = () => {
    fetch(`${API_BASE_URL}/api/health`)
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "healthy") {
          setBackendConnected(true);
        } else {
          setBackendConnected(false);
        }
      })
      .catch(() => {
        setBackendConnected(false);
      });
  };
  const fetchSourcesWithToken = async (
    currentUser: User | null,
    token: string,
  ) => {
    const activeUser = currentUser || user;
    if (!activeUser || activeUser.role !== "admin") {
      setSources([]);
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/sources`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setSources(data);
      }
    } catch (err) {
      console.error("Failed to load knowledge sources:", err);
    }
  };
  const fetchRecentPlansWithToken = async (token: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/coach/recent-plans`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setRecentPlans(data.plans || []);
      }
    } catch (err) {
      console.error("Failed to fetch recent plans:", err);
    }
  };
  const fetchActivePlanWithToken = async (token: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/coach/active-plan`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        if (data.active) {
          setActivePlan(data.plan);
          setWorkouts(data.workouts);
        } else {
          setActivePlan(null);
          setWorkouts([]);
        }
      }
      fetchRecentPlansWithToken(token);
    } catch (err) {
      console.error("Failed to fetch active plan:", err);
    }
  };
  const fetchSources = () => {
    const token = localStorage.getItem("uphill_session_token");
    if (token) fetchSourcesWithToken(user, token);
  };
  const fetchActivePlan = () => {
    const token = localStorage.getItem("uphill_session_token");
    if (token) {
      fetchActivePlanWithToken(token);
      fetchRecentPlansWithToken(token);
    }
  };
  // Scroll chat history to bottom
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);
  // Auth actions
  const handleMockLogin = async (emailToUse: string) => {
    setAuthLoading(true);
    setAuthErrorMsg("");
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/mock-login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: emailToUse }),
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Mock Login failed.");
      }
      const data = await response.json();
      localStorage.setItem("uphill_session_token", data.session_token);
      setUser(data.user);
      setProfileForm({
        age: String(data.user.age ?? 30),
        current_weekly_km: String(data.user.current_weekly_km ?? 30.0),
        max_hr: String(data.user.max_hr ?? 185),
        resting_hr: String(data.user.resting_hr ?? 60),
        aet_hr: String(data.user.aet_hr ?? 135),
        ant_hr: String(data.user.ant_hr ?? 165),
        gemini_api_key: data.user.gemini_api_key ?? "",
        zone2_pace_min: data.user.zone2_pace_min ?? "6:30",
        zone2_pace_max: data.user.zone2_pace_max ?? "5:45",
      });
      // Show onboarding wizard for new users
      if (!data.user.onboarding_complete) {
        setOnboardingOpen(true);
        setOnboardingStep(0);
      }
      setAuthModalOpen(false);
      fetchSourcesWithToken(data.user, data.session_token);
      fetchActivePlanWithToken(data.session_token);
    } catch (err: any) {
      setAuthErrorMsg(err.message || "Mock login failed");
    } finally {
      setAuthLoading(false);
    }
  };
  const handleGoogleLogin = async (idToken: string) => {
    setAuthLoading(true);
    setAuthErrorMsg("");
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/google`, {
        method: `POST`,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential: idToken }),
      });
      if (!response.ok) {
        const errData = await response.json();
        let errMsg = "Google Login failed.";
        if (typeof errData.detail === "string") {
          errMsg = errData.detail;
        } else if (Array.isArray(errData.detail)) {
          errMsg = errData.detail
            .map((e: any) => e.msg || JSON.stringify(e))
            .join(", ");
        } else if (errData.detail) {
          errMsg = JSON.stringify(errData.detail);
        }
        throw new Error(errMsg);
      }
      const data = await response.json();
      localStorage.setItem("uphill_session_token", data.session_token);
      setUser(data.user);
      setProfileForm({
        age: String(data.user.age ?? 30),
        current_weekly_km: String(data.user.current_weekly_km ?? 30.0),
        max_hr: String(data.user.max_hr ?? 185),
        resting_hr: String(data.user.resting_hr ?? 60),
        aet_hr: String(data.user.aet_hr ?? 135),
        ant_hr: String(data.user.ant_hr ?? 165),
        gemini_api_key: data.user.gemini_api_key ?? "",
        zone2_pace_min: data.user.zone2_pace_min ?? "6:30",
        zone2_pace_max: data.user.zone2_pace_max ?? "5:45",
      });
      if (!data.user.onboarding_complete) {
        setOnboardingOpen(true);
        setOnboardingStep(0);
      }
      setAuthModalOpen(false);
      fetchSourcesWithToken(data.user, data.session_token);
      fetchActivePlanWithToken(data.session_token);
    } catch (err: any) {
      setAuthErrorMsg(err.message || "Failed to sign in with Google.");
    } finally {
      setAuthLoading(false);
    }
  };
  const handleSaveProfile = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setAuthLoading(true);
    setAuthErrorMsg("");
    const token = localStorage.getItem("uphill_session_token");
    if (!token) return;
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/update-profile`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          age: parseInt(profileForm.age),
          current_weekly_km: parseFloat(profileForm.current_weekly_km),
          max_hr: parseInt(profileForm.max_hr),
          resting_hr: parseInt(profileForm.resting_hr),
          aet_hr: parseInt(profileForm.aet_hr),
          ant_hr: parseInt(profileForm.ant_hr),
          gemini_api_key: profileForm.gemini_api_key,
          zone2_pace_min: profileForm.zone2_pace_min,
          zone2_pace_max: profileForm.zone2_pace_max,
        }),
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Profile update failed.");
      }
      const updatedUser = await response.json();
      setUser(updatedUser);
      setAuthModalOpen(false);
      setOnboardingOpen(false);
    } catch (err: any) {
      setAuthErrorMsg(err.message || "Failed to save physiology settings.");
    } finally {
      setAuthLoading(false);
    }
  };
  const handleSetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMsg("");
    setPasswordError("");
    if (newPassword.length < 8) {
      setPasswordError("Password must be at least 8 characters.");
      return;
    }
    if (newPassword !== confirmNewPassword) {
      setPasswordError("Passwords do not match.");
      return;
    }
    const token = localStorage.getItem("uphill_session_token");
    if (!token) return;
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/set-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ password: newPassword }),
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Failed to set password.");
      }
      setPasswordMsg("Password set successfully!");
      setNewPassword("");
      setConfirmNewPassword("");
      setPasswordFormOpen(false);
      if (user) {
        setUser({ ...user, has_password: true });
      }
    } catch (err: any) {
      setPasswordError(err.message || "Failed to set password.");
    }
  };
  const handleOAuthLogin = (provider: "google" | "facebook") => {
    setAuthLoading(true);
    setAuthErrorMsg("");
    const width = 500;
    const height = 600;
    const left = window.screenX + (window.outerWidth - width) / 2;
    const top = window.screenY + (window.outerHeight - height) / 2;
    const popup = window.open(
      "",
      `${provider}-login`,
      `width=${width},height=${height},left=${left},top=${top},status=no,resizable=yes`,
    );
    if (popup) {
      popup.document.write(`
        <html>
          <head>
            <title>Authorize Uphill.AI</title>
            <style>
              body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: #0b0c10;
                color: #ffffff;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                padding: 20px;
                box-sizing: border-box;
                text-align: center;
              }
              .logo {
                font-size: 24px;
                font-weight: 800;
                margin-bottom: 20px;
                color: #c5f82a;
              }
              .card {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 30px;
                width: 100%;
                max-width: 380px;
              }
              h3 { margin-top: 0; font-size: 18px; }
              p { color: #8f929d; font-size: 13px; line-height: 1.5; margin-bottom: 24px; }
              .btn {
                display: block;
                width: 100%;
                padding: 12px;
                margin-bottom: 10px;
                border-radius: 6px;
                border: none;
                font-weight: 600;
                font-size: 13px;
                cursor: pointer;
                text-align: center;
                box-sizing: border-box;
              }
              .btn-primary { background: #c5f82a; color: #000; }
              .btn-secondary { background: rgba(255, 255, 255, 0.08); color: #fff; border: 1px solid rgba(255, 255, 255, 0.1); }
            </style>
          </head>
          <body>
            <div class="logo">Uphill.AI</div>
            <div class="card">
              <h3>Consent Request</h3>
              <p>Authorize Uphill.AI to access your profile name and email address via <strong>${provider === "google" ? "Google" : "Facebook"} OAuth</strong>.</p>
              <button class="btn btn-primary" onclick="login('admin')">🔐 Connect as Coach Admin</button>
              <button class="btn btn-secondary" onclick="login('user')"><PersonSimpleRun weight="bold" style={{marginRight: "6px", verticalAlign: "middle"}}/> Connect as Athlete User</button>
            </div>
            <script>
              function login(role) {
                const email = role === 'admin' ? 'admin@uphill.ai' : 'athlete@uphill.ai';
                window.opener.postMessage({ provider: '${provider}', email: email }, '*');
                window.close();
              }
            </script>
          </body>
        </html>
      `);
      popup.document.close();
    }
  };
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthErrorMsg("");
    if (passwordInput !== confirmPasswordInput) {
      setAuthErrorMsg("Passwords do not match.");
      setAuthLoading(false);
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: nameInput.trim(),
          email: emailInput.trim(),
          password: passwordInput,
        }),
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Registration failed.");
      }
      const data = await response.json();
      localStorage.setItem("uphill_session_token", data.session_token);
      setUser(data.user);
      setAuthModalOpen(false);
      setOnboardingOpen(true);
      setOnboardingStep(0);
      fetchSourcesWithToken(data.user, data.session_token);
      fetchActivePlanWithToken(data.session_token);
    } catch (err: any) {
      setAuthErrorMsg(err.message || "Registration failed.");
    } finally {
      setAuthLoading(false);
    }
  };
  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthErrorMsg("");
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: emailInput.trim(),
          password: passwordInput,
        }),
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Login failed.");
      }
      const data = await response.json();
      localStorage.setItem("uphill_session_token", data.session_token);
      setUser(data.user);
      setAuthModalOpen(false);
      if (!data.user.onboarding_complete) {
        setOnboardingOpen(true);
        setOnboardingStep(0);
      } else {
        fetchActivePlanWithToken(data.session_token);
      }
      fetchSourcesWithToken(data.user, data.session_token);
    } catch (err: any) {
      setAuthErrorMsg(err.message || "Login failed.");
    } finally {
      setAuthLoading(false);
    }
  };
  const startPlanJobPoller = (jobId: string, token: string) => {
    if (planJobPollerRef.current) clearInterval(planJobPollerRef.current);
    setPlanJobId(jobId);
    setPlanJobStatus("generating");
    setPlanJobMessage("");
    const poll = async () => {
      try {
        const res = await fetch(
          `${API_BASE_URL}/api/coach/plan-status/${jobId}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          },
        );
        if (!res.ok) {
          console.error("Plan status polling failed. HTTP Status:", res.status);
          return;
        }
        const data = await res.json();
        console.log("Plan job polling status update:", data);
        if (data.status === "done") {
          clearInterval(planJobPollerRef.current!);
          planJobPollerRef.current = null;
          setPlanJobStatus("done");
          // Re-fetch active plan and workouts from database to guarantee complete state synchronization
          await fetchActivePlanWithToken(token);
          setSelectedWeek(1);
          // Auto-dismiss banner after 10 seconds
          setTimeout(() => setPlanJobStatus("idle"), 10000);
        } else if (data.status === "error") {
          clearInterval(planJobPollerRef.current!);
          planJobPollerRef.current = null;
          setPlanJobStatus("error");
          setPlanJobMessage(data.error || "Plan generation failed.");
          setTimeout(() => setPlanJobStatus("idle"), 10000);
        }
      } catch (err) {
        console.error("Exception during plan job polling:", err);
      }
    };
    planJobPollerRef.current = setInterval(poll, 4000);
    // Poll immediately too
    poll();
  };
  const handleCompleteOnboarding = async () => {
    const token = localStorage.getItem("uphill_session_token");
    if (!token || !user) return;
    setOnboardingGenerating(true);
    try {
      // Calculate age from DOB if provided
      let age = 30;
      if (onboardingAnswers.dob) {
        const born = new Date(onboardingAnswers.dob);
        age = Math.floor(
          (Date.now() - born.getTime()) / (365.25 * 24 * 3600 * 1000),
        );
      }
      const payload: any = {
        dob: onboardingAnswers.dob || null,
        age,
        goal_type: onboardingAnswers.goal_type,
        injury_history: onboardingAnswers.injury_history || null,
        preferred_run_days: onboardingAnswers.preferred_run_days,
        long_run_day: onboardingAnswers.long_run_day || "Saturday",
        days_per_week: onboardingAnswers.days_per_week || 4,
        current_weekly_km:
          parseFloat(onboardingAnswers.current_weekly_km) || 30.0,
        has_gym_access: onboardingAnswers.has_gym_access || false,
        training_environment: onboardingAnswers.training_environment || "flat",
        double_session_days: onboardingAnswers.double_session_days || [],
        zone2_pace_min: onboardingAnswers.zone2_pace_min || "6:30",
        zone2_pace_max: onboardingAnswers.zone2_pace_max || "5:45",
        terrain: onboardingAnswers.terrain || "trail",
        time_away: onboardingAnswers.time_away || null,
        reason_for_break: onboardingAnswers.reason_for_break || null,
        fitness_feel: onboardingAnswers.fitness_feel || null,
        race_distance_completed:
          onboardingAnswers.race_distance_completed || null,
        days_since_race: onboardingAnswers.days_since_race
          ? parseInt(onboardingAnswers.days_since_race)
          : null,
        recovery_feel: onboardingAnswers.recovery_feel || null,
        next_goal: onboardingAnswers.next_goal || null,
        lang: lang,
      };
      // HR zones
      if (onboardingAnswers.aet_hr)
        payload.aet_hr = parseInt(onboardingAnswers.aet_hr);
      if (onboardingAnswers.ant_hr)
        payload.ant_hr = parseInt(onboardingAnswers.ant_hr);
      if (onboardingAnswers.max_hr)
        payload.max_hr = parseInt(onboardingAnswers.max_hr);
      if (onboardingAnswers.resting_hr)
        payload.resting_hr = parseInt(onboardingAnswers.resting_hr);
      // Race/distance targets
      if (onboardingAnswers.race_name)
        payload.race_name = onboardingAnswers.race_name;
      if (onboardingAnswers.race_date)
        payload.race_date = onboardingAnswers.race_date;
      if (onboardingAnswers.course_distance_km)
        payload.course_distance_km = parseFloat(
          onboardingAnswers.course_distance_km,
        );
      if (onboardingAnswers.course_elevation_gain_m)
        payload.course_elevation_gain_m = parseFloat(
          onboardingAnswers.course_elevation_gain_m,
        );
      if (onboardingAnswers.plan_start_date)
        payload.plan_start_date = onboardingAnswers.plan_start_date;
      // Race goals
      payload.race_goal = onboardingAnswers.race_goal || "finish";
      if (onboardingAnswers.race_goal === "time") {
        const hh = String(onboardingAnswers.expected_finish_hours || "0");
        const mm = String(onboardingAnswers.expected_finish_minutes || "0");
        payload.expected_finish_time = `${hh.padStart(2, "0")}:${mm.padStart(2, "0")}:00`;
      } else {
        payload.expected_finish_time = null;
      }
      const response = await fetch(`${API_BASE_URL}/api/auth/onboarding`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error("Failed to complete onboarding.");
      const data = await response.json();
      // Update user immediately so the app is accessible
      if (data.user) setUser(data.user);
      if (data.plan) setActivePlan(data.plan);
      // Close onboarding and let user into the app right away
      setOnboardingOpen(false);
      handleTabSwitch("home");
      // Start polling for plan generation in the background
      if (data.job_id) {
        startPlanJobPoller(data.job_id, token);
      }
    } catch (err: any) {
      setAuthErrorMsg(err.message || "Onboarding failed.");
    } finally {
      setOnboardingGenerating(false);
    }
  };
  const handleLogout = async () => {
    const token = localStorage.getItem("uphill_session_token");
    if (token) {
      try {
        await fetch(`${API_BASE_URL}/api/auth/logout`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch (err) {
        console.error("Logout request failed:", err);
      }
    }
    localStorage.removeItem("uphill_session_token");
    setUser(null);
    setActivePlan(null);
    setWorkouts([]);
    setSources([]);
    setAuthModalOpen(true);
  };
  // Send message to Coach Chat API
  const handleSendMessage = async (textToSend?: string) => {
    const messageText = textToSend || chatInput;
    if (!messageText.trim()) return;
    if (!textToSend) {
      setChatInput("");
    }
    const updatedMessages = [
      ...chatMessages,
      { role: "user" as const, content: messageText },
    ];
    setChatMessages(updatedMessages);
    setChatLoading(true);
    const token = localStorage.getItem("uphill_session_token");
    const headers: any = { "Content-Type": "application/json" };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/coach/chat`, {
        method: "POST",
        headers: headers,
        body: JSON.stringify({
          messages: updatedMessages,
          user_profile: {
            age: user?.age ?? 30,
            current_weekly_km: user?.current_weekly_km ?? 30.0,
            max_hr: user?.max_hr ?? 185,
            resting_hr: user?.resting_hr ?? 60,
            aet_hr: user?.aet_hr ?? 135,
            ant_hr: user?.ant_hr ?? 165,
            use_treadmill: activePlan?.use_treadmill === true,
            gemini_api_key: user?.gemini_api_key ?? "",
            zone2_pace_min: user?.zone2_pace_min ?? "6:30",
            zone2_pace_max: user?.zone2_pace_max ?? "5:45",
            recent_race: planForm.race_name,
          },
          context_data: activePlan
            ? {
                race_name: activePlan.race_name,
                race_date: activePlan.race_date,
                goal_type: activePlan.goal_type,
                total_weeks: activePlan.total_weeks,
                workouts: workouts,
              }
            : null,
        }),
      });
      if (!response.ok) {
        throw new Error("Failed to communicate with Coach API");
      }
      const replyData = await response.json();
      setChatMessages((prev: any) => [...prev, replyData]);
    } catch (err: any) {
      setChatMessages((prev: any) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Sorry, I had trouble reaching the coaching server. Please make sure the backend server is running.",
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };
  const sendPresetPrompt = (prompt: string) => {
    handleSendMessage(prompt);
  };
  // File Upload Handlers (FIT/GPX Telemetry)
  const handleDropzoneClick = () => {
    fileInputRef.current?.click();
  };
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await processFile(file);
  };
  const processFile = async (file: File) => {
    setParserLoading(true);
    setUploadedFileName(file.name);
    setParserErrorMsg("");
    setParsedSummary(null);
    setGpxCheckpoints([]);
    setPacedCheckpoints([]);
    const formData = new FormData();
    formData.append("file", file);
    const extension = file.name.split(".").pop()?.toLowerCase();
    let url = "";
    if (extension === "fit") {
      url = `${API_BASE_URL}/api/parser/fit`;
    } else if (extension === "gpx") {
      url = `${API_BASE_URL}/api/parser/gpx`;
    } else {
      setParserErrorMsg(
        "Unsupported file format. Please upload a .fit or .gpx file.",
      );
      setParserLoading(false);
      return;
    }
    try {
      const response = await fetch(url, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || "Parsing failed on server");
      }
      const result = await response.json();
      const sum = result.summary;
      if (extension === "fit") {
        const fitDist = parseFloat(
          ((sum.total_distance_meters || 0) / 1000).toFixed(2),
        );
        const fitElev = Math.round(sum.total_elevation_gain_meters || 0);
        setParsedSummary({
          distance_km: fitDist,
          duration_mins: parseFloat(
            ((sum.total_duration_seconds || 0) / 60).toFixed(1),
          ),
          elevation_gain_m: fitElev,
          avg_hr: sum.avg_heart_rate
            ? Math.round(sum.avg_heart_rate)
            : undefined,
          avg_speed: sum.avg_speed_mps
            ? `${(16.6667 / sum.avg_speed_mps).toFixed(2)} min/km`
            : undefined,
          source_type: "FIT",
        });
      } else {
        const gpxDist = parseFloat(
          ((sum.total_distance_meters || 0) / 1000).toFixed(2),
        );
        const gpxElev = Math.round(sum.total_elevation_gain_meters || 0);
        setParsedSummary({
          distance_km: gpxDist,
          duration_mins: 0,
          elevation_gain_m: gpxElev,
          source_type: "GPX",
        });
        setGpxCheckpoints(result.checkpoints);
      }
    } catch (err: any) {
      setParserErrorMsg(
        err.message || "An error occurred while uploading/parsing.",
      );
    } finally {
      setParserLoading(false);
    }
  };
  const handlePlannerGpxFileChange = async (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPlannerGpxLoading(true);
    setPlannerGpxError("");
    setPlannerGpxFile(null);
    const formData = new FormData();
    formData.append("file", file);
    const extension = file.name.split(".").pop()?.toLowerCase();
    if (extension !== "gpx") {
      setPlannerGpxError("Unsupported file format. Please upload a .gpx file.");
      setPlannerGpxLoading(false);
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/parser/gpx`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || "Parsing failed on server");
      }
      const result = await response.json();
      const sum = result.summary;
      const dist = parseFloat(
        ((sum.total_distance_meters || 0) / 1000).toFixed(2),
      );
      const elev = Math.round(sum.total_elevation_gain_meters || 0);
      setPlanForm({
        ...planForm,
        course_distance_km: dist.toString(),
        course_elevation_gain_m: elev.toString(),
      });
      setPlannerGpxFile(file);
    } catch (err: any) {
      setPlannerGpxError(
        err.message || "An error occurred while uploading/parsing.",
      );
    } finally {
      setPlannerGpxLoading(false);
    }
  };
  // RAG Link Ingestion
  const handleAddLink = async () => {
    if (!linkInput.trim()) return;
    setRagLoading(true);
    setRagErrorMsg("");
    const token = localStorage.getItem("uphill_session_token");
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/link`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ url: linkInput }),
      });
      if (!response.ok) {
        const errorText = await response.json();
        throw new Error(errorText.detail || "Link ingestion failed.");
      }
      setLinkInput("");
      await fetchSources();
    } catch (err: any) {
      setRagErrorMsg(err.message);
    } finally {
      setRagLoading(false);
    }
  };
  // RAG PDF File Ingestion
  const triggerPdfUpload = () => {
    pdfInputRef.current?.click();
  };
  const handlePdfFileChange = async (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setRagLoading(true);
    setRagErrorMsg("");
    const formData = new FormData();
    formData.append("file", file);
    const token = localStorage.getItem("uphill_session_token");
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });
      if (!response.ok) {
        const errorText = await response.json();
        throw new Error(errorText.detail || "PDF upload failed.");
      }
      await fetchSources();
    } catch (err: any) {
      setRagErrorMsg(err.message);
    } finally {
      setRagLoading(false);
    }
  };
  // Remove Grounding Source
  const handleDeleteSource = async (id: number) => {
    const token = localStorage.getItem("uphill_session_token");
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/sources/${id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.ok) {
        await fetchSources();
      }
    } catch (err) {
      console.error("Failed to delete source:", err);
    }
  };
  // Plan Generator Action
  const handleGeneratePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    const isRaceOrDistVal =
      planForm.plan_goal_category === "race" ||
      planForm.plan_goal_category === "distance";
    if (isRaceOrDistVal && (!planForm.race_name || !planForm.race_date)) {
      setPlanErrorMsg(
        "Race Name and Race Date are required for Race/Distance goals.",
      );
      return;
    }
    if (!isRaceOrDistVal && !planForm.plan_start_date) {
      setPlanErrorMsg("Please select a Plan Start Date.");
      return;
    }
    setPlanLoading(true);
    setPlanErrorMsg("");
    const token = localStorage.getItem("uphill_session_token");
    try {
      const isRaceOrDist =
        planForm.plan_goal_category === "race" ||
        planForm.plan_goal_category === "distance";
      // Build request body
      const body: Record<string, any> = {
        race_name: isRaceOrDist
          ? planForm.race_name
          : planForm.plan_goal_category.replace("_", " "),
        race_date: isRaceOrDist ? planForm.race_date : "",
        goal_type: isRaceOrDist
          ? planForm.goal_type
          : planForm.plan_goal_category,
        terrain: planForm.terrain,
        course_distance_km: planForm.course_distance_km
          ? parseFloat(planForm.course_distance_km)
          : null,
        course_elevation_gain_m: planForm.course_elevation_gain_m
          ? parseFloat(planForm.course_elevation_gain_m)
          : null,
        days_per_week: planForm.days_per_week,
        long_run_day: planForm.long_run_day,
        preferred_days: planForm.preferred_days,
        plan_start_date: planForm.plan_start_date || null,
        plan_duration_weeks: isRaceOrDist ? null : planForm.plan_duration_weeks,
        // non-race context fields
        time_away: planForm.time_away || null,
        fitness_feel: planForm.fitness_feel || null,
        race_distance_completed: planForm.race_distance_completed || null,
        days_since_race: planForm.days_since_race
          ? parseInt(planForm.days_since_race)
          : null,
        recovery_feel: planForm.recovery_feel || null,
        lang: lang,
      };
      // Combine H/M/S into decimal hours
      if (planForm.goal_type === "time") {
        const h = parseFloat(targetTimeH || "0");
        const m = parseFloat(targetTimeM || "0");
        const s = parseFloat(targetTimeS || "0");
        const total = h + m / 60 + s / 3600;
        if (total > 0) body.target_time_hours = total;
      } else if (planForm.goal_type === "finish") {
        const h = parseFloat(cutoffTimeH || "0");
        const m = parseFloat(cutoffTimeM || "0");
        const s = parseFloat(cutoffTimeS || "0");
        const total = h + m / 60 + s / 3600;
        if (total > 0) body.cutoff_time_hours = total;
      }
      const response = await fetch(`${API_BASE_URL}/api/coach/generate-plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const errorText = await response.json();
        throw new Error(errorText.detail || "Plan generation failed.");
      }
      const result = await response.json();
      trackEvent("plan_generated", {
        success: true,
        goal_type: body.goal_type,
        terrain: body.terrain,
        duration_weeks: body.plan_duration_weeks,
      });
      // Set plan immediately from the fast response
      if (result.plan) {
        setActivePlan(result.plan);
        setBackupActivePlan(null);
        setBackupWorkouts([]);
      }
      setSelectedWeek(1);
      // Start background polling for workouts
      if (result.job_id) {
        startPlanJobPoller(result.job_id, token!);
      } else {
        // Fallback: if somehow we got workouts synchronously
        if (result.workouts) setWorkouts(result.workouts);
        if (token) fetchRecentPlansWithToken(token);
      }
    } catch (err: any) {
      setPlanErrorMsg(err.message);
      trackEvent("plan_generated", { success: false, error: err.message });
    } finally {
      setPlanLoading(false);
    }
  };
  const getPlanDistance = (p: ActivePlan) => {
    if (p.course_distance_km !== undefined && p.course_distance_km !== null)
      return p.course_distance_km;
    if (p.race_name && p.race_name.toUpperCase().includes("SUM30")) return 30;
    return null;
  };
  const getPlanElevation = (p: ActivePlan) => {
    if (
      p.course_elevation_gain_m !== undefined &&
      p.course_elevation_gain_m !== null
    )
      return p.course_elevation_gain_m;
    if (p.race_name && p.race_name.toUpperCase().includes("SUM30")) return 1200;
    return null;
  };
  const formatPlanName = (p: ActivePlan) => {
    const dist = getPlanDistance(p);
    const elev = getPlanElevation(p);
    const kmStr = dist ? `${dist}km` : "0km";
    const gainStr = elev ? `+${elev}m` : "+0m";
    let targetStr = "Finish";
    let dateStr = p.race_date || "No Date";
    if (p.goal_type === "time" && p.target_time_hours) {
      targetStr = `${p.target_time_hours}h`;
    } else if (p.goal_type === "optimal") {
      targetStr = "Optimal";
    } else if (p.goal_type) {
      targetStr =
        p.goal_type.charAt(0).toUpperCase() +
        p.goal_type.slice(1).replace("_", " ");
    }
    if (["start_running", "return", "recovery"].includes(p.goal_type || "")) {
      dateStr = `Ends ${p.race_date}`;
      return `${p.race_name || "Untitled Plan"} (${dateStr}) | ${targetStr}`;
    } else {
      dateStr = `Race: ${p.race_date}`;
      return `${p.race_name || "Untitled Plan"} (${dateStr}) | ${kmStr} | +${elev || 0}m | ${targetStr}`;
    }
  };
  const handleSelectPlan = async (planId: number) => {
    const token = localStorage.getItem("uphill_session_token");
    if (!token) return;
    try {
      setPlanLoading(true);
      setPlanErrorMsg("");
      const response = await fetch(`${API_BASE_URL}/api/coach/select-plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ plan_id: planId }),
      });
      if (response.ok) {
        const data = await response.json();
        setActivePlan(data.plan);
        setWorkouts(data.workouts);
        setBackupActivePlan(null);
        setBackupWorkouts([]);
        setSelectedWeek(1);
        fetchRecentPlansWithToken(token);
      } else {
        const errorText = await response.json();
        setPlanErrorMsg(errorText.detail || "Failed to select plan.");
      }
    } catch (err: any) {
      setPlanErrorMsg(err.message);
    } finally {
      setPlanLoading(false);
    }
  };
  // Workout swap action
  const handleSwapWorkouts = async () => {
    if (!activePlan) return;
    const token = localStorage.getItem("uphill_session_token");
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/coach/modify-calendar`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            plan_id: activePlan.id,
            week_number: selectedWeek,
            day_1: swapDay1,
            day_2: swapDay2,
          }),
        },
      );
      if (response.ok) {
        const result = await response.json();
        setWorkouts(result.workouts);
      }
    } catch (err) {
      console.error("Failed to swap workouts:", err);
    }
  };
  // Mark workout complete (locally)
  const handleToggleComplete = async (woId: number, isCompleted: boolean) => {
    setWorkouts((prev: any) =>
      prev.map((wo: any) =>
        wo.id === woId ? { ...wo, is_completed: isCompleted ? 1 : 0 } : wo,
      ),
    );
  };
  const getWeekWorkouts = (weekNum: number) => {
    return workouts.filter((w: any) => w.week_number === weekNum);
  };
  const getWorkoutDate = (wo: Workout) => {
    if (!activePlan || !activePlan.race_date) return "";
    try {
      const parts = activePlan.race_date.split("-");
      if (parts.length !== 3) return "";
      const year = parseInt(parts[0], 10);
      const month = parseInt(parts[1], 10) - 1;
      const day = parseInt(parts[2], 10);
      const raceDate = new Date(year, month, day);
      const raceWo = workouts.find((w: any) => {
        const title = w.title.toUpperCase();
        const type = w.type.toUpperCase();
        return title.includes("TARGET EVENT") || type === "RACE";
      });
      const raceWeek = raceWo ? raceWo.week_number : activePlan.total_weeks;
      const getMondayRelativeOffset = (jsDay: number) => {
        if (jsDay === 0) return 6; // Sunday
        return jsDay - 1; // Mon-Sat
      };
      const raceDayOffset = getMondayRelativeOffset(raceDate.getDay());
      const raceWeekMonday = new Date(raceDate);
      raceWeekMonday.setDate(raceDate.getDate() - raceDayOffset);
      const startMonday = new Date(raceWeekMonday);
      startMonday.setDate(raceWeekMonday.getDate() - (raceWeek - 1) * 7);
      const DAY_OFFSETS: Record<string, number> = {
        Monday: 0,
        Tuesday: 1,
        Wednesday: 2,
        Thursday: 3,
        Friday: 4,
        Saturday: 5,
        Sunday: 6,
      };
      const dayName = wo.day_of_week;
      const workoutDayOffset =
        DAY_OFFSETS[dayName] !== undefined ? DAY_OFFSETS[dayName] : 0;
      const workoutDate = new Date(startMonday);
      workoutDate.setDate(
        startMonday.getDate() + (wo.week_number - 1) * 7 + workoutDayOffset,
      );
      return workoutDate.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      });
    } catch (e) {
      console.error(e);
      return "";
    }
  };
  // --- Phase 3 Calculator Handlers ---
  // Tab Icon generator
  const getTabIcon = (tabName: string, active: boolean, size = 18) => {
    const color = active ? "var(--accent-primary)" : "var(--text-secondary)";
    const weight = active ? "fill" : "regular";
    switch (tabName) {
      case "home":
        return <House size={size} color={color} weight={weight} />;
      case "about":
        return <Mountains size={size} color={color} weight={weight} />;
      case "chat":
        return <Robot size={size} color={color} weight={weight} />;
      case "planner":
        return <CalendarBlank size={size} color={color} weight={weight} />;
      case "tools":
        return <Calculator size={size} color={color} weight={weight} />;
      case "knowledge":
        return <BookOpen size={size} color={color} weight={weight} />;
      default:
        return null;
    }
  };
  const renderActiveTab = (isMobile: boolean) => {
    switch (activeTab) {
      case "home":
        return <HomeTab isMobile={isMobile} />;
      case "about":
        return <AboutTab isMobile={isMobile} />;
      case "chat":
        return <ChatTab isMobile={isMobile} />;
      case "planner":
        return <PlannerView isMobile={isMobile} />;
      case "tools":
        return <ToolsView isMobile={isMobile} />;
      case "knowledge":
        return <KnowledgeView isMobile={isMobile} />;
      default:
        return <HomeTab isMobile={isMobile} />;
    }
  };
  const changeViewMode = (mode: "showcase" | "desktop" | "mobile") => {
    setViewMode(mode);
    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.set("mode", mode);
      window.history.pushState(null, "", url.pathname + url.search);
    }
  };
  // ─── Onboarding Wizard ────────────────────────────────────────────────────
  // ─── Profile Settings Modal ───────────────────────────────────────────────
  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        height: "100dvh",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* ── Video Background: Two stacked videos for seamless crossfade ── */}
      <div className="video-bg-container">
        {/* Video A */}
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
            transition: "none",
            willChange: "opacity",
            zIndex: 2,
            pointerEvents: "none",
          }}
        />
        {/* Video B */}
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
            transition: "none",
            willChange: "opacity",
            zIndex: 1,
            pointerEvents: "none",
          }}
        />
      </div>
      {/* ── Plan Generation Notification Banner ── */}
      {planJobStatus !== "idle" && (
        <div
          style={{
            position: "fixed",
            bottom: isViewportMobile ? "90px" : "24px",
            left: isViewportMobile ? "16px" : "24px",
            right: isViewportMobile ? "16px" : "auto",
            transform: "none",
            zIndex: 9999,
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "12px 20px",
            borderRadius: "16px",
            background:
              planJobStatus === "done"
                ? "rgba(34, 197, 94, 0.18)"
                : planJobStatus === "error"
                  ? "rgba(239, 68, 68, 0.18)"
                  : "rgba(99, 102, 241, 0.18)",
            backdropFilter: "blur(20px)",
            WebkitBackdropFilter: "blur(20px)",
            border: `1px solid ${planJobStatus === "done" ? "rgba(34,197,94,0.4)" : planJobStatus === "error" ? "rgba(239,68,68,0.4)" : "rgba(99,102,241,0.4)"}`,
            boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
            color: "#fff",
            fontSize: "14px",
            fontWeight: 600,
            whiteSpace: "nowrap",
            maxWidth: "90vw",
          }}
        >
          {planJobStatus === "generating" && (
            <>
              <span
                style={{
                  display: "inline-block",
                  width: "16px",
                  height: "16px",
                  border: "2px solid rgba(255,255,255,0.4)",
                  borderTopColor: "#a78bfa",
                  borderRadius: "50%",
                  animation: "spin 0.8s linear infinite",
                  flexShrink: 0,
                }}
              />
              <span>⚡ Generating your training plan…</span>
              <span style={{ fontSize: "12px", opacity: 0.7, fontWeight: 400 }}>
                This may take a few minutes
              </span>
            </>
          )}
          {planJobStatus === "done" && (
            <>
              <span style={{ fontSize: "20px" }}>✅</span>
              <span>Your training plan is ready!</span>
              <button
                onClick={() => handleTabSwitch("planner")}
                style={{
                  marginLeft: "8px",
                  padding: "4px 12px",
                  borderRadius: "8px",
                  background: "rgba(34,197,94,0.3)",
                  border: "1px solid rgba(34,197,94,0.5)",
                  color: "#fff",
                  fontSize: "12px",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                View Planner →
              </button>
              <button
                onClick={() => setPlanJobStatus("idle")}
                style={{
                  marginLeft: "4px",
                  background: "transparent",
                  border: "none",
                  color: "rgba(255,255,255,0.6)",
                  cursor: "pointer",
                  fontSize: "16px",
                  lineHeight: 1,
                }}
                aria-label="Dismiss"
              >
                ×
              </button>
            </>
          )}
          {planJobStatus === "error" && (
            <>
              <span style={{ fontSize: "20px" }}>
                <Warning weight="fill" />
              </span>
              <span>Plan generation failed.</span>
              {planJobMessage && (
                <span
                  style={{
                    fontSize: "12px",
                    opacity: 0.7,
                    fontWeight: 400,
                    maxWidth: "200px",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {planJobMessage}
                </span>
              )}
              <button
                onClick={() => setPlanJobStatus("idle")}
                style={{
                  marginLeft: "8px",
                  background: "transparent",
                  border: "none",
                  color: "rgba(255,255,255,0.6)",
                  cursor: "pointer",
                  fontSize: "16px",
                  lineHeight: 1,
                }}
                aria-label="Dismiss"
              >
                ×
              </button>
            </>
          )}
        </div>
      )}
      {viewMode === "desktop" ? (
        <div
          className="desktop-only-wrapper"
          style={{
            display: "flex",
            width: "100%",
            height: "100%",
            overflow: "hidden",
            position: "relative",
          }}
        >
          {/* Glow Effects */}
          <div className="glow-bg" style={{ opacity: 0.45 }}></div>
          <div className="glow-bg-left" style={{ opacity: 0.35 }}></div>
          {/* Left Navigation Sidebar */}
          <aside className="laptop-sidebar" style={{ height: "100%" }}>
            <div>
              <div className="laptop-sidebar-logo">
                Uphill<span>.AI</span>
              </div>
              <ul className="sidebar-nav-list">
                {(
                  [
                    "home",
                    "about",
                    "chat",
                    "planner",
                    "tools",
                    "knowledge",
                  ] as const
                ).map((tab) => {
                  const active = activeTab === tab;
                  return (
                    <li
                      key={tab}
                      onClick={() => handleTabSwitch(tab)}
                      className={`sidebar-nav-item ${active ? "sidebar-nav-item-active" : ""}`}
                    >
                      {getTabIcon(tab, active)}
                      <span>
                        {tab === "home"
                          ? t("tab_home")
                          : tab === "chat"
                            ? t("tab_chat")
                            : tab === "planner"
                              ? t("tab_scheduler")
                              : tab === "knowledge"
                                ? t("tab_knowledge")
                                : tab === "about"
                                  ? t("tab_about")
                                  : t("tab_tools")}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
            {/* Sidebar Profile trigger */}
            <div style={{ padding: "0 8px" }}>
              {user ? (
                <div
                  onClick={() => {
                    setProfileSettingsOpen(true);
                  }}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    cursor: "pointer",
                    padding: "8px",
                    borderRadius: "12px",
                    background: "rgba(255,255,255,0.2)",
                    border: "1px solid var(--border-color)",
                  }}
                >
                  <div
                    style={{
                      width: "32px",
                      height: "32px",
                      borderRadius: "50%",
                      background: "var(--accent-primary)",
                      color: "#fff",
                      display: "flex",
                      alignItems: "center",
                      justifyItems: "center",
                      justifyContent: "center",
                      fontWeight: "700",
                      fontSize: "14px",
                      flexShrink: 0,
                    }}
                  >
                    {user.name[0].toUpperCase()}
                  </div>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      overflow: "hidden",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "12px",
                        fontWeight: "700",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        maxWidth: "100px",
                      }}
                    >
                      {user.name}
                    </span>
                    <span
                      style={{
                        fontSize: "9.5px",
                        color: "var(--accent-primary)",
                        textDecoration: "underline",
                      }}
                    >
                      {lang === "en" ? "Settings" : "Cài đặt"}
                    </span>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setAuthModalOpen(true)}
                  className="btn btn-primary"
                  style={{
                    width: "100%",
                    height: "36px",
                    padding: "0",
                    fontSize: "12.5px",
                  }}
                >
                  {t("auth_sign_in")}
                </button>
              )}
            </div>
          </aside>
          {/* Main Content Area */}
          <main className="laptop-main-area" style={{ height: "100%" }}>
            {/* Mini-NavBar */}
            <nav className="laptop-nav-bar">
              <div
                style={{ display: "flex", alignItems: "center", gap: "8px" }}
              >
                <span
                  style={{
                    fontSize: "12.5px",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                    color: "var(--text-secondary)",
                    fontWeight: "600",
                  }}
                >
                  {lang === "en" ? "Dashboard" : "Bảng điều khiển"} /{" "}
                  <span style={{ color: "var(--accent-primary)" }}>
                    {activeTab === "home"
                      ? t("tab_home")
                      : activeTab === "chat"
                        ? t("tab_chat")
                        : activeTab === "planner"
                          ? t("tab_scheduler")
                          : activeTab === "knowledge"
                            ? t("tab_knowledge")
                            : activeTab === "about"
                              ? t("tab_about")
                              : t("tab_tools")}
                  </span>
                </span>
              </div>
              <div
                style={{ display: "flex", alignItems: "center", gap: "16px" }}
              >
                {/* Layout Switcher */}
                <div
                  style={{
                    display: "flex",
                    background: "rgba(255, 255, 255, 0.45)",
                    border: "1px solid var(--border-color)",
                    padding: "2px",
                    borderRadius: "8px",
                    gap: "2px",
                  }}
                >
                  <button
                    onClick={() => changeViewMode("showcase")}
                    style={{
                      padding: "4px 8px",
                      fontSize: "10px",
                      borderRadius: "6px",
                      border: "none",
                      background:
                        (viewMode as string) === "showcase"
                          ? "var(--accent-primary)"
                          : "transparent",
                      color:
                        (viewMode as string) === "showcase"
                          ? "#ffffff"
                          : "var(--text-secondary)",
                      cursor: "pointer",
                      fontWeight:
                        (viewMode as string) === "showcase" ? "600" : "500",
                      transition: "all 0.15s",
                    }}
                  >
                    {lang === "en" ? "Showcase" : "Giới thiệu"}
                  </button>
                  <button
                    onClick={() => changeViewMode("desktop")}
                    style={{
                      padding: "4px 8px",
                      fontSize: "10px",
                      borderRadius: "6px",
                      border: "none",
                      background:
                        (viewMode as string) === "desktop"
                          ? "var(--accent-primary)"
                          : "transparent",
                      color:
                        (viewMode as string) === "desktop"
                          ? "#ffffff"
                          : "var(--text-secondary)",
                      cursor: "pointer",
                      fontWeight:
                        (viewMode as string) === "desktop" ? "600" : "500",
                      transition: "all 0.15s",
                    }}
                  >
                    {lang === "en" ? "Desktop Only" : "Chỉ Máy tính"}
                  </button>
                  <button
                    onClick={() => changeViewMode("mobile")}
                    style={{
                      padding: "4px 8px",
                      fontSize: "10px",
                      borderRadius: "6px",
                      border: "none",
                      background:
                        (viewMode as string) === "mobile"
                          ? "var(--accent-primary)"
                          : "transparent",
                      color:
                        (viewMode as string) === "mobile"
                          ? "#ffffff"
                          : "var(--text-secondary)",
                      cursor: "pointer",
                      fontWeight:
                        (viewMode as string) === "mobile" ? "600" : "500",
                      transition: "all 0.15s",
                    }}
                  >
                    {lang === "en" ? "Mobile Only" : "Chỉ Di động"}
                  </button>
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    fontSize: "12px",
                    color: "var(--text-secondary)",
                  }}
                >
                  <span
                    className="coach-status-dot"
                    style={{
                      backgroundColor: backendConnected
                        ? "var(--accent-success)"
                        : "var(--accent-alert)",
                    }}
                  ></span>
                  {backendConnected ? "Live" : "Offline"}
                </div>
                {user && (
                  <button
                    onClick={handleLogout}
                    className="btn btn-secondary"
                    style={{
                      padding: "4px 10px",
                      fontSize: "11px",
                      height: "26px",
                      borderRadius: "6px",
                    }}
                  >
                    {t("logout")}
                  </button>
                )}
              </div>
            </nav>
            {/* Scrollable Dashboard View */}
            <div
              className="laptop-scrollable-content"
              style={{
                height: "calc(100% - 60px)",
                display: "flex",
                flexDirection: "column",
                overflow: activeTab === "chat" ? "hidden" : "auto",
                padding: activeTab === "chat" ? "0" : undefined,
              }}
            >
              {activeTab === "home" ? (
                renderActiveTab(false)
              ) : (
                <div
                  className={`content-panel ${activeTab === "chat" ? "chat-panel-active" : ""}`}
                  style={
                    activeTab === "chat"
                      ? { overflowY: "hidden", flex: 1, minHeight: 0 }
                      : { flex: 1, minHeight: 0 }
                  }
                >
                  <div
                    className="content-panel-inner"
                    style={{
                      width: "100%",
                      height: activeTab === "chat" ? undefined : "auto",
                      flex: activeTab === "chat" ? 1 : "1 0 auto",
                      minHeight: activeTab === "chat" ? 0 : "100%",
                      display: "flex",
                      flexDirection: "column",
                      maxWidth: activeTab === "chat" ? "680px" : undefined,
                    }}
                  >
                    {/* Panel header breadcrumb */}
                    <div className="panel-header">
                      <span
                        className="panel-header-icon"
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          color: "var(--text-primary)",
                        }}
                      >
                        {activeTab === "chat" ? (
                          <Robot size={28} weight="duotone" />
                        ) : activeTab === "planner" ? (
                          <CalendarBlank size={28} weight="duotone" />
                        ) : activeTab === "knowledge" ? (
                          <BookOpen size={28} weight="duotone" />
                        ) : activeTab === "tools" ? (
                          <Calculator size={28} weight="duotone" />
                        ) : (
                          <Mountains size={28} weight="duotone" />
                        )}
                      </span>
                      <div>
                        <h2>
                          {activeTab === "chat"
                            ? t("tab_chat")
                            : activeTab === "planner"
                              ? t("plan_setup")
                              : activeTab === "knowledge"
                                ? t("know_title")
                                : activeTab === "tools"
                                  ? t("tab_tools")
                                  : t("tab_about")}
                        </h2>
                        <p>
                          {activeTab === "chat"
                            ? t("header_chat_desc")
                            : activeTab === "planner"
                              ? t("header_planner_desc")
                              : activeTab === "knowledge"
                                ? t("header_knowledge_desc")
                                : activeTab === "tools"
                                  ? t("header_tools_desc")
                                  : t("header_about_desc")}
                        </p>
                      </div>
                    </div>
                    {/* Render actual tab content */}
                    {renderActiveTab(false)}
                  </div>
                </div>
              )}
            </div>
          </main>
        </div>
      ) : viewMode === "mobile" ? (
        <div
          className="mobile-only-wrapper"
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            height: "100dvh",
            width: "100%",
            position: "relative",
            overflow: "hidden",
          }}
        >
          {/* Glow Effects */}
          <div className="glow-bg" style={{ opacity: 0.45 }}></div>
          <div className="glow-bg-left" style={{ opacity: 0.35 }}></div>
          <div
            style={{
              width: "100%",
              maxWidth: "480px",
              height: "100%",
              background: "var(--bg-main)",
              display: "flex",
              flexDirection: "column",
              borderLeft: "1px solid var(--border-color)",
              borderRight: "1px solid var(--border-color)",
              position: "relative",
              boxShadow: "0 0 40px rgba(0,0,0,0.05)",
              overflow: "hidden",
            }}
          >
            {/* Phone Top Header */}
            <header
              className="phone-header-bar"
              style={{ padding: "12px 16px" }}
            >
              <a href="#" className="phone-logo" style={{ fontSize: "16px" }}>
                Uphill<span>.AI</span>
              </a>
              <div
                style={{ display: "flex", alignItems: "center", gap: "12px" }}
              >
                {/* Simple Mode Selector */}
                <select
                  value={viewMode}
                  onChange={(e) => changeViewMode(e.target.value as any)}
                  style={{
                    background: "transparent",
                    border: "1px solid var(--border-color)",
                    borderRadius: "6px",
                    fontSize: "10px",
                    padding: "2px 6px",
                    color: "var(--text-secondary)",
                    outline: "none",
                    cursor: "pointer",
                  }}
                >
                  <option value="showcase">
                    {lang === "en" ? "Showcase" : "Giới thiệu"}
                  </option>
                  <option value="desktop">
                    {lang === "en" ? "Desktop Only" : "Chỉ Máy tính"}
                  </option>
                  <option value="mobile">
                    {lang === "en" ? "Mobile Only" : "Chỉ Di động"}
                  </option>
                </select>
                <span
                  className="coach-status-dot"
                  style={{
                    width: "6px",
                    height: "6px",
                    backgroundColor: backendConnected
                      ? "var(--accent-success)"
                      : "var(--accent-alert)",
                  }}
                ></span>
                {user ? (
                  <span
                    onClick={() => {
                      setProfileSettingsOpen(true);
                    }}
                    style={{
                      fontSize: "11px",
                      fontWeight: "700",
                      color: "var(--accent-primary)",
                      cursor: "pointer",
                    }}
                  >
                    {lang === "en" ? "Profile" : "Hồ sơ"}
                  </span>
                ) : (
                  <span
                    onClick={() => setAuthModalOpen(true)}
                    style={{
                      fontSize: "11px",
                      fontWeight: "700",
                      color: "var(--accent-primary)",
                      cursor: "pointer",
                    }}
                  >
                    {t("auth_sign_in")}
                  </span>
                )}
              </div>
            </header>
            {/* Mobile Scrollable content */}
            <div
              className="phone-scrollable-content"
              style={{
                flex: 1,
                overflowY: activeTab === "chat" ? "hidden" : "auto",
                padding: activeTab === "chat" ? "0px" : "16px",
                paddingBottom: activeTab === "chat" ? "56px" : "76px",
                display: "flex",
                flexDirection: "column",
                minHeight: 0,
              }}
            >
              {renderActiveTab(true)}
            </div>
            {/* Persistent Bottom Tab Bar */}
            <nav className="phone-bottom-tab-bar">
              {(
                [
                  "home",
                  "about",
                  "chat",
                  "planner",
                  "tools",
                  "knowledge",
                ] as const
              ).map((tab) => {
                const active = activeTab === tab;
                const tabLabel =
                  tab === "home"
                    ? "Home"
                    : tab === "chat"
                      ? "Coach"
                      : tab === "planner"
                        ? "Planner"
                        : tab === "knowledge"
                          ? "Hub"
                          : tab === "tools"
                            ? "Calculators"
                            : "Philosophy";
                return (
                  <div
                    key={tab}
                    onClick={() => handleTabSwitch(tab)}
                    className={`tab-bar-item ${active ? "tab-bar-item-active" : ""}`}
                  >
                    {getTabIcon(tab, active, 16)}
                    <span
                      className="tab-bar-item-label"
                      style={{ textTransform: "none" }}
                    >
                      {tabLabel}
                    </span>
                  </div>
                );
              })}
            </nav>
          </div>
        </div>
      ) : (
        <div
          className="app-root"
          style={{
            position: "relative",
            zIndex: 10,
            display: "flex",
            flexDirection: "column",
            height: "100dvh",
            overflow: "hidden",
          }}
        >
          {/* ── Top Navigation ──────────────────────────────────── */}
          <nav className="top-nav" style={{ flexShrink: 0 }}>
            {/* Logo */}
            <a className="top-nav-logo" href="#">
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "2px",
                }}
              >
                <svg
                  width="28"
                  height="28"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  style={{ color: "var(--accent-success)" }}
                >
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                  <polyline points="17 6 23 6 23 12" />
                </svg>
                Uphill<span className="logo-accent">.AI</span>
              </span>
            </a>
            {/* Centre tab pills */}
            <div className="top-nav-tabs">
              {(
                [
                  "home",
                  "chat",
                  "planner",
                  "knowledge",
                  "tools",
                  "about",
                ] as const
              ).map((tab) => {
                const label =
                  tab === "home"
                    ? `${t("tab_home")}`
                    : tab === "chat"
                      ? `${t("tab_chat")}`
                      : tab === "planner"
                        ? `${t("tab_scheduler")}`
                        : tab === "knowledge"
                          ? `${t("tab_knowledge")}`
                          : tab === "about"
                            ? `${t("tab_about")}`
                            : `${t("tab_tools")}`;
                return (
                  <button
                    key={tab}
                    className={`top-nav-tab ${activeTab === tab ? "active" : ""}`}
                    onClick={() => handleTabSwitch(tab)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    {getTabIcon(tab, activeTab === tab, 18)}
                    {label}
                  </button>
                );
              })}
            </div>
            {/* Right — status + user */}
            <div className="top-nav-right">
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  fontSize: "12px",
                  color: "rgba(0,0,0,0.6)",
                }}
              >
                <span
                  className="coach-status-dot"
                  style={{
                    backgroundColor: backendConnected
                      ? "var(--accent-success)"
                      : "var(--accent-alert)",
                  }}
                />
                <span>{backendConnected ? "Live" : "Offline"}</span>
              </div>
              {user ? (
                <div
                  className="top-nav-avatar"
                  onClick={() => {
                    setProfileSettingsOpen(true);
                  }}
                  title={
                    lang === "en"
                      ? `${user.name} — click to open settings`
                      : `${user.name} — nhấn để mở cài đặt`
                  }
                  style={{
                    background:
                      "linear-gradient(135deg, var(--accent-success), #16a34a)",
                  }}
                >
                  {user.name[0].toUpperCase()}
                </div>
              ) : (
                <button
                  className="btn btn-primary"
                  onClick={() => setAuthModalOpen(true)}
                  style={{
                    padding: "8px 18px",
                    fontSize: "12.5px",
                    background: "var(--accent-success)",
                  }}
                >
                  {t("auth_sign_in")}
                </button>
              )}
            </div>
          </nav>
          {/* ── Main Content Body ───────────────────────────────── */}
          <div
            style={{
              flex: 1,
              overflow: "hidden",
              position: "relative",
              display: "flex",
              flexDirection: "column",
            }}
          >
            {/* ── HOME TAB: introductory hero view ────────────────── */}
            {activeTab === "home" && (
              <section
                className="hero-section"
                style={{
                  height: "100%",
                  overflowY: "auto",
                  justifyContent: "center",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  paddingTop: "40px",
                  paddingBottom: isViewportMobile ? "160px" : "40px",
                  marginTop: 0,
                }}
              >
                {renderActiveTab(isViewportMobile)}
              </section>
            )}
            {activeTab !== "home" && (
              <div
                className={`content-panel ${activeTab === "chat" ? "chat-panel-active" : ""}`}
                style={
                  activeTab === "chat"
                    ? { overflowY: "hidden", flex: 1, minHeight: 0 }
                    : { flex: 1, minHeight: 0 }
                }
              >
                <div
                  className="content-panel-inner"
                  style={{
                    width: "100%",
                    height: activeTab === "chat" ? undefined : "auto",
                    flex: activeTab === "chat" ? 1 : "1 0 auto",
                    minHeight: activeTab === "chat" ? 0 : "100%",
                    display: "flex",
                    flexDirection: "column",
                    maxWidth: activeTab === "chat" ? "680px" : undefined,
                    padding:
                      activeTab === "chat" && isViewportMobile
                        ? "0px"
                        : undefined,
                    paddingBottom:
                      activeTab === "chat" && isViewportMobile
                        ? "calc(80px + env(safe-area-inset-bottom))"
                        : undefined,
                  }}
                >
                  {renderActiveTab(isViewportMobile)}
                </div>
              </div>
            )}
          </div>
          {/* Mobile Bottom Navigation Tabs (visible only on mobile viewports via CSS) */}
          <div className="mobile-bottom-nav-tabs">
            {(
              [
                "home",
                "chat",
                "planner",
                "knowledge",
                "tools",
                "about",
              ] as const
            ).map((tab) => {
              const active = activeTab === tab;
              const tabLabel =
                tab === "home"
                  ? t("tab_home")
                  : tab === "chat"
                    ? t("tab_chat")
                    : tab === "planner"
                      ? t("tab_scheduler")
                      : tab === "knowledge"
                        ? t("tab_knowledge")
                        : tab === "tools"
                          ? t("tab_tools")
                          : t("tab_about");
              return (
                <button
                  key={tab}
                  className={`mobile-bottom-nav-tab ${active ? "active" : ""}`}
                  onClick={() => handleTabSwitch(tab)}
                >
                  <span className="mobile-bottom-nav-tab-icon">
                    {getTabIcon(tab, active, 20)}
                  </span>
                  <span className="mobile-bottom-nav-tab-label">
                    {tabLabel}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}
      {/* Global Modals */}
      <AuthModal />
      <OnboardingWizard />
      <ProfileSettingsModal />
      <NutritionLab
        isOpen={isNutritionLabOpen}
        onClose={() => setIsNutritionLabOpen(false)}
        lang={lang}
        user={user}
        activePlan={activePlan}
      />
      <GearVault
        isOpen={isGearVaultOpen}
        onClose={() => setIsGearVaultOpen(false)}
        lang={lang}
        user={user}
        activePlan={activePlan}
      />
      <PaceStrategy
        isOpen={isPaceStrategyOpen}
        onClose={() => setIsPaceStrategyOpen(false)}
        lang={lang}
        user={user}
        activePlan={activePlan}
      />
    </div>
  );
}
