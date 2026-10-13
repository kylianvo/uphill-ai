import { describe, expect, it } from "vitest";
import { formatKm, formatNumber, formatPace, manualResultPayload, safeResultUrl } from "./raceHistory";
const draft = { race_name: "Race", race_date: "2023-12-03", discipline: "road", distance_km: "42.195", finish_time: "3:39:14", is_dnf: false };
describe("race result inputs", () => {
  it("rejects executable and credential-bearing links", () => {
    expect(safeResultUrl("https://example.org/result")).toBe("https://example.org/result");
    expect(safeResultUrl("javascript:alert(1)")).toBeNull();
    expect(safeResultUrl("https://a:b@example.org/result")).toBeNull();
    expect(safeResultUrl(null)).toBeNull();
  });
  it("clears optional metadata and preserves zero elevation", () => {
    const value = manualResultPayload({ ...draft, elevation_gain_m: "0" });
    expect(value.finish_time_sec).toBe(13154); expect(value.location).toBeNull();
    expect(value.result_url).toBeNull(); expect(value.elevation_gain_m).toBe(0);
    expect(value).not.toHaveProperty("finish_time");
  });
  it("rejects invalid ranking-only edits and fractional ranks", () => {
    expect(() => manualResultPayload({ ...draft, rank_overall: "11", total_overall: "10" })).toThrow();
    expect(() => manualResultPayload({ ...draft, rank_gender: "1.2" })).toThrow();
  });
});

describe("display formatting", () => {
  it("formats numbers by app language", () => {
    expect(formatNumber(1234.5, "en")).toBe("1,234.5");
    expect(formatNumber(1234.5, "vi")).toBe("1.234,5");
  });
  it("shows at most one decimal and no trailing .0", () => {
    expect(formatKm(50)).toBe("50");
    expect(formatKm(42.195)).toBe("42.2");
    expect(formatKm(10.04)).toBe("10");
    expect(formatKm(21.1)).toBe("21.1");
  });
  it("rounds pace once before splitting", () => {
    expect(formatPace(359.5)).toBe("6:00");
    expect(formatPace(359.4)).toBe("5:59");
  });
});
