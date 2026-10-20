import { describe, it, expect } from "vitest";
import { weekDiffChips } from "./weekDiff";

const wo = (type: string, duration_minutes: number) => ({ type, duration_minutes });

describe("weekDiffChips", () => {
  it("reports time, long-run and session-type changes, ignoring Rest days", () => {
    const prev = [wo("Easy", 60), wo("Easy", 45), wo("Long Run", 105), wo("Rest", 0)];
    const cur = [wo("Easy", 65), wo("Long Run", 115), wo("Muscular Endurance", 45)];
    expect(weekDiffChips(prev, cur)).toEqual([
      { kind: "time", delta: 15 },
      { kind: "long", from: 105, to: 115 },
      { kind: "added", type: "Muscular Endurance", count: 1 },
      { kind: "removed", type: "Easy", count: 1 },
    ]);
  });

  it("is empty when there is no previous week or nothing changed", () => {
    expect(weekDiffChips([], [wo("Easy", 60)])).toEqual([]);
    expect(weekDiffChips([wo("Easy", 60)], [wo("Easy", 60)])).toEqual([]);
  });

  it("reports a drop as a negative delta", () => {
    expect(weekDiffChips([wo("Easy", 100)], [wo("Easy", 75)])).toEqual([{ kind: "time", delta: -25 }]);
  });
});
