import { describe, it, expect } from "vitest";
import {
  parsePaceToDecimalMinutes,
  calculateTreadmillSettings,
  getTreadmillGuide,
  DEFAULT_TREADMILL_GRADE_PERCENT,
} from "./treadmill";

describe("parsePaceToDecimalMinutes", () => {
  it("parses 'MM:SS /km' into decimal minutes", () => {
    expect(parsePaceToDecimalMinutes("6:00 /km")).toBe(6.0);
    expect(parsePaceToDecimalMinutes("6:30/km")).toBe(6.5);
  });

  it("returns null for missing or unparseable input", () => {
    expect(parsePaceToDecimalMinutes(null)).toBeNull();
    expect(parsePaceToDecimalMinutes(undefined)).toBeNull();
    expect(parsePaceToDecimalMinutes("N/A")).toBeNull();
  });
});

describe("calculateTreadmillSettings", () => {
  it("converts flat pace to speed with no incline adjustment at 0% grade", () => {
    const result = calculateTreadmillSettings(6.0, 0);
    expect(result.speedKph).toBe(10.0);
    expect(result.inclinePercent).toBe(0);
  });

  it("reduces speed as grade increases to hold effort constant", () => {
    const result = calculateTreadmillSettings(6.0, 1.0);
    expect(result.speedKph).toBe(9.6);
    expect(result.inclinePercent).toBe(1.0);
  });

  it("returns zero speed for a non-positive pace", () => {
    const result = calculateTreadmillSettings(0, 1.0);
    expect(result.speedKph).toBe(0);
  });
});

describe("getTreadmillGuide", () => {
  it("prefers the AI's own speed/incline when both are set", () => {
    const guide = getTreadmillGuide("6:00 /km", 9.5, 12.0);
    expect(guide).toEqual({ speedKph: 9.5, inclinePercent: 12.0, estimated: false, gradeSource: "ai" });
  });

  it("derives speed/incline from target pace using the default 1% grade when the AI and outdoor grade are both blank", () => {
    const guide = getTreadmillGuide("6:00 /km", 0, 0);
    expect(guide?.estimated).toBe(true);
    expect(guide?.gradeSource).toBe("default");
    expect(guide?.inclinePercent).toBe(DEFAULT_TREADMILL_GRADE_PERCENT);
    expect(guide?.speedKph).toBe(9.6);
  });

  it("prefers this run's own outdoor grade_percent over the flat default when the AI left incline blank", () => {
    const guide = getTreadmillGuide("6:00 /km", 0, 0, 5.0);
    expect(guide?.estimated).toBe(true);
    expect(guide?.gradeSource).toBe("outdoor-grade");
    expect(guide?.inclinePercent).toBe(5.0);
  });

  it("still prefers an explicit AI incline over the outdoor grade_percent", () => {
    const guide = getTreadmillGuide("6:00 /km", 0, 8.0, 5.0);
    expect(guide?.gradeSource).toBe("ai");
    expect(guide?.inclinePercent).toBe(8.0);
  });

  it("returns null when there is no pace and no AI-supplied settings", () => {
    expect(getTreadmillGuide(null, 0, 0)).toBeNull();
  });

  it("falls back to whatever partial AI value exists when pace is unparseable", () => {
    const guide = getTreadmillGuide(null, 8.0, 0);
    expect(guide).toEqual({ speedKph: 8.0, inclinePercent: 0, estimated: false, gradeSource: "ai" });
  });

  it("passes the backend's range strings through verbatim", () => {
    const guide = getTreadmillGuide("6:30 - 5:45 /km", "8.1-9.2", "2-4");
    expect(guide).toEqual({ speedKph: "8.1-9.2", inclinePercent: "2-4", estimated: false, gradeSource: "ai" });
  });

  it('treats "0" range strings as unset and estimates from pace instead', () => {
    const guide = getTreadmillGuide("6:00 /km", "0", "0");
    expect(guide?.estimated).toBe(true);
    expect(guide?.gradeSource).toBe("default");
  });
});
