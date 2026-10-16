import { describe, it, expect, vi } from "vitest";
import { useState } from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { translations } from "../app/translations";
import { parseDayList, TrainingVenueFields, type TrainingVenueValue } from "./TrainingVenueFields";

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

it("selects the shared mountain and its default minimum", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => [
    { key: "nui_dinh", area: "hcmc", name_en: "Núi Dinh", name_vi: "Núi Dinh", climb_rate: 60, repeats_only: false, default_min_minutes: 180 },
    { key: "dalat", area: "dalat", name_en: "Dalat trails", name_vi: "Trail Đà Lạt", climb_rate: 47, repeats_only: false, default_min_minutes: null },
  ] }));
  const onChange = vi.fn();
  function Fields() {
    const [value, setValue] = useState<TrainingVenueValue>({ mountain_days: [], stair_access: false, treadmill_max_incline: 15 });
    return <TrainingVenueFields lang="en" t={key => translations.en[key]} value={value} useTreadmill={false} onChange={patch => {
      onChange(patch); setValue(v => ({ ...v, ...patch }));
    }} />;
  }
  render(<Fields />);
  await screen.findByRole("option", { name: "Núi Dinh · 60 m D+/km" });
  fireEvent.change(screen.getByLabelText("Training mountain"), { target: { value: "nui_dinh" } });
  expect(onChange).toHaveBeenCalledWith({ training_mountain: "nui_dinh", mountain_min_minutes: 180 });
  expect(screen.getByLabelText("Minimum minutes")).toHaveValue(180);
  fireEvent.change(screen.getByLabelText("Training mountain"), { target: { value: "dalat" } });
  expect(onChange).toHaveBeenLastCalledWith({ training_mountain: "dalat", mountain_min_minutes: null });
  fireEvent.change(screen.getByLabelText("Training mountain"), { target: { value: "" } });
  expect(onChange).toHaveBeenLastCalledWith({ training_mountain: null, mountain_min_minutes: null });
  expect(screen.getByLabelText("Minimum minutes")).toHaveValue(null);
  vi.unstubAllGlobals();
});
