import { describe, it, expect } from "vitest";
import { parseDayList } from "./TrainingVenueFields";

describe("parseDayList", () => {
  it("reads the JSON text stored on plans, in weekday order", () => {
    expect(parseDayList('["Sunday","Saturday"]')).toEqual(["Saturday", "Sunday"]);
  });

  it("accepts an array and drops anything that is not a weekday", () => {
    expect(parseDayList(["Saturday", "Funday", 3])).toEqual(["Saturday"]);
  });

  it("returns an empty list for missing or malformed values", () => {
    expect(parseDayList(undefined)).toEqual([]);
    expect(parseDayList("not json")).toEqual([]);
    expect(parseDayList({ Saturday: true })).toEqual([]);
  });
});
