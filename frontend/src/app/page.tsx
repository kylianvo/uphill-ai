"use client";

import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import Link from "next/link";
import WorkoutDescription from "@/components/WorkoutDescription";
import { NutritionLab } from "../components/NutritionLab";
import { GearVault } from "../components/GearVault";
import { translations } from "./translations";
import { 
  Plus, ArrowsLeftRight, Heartbeat, Clock, Calendar, Lightbulb, Sneaker, Plant, Code, Robot, CalendarBlank, BookOpen, Calculator, Mountains, PersonSimpleRun, Trash, Target, XCircle, Warning, Trophy, 
  Barbell, BowlFood, Bed, Timer, Brain, Backpack, CaretDown, CaretUp, Book, House
} from "@phosphor-icons/react";
if (typeof window !== "undefined") {
  // Check for api query parameter to override API URL
  const params = new URLSearchParams(window.location.search);
  const apiParam = params.get("api");
  if (apiParam) {
    let cleanParam = apiParam.trim();
    if ((cleanParam.startsWith('"') && cleanParam.endsWith('"')) || (cleanParam.startsWith("'") && cleanParam.endsWith("'"))) {
      cleanParam = cleanParam.slice(1, -1).trim();
    }
    if (cleanParam === "default" || cleanParam === "reset" || cleanParam === "clear") {
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
    let url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
    if (url.startsWith(API_BASE_URL)) {
      const apiBase = localStorage.getItem("UPHILL_API_URL_OVERRIDE") || process.env.NEXT_PUBLIC_API_URL || API_BASE_URL;
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
  treadmill_incline: number;
  treadmill_speed: number;
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
        <h4 key={lineIdx} style={{ fontSize: "15px", fontWeight: "700", marginTop: "12px", marginBottom: "6px", color: "var(--accent-secondary)" }}>
          {parseInlineStyles(trimmed.substring(4))}
        </h4>
      );
    }
    if (trimmed.startsWith("## ")) {
      return (
        <h3 key={lineIdx} style={{ fontSize: "16px", fontWeight: "700", marginTop: "16px", marginBottom: "8px", color: "var(--accent-secondary)" }}>
          {parseInlineStyles(trimmed.substring(3))}
        </h3>
      );
    }
    if (trimmed.startsWith("# ")) {
      return (
        <h2 key={lineIdx} style={{ fontSize: "18px", fontWeight: "700", marginTop: "20px", marginBottom: "10px", color: "var(--accent-secondary)" }}>
          {parseInlineStyles(trimmed.substring(2))}
        </h2>
      );
    }
    const isBullet = trimmed.startsWith("* ") || trimmed.startsWith("- ") || trimmed.startsWith("• ");
    if (isBullet) {
      return (
        <li key={lineIdx} style={{ marginLeft: "16px", marginBottom: "4px", listStyleType: "disc" }}>
          {parseInlineStyles(trimmed.substring(2))}
        </li>
      );
    }
    const numMatch = trimmed.match(/^(\d+)\.\s(.*)/);
    if (numMatch) {
      return (
        <li key={lineIdx} style={{ marginLeft: "16px", marginBottom: "4px", listStyleType: "decimal" }}>
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
      return <strong key={index} style={{ fontWeight: "700", color: "var(--text-bright)" }}>{part}</strong>;
    }
    return part;
  });
};

const topicColors: Record<string, string> = {
  Training: "#3b82f6", Nutrition: "#10b981", Recovery: "#8b5cf6",
  Pacing: "#f59e0b", Mindset: "#ec4899", Gear: "#14b8a6",
};
const topicIcons: Record<string, React.ReactNode> = {
  Training: <Mountains weight="fill" />, 
  Nutrition: <BowlFood weight="fill" />, 
  Recovery: <Bed weight="fill" />,
  Pacing: <Timer weight="fill" />, 
  Mindset: <Brain weight="fill" />, 
  Gear: <Backpack weight="fill" />,
};

const KnowledgeCard = ({ card, expanded = false }: { card: any; expanded?: boolean }) => {
  const [open, setOpen] = useState(expanded);
  const color = topicColors[card.topic] || "#6366f1";
  const icon = topicIcons[card.topic] || <Book weight="fill" />;
  return (
    <div style={{
      background: "var(--bg-card)", border: `1px solid var(--border-color)`,
      borderRadius: "14px", padding: "16px", cursor: "pointer",
      transition: "all 0.2s cubic-bezier(0.16, 1, 0.3, 1)", backdropFilter: "blur(8px)",
      boxShadow: "inset 0 1px 0 rgba(255,255,255,0.05)"
    }}
      onClick={() => setOpen(!open)}
      onMouseEnter={e => {
        e.currentTarget.style.background = "var(--bg-card-hover)";
        e.currentTarget.style.transform = "translateY(-1px)";
      }}
      onMouseLeave={e => {
        e.currentTarget.style.background = "var(--bg-card)";
        e.currentTarget.style.transform = "translateY(0)";
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "8px", marginBottom: "8px" }}>
        <span style={{
          display: "flex", alignItems: "center", gap: "4px",
          fontSize: "10px", fontWeight: "700", padding: "4px 8px", borderRadius: "20px",
          background: `${color}22`, color: color, letterSpacing: "0.5px", flexShrink: 0,
        }}>{icon} {card.topic?.toUpperCase()}</span>
        <span style={{ fontSize: "14px", color: "var(--text-muted)", flexShrink: 0 }}>{open ? <CaretUp weight="bold"/> : <CaretDown weight="bold"/>}</span>
      </div>
      <div style={{ fontWeight: "700", fontSize: "14px", color: "var(--text-bright)", marginBottom: "8px", lineHeight: "1.4" }}>
        {card.chapter_title}
      </div>
      <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6", margin: 0 }}>
        {card.summary}
      </p>
      {open && card.key_points?.length > 0 && (
        <ul style={{ marginTop: "12px", paddingLeft: "16px", display: "flex", flexDirection: "column", gap: "6px" }}>
          {card.key_points.map((pt: string, i: number) => (
            <li key={i} style={{ fontSize: "12.5px", color: "var(--text-secondary)", lineHeight: "1.5" }}>
              {pt}
            </li>
          ))}
        </ul>
      )}
      {open && card.tags?.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "4px", marginTop: "10px" }}>
          {card.tags.map((tag: string, i: number) => (
            <span key={i} style={{
              fontSize: "10px", padding: "2px 6px", borderRadius: "10px",
              background: "rgba(255,255,255,0.1)", color: "var(--text-muted)",
            }}>#{tag}</span>
          ))}
        </div>
      )}
    </div>
  );
};

export default function Home() {
  // Navigation active tab
    const [isNutritionLabOpen, setIsNutritionLabOpen] = useState(false);
  const [isGearVaultOpen, setIsGearVaultOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"home" | "about" | "chat" | "planner" | "tools" | "knowledge">("home");

  const handleTabSwitch = (tab: "home" | "about" | "chat" | "planner" | "tools" | "knowledge") => {
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
  const [lang, setLang] = useState<"en" | "vi">("en");

  // State for homepage CTA button hover effect
  const [startBtnHovered, setStartBtnHovered] = useState(false);
  
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
  const [viewportWidth, setViewportWidth] = useState<number>(1024);
  const [selectedDeviceView, setSelectedDeviceView] = useState<"laptop" | "phone">("laptop");
  const [viewMode, setViewMode] = useState<"showcase" | "desktop" | "mobile">("showcase");
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
  const [heroInput, setHeroInput] = useState("");


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
      onDone?: () => void
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

      const outVid  = activeVideoRef.current === "A" ? vidA : vidB;
      const inVid   = activeVideoRef.current === "A" ? vidB : vidA;
      const outRaf  = activeVideoRef.current === "A" ? crossfadeRafARef : crossfadeRafBRef;
      const inRaf   = activeVideoRef.current === "A" ? crossfadeRafBRef : crossfadeRafARef;

      // Pre-position the incoming video and start playing it silently at opacity 0
      inVid.currentTime = 0;
      inVid.style.opacity = "0";
      inVid.style.zIndex  = "2";
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
      if (vidA.duration - vidA.currentTime <= FADE_THRESHOLD) triggerCrossfade();
    };
    const handleTimeUpdateB = () => {
      if (!vidB.duration || activeVideoRef.current !== "B") return;
      if (vidB.duration - vidB.currentTime <= FADE_THRESHOLD) triggerCrossfade();
    };

    // Initial startup: fade vidA in
    vidA.style.opacity = "0";
    vidB.style.opacity = "0";
    vidA.style.zIndex  = "2";
    vidB.style.zIndex  = "1";

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
      if (crossfadeRafARef.current) cancelAnimationFrame(crossfadeRafARef.current);
      if (crossfadeRafBRef.current) cancelAnimationFrame(crossfadeRafBRef.current);
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

    const headers = { "Authorization": `Bearer ${token}` };

    const loadCards = async (topic?: string) => {
      try {
        const url = topic && topic !== "All"
          ? `${API_BASE_URL}/api/knowledge/cards?topic=${encodeURIComponent(topic)}&lang=${lang}`
          : `${API_BASE_URL}/api/knowledge/cards?lang=${lang}`;
        const [cardsRes, dailyRes, topicsRes] = await Promise.all([
          fetch(url, { headers }),
          fetch(`${API_BASE_URL}/api/knowledge/cards/random?n=3&lang=${lang}`, { headers }),
          fetch(`${API_BASE_URL}/api/knowledge/topics`, { headers }),
        ]);
        if (cardsRes.ok) { const d = await cardsRes.json(); setKnowledgeCards(d.cards || []); }
        if (dailyRes.ok) { const d = await dailyRes.json(); setDailyCards(d.cards || []); }
        if (topicsRes.ok) { const d = await topicsRes.json(); setKnowledgeTopics(d.topics || []); }
      } catch (e) { console.error("Knowledge load error", e); }
    };

    const checkStatus = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/knowledge/extract/status`, { headers });
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
        const statusRes = await fetch(`${API_BASE_URL}/api/knowledge/extract/status`, { headers });
        if (statusRes.ok) {
          const s = await statusRes.json();
          setExtractStatus(s);
          if ((s.card_count || 0) === 0 && s.status !== "extracting") {
            // Auto-trigger background extraction
            await fetch(`${API_BASE_URL}/api/knowledge/trigger`, { method: "POST", headers });
            setExtractStatus(prev => ({ ...prev, status: "extracting" }));
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
      const res = await fetch(`${API_BASE_URL}/api/knowledge/cards/random?n=3&lang=${lang}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) { const d = await res.json(); setDailyCards(d.cards || []); }
    } catch (e) {}
  };

  const filterKnowledgeByTopic = async (topic: string) => {
    setKnowledgeTopic(topic);
    const token = localStorage.getItem("uphill_session_token");
    if (!token) return;
    try {
      const url = topic !== "All"
        ? `${API_BASE_URL}/api/knowledge/cards?topic=${encodeURIComponent(topic)}&lang=${lang}`
        : `${API_BASE_URL}/api/knowledge/cards?lang=${lang}`;
      const res = await fetch(url, { headers: { "Authorization": `Bearer ${token}` } });
      if (res.ok) { const d = await res.json(); setKnowledgeCards(d.cards || []); }
    } catch (e) {}
  };


  // Backend connection status
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);

  // Chat sandbox state
  const [chatMessages, setChatMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I’m Coach Uphill AI. Are you training for a trail ultra or a road marathon?",
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // File parser sandbox state
  const [parsedSummary, setParsedSummary] = useState<ParsedSummary | null>(null);
  const [parserLoading, setParserLoading] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState("");
  const [parserErrorMsg, setParserErrorMsg] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [gpxCheckpoints, setGpxCheckpoints] = useState<any[]>([]);

  // RAG sandbox state
  const [sources, setSources] = useState<RagSource[]>([]);
  const [linkInput, setLinkInput] = useState("");
  const [ragLoading, setRagLoading] = useState(false);
  const [ragErrorMsg, setRagErrorMsg] = useState("");
  const pdfInputRef = useRef<HTMLInputElement>(null);

  // Knowledge Hub state
  const [knowledgeCards, setKnowledgeCards] = useState<any[]>([]);
  const [dailyCards, setDailyCards] = useState<any[]>([]);
  const [knowledgeTopics, setKnowledgeTopics] = useState<string[]>([]);
  const [knowledgeTopic, setKnowledgeTopic] = useState("All");
  const [extractStatus, setExtractStatus] = useState<{status: string; current_topic?: string; progress?: number; total?: number; card_count?: number}>({ status: "idle" });
  const knowledgePollerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Async plan generation job tracking
  const [planJobId, setPlanJobId] = useState<string | null>(null);
  const [planJobStatus, setPlanJobStatus] = useState<"idle" | "generating" | "done" | "error">("idle");
  const [planJobMessage, setPlanJobMessage] = useState("");
  const planJobPollerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Active Training Plan state
  const [activePlan, setActivePlan] = useState<ActivePlan | null>(null);
  const [backupActivePlan, setBackupActivePlan] = useState<ActivePlan | null>(null);
  const [backupWorkouts, setBackupWorkouts] = useState<Workout[]>([]);
  const [recentPlans, setRecentPlans] = useState<ActivePlan[]>([]);
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [selectedWeek, setSelectedWeek] = useState<number>(1);
  const [exportTimePref, setExportTimePref] = useState("all_day");
  const [showExportOptions, setShowExportOptions] = useState(false);
  const [planForm, setPlanForm] = useState({
    race_name: "",
    race_date: "",
    goal_type: "finish",
    terrain: "trail",
    course_distance_km: "",
    course_elevation_gain_m: "",
    days_per_week: 4,
    long_run_day: "Saturday",
    preferred_days: ["Monday", "Wednesday", "Saturday"] as string[],
    // ── Plan goal category (mirrors onboarding)
    plan_goal_category: "race" as string,  // race | distance | start_running | return | recovery
    plan_start_date: new Date().toISOString().split("T")[0],
    plan_duration_weeks: 12,
    // non-race sub-fields
    time_away: "",
    fitness_feel: "",
    race_distance_completed: "",
    days_since_race: "",
    recovery_feel: "",
  });
  // Target time fields (H/M/S)
  const [targetTimeH, setTargetTimeH] = useState("");
  const [targetTimeM, setTargetTimeM] = useState("");
  const [targetTimeS, setTargetTimeS] = useState("");
  // Cutoff time fields (H/M/S) — for "Just to Finish" goal
  const [cutoffTimeH, setCutoffTimeH] = useState("");
  const [cutoffTimeM, setCutoffTimeM] = useState("");
  const [cutoffTimeS, setCutoffTimeS] = useState("");
  const [planLoading, setPlanLoading] = useState(false);
  const [planErrorMsg, setPlanErrorMsg] = useState("");

  const [courseInputMode, setCourseInputMode] = useState<"manual" | "gpx">("manual");
  const [plannerGpxFile, setPlannerGpxFile] = useState<File | null>(null);
  const [plannerGpxLoading, setPlannerGpxLoading] = useState(false);
  const [plannerGpxError, setPlannerGpxError] = useState("");
  const plannerGpxInputRef = useRef<HTMLInputElement>(null);

  // Swap State
  const [swapDay1, setSwapDay1] = useState("Wednesday");
  const [swapDay2, setSwapDay2] = useState("Thursday");

  // Phase 3 States
  // Pacing
  const [targetFlatPace, setTargetFlatPace] = useState("6.0");
  const [pacedCheckpoints, setPacedCheckpoints] = useState<PacedCheckpoint[]>([]);
  const [pacingLoading, setPacingLoading] = useState(false);
  
  // Fueling
  const [fuelDuration, setFuelDuration] = useState("4.0");
  const [fuelSweatRate, setFuelSweatRate] = useState("moderate");
  const [fuelTemp, setFuelTemp] = useState("moderate");
  const [fuelStrategy, setFuelStrategy] = useState<FuelStrategy | null>(null);
  const [fuelLoading, setFuelLoading] = useState(false);

  // Shoes
  const [shoeSurface, setShoeSurface] = useState("trail");
  const [shoeCushion, setShoeCushion] = useState("balanced");
  const [shoeWidth, setShoeWidth] = useState("normal");
  const [recommendedShoes, setRecommendedShoes] = useState<Shoe[]>([]);
  const [shoesLoading, setShoesLoading] = useState(false);

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
    use_treadmill?: number;
    gemini_api_key?: string;
    notebooklm_notebook_id?: string;
    notebooklm_auth_json?: string;
    zone2_pace_min?: string;
    zone2_pace_max?: string;
    provider?: string;
    has_password?: boolean;
  }

  const [user, setUser] = useState<User | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [mockEmailInput, setMockEmailInput] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [authErrorMsg, setAuthErrorMsg] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);

  // Onboarding / Profile Settings State
  const [onboardingOpen, setOnboardingOpen] = useState(false);
  const [profileSettingsOpen, setProfileSettingsOpen] = useState(false);
  const [passwordFormOpen, setPasswordFormOpen] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [passwordMsg, setPasswordMsg] = useState("");
  const [passwordError, setPasswordError] = useState("");

  // New auth modal state
  const [authTab, setAuthTab] = useState<"signin" | "register">("signin");
  const [emailInput, setEmailInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [nameInput, setNameInput] = useState("");
  const [confirmPasswordInput, setConfirmPasswordInput] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  // Onboarding wizard state
  const [onboardingStep, setOnboardingStep] = useState(0);
  const [onboardingAnswers, setOnboardingAnswers] = useState<Record<string, any>>({
    dob: "",
    goal_type: "",
    fitness_input_mode: "estimate",
    aet_hr: "", ant_hr: "", max_hr: "", resting_hr: "",
    zone2_pace_min: "6:30", zone2_pace_max: "5:45",
    race_distance: "10k", race_time_hours: "0", race_time_minutes: "50",
    injury_history: "",
    race_name: "", race_date: "",
    course_distance_km: "", course_elevation_gain_m: "", terrain: "trail",
    race_goal: "finish", expected_finish_hours: "", expected_finish_minutes: "",
    days_per_week: 4,
    preferred_run_days: [] as string[],
    long_run_day: "Saturday",
    current_weekly_km: "30",
    has_gym_access: false,
    time_away: "", reason_for_break: "", fitness_feel: "",
    race_distance_completed: "", days_since_race: "", recovery_feel: "", next_goal: "",
    plan_start_date: new Date().toISOString().split("T")[0],
  });
  const [onboardingGenerating, setOnboardingGenerating] = useState(false);
  const [profileForm, setProfileForm] = useState({
    age: "30",
    current_weekly_km: "30",
    max_hr: "185",
    resting_hr: "60",
    aet_hr: "135",
    ant_hr: "165",
    use_treadmill: false,
    gemini_api_key: "",
    zone2_pace_min: "6:30",
    zone2_pace_max: "5:45"
  });

  const [onboardingMode, setOnboardingMode] = useState<"estimate" | "manual">("estimate");
  const [raceDistance, setRaceDistance] = useState("10k");
  const [raceTimeHours, setRaceTimeHours] = useState("0");
  const [raceTimeMinutes, setRaceTimeMinutes] = useState("50");
  const [easyPaceMin, setEasyPaceMin] = useState("6");
  const [easyPaceSec, setEasyPaceSec] = useState("30");
  const [zone2Min, setZone2Min] = useState("125");
  const [zone2Max, setZone2Max] = useState("142");

  useEffect(() => {
    if (onboardingMode === "estimate") {
      const ageNum = parseInt(profileForm.age) || 30;
      const zone2MaxNum = parseInt(zone2Max) || 140;
      
      const maxHrEst = 220 - ageNum;
      const aetHrEst = zone2MaxNum;
      const antHrEst = Math.round(zone2MaxNum * 1.18);

      setProfileForm(prev => {
        if (prev.max_hr === String(maxHrEst) && prev.aet_hr === String(aetHrEst) && prev.ant_hr === String(antHrEst)) {
          return prev;
        }
        return {
          ...prev,
          max_hr: String(maxHrEst),
          aet_hr: String(aetHrEst),
          ant_hr: String(antHrEst)
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
        headers: { "Authorization": `Bearer ${token}` }
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
            use_treadmill: userData.use_treadmill === 1,
            gemini_api_key: userData.gemini_api_key ?? "",
            zone2_pace_min: userData.zone2_pace_min ?? "6:30",
            zone2_pace_max: userData.zone2_pace_max ?? "5:45"
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
        const client_id = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com";
        g.accounts.id.initialize({
          client_id: client_id,
          callback: (response: any) => {
            if (response && response.credential) {
              handleGoogleLogin(response.credential);
            }
          }
        });

        const btnContainer = document.getElementById("google-signin-btn");
        if (btnContainer) {
          g.accounts.id.renderButton(
            btnContainer,
            { 
              theme: "outline", 
              size: "large", 
              width: btnContainer.clientWidth || 416, 
              text: "continue_with",
              shape: "rectangular"
            }
          );
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

  const fetchSourcesWithToken = async (currentUser: User | null, token: string) => {
    const activeUser = currentUser || user;
    if (!activeUser || activeUser.role !== 'admin') {
      setSources([]);
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/sources`, {
        headers: { "Authorization": `Bearer ${token}` }
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
        headers: { "Authorization": `Bearer ${token}` }
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
        headers: { "Authorization": `Bearer ${token}` }
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
        use_treadmill: data.user.use_treadmill === 1,
        gemini_api_key: data.user.gemini_api_key ?? "",
        zone2_pace_min: data.user.zone2_pace_min ?? "6:30",
        zone2_pace_max: data.user.zone2_pace_max ?? "5:45"
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
          errMsg = errData.detail.map((e: any) => e.msg || JSON.stringify(e)).join(", ");
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
        use_treadmill: data.user.use_treadmill === 1,
        gemini_api_key: data.user.gemini_api_key ?? "",
        zone2_pace_min: data.user.zone2_pace_min ?? "6:30",
        zone2_pace_max: data.user.zone2_pace_max ?? "5:45"
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
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          age: parseInt(profileForm.age),
          current_weekly_km: parseFloat(profileForm.current_weekly_km),
          max_hr: parseInt(profileForm.max_hr),
          resting_hr: parseInt(profileForm.resting_hr),
          aet_hr: parseInt(profileForm.aet_hr),
          ant_hr: parseInt(profileForm.ant_hr),
          use_treadmill: profileForm.use_treadmill,
          gemini_api_key: profileForm.gemini_api_key,
          zone2_pace_min: profileForm.zone2_pace_min,
          zone2_pace_max: profileForm.zone2_pace_max
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
          "Authorization": `Bearer ${token}`
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
      `width=${width},height=${height},left=${left},top=${top},status=no,resizable=yes`
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
              <p>Authorize Uphill.AI to access your profile name and email address via <strong>${provider === 'google' ? 'Google' : 'Facebook'} OAuth</strong>.</p>
              
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
        body: JSON.stringify({ name: nameInput.trim(), email: emailInput.trim(), password: passwordInput }),
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
        body: JSON.stringify({ email: emailInput.trim(), password: passwordInput }),
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
        const res = await fetch(`${API_BASE_URL}/api/coach/plan-status/${jobId}`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
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
        age = Math.floor((Date.now() - born.getTime()) / (365.25 * 24 * 3600 * 1000));
      }
      const payload: any = {
        dob: onboardingAnswers.dob || null,
        age,
        goal_type: onboardingAnswers.goal_type,
        injury_history: onboardingAnswers.injury_history || null,
        preferred_run_days: onboardingAnswers.preferred_run_days,
        long_run_day: onboardingAnswers.long_run_day || "Saturday",
        days_per_week: onboardingAnswers.days_per_week || 4,
        current_weekly_km: parseFloat(onboardingAnswers.current_weekly_km) || 30.0,
        has_gym_access: onboardingAnswers.has_gym_access || false,
        zone2_pace_min: onboardingAnswers.zone2_pace_min || "6:30",
        zone2_pace_max: onboardingAnswers.zone2_pace_max || "5:45",
        terrain: onboardingAnswers.terrain || "trail",
        time_away: onboardingAnswers.time_away || null,
        reason_for_break: onboardingAnswers.reason_for_break || null,
        fitness_feel: onboardingAnswers.fitness_feel || null,
        race_distance_completed: onboardingAnswers.race_distance_completed || null,
        days_since_race: onboardingAnswers.days_since_race ? parseInt(onboardingAnswers.days_since_race) : null,
        recovery_feel: onboardingAnswers.recovery_feel || null,
        next_goal: onboardingAnswers.next_goal || null,
        lang: lang,
      };
      // HR zones
      if (onboardingAnswers.aet_hr) payload.aet_hr = parseInt(onboardingAnswers.aet_hr);
      if (onboardingAnswers.ant_hr) payload.ant_hr = parseInt(onboardingAnswers.ant_hr);
      if (onboardingAnswers.max_hr) payload.max_hr = parseInt(onboardingAnswers.max_hr);
      if (onboardingAnswers.resting_hr) payload.resting_hr = parseInt(onboardingAnswers.resting_hr);
      // Race/distance targets
      if (onboardingAnswers.race_name) payload.race_name = onboardingAnswers.race_name;
      if (onboardingAnswers.race_date) payload.race_date = onboardingAnswers.race_date;
      if (onboardingAnswers.course_distance_km) payload.course_distance_km = parseFloat(onboardingAnswers.course_distance_km);
      if (onboardingAnswers.course_elevation_gain_m) payload.course_elevation_gain_m = parseFloat(onboardingAnswers.course_elevation_gain_m);
      if (onboardingAnswers.plan_start_date) payload.plan_start_date = onboardingAnswers.plan_start_date;

      // Race goals
      payload.race_goal = onboardingAnswers.race_goal || "finish";
      if (onboardingAnswers.race_goal === "time") {
        const hh = String(onboardingAnswers.expected_finish_hours || "0");
        const mm = String(onboardingAnswers.expected_finish_minutes || "0");
        payload.expected_finish_time = `${hh.padStart(2, '0')}:${mm.padStart(2, '0')}:00`;
      } else {
        payload.expected_finish_time = null;
      }

      const response = await fetch(`${API_BASE_URL}/api/auth/onboarding`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
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
          headers: { "Authorization": `Bearer ${token}` }
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

    const updatedMessages = [...chatMessages, { role: "user" as const, content: messageText }];
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
            use_treadmill: user?.use_treadmill === 1,
            gemini_api_key: user?.gemini_api_key ?? "",
            zone2_pace_min: user?.zone2_pace_min ?? "6:30",
            zone2_pace_max: user?.zone2_pace_max ?? "5:45",
            recent_race: planForm.race_name,
          },
          context_data: activePlan ? {
            race_name: activePlan.race_name,
            race_date: activePlan.race_date,
            goal_type: activePlan.goal_type,
            total_weeks: activePlan.total_weeks,
            workouts: workouts
          } : null
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to communicate with Coach API");
      }

      const replyData = await response.json();
      setChatMessages((prev) => [...prev, replyData]);
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I had trouble reaching the coaching server. Please make sure the backend server is running.",
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
      setParserErrorMsg("Unsupported file format. Please upload a .fit or .gpx file.");
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
        const fitDist = parseFloat(((sum.total_distance_meters || 0) / 1000).toFixed(2));
        const fitElev = Math.round(sum.total_elevation_gain_meters || 0);
        setParsedSummary({
          distance_km: fitDist,
          duration_mins: parseFloat(((sum.total_duration_seconds || 0) / 60).toFixed(1)),
          elevation_gain_m: fitElev,
          avg_hr: sum.avg_heart_rate ? Math.round(sum.avg_heart_rate) : undefined,
          avg_speed: sum.avg_speed_mps ? `${(16.6667 / sum.avg_speed_mps).toFixed(2)} min/km` : undefined,
          source_type: "FIT",
        });
      } else {
        const gpxDist = parseFloat(((sum.total_distance_meters || 0) / 1000).toFixed(2));
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
      setParserErrorMsg(err.message || "An error occurred while uploading/parsing.");
    } finally {
      setParserLoading(false);
    }
  };

  const handlePlannerGpxFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
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
      const dist = parseFloat(((sum.total_distance_meters || 0) / 1000).toFixed(2));
      const elev = Math.round(sum.total_elevation_gain_meters || 0);

      setPlanForm({
        ...planForm,
        course_distance_km: dist.toString(),
        course_elevation_gain_m: elev.toString()
      });
      setPlannerGpxFile(file);
    } catch (err: any) {
      setPlannerGpxError(err.message || "An error occurred while uploading/parsing.");
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
          "Authorization": `Bearer ${token}`
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

  const handlePdfFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
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
          "Authorization": `Bearer ${token}`
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
          "Authorization": `Bearer ${token}`
        }
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
    const isRaceOrDistVal = planForm.plan_goal_category === "race" || planForm.plan_goal_category === "distance";
    if (isRaceOrDistVal && (!planForm.race_name || !planForm.race_date)) {
      setPlanErrorMsg("Race Name and Race Date are required for Race/Distance goals.");
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
      const isRaceOrDist = planForm.plan_goal_category === "race" || planForm.plan_goal_category === "distance";
      // Build request body
      const body: Record<string, any> = {
        race_name: isRaceOrDist ? planForm.race_name : planForm.plan_goal_category.replace("_", " "),
        race_date: isRaceOrDist ? planForm.race_date : "",
        goal_type: isRaceOrDist ? planForm.goal_type : planForm.plan_goal_category,
        terrain: planForm.terrain,
        course_distance_km: planForm.course_distance_km ? parseFloat(planForm.course_distance_km) : null,
        course_elevation_gain_m: planForm.course_elevation_gain_m ? parseFloat(planForm.course_elevation_gain_m) : null,
        days_per_week: planForm.days_per_week,
        long_run_day: planForm.long_run_day,
        preferred_days: planForm.preferred_days,
        plan_start_date: planForm.plan_start_date || null,
        plan_duration_weeks: isRaceOrDist ? null : planForm.plan_duration_weeks,
        // non-race context fields
        time_away: planForm.time_away || null,
        fitness_feel: planForm.fitness_feel || null,
        race_distance_completed: planForm.race_distance_completed || null,
        days_since_race: planForm.days_since_race ? parseInt(planForm.days_since_race) : null,
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
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errorText = await response.json();
        throw new Error(errorText.detail || "Plan generation failed.");
      }

      const result = await response.json();
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
    } finally {
      setPlanLoading(false);
    }
  };


  const getPlanDistance = (p: ActivePlan) => {
    if (p.course_distance_km !== undefined && p.course_distance_km !== null) return p.course_distance_km;
    if (p.race_name && p.race_name.toUpperCase().includes("SUM30")) return 30;
    return null;
  };

  const getPlanElevation = (p: ActivePlan) => {
    if (p.course_elevation_gain_m !== undefined && p.course_elevation_gain_m !== null) return p.course_elevation_gain_m;
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
      targetStr = p.goal_type.charAt(0).toUpperCase() + p.goal_type.slice(1).replace("_", " ");
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
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ plan_id: planId })
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
      const response = await fetch(`${API_BASE_URL}/api/coach/modify-calendar`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          plan_id: activePlan.id,
          week_number: selectedWeek,
          day_1: swapDay1,
          day_2: swapDay2
        }),
      });

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
    setWorkouts((prev) =>
      prev.map((wo) => (wo.id === woId ? { ...wo, is_completed: isCompleted ? 1 : 0 } : wo))
    );
  };

  const getWeekWorkouts = (weekNum: number) => {
    return workouts.filter((w) => w.week_number === weekNum);
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
      
      const raceWo = workouts.find((w) => {
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
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6
      };
      
      const dayName = wo.day_of_week;
      const workoutDayOffset = DAY_OFFSETS[dayName] !== undefined ? DAY_OFFSETS[dayName] : 0;
      
      const workoutDate = new Date(startMonday);
      workoutDate.setDate(startMonday.getDate() + (wo.week_number - 1) * 7 + workoutDayOffset);
      
      return workoutDate.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    } catch (e) {
      console.error(e);
      return "";
    }
  };

  // --- Phase 3 Calculator Handlers ---
  const handleCalculatePacing = async () => {
    if (gpxCheckpoints.length === 0) return;
    setPacingLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/coach/calculate-pacing`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          checkpoints: gpxCheckpoints,
          target_flat_pace_min_km: parseFloat(targetFlatPace)
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setPacedCheckpoints(result);
      }
    } catch (err) {
      console.error("Failed to calculate pacing:", err);
    } finally {
      setPacingLoading(false);
    }
  };

  const handleCalculateFueling = async () => {
    setFuelLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/coach/calculate-fueling`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          duration_hours: parseFloat(fuelDuration),
          sweat_rate: fuelSweatRate,
          weather_temp: fuelTemp
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setFuelStrategy(result);
      }
    } catch (err) {
      console.error("Failed to calculate fueling:", err);
    } finally {
      setFuelLoading(false);
    }
  };

  const handleRecommendShoes = async () => {
    setShoesLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/coach/recommend-shoes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          surface: shoeSurface,
          cushioning: shoeCushion,
          width: shoeWidth
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setRecommendedShoes(result);
      }
    } catch (err) {
      console.error("Failed to fetch shoes recommendations:", err);
    } finally {
      setShoesLoading(false);
    }
  };

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

  const renderHome = (isMobile: boolean) => {
    return (
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
    );
  };

  const renderAboutUs = (isMobile: boolean) => {
    return (
      <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '8px', padding: '0 16px' }}>
            <Mountains size={isMobile ? 28 : 36} color="var(--accent-primary)" weight="duotone" />
            <h3 className="card-title" style={{ margin: 0, fontSize: isMobile ? '24px' : '32px' }}>
              {lang === "en" ? "About Uphill.AI" : "Về Uphill.AI"}
            </h3>
        </div>
        
        {/* Bento Grid */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', 
          gap: '24px',
          padding: '0 16px' 
        }}>
          
          {/* Block A: The Engine (Span 2 cols on Desktop) */}
          <div className="snow-glass" style={{ 
            gridColumn: isMobile ? 'auto' : 'span 2',
            padding: '32px',
            borderRadius: '32px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '16px', background: 'rgba(255, 255, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Brain size={28} color="var(--text-primary)" weight="duotone" />
              </div>
              <h4 style={{ color: 'var(--text-primary)', margin: 0, fontSize: '20px', fontWeight: 600 }}>
                {lang === "en" ? "The LLM + RAG Architecture" : "Kiến trúc LLM + RAG"}
              </h4>
            </div>
            <p style={{ fontSize: '15px', lineHeight: '1.7', color: 'var(--text-secondary)', marginBottom: '0' }}>
              {lang === "en" 
                ? "Uphill.AI leverages state-of-the-art LLM + Retrieval-Augmented Generation (RAG). Instead of generating generic fitness advice, our AI engine specifically retrieves and synthesizes the gold-standard endurance science from " 
                : "Uphill.AI ứng dụng công nghệ LLM + Retrieval-Augmented Generation (RAG). Thay vì đưa ra những lời khuyên tập luyện chung chung, hệ thống AI của chúng tôi tập trung tìm kiếm và tổng hợp các kiến thức khoa học sức bền cốt lõi từ cuốn sách "}
              <a href="https://www.amazon.com/Training-Uphill-Athlete-Mountain-Mountaineers/dp/B088MKG7DS/" target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent-primary)", textDecoration: "underline", fontWeight: "600" }}>
                Training for the Uphill Athlete
              </a>
              {lang === "en" 
                ? " to ensure your training plans are rooted in proven aerobic capacity building and terrain-specific muscular endurance."
                : ". Nhờ đó, các giáo án tập luyện của bạn luôn được xây dựng dựa trên những phương pháp cải thiện sức bền hiếu khí và sức bền cơ bắp đặc thù theo từng địa hình đã được kiểm chứng."}
            </p>
          </div>

          {/* Block B: Author Motivation */}
          <div className="snow-glass" style={{ 
            padding: '32px',
            borderRadius: '32px'
          }}>
             <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '16px', background: 'rgba(255, 255, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <PersonSimpleRun size={28} color="var(--text-primary)" weight="duotone" />
              </div>
              <h4 style={{ color: 'var(--text-primary)', margin: 0, fontSize: '20px', fontWeight: 600 }}>
                {lang === "en" ? "Built for Runners" : "Dành cho những Runners"}
              </h4>
            </div>
            <p style={{ fontSize: '15px', lineHeight: '1.7', color: 'var(--text-secondary)' }}>
              {lang === "en"
                ? "Created by a trail runner with an IT, AI, and Data Engineering background. After experiencing immense personal growth racing the "
                : "Ứng dụng được xây dựng bởi một trail runner có background về IT, AI và Data Engineering. Sau khi tự mình trải nghiệm sự tiến bộ rõ rệt tại giải "
              }
              <strong style={{ color: "var(--text-primary)" }}>{lang === "en" ? "Ultra-Trail Australia by UTMB (in the Blue Mountains, NSW)" : "Ultra-Trail Australia của UTMB (Blue Mountains, bang New South Wales, Úc)"}</strong>
              {lang === "en"
                ? " using these exact principles, this app was built to democratize that specific training science for everyone."
                : " nhờ áp dụng chính xác các nguyên lý này, ứng dụng được ra đời với mong muốn chia sẻ và đưa những kiến thức khoa học tập luyện chuyên sâu này đến gần hơn với tất cả mọi người."
              }
            </p>
          </div>

          {/* Block C: Core Source & Philosophy (Span 3 cols) */}
          <div className="snow-glass" style={{ 
            gridColumn: isMobile ? 'auto' : 'span 3',
            padding: '32px',
            borderRadius: '32px'
          }}>
             <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '16px', background: 'rgba(255, 255, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Target size={28} color="var(--text-primary)" weight="duotone" />
              </div>
              <h4 style={{ color: 'var(--text-primary)', margin: 0, fontSize: '20px', fontWeight: 600 }}>
                {lang === "en" ? "The Core Philosophy" : "Triết Lý Huấn Luyện Cốt Lõi"}
              </h4>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: '20px' }}>
               <div>
                  <h5 style={{ color: "var(--text-primary)", fontSize: "16px", marginBottom: "8px" }}>{lang === "en" ? "Aerobic Volume" : "Tích lũy Hiếu khí"}</h5>
                  <p style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: "1.6" }}>
                    {lang === "en" ? "Long-term athletic success in the mountains is built upon a foundation of structured, high-volume aerobic capacity training." : "Thành quả tập luyện lâu dài trên những cung đường dốc được xây dựng từ nền tảng tập luyện sức bền hiếu khí một cách bài bản và đều đặn."}
                  </p>
               </div>
               <div>
                  <h5 style={{ color: "var(--text-primary)", fontSize: "16px", marginBottom: "8px" }}>{lang === "en" ? "Muscular Endurance" : "Sức bền Cơ bắp"}</h5>
                  <p style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: "1.6" }}>
                    {lang === "en" ? "Building resistance to localized muscular fatigue ensures you can sustain efforts over vertical terrain for hours." : "Việc rèn luyện khả năng chống chịu mỏi cơ cục bộ sẽ giúp bạn duy trì được sự dẻo dai và ổn định khi leo dốc liên tục suốt nhiều giờ liền."}
                  </p>
               </div>
               <div>
                  <h5 style={{ color: "var(--text-primary)", fontSize: "16px", marginBottom: "8px" }}>{lang === "en" ? "The Authors of \"Training for the Uphill Athlete\"" : "Về các Tác giả của quyển sách \"Training for the Uphill Athlete\""}</h5>
                  <p style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: "1.6" }}>
                    {lang === "en" ? "We express our deepest gratitude to Steve House, Scott Johnston, and Kilian Jornet for their groundbreaking work in endurance science and trail running." : "Ứng dụng xin được bày tỏ lòng tri ân sâu sắc đến Steve House, Scott Johnston và Kilian Jornet vì những đóng góp mang tính nền tảng của họ cho khoa học sức bền và chạy trail."}
                  </p>
               </div>
            </div>
          </div>
        </div>
      </div>
    );
  };
const renderChat = (isMobile: boolean) => {
    const welcomeText = lang === "en" 
      ? "Hello! I’m Coach Uphill AI. Are you training for a trail ultra or a road marathon?"
      : "Xin chào! Tôi là Coach Uphill AI. Bạn đang chuẩn bị cho một giải chạy trail ultra hay marathon đường bằng?";

    return (
      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
        {/* Chat Pane */}
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, width: '100%', minHeight: 0 }}>
          {!isMobile && (
            <h3 style={{ marginBottom: "12px", fontSize: "20px" }}>
              {lang === "en" ? "Chat Workspace" : "Không gian Trò chuyện"}
            </h3>
          )}
          <div className="chat-pane" style={{ flex: 1, display: "flex", flexDirection: "column", width: '100%', minHeight: isMobile ? "0px" : "350px" }}>
            <div className="chat-header" style={{ padding: isMobile ? "8px 12px" : "16px 20px" }}>
              <span className="coach-status-dot"></span>
              <span className="chat-header-title" style={{ fontSize: isMobile ? "13px" : "16px" }}>
                {lang === "en" ? "Coach Uphill (AI)" : "Huấn luyện viên Uphill (AI)"}
              </span>
            </div>
            <div className="chat-history" style={{ padding: isMobile ? "8px" : "20px", gap: isMobile ? "8px" : "16px", minHeight: 0, flex: 1, height: isMobile ? "0px" : undefined, overflowY: "auto" }}>
              {chatMessages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`chat-bubble ${
                    msg.role === "user" ? "chat-bubble-user" : "chat-bubble-assistant"
                  }`}
                  style={{
                    fontSize: isMobile ? "13px" : "14.5px",
                    padding: isMobile ? "8px 12px" : "12px 18px",
                    maxWidth: isMobile ? "90%" : "80%"
                  }}
                >
                  {msg.role === "assistant" 
                    ? (idx === 0 ? parseMarkdown(welcomeText) : parseMarkdown(msg.content)) 
                    : msg.content}
                </div>
              ))}
              {chatLoading && (
                <div className="chat-bubble chat-bubble-assistant" style={{ fontStyle: "italic", opacity: 0.7, fontSize: isMobile ? "13px" : "14.5px", padding: isMobile ? "8px 12px" : "12px 18px" }}>
                  {lang === "en" ? "Coach Uphill is thinking..." : "Coach Uphill đang suy nghĩ..."}
                </div>
              )}
              <div ref={chatBottomRef}></div>
            </div>
            
            <div className="preset-prompt-list" style={{ padding: isMobile ? "0 8px" : "0 20px", gap: "4px", marginBottom: isMobile ? "4px" : "8px" }}>
              <button className="preset-prompt-btn" style={{ fontSize: isMobile ? "10px" : "12px", padding: isMobile ? "3px 8px" : "4px 10px" }} onClick={() => sendPresetPrompt(lang === "en" ? "Can you give me an ME workout for trails?" : "Bạn có thể cho tôi một bài tập ME chạy địa hình không?")}>
                {lang === "en" ? "ME Workout" : "Bài tập ME"}
              </button>
              <button className="preset-prompt-btn" style={{ fontSize: isMobile ? "10px" : "12px", padding: isMobile ? "3px 8px" : "4px 10px" }} onClick={() => sendPresetPrompt(lang === "en" ? "How does the 80/20 rule work?" : "Quy tắc 80/20 hoạt động như thế nào?")}>
                {lang === "en" ? "80/20 Rule" : "Quy tắc 80/20"}
              </button>
            </div>

            <div className="chat-input-bar" style={{ padding: isMobile ? "12px" : "16px" }}>
              <input
                type="text"
                className="chat-input"
                style={{ padding: isMobile ? "10px 16px" : "12px 16px", fontSize: isMobile ? "14px" : "14px" }}
                placeholder={t("chat_input_placeholder")}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                disabled={chatLoading}
              />
              <button className="chat-send-btn" style={{ width: isMobile ? "38px" : "44px", height: isMobile ? "38px" : "44px" }} onClick={() => handleSendMessage()} disabled={chatLoading}>
                <svg width={isMobile ? "15" : "18"} height={isMobile ? "15" : "18"} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderKnowledge = (isMobile: boolean) => {
    const isExtracting = extractStatus.status === "extracting";
    const hasCards = knowledgeCards.length > 0 || dailyCards.length > 0;

    return (
      <div style={{ maxWidth: "860px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>

        {/* Extraction status banner */}
        {isExtracting && (
          <div style={{
            padding: "16px 20px", borderRadius: "12px",
            background: "linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.15))",
            border: "1px solid rgba(139,92,246,0.3)", display: "flex", alignItems: "center", gap: "12px",
          }}>
            <div style={{ fontSize: "20px", animation: "spin 2s linear infinite" }}><Brain weight="bold" /></div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: "700", fontSize: "13px", color: "var(--text-bright)", marginBottom: "4px" }}>
                {lang === "en" ? "Building your Knowledge Hub…" : "Đang tạo Thư viện Kiến thức…"}
              </div>
              <div style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                {extractStatus.current_topic
                  ? `${lang === "en" ? "Extracting:" : "Đang trích xuất:"} ${extractStatus.current_topic} (${extractStatus.progress ?? 0}/${extractStatus.total ?? 8})`
                  : (lang === "en" ? "Querying NotebookLM and structuring knowledge cards…" : "Đang truy vấn NotebookLM và cấu trúc các thẻ kiến thức…")}
              </div>
              <div style={{ marginTop: "6px", height: "4px", borderRadius: "4px", background: "rgba(255,255,255,0.1)", overflow: "hidden" }}>
                <div style={{
                  height: "100%", borderRadius: "4px",
                  background: "linear-gradient(90deg, #34d399, #10b981)",
                  width: `${(((extractStatus.progress ?? 0) / (extractStatus.total ?? 8)) * 100)}%`,
                  transition: "width 0.5s ease",
                }} />
              </div>
            </div>
          </div>
        )}

        {/* ① Daily Knowledge */}
        <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <Lightbulb size={26} color="var(--accent-primary)" weight="duotone" />
              <div>
                <h3 style={{ margin: 0, fontSize: isMobile ? "16px" : "20px", fontWeight: "800" }}>{t("home_daily_insight")}</h3>
                <p style={{ margin: 0, fontSize: "12px", color: "var(--text-secondary)" }}>{t("home_daily_desc")}</p>
              </div>
            </div>
            {hasCards && (
              <button
                className="btn btn-secondary"
                style={{ fontSize: "12px", padding: "6px 14px", borderRadius: "8px", height: "32px", flexShrink: 0 }}
                onClick={shuffleDailyCards}
              >🔀 {t("home_shuffle_btn")}</button>
            )}
          </div>

          {!hasCards && !isExtracting && (
            <div style={{ textAlign: "center", padding: "32px 16px", color: "var(--text-muted)", fontSize: "13px" }}>
              {extractStatus.status === "no_notebooklm"
                ? t("home_connect_notebooklm")
                : t("home_no_cards_yet")}
            </div>
          )}

          {!hasCards && isExtracting && (
            <div style={{ textAlign: "center", padding: "32px 16px", color: "var(--text-muted)", fontSize: "13px" }}>
              ⏳ {t("home_extraction_in_progress")}
            </div>
          )}

          {dailyCards.length > 0 && (
            <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1.3fr 1fr 1.1fr", gap: "14px" }}>
              {dailyCards.map((card, i) => <KnowledgeCard key={i} card={card} />)}
            </div>
          )}
        </div>



        {/* ③ Sources / Upload (Admin only) */}
        {user?.role === "admin" && (
          <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
              <span style={{ fontSize: "24px" }}>📂</span>
              <h3 style={{ margin: 0, fontSize: isMobile ? "16px" : "18px", fontWeight: "800" }}>{t("know_indexed_files")}</h3>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "20px" }}>
              <label style={{ fontSize: "12.5px", fontWeight: "600", color: "var(--text-secondary)" }}>{t("know_ingest_link")}</label>
              <div style={{ display: "flex", gap: "8px" }}>
                <input type="text" className="chat-input" style={{ borderRadius: "8px", padding: "10px 14px", fontSize: "13px" }}
                  placeholder="https://uphillathlete.com/aerobic-training/" value={linkInput}
                  onChange={(e) => setLinkInput(e.target.value)} disabled={ragLoading} />
                <button className="btn btn-primary" style={{ borderRadius: "8px", padding: "8px 18px", fontSize: "13px", height: "40px", flexShrink: 0 }}
                  onClick={handleAddLink} disabled={ragLoading}>{t("know_submit_url")}</button>
              </div>
            </div>
            <div style={{ marginBottom: "20px" }}>
              <label style={{ display: "block", fontSize: "12.5px", fontWeight: "600", color: "var(--text-secondary)", marginBottom: "8px" }}>{t("know_upload_pdf")}</label>
              <button className="btn btn-secondary" style={{ borderRadius: "8px", padding: "10px 16px", fontSize: "13px", width: "100%", height: "40px", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}
                onClick={triggerPdfUpload} disabled={ragLoading}>
                {lang === "en" ? "📥 Choose & Upload PDF" : "📥 Chọn & Tải lên PDF"}
              </button>
              <input type="file" ref={pdfInputRef} onChange={handlePdfFileChange} style={{ display: "none" }} accept=".pdf" />
            </div>
            {ragLoading && <div style={{ color: "var(--accent-secondary)", fontSize: "13px", marginBottom: "12px" }}>{lang === "en" ? "Indexing contents…" : "Đang lập chỉ mục nội dung…"}</div>}
            {ragErrorMsg && <div style={{ color: "var(--accent-alert)", fontSize: "12px", padding: "10px", background: "rgba(239,68,68,0.08)", borderRadius: "8px", marginBottom: "12px" }}>{ragErrorMsg}</div>}
            <div style={{ borderTop: "1px solid var(--border-color)", paddingTop: "16px" }}>
              <h4 style={{ fontSize: "13px", fontWeight: "700", marginBottom: "10px" }}>{lang === "en" ? "Sources" : "Nguồn"} ({sources.length})</h4>
              <div style={{ maxHeight: "200px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "8px" }}>
                {sources.length === 0
                  ? <div style={{ color: "var(--text-muted)", fontSize: "12.5px", fontStyle: "italic", textAlign: "center", padding: "12px 0" }}>{t("know_no_files")}</div>
                  : sources.map((src) => (
                    <div key={src.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "rgba(255,255,255,0.1)", border: "1px solid var(--border-color)", borderRadius: "8px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", overflow: "hidden" }}>
                        <span>{src.type === "pdf" ? "📄" : src.type === "youtube" ? "📺" : "🌐"}</span>
                        <span style={{ fontSize: "13px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: isMobile ? "200px" : "450px" }} title={src.title}>{src.title}</span>
                      </div>
                      <button style={{ background: "none", border: "none", color: "rgba(239,68,68,0.7)", cursor: "pointer", fontSize: "14px", padding: "4px" }} onClick={() => handleDeleteSource(src.id)}><Trash weight="bold" /></button>
                    </div>
                  ))
                }
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };



  const renderPlanner = (isMobile: boolean) => {
    return (
      <div>
        {!activePlan ? (
          <form onSubmit={handleGeneratePlan} style={{ background: "rgba(255, 255, 255, 0.95)", border: "1px solid var(--border-color)", padding: isMobile ? "20px" : "32px", borderRadius: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "8px" }}>
              <h3 style={{ fontSize: isMobile ? "18px" : "22px", margin: 0, color: "var(--accent-primary)" }}>
                {lang === "en" ? "Plan Settings" : "Cài đặt Kế hoạch"}
              </h3>
            </div>

            {/* ── Step 1: Plan Goal Category ────────────────────── */}
            <div style={{ marginBottom: "20px" }}>
              <label style={{ display: "block", fontSize: "12px", fontWeight: "700", marginBottom: "10px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                {t("goal_category")}
              </label>
              <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr 1fr" : "repeat(5, 1fr)", gap: "8px" }}>
                {([
                  { val: "race",          Icon: Trophy, label: t("goal_race").replace(" 🏆", "") },
                  { val: "distance",      Icon: Target, label: t("goal_distance").replace(" 📏", "") },
                  { val: "start_running", Icon: Sneaker, label: t("goal_start").replace(" 🌱", "") },
                  { val: "return",        Icon: PersonSimpleRun, label: t("goal_return").replace(" 🔄", "") },
                  { val: "recovery",      Icon: Bed, label: t("goal_recovery").replace(" 💤", "") },
                ] as const).map(({ val, Icon, label }) => {
                  const active = planForm.plan_goal_category === val;
                  return (
                    <button key={val} type="button"
                      onClick={() => setPlanForm({ ...planForm, plan_goal_category: val })}
                      style={{ padding: "10px 6px", borderRadius: "10px", border: `1.5px solid ${active ? "var(--accent-primary)" : "var(--border-color)"}`, background: active ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: active ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: active ? "700" : "500", fontSize: "12px", cursor: "pointer", textAlign: "center" as const, display: "flex", flexDirection: "column" as const, alignItems: "center", gap: "4px" }}>
                      <Icon size={24} weight="duotone" />
                      <span>{label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* ── Race / Distance fields ────────────────────────── */}
            {(planForm.plan_goal_category === "race" || planForm.plan_goal_category === "distance") && (<>

              <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: isMobile ? "12px" : "16px", marginBottom: "12px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                    {planForm.plan_goal_category === "race" ? t("plan_race_name") : (lang === "en" ? "Distance Goal Name" : "Tên Mục tiêu Cự ly")}
                  </label>
                  <input type="text" className="chat-input"
                    style={{ borderRadius: "8px", width: "100%", padding: "10px" }}
                    placeholder={planForm.plan_goal_category === "race" ? "e.g. UTMB, SUM30" : "e.g. My First Marathon"}
                    value={planForm.race_name}
                    onChange={(e) => setPlanForm({ ...planForm, race_name: e.target.value })} />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                    {planForm.plan_goal_category === "race" ? t("plan_race_date") : (lang === "en" ? "Target Date" : "Ngày Mục tiêu")}
                  </label>
                  <input type="date" className="chat-input"
                    style={{ borderRadius: "8px", width: "100%", padding: "10px" }}
                    value={planForm.race_date}
                    onChange={(e) => setPlanForm({ ...planForm, race_date: e.target.value })} />
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: isMobile ? "12px" : "16px", marginBottom: "16px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>{t("plan_terrain")}</label>
                  <select className="chat-input" style={{ borderRadius: "8px", width: "100%", height: "38px", padding: "0 8px", fontSize: "13px" }}
                    value={planForm.terrain} onChange={(e) => setPlanForm({ ...planForm, terrain: e.target.value })}>
                    <option value="trail">{t("plan_trail")}</option>
                    <option value="road">{t("plan_road")}</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>{t("plan_goal_type")}</label>
                  <select className="chat-input" style={{ borderRadius: "8px", width: "100%", height: "38px", padding: "0 8px", fontSize: "13px" }}
                    value={planForm.goal_type} onChange={(e) => setPlanForm({ ...planForm, goal_type: e.target.value })}>
                    <option value="finish">{t("plan_goal_finish")}</option>
                    <option value="time">{t("plan_goal_time")}</option>
                    <option value="optimal">{t("plan_goal_optimal")}</option>
                  </select>
                </div>
              </div>

              {/* Target time */}
              {planForm.goal_type === "time" && (
                <div style={{ marginBottom: "16px" }}>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>{t("plan_target_time")}</label>
                  <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr 1.1fr", gap: "8px" }}>
                    <div><label style={{ display: "block", fontSize: "11px", color: "var(--text-secondary)", marginBottom: "4px" }}>{lang === "en" ? "Hours" : "Giờ"}</label><input type="number" min="0" max="99" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "8px", textAlign: "center" }} placeholder="0" value={targetTimeH} onChange={(e) => setTargetTimeH(e.target.value)} /></div>
                    <div><label style={{ display: "block", fontSize: "11px", color: "var(--text-secondary)", marginBottom: "4px" }}>{lang === "en" ? "Minutes" : "Phút"}</label><input type="number" min="0" max="59" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "8px", textAlign: "center" }} placeholder="0" value={targetTimeM} onChange={(e) => setTargetTimeM(e.target.value)} /></div>
                    <div><label style={{ display: "block", fontSize: "11px", color: "var(--text-secondary)", marginBottom: "4px" }}>{lang === "en" ? "Seconds" : "Giây"}</label><input type="number" min="0" max="59" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "8px", textAlign: "center" }} placeholder="0" value={targetTimeS} onChange={(e) => setTargetTimeS(e.target.value)} /></div>
                  </div>
                </div>
              )}

              {/* Cutoff time */}
              {planForm.goal_type === "finish" && (
                <div style={{ marginBottom: "16px" }}>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "2px", color: "var(--text-secondary)" }}>{t("plan_cutoff_time")} <span style={{ fontWeight: 400, opacity: 0.7 }}>{lang === "en" ? "(optional — we'll target 85% of cutoff)" : "(tùy chọn — mục tiêu đạt 85% cutoff)"}</span></label>
                  <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr 1.1fr", gap: "8px", marginTop: "6px" }}>
                    <div><label style={{ display: "block", fontSize: "11px", color: "var(--text-secondary)", marginBottom: "4px" }}>{lang === "en" ? "Hours" : "Giờ"}</label><input type="number" min="0" max="99" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "8px", textAlign: "center" }} placeholder="0" value={cutoffTimeH} onChange={(e) => setCutoffTimeH(e.target.value)} /></div>
                    <div><label style={{ display: "block", fontSize: "11px", color: "var(--text-secondary)", marginBottom: "4px" }}>{lang === "en" ? "Minutes" : "Phút"}</label><input type="number" min="0" max="59" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "8px", textAlign: "center" }} placeholder="0" value={cutoffTimeM} onChange={(e) => setCutoffTimeM(e.target.value)} /></div>
                    <div><label style={{ display: "block", fontSize: "11px", color: "var(--text-secondary)", marginBottom: "4px" }}>{lang === "en" ? "Seconds" : "Giây"}</label><input type="number" min="0" max="59" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "8px", textAlign: "center" }} placeholder="0" value={cutoffTimeS} onChange={(e) => setCutoffTimeS(e.target.value)} /></div>
                  </div>
                </div>
              )}

              {/* Course profile */}
              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>{t("plan_course_mode")}</label>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button type="button" className={`btn ${courseInputMode === "manual" ? "btn-primary" : "btn-secondary"}`} style={{ padding: "6px 12px", fontSize: "12px", borderRadius: "8px", height: "32px", flex: 1 }} onClick={() => setCourseInputMode("manual")}>
                    {lang === "en" ? "✍️ Manual" : "✍️ Thủ công"}
                  </button>
                  <button type="button" className={`btn ${courseInputMode === "gpx" ? "btn-primary" : "btn-secondary"}`} style={{ padding: "6px 12px", fontSize: "12px", borderRadius: "8px", height: "32px", flex: 1 }} onClick={() => setCourseInputMode("gpx")}>
                    {lang === "en" ? "📂 GPX Route" : "📂 Tệp GPX"}
                  </button>
                </div>
              </div>

              {courseInputMode === "manual" ? (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: isMobile ? "12px" : "16px", marginBottom: "20px" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Distance (km)" : "Cự ly (km)"}
                    </label>
                    <input type="number" step="0.1" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "10px" }} placeholder="e.g. 50" value={planForm.course_distance_km} onChange={(e) => setPlanForm({ ...planForm, course_distance_km: e.target.value })} />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Elevation Gain (m)" : "Độ cao lũy kế (m)"}
                    </label>
                    <input type="number" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "10px" }} placeholder="e.g. 1500" value={planForm.course_elevation_gain_m} onChange={(e) => setPlanForm({ ...planForm, course_elevation_gain_m: e.target.value })} />
                  </div>
                </div>
              ) : (
                <div style={{ marginBottom: "20px", padding: "16px", background: "rgba(255,255,255,0.1)", border: "1px dashed var(--border-color)", borderRadius: "12px", textAlign: "center" }}>
                  <input type="file" accept=".gpx" style={{ display: "none" }} ref={plannerGpxInputRef} onChange={handlePlannerGpxFileChange} />
                  <button type="button" className="btn btn-secondary" style={{ fontSize: "12px", padding: "6px 12px", height: "32px", margin: "0 auto 8px auto" }} onClick={() => plannerGpxInputRef.current?.click()} disabled={plannerGpxLoading}>
                    {plannerGpxLoading ? (lang === "en" ? "Parsing..." : "Đang đọc...") : (lang === "en" ? "Select GPX" : "Chọn tệp GPX")}
                  </button>
                  {plannerGpxFile && <div style={{ marginTop: "6px", padding: "6px", background: "rgba(16, 185, 129, 0.05)", border: "1px solid var(--border-color)", borderRadius: "6px", fontSize: "11.5px" }}>✅ {planForm.course_distance_km}km, {planForm.course_elevation_gain_m}m</div>}
                  {plannerGpxError && <div style={{ marginTop: "6px", fontSize: "11px", color: "var(--accent-alert)" }}><XCircle weight="fill" style={{marginRight: "4px", verticalAlign: "middle"}}/> {plannerGpxError}</div>}
                </div>
              )}
            </>)}

            {/* ── Start Running fields ───────────────────────────── */}
            {planForm.plan_goal_category === "start_running" && (
              <div style={{ marginBottom: "16px", padding: "16px", border: "1px solid var(--border-color)", borderRadius: "12px", display: "flex", flexDirection: "column", gap: "12px" }}>
                <h4 style={{ margin: 0, fontSize: "14px", fontWeight: "700", color: "var(--text-bright)", borderBottom: "1px solid var(--border-color)", paddingBottom: "8px" }}>
                  {lang === "en" ? "Start Running Program" : "Lộ trình Bắt đầu Chạy bộ"}
                </h4>
                <div style={{ fontSize: "12.5px", color: "var(--text-muted)" }}>
                  {lang === "en" ? "We'll build a gentle walk-to-run programme starting from your plan start date." : "Chúng tôi sẽ xây dựng một lộ trình chạy kết hợp đi bộ nhẹ nhàng bắt đầu từ ngày bạn chọn."}
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Plan Start Date" : "Ngày bắt đầu kế hoạch"}
                    </label>
                    <input type="date" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "10px" }} value={planForm.plan_start_date} onChange={e => setPlanForm({ ...planForm, plan_start_date: e.target.value })} />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Duration (weeks)" : "Thời lượng (tuần)"}
                    </label>
                    <select className="chat-input" style={{ borderRadius: "8px", width: "100%", height: "38px", padding: "0 8px", fontSize: "13px" }} value={planForm.plan_duration_weeks} onChange={e => setPlanForm({ ...planForm, plan_duration_weeks: parseInt(e.target.value) })}>
                      {[6,8,10,12,16].map(w => <option key={w} value={w}>{w} {lang === "en" ? "weeks" : "tuần"}</option>)}
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* ── Return to Running fields ───────────────────────── */}
            {planForm.plan_goal_category === "return" && (
              <div style={{ marginBottom: "16px", padding: "16px", border: "1px solid var(--border-color)", borderRadius: "12px", display: "flex", flexDirection: "column", gap: "12px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border-color)", paddingBottom: "8px", flexWrap: "wrap", gap: "8px" }}>
                  <h4 style={{ margin: 0, fontSize: "14px", fontWeight: "700", color: "var(--text-bright)" }}>
                    {lang === "en" ? "🔄 Return to Running" : "🔄 Tập luyện trở lại"}
                  </h4>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px" }}>
                    <select
                      className="btn btn-secondary"
                      style={{
                        fontSize: "12px",
                        height: "36px",
                        padding: "0 16px",
                        cursor: "pointer",
                        outline: "none",
                        border: "1px solid rgba(0, 0, 0, 0.1)",
                        background: "rgba(0, 0, 0, 0.06)",
                        color: "#111111",
                        textAlignLast: "center",
                        WebkitAppearance: "none",
                        MozAppearance: "none",
                        appearance: "none",
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        borderRadius: "9999px",
                        width: "auto",
                        maxWidth: "220px"
                      }}
                      value=""
                      onChange={(e) => {
                        const val = e.target.value;
                        if (val) handleSelectPlan(Number(val));
                      }}
                    >
                      <option value="" style={{ color: "var(--text-primary)" }}>
                        {lang === "en" ? "Load Recent Plan..." : "Tải lịch tập gần đây..."}
                      </option>
                      {recentPlans.length === 0 ? (
                        <option value="" disabled style={{ color: "var(--text-muted)" }}>
                          {lang === "en" ? "— No plans available —" : "— Không có lịch tập —"}
                        </option>
                      ) : (
                        recentPlans.slice(0, 3).map((p) => (
                          <option key={p.id} value={p.id} style={{ color: "var(--text-primary)" }}>
                            {formatPlanName(p)}
                          </option>
                        ))
                      )}
                    </select>
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Plan Start Date" : "Ngày bắt đầu kế hoạch"}
                    </label>
                    <input type="date" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "10px" }} value={planForm.plan_start_date} onChange={e => setPlanForm({ ...planForm, plan_start_date: e.target.value })} />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Duration (weeks)" : "Thời lượng (tuần)"}
                    </label>
                    <select className="chat-input" style={{ borderRadius: "8px", width: "100%", height: "38px", padding: "0 8px", fontSize: "13px" }} value={planForm.plan_duration_weeks} onChange={e => setPlanForm({ ...planForm, plan_duration_weeks: parseInt(e.target.value) })}>
                      {[6,8,10,12,16].map(w => <option key={w} value={w}>{w} {lang === "en" ? "weeks" : "tuần"}</option>)}
                    </select>
                  </div>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "12.5px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                    {lang === "en" ? "How long have you been away?" : "Bạn đã dừng chạy trong bao lâu?"}
                  </label>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                    {["< 2 weeks","2–6 weeks","1–3 months","3–6 months","6+ months"].map(v => {
                      const label = lang === "vi" 
                        ? v.replace("< 2 weeks", "< 2 tuần").replace("weeks", "tuần").replace("months", "tháng").replace("months+", "tháng trở lên")
                        : v;
                      return (
                        <button key={v} type="button" onClick={() => setPlanForm({ ...planForm, time_away: v })}
                          style={{ padding: "6px 10px", borderRadius: "8px", border: `1.5px solid ${planForm.time_away === v ? "var(--accent-primary)" : "var(--border-color)"}`, background: planForm.time_away === v ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: planForm.time_away === v ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: planForm.time_away === v ? "700" : "500", fontSize: "12px", cursor: "pointer" }}>
                          {label}
                        </button>
                      );
                    })}
                  </div>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "12.5px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                    {lang === "en" ? "How are you feeling now?" : "Hiện tại bạn cảm thấy thế nào?"}
                  </label>
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    {["Feeling good, just need structure","A bit rusty, slightly deconditioned","Significant deconditioning — starting nearly fresh"].map(v => {
                      const label = lang === "vi"
                        ? v.replace("Feeling good, just need structure", "Cảm thấy tốt, chỉ cần lộ trình bài bản")
                           .replace("A bit rusty, slightly deconditioned", "Hơi oải, giảm thể lực nhẹ")
                           .replace("Significant deconditioning — starting nearly fresh", "Giảm thể lực nhiều — bắt đầu gần như mới")
                        : v;
                      return (
                        <button key={v} type="button" onClick={() => setPlanForm({ ...planForm, fitness_feel: v })}
                          style={{ padding: "8px 12px", borderRadius: "8px", border: `1.5px solid ${planForm.fitness_feel === v ? "var(--accent-primary)" : "var(--border-color)"}`, background: planForm.fitness_feel === v ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: planForm.fitness_feel === v ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: planForm.fitness_feel === v ? "700" : "500", fontSize: "12.5px", cursor: "pointer", textAlign: "left" as const }}>
                          {label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {/* ── Post-Race Recovery fields ──────────────────────── */}
            {planForm.plan_goal_category === "recovery" && (
              <div style={{ marginBottom: "16px", padding: "16px", border: "1px solid var(--border-color)", borderRadius: "12px", display: "flex", flexDirection: "column", gap: "12px" }}>
                <h4 style={{ margin: 0, fontSize: "14px", fontWeight: "700", color: "var(--text-bright)", borderBottom: "1px solid var(--border-color)", paddingBottom: "8px" }}>
                  {lang === "en" ? "💤 Post-Race Recovery Program" : "💤 Lộ trình Phục hồi sau Giải chạy"}
                </h4>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Plan Start Date" : "Ngày bắt đầu kế hoạch"}
                    </label>
                    <input type="date" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "10px" }} value={planForm.plan_start_date} onChange={e => setPlanForm({ ...planForm, plan_start_date: e.target.value })} />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Duration (weeks)" : "Thời lượng (tuần)"}
                    </label>
                    <select className="chat-input" style={{ borderRadius: "8px", width: "100%", height: "38px", padding: "0 8px", fontSize: "13px" }} value={planForm.plan_duration_weeks} onChange={e => setPlanForm({ ...planForm, plan_duration_weeks: parseInt(e.target.value) })}>
                      {[4,6,8,10,12].map(w => <option key={w} value={w}>{w} {lang === "en" ? "weeks" : "tuần"}</option>)}
                    </select>
                  </div>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "12.5px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                    {lang === "en" ? "Race you completed" : "Giải chạy bạn đã hoàn thành"}
                  </label>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                    {["5k","10k","Half Marathon","Marathon","Ultra (< 60k)","Ultra (60k+)"].map(v => (
                      <button key={v} type="button" onClick={() => setPlanForm({ ...planForm, race_distance_completed: v })}
                        style={{ padding: "6px 10px", borderRadius: "8px", border: `1.5px solid ${planForm.race_distance_completed === v ? "var(--accent-primary)" : "var(--border-color)"}`, background: planForm.race_distance_completed === v ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: planForm.race_distance_completed === v ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: planForm.race_distance_completed === v ? "700" : "500", fontSize: "12px", cursor: "pointer" }}>
                        {v}
                      </button>
                    ))}
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Days since race" : "Số ngày kể từ giải chạy"}
                    </label>
                    <input type="number" min="0" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "10px" }} placeholder="e.g. 3" value={planForm.days_since_race} onChange={e => setPlanForm({ ...planForm, days_since_race: e.target.value })} />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "How are you feeling?" : "Bạn cảm thấy như thế nào?"}
                    </label>
                    <select className="chat-input" style={{ borderRadius: "8px", width: "100%", height: "38px", padding: "0 8px", fontSize: "13px" }} value={planForm.recovery_feel} onChange={e => setPlanForm({ ...planForm, recovery_feel: e.target.value })}>
                      <option value="">{lang === "en" ? "Select..." : "Chọn..."}</option>
                      <option value="Feeling great, minimal soreness">{lang === "en" ? "Great, minimal soreness" : "Rất tốt, mỏi cơ tối thiểu"}</option>
                      <option value="Moderate fatigue, some soreness">{lang === "en" ? "Moderate fatigue" : "Mệt mỏi vừa phải"}</option>
                      <option value="Very fatigued — need real rest">{lang === "en" ? "Very fatigued" : "Rất mệt mỏi"}</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* ── Plan Start Date for Race/Distance ─────────────── */}
            {(planForm.plan_goal_category === "race" || planForm.plan_goal_category === "distance") && (
              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>{t("plan_start_date")}</label>
                <input type="date" className="chat-input" style={{ borderRadius: "8px", width: "100%", padding: "10px" }} value={planForm.plan_start_date} onChange={e => setPlanForm({ ...planForm, plan_start_date: e.target.value })} />
                <p style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "5px", margin: "5px 0 0 0" }}>
                  {lang === "en" 
                    ? "Week 1 of your plan will begin from this date (defaults to today)."
                    : "Tuần 1 trong kế hoạch của bạn sẽ bắt đầu từ ngày này (mặc định là hôm nay)."}
                </p>
              </div>
            )}

            {/* ── Schedule Preferences (shared) ─────────────────── */}
            <div style={{ marginBottom: "16px", padding: "14px", background: "rgba(255,255,255,0.15)", border: "1px solid var(--border-color)", borderRadius: "12px" }}>
              <label style={{ display: "block", fontSize: "12px", fontWeight: "700", marginBottom: "10px", color: "var(--text-secondary)", letterSpacing: "0.04em", textTransform: "uppercase" }}>
                {t("plan_schedule_prefs")}
              </label>

              <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                    {t("plan_days_per_week")}
                  </label>
                  <div style={{ display: "flex", gap: "6px" }}>
                    {[3, 4, 5, 6, 7].map(n => (
                      <button key={n} type="button" onClick={() => setPlanForm({ ...planForm, days_per_week: n })}
                        style={{ flex: 1, padding: "7px 0", borderRadius: "8px", border: `1.5px solid ${planForm.days_per_week === n ? "var(--accent-primary)" : "var(--border-color)"}`, background: planForm.days_per_week === n ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: planForm.days_per_week === n ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: "700", fontSize: "13px", cursor: "pointer" }}
                      >{n}</button>
                    ))}
                  </div>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                    {t("plan_long_run_day")}
                  </label>
                  <select className="chat-input" style={{ borderRadius: "8px", width: "100%", height: "38px", padding: "0 8px", fontSize: "13px" }}
                    value={planForm.long_run_day} onChange={e => setPlanForm({ ...planForm, long_run_day: e.target.value })}>
                    {["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].map(d => {
                      const label = lang === "vi" 
                        ? d.replace("Monday", "Thứ Hai").replace("Tuesday", "Thứ Ba").replace("Wednesday", "Thứ Tư").replace("Thursday", "Thứ Năm").replace("Friday", "Thứ Sáu").replace("Saturday", "Thứ Bảy").replace("Sunday", "Chủ Nhật")
                        : d;
                      return (
                        <option key={d} value={d}>{label}</option>
                      );
                    })}
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
                  {t("plan_preferred_days")}
                </label>
                <div style={{ display: "flex", gap: "5px", flexWrap: "wrap" }}>
                  {["Mon","Tue","Wed","Thu","Fri","Sat","Sun"].map((short, i) => {
                    const full = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][i];
                    const selected = planForm.preferred_days.includes(full);
                    const label = lang === "vi"
                      ? ["T2","T3","T4","T5","T6","T7","CN"][i]
                      : short;
                    return (
                      <button key={full} type="button"
                        onClick={() => {
                          const next = selected ? planForm.preferred_days.filter(d => d !== full) : [...planForm.preferred_days, full];
                          setPlanForm({ ...planForm, preferred_days: next });
                        }}
                        style={{ padding: "5px 10px", borderRadius: "8px", border: `1.5px solid ${selected ? "var(--accent-primary)" : "var(--border-color)"}`, background: selected ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: selected ? "var(--accent-primary)" : "var(--text-secondary)", fontWeight: selected ? "700" : "500", fontSize: "12px", cursor: "pointer" }}
                      >{label}</button>
                    );
                  })}
                </div>
                <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "5px", margin: "5px 0 0 0" }}>
                  {lang === "en" 
                    ? "The AI will prioritise these days when building your weekly schedule."
                    : "Trí tuệ nhân tạo (AI) sẽ ưu tiên xếp lịch tập vào các ngày này."}
                </p>
              </div>
            </div>

            {planErrorMsg && (
              <div style={{ color: "var(--accent-alert)", fontSize: "12px", padding: "10px", background: "rgba(239, 68, 68, 0.08)", borderRadius: "6px", marginBottom: "16px" }}>
                {planErrorMsg}
              </div>
            )}

            {backupActivePlan ? (
              <div style={{ display: "flex", gap: "10px", width: "100%" }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ flex: 1, height: "42px", fontSize: "13.5px" }}
                  onClick={() => {
                    setActivePlan(backupActivePlan);
                    setWorkouts(backupWorkouts);
                    setBackupActivePlan(null);
                    setBackupWorkouts([]);
                  }}
                >
                  {lang === "en" ? "◀ Go Back" : "◀ Quay lại"}
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ flex: 2, height: "42px", fontSize: "13.5px" }}
                  disabled={planLoading}
                >
                  {planLoading ? (lang === "en" ? "Building Plan..." : "Đang tạo Kế hoạch...") : (lang === "en" ? "🛠️ Build Custom Calendar" : "🛠️ Thiết lập Lịch tập tùy chỉnh")}
                </button>
              </div>
            ) : (
              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: "100%", height: "42px", fontSize: "13.5px" }}
                disabled={planLoading}
              >
                {planLoading ? (lang === "en" ? "Building Plan..." : "Đang tạo Kế hoạch...") : (lang === "en" ? "🛠️ Build Custom Calendar" : "🛠️ Thiết lập Lịch tập tùy chỉnh")}
              </button>
            )}
          </form>
        ) : (
          <div style={{ background: "rgba(255, 255, 255, 0.95)", border: "1px solid var(--border-color)", padding: isMobile ? "20px" : "32px", borderRadius: "16px" }}>
            {/* Header info */}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "16px" }}>
              <div>
                <h3 style={{ fontSize: isMobile ? "18px" : "22px", margin: 0 }}>
                  {activePlan.race_name}
                  {(getPlanDistance(activePlan) || getPlanElevation(activePlan)) && (
                    <span style={{ fontWeight: "normal", opacity: 0.85, fontSize: isMobile ? "14px" : "17px", marginLeft: "8px" }}>
                      ({getPlanDistance(activePlan) ? `${getPlanDistance(activePlan)}km` : ""}{getPlanDistance(activePlan) && getPlanElevation(activePlan) ? ", " : ""}{getPlanElevation(activePlan) ? `+${getPlanElevation(activePlan)}m` : ""})
                    </span>
                  )}
                </h3>
                <p style={{ color: "var(--text-secondary)", fontSize: "12px", marginTop: "2px", fontWeight: "500" }}>
                  {(() => {
                    const goal = activePlan.goal_type || "";
                    if (["start_running", "return", "recovery"].includes(goal)) {
                      return lang === "en" ? `Block ends: ${activePlan.race_date}` : `Kết thúc: ${activePlan.race_date}`;
                    } else {
                      return lang === "en" ? `Race Day: ${activePlan.race_date}` : `Ngày đua: ${activePlan.race_date}`;
                    }
                  })()} | {activePlan.goal_type === "finish" 
                    ? (lang === "en" ? "Simply Finish" : "Chỉ cần Hoàn thành")
                    : activePlan.goal_type === "time"
                      ? (lang === "en" ? "Time Target" : "Mục tiêu Thời gian")
                      : activePlan.goal_type === "optimal"
                        ? (lang === "en" ? "Optimal Performance" : "Hiệu suất Tối ưu")
                        : activePlan.goal_type.toUpperCase().replace("_", " ")}
                </p>
              </div>
              
              {!showExportOptions ? (
                <div style={{ display: "flex", gap: "10px", width: "100%", flexWrap: "wrap" }}>
                  <button
                    className="btn btn-primary"
                    style={{ flex: 1, minWidth: "120px", fontSize: "12px", height: "36px", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}
                    onClick={() => setShowExportOptions(true)}
                  >
                    {lang === "en" ? "Export Calendar" : "Xuất lịch tập"}
                  </button>
                  
                  <select
                    className="btn btn-secondary"
                    style={{
                      flex: 1,
                      minWidth: "120px",
                      fontSize: "12px",
                      height: "36px",
                      padding: "0 8px",
                      cursor: "pointer",
                      outline: "none",
                      border: "1px solid rgba(0, 0, 0, 0.1)",
                      background: "rgba(0, 0, 0, 0.06)",
                      color: "#111111",
                      textAlignLast: "center",
                      WebkitAppearance: "none",
                      MozAppearance: "none",
                      appearance: "none",
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                      borderRadius: "9999px",
                    }}
                    value=""
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val) handleSelectPlan(Number(val));
                    }}
                  >
                    <option value="" style={{ color: "var(--text-primary)" }}>
                      {lang === "en" ? "Load Recent Plan..." : "Tải lịch tập gần đây..."}
                    </option>
                    {recentPlans.length === 0 ? (
                      <option value="" disabled style={{ color: "var(--text-muted)" }}>
                        {lang === "en" ? "— No plans available —" : "— Không có lịch tập —"}
                      </option>
                    ) : (
                      recentPlans.map((p) => (
                        <option key={p.id} value={p.id} style={{ color: "var(--text-primary)" }}>
                          {formatPlanName(p)}
                        </option>
                      ))
                    )}
                  </select>

                  <button
                    className="btn btn-primary"
                    style={{ flex: 1, minWidth: "120px", fontSize: "13px", fontWeight: "600", height: "38px", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px", boxShadow: "0 4px 12px rgba(25, 206, 139, 0.2)" }}
                    onClick={() => {
                      setBackupActivePlan(activePlan);
                      setBackupWorkouts(workouts);
                      setActivePlan(null);
                    }}
                  >
                    <Plus size={16} weight="bold" />
                    {lang === "en" ? "New Plan" : "Kế hoạch mới"}
                  </button>
                </div>
              ) : (
                <div style={{
                  background: "rgba(255, 255, 255, 0.95)",
                  border: "1px solid var(--border-color)",
                  padding: "12px",
                  borderRadius: "10px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px",
                  width: "100%",
                  boxShadow: "0 4px 12px rgba(0,0,0,0.05)"
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "12px", fontWeight: "600", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "Select Preferred Workout Time:" : "Chọn thời gian tập ưa thích:"}
                    </span>
                    <button
                      type="button"
                      style={{ background: "none", border: "none", cursor: "pointer", fontSize: "12px", color: "var(--text-muted)" }}
                      onClick={() => setShowExportOptions(false)}
                    >✕</button>
                  </div>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <select
                      className="chat-input"
                      style={{ flex: 1, borderRadius: "6px", padding: "6px", height: "32px", fontSize: "12px" }}
                      value={exportTimePref}
                      onChange={(e) => setExportTimePref(e.target.value)}
                    >
                      <option value="all_day">{lang === "en" ? "All Day" : "Cả ngày"}</option>
                      <option value="morning">{lang === "en" ? "Morning" : "Buổi sáng"}</option>
                      <option value="afternoon">{lang === "en" ? "Afternoon" : "Buổi chiều"}</option>
                      <option value="evening">{lang === "en" ? "Evening" : "Buổi tối"}</option>
                    </select>
                    <a
                      href={`${API_BASE_URL}/api/coach/export-ics?plan_id=${activePlan.id}&race_date=${activePlan.race_date}&time_pref=${exportTimePref}&token=${typeof window !== 'undefined' ? localStorage.getItem('uphill_session_token') || '' : ''}`}
                      className="btn btn-primary"
                      style={{ fontSize: "12px", padding: "0 14px", height: "32px", display: "flex", alignItems: "center", textDecoration: "none", justifyContent: "center" }}
                      onClick={() => setShowExportOptions(false)}
                    >
                      {lang === "en" ? "Add to Calendar (.ics)" : "Thêm vào Lịch (.ics)"}
                    </a>
                  </div>
                </div>
              )}
            </div>

            {/* Week Selector Tabs */}
            <div style={{ display: "flex", gap: "6px", overflowX: "auto", paddingBottom: "8px", marginBottom: "16px" }}>
              {Array.from({ length: activePlan.total_weeks }).map((_, i) => {
                const w = i + 1;
                const firstWo = workouts.find((wo) => wo.week_number === w);
                const phase = firstWo ? firstWo.phase : "Training";
                const active = selectedWeek === w;
                const phaseDisplay = lang === "vi"
                  ? phase.replace("Base", "Base").replace("Build", "Build").replace("Taper", "Taper").replace("Peak", "Peak").replace("Recovery", "Phục hồi").replace("Transition", "Chuyển đổi")
                  : phase;
                return (
                  <button
                    key={w}
                    className={`btn ${active ? "btn-primary" : "btn-secondary"}`}
                    style={{
                      padding: "6px 12px",
                      borderRadius: "8px",
                      flexShrink: 0,
                      fontSize: "12px",
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      gap: "1px",
                      minWidth: "60px",
                      height: "44px",
                      background: active ? "var(--accent-primary)" : "rgba(255,255,255,0.25)",
                      borderColor: active ? "var(--accent-primary)" : "var(--border-color)",
                      color: active ? "#ffffff" : "var(--text-primary)"
                    }}
                    onClick={() => setSelectedWeek(w)}
                  >
                    <span>{lang === "en" ? `Wk ${w}` : `Tuần ${w}`}</span>
                    <span style={{ fontSize: "9px", opacity: 0.7 }}>{phaseDisplay}</span>
                  </button>
                );
              })}
            </div>

            {/* Weekly Volume Stats */}
            {(() => {
              const weekWorkouts = getWeekWorkouts(selectedWeek);
              const weeklyKm = weekWorkouts.reduce((sum, wo) => sum + (wo.distance_km || 0), 0);
              const weeklyMins = weekWorkouts.reduce((sum, wo) => sum + (wo.duration_minutes || 0), 0);
              const weeklyHours = parseFloat((weeklyMins / 60).toFixed(1));

              return (
                <div style={{ marginBottom: "16px" }}>
                  <div className="card" style={{ 
                    padding: "12px 16px", 
                    background: "rgba(255, 255, 255, 0.45)", 
                    border: "1px solid var(--border-color)", 
                    borderRadius: "12px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "4px"
                  }}>
                    <span style={{ fontSize: "10px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: "700" }}>
                      {lang === "en" ? `Weekly Volume (Wk ${selectedWeek})` : `Thể tích tuần (Tuần ${selectedWeek})`}
                    </span>
                    <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                      <span style={{ fontSize: "18px", fontWeight: "800", color: "var(--accent-primary)" }}>{weeklyKm.toFixed(1)} km</span>
                      <span style={{ fontSize: "13px", color: "var(--text-muted)", fontWeight: "600" }}>/ {weeklyHours} {lang === "en" ? "hrs" : "giờ"}</span>
                    </div>
                  </div>
                </div>
              );
            })()}



            {/* Week Workouts Grid */}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {getWeekWorkouts(selectedWeek).map((wo) => {
                const rest = wo.type === "Rest";
                const dayOfWeekShort = lang === "vi"
                  ? wo.day_of_week.replace("Monday", "T2").replace("Tuesday", "T3").replace("Wednesday", "T4").replace("Thursday", "T5").replace("Friday", "T6").replace("Saturday", "T7").replace("Sunday", "CN")
                  : wo.day_of_week.slice(0, 3);
                const woTypeTranslated = wo.type === "Rest" ? (lang === "en" ? "Rest" : "Nghỉ ngơi") : wo.type;

                return (
                  <div
                    key={wo.id}
                    style={{
                      background: rest ? "rgba(255,255,255,0.05)" : "var(--bg-card)",
                      backdropFilter: "blur(20px)",
                      WebkitBackdropFilter: "blur(20px)",
                      boxShadow: "inset 0 1px 0 rgba(255,255,255,0.4), 0 8px 24px rgba(0,0,0,0.05)",
                      border: "1px solid",
                      borderColor: wo.is_completed ? "var(--accent-success)" : "var(--border-color)",
                      borderRadius: "12px",
                      padding: isMobile ? "14px" : "20px",
                      opacity: rest ? 0.75 : 1,
                      display: "grid",
                      gridTemplateColumns: isMobile ? "1fr" : "70px 1.6fr 1.1fr",
                      gap: isMobile ? "10px" : "16px",
                      alignItems: "start",
                    }}
                  >
                    {/* Day name & Status Checkbox */}
                    <div style={{
                      display: "flex",
                      flexDirection: isMobile ? "row" : "column",
                      alignItems: "center",
                      justifyContent: isMobile ? "space-between" : "center",
                      textAlign: "center",
                      borderBottom: isMobile ? "1px solid rgba(0,0,0,0.05)" : "none",
                      paddingBottom: isMobile ? "8px" : 0,
                    }}>
                      <div style={{ display: "flex", gap: "8px", alignItems: "baseline" }}>
                        <span style={{ fontWeight: "700", fontSize: "15px" }}>{dayOfWeekShort}</span>
                        <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>{getWorkoutDate(wo)}</span>
                      </div>
                      {!rest && (
                        <input
                          type="checkbox"
                          style={{ width: "18px", height: "18px", accentColor: "var(--accent-success)", cursor: "pointer", margin: 0 }}
                          checked={wo.is_completed === 1}
                          onChange={(e) => handleToggleComplete(wo.id, e.target.checked)}
                        />
                      )}
                    </div>

                    {/* Workout Details */}
                    <div>
                      <div style={{ display: "flex", gap: "6px", alignItems: "center", flexWrap: "wrap", marginBottom: "6px" }}>
                        <h4 style={{ fontSize: isMobile ? "15px" : "17px", margin: 0 }}>{wo.title}</h4>
                        <span className="badge" style={{ margin: 0, fontSize: "9px", padding: "2px 6px" }}>{woTypeTranslated}</span>
                      </div>
                      <WorkoutDescription description={wo.description || ""} />
                      {wo.fueling_tip && (
                        <div style={{ background: "rgba(16, 185, 129, 0.03)", borderLeft: "2px solid var(--accent-primary)", padding: "6px 10px", borderRadius: "4px", fontSize: "12px" }}>
                          {wo.fueling_tip}
                        </div>
                      )}
                    </div>

                    {/* Target Metrics Column */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "12.5px" }}>
                      {wo.duration_minutes > 0 && (
                        <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(0,0,0,0.04)", paddingBottom: "4px" }}>
                          <span style={{ color: "var(--text-muted)", fontWeight: "600" }}>
                            {lang === "en" ? "Target Time:" : "Thời gian mục tiêu:"}
                          </span>
                          <span style={{ fontWeight: "700" }}>{wo.duration_minutes}m</span>
                        </div>
                      )}
                      {wo.distance_km !== undefined && wo.distance_km > 0 && (
                        <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(0,0,0,0.04)", paddingBottom: "4px" }}>
                          <span style={{ color: "var(--text-muted)", fontWeight: "600" }}>
                            {lang === "en" ? "Est. Dist:" : "Cự ly ước tính:"}
                          </span>
                          <span style={{ fontWeight: "700", color: "var(--accent-primary)" }}>{wo.distance_km}km</span>
                        </div>
                      )}
                      {wo.target_pace && wo.target_pace.trim() !== "" && (
                        <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(0,0,0,0.04)", paddingBottom: "4px" }}>
                          <span style={{ color: "var(--text-muted)", fontWeight: "600" }}>
                            {lang === "en" ? "Target Pace:" : "Pace mục tiêu:"}
                          </span>
                          <span style={{ fontWeight: "700", color: "var(--accent-success)" }}>{wo.target_pace}</span>
                        </div>
                      )}
                      {wo.target_hr_range && (
                        <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(0,0,0,0.04)", paddingBottom: "4px" }}>
                          <span style={{ color: "var(--text-muted)", fontWeight: "600" }}>
                            {lang === "en" ? "HR Limit:" : "Giới hạn HR:"}
                          </span>
                          <span style={{ fontWeight: "700", color: "var(--accent-secondary)" }}>{wo.target_hr_range}</span>
                        </div>
                      )}
                      {wo.treadmill_incline > 0 && (
                        <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                          <div style={{ display: "flex", justifyContent: "space-between" }}>
                            <span style={{ color: "var(--text-muted)", fontWeight: "600" }}>
                              {lang === "en" ? "Incline:" : "Độ dốc (Incline):"}
                            </span>
                            <span style={{ fontWeight: "700" }}>{wo.treadmill_incline}%</span>
                          </div>
                          <div style={{ display: "flex", justifyContent: "space-between" }}>
                            <span style={{ color: "var(--text-muted)", fontWeight: "600" }}>
                              {lang === "en" ? "Speed:" : "Tốc độ (Speed):"}
                            </span>
                            <span style={{ fontWeight: "700" }}>{wo.treadmill_speed}kph</span>
                          </div>
                        </div>
                      )}
                      {rest && (
                        <div style={{ display: "flex", justifyContent: "center", padding: "6px", background: "rgba(0,0,0,0.02)", borderRadius: "6px" }}>
                          <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                            {lang === "en" ? "Rest Day" : "Ngày nghỉ ngơi"}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderTools = (isMobile: boolean) => {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {/* Card 1: Precision Fueling Engine (Launch Button) */}
        <div className="card" style={{ padding: isMobile ? "16px" : "24px", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", textAlign: "center", cursor: "pointer", border: "1px solid var(--accent-primary)" }} onClick={() => setIsNutritionLabOpen(true)}>
          <BowlFood size={48} color="var(--accent-primary)" weight="duotone" style={{ marginBottom: "16px" }} />
          <h3 style={{ fontSize: isMobile ? "18px" : "20px", marginBottom: "8px", color: "var(--text-primary)" }}>
            Nutrition Lab
          </h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px", marginBottom: "0" }}>
            {lang === "en" 
              ? "Launch the metabolic command center to calculate custom gel recipes."
              : "Mở trung tâm dinh dưỡng để tính toán công thức gel tùy chỉnh."}
          </p>
        </div>

        {/* Card 2: Gear Finder (Launch Button) */}
        <div className="card" style={{ padding: isMobile ? "16px" : "24px", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", textAlign: "center", cursor: "pointer", border: "1px solid var(--accent-primary)" }} onClick={() => setIsGearVaultOpen(true)}>
          <Sneaker size={48} color="var(--accent-primary)" weight="duotone" style={{ marginBottom: "16px" }} />
          <h3 style={{ fontSize: isMobile ? "18px" : "20px", marginBottom: "8px", color: "var(--text-primary)" }}>
            Gear Finder
          </h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px", marginBottom: "0" }}>
            {lang === "en" 
              ? "Launch the technical equipment matching vault."
              : "Mở kho tìm kiếm trang bị kỹ thuật."}
          </p>
        </div>

        {/* Card 3: GPX Checkpoint Pacer */}
        <div className="card" style={{ padding: isMobile ? "16px" : "24px" }}>
          <h3 style={{ fontSize: isMobile ? "16px" : "18px", marginBottom: "8px", color: "var(--accent-primary)" }}>GPX Checkpoint Pacer</h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "12.5px", marginBottom: "16px" }}>
            {lang === "en" 
              ? "Upload a course GPX file to parse checkpoint metrics, or a workout FIT file to view telemetry."
              : "Tải lên tệp GPX đường chạy để phân tích thông số checkpoint, hoặc tệp FIT buổi tập để xem dữ liệu đo lường."}
          </p>

          <div className="dropzone" onClick={handleDropzoneClick} style={{ padding: "12px 10px", gap: "4px", marginBottom: "16px", cursor: "pointer" }}>
            <div className="dropzone-icon" style={{ fontSize: "18px" }}>📥</div>
            <div className="dropzone-title" style={{ fontSize: "12px" }}>
              {lang === "en" ? "Upload GPX or FIT" : "Tải lên tệp GPX hoặc FIT"}
            </div>
            <div className="dropzone-subtitle" style={{ fontSize: "10px", color: "var(--text-muted)" }}>
              {lang === "en" ? "Drag or tap here" : "Kéo hoặc chạm vào đây"}
            </div>
            {uploadedFileName && (
              <div style={{ color: "var(--accent-primary)", fontSize: "11px", fontWeight: "600", marginTop: "2px" }}>
                {uploadedFileName}
              </div>
            )}
          </div>

          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden-file-input"
            accept=".fit,.gpx"
            style={{ display: "none" }}
          />

          {parserLoading && (
            <div style={{ textTransform: "lowercase", textAlign: "center", color: "var(--accent-secondary)", fontSize: "11px", marginBottom: "12px" }}>
              {lang === "en" ? "Extracting telemetry..." : "Đang trích xuất dữ liệu đo lường..."}
            </div>
          )}

          {parserErrorMsg && (
            <div style={{ color: "var(--accent-alert)", fontSize: "11px", padding: "8px", background: "rgba(239, 68, 68, 0.08)", borderRadius: "6px", marginBottom: "12px" }}>
              {parserErrorMsg}
            </div>
          )}

          {parsedSummary && (
            <div style={{ padding: "10px", background: "rgba(255,255,255,0.15)", border: "1px solid var(--border-color)", borderRadius: "8px", marginBottom: "16px" }}>
              <div style={{ fontWeight: "700", fontSize: "11.5px", color: "var(--accent-secondary)", marginBottom: "6px" }}>
                {lang === "en" ? "Parsed Telemetry" : "Dữ liệu Đo lường đã Phân tích"}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                <div className="metric-item" style={{ padding: "6px" }}>
                  <div className="metric-label" style={{ fontSize: "9px" }}>
                    {lang === "en" ? "Distance" : "Cự ly"}
                  </div>
                  <div className="metric-value" style={{ fontSize: "12px" }}>{parsedSummary.distance_km} km</div>
                </div>
                <div className="metric-item" style={{ padding: "6px" }}>
                  <div className="metric-label" style={{ fontSize: "9px" }}>
                    {lang === "en" ? "Elevation" : "Độ cao"}
                  </div>
                  <div className="metric-value" style={{ fontSize: "12px" }}>{parsedSummary.elevation_gain_m} m</div>
                </div>
              </div>
            </div>
          )}

          <div style={{ marginBottom: "12px" }}>
            <label style={{ display: "block", fontSize: "11.5px", color: "var(--text-muted)", marginBottom: "4px" }}>
              {lang === "en" ? "Target Flat Pace (min/km)" : "Flat Pace Mục tiêu (min/km)"}
            </label>
            <input
              type="number"
              step="0.1"
              className="chat-input"
              style={{ borderRadius: "8px", width: "100%", padding: "8px" }}
              value={targetFlatPace}
              onChange={(e) => setTargetFlatPace(e.target.value)}
            />
          </div>

          <button
            className="btn btn-primary"
            style={{ 
              width: "100%", marginBottom: "12px", height: "36px", fontSize: "12.5px",
              ...(gpxCheckpoints.length === 0 ? { filter: "blur(3px)", opacity: 0.7, pointerEvents: "none" } : {})
            }}
            onClick={handleCalculatePacing}
            disabled={gpxCheckpoints.length === 0 || pacingLoading}
          >
            {pacingLoading 
              ? (lang === "en" ? "Calculating Splits..." : "Đang tính toán checkpoint...") 
              : gpxCheckpoints.length === 0 
                ? (lang === "en" ? "Upload GPX First" : "Cần tải lên GPX trước") 
                : (lang === "en" ? "Generate Splits" : "Tạo Checkpoint Pace")}
          </button>

          {pacedCheckpoints.length > 0 && (
            <div style={{ maxHeight: "160px", overflowY: "auto", border: "1px solid var(--border-color)", borderRadius: "8px", background: "rgba(255, 255, 255, 0.2)" }}>
              <table style={{ width: "100%", fontSize: "11px", borderCollapse: "collapse", textAlign: "left" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-muted)" }}>
                    <th style={{ padding: "6px" }}>{lang === "en" ? "Name" : "Tên"}</th>
                    <th style={{ padding: "6px" }}>{lang === "en" ? "Dist" : "Cự ly"}</th>
                    <th style={{ padding: "6px" }}>Pace</th>
                    <th style={{ padding: "6px" }}>{lang === "en" ? "Split" : "Tách (Split)"}</th>
                  </tr>
                </thead>
                <tbody>
                  {pacedCheckpoints.map((cp, idx) => (
                    <tr key={idx} style={{ borderBottom: "1px solid rgba(0,0,0,0.02)" }}>
                      <td style={{ padding: "6px", fontWeight: "600" }}>{cp.name}</td>
                      <td style={{ padding: "6px" }}>{cp.distance_km}k</td>
                      <td style={{ padding: "6px" }}>{cp.target_pace}/k</td>
                      <td style={{ padding: "700", fontWeight: "700" }}>{cp.split_time}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    );
  };

  const renderActiveTab = (isMobile: boolean) => {
    switch (activeTab) {
      case "home":
        return renderHome(isMobile);
      case "about":
        return renderAboutUs(isMobile);
      case "chat":
        return renderChat(isMobile);
      case "planner":
        return renderPlanner(isMobile);
      case "tools":
        return renderTools(isMobile);
      case "knowledge":
        return renderKnowledge(isMobile);
      default:
        return renderHome(isMobile);
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

  const renderAuthModal = () => {
    if (!authModalOpen) return null;
    const DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];
    const inputStyle: React.CSSProperties = { borderRadius: "8px", width: "100%", height: "36px", margin: 0, padding: "0 10px", fontSize: "13px", background: "transparent", border: "1px solid var(--border-color)", color: "var(--text-primary)", boxSizing: "border-box" as const };
    const labelStyle: React.CSSProperties = { display: "block", fontSize: "11.5px", fontWeight: "600", color: "var(--text-muted)", marginBottom: "5px" };
    const cardBtnStyle = (selected: boolean): React.CSSProperties => ({
      flex: "1 1 auto", minWidth: "120px", padding: "10px 12px", borderRadius: "10px", border: `1.5px solid ${selected ? "var(--accent-primary)" : "var(--border-color)"}`,
      background: selected ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", color: selected ? "var(--accent-primary)" : "var(--text-primary)",
      fontWeight: selected ? "700" : "500", fontSize: "12.5px", cursor: "pointer", textAlign: "center" as const, transition: "all 0.15s"
    });

    return (
      <div style={{ position: "fixed", inset: 0, background: "rgba(255,255,255,0.35)", backdropFilter: "blur(16px)", display: "flex", justifyContent: "center", alignItems: "center", zIndex: 1000, padding: "20px" }}>
        <div style={{ background: "var(--bg-card)", backdropFilter: "blur(30px)", border: "1px solid var(--border-color)", borderRadius: "24px", padding: "32px", width: "100%", maxWidth: "480px", maxHeight: "90vh", overflowY: "auto", boxShadow: "0 20px 60px rgba(0,0,0,0.1)", position: "relative", color: "var(--text-primary)" }}>

          {/* Header */}
          <button 
            onClick={() => setAuthModalOpen(false)} 
            style={{ position: "absolute", top: "20px", right: "20px", background: "transparent", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: "4px", display: "flex", alignItems: "center", justifyContent: "center", borderRadius: "50%", transition: "all 0.2s" }}
            onMouseOver={(e) => e.currentTarget.style.color = "var(--text-primary)"}
            onMouseOut={(e) => e.currentTarget.style.color = "var(--text-muted)"}
          >
            <XCircle size={24} weight="duotone" />
          </button>
          <div style={{ textAlign: "center", marginBottom: "24px" }}>
            <div style={{ fontSize: "26px", fontWeight: "800", letterSpacing: "-0.03em" }}>Uphill<span style={{ color: "var(--accent-primary)" }}>.AI</span></div>
            <p style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "4px" }}>Your elite running intelligence coach</p>
          </div>

          {authErrorMsg && (
            <div style={{ color: "#ef4444", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.15)", borderRadius: "8px", padding: "10px", fontSize: "12.5px", marginBottom: "16px" }}>
              <Warning weight="fill" style={{marginRight: "4px", verticalAlign: "middle"}}/> {authErrorMsg}
            </div>
          )}

          {/* OAuth Buttons (always visible) */}
          <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "16px" }}>
            <div id="google-signin-btn" style={{ width: "100%", height: "40px", minHeight: "40px", display: "flex", justifyContent: "center" }} />
          </div>

          {/* Divider */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
            <div style={{ flex: 1, height: "1px", background: "rgba(0,0,0,0.08)" }} />
            <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>or</span>
            <div style={{ flex: 1, height: "1px", background: "rgba(0,0,0,0.08)" }} />
          </div>

          {/* Tab switcher */}
          <div style={{ display: "flex", background: "rgba(255,255,255,0.4)", border: "1px solid var(--border-color)", padding: "3px", borderRadius: "10px", marginBottom: "18px" }}>
            {(["signin", "register"] as const).map(tab => (
              <button key={tab} type="button" onClick={() => { setAuthTab(tab); setAuthErrorMsg(""); }}
                style={{ flex: 1, height: "30px", fontSize: "12px", borderRadius: "8px", border: "none", background: authTab === tab ? "var(--accent-primary)" : "transparent", color: authTab === tab ? "#fff" : "var(--text-secondary)", fontWeight: "600", cursor: "pointer", transition: "all 0.15s" }}>
                {tab === "signin" ? "Sign In" : "Create Account"}
              </button>
            ))}
          </div>

          {authTab === "signin" ? (
            <form onSubmit={handleEmailLogin} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={labelStyle}>Email</label>
                <input type="email" style={inputStyle} className="chat-input" placeholder="you@example.com" value={emailInput} onChange={e => setEmailInput(e.target.value)} required />
              </div>
              <div>
                <label style={labelStyle}>Password</label>
                <div style={{ position: "relative" }}>
                  <input type={showPassword ? "text" : "password"} style={{ ...inputStyle, paddingRight: "40px" }} className="chat-input" placeholder="Your password" value={passwordInput} onChange={e => setPasswordInput(e.target.value)} required />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} style={{ position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: "14px", color: "var(--text-muted)" }}>{showPassword ? "👁️" : "🙈"}</button>
                </div>
              </div>
              <button type="submit" className="btn btn-primary" style={{ width: "100%", height: "40px", fontSize: "13.5px", marginTop: "4px" }} disabled={authLoading}>
                {authLoading ? "Signing in..." : "Sign In"}
              </button>
            </form>
          ) : (
            <form onSubmit={handleRegister} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={labelStyle}>Full Name</label>
                <input type="text" style={inputStyle} className="chat-input" placeholder="Alex Runner" value={nameInput} onChange={e => setNameInput(e.target.value)} required />
              </div>
              <div>
                <label style={labelStyle}>Email</label>
                <input type="email" style={inputStyle} className="chat-input" placeholder="you@example.com" value={emailInput} onChange={e => setEmailInput(e.target.value)} required />
              </div>
              <div>
                <label style={labelStyle}>Password</label>
                <div style={{ position: "relative" }}>
                  <input type={showPassword ? "text" : "password"} style={{ ...inputStyle, paddingRight: "40px" }} className="chat-input" placeholder="Min 8 characters" value={passwordInput} onChange={e => setPasswordInput(e.target.value)} required minLength={8} />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} style={{ position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: "14px", color: "var(--text-muted)" }}>{showPassword ? "👁️" : "🙈"}</button>
                </div>
              </div>
              <div>
                <label style={labelStyle}>Confirm Password</label>
                <input type="password" style={inputStyle} className="chat-input" placeholder="Repeat password" value={confirmPasswordInput} onChange={e => setConfirmPasswordInput(e.target.value)} required minLength={8} />
              </div>
              <button type="submit" className="btn btn-primary" style={{ width: "100%", height: "40px", fontSize: "13.5px", marginTop: "4px" }} disabled={authLoading}>
                {authLoading ? "Creating account..." : "Create Account"}
              </button>
            </form>
          )}
          {authLoading && <div style={{ textAlign: "center", color: "var(--accent-secondary)", fontSize: "11px", marginTop: "12px" }}>Authenticating...</div>}
        </div>
      </div>
    );
  };

  // ─── Onboarding Wizard ────────────────────────────────────────────────────
  const renderOnboardingWizard = () => {
    if (!onboardingOpen || !user) return null;
    const DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];
    const goal = onboardingAnswers.goal_type;
    const isRaceOrDist = goal === "race" || goal === "distance";
    const isStart = goal === "start_running";
    const isReturn = goal === "return";
    const isRecovery = goal === "recovery";

    // Build steps array based on goal
    const steps = ["dob", "goal"];
    if (isRaceOrDist) steps.push("fitness", "injury", "target", "schedule");
    else if (isStart) steps.push("schedule");
    else if (isReturn) steps.push("return_questions", "schedule");
    else if (isRecovery) steps.push("recovery_questions", "schedule");
    else if (!goal) { /* no extra steps yet */ }
    else steps.push("schedule");
    steps.push("generate");

    const totalSteps = steps.length;
    const currentStepKey = steps[onboardingStep] || "dob";
    const inputS: React.CSSProperties = { borderRadius: "8px", width: "100%", height: "36px", margin: 0, padding: "0 10px", fontSize: "13px", background: "transparent", border: "1px solid var(--border-color)", color: "var(--text-primary)", boxSizing: "border-box" };
    const labelS: React.CSSProperties = { display: "block", fontSize: "12px", fontWeight: "600", color: "var(--text-muted)", marginBottom: "6px" };
    const optBtn = (val: string, label: string, emoji?: string): React.CSSProperties => ({
      padding: "10px 14px", borderRadius: "10px", border: `1.5px solid ${onboardingAnswers[currentStepKey === "goal" ? "goal_type" : currentStepKey] === val ? "var(--accent-primary)" : "var(--border-color)"}`,
      background: onboardingAnswers[currentStepKey === "goal" ? "goal_type" : currentStepKey] === val ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)",
      color: onboardingAnswers[currentStepKey === "goal" ? "goal_type" : currentStepKey] === val ? "var(--accent-primary)" : "var(--text-primary)",
      fontWeight: onboardingAnswers[currentStepKey === "goal" ? "goal_type" : currentStepKey] === val ? "700" : "500",
      fontSize: "13px", cursor: "pointer", textAlign: "center" as const, transition: "all 0.15s"
    });
    const setAns = (key: string, val: any) => setOnboardingAnswers(prev => ({ ...prev, [key]: val }));
    const nextStep = () => setOnboardingStep(s => Math.min(s + 1, totalSteps - 1));
    const prevStep = () => setOnboardingStep(s => Math.max(s - 1, 0));

    const toggleDay = (day: string) => {
      setOnboardingAnswers(prev => {
        const days = [...(prev.preferred_run_days || [])];
        if (days.includes(day)) return { ...prev, preferred_run_days: days.filter(d => d !== day) };
        return { ...prev, preferred_run_days: [...days, day] };
      });
    };

    const renderStep = () => {
      switch (currentStepKey) {
        case "dob":
          return (
            <div>
              <div style={{ fontSize: "22px", fontWeight: "800", marginBottom: "6px" }}>
                {lang === "en" ? `Welcome, ${user.name.split(" ")[0]}! 🎉` : `Chào mừng, ${user.name.split(" ")[0]}! 🎉`}
              </div>
              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "20px" }}>
                {lang === "en" ? "Let's set up your personalised training plan. First, select your language and when you were born." : "Hãy cùng thiết lập kế hoạch tập luyện cá nhân hóa của bạn. Đầu tiên, chọn ngôn ngữ của bạn và nhập ngày sinh."}
              </p>
              
              <div style={{ marginBottom: "20px" }}>
                <label style={labelS}>{lang === "en" ? "Language" : "Ngôn ngữ"}</label>
                <div style={{ display: "flex", background: "rgba(255,255,255,0.4)", border: "1px solid var(--border-color)", padding: "3px", borderRadius: "10px" }}>
                  {(["en", "vi"] as const).map(l => (
                    <button key={l} type="button" onClick={() => handleSetLang(l)}
                      style={{ flex: 1, height: "30px", fontSize: "12px", borderRadius: "8px", border: "none", background: lang === l ? "var(--accent-primary)" : "transparent", color: lang === l ? "#fff" : "var(--text-secondary)", fontWeight: "600", cursor: "pointer", transition: "all 0.15s" }}>
                      {l === "en" ? "🇬🇧 English" : "🇻🇳 Tiếng Việt"}
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ marginBottom: "10px" }}>
                <label style={labelS}>{t("onboard_dob")}</label>
                <input type="date" style={inputS} className="chat-input" value={onboardingAnswers.dob} onChange={e => setAns("dob", e.target.value)} />
                <p style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "8px" }}>
                  {lang === "en" ? "Used to estimate your maximum heart rate (220 − age)" : "Được sử dụng để ước tính nhịp tim tối đa của bạn (220 − số tuổi)"}
                </p>
              </div>
            </div>
          );
        case "goal":
          return (
            <div>
              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>
                {lang === "en" ? "What's your goal?" : "Mục tiêu của bạn là gì?"}
              </div>
              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "20px" }}>
                {lang === "en" ? "Your training plan will be designed specifically around this." : "Kế hoạch tập luyện của bạn sẽ được thiết kế riêng xung quanh mục tiêu này."}
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {[
                  { val: "race", Icon: Trophy, label: lang === "en" ? "Race (target event)" : "Giải chạy (sự kiện mục tiêu)" },
                  { val: "distance", Icon: Target, label: lang === "en" ? "Run a Specific Distance" : "Chạy một cự ly cụ thể" },
                  { val: "start_running", Icon: Sneaker, label: lang === "en" ? "Start Running" : "Bắt đầu chạy bộ" },
                  { val: "return", Icon: PersonSimpleRun, label: lang === "en" ? "Get Back to Running" : "Tập luyện chạy bộ trở lại" },
                  { val: "recovery", Icon: Bed, label: lang === "en" ? "Post-Race Recovery" : "Phục hồi sau cuộc đua" },
                ].map(({ val, Icon, label }) => (
                  <button key={val} type="button"
                    onClick={() => {
                      setAns("goal_type", val);
                      if (val === "start_running") {
                        setAns("zone2_pace_min", "8:30");
                        setAns("zone2_pace_max", "7:30");
                      } else {
                        if (onboardingAnswers.zone2_pace_min === "8:30") setAns("zone2_pace_min", "6:30");
                        if (onboardingAnswers.zone2_pace_max === "7:30") setAns("zone2_pace_max", "5:45");
                      }
                    }}
                    style={{ ...optBtn(val, label), display: "flex", alignItems: "center", gap: "10px", textAlign: "left" as const }}>
                    <Icon size={24} color="var(--accent-primary)" weight="duotone" />
                    <span>{label}</span>
                    {onboardingAnswers.goal_type === val && <span style={{ marginLeft: "auto" }}>✓</span>}
                  </button>
                ))}
              </div>
            </div>
          );
        case "fitness":
          return (
            <div>
              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>
                {lang === "en" ? "Current Fitness 💓" : "Thể trạng hiện tại 💓"}
              </div>
              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "16px" }}>
                {lang === "en" ? "How would you like to input your heart rate zones?" : "Bạn muốn thiết lập các vùng nhịp tim của mình như thế nào?"}
              </p>
              <div style={{ display: "flex", background: "rgba(255,255,255,0.4)", border: "1px solid var(--border-color)", padding: "3px", borderRadius: "10px", marginBottom: "16px" }}>
                {(["estimate", "manual"] as const).map(m => (
                  <button key={m} type="button" onClick={() => setAns("fitness_input_mode", m)}
                    style={{ flex: 1, height: "30px", fontSize: "12px", borderRadius: "8px", border: "none", background: onboardingAnswers.fitness_input_mode === m ? "var(--accent-primary)" : "transparent", color: onboardingAnswers.fitness_input_mode === m ? "#fff" : "var(--text-secondary)", fontWeight: "600", cursor: "pointer" }}>
                    {m === "estimate" 
                      ? (lang === "en" ? "⚡ Estimate from race" : "⚡ Ước tính từ giải chạy") 
                      : (lang === "en" ? "🧪 I know my zones" : "🧪 Tôi đã biết các vùng nhịp tim")}
                  </button>
                ))}
              </div>
              {onboardingAnswers.fitness_input_mode === "estimate" ? (
                <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 1fr", gap: "8px" }}>
                  <div>
                    <label style={labelS}>{lang === "en" ? "Race Distance" : "Cự ly giải chạy"}</label>
                    <select className="chat-input" style={{ ...inputS }} value={onboardingAnswers.race_distance} onChange={e => setAns("race_distance", e.target.value)}>
                      <option value="5k">5k</option><option value="10k">10k</option><option value="half">Half Marathon</option><option value="marathon">Marathon</option>
                    </select>
                  </div>
                  <div><label style={labelS}>{lang === "en" ? "Hours" : "Giờ"}</label><input type="number" min="0" className="chat-input" style={inputS} value={onboardingAnswers.race_time_hours} onChange={e => setAns("race_time_hours", e.target.value)} /></div>
                  <div><label style={labelS}>{lang === "en" ? "Minutes" : "Phút"}</label><input type="number" min="0" max="59" className="chat-input" style={inputS} value={onboardingAnswers.race_time_minutes} onChange={e => setAns("race_time_minutes", e.target.value)} /></div>
                </div>
              ) : (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <div><label style={labelS}>AeT HR (bpm)</label><input type="number" className="chat-input" style={inputS} placeholder="135" value={onboardingAnswers.aet_hr} onChange={e => setAns("aet_hr", e.target.value)} /></div>
                  <div><label style={labelS}>AnT HR (bpm)</label><input type="number" className="chat-input" style={inputS} placeholder="165" value={onboardingAnswers.ant_hr} onChange={e => setAns("ant_hr", e.target.value)} /></div>
                  <div><label style={labelS}>Max HR (bpm)</label><input type="number" className="chat-input" style={inputS} placeholder="185" value={onboardingAnswers.max_hr} onChange={e => setAns("max_hr", e.target.value)} /></div>
                  <div><label style={labelS}>Resting HR (bpm)</label><input type="number" className="chat-input" style={inputS} placeholder="60" value={onboardingAnswers.resting_hr} onChange={e => setAns("resting_hr", e.target.value)} /></div>
                </div>
              )}

              <div style={{ marginTop: "16px", borderTop: "1px solid var(--border-color)", paddingTop: "16px" }}>
                <label style={{ ...labelS, marginBottom: "8px" }}>
                  {lang === "en" ? "Zone 2 Pace Range (Aerobic Pacing)" : "Khoảng tốc độ Zone 2 (Tốc độ hiếu khí)"}
                </label>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <div>
                    <label style={{ ...labelS, fontSize: "11px", fontWeight: "normal" }}>{lang === "en" ? "Slowest Pace (min/km)" : "Tốc độ chậm nhất (phút/km)"}</label>
                    <input type="text" className="chat-input" style={inputS} placeholder="e.g. 6:30" value={onboardingAnswers.zone2_pace_min} onChange={e => setAns("zone2_pace_min", e.target.value)} />
                  </div>
                  <div>
                    <label style={{ ...labelS, fontSize: "11px", fontWeight: "normal" }}>{lang === "en" ? "Fastest Pace (min/km)" : "Tốc độ nhanh nhất (phút/km)"}</label>
                    <input type="text" className="chat-input" style={inputS} placeholder="e.g. 5:45" value={onboardingAnswers.zone2_pace_max} onChange={e => setAns("zone2_pace_max", e.target.value)} />
                  </div>
                </div>
                <p style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "6px", lineHeight: "1.3" }}>
                  {lang === "en" ? "This is your conversational running pace range." : "Đây là khoảng tốc độ chạy mà bạn vẫn có thể nói chuyện thoải mái."}
                </p>
              </div>
            </div>
          );
        case "injury":
          return (
            <div>
              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>
                {lang === "en" ? "Injury History 🩺" : "Lịch sử chấn thương 🩺"}
              </div>
              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "20px" }}>
                {lang === "en" ? "This helps us pace your plan's load progression carefully." : "Điều này giúp chúng tôi điều chỉnh tiến trình tăng tải của kế hoạch một cách cẩn thận."}
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {[
                  { val: "rarely", label: lang === "en" ? "Rarely or never injured" : "Hiếm khi hoặc không bao giờ chấn thương", sub: lang === "en" ? "I bounce back quickly from hard efforts" : "Tôi phục hồi nhanh chóng sau những nỗ lực nặng" },
                  { val: "minor", label: lang === "en" ? "Minor or past significant injury" : "Chấn thương nhẹ hoặc từng bị chấn thương nặng", sub: lang === "en" ? "Mostly resolved, occasionally careful" : "Hầu như đã khỏi hoàn toàn, thỉnh thoảng cần lưu ý" },
                  { val: "frequent", label: lang === "en" ? "Frequently or recently injured" : "Thường xuyên hoặc mới bị chấn thương", sub: lang === "en" ? "Need careful, conservative buildup" : "Cần tích lũy khối lượng cẩn thận và thận trọng" },
                  { val: "prefer_not", label: lang === "en" ? "Prefer not to say" : "Không muốn chia sẻ", sub: "" },
                ].map(({ val, label, sub }) => (
                  <button key={val} type="button" onClick={() => setAns("injury_history", val)}
                    style={{ padding: "12px 14px", borderRadius: "10px", border: `1.5px solid ${onboardingAnswers.injury_history === val ? "var(--accent-primary)" : "var(--border-color)"}`, background: onboardingAnswers.injury_history === val ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", cursor: "pointer", textAlign: "left" as const }}>
                    <div style={{ fontWeight: "600", fontSize: "13px", color: onboardingAnswers.injury_history === val ? "var(--accent-primary)" : "var(--text-primary)" }}>{label}</div>
                    {sub && <div style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "3px" }}>{sub}</div>}
                  </button>
                ))}
              </div>
            </div>
          );
        case "target":
          return (
            <div>
              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>
                {goal === "race" 
                  ? (lang === "en" ? "Race Details 🏁" : "Thông tin giải chạy 🏁") 
                  : (lang === "en" ? "Distance Target 📏" : "Mục tiêu cự ly 📏")}
              </div>
              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "16px" }}>
                {goal === "race" 
                  ? (lang === "en" ? "Tell us about the race you're training for." : "Hãy chia sẻ về giải chạy mà bạn đang chuẩn bị tham gia.") 
                  : (lang === "en" ? "What distance are you aiming to run?" : "Cự ly nào mà bạn đang hướng tới?")}
              </p>
              {goal === "race" && (
                <div style={{ marginBottom: "10px" }}>
                  <label style={labelS}>{lang === "en" ? "Race Name" : "Tên giải chạy"}</label>
                  <input type="text" className="chat-input" style={inputS} placeholder="e.g. UTMB, Boston Marathon" value={onboardingAnswers.race_name} onChange={e => setAns("race_name", e.target.value)} />
                </div>
              )}
              {goal === "race" && (
                <div style={{ marginBottom: "10px" }}>
                  <label style={labelS}>{lang === "en" ? "Race Date" : "Ngày chạy"}</label>
                  <input type="date" className="chat-input" style={inputS} value={onboardingAnswers.race_date} onChange={e => setAns("race_date", e.target.value)} />
                </div>
              )}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "10px" }}>
                <div><label style={labelS}>{lang === "en" ? "Distance (km)" : "Cự ly (km)"}</label><input type="number" className="chat-input" style={inputS} placeholder="42" value={onboardingAnswers.course_distance_km} onChange={e => setAns("course_distance_km", e.target.value)} /></div>
                <div><label style={labelS}>{lang === "en" ? "Elevation Gain (m)" : "Độ cao lũy kế (mét)"}</label><input type="number" className="chat-input" style={inputS} placeholder="1500" value={onboardingAnswers.course_elevation_gain_m} onChange={e => setAns("course_elevation_gain_m", e.target.value)} /></div>
              </div>
              <div style={{ marginTop: "12px" }}>
                <label style={labelS}>{lang === "en" ? "Terrain" : "Địa hình"}</label>
                <div style={{ display: "flex", gap: "8px" }}>
                  {["trail","road","mixed"].map(t => (
                    <button key={t} type="button" onClick={() => setAns("terrain", t)}
                      style={{ flex: 1, padding: "8px", borderRadius: "8px", border: `1.5px solid ${onboardingAnswers.terrain === t ? "var(--accent-primary)" : "var(--border-color)"}`, background: onboardingAnswers.terrain === t ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", color: onboardingAnswers.terrain === t ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: "600", fontSize: "12px", cursor: "pointer" }}>
                      {t === "trail" ? (lang === "en" ? "Trail" : "Địa hình") :
                       t === "road" ? (lang === "en" ? "Road" : "Đường bằng") :
                       (lang === "en" ? "Mixed" : "Hỗn hợp")}
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ marginTop: "12px" }}>
                <label style={labelS}>{lang === "en" ? "Race Goal" : "Mục tiêu giải chạy"}</label>
                <div style={{ display: "flex", background: "rgba(255,255,255,0.4)", border: "1px solid var(--border-color)", padding: "3px", borderRadius: "10px", marginBottom: "10px" }}>
                  {[
                    { val: "finish", label: lang === "en" ? "Just Finish" : "Hoàn thành" },
                    { val: "time", label: lang === "en" ? "Time Target" : "Đạt mốc thời gian" }
                  ].map(({ val, label }) => (
                    <button key={val} type="button" onClick={() => setAns("race_goal", val)}
                      style={{ flex: 1, height: "30px", fontSize: "12px", borderRadius: "8px", border: "none", background: (onboardingAnswers.race_goal || "finish") === val ? "var(--accent-primary)" : "transparent", color: (onboardingAnswers.race_goal || "finish") === val ? "#fff" : "var(--text-secondary)", fontWeight: "600", cursor: "pointer" }}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {(onboardingAnswers.race_goal === "time") && (
                <div style={{ marginTop: "10px" }}>
                  <label style={labelS}>{lang === "en" ? "Expected Finish Time" : "Thời gian hoàn thành mục tiêu"}</label>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                    <div>
                      <label style={{ ...labelS, fontSize: "11px", fontWeight: "normal" }}>{lang === "en" ? "Hours" : "Giờ"}</label>
                      <input type="number" min="0" className="chat-input" style={inputS} placeholder="4" value={onboardingAnswers.expected_finish_hours} onChange={e => setAns("expected_finish_hours", e.target.value)} />
                    </div>
                    <div>
                      <label style={{ ...labelS, fontSize: "11px", fontWeight: "normal" }}>{lang === "en" ? "Minutes" : "Phút"}</label>
                      <input type="number" min="0" max="59" className="chat-input" style={inputS} placeholder="30" value={onboardingAnswers.expected_finish_minutes} onChange={e => setAns("expected_finish_minutes", e.target.value)} />
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        case "return_questions":
          return (
            <div>
              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>
                {lang === "en" ? "Getting Back 🔄" : "Tập luyện trở lại 🔄"}
              </div>
              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "16px" }}>
                {lang === "en" ? "Help us understand where you're coming from." : "Giúp chúng tôi hiểu rõ hơn về tình trạng hiện tại của bạn."}
              </p>
              <div style={{ marginBottom: "12px" }}>
                <label style={labelS}>{lang === "en" ? "How long have you been away?" : "Bạn đã dừng chạy trong bao lâu?"}</label>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  {["< 2 weeks","2–6 weeks","1–3 months","3–6 months","6+ months"].map(v => {
                    const label = lang === "vi" 
                      ? v.replace("< 2 weeks", "< 2 tuần").replace("weeks", "tuần").replace("months", "tháng").replace("months+", "tháng trở lên")
                      : v;
                    return (
                      <button key={v} type="button" onClick={() => setAns("time_away", v)} style={{ padding: "8px 12px", borderRadius: "8px", border: `1.5px solid ${onboardingAnswers.time_away === v ? "var(--accent-primary)" : "var(--border-color)"}`, background: onboardingAnswers.time_away === v ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", color: onboardingAnswers.time_away === v ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: onboardingAnswers.time_away === v ? "700" : "500", fontSize: "12.5px", cursor: "pointer", textAlign: "left" as const }}>{label}</button>
                    );
                  })}
                </div>
              </div>
              <div style={{ marginBottom: "12px" }}>
                <label style={labelS}>{lang === "en" ? "How are you feeling now?" : "Cảm nhận hiện tại của bạn?"}</label>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  {[
                    { val: "Feeling good, just need structure", en: "Feeling good, just need structure", vi: "Cảm thấy tốt, chỉ cần lịch trình tập" },
                    { val: "A bit rusty, slightly deconditioned", en: "A bit rusty, slightly deconditioned", vi: "Hơi uể oải, thể lực giảm nhẹ" },
                    { val: "Significant deconditioning — starting nearly fresh", en: "Significant deconditioning — starting nearly fresh", vi: "Giảm thể lực nghiêm trọng — bắt đầu lại gần như từ đầu" }
                  ].map(({ val, en, vi }) => (
                    <button key={val} type="button" onClick={() => setAns("fitness_feel", val)} style={{ padding: "8px 12px", borderRadius: "8px", border: `1.5px solid ${onboardingAnswers.fitness_feel === val ? "var(--accent-primary)" : "var(--border-color)"}`, background: onboardingAnswers.fitness_feel === val ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", color: onboardingAnswers.fitness_feel === val ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: onboardingAnswers.fitness_feel === val ? "700" : "500", fontSize: "12.5px", cursor: "pointer", textAlign: "left" as const }}>
                      {lang === "en" ? en : vi}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          );
        case "recovery_questions":
          return (
            <div>
              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>
                {lang === "en" ? "Post-Race Recovery 💤" : "Phục hồi sau giải chạy 💤"}
              </div>
              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "16px" }}>
                {lang === "en" ? "Let's make sure you recover smart before the next build." : "Đảm bảo bạn phục hồi thông minh trước khi bắt đầu chu kỳ tập tiếp theo."}
              </p>
              <div style={{ marginBottom: "12px" }}>
                <label style={labelS}>{lang === "en" ? "What race did you complete?" : "Cự ly giải chạy bạn vừa hoàn thành?"}</label>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                  {["5k","10k","Half Marathon","Marathon","Ultra (< 60k)","Ultra (60k+)"].map(v => {
                    const label = lang === "vi" ? v.replace("Half Marathon", "Bán marathon").replace("Marathon", "Chạy marathon") : v;
                    return (
                      <button key={v} type="button" onClick={() => setAns("race_distance_completed", v)} style={{ padding: "7px 12px", borderRadius: "8px", border: `1.5px solid ${onboardingAnswers.race_distance_completed === v ? "var(--accent-primary)" : "var(--border-color)"}`, background: onboardingAnswers.race_distance_completed === v ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", color: onboardingAnswers.race_distance_completed === v ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: onboardingAnswers.race_distance_completed === v ? "700" : "500", fontSize: "12px", cursor: "pointer" }}>{label}</button>
                    );
                  })}
                </div>
              </div>
              <div style={{ marginBottom: "12px" }}>
                <label style={labelS}>{lang === "en" ? "Days since race" : "Số ngày kể từ giải chạy"}</label>
                <input type="number" min="0" className="chat-input" style={inputS} placeholder="e.g. 3" value={onboardingAnswers.days_since_race} onChange={e => setAns("days_since_race", e.target.value)} />
              </div>
              <div>
                <label style={labelS}>{lang === "en" ? "How are you feeling?" : "Bạn cảm thấy như thế nào?"}</label>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  {[
                    { val: "Feeling great, minimal soreness", en: "Feeling great, minimal soreness", vi: "Khá tốt, mỏi cơ không đáng kể" },
                    { val: "Moderate fatigue, some soreness", en: "Moderate fatigue, some soreness", vi: "Mệt mỏi vừa phải, đau cơ nhẹ" },
                    { val: "Very fatigued — need real rest", en: "Very fatigued — need real rest", vi: "Rất mệt mỏi — cần nghỉ ngơi thực sự" }
                  ].map(({ val, en, vi }) => (
                    <button key={val} type="button" onClick={() => setAns("recovery_feel", val)} style={{ padding: "8px 12px", borderRadius: "8px", border: `1.5px solid ${onboardingAnswers.recovery_feel === val ? "var(--accent-primary)" : "var(--border-color)"}`, background: onboardingAnswers.recovery_feel === val ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", color: onboardingAnswers.recovery_feel === val ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: onboardingAnswers.recovery_feel === val ? "700" : "500", fontSize: "12.5px", cursor: "pointer", textAlign: "left" as const }}>
                      {lang === "en" ? en : vi}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          );
        case "schedule":
          return (
            <div>
              <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "6px" }}>
                {lang === "en" ? "Your Schedule 📅" : "Lịch tập của bạn 📅"}
              </div>
              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "16px" }}>
                {lang === "en" ? "We'll build your plan around your availability." : "Chúng tôi sẽ xây dựng kế hoạch quanh thời gian rảnh của bạn."}
              </p>
              <div style={{ marginBottom: "14px" }}>
                <label style={labelS}>{lang === "en" ? "Days per week" : "Số ngày mỗi tuần"}</label>
                <div style={{ display: "flex", gap: "6px" }}>
                  {[3,4,5,6,7].map(n => (
                    <button key={n} type="button" onClick={() => setAns("days_per_week", n)} style={{ flex: 1, padding: "8px", borderRadius: "8px", border: `1.5px solid ${onboardingAnswers.days_per_week === n ? "var(--accent-primary)" : "var(--border-color)"}`, background: onboardingAnswers.days_per_week === n ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", color: onboardingAnswers.days_per_week === n ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: "600", fontSize: "14px", cursor: "pointer" }}>{n}</button>
                  ))}
                </div>
              </div>
              <div style={{ marginBottom: "14px" }}>
                <label style={labelS}>Which days can you run?</label>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                  {DAYS.map(day => {
                    const sel = (onboardingAnswers.preferred_run_days || []).includes(day);
                    return (
                      <button key={day} type="button" onClick={() => toggleDay(day)} style={{ padding: "6px 10px", borderRadius: "8px", border: `1.5px solid ${sel ? "var(--accent-primary)" : "var(--border-color)"}`, background: sel ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", color: sel ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: sel ? "700" : "500", fontSize: "12px", cursor: "pointer" }}>{day.slice(0,3)}</button>
                    );
                  })}
                </div>
              </div>
              <div style={{ marginBottom: "14px" }}>
                <label style={labelS}>Long run day</label>
                <select className="chat-input" style={inputS} value={onboardingAnswers.long_run_day} onChange={e => setAns("long_run_day", e.target.value)}>
                  {DAYS.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "14px" }}>
                <div><label style={labelS}>Current weekly km</label><input type="number" className="chat-input" style={inputS} placeholder="30" value={onboardingAnswers.current_weekly_km} onChange={e => setAns("current_weekly_km", e.target.value)} /></div>
                <div style={{ display: "flex", flexDirection: "column", justifyContent: "flex-end" }}>
                  <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", fontSize: "12.5px", color: "var(--text-primary)", paddingBottom: "4px" }}>
                    <input type="checkbox" checked={onboardingAnswers.has_gym_access} onChange={e => setAns("has_gym_access", e.target.checked)} style={{ width: "16px", height: "16px", accentColor: "var(--accent-primary)" }} />
                    Gym / Treadmill access?
                  </label>
                </div>
              </div>
              <div>
                <label style={labelS}>{lang === "en" ? "Plan Start Date" : "Ngày bắt đầu kế hoạch"}</label>
                <input type="date" className="chat-input" style={inputS} value={onboardingAnswers.plan_start_date} onChange={e => setAns("plan_start_date", e.target.value)} />
                <p style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "5px", margin: "5px 0 0 0" }}>
                  {lang === "en" ? "Week 1 of your plan will begin from this date." : "Tuần 1 của kế hoạch sẽ bắt đầu từ ngày này."}
                </p>
              </div>
            </div>
          );
        case "generate":
          return (
            <div style={{ textAlign: "center", padding: "20px 0" }}>
              {onboardingGenerating ? (
                <>
                  <div style={{ fontSize: "40px", marginBottom: "16px", animation: "spin 2s linear infinite" }}>⚙️</div>
                  <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "8px" }}>
                    {lang === "en" ? "Building your plan..." : "Đang tạo kế hoạch..."}
                  </div>
                  <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>
                    {lang === "en" 
                      ? "Coach Uphill is crafting a personalised training plan based on your profile. This may take 30–60 seconds." 
                      : "Coach Uphill đang chuẩn bị kế hoạch tập luyện cá nhân hóa của bạn. Quá trình này có thể mất 30–60 giây."}
                  </p>
                </>
              ) : (
                <>
                  <div style={{ fontSize: "40px", marginBottom: "16px" }}>✨</div>
                  <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "8px" }}>
                    {lang === "en" ? "You're all set!" : "Tất cả đã sẵn sàng!"}
                  </div>
                  <p style={{ color: "var(--text-muted)", fontSize: "13px", marginBottom: "20px" }}>
                    {lang === "en" 
                      ? `Ready to generate your personalised ${onboardingAnswers.goal_type?.replace("_"," ")} training plan?` 
                      : `Bạn đã sẵn sàng khởi tạo kế hoạch tập luyện ${onboardingAnswers.goal_type?.replace("_"," ")} cá nhân hóa chưa?`}
                  </p>
                  <div style={{ background: "rgba(16,185,129,0.06)", border: "1px solid rgba(16,185,129,0.15)", borderRadius: "12px", padding: "14px", marginBottom: "20px", textAlign: "left" }}>
                    <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "6px", fontWeight: "600" }}>
                      {lang === "en" ? "SUMMARY" : "BẢN TỔNG HỢP"}
                    </div>
                    <div style={{ fontSize: "13px", display: "flex", flexDirection: "column", gap: "4px" }}>
                      <div>{lang === "en" ? "Goal:" : "Mục tiêu:"} <strong>{onboardingAnswers.goal_type?.replace("_"," ")}</strong></div>
                      <div>{lang === "en" ? "Starts:" : "Bắt đầu:"} <strong>{onboardingAnswers.plan_start_date || "Today"}</strong> · {onboardingAnswers.days_per_week || 4} {lang === "en" ? "days/week" : "ngày/tuần"}</div>
                      <div>🌙 {lang === "en" ? "Long run:" : "Chạy dài:"} <strong>{onboardingAnswers.long_run_day}</strong> · {lang === "en" ? "Volume:" : "Thể tích:"} <strong>{onboardingAnswers.current_weekly_km || 30} km/{lang === "en" ? "wk" : "tuần"}</strong></div>
                      {onboardingAnswers.race_name && <div>🏁 {lang === "en" ? "Race:" : "Giải chạy:"} <strong>{onboardingAnswers.race_name}</strong></div>}
                    </div>
                  </div>
                  <button className="btn btn-primary" style={{ width: "100%", height: "44px", fontSize: "14px", fontWeight: "700" }} onClick={handleCompleteOnboarding}>
                    🚀 {lang === "en" ? "Generate My Training Plan" : "Khởi tạo Kế hoạch Tập luyện Của Tôi"}
                  </button>
                </>
              )}
            </div>
          );
        default:
          return null;
      }
    };

    return (
      <div style={{ position: "fixed", inset: 0, background: "rgba(255,255,255,0.35)", backdropFilter: "blur(16px)", display: "flex", justifyContent: "center", alignItems: "center", zIndex: 1001, padding: "20px" }}>
        <div style={{ background: "var(--bg-card)", backdropFilter: "blur(30px)", border: "1px solid var(--border-color)", borderRadius: "24px", padding: "32px", width: "100%", maxWidth: "500px", maxHeight: "90vh", overflowY: "auto", boxShadow: "0 20px 60px rgba(0,0,0,0.1)", color: "var(--text-primary)" }}>
          {/* Progress bar */}
          <div style={{ marginBottom: "24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-muted)", marginBottom: "6px" }}>
              <span>{lang === "en" ? "Step" : "Bước"} {onboardingStep + 1} {lang === "en" ? "of" : "trên"} {totalSteps}</span>
              <span>{Math.round(((onboardingStep + 1) / totalSteps) * 100)}%</span>
            </div>
            <div style={{ height: "4px", background: "rgba(0,0,0,0.06)", borderRadius: "4px", overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${((onboardingStep + 1) / totalSteps) * 100}%`, background: "var(--accent-primary)", borderRadius: "4px", transition: "width 0.3s ease" }} />
            </div>
          </div>

          {/* Step content */}
          {renderStep()}

          {/* Navigation */}
          {!onboardingGenerating && currentStepKey !== "generate" && (
            <div style={{ display: "flex", gap: "10px", marginTop: "24px" }}>
              {onboardingStep > 0 && (
                <button type="button" onClick={prevStep} style={{ flex: 1, height: "40px", borderRadius: "10px", border: "1px solid var(--border-color)", background: "transparent", color: "var(--text-secondary)", fontWeight: "600", fontSize: "13px", cursor: "pointer" }}>
                  ← {lang === "en" ? "Back" : "Quay lại"}
                </button>
              )}
              <button type="button" onClick={nextStep}
                disabled={currentStepKey === "goal" && !onboardingAnswers.goal_type}
                className="btn btn-primary" style={{ flex: 2, height: "40px", fontSize: "13px" }}>
                {onboardingStep === totalSteps - 2 
                  ? (lang === "en" ? "Review →" : "Xem lại →") 
                  : (lang === "en" ? "Next →" : "Tiếp theo →")}
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };

  // ─── Profile Settings Modal ───────────────────────────────────────────────
  const renderProfileSettingsModal = () => {
    if (!profileSettingsOpen || !user) return null;

    const inputStyle: React.CSSProperties = {
      borderRadius: "8px", width: "100%", height: "36px", margin: 0, padding: "0 10px",
      fontSize: "13px", background: "transparent", border: "1px solid var(--border-color)",
      color: "var(--text-primary)", boxSizing: "border-box" as const
    };
    const labelStyle: React.CSSProperties = {
      display: "block", fontSize: "11.5px", fontWeight: "600", color: "var(--text-muted)", marginBottom: "5px"
    };

    return (
      <div style={{ position: "fixed", inset: 0, background: "rgba(255,255,255,0.35)", backdropFilter: "blur(16px)", display: "flex", justifyContent: "center", alignItems: "center", zIndex: 1000, padding: "20px" }}>
        <div style={{ background: "var(--bg-card)", backdropFilter: "blur(30px)", border: "1px solid var(--border-color)", borderRadius: "24px", padding: "32px", width: "100%", maxWidth: "520px", maxHeight: "90vh", overflowY: "auto", boxShadow: "0 20px 60px rgba(0,0,0,0.1)", position: "relative", color: "var(--text-primary)" }}>
          
          {/* Close button */}
          <button 
            type="button" 
            onClick={() => { setProfileSettingsOpen(false); setPasswordFormOpen(false); setPasswordMsg(""); setPasswordError(""); }}
            style={{ position: "absolute", top: "20px", right: "20px", background: "none", border: "none", fontSize: "20px", cursor: "pointer", color: "var(--text-muted)" }}
          >
            ✕
          </button>

          {/* Header */}
          <div style={{ marginBottom: "24px" }}>
            <div style={{ fontSize: "22px", fontWeight: "800", letterSpacing: "-0.02em" }}>
              {lang === "en" ? "Profile Settings" : "Cài đặt Hồ sơ"}
            </div>
            <p style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "4px" }}>
              {lang === "en" ? "Manage your physiology parameters and security settings" : "Quản lý các thông số sinh lý và cài đặt bảo mật của bạn"}
            </p>
          </div>

          {authErrorMsg && (
            <div style={{ color: "#ef4444", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.15)", borderRadius: "8px", padding: "10px", fontSize: "12.5px", marginBottom: "16px" }}>
              <Warning weight="fill" style={{marginRight: "4px", verticalAlign: "middle"}}/> {authErrorMsg}
            </div>
          )}

          <form onSubmit={handleSaveProfile} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            
            {/* Physiology Section */}
            <div>
              <h3 style={{ fontSize: "14px", fontWeight: "700", borderBottom: "1px solid var(--border-color)", paddingBottom: "6px", marginBottom: "12px", color: "var(--accent-primary)" }}>
                {t("profile_title").toUpperCase()}
              </h3>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <label style={labelStyle}>{t("profile_age").replace(" (Years)", "")}</label>
                  <input type="number" style={inputStyle} value={profileForm.age} onChange={e => setProfileForm({ ...profileForm, age: e.target.value })} required />
                </div>
                <div>
                  <label style={labelStyle}>{lang === "en" ? "Weekly Volume (km)" : "Khối lượng tuần (km)"}</label>
                  <input type="number" step="0.1" style={inputStyle} value={profileForm.current_weekly_km} onChange={e => setProfileForm({ ...profileForm, current_weekly_km: e.target.value })} required />
                </div>
                <div>
                  <label style={labelStyle}>{t("profile_max_hr")}</label>
                  <input type="number" style={inputStyle} value={profileForm.max_hr} onChange={e => setProfileForm({ ...profileForm, max_hr: e.target.value })} required />
                </div>
                <div>
                  <label style={labelStyle}>{t("profile_resting_hr")}</label>
                  <input type="number" style={inputStyle} value={profileForm.resting_hr} onChange={e => setProfileForm({ ...profileForm, resting_hr: e.target.value })} required />
                </div>
                <div>
                  <label style={labelStyle}>{t("profile_aet_hr")}</label>
                  <input type="number" style={inputStyle} value={profileForm.aet_hr} onChange={e => setProfileForm({ ...profileForm, aet_hr: e.target.value })} required />
                </div>
                <div>
                  <label style={labelStyle}>{t("profile_ant_hr")}</label>
                  <input type="number" style={inputStyle} value={profileForm.ant_hr} onChange={e => setProfileForm({ ...profileForm, ant_hr: e.target.value })} required />
                </div>
                <div>
                  <label style={labelStyle}>{lang === "en" ? "Zone 2 Pace Min" : "Zone 2 Pace Min"}</label>
                  <input type="text" style={inputStyle} value={profileForm.zone2_pace_min} onChange={e => setProfileForm({ ...profileForm, zone2_pace_min: e.target.value })} required />
                </div>
                <div>
                  <label style={labelStyle}>{lang === "en" ? "Zone 2 Pace Max" : "Zone 2 Pace Max"}</label>
                  <input type="text" style={inputStyle} value={profileForm.zone2_pace_max} onChange={e => setProfileForm({ ...profileForm, zone2_pace_max: e.target.value })} required />
                </div>
              </div>
              <div style={{ marginTop: "12px" }}>
                <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", cursor: "pointer", color: "var(--text-primary)" }}>
                  <input type="checkbox" checked={profileForm.use_treadmill} onChange={e => setProfileForm({ ...profileForm, use_treadmill: e.target.checked })} style={{ width: "16px", height: "16px", accentColor: "var(--accent-primary)" }} />
                  {t("profile_treadmill")}
                </label>
              </div>
              <div style={{ marginTop: "12px" }}>
                <label style={labelStyle}>{t("profile_gemini_key")}</label>
                <input type="password" style={inputStyle} placeholder={lang === "en" ? "Leave blank to use system key" : "Để trống để sử dụng key của hệ thống"} value={profileForm.gemini_api_key} onChange={e => setProfileForm({ ...profileForm, gemini_api_key: e.target.value })} />
              </div>
            </div>

            {/* Language Settings Section */}
            <div style={{ marginTop: "10px" }}>
              <h3 style={{ fontSize: "14px", fontWeight: "700", borderBottom: "1px solid var(--border-color)", paddingBottom: "6px", marginBottom: "12px", color: "var(--accent-primary)" }}>
                {lang === "en" ? "LANGUAGE CONFIGURATION" : "CẤU HÌNH NGÔN NGỮ"}
              </h3>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
                <span style={{ fontSize: "13.5px", color: "var(--text-primary)" }}>
                  {lang === "en" ? "Select Language:" : "Chọn ngôn ngữ:"}
                </span>
                <div style={{ display: "flex", background: "rgba(0, 0, 0, 0.05)", border: "1px solid var(--border-color)", padding: "2px", borderRadius: "8px", gap: "2px" }}>
                  <button 
                    type="button"
                    onClick={() => handleSetLang("en")}
                    style={{ padding: "6px 12px", fontSize: "11px", borderRadius: "6px", border: "none", background: lang === "en" ? "var(--accent-primary)" : "transparent", color: lang === "en" ? "#ffffff" : "var(--text-secondary)", cursor: "pointer", fontWeight: lang === "en" ? "600" : "500", transition: "all 0.15s" }}
                  >
                    English
                  </button>
                  <button 
                    type="button"
                    onClick={() => handleSetLang("vi")}
                    style={{ padding: "6px 12px", fontSize: "11px", borderRadius: "6px", border: "none", background: lang === "vi" ? "var(--accent-primary)" : "transparent", color: lang === "vi" ? "#ffffff" : "var(--text-secondary)", cursor: "pointer", fontWeight: lang === "vi" ? "600" : "500", transition: "all 0.15s" }}
                  >
                    Tiếng Việt
                  </button>
                </div>
              </div>
            </div>

            {/* Account Settings Section */}
            <div style={{ marginTop: "10px" }}>
              <h3 style={{ fontSize: "14px", fontWeight: "700", borderBottom: "1px solid var(--border-color)", paddingBottom: "6px", marginBottom: "12px", color: "var(--accent-primary)" }}>{lang === "en" ? "ACCOUNT & SECURITY" : "TÀI KHOẢN & BẢO MẬT"}</h3>
              <div style={{ fontSize: "13px", display: "flex", flexDirection: "column", gap: "6px", marginBottom: "14px" }}>
                <div>{lang === "en" ? "Name:" : "Tên:"} <strong>{user.name}</strong></div>
                <div>Email: <strong>{user.email}</strong></div>
                <div>{lang === "en" ? "Login Provider:" : "Phương thức đăng nhập:"} <strong style={{ textTransform: "capitalize" }}>{user.provider}</strong></div>
              </div>

              {/* Password configuration */}
              {passwordMsg && (
                <div style={{ color: "#10b981", background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.15)", borderRadius: "8px", padding: "10px", fontSize: "12.5px", marginBottom: "12px" }}>
                  ✓ {passwordMsg}
                </div>
              )}
              {passwordError && (
                <div style={{ color: "#ef4444", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.15)", borderRadius: "8px", padding: "10px", fontSize: "12.5px", marginBottom: "12px" }}>
                  <Warning weight="fill" style={{marginRight: "4px", verticalAlign: "middle"}}/> {passwordError}
                </div>
              )}

              {!user.has_password ? (
                <div style={{ background: "rgba(245,158,11,0.06)", border: "1px solid rgba(245,158,11,0.2)", borderRadius: "12px", padding: "14px" }}>
                  <div style={{ fontSize: "12.5px", fontWeight: "700", color: "#d97706", marginBottom: "4px" }}>
                    {lang === "en" ? "No Password Configured" : "Chưa Thiết lập Mật khẩu"}
                  </div>
                  <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: "0 0 10px 0" }}>
                    {lang === "en" 
                      ? `You currently sign in via OAuth (${user.provider}). Add a password to log in directly using your email address later.` 
                      : `Bạn đang đăng nhập qua OAuth (${user.provider}). Hãy thiết lập mật khẩu để đăng nhập trực tiếp bằng email sau này.`}
                  </p>
                  
                  {passwordFormOpen ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                      <div>
                        <label style={labelStyle}>{lang === "en" ? "New Password" : "Mật khẩu Mới"}</label>
                        <input type="password" style={inputStyle} placeholder="Min 8 characters" value={newPassword} onChange={e => setNewPassword(e.target.value)} required minLength={8} />
                      </div>
                      <div>
                        <label style={labelStyle}>{lang === "en" ? "Confirm New Password" : "Xác nhận Mật khẩu Mới"}</label>
                        <input type="password" style={inputStyle} placeholder="Repeat password" value={confirmNewPassword} onChange={e => setConfirmNewPassword(e.target.value)} required minLength={8} />
                      </div>
                      <div style={{ display: "flex", gap: "8px" }}>
                        <button type="button" onClick={handleSetPassword} className="btn btn-primary" style={{ height: "32px", fontSize: "12px", padding: "0 14px" }}>
                          {lang === "en" ? "Set Password" : "Thiết lập mật khẩu"}
                        </button>
                        <button type="button" onClick={() => setPasswordFormOpen(false)} style={{ height: "32px", border: "1px solid var(--border-color)", background: "transparent", color: "var(--text-secondary)", borderRadius: "8px", padding: "0 12px", cursor: "pointer", fontSize: "12px" }}>
                          {lang === "en" ? "Cancel" : "Hủy"}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button type="button" onClick={() => setPasswordFormOpen(true)} className="btn btn-primary" style={{ height: "32px", fontSize: "12.5px", padding: "0 14px" }}>
                      🔑 {lang === "en" ? "Set Account Password" : "Thiết lập Mật khẩu Tài khoản"}
                    </button>
                  )}
                </div>
              ) : (
                <div>
                  {passwordFormOpen ? (
                    <div style={{ background: "rgba(255,255,255,0.2)", border: "1px solid var(--border-color)", borderRadius: "12px", padding: "14px", display: "flex", flexDirection: "column", gap: "10px" }}>
                      <div>
                        <label style={labelStyle}>{lang === "en" ? "New Password" : "Mật khẩu Mới"}</label>
                        <input type="password" style={inputStyle} placeholder="Min 8 characters" value={newPassword} onChange={e => setNewPassword(e.target.value)} required minLength={8} />
                      </div>
                      <div>
                        <label style={labelStyle}>{lang === "en" ? "Confirm New Password" : "Xác nhận Mật khẩu Mới"}</label>
                        <input type="password" style={inputStyle} placeholder="Repeat password" value={confirmNewPassword} onChange={e => setConfirmNewPassword(e.target.value)} required minLength={8} />
                      </div>
                      <div style={{ display: "flex", gap: "8px" }}>
                        <button type="button" onClick={handleSetPassword} className="btn btn-primary" style={{ height: "32px", fontSize: "12px", padding: "0 14px" }}>
                          {lang === "en" ? "Update Password" : "Cập nhật Mật khẩu"}
                        </button>
                        <button type="button" onClick={() => setPasswordFormOpen(false)} style={{ height: "32px", border: "1px solid var(--border-color)", background: "transparent", color: "var(--text-secondary)", borderRadius: "8px", padding: "0 12px", cursor: "pointer", fontSize: "12px" }}>
                          {lang === "en" ? "Cancel" : "Hủy"}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button type="button" onClick={() => setPasswordFormOpen(true)} style={{ height: "32px", border: "1px solid var(--border-color)", background: "transparent", color: "var(--text-primary)", borderRadius: "8px", padding: "0 12px", cursor: "pointer", fontSize: "12.5px", fontWeight: "600" }}>
                      🔄 {lang === "en" ? "Change Account Password" : "Thay đổi Mật khẩu Tài khoản"}
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Bottom Actions */}
            <div style={{ display: "flex", gap: "10px", borderTop: "1px solid var(--border-color)", paddingTop: "18px", marginTop: "10px" }}>
              <button type="button" onClick={() => { setProfileSettingsOpen(false); setPasswordFormOpen(false); setPasswordMsg(""); setPasswordError(""); }} style={{ height: "40px", borderRadius: "10px", border: "1px solid var(--border-color)", background: "transparent", color: "var(--text-secondary)", fontWeight: "600", fontSize: "13px", cursor: "pointer", padding: "0 14px" }}>
                {lang === "en" ? "Cancel" : "Hủy"}
              </button>
              <button type="submit" className="btn btn-primary" style={{ flex: 1, height: "40px", fontSize: "13px" }} disabled={authLoading}>
                {authLoading ? (lang === "en" ? "Saving..." : "Đang lưu...") : (lang === "en" ? "Save Settings" : "Lưu cài đặt")}
              </button>
              <button
                type="button"
                onClick={() => { setProfileSettingsOpen(false); handleLogout(); }}
                style={{ height: "40px", borderRadius: "10px", border: "1px solid rgba(239,68,68,0.3)", background: "rgba(239,68,68,0.06)", color: "#dc2626", fontWeight: "700", fontSize: "13px", cursor: "pointer", padding: "0 14px", whiteSpace: "nowrap" }}
              >
                🚪 {lang === "en" ? "Sign Out" : "Đăng xuất"}
              </button>
            </div>
          </form>

        </div>
      </div>
    );
  };

  return (
    <div style={{ position: "fixed", top: 0, left: 0, right: 0, height: "100dvh", display: "flex", flexDirection: "column", overflow: "hidden" }}>

      {/* ── Video Background: Two stacked videos for seamless crossfade ── */}
      <div className="video-bg-container">
        {/* Video A */}
        <video
          ref={videoARef}
          autoPlay
          muted
          playsInline
          style={{ position: "absolute", top: "50%", left: "50%", width: "115%", height: "115%",
            transform: "translate(-50%, -50%)", objectFit: "cover", objectPosition: "center top",
            opacity: 0, transition: "none", willChange: "opacity", zIndex: 2, pointerEvents: "none" }}
        />
        {/* Video B */}
        <video
          ref={videoBRef}
          autoPlay
          muted
          playsInline
          style={{ position: "absolute", top: "50%", left: "50%", width: "115%", height: "115%",
            transform: "translate(-50%, -50%)", objectFit: "cover", objectPosition: "center top",
            opacity: 0, transition: "none", willChange: "opacity", zIndex: 1, pointerEvents: "none" }}
        />
      </div>

      {/* ── Plan Generation Notification Banner ── */}
      {planJobStatus !== "idle" && (
        <div style={{
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
          background: planJobStatus === "done"
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
        }}>
          {planJobStatus === "generating" && (
            <>
              <span style={{
                display: "inline-block",
                width: "16px",
                height: "16px",
                border: "2px solid rgba(255,255,255,0.4)",
                borderTopColor: "#a78bfa",
                borderRadius: "50%",
                animation: "spin 0.8s linear infinite",
                flexShrink: 0,
              }} />
              <span>⚡ Generating your training plan…</span>
              <span style={{ fontSize: "12px", opacity: 0.7, fontWeight: 400 }}>This may take a few minutes</span>
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
                style={{ marginLeft: "4px", background: "transparent", border: "none", color: "rgba(255,255,255,0.6)", cursor: "pointer", fontSize: "16px", lineHeight: 1 }}
                aria-label="Dismiss"
              >×</button>
            </>
          )}
          {planJobStatus === "error" && (
            <>
              <span style={{ fontSize: "20px" }}><Warning weight="fill" /></span>
              <span>Plan generation failed.</span>
              {planJobMessage && <span style={{ fontSize: "12px", opacity: 0.7, fontWeight: 400, maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis" }}>{planJobMessage}</span>}
              <button
                onClick={() => setPlanJobStatus("idle")}
                style={{ marginLeft: "8px", background: "transparent", border: "none", color: "rgba(255,255,255,0.6)", cursor: "pointer", fontSize: "16px", lineHeight: 1 }}
                aria-label="Dismiss"
              >×</button>
            </>
          )}
        </div>
      )}

      {viewMode === "desktop" ? (
        <div className="desktop-only-wrapper" style={{ display: "flex", width: "100%", height: "100%", overflow: "hidden", position: "relative" }}>
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
                {(["home", "about", "chat", "planner", "tools", "knowledge"] as const).map((tab) => {
                  const active = activeTab === tab;
                  return (
                    <li 
                      key={tab}
                      onClick={() => handleTabSwitch(tab)}
                      className={`sidebar-nav-item ${active ? "sidebar-nav-item-active" : ""}`}
                    >
                      {getTabIcon(tab, active)}
                      <span>
                        {tab === "home" ? t("tab_home") :
                         tab === "chat" ? t("tab_chat") :
                         tab === "planner" ? t("tab_scheduler") :
                         tab === "knowledge" ? t("tab_knowledge") :
                         tab === "about" ? t("tab_about") :
                         t("tab_tools")}
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
                  onClick={() => { setProfileSettingsOpen(true); }}
                  style={{ display: "flex", alignItems: "center", gap: "10px", cursor: "pointer", padding: "8px", borderRadius: "12px", background: "rgba(255,255,255,0.2)", border: "1px solid var(--border-color)" }}
                >
                  <div style={{ width: "32px", height: "32px", borderRadius: "50%", background: "var(--accent-primary)", color: "#fff", display: "flex", alignItems: "center", justifyItems: "center", justifyContent: "center", fontWeight: "700", fontSize: "14px", flexShrink: 0 }}>
                    {user.name[0].toUpperCase()}
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
                    <span style={{ fontSize: "12px", fontWeight: "700", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: "100px" }}>{user.name}</span>
                    <span style={{ fontSize: "9.5px", color: "var(--accent-primary)", textDecoration: "underline" }}>
                      {lang === "en" ? "Settings" : "Cài đặt"}
                    </span>
                  </div>
                </div>
              ) : (
                <button 
                  onClick={() => setAuthModalOpen(true)} 
                  className="btn btn-primary"
                  style={{ width: "100%", height: "36px", padding: "0", fontSize: "12.5px" }}
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
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontSize: "12.5px", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-secondary)", fontWeight: "600" }}>
                  {lang === "en" ? "Dashboard" : "Bảng điều khiển"} / <span style={{ color: "var(--accent-primary)" }}>
                    {activeTab === "home" ? t("tab_home") :
                     activeTab === "chat" ? t("tab_chat") :
                     activeTab === "planner" ? t("tab_scheduler") :
                     activeTab === "knowledge" ? t("tab_knowledge") :
                     activeTab === "about" ? t("tab_about") :
                     t("tab_tools")}
                  </span>
                </span>
              </div>
              
              <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>


                {/* Layout Switcher */}
                <div style={{ display: "flex", background: "rgba(255, 255, 255, 0.45)", border: "1px solid var(--border-color)", padding: "2px", borderRadius: "8px", gap: "2px" }}>
                  <button 
                    onClick={() => changeViewMode("showcase")}
                    style={{ padding: "4px 8px", fontSize: "10px", borderRadius: "6px", border: "none", background: (viewMode as string) === "showcase" ? "var(--accent-primary)" : "transparent", color: (viewMode as string) === "showcase" ? "#ffffff" : "var(--text-secondary)", cursor: "pointer", fontWeight: (viewMode as string) === "showcase" ? "600" : "500", transition: "all 0.15s" }}
                  >
                    {lang === "en" ? "Showcase" : "Giới thiệu"}
                  </button>
                  <button 
                    onClick={() => changeViewMode("desktop")}
                    style={{ padding: "4px 8px", fontSize: "10px", borderRadius: "6px", border: "none", background: (viewMode as string) === "desktop" ? "var(--accent-primary)" : "transparent", color: (viewMode as string) === "desktop" ? "#ffffff" : "var(--text-secondary)", cursor: "pointer", fontWeight: (viewMode as string) === "desktop" ? "600" : "500", transition: "all 0.15s" }}
                  >
                    {lang === "en" ? "Desktop Only" : "Chỉ Máy tính"}
                  </button>
                  <button 
                    onClick={() => changeViewMode("mobile")}
                    style={{ padding: "4px 8px", fontSize: "10px", borderRadius: "6px", border: "none", background: (viewMode as string) === "mobile" ? "var(--accent-primary)" : "transparent", color: (viewMode as string) === "mobile" ? "#ffffff" : "var(--text-secondary)", cursor: "pointer", fontWeight: (viewMode as string) === "mobile" ? "600" : "500", transition: "all 0.15s" }}
                  >
                    {lang === "en" ? "Mobile Only" : "Chỉ Di động"}
                  </button>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", color: "var(--text-secondary)" }}>
                  <span className="coach-status-dot" style={{ backgroundColor: backendConnected ? "var(--accent-success)" : "var(--accent-alert)" }}></span>
                  {backendConnected ? "Live" : "Offline"}
                </div>
                {user && (
                  <button 
                    onClick={handleLogout} 
                    className="btn btn-secondary" 
                    style={{ padding: "4px 10px", fontSize: "11px", height: "26px", borderRadius: "6px" }}
                  >
                    {t("logout")}
                  </button>
                )}
              </div>
            </nav>

            {/* Scrollable Dashboard View */}
            <div className="laptop-scrollable-content" style={{ height: "calc(100% - 60px)", display: "flex", flexDirection: "column", overflow: activeTab === "chat" ? "hidden" : "auto", padding: activeTab === "chat" ? "0" : undefined }}>
              {activeTab === "home" ? (
                renderActiveTab(false)
              ) : (
                <div className={`content-panel ${activeTab === "chat" ? "chat-panel-active" : ""}`} style={activeTab === "chat" ? { overflowY: "hidden", flex: 1, minHeight: 0 } : { flex: 1, minHeight: 0 }}>
                  <div className="content-panel-inner" style={{ width: "100%", height: activeTab === "chat" ? undefined : "auto", flex: activeTab === "chat" ? 1 : "1 0 auto", minHeight: activeTab === "chat" ? 0 : "100%", display: "flex", flexDirection: "column", maxWidth: activeTab === "chat" ? "680px" : undefined }}>
                    {/* Panel header breadcrumb */}
                    <div className="panel-header">
                      <span className="panel-header-icon" style={{ display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-primary)" }}>
                        {activeTab === "chat" ? <Robot size={28} weight="duotone" /> :
                         activeTab === "planner" ? <CalendarBlank size={28} weight="duotone" /> :
                         activeTab === "knowledge" ? <BookOpen size={28} weight="duotone" /> :
                         activeTab === "tools" ? <Calculator size={28} weight="duotone" /> : <Mountains size={28} weight="duotone" />}
                      </span>
                      <div>
                        <h2>{activeTab === "chat" ? t("tab_chat") :
                             activeTab === "planner" ? t("plan_setup") :
                             activeTab === "knowledge" ? t("know_title") :
                             activeTab === "tools" ? t("tab_tools") : t("tab_about")}</h2>
                        <p>
                          {activeTab === "chat" ? t("header_chat_desc") :
                           activeTab === "planner" ? t("header_planner_desc") :
                           activeTab === "knowledge" ? t("header_knowledge_desc") :
                           activeTab === "tools" ? t("header_tools_desc") : t("header_about_desc")}
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
        <div className="mobile-only-wrapper" style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100dvh", width: "100%", position: "relative", overflow: "hidden" }}>
          {/* Glow Effects */}
          <div className="glow-bg" style={{ opacity: 0.45 }}></div>
          <div className="glow-bg-left" style={{ opacity: 0.35 }}></div>

          <div style={{ width: "100%", maxWidth: "480px", height: "100%", background: "var(--bg-main)", display: "flex", flexDirection: "column", borderLeft: "1px solid var(--border-color)", borderRight: "1px solid var(--border-color)", position: "relative", boxShadow: "0 0 40px rgba(0,0,0,0.05)", overflow: "hidden" }}>
            {/* Phone Top Header */}
            <header className="phone-header-bar" style={{ padding: "12px 16px" }}>
              <a href="#" className="phone-logo" style={{ fontSize: "16px" }}>
                Uphill<span>.AI</span>
              </a>
              
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                {/* Simple Mode Selector */}
                <select 
                  value={viewMode} 
                  onChange={(e) => changeViewMode(e.target.value as any)}
                  style={{ background: "transparent", border: "1px solid var(--border-color)", borderRadius: "6px", fontSize: "10px", padding: "2px 6px", color: "var(--text-secondary)", outline: "none", cursor: "pointer" }}
                >
                  <option value="showcase">{lang === "en" ? "Showcase" : "Giới thiệu"}</option>
                  <option value="desktop">{lang === "en" ? "Desktop Only" : "Chỉ Máy tính"}</option>
                  <option value="mobile">{lang === "en" ? "Mobile Only" : "Chỉ Di động"}</option>
                </select>



                <span 
                  className="coach-status-dot" 
                  style={{ width: "6px", height: "6px", backgroundColor: backendConnected ? "var(--accent-success)" : "var(--accent-alert)" }}
                ></span>
                {user ? (
                  <span 
                    onClick={() => { setProfileSettingsOpen(true); }}
                    style={{ fontSize: "11px", fontWeight: "700", color: "var(--accent-primary)", cursor: "pointer" }}
                  >
                    {lang === "en" ? "Profile" : "Hồ sơ"}
                  </span>
                ) : (
                  <span 
                    onClick={() => setAuthModalOpen(true)}
                    style={{ fontSize: "11px", fontWeight: "700", color: "var(--accent-primary)", cursor: "pointer" }}
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
                minHeight: 0
              }}
            >
              {renderActiveTab(true)}
            </div>

            {/* Persistent Bottom Tab Bar */}
            <nav className="phone-bottom-tab-bar">
              {(["home", "about", "chat", "planner", "tools", "knowledge"] as const).map((tab) => {
                const active = activeTab === tab;
                const tabLabel = tab === "home" ? "Home" :
                                 tab === "chat" ? "Coach" :
                                 tab === "planner" ? "Planner" :
                                 tab === "knowledge" ? "Hub" :
                                 tab === "tools" ? "Calculators" :
                                 "Philosophy";
                return (
                  <div 
                    key={tab}
                    onClick={() => handleTabSwitch(tab)}
                    className={`tab-bar-item ${active ? "tab-bar-item-active" : ""}`}
                  >
                    {getTabIcon(tab, active, 16)}
                    <span className="tab-bar-item-label" style={{ textTransform: "none" }}>
                      {tabLabel}
                    </span>
                  </div>
                );
              })}
            </nav>
          </div>
        </div>
      ) : (
        <div className="app-root" style={{ position: "relative", zIndex: 10, display: "flex", flexDirection: "column", height: "100dvh", overflow: "hidden" }}>

          {/* ── Top Navigation ──────────────────────────────────── */}
          <nav className="top-nav" style={{ flexShrink: 0 }}>
            {/* Logo */}
            <a className="top-nav-logo" href="#">
              <span style={{ display: "inline-flex", alignItems: "center", gap: "2px" }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--accent-success)" }}>
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                  <polyline points="17 6 23 6 23 12"/>
                </svg>
                Uphill<span className="logo-accent">.AI</span>
              </span>
            </a>

            {/* Centre tab pills */}
            <div className="top-nav-tabs">
              {(["home", "chat", "planner", "knowledge", "tools", "about"] as const).map((tab) => {
                const label = tab === "home" ? `${t("tab_home")}` :
                              tab === "chat" ? `${t("tab_chat")}` :
                              tab === "planner" ? `${t("tab_scheduler")}` :
                              tab === "knowledge" ? `${t("tab_knowledge")}` :
                              tab === "about" ? `${t("tab_about")}` :
                              `${t("tab_tools")}`;
                return (
                  <button
                    key={tab}
                    className={`top-nav-tab ${activeTab === tab ? "active" : ""}`}
                    onClick={() => handleTabSwitch(tab)}
                    style={{ display: "flex", alignItems: "center", gap: "6px" }}
                  >
                    {getTabIcon(tab, activeTab === tab, 18)}
                    {label}
                  </button>
                );
              })}
            </div>

            {/* Right — status + user */}
            <div className="top-nav-right">


              <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", color: "rgba(0,0,0,0.6)" }}>
                <span className="coach-status-dot" style={{ backgroundColor: backendConnected ? "var(--accent-success)" : "var(--accent-alert)" }} />
                <span>{backendConnected ? "Live" : "Offline"}</span>
              </div>
              {user ? (
                <div
                  className="top-nav-avatar"
                  onClick={() => { setProfileSettingsOpen(true); }}
                  title={lang === "en" ? `${user.name} — click to open settings` : `${user.name} — nhấn để mở cài đặt`}
                  style={{ background: "linear-gradient(135deg, var(--accent-success), #16a34a)" }}
                >
                  {user.name[0].toUpperCase()}
                </div>
              ) : (
                <button
                  className="btn btn-primary"
                  onClick={() => setAuthModalOpen(true)}
                  style={{ padding: "8px 18px", fontSize: "12.5px", background: "var(--accent-success)" }}
                >
                  {t("auth_sign_in")}
                </button>
              )}
            </div>
          </nav>

          {/* ── Main Content Body ───────────────────────────────── */}
          <div style={{ flex: 1, overflow: "hidden", position: "relative", display: "flex", flexDirection: "column" }}>
            
            {/* ── HOME TAB: introductory hero view ────────────────── */}
            {activeTab === "home" && (
              <section className="hero-section" style={{ height: "100%", overflowY: "auto", justifyContent: "center", display: "flex", flexDirection: "column", alignItems: "center", paddingTop: "40px", paddingBottom: isViewportMobile ? "160px" : "40px", marginTop: 0 }}>
                {renderActiveTab(isViewportMobile)}
              </section>
            )}

            {activeTab !== "home" && (
              <div 
                className={`content-panel ${activeTab === "chat" ? "chat-panel-active" : ""}`}
                style={activeTab === "chat" 
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
                    padding: activeTab === "chat" && isViewportMobile ? "0px" : undefined,
                    paddingBottom: activeTab === "chat" && isViewportMobile ? "calc(80px + env(safe-area-inset-bottom))" : undefined
                  }}
                >
                  {renderActiveTab(isViewportMobile)}
                </div>
              </div>
            )}
          </div>

          {/* Mobile Bottom Navigation Tabs (visible only on mobile viewports via CSS) */}
          <div className="mobile-bottom-nav-tabs">
            {(["home", "chat", "planner", "knowledge", "tools", "about"] as const).map((tab) => {
              const active = activeTab === tab;
              const tabLabel = tab === "home" ? t("tab_home") :
                               tab === "chat" ? t("tab_chat") :
                               tab === "planner" ? t("tab_scheduler") :
                               tab === "knowledge" ? t("tab_knowledge") :
                               tab === "tools" ? t("tab_tools") :
                               t("tab_about");
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
      {renderAuthModal()}
      {renderOnboardingWizard()}
      {renderProfileSettingsModal()}
      <NutritionLab isOpen={isNutritionLabOpen} onClose={() => setIsNutritionLabOpen(false)} lang={lang} user={user} activePlan={activePlan} />
      <GearVault isOpen={isGearVaultOpen} onClose={() => setIsGearVaultOpen(false)} lang={lang} user={user} activePlan={activePlan} />
    </div>
  );
}
