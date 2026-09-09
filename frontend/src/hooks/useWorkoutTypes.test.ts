import { describe, it, expect } from "vitest";
import { resolveWorkoutInfo, WorkoutTypeEntry } from "./useWorkoutTypes";

function makeType(overrides: Partial<WorkoutTypeEntry>): WorkoutTypeEntry {
  return {
    type_key: "easy_run",
    display_name: "Easy Run",
    zone: "Z2",
    color: "#00aa00",
    overview: "",
    execution: "",
    benefit: "",
    warning: "",
    lang: "en",
    ...overrides,
  };
}

describe("resolveWorkoutInfo", () => {
  it("matches via the direct backend type -> type_key mapping", () => {
    const dbTypes = [makeType({ type_key: "tempo_run", color: "#ff0000" })];
    const info = resolveWorkoutInfo("Anything", "tempo", dbTypes);
    expect(info?.color).toBe("#ff0000");
  });

  it("prefers a title keyword match over the direct type mapping", () => {
    const dbTypes = [
      makeType({ type_key: "tempo_run", color: "#ff0000" }),
      makeType({ type_key: "interval", color: "#00ff00" }),
    ];
    // Title mentions "interval" explicitly even though the raw type is "tempo".
    const info = resolveWorkoutInfo("Aerobic Base + Interval Sprints", "tempo", dbTypes);
    expect(info?.color).toBe("#00ff00");
  });

  it("falls back to the static workout library when no dbTypes are provided", () => {
    const info = resolveWorkoutInfo("Easy Run", "easy", []);
    expect(info).toMatchObject({ zone: "easy", color: "#3b82f6" });
  });

  it("returns null when neither dbTypes nor the static fallback have a match", () => {
    const dbTypes = [makeType({ type_key: "tempo_run" })];
    const info = resolveWorkoutInfo("Totally Unrelated Title", "unknown-type", dbTypes);
    expect(info).toBeNull();
  });

  describe("a title must not escalate a session the type already calls easy", () => {
    // Regression: a beginner's "Aerobic Base: Progressive Walk-Jog Intervals" (type Easy)
    // matched the `interval` key on the word "Intervals" and rendered red / "Zone 4-5".
    const dbTypes = [
      makeType({ type_key: "easy_run", zone: "easy", color: "#3b82f6" }),
      makeType({ type_key: "long_run", zone: "moderate", color: "#10b981" }),
      makeType({ type_key: "interval", zone: "hard", color: "#ef4444" }),
    ];

    it("keeps an Easy walk-jog easy despite 'Intervals' in the title", () => {
      const info = resolveWorkoutInfo("Aerobic Base: Progressive Walk-Jog Intervals", "Easy", dbTypes);
      expect(info).toMatchObject({ zone: "easy", color: "#3b82f6" });
    });

    it("keeps a Long Run moderate despite 'Intervals' in the title", () => {
      const info = resolveWorkoutInfo("Aerobic Base: Foundation Long Run Intervals", "Long Run", dbTypes);
      expect(info).toMatchObject({ zone: "moderate", color: "#10b981" });
    });

    it("still lets a genuinely hard compound session escalate", () => {
      // "tempo" is not a non-escalating type, so the title may still refine it.
      const info = resolveWorkoutInfo("Aerobic Base + Interval Sprints", "tempo", [
        ...dbTypes,
        makeType({ type_key: "tempo_run", zone: "tempo", color: "#f59e0b" }),
      ]);
      expect(info).toMatchObject({ zone: "hard" });
    });

    it("applies the same guard in the static library fallback (no dbTypes)", () => {
      const info = resolveWorkoutInfo("Aerobic Base: Progressive Walk-Jog Intervals", "Easy", []);
      expect(info?.zone).toBe("easy");
    });
  });
});
