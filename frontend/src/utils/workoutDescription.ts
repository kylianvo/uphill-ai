export interface DescriptionSections {
  overall: string | null;
  process: string | null;
  reason: string | null;
  benefit: string | null;
  warning: string | null;
}

const SECTION_KEYWORDS = ["Overall", "Process", "Reason", "Benefit", "Warning"] as const;

function extractSection(description: string, keyword: string): string | null {
  const regex = new RegExp(
    `${keyword}[:\\-]\\s*([\\s\\S]*?)(?=(${SECTION_KEYWORDS.join("|")})[:\\-]|$)`,
    "i"
  );
  const match = description.match(regex);
  const value = match ? match[1].trim() : null;
  return value ? value : null;
}

export function extractDescriptionSections(description: string): DescriptionSections {
  return {
    overall: extractSection(description, "Overall"),
    process: extractSection(description, "Process"),
    reason: extractSection(description, "Reason"),
    benefit: extractSection(description, "Benefit"),
    warning: extractSection(description, "Warning"),
  };
}

export interface ExecutionSteps {
  warmup: string | null;
  mainSteps: string[];
  cooldown: string | null;
}

// Parse execution text into warm-up / main steps / cool-down.
// Tries arrow-separated (→) first, falls back to sentence splitting.
export function parseExecutionSteps(execution: string): ExecutionSteps {
  const isWarmup = (s: string) => {
    const l = s.toLowerCase();
    return l.includes("warm") || (l.includes("easy jog") && l.includes("start"));
  };
  const isCooldown = (s: string) => {
    const l = s.toLowerCase();
    return l.includes("cool") || l.includes("stretch");
  };

  const arrowParts = execution.split(/\s*→\s*/).map((s) => s.trim()).filter(Boolean);
  if (arrowParts.length > 1) {
    const warmup: string[] = [];
    const main: string[] = [];
    const cooldown: string[] = [];
    let seenMain = false;

    for (const part of arrowParts) {
      if (!seenMain && isWarmup(part)) {
        warmup.push(part);
      } else if (isCooldown(part)) {
        cooldown.push(part);
      } else {
        main.push(part);
        seenMain = true;
      }
    }

    return {
      warmup: warmup.length > 0 ? warmup.join(" → ") : null,
      mainSteps: main,
      cooldown: cooldown.length > 0 ? cooldown.join(" → ") : null,
    };
  }

  const sentences = execution.split(/(?<=[.!?])\s+/).filter((s) => s.trim().length > 0);
  const warmup: string[] = [];
  const main: string[] = [];
  const cooldown: string[] = [];
  let inCooldown = false;

  for (const s of sentences) {
    if (!main.length && !inCooldown && isWarmup(s)) {
      warmup.push(s);
    } else if (isCooldown(s)) {
      cooldown.push(s);
      inCooldown = true;
    } else if (inCooldown) {
      cooldown.push(s);
    } else {
      main.push(s);
    }
  }

  return {
    warmup: warmup.length > 0 ? warmup.join(" ") : null,
    mainSteps: main.length > 0 ? main : [execution],
    cooldown: cooldown.length > 0 ? cooldown.join(" ") : null,
  };
}

// Extracts the first number found in a warm-up/cool-down text chunk, e.g.
// 15 from "15-minute easy Zone 1/2 warm-up." Returns null if none found.
export function extractLeadingMinutes(text: string | null): number | null {
  if (!text) return null;
  const match = text.match(/(\d+)/);
  return match ? parseInt(match[1], 10) : null;
}

// A workout's total duration_minutes is warm-up + main + cool-down; Main Set
// should display only the main portion. Derives it by subtracting the
// parsed warm-up/cool-down minutes from the total. Falls back to the full
// total when either chunk is missing or has no parseable number, so the
// displayed duration is never blank.
export function mainDurationMinutes(totalMinutes: number, steps: ExecutionSteps): number {
  const warmup = extractLeadingMinutes(steps.warmup);
  const cooldown = extractLeadingMinutes(steps.cooldown);
  if (warmup === null || cooldown === null || totalMinutes <= 0) {
    return totalMinutes;
  }
  return Math.max(0, totalMinutes - warmup - cooldown);
}

export interface LibraryExecutionInfo {
  execution: string;
  overview: string;
}

export interface MainSetText {
  executionText: string;
  overviewText: string;
}

export function selectMainSetText(
  library: LibraryExecutionInfo,
  description?: string | null
): MainSetText {
  const sections = description ? extractDescriptionSections(description) : null;
  return {
    executionText: sections?.process ? sections.process : library.execution,
    overviewText: sections?.overall ? sections.overall : library.overview,
  };
}

export interface CoachNotesContent {
  hasSections: boolean;
  overall: string | null;
  reason: string | null;
  benefit: string | null;
  warning: string | null;
  fallbackText: string;
}

export function buildCoachNotesContent(description: string): CoachNotesContent {
  const sections = extractDescriptionSections(description);
  const hasSections = Boolean(sections.overall || sections.reason || sections.benefit || sections.warning);
  return {
    hasSections,
    overall: sections.overall,
    reason: sections.reason,
    benefit: sections.benefit,
    warning: sections.warning,
    fallbackText: description,
  };
}
