import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import RaceBreakdownCard from "./RaceBreakdownCard";

describe("RaceBreakdownCard", () => {
  it("renders empty state message when no races exist", () => {
    render(<RaceBreakdownCard races={[]} lang="en" />);
    expect(screen.getByText(/No athletes currently have an active plan with a target race/i)).toBeDefined();
  });

  it("renders race items with athlete counts and names", () => {
    const mockRaces = [
      {
        race_name: "VMM 50K",
        race_date: "2026-09-20",
        count: 2,
        athletes: [
          { athlete_id: 1, name: "Kylian Vo" },
          { athlete_id: 2, name: "Minh Tran" },
        ],
      },
      {
        race_name: "Dalapa Ultra Trail 70K",
        race_date: "2026-11-15",
        count: 1,
        athletes: [{ athlete_id: 3, name: "Lan Nguyen" }],
      },
    ];

    render(<RaceBreakdownCard races={mockRaces} athletesWithoutRace={1} lang="en" />);

    expect(screen.getByText("VMM 50K")).toBeDefined();
    expect(screen.getByText("2026-09-20")).toBeDefined();
    expect(screen.getByText("2 runners")).toBeDefined();
    expect(screen.getByText("Kylian Vo")).toBeDefined();
    expect(screen.getByText("Minh Tran")).toBeDefined();

    expect(screen.getByText("Dalapa Ultra Trail 70K")).toBeDefined();
    expect(screen.getByText("1 runner")).toBeDefined();
    expect(screen.getByText("Lan Nguyen")).toBeDefined();

    expect(screen.getByText("Athletes without target race:")).toBeDefined();
    expect(screen.getByText("1")).toBeDefined();
  });

  it("triggers onSelectRace callback when clicking a race", () => {
    const onSelectRace = vi.fn();
    const mockRaces = [
      {
        race_name: "VMM 50K",
        race_date: "2026-09-20",
        count: 2,
        athletes: [{ athlete_id: 1, name: "Kylian Vo" }],
      },
    ];

    render(<RaceBreakdownCard races={mockRaces} onSelectRace={onSelectRace} lang="en" />);
    fireEvent.click(screen.getByText("VMM 50K"));
    expect(onSelectRace).toHaveBeenCalledWith("VMM 50K");
  });
});
