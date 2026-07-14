import { describe, it, expect } from "vitest";
import {
  parsePaceToMinutes,
  formatDurationHM,
  formatDurationHMS,
  synthesizeCourse,
  addClockEtas,
  sliderBoundsMins,
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

  it("builds an out-and-back style elevation profile that returns to start", () => {
    const course = synthesizeCourse(10, 500);
    expect(course[course.length - 1].elevation_meters).toBeCloseTo(course[0].elevation_meters);
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
