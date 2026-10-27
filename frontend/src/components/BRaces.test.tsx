import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import NextRaces from "./NextRaces";
import AddRaceModal from "./AddRaceModal";
import RaceDebriefModal from "./RaceDebriefModal";
import type { BRace, BRaceAssessment, BRaceVerdict } from "../lib/bRace";

const verdict = (level: BRaceVerdict["level"], over: Partial<BRaceVerdict> = {}): BRaceVerdict => ({
  level, reasons: [], numbers: {}, taper_days: 3, recovery_days: 5, suggestion: null, cost: null, ...over,
});
const race = (over: Partial<BRace> = {}): BRace => ({
  id: 1, race_name: "Ta Xua 25K", race_date: "2026-11-29", distance_km: 25, elevation_gain_m: 1000, effort: "race",
  status: "planned", kept_against: null, verdict: verdict("good"), opinion: "Good test.", predicted: null,
  result_seconds: null, debrief: null, ...over,
});
const plan = { race_name: "VMM 70K", race_date: "2026-12-13", b_races: [race()] };

describe("NextRaces", () => {
  it("lists B-races and the A-race by date with their badges", () => {
    render(<NextRaces plan={plan} lang="en" today="2026-10-26" onAdd={vi.fn()} onOpen={vi.fn()} onDebrief={vi.fn()} />);
    const names = screen.getAllByTestId("next-race-name").map((n) => n.textContent);
    expect(names).toEqual(["Ta Xua 25K", "VMM 70K"]);
    expect(screen.getByText("Good test")).toBeInTheDocument();
    expect(screen.getByText("Goal")).toBeInTheDocument();
  });
  it("asks for a debrief once a race is past", () => {
    const onDebrief = vi.fn();
    render(<NextRaces plan={plan} lang="en" today="2026-11-30" onAdd={vi.fn()} onOpen={vi.fn()} onDebrief={onDebrief} />);
    fireEvent.click(screen.getByRole("button", { name: "How did Ta Xua 25K go?" }));
    expect(onDebrief).toHaveBeenCalledWith(plan.b_races[0]);
  });
});

const assessment = (v: BRaceVerdict): BRaceAssessment => ({
  race: { race_name: "Sapa 50K", race_date: "2026-11-22", distance_km: 50, elevation_gain_m: 2500, effort: "race", options_km: [21, 50] },
  verdict: v, predicted: null,
});

describe("AddRaceModal", () => {
  const fill = () => {
    fireEvent.change(screen.getByLabelText("Race"), { target: { value: "Sapa 50K" } });
    fireEvent.change(screen.getByLabelText("Date"), { target: { value: "2026-11-22" } });
    fireEvent.change(screen.getByLabelText("Distance (km)"), { target: { value: "50" } });
  };

  it("makes the safer option the primary button when the race is risky", async () => {
    const risky = verdict("risky", { reasons: ["overlaps_taper"], suggestion: { distance_km: 21, effort: "training" },
      cost: { changed: [{ week: 9, day: "Saturday", title_before: "Long Run", title_after: "Easy Recovery Run", minutes_before: 300, minutes_after: 45 }], peak_week_minutes: { before: 600, after: 420 } } });
    const assess = vi.fn().mockResolvedValue(assessment(risky));
    const save = vi.fn().mockResolvedValue(true);
    render(<AddRaceModal lang="en" assess={assess} save={save} onClose={vi.fn()} />);
    fill();
    await waitFor(() => expect(screen.getByText("Risky")).toBeInTheDocument());
    expect(screen.getByText(/Long Run → Easy Recovery Run/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Add it as 21 km · as a training run" }));
    await waitFor(() => expect(save).toHaveBeenCalledWith(expect.objectContaining({ distance_km: 21, effort: "training" })));
  });

  it("keeps the runner's choice when they insist", async () => {
    const assess = vi.fn().mockResolvedValue(assessment(verdict("risky", { suggestion: { distance_km: 21, effort: "race" } })));
    const save = vi.fn().mockResolvedValue(true);
    render(<AddRaceModal lang="en" assess={assess} save={save} onClose={vi.fn()} />);
    fill();
    await waitFor(() => screen.getByRole("button", { name: "Keep 50 km anyway" }));
    fireEvent.click(screen.getByRole("button", { name: "Keep 50 km anyway" }));
    await waitFor(() => expect(save).toHaveBeenCalledWith(expect.objectContaining({ distance_km: 50, effort: "race" })));
  });

  it("adds a not-recommended race as a training run", async () => {
    const assess = vi.fn().mockResolvedValue(assessment(verdict("not_recommended", { reasons: ["too_close"] })));
    const save = vi.fn().mockResolvedValue(true);
    render(<AddRaceModal lang="en" assess={assess} save={save} onClose={vi.fn()} />);
    fill();
    await waitFor(() => screen.getByRole("button", { name: "Add as a training run" }));
    fireEvent.click(screen.getByRole("button", { name: "Add as a training run" }));
    await waitFor(() => expect(save).toHaveBeenCalledWith(expect.objectContaining({ effort: "training" })));
  });
});

describe("AddRaceModal editing", () => {
  it("shows the coach's opinion of a saved race", () => {
    render(<AddRaceModal lang="en" race={race({ opinion: "Good test. Run it as a rehearsal." })} assess={vi.fn().mockResolvedValue(assessment(verdict("good")))} save={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByText("Good test. Run it as a rehearsal.")).toBeInTheDocument();
  });
});

describe("RaceDebriefModal", () => {
  it("sends the time and the three answers, then shows the coach's debrief", async () => {
    const submitResult = vi.fn().mockResolvedValue(true);
    const submitDebrief = vi.fn().mockResolvedValue({ debrief: { text: "Fuel worked." }, goal: { suggested_target_hours: null } });
    render(<RaceDebriefModal race={race()} lang="en" submitResult={submitResult} submitDebrief={submitDebrief} onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText("Finish time (h:mm:ss)"), { target: { value: "3:11:00" } });
    fireEvent.click(screen.getByRole("button", { name: "Went to plan" }));
    fireEvent.click(screen.getByRole("button", { name: "Too fast early" }));
    fireEvent.click(screen.getByRole("button", { name: "All good" }));
    fireEvent.click(screen.getByRole("button", { name: "Get my debrief" }));
    await waitFor(() => expect(screen.getByText("Fuel worked.")).toBeInTheDocument());
    expect(submitResult).toHaveBeenCalledWith(11460);
    expect(submitDebrief).toHaveBeenCalledWith({ fuel: "plan", pacing: "fast_start", gear: "ok" });
  });
});
