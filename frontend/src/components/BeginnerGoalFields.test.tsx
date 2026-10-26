import React, { useState } from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import BeginnerGoalFields, { type BeginnerGoalValue } from "./BeginnerGoalFields";

function Harness({ initial }: { initial?: Partial<BeginnerGoalValue> }) {
  const [v, setV] = useState<BeginnerGoalValue>({ milestone_target: "5k", current_jog_min: 0, event_name: "", event_date: "", ...initial });
  return (
    <>
      <BeginnerGoalFields value={v} onChange={setV} startDate="2026-10-05" lang="en" />
      <output data-testid="out">{JSON.stringify(v)}</output>
    </>
  );
}
const out = () => JSON.parse(screen.getByTestId("out").textContent || "{}");

describe("BeginnerGoalFields", () => {
  it("picks target and current jog", () => {
    render(<Harness />);
    fireEvent.click(screen.getByRole("button", { name: "First 10K" }));
    fireEvent.click(screen.getByRole("button", { name: "10 min" }));
    expect(out()).toMatchObject({ milestone_target: "10k", current_jog_min: 10 });
  });
  it("shows nine path rows for 10K and pre-ticks what the jog already covers", () => {
    render(<Harness initial={{ milestone_target: "10k", current_jog_min: 10 }} />);
    expect(screen.getAllByRole("listitem")).toHaveLength(9);
    expect(screen.getByText("10 min unbroken jog").closest("li")).toHaveTextContent("✓");
  });
  it("warns, but does not block, when the event is too soon", () => {
    render(<Harness />);
    fireEvent.click(screen.getByLabelText("I have an event in mind"));
    fireEvent.change(screen.getByLabelText("Event date"), { target: { value: "2026-11-02" } });
    expect(screen.getByRole("note")).toHaveTextContent("about 9 weeks");
    expect(out().event_date).toBe("2026-11-02");
  });
  it("no warning for an event with room", () => {
    render(<Harness />);
    fireEvent.click(screen.getByLabelText("I have an event in mind"));
    fireEvent.change(screen.getByLabelText("Event date"), { target: { value: "2026-12-12" } });
    expect(screen.queryByRole("note")).toBeNull();
  });
});
