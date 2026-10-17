import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
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

const mountains = [
  { key: "nui_dinh", area: "hcmc", name_en: "Núi Dinh", name_vi: "Núi Dinh", climb_rate: 60, repeats_only: false, default_min_minutes: 180 },
  { key: "dalat", area: "dalat", name_en: "Dalat trails", name_vi: "Trail Đà Lạt", climb_rate: 47, repeats_only: false, default_min_minutes: null },
];
beforeEach(() => vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => mountains })));
afterEach(() => vi.unstubAllGlobals());

function renderFields(initial: Partial<TrainingVenueValue> = {}) {
  const onChange = vi.fn();
  function Fields() {
    const [value, setValue] = useState<TrainingVenueValue>({ mountain_days: [], stair_access: false, treadmill_max_incline: 15, ...initial });
    return <TrainingVenueFields lang="en" t={key => translations.en[key]} value={value} useTreadmill={false} onChange={patch => {
      onChange(patch); setValue(v => ({ ...v, ...patch }));
    }} />;
  }
  render(<Fields />);
  return onChange;
}

it("reveals place, then days, while keeping duration optional", async () => {
  const onChange = renderFields();
  expect(screen.queryByRole("combobox")).toBeNull();
  expect(screen.queryByRole("button", { name: "Sat" })).toBeNull();
  fireEvent.click(screen.getByRole("radio", { name: "Yes" }));
  await screen.findByRole("option", { name: "Núi Dinh" });
  expect(screen.queryByRole("button", { name: "Sat" })).toBeNull();
  fireEvent.change(screen.getByLabelText("Where do you usually train?"), { target: { value: "nui_dinh" } });
  fireEvent.click(screen.getByRole("button", { name: "Sat" }));
  expect(onChange).toHaveBeenLastCalledWith({ mountain_days: ["Saturday"] });
  expect(screen.queryByRole("spinbutton")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Duration settings" }));
  expect(screen.getByLabelText("Minimum duration (min)")).toHaveValue(180);
  fireEvent.change(screen.getByLabelText("Minimum duration (min)"), { target: { value: "210" } });
  expect(onChange).toHaveBeenLastCalledWith({ mountain_min_minutes: 210 });
  fireEvent.click(screen.getByRole("button", { name: "Use location default" }));
  expect(onChange).toHaveBeenLastCalledWith({ mountain_min_minutes: 180 });
  expect(screen.queryByRole("spinbutton")).toBeNull();
});

it("clears only Trail settings when access is turned off", () => {
  const onChange = renderFields({ training_mountain: "nui_dinh", mountain_days: ["Saturday"], mountain_min_minutes: 210, stair_access: true });
  fireEvent.click(screen.getByRole("radio", { name: "Not right now" }));
  expect(onChange).toHaveBeenLastCalledWith({ training_mountain: null, mountain_days: [], mountain_min_minutes: null });
  expect(screen.queryByRole("combobox")).toBeNull();
  expect(screen.getByRole("checkbox", { name: translations.en.plan_stair_access })).toBeChecked();
  fireEvent.click(screen.getByRole("radio", { name: "Yes" }));
  expect(screen.queryByRole("button", { name: "Sat" })).toBeNull();
});

it("keeps a saved custom minimum visible in the collapsed summary", async () => {
  const onChange = renderFields({ training_mountain: "nui_dinh", mountain_days: ["Sunday"], mountain_min_minutes: 210 });
  await screen.findByRole("option", { name: "Núi Dinh" });
  expect(screen.getByRole("radio", { name: "Yes" })).toBeChecked();
  expect(screen.getByRole("button", { name: "Sun" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByText("Minimum Long Run duration: 210 min")).toBeInTheDocument();
  expect(screen.queryByRole("spinbutton")).toBeNull();
  expect(onChange).not.toHaveBeenCalled();
});

it("supports Other and clears the old minimum when changing location", async () => {
  const onChange = renderFields({ training_mountain: "nui_dinh", mountain_days: ["Sunday"], mountain_min_minutes: 210 });
  await screen.findByRole("option", { name: "Dalat trails" });
  fireEvent.change(screen.getByLabelText("Where do you usually train?"), { target: { value: "dalat" } });
  expect(onChange).toHaveBeenLastCalledWith({ training_mountain: "dalat", mountain_min_minutes: null });
  fireEvent.change(screen.getByLabelText("Where do you usually train?"), { target: { value: "other" } });
  expect(onChange).toHaveBeenLastCalledWith({ training_mountain: null, mountain_min_minutes: null });
  expect(screen.getByRole("button", { name: "Sun" })).toHaveAttribute("aria-pressed", "true");
});

it("reopens older Trail day settings without requiring a catalog location", () => {
  renderFields({ mountain_days: ["Sunday"] });
  expect(screen.getByLabelText("Where do you usually train?")).toHaveValue("other");
  expect(screen.getByRole("button", { name: "Sun" })).toHaveAttribute("aria-pressed", "true");
});

it("allows Other while locations fail and can retry the catalog", async () => {
  vi.mocked(fetch).mockRejectedValueOnce(new Error("offline"));
  renderFields();
  fireEvent.click(screen.getByRole("radio", { name: "Yes" }));
  await screen.findByRole("alert");
  fireEvent.change(screen.getByLabelText("Where do you usually train?"), { target: { value: "other" } });
  expect(screen.getByRole("button", { name: "Sat" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Retry locations" }));
  await screen.findByRole("option", { name: "Núi Dinh" });
  expect(screen.queryByRole("alert")).toBeNull();
});
