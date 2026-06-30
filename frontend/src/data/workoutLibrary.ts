export type WorkoutZone = "easy" | "moderate" | "tempo" | "hard" | "strength" | "rest" | "cross";

export interface WorkoutInfo {
  zone: WorkoutZone;
  color: string;
  overview: string;
  execution: string;
  benefit: string;
  warning: string;
}

// Ordered longest-match-first to avoid "easy" matching "easy stride"
const LIBRARY: Array<[string, WorkoutInfo]> = [
  ["recovery run", {
    zone: "easy", color: "#3b82f6",
    overview: "A short, slow run to flush waste products and keep the legs moving without adding training stress.",
    execution: "Zone 1 only. 20–40 min max. Run noticeably slower than your easy pace. Your breathing should be effortless.",
    benefit: "Promotes blood flow that accelerates muscle repair. Keeps the training habit on days between harder efforts without adding meaningful load.",
    warning: "Any pace that elevates HR above Zone 1 turns recovery into work — counterproductive after a hard day. When in doubt, slow down.",
  }],
  ["easy run", {
    zone: "easy", color: "#3b82f6",
    overview: "A comfortable aerobic run at full conversational pace. You should be able to hold a complete sentence.",
    execution: "Run at Zone 1–2 (roughly 60–70% max HR). If you feel like pushing, hold back. The goal is time on feet, not effort.",
    benefit: "Builds your aerobic base, trains fat oxidation, and promotes recovery between harder sessions — the foundation all other fitness builds on.",
    warning: "Most easy runs are run too fast. If in doubt, slow down — this isn't laziness, it's the most important discipline in training.",
  }],
  ["long run", {
    zone: "moderate", color: "#10b981",
    overview: "The signature aerobic workout of the week. The long run builds endurance, fat oxidation, and mental resilience for race distance.",
    execution: "Start 15–20% slower than you feel you should. Hold Zone 2 throughout. The last quarter can feel comfortably hard but never like a race. Fuel every 40–50 min.",
    benefit: "Develops mitochondrial density, grows glycogen storage capacity, trains fat burning at pace, and hardens the mind for race-day distance.",
    warning: "Don't race the long run. Arriving tired-but-not-wrecked is success. Going too hard turns the week's most important session into a recovery problem.",
  }],
  ["trail run", {
    zone: "moderate", color: "#10b981",
    overview: "Running on natural terrain — trails, paths, mountain routes. Focus on effort over pace.",
    execution: "Hike the steep sections when HR climbs above Zone 3. Run the flat and runnable climbs. Effort is the metric, not pace.",
    benefit: "Develops trail-specific movement patterns, foot strength, and the discipline to use HR as a guide on variable terrain.",
    warning: "Trail pace is dramatically slower than road pace — ignore your watch and run by feel and HR.",
  }],
  ["tempo run", {
    zone: "tempo", color: "#f59e0b",
    overview: "A sustained effort at your lactate threshold — comfortably hard. You can speak in short phrases, not sentences.",
    execution: "Warm up 10–15 min easy → hold tempo effort for the prescribed block → cool down 10 min easy. Target pace: roughly 10K to half-marathon race pace.",
    benefit: "Raises your lactate threshold — the speed you can sustain for long races — one of the highest-leverage adaptations in endurance training.",
    warning: "Tempo should feel controlled. If form breaks or you gasp, you're too fast. Find the sustainable edge and hold it.",
  }],
  ["threshold", {
    zone: "tempo", color: "#f59e0b",
    overview: "Sustained effort at or just below your lactate threshold — comfortably hard, breathing audible but rhythmic.",
    execution: "Warm up 10–15 min → sustain Z3–4 for the prescribed block → cool down 10 min. Not a race — a controlled sustained effort.",
    benefit: "Extends the pace you can hold for 30–60 minutes without excessive lactate buildup. Critical for trail race performance.",
    warning: "Threshold is easier to go too hard in than any other session. Aim for the lower end of the effort range.",
  }],
  ["interval", {
    zone: "hard", color: "#ef4444",
    overview: "High-intensity repeats with recovery between efforts. The hardest sessions in your plan — keep them that way.",
    execution: "Warm up 15 min thoroughly → complete prescribed reps at Z5 (very hard, near-maximal) → recovery jog between reps → cool down 10–15 min.",
    benefit: "Develops VO2max, running economy, and race-specific speed — the high-end fitness that tempo alone cannot build.",
    warning: "Full recovery between sessions is mandatory. Intervals must be followed by easy days. Failing to recover from intervals is how overtraining starts.",
  }],
  ["hill repeat", {
    zone: "hard", color: "#ef4444",
    overview: "Sustained hill repeats targeting uphill power, neuromuscular drive, and climbing efficiency.",
    execution: "Find a 6–10% gradient → hold Z4–5 for 60–90 sec → walk or easy jog down fully before the next rep → 6–10 reps.",
    benefit: "Builds leg power, stride rate, and running economy without the impact of flat-ground speed work. Essential for mountain racing.",
    warning: "Full walk-down recovery is the rule — not optional. Descending too fast defeats the purpose and adds unnecessary eccentric load.",
  }],
  ["hill sprint", {
    zone: "hard", color: "#ef4444",
    overview: "Short maximal bursts up a steep hill to develop raw neuromuscular power and stride mechanics.",
    execution: "8–12 sec sprint at absolute maximum up a 8–10% slope → walk down completely → rest 90 sec between reps → 6–12 reps.",
    benefit: "Maximizes neuromuscular recruitment and power output. Produces strength gains in the running-specific muscles without gym equipment.",
    warning: "These are sprints, not runs. If you can hold them for 15 seconds you're not going hard enough.",
  }],
  ["fartlek", {
    zone: "moderate", color: "#f59e0b",
    overview: "Unstructured speed play — mix easy running with surges of effort at your own intuition. From Swedish: 'speed play.'",
    execution: "Easy warm-up → surge when you feel like it (effort level varies freely) → return to easy between surges → total session includes 15–30% hard effort.",
    benefit: "Develops the ability to change pace, responds to natural terrain, and builds aerobic-speed connection without the rigidity of intervals.",
    warning: "Fartlek should feel playful, not prescribed. If it starts to feel like a structured workout, you're doing it wrong.",
  }],
  ["me session", {
    zone: "strength", color: "#8b5cf6",
    overview: "Muscular Endurance — gym circuit targeting the muscles that sustain uphill effort: quads, glutes, calves.",
    execution: "Weighted step-ups, single-leg squats, Romanian deadlifts, calf raises. 3–4 sets of 8–12 reps at moderate weight, controlled tempo. 60–90 sec rest between sets.",
    benefit: "Builds the quad and glute strength that translates to sustained uphill power — the direct difference-maker in mountain and trail races.",
    warning: "ME sessions are taxing. Schedule before a rest day. Stop at the first sign of form breakdown — fatigue-form failure is the injury mechanism.",
  }],
  ["gym-based", {
    zone: "strength", color: "#8b5cf6",
    overview: "Gym session focused on running-specific strength and injury prevention.",
    execution: "Compound movements (squats, deadlifts, lunges, hip hinge). 3–5 sets per exercise with weight that challenges but maintains full ROM.",
    benefit: "Corrects muscular imbalances, improves running economy through better neuromuscular coordination, and is the most effective long-term injury prevention.",
    warning: "Don't strength-train the day before a key run session. Allow 24–36 hours between hard strength and hard run work.",
  }],
  ["strength", {
    zone: "strength", color: "#8b5cf6",
    overview: "General strength training session complementing your running load.",
    execution: "Focus on compound movements: squats, deadlifts, lunges, hip hinge. 3–5 sets per exercise, use weight that challenges while maintaining full range of motion.",
    benefit: "Corrects muscular imbalances, improves running economy through better neuromuscular coordination — the best long-term injury prevention available.",
    warning: "Don't strength-train the day before a key run session. Allow 24–36 hours between hard strength and hard run work.",
  }],
  ["cross-training", {
    zone: "cross", color: "#14b8a6",
    overview: "Non-running cardio — cycling, swimming, elliptical, or hiking. Builds aerobic fitness with reduced ground impact.",
    execution: "Choose a low-impact activity at Z1–2 intensity. Duration matches the run session it replaces. Consistent aerobic work, not intensity, is the goal.",
    benefit: "Maintains or builds aerobic capacity during injury phases, or adds training volume without additional impact stress.",
    warning: "Cross-training doesn't replace running's neural and mechanical adaptations. It's a supplement, not a substitute.",
  }],
  ["rest", {
    zone: "rest", color: "#94a3b8",
    overview: "Complete rest or very gentle movement. This day is as much a part of your training as any hard session.",
    execution: "Nothing that meaningfully raises your heart rate. A gentle walk or 20 min of mobility work is fine. Focus on sleep and nutrition.",
    benefit: "Adaptation happens during rest, not training. Your body repairs microdamage, consolidates fitness gains, and restores glycogen stores.",
    warning: "Don't add a bonus easy run on rest days. The plan placed rest here for a reason. Trust it.",
  }],
];

// Direct type → library key mapping for the AI-generated type values
const TYPE_MAP: Record<string, string> = {
  "easy":               "easy run",
  "long run":           "long run",
  "tempo":              "tempo run",
  "threshold":          "threshold",
  "interval":           "interval",
  "muscular endurance": "me session",
  "strength":           "strength",
  "recovery":           "recovery run",
  "active recovery":    "recovery run",
  "cross-training":     "cross-training",
  "aerobic capacity":   "easy run",
  "walk/run":           "easy run",
  "race":               "rest",
};

export function getWorkoutInfo(title: string, type: string): WorkoutInfo | null {
  // 1. Try direct type mapping first (most reliable)
  const mapped = TYPE_MAP[type.toLowerCase()];
  if (mapped) {
    const entry = LIBRARY.find(([k]) => k === mapped);
    if (entry) return entry[1];
  }
  // 2. Fall back to keyword search across title + type
  const key = `${title} ${type}`.toLowerCase();
  for (const [keyword, info] of LIBRARY) {
    if (key.includes(keyword)) return info;
  }
  return null;
}

export function getZoneColor(targetZone: string, title: string, type: string): string {
  const info = getWorkoutInfo(title, type);
  if (info) return info.color;
  const z = (targetZone || "").toLowerCase();
  if (z.includes("1") || z.includes("2")) return "#3b82f6";
  if (z.includes("3")) return "#f59e0b";
  if (z.includes("4") || z.includes("5")) return "#ef4444";
  return "#6b7280";
}

export const RPE_DESCRIPTORS: Record<number, { label: string; color: string }> = {
  1: { label: "Very easy — barely moving", color: "#3b82f6" },
  2: { label: "Easy — could go all day", color: "#3b82f6" },
  3: { label: "Light — comfortable cruise", color: "#3b82f6" },
  4: { label: "Moderate — aware of the effort", color: "#10b981" },
  5: { label: "Moderate-hard — breathing deepens", color: "#10b981" },
  6: { label: "Comfortably hard — sentences get short", color: "#f59e0b" },
  7: { label: "Hard — focused, controlled", color: "#f59e0b" },
  8: { label: "Very hard — holding on", color: "#f97316" },
  9: { label: "Extremely hard — near max", color: "#ef4444" },
  10: { label: "Maximum — nothing left", color: "#dc2626" },
};
