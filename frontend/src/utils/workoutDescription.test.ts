import { describe, it, expect } from "vitest";
import {
  extractDescriptionSections,
  parseExecutionSteps,
  selectMainSetText,
  buildCoachNotesContent,
  extractLeadingMinutes,
  mainDurationMinutes,
} from "./workoutDescription";

describe("extractDescriptionSections", () => {
  it("extracts all five sections regardless of order", () => {
    const description =
      "Overall: A steady tempo effort.\n" +
      "Process: Warm up 10 min easy → 20 min @ tempo pace → cool down 10 min.\n" +
      "Reason: Building lactate threshold ahead of race week.\n" +
      "Benefit: Improved sustained pace.\n" +
      "Warning: Stop if calf tightness returns.";

    const sections = extractDescriptionSections(description);

    expect(sections.overall).toBe("A steady tempo effort.");
    expect(sections.process).toBe("Warm up 10 min easy → 20 min @ tempo pace → cool down 10 min.");
    expect(sections.reason).toBe("Building lactate threshold ahead of race week.");
    expect(sections.benefit).toBe("Improved sustained pace.");
    expect(sections.warning).toBe("Stop if calf tightness returns.");
  });

  it("is case-insensitive on section headers", () => {
    const description = "OVERALL: Short summary.\nprocess: Do the thing.";
    const sections = extractDescriptionSections(description);
    expect(sections.overall).toBe("Short summary.");
    expect(sections.process).toBe("Do the thing.");
  });

  it("returns null for sections that are not present", () => {
    const description = "Process: Just the steps.";
    const sections = extractDescriptionSections(description);
    expect(sections.process).toBe("Just the steps.");
    expect(sections.overall).toBeNull();
    expect(sections.reason).toBeNull();
    expect(sections.benefit).toBeNull();
    expect(sections.warning).toBeNull();
  });

  it("returns all nulls for unstructured text with no section headers", () => {
    const sections = extractDescriptionSections("Just run easy today, whatever feels good.");
    expect(sections).toEqual({
      overall: null,
      process: null,
      reason: null,
      benefit: null,
      warning: null,
    });
  });
});

describe("parseExecutionSteps", () => {
  it("splits arrow-separated text into warmup/main/cooldown", () => {
    const result = parseExecutionSteps(
      "Warm up 10 min easy jog → 4 x 6min @ Zone 4, 2min jog recovery → cool down 10 min stretch"
    );
    expect(result.warmup).toBe("Warm up 10 min easy jog");
    expect(result.mainSteps).toEqual(["4 x 6min @ Zone 4, 2min jog recovery"]);
    expect(result.cooldown).toBe("cool down 10 min stretch");
  });

  it("falls back to sentence splitting when there are no arrows", () => {
    const result = parseExecutionSteps(
      "Warm up with 10 minutes of easy jogging. Complete 4 sets of 12 squats with 90 seconds rest between sets. Cool down and stretch for 10 minutes."
    );
    expect(result.warmup).toContain("Warm up");
    expect(result.mainSteps.join(" ")).toContain("4 sets of 12 squats");
    expect(result.cooldown).toContain("Cool down");
  });
});

describe("selectMainSetText", () => {
  const library: import("./workoutDescription").LibraryExecutionInfo = {
    execution: "3-4 sets of 8-12 reps at moderate weight.",
    overview: "Strength work builds durability for the descents.",
  };

  it("prefers the AI Process/Overall text when present", () => {
    const description =
      "Overall: Today's specific strength focus.\n" +
      "Process: 5 sets of 10 reps weighted step-ups → 3 sets of 12 lunges each leg.";
    const result = selectMainSetText(library, description);
    expect(result.executionText).toBe("5 sets of 10 reps weighted step-ups → 3 sets of 12 lunges each leg.");
    expect(result.overviewText).toBe("Today's specific strength focus.");
  });

  it("falls back to the library template when there is no description", () => {
    const result = selectMainSetText(library, undefined);
    expect(result.executionText).toBe(library.execution);
    expect(result.overviewText).toBe(library.overview);
  });

  it("falls back to the library template when Process/Overall are empty or whitespace-only", () => {
    const description = "Reason: Scheduled for recovery.\nProcess:    \nOverall:   ";
    const result = selectMainSetText(library, description);
    expect(result.executionText).toBe(library.execution);
    expect(result.overviewText).toBe(library.overview);
  });
});

describe("buildCoachNotesContent", () => {
  it("excludes process but includes reason when sections are present", () => {
    const description =
      "Overall: Summary.\nProcess: Steps that belong in Main Set only.\nReason: Because of last week's RPE.\nBenefit: Adaptation.\nWarning: Watch your knees.";
    const content = buildCoachNotesContent(description);
    expect(content.hasSections).toBe(true);
    expect(content.overall).toBe("Summary.");
    expect(content.reason).toBe("Because of last week's RPE.");
    expect(content.benefit).toBe("Adaptation.");
    expect(content.warning).toBe("Watch your knees.");
    expect(content).not.toHaveProperty("process");
  });

  it("falls back to the raw description text when no sections are found", () => {
    const description = "Just take it easy today.";
    const content = buildCoachNotesContent(description);
    expect(content.hasSections).toBe(false);
    expect(content.fallbackText).toBe(description);
  });
});

describe("extractLeadingMinutes", () => {
  it("extracts the first number found in the text", () => {
    expect(extractLeadingMinutes("15-minute easy Zone 1/2 warm-up.")).toBe(15);
    expect(extractLeadingMinutes("Warmup 10m.")).toBe(10);
  });

  it("returns null for text with no number", () => {
    expect(extractLeadingMinutes("Easy warm-up jog.")).toBeNull();
  });

  it("returns null for null input", () => {
    expect(extractLeadingMinutes(null)).toBeNull();
  });
});

describe("mainDurationMinutes", () => {
  it("subtracts parsed warm-up and cool-down minutes from the total", () => {
    const steps = { warmup: "15-minute easy warm-up.", mainSteps: ["Run tempo."], cooldown: "10-minute cool-down." };
    expect(mainDurationMinutes(60, steps)).toBe(35);
  });

  it("falls back to the total when warm-up is missing", () => {
    const steps = { warmup: null, mainSteps: ["Run tempo."], cooldown: "10-minute cool-down." };
    expect(mainDurationMinutes(60, steps)).toBe(60);
  });

  it("falls back to the total when cool-down text has no parseable number", () => {
    const steps = { warmup: "15-minute easy warm-up.", mainSteps: ["Run tempo."], cooldown: "Easy jog to finish." };
    expect(mainDurationMinutes(60, steps)).toBe(60);
  });

  it("clamps to zero instead of going negative when warm-up+cool-down exceed the total", () => {
    const steps = { warmup: "40-minute warm-up.", mainSteps: ["Run tempo."], cooldown: "40-minute cool-down." };
    expect(mainDurationMinutes(60, steps)).toBe(0);
  });
});
