import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import BRaceSetupFields, { completeRaces } from "./BRaceSetupFields";

describe("BRaceSetupFields", () => {
  it("adds up to three races and edits them", () => {
    const onChange = vi.fn();
    const { rerender } = render(<BRaceSetupFields lang="en" value={[]} onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: "+ Add a tune-up race" }));
    expect(onChange).toHaveBeenLastCalledWith([{ race_name: "", race_date: "", distance_km: null }]);
    const three = [1, 2, 3].map((i) => ({ race_name: `R${i}`, race_date: "2026-11-01", distance_km: 21 }));
    rerender(<BRaceSetupFields lang="en" value={three} onChange={onChange} />);
    expect(screen.queryByRole("button", { name: "+ Add a tune-up race" })).toBeNull();
    fireEvent.change(screen.getAllByLabelText("Race")[0], { target: { value: "Ta Xua" } });
    expect(onChange).toHaveBeenLastCalledWith([{ ...three[0], race_name: "Ta Xua" }, three[1], three[2]]);
  });
  it("sends only rows with a name and a date", () => {
    expect(completeRaces([{ race_name: "Ta Xua", race_date: "2026-11-01", distance_km: null },
      { race_name: "", race_date: "2026-11-08", distance_km: 21 }])).toEqual([
      { race_name: "Ta Xua", race_date: "2026-11-01", distance_km: null, effort: "race" },
    ]);
  });
});
