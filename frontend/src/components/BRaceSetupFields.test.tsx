import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import BRaceSetupFields, { completeRaces, racesBlocked } from "./BRaceSetupFields";

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
  it("blocks a started race the server would drop, and says why", () => {
    const blank = { race_name: "", race_date: "", distance_km: null };
    const ok = { race_name: "Ta Xua", race_date: "2026-11-01", distance_km: 25 };
    expect(racesBlocked([blank, ok], "2026-12-13")).toBe(false);
    expect(racesBlocked([{ ...ok, distance_km: null }], "2026-12-13")).toBe(true);
    expect(racesBlocked([{ ...ok, race_date: "" }], "2026-12-13")).toBe(true);
    expect(racesBlocked([{ ...ok, race_name: " " }], "2026-12-13")).toBe(true);
    expect(racesBlocked([{ ...ok, race_date: "2026-12-13" }], "2026-12-13")).toBe(true);
    render(<BRaceSetupFields lang="vi" goalDate="2026-12-13" value={[blank, { ...ok, distance_km: null }]} onChange={vi.fn()} />);
    expect(screen.getAllByRole("alert")).toHaveLength(1);
    expect(screen.getByRole("alert").textContent).toBe("Thêm tên, cự ly và ngày trước race mục tiêu, hoặc xoá race này.");
  });
});
