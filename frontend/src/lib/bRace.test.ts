import { describe, it, expect } from "vitest";
import { formatHms, needsDebrief, parseHms, suggestionLabel, type BRace } from "./bRace";

describe("bRace helpers", () => {
  it("formats and parses race times", () => {
    expect(formatHms(11460)).toBe("3:11:00");
    expect(parseHms("3:11:00")).toBe(11460);
    expect(parseHms("3:11")).toBe(11460);
    expect(parseHms("3:75")).toBeNull();
    expect(parseHms("fast")).toBeNull();
  });
  it("labels a suggestion", () => {
    expect(suggestionLabel({ distance_km: 25, effort: "race" }, "en")).toBe("25 km");
    expect(suggestionLabel({ distance_km: 42, effort: "training" }, "en")).toBe("42 km · as a training run");
  });
  it("asks for a debrief only once the race is past and not debriefed", () => {
    const r = { race_date: "2026-11-01", status: "planned", debrief: null } as BRace;
    expect(needsDebrief(r, "2026-10-31")).toBe(false);
    expect(needsDebrief(r, "2026-11-02")).toBe(true);
    expect(needsDebrief({ ...r, debrief: { text: "ok" } }, "2026-11-02")).toBe(false);
  });
});
