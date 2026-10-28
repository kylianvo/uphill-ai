import { describe, it, expect } from "vitest";
import { recommendedRunDays } from "./runDays";

describe("recommendedRunDays", () => {
  it("asks for 4 run days for 50 km and 5 for 100 km+, only when the runner picked fewer", () => {
    expect(recommendedRunDays(56.4, 3)).toBe(4);
    expect(recommendedRunDays(56.4, 4)).toBeNull();
    expect(recommendedRunDays(104.2, 4)).toBe(5);
    expect(recommendedRunDays(104.2, 5)).toBeNull();
    expect(recommendedRunDays(21.1, 3)).toBeNull();
    expect(recommendedRunDays(null, 3)).toBeNull();
  });
});
