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
});
