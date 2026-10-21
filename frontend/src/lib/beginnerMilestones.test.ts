import { describe, it, expect } from "vitest";
import { MILESTONE_KEYS, milestoneLabel, minimumWeeks, headerText, type PlanMilestones } from "./beginnerMilestones";

describe("beginnerMilestones", () => {
  it("has an en and vi label for every key", () => {
    for (const k of MILESTONE_KEYS) {
      expect(milestoneLabel(k, "en")).not.toBe(k);
      expect(milestoneLabel(k, "vi")).not.toBe(k);
    }
  });
  it("minimumWeeks mirrors the backend", () => {
    expect(minimumWeeks("10k", 30)).toBe(9);
    expect(minimumWeeks("5k", 0)).toBe(9);
    expect(minimumWeeks("10k", null)).toBe(17);
  });
  it("headerText counts reached of total and adds the event", () => {
    const ms = { target: "5k", has_event: true, next_key: "jog_10", items: [{ achieved_at: "x" }, { achieved_at: "y" }, { achieved_at: null }] } as unknown as PlanMilestones;
    expect(headerText(ms, "en", 6)).toBe("First 5K · 2 of 3 milestones · 6 weeks to event");
    expect(headerText({ ...ms, has_event: false }, "vi", null)).toBe("5K đầu tiên · 2/3 cột mốc");
  });
});
