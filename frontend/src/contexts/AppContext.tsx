"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */


import React, { createContext, useContext, useState, ReactNode } from "react";
import { Message, ParsedSummary, RagSource, Workout, ActivePlan, PacedCheckpoint, FuelStrategy, Shoe, User } from "../types";

interface AppContextType {
  isNutritionLabOpen: any;
  setIsNutritionLabOpen: any;
  isGearVaultOpen: any;
  setIsGearVaultOpen: any;
  isPaceStrategyOpen: any;
  setIsPaceStrategyOpen: any;
  paceHandoff: any;
  setPaceHandoff: any;
  settingsHandoff: any;
  setSettingsHandoff: any;
  isGoalDeterminerOpen: any;
  setIsGoalDeterminerOpen: any;
  activeTab: any;
  setActiveTab: any;
  lang: "en" | "vi";
  setLang: any;
  startBtnHovered: any;
  setStartBtnHovered: any;
  viewportWidth: any;
  setViewportWidth: any;
  selectedDeviceView: any;
  setSelectedDeviceView: any;
  viewMode: any;
  setViewMode: any;
  heroInput: any;
  setHeroInput: any;
  backendConnected: any;
  setBackendConnected: any;
  chatMessages: any;
  setChatMessages: any;
  chatInput: any;
  setChatInput: any;
  chatLoading: any;
  setChatLoading: any;
  parsedSummary: any;
  setParsedSummary: any;
  parserLoading: any;
  setParserLoading: any;
  uploadedFileName: any;
  setUploadedFileName: any;
  parserErrorMsg: any;
  setParserErrorMsg: any;
  gpxCheckpoints: any;
  setGpxCheckpoints: any;
  sources: any;
  setSources: any;
  linkInput: any;
  setLinkInput: any;
  ragLoading: any;
  setRagLoading: any;
  ragErrorMsg: any;
  setRagErrorMsg: any;
  knowledgeCards: any;
  setKnowledgeCards: any;
  dailyCards: any;
  setDailyCards: any;
  knowledgeTopics: any;
  setKnowledgeTopics: any;
  knowledgeTopic: any;
  setKnowledgeTopic: any;
  extractStatus: any;
  setExtractStatus: any;
  planJobId: any;
  setPlanJobId: any;
  planJobStatus: any;
  setPlanJobStatus: any;
  planJobMessage: any;
  setPlanJobMessage: any;
  activePlan: any;
  setActivePlan: any;
  backupActivePlan: any;
  setBackupActivePlan: any;
  backupWorkouts: any;
  setBackupWorkouts: any;
  recentPlans: any;
  setRecentPlans: any;
  workouts: any;
  setWorkouts: any;
  selectedWeek: any;
  setSelectedWeek: any;
  exportTimePref: any;
  setExportTimePref: any;
  showExportOptions: any;
  setShowExportOptions: any;
  planForm: any;
  setPlanForm: any;
  targetTimeH: any;
  setTargetTimeH: any;
  targetTimeM: any;
  setTargetTimeM: any;
  targetTimeS: any;
  setTargetTimeS: any;
  cutoffTimeH: any;
  setCutoffTimeH: any;
  cutoffTimeM: any;
  setCutoffTimeM: any;
  cutoffTimeS: any;
  setCutoffTimeS: any;
  planLoading: any;
  setPlanLoading: any;
  planErrorMsg: any;
  setPlanErrorMsg: any;
  courseInputMode: any;
  setCourseInputMode: any;
  plannerGpxFile: any;
  setPlannerGpxFile: any;
  plannerGpxLoading: any;
  setPlannerGpxLoading: any;
  plannerGpxError: any;
  setPlannerGpxError: any;
  swapDay1: any;
  setSwapDay1: any;
  swapDay2: any;
  setSwapDay2: any;
  targetFlatPace: any;
  setTargetFlatPace: any;
  pacedCheckpoints: any;
  setPacedCheckpoints: any;
  pacingLoading: any;
  setPacingLoading: any;
  fuelDuration: any;
  setFuelDuration: any;
  fuelSweatRate: any;
  setFuelSweatRate: any;
  fuelTemp: any;
  setFuelTemp: any;
  fuelStrategy: any;
  setFuelStrategy: any;
  fuelLoading: any;
  setFuelLoading: any;
  shoeSurface: any;
  setShoeSurface: any;
  shoeCushion: any;
  setShoeCushion: any;
  shoeWidth: any;
  setShoeWidth: any;
  recommendedShoes: any;
  setRecommendedShoes: any;
  shoesLoading: any;
  setShoesLoading: any;
  user: any;
  setUser: any;
  authModalOpen: any;
  setAuthModalOpen: any;
  mockEmailInput: any;
  setMockEmailInput: any;
  authLoading: any;
  setAuthLoading: any;
  authErrorMsg: any;
  setAuthErrorMsg: any;
  handleLogout: () => void;
  showApiKey: any;
  setShowApiKey: any;
  onboardingOpen: any;
  setOnboardingOpen: any;
  profileSettingsOpen: any;
  setProfileSettingsOpen: any;
  passwordFormOpen: any;
  setPasswordFormOpen: any;
  newPassword: any;
  setNewPassword: any;
  confirmNewPassword: any;
  setConfirmNewPassword: any;
  passwordMsg: any;
  setPasswordMsg: any;
  passwordError: any;
  setPasswordError: any;
  authTab: any;
  setAuthTab: any;
  emailInput: any;
  setEmailInput: any;
  passwordInput: any;
  setPasswordInput: any;
  nameInput: any;
  setNameInput: any;
  confirmPasswordInput: any;
  setConfirmPasswordInput: any;
  showPassword: any;
  setShowPassword: any;
  onboardingStep: any;
  setOnboardingStep: any;
  onboardingAnswers: any;
  setOnboardingAnswers: any;
  onboardingGenerating: any;
  setOnboardingGenerating: any;
  profileForm: any;
  setProfileForm: any;
  onboardingMode: any;
  setOnboardingMode: any;
  raceDistance: any;
  setRaceDistance: any;
  raceTimeHours: any;
  setRaceTimeHours: any;
  raceTimeMinutes: any;
  setRaceTimeMinutes: any;
  easyPaceMin: any;
  setEasyPaceMin: any;
  easyPaceSec: any;
  setEasyPaceSec: any;
  zone2Min: any;
  setZone2Min: any;
  zone2Max: any;
  setZone2Max: any;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: ReactNode }) => {
    const [isNutritionLabOpen, setIsNutritionLabOpen] = useState(false);
  const [isGearVaultOpen, setIsGearVaultOpen] = useState(false);
  const [isPaceStrategyOpen, setIsPaceStrategyOpen] = useState(false);
  const [isGoalDeterminerOpen, setIsGoalDeterminerOpen] = useState(false);
  // Race context handed between tools (Pace Strategy → Nutrition/Gear,
  // Goal Determiner → Pace Strategy)
  const [paceHandoff, setPaceHandoff] = useState<{
    duration_hours?: number;
    weather_temp?: "cool" | "moderate" | "hot";
    race_name?: string;
    distance_label?: string;
    distance_km?: number;
    target_time_mins?: number;
  } | null>(null);
  // Goal Determiner → Plan Settings: hands a chosen goal's target time back
  // into the create-plan form, one-shot like paceHandoff above.
  const [settingsHandoff, setSettingsHandoff] = useState<{
    target_time_mins?: number;
    source_label?: string;
  } | null>(null);
  const [activeTab, setActiveTab] = useState<"home" | "about" | "chat" | "planner" | "tools" | "knowledge">("home");
  const [lang, setLang] = useState<"en" | "vi">("en");
  const [startBtnHovered, setStartBtnHovered] = useState(false);
  const [viewportWidth, setViewportWidth] = useState<number>(1024);
  const [selectedDeviceView, setSelectedDeviceView] = useState<"laptop" | "phone">("laptop");
  const [viewMode, setViewMode] = useState<"showcase" | "desktop" | "mobile">("showcase");
  const [heroInput, setHeroInput] = useState("");
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);
  const [chatMessages, setChatMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I’m Coach Uphill AI. Are you training for a trail ultra or a road marathon?",
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [parsedSummary, setParsedSummary] = useState<ParsedSummary | null>(null);
  const [parserLoading, setParserLoading] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState("");
  const [parserErrorMsg, setParserErrorMsg] = useState("");
  const [gpxCheckpoints, setGpxCheckpoints] = useState<any[]>([]);
  const [sources, setSources] = useState<RagSource[]>([]);
  const [linkInput, setLinkInput] = useState("");
  const [ragLoading, setRagLoading] = useState(false);
  const [ragErrorMsg, setRagErrorMsg] = useState("");
  const [knowledgeCards, setKnowledgeCards] = useState<any[]>([]);
  const [dailyCards, setDailyCards] = useState<any[]>([]);
  const [knowledgeTopics, setKnowledgeTopics] = useState<string[]>([]);
  const [knowledgeTopic, setKnowledgeTopic] = useState("All");
  const [extractStatus, setExtractStatus] = useState<{status: string; current_topic?: string; progress?: number; total?: number; card_count?: number}>({ status: "idle" });
  const [planJobId, setPlanJobId] = useState<string | null>(null);
  const [planJobStatus, setPlanJobStatus] = useState<"idle" | "generating" | "done" | "error">("idle");
  const [planJobMessage, setPlanJobMessage] = useState("");
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
    goal_type: "time",
    terrain: "trail",
    course_distance_km: "",
    course_elevation_gain_m: "",
    days_per_week: 4,
    long_run_day: "Saturday",
    preferred_days: ["Monday", "Wednesday", "Saturday"] as string[],
    has_gym_access: false,
    use_treadmill: false,
    training_environment: "flat" as "flat" | "hilly" | "mixed",
    double_session_days: [] as string[],
    plan_goal_category: "race" as string,  // race | distance | start_running | return | recovery
    plan_start_date: new Date().toISOString().split("T")[0],
    plan_duration_weeks: 12,
    time_away: "",
    fitness_feel: "",
    race_distance_completed: "",
    days_since_race: "",
    recovery_feel: "",
  });
  const [targetTimeH, setTargetTimeH] = useState("");
  const [targetTimeM, setTargetTimeM] = useState("");
  const [targetTimeS, setTargetTimeS] = useState("");
  const [cutoffTimeH, setCutoffTimeH] = useState("");
  const [cutoffTimeM, setCutoffTimeM] = useState("");
  const [cutoffTimeS, setCutoffTimeS] = useState("");
  const [planLoading, setPlanLoading] = useState(false);
  const [planErrorMsg, setPlanErrorMsg] = useState("");
  const [courseInputMode, setCourseInputMode] = useState<"manual" | "gpx">("manual");
  const [plannerGpxFile, setPlannerGpxFile] = useState<File | null>(null);
  const [plannerGpxLoading, setPlannerGpxLoading] = useState(false);
  const [plannerGpxError, setPlannerGpxError] = useState("");
  const [swapDay1, setSwapDay1] = useState("Wednesday");
  const [swapDay2, setSwapDay2] = useState("Thursday");
  const [targetFlatPace, setTargetFlatPace] = useState("6.0");
  const [pacedCheckpoints, setPacedCheckpoints] = useState<PacedCheckpoint[]>([]);
  const [pacingLoading, setPacingLoading] = useState(false);
  const [fuelDuration, setFuelDuration] = useState("4.0");
  const [fuelSweatRate, setFuelSweatRate] = useState("moderate");
  const [fuelTemp, setFuelTemp] = useState("moderate");
  const [fuelStrategy, setFuelStrategy] = useState<FuelStrategy | null>(null);
  const [fuelLoading, setFuelLoading] = useState(false);
  const [shoeSurface, setShoeSurface] = useState("trail");
  const [shoeCushion, setShoeCushion] = useState("balanced");
  const [shoeWidth, setShoeWidth] = useState("normal");
  const [recommendedShoes, setRecommendedShoes] = useState<Shoe[]>([]);
  const [shoesLoading, setShoesLoading] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [mockEmailInput, setMockEmailInput] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [authErrorMsg, setAuthErrorMsg] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [onboardingOpen, setOnboardingOpen] = useState(false);
  const [profileSettingsOpen, setProfileSettingsOpen] = useState(false);
  const [passwordFormOpen, setPasswordFormOpen] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [passwordMsg, setPasswordMsg] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [authTab, setAuthTab] = useState<"signin" | "register">("signin");
  const [emailInput, setEmailInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [nameInput, setNameInput] = useState("");
  const [confirmPasswordInput, setConfirmPasswordInput] = useState("");
  const [showPassword, setShowPassword] = useState(false);
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
    training_environment: "flat" as "flat" | "hilly" | "mixed",
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


  const handleLogout = () => {
    localStorage.removeItem("uphill_session_token");
    setUser(null);
    setActivePlan(null);
    setWorkouts([]);
    setSources([]);
    setProfileSettingsOpen(false);
  };

  return (
    <AppContext.Provider value={{
      isNutritionLabOpen, setIsNutritionLabOpen,
      isGearVaultOpen, setIsGearVaultOpen,
      isPaceStrategyOpen, setIsPaceStrategyOpen,
      paceHandoff, setPaceHandoff,
      settingsHandoff, setSettingsHandoff,
      isGoalDeterminerOpen, setIsGoalDeterminerOpen,
      activeTab, setActiveTab,
      lang, setLang,
      startBtnHovered, setStartBtnHovered,
      viewportWidth, setViewportWidth,
      selectedDeviceView, setSelectedDeviceView,
      viewMode, setViewMode,
      heroInput, setHeroInput,
      backendConnected, setBackendConnected,
      chatMessages, setChatMessages,
      chatInput, setChatInput,
      chatLoading, setChatLoading,
      parsedSummary, setParsedSummary,
      parserLoading, setParserLoading,
      uploadedFileName, setUploadedFileName,
      parserErrorMsg, setParserErrorMsg,
      gpxCheckpoints, setGpxCheckpoints,
      sources, setSources,
      linkInput, setLinkInput,
      ragLoading, setRagLoading,
      ragErrorMsg, setRagErrorMsg,
      knowledgeCards, setKnowledgeCards,
      dailyCards, setDailyCards,
      knowledgeTopics, setKnowledgeTopics,
      knowledgeTopic, setKnowledgeTopic,
      extractStatus, setExtractStatus,
      planJobId, setPlanJobId,
      planJobStatus, setPlanJobStatus,
      planJobMessage, setPlanJobMessage,
      activePlan, setActivePlan,
      backupActivePlan, setBackupActivePlan,
      backupWorkouts, setBackupWorkouts,
      recentPlans, setRecentPlans,
      workouts, setWorkouts,
      selectedWeek, setSelectedWeek,
      exportTimePref, setExportTimePref,
      showExportOptions, setShowExportOptions,
      planForm, setPlanForm,
      targetTimeH, setTargetTimeH,
      targetTimeM, setTargetTimeM,
      targetTimeS, setTargetTimeS,
      cutoffTimeH, setCutoffTimeH,
      cutoffTimeM, setCutoffTimeM,
      cutoffTimeS, setCutoffTimeS,
      planLoading, setPlanLoading,
      planErrorMsg, setPlanErrorMsg,
      courseInputMode, setCourseInputMode,
      plannerGpxFile, setPlannerGpxFile,
      plannerGpxLoading, setPlannerGpxLoading,
      plannerGpxError, setPlannerGpxError,
      swapDay1, setSwapDay1,
      swapDay2, setSwapDay2,
      targetFlatPace, setTargetFlatPace,
      pacedCheckpoints, setPacedCheckpoints,
      pacingLoading, setPacingLoading,
      fuelDuration, setFuelDuration,
      fuelSweatRate, setFuelSweatRate,
      fuelTemp, setFuelTemp,
      fuelStrategy, setFuelStrategy,
      fuelLoading, setFuelLoading,
      shoeSurface, setShoeSurface,
      shoeCushion, setShoeCushion,
      shoeWidth, setShoeWidth,
      recommendedShoes, setRecommendedShoes,
      shoesLoading, setShoesLoading,
      user, setUser,
      authModalOpen, setAuthModalOpen,
      mockEmailInput, setMockEmailInput,
      authLoading, setAuthLoading,
      authErrorMsg, setAuthErrorMsg,
      handleLogout,
      showApiKey, setShowApiKey,
      onboardingOpen, setOnboardingOpen,
      profileSettingsOpen, setProfileSettingsOpen,
      passwordFormOpen, setPasswordFormOpen,
      newPassword, setNewPassword,
      confirmNewPassword, setConfirmNewPassword,
      passwordMsg, setPasswordMsg,
      passwordError, setPasswordError,
      authTab, setAuthTab,
      emailInput, setEmailInput,
      passwordInput, setPasswordInput,
      nameInput, setNameInput,
      confirmPasswordInput, setConfirmPasswordInput,
      showPassword, setShowPassword,
      onboardingStep, setOnboardingStep,
      onboardingAnswers, setOnboardingAnswers,
      onboardingGenerating, setOnboardingGenerating,
      profileForm, setProfileForm,
      onboardingMode, setOnboardingMode,
      raceDistance, setRaceDistance,
      raceTimeHours, setRaceTimeHours,
      raceTimeMinutes, setRaceTimeMinutes,
      easyPaceMin, setEasyPaceMin,
      easyPaceSec, setEasyPaceSec,
      zone2Min, setZone2Min,
      zone2Max, setZone2Max,
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useAppContext must be used within an AppProvider");
  }
  return context;
};
