import { describe, it, expect } from "vitest";
import {
  parsePaceToMinutes,
  formatDurationHM,
  formatDurationHMS,
  synthesizeCourse,
  addClockEtas,
  sliderBoundsMins,
  tempBucket,
  parseDurationToMinutes,
  percentilePoints,
  percentileForTime,
} from "./paceStrategy";

describe("parsePaceToMinutes", () => {
  it("parses mm:ss pace strings", () => {
    expect(parsePaceToMinutes("5:30")).toBe(5.5);
    expect(parsePaceToMinutes("10:15")).toBe(10.25);
  });

  it("parses decimal pace strings", () => {
    expect(parsePaceToMinutes("6")).toBe(6);
    expect(parsePaceToMinutes("6.5")).toBe(6.5);
  });

  it("takes the first pace of a range", () => {
    expect(parsePaceToMinutes("6:30-5:45")).toBe(6.5);
  });

  it("returns null for garbage", () => {
    expect(parsePaceToMinutes("")).toBeNull();
    expect(parsePaceToMinutes("fast")).toBeNull();
  });
});

describe("formatDurationHM / formatDurationHMS", () => {
  it("formats minutes as h:mm", () => {
    expect(formatDurationHM(195)).toBe("3:15");
    expect(formatDurationHM(59)).toBe("0:59");
  });

  it("formats minutes as h:mm:ss", () => {
    expect(formatDurationHMS(195.5)).toBe("3:15:30");
  });
});

describe("synthesizeCourse", () => {
  it("builds per-km checkpoints matching the backend shape", () => {
    const course = synthesizeCourse(10, 500);
    // start point + 10 km markers
    expect(course).toHaveLength(11);
    expect(course[0].distance_meters).toBe(0);
    expect(course[10].distance_meters).toBe(10000);
    // gain and loss spread evenly (loss defaults to gain: race loops)
    const totalGain = course.reduce((s, c) => s + c.segment_gain_meters, 0);
    const totalLoss = course.reduce((s, c) => s + c.segment_loss_meters, 0);
    expect(totalGain).toBeCloseTo(500);
    expect(totalLoss).toBeCloseTo(500);
  });

  it("handles fractional final km", () => {
    const course = synthesizeCourse(10.5, 0);
    expect(course[course.length - 1].distance_meters).toBeCloseTo(10500);
  });

  it("preserves total gain and loss for fractional distances", () => {
    const course = synthesizeCourse(5.3, 1000);
    const totalGain = course.reduce((s, c) => s + c.segment_gain_meters, 0);
    const totalLoss = course.reduce((s, c) => s + c.segment_loss_meters, 0);
    expect(totalGain).toBeCloseTo(1000);
    expect(totalLoss).toBeCloseTo(1000);
  });

  it("builds an out-and-back style elevation profile that returns to start", () => {
    const course = synthesizeCourse(10, 500);
    expect(course[course.length - 1].elevation_meters).toBeCloseTo(course[0].elevation_meters);
  });

  it("supports 5k and 10k split intervals with totals preserved", () => {
    const five = synthesizeCourse(42.2, 1000, 1000, 0, 5);
    // start + ceil(42.2/5)=9 markers
    expect(five).toHaveLength(10);
    expect(five[1].distance_meters).toBe(5000);
    expect(five[five.length - 1].distance_meters).toBeCloseTo(42200);
    const totalGain = five.reduce((s, c) => s + c.segment_gain_meters, 0);
    expect(totalGain).toBeCloseTo(1000);

    const ten = synthesizeCourse(100, 5000, 5000, 0, 10);
    expect(ten).toHaveLength(11);
    expect(ten[1].name).toBe("KM 10");
  });
});

describe("addClockEtas", () => {
  const paced = [
    { cumulative_time_mins: 0 },
    { cumulative_time_mins: 60 },
    { cumulative_time_mins: 120 },
  ];

  it("adds start clock time and cumulative rest from earlier checkpoints", () => {
    // 10 min rest taken AT checkpoint 1 delays checkpoint 2's arrival only
    const etas = addClockEtas(paced, [0, 10, 0], "05:00");
    expect(etas).toEqual(["05:00", "06:00", "07:10"]);
  });

  it("rolls past midnight", () => {
    const etas = addClockEtas(paced, [0, 0, 0], "23:30");
    expect(etas[2]).toBe("01:30");
  });

  it("returns elapsed durations when no start time given", () => {
    const etas = addClockEtas(paced, [0, 0, 0]);
    expect(etas[1]).toBe("1:00");
  });
});

describe("parseDurationToMinutes", () => {
  it("parses h:mm:ss race times", () => {
    expect(parseDurationToMinutes("9:10:58")).toBeCloseTo(550.97, 1);
    expect(parseDurationToMinutes("11:52:42")).toBeCloseTo(712.7, 1);
  });

  it("parses h:mm times", () => {
    expect(parseDurationToMinutes("2:30")).toBe(150);
  });

  it("returns null for garbage", () => {
    expect(parseDurationToMinutes("dnf")).toBeNull();
    expect(parseDurationToMinutes("")).toBeNull();
  });
});

describe("tempBucket", () => {
  it("maps forecast temperature to Nutrition Lab buckets", () => {
    expect(tempBucket(8)).toBe("cool");
    expect(tempBucket(20)).toBe("moderate");
    expect(tempBucket(29)).toBe("hot");
  });

  it("defaults to moderate when no forecast", () => {
    expect(tempBucket(null)).toBe("moderate");
    expect(tempBucket(undefined)).toBe("moderate");
  });
});

describe("percentilePoints / percentileForTime", () => {
  const ps = { p10: "14:00:00", p25: "16:00:00", p50: "19:00:00", p75: "22:00:00", p90: "25:00:00" };

  it("parses and sorts percentile anchor points", () => {
    const pts = percentilePoints(ps);
    expect(pts).toHaveLength(5);
    expect(pts[0]).toEqual({ q: 10, mins: 840 });
    expect(pts[4]).toEqual({ q: 90, mins: 1500 });
  });

  it("returns the exact percentile on an anchor hit", () => {
    expect(percentileForTime(ps, 19 * 60)).toEqual({ pct: 50, clamped: null });
  });

  it("interpolates linearly between anchors", () => {
    // halfway between p25 (16h) and p50 (19h) -> 37.5%
    expect(percentileForTime(ps, 17.5 * 60)?.pct).toBeCloseTo(37.5);
  });

  it("clamps faster than p10 without a winner anchor", () => {
    expect(percentileForTime(ps, 12 * 60)).toEqual({ pct: 10, clamped: "fast" });
  });

  it("interpolates between winner and p10 when the winner time is given", () => {
    // winner 10h (0%), p10 14h -> 12h is 5%
    expect(percentileForTime(ps, 12 * 60, 600)?.pct).toBeCloseTo(5);
  });

  it("clamps slower than p90", () => {
    expect(percentileForTime(ps, 27 * 60)).toEqual({ pct: 90, clamped: "slow" });
  });

  it("returns null with fewer than two valid anchors", () => {
    expect(percentileForTime({ p50: "19:00:00" }, 1000)).toBeNull();
    expect(percentileForTime({}, 1000)).toBeNull();
  });
});

describe("sliderBoundsMins", () => {
  it("gives a plausible range for a mountain 70k", () => {
    const { min, max } = sliderBoundsMins(70, 4000);
    expect(min).toBeLessThan(9 * 60); // faster than 9h possible
    expect(max).toBeGreaterThan(16 * 60); // slower than 16h possible
    expect(min).toBeGreaterThan(4 * 60); // but not absurd
  });

  it("scales with distance", () => {
    expect(sliderBoundsMins(100, 5000).max).toBeGreaterThan(sliderBoundsMins(21, 1000).max);
  });
});
