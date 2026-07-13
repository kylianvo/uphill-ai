import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { RaceNameField } from "./RaceNameField";
import { RaceMatch } from "../hooks/useRaceMatch";

function jsonResponse(body: unknown, ok = true) {
  return { ok, json: async () => body } as Response;
}

function Harness({ onMatchChange }: { onMatchChange?: (m: RaceMatch | null) => void }) {
  const [value, setValue] = React.useState("");
  return (
    <RaceNameField value={value} onChange={setValue} lang="en" onMatchChange={onMatchChange} placeholder="race" />
  );
}

describe("RaceNameField", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    localStorage.clear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders a confirmation chip and reports the match when auto-applying", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        matched: true,
        auto_apply: true,
        match: {
          race_name: "Vietnam Mountain Marathon",
          distance_label: "50km",
          distance_km: 46.7,
          elevation_gain_m: 2800,
          terrain: [],
        },
      })
    );
    const onMatchChange = vi.fn();
    render(<Harness onMatchChange={onMatchChange} />);

    fireEvent.change(screen.getByPlaceholderText("race"), { target: { value: "VMM" } });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    expect(screen.getByText("Vietnam Mountain Marathon")).toBeInTheDocument();
    expect(screen.getByText("Change")).toBeInTheDocument();
    expect(onMatchChange).toHaveBeenLastCalledWith(
      expect.objectContaining({ race_name: "Vietnam Mountain Marathon" })
    );
  });

  it("renders a candidate dropdown instead of a chip when the match is ambiguous", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        matched: true,
        auto_apply: false,
        match: {
          race_name: "Marathon du Mont-Blanc",
          distance_label: null,
          distance_km: null,
          elevation_gain_m: null,
          terrain: [],
        },
        candidates: [
          {
            race_name: "Marathon du Mont-Blanc",
            distance_label: "42km",
            distance_km: 42,
            elevation_gain_m: 2500,
            terrain: [],
            score: 100,
          },
          {
            race_name: "Cross du Mont-Blanc",
            distance_label: "23km",
            distance_km: 23,
            elevation_gain_m: 1400,
            terrain: [],
            score: 100,
          },
        ],
      })
    );
    render(<Harness />);

    fireEvent.change(screen.getByPlaceholderText("race"), { target: { value: "Marathon du Mont Blanc" } });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    expect(screen.getByRole("listbox")).toBeInTheDocument();
    expect(screen.getAllByRole("option")).toHaveLength(2);
    expect(screen.queryByText("Change")).not.toBeInTheDocument();
  });

  it("selects a candidate via keyboard (ArrowDown + Enter) and collapses to the chip", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        matched: true,
        auto_apply: false,
        match: {
          race_name: "Marathon du Mont-Blanc",
          distance_label: null,
          distance_km: null,
          elevation_gain_m: null,
          terrain: [],
        },
        candidates: [
          {
            race_name: "Marathon du Mont-Blanc",
            distance_label: "42km",
            distance_km: 42,
            elevation_gain_m: 2500,
            terrain: [],
            score: 100,
          },
          {
            race_name: "Cross du Mont-Blanc",
            distance_label: "23km",
            distance_km: 23,
            elevation_gain_m: 1400,
            terrain: [],
            score: 100,
          },
        ],
      })
    );
    const onMatchChange = vi.fn();
    render(<Harness onMatchChange={onMatchChange} />);

    const input = screen.getByPlaceholderText("race");
    fireEvent.change(input, { target: { value: "Marathon du Mont Blanc" } });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    fireEvent.keyDown(input, { key: "ArrowDown" });
    fireEvent.keyDown(input, { key: "Enter" });

    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(screen.getByText("Cross du Mont-Blanc")).toBeInTheDocument();
    expect(onMatchChange).toHaveBeenLastCalledWith(expect.objectContaining({ race_name: "Cross du Mont-Blanc" }));
  });

  it("Escape dismisses the dropdown without applying a match", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        matched: true,
        auto_apply: false,
        match: {
          race_name: "Marathon du Mont-Blanc",
          distance_label: null,
          distance_km: null,
          elevation_gain_m: null,
          terrain: [],
        },
        candidates: [
          {
            race_name: "Marathon du Mont-Blanc",
            distance_label: "42km",
            distance_km: 42,
            elevation_gain_m: 2500,
            terrain: [],
            score: 100,
          },
          {
            race_name: "Cross du Mont-Blanc",
            distance_label: "23km",
            distance_km: 23,
            elevation_gain_m: 1400,
            terrain: [],
            score: 100,
          },
        ],
      })
    );
    render(<Harness />);

    const input = screen.getByPlaceholderText("race");
    fireEvent.change(input, { target: { value: "Marathon du Mont Blanc" } });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    fireEvent.keyDown(input, { key: "Escape" });

    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(screen.queryByText("Marathon du Mont-Blanc")).not.toBeInTheDocument();
  });

  it("clicking Change on an auto-applied chip reopens the dropdown with the current match", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        matched: true,
        auto_apply: true,
        match: {
          race_name: "Vietnam Mountain Marathon",
          distance_label: "50km",
          distance_km: 46.7,
          elevation_gain_m: 2800,
          terrain: [],
        },
      })
    );
    render(<Harness />);

    const input = screen.getByPlaceholderText("race");
    fireEvent.change(input, { target: { value: "VMM" } });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    fireEvent.click(screen.getByText("Change"));

    expect(screen.getByRole("listbox")).toBeInTheDocument();
    expect(screen.getByRole("option")).toHaveTextContent("Vietnam Mountain Marathon");
  });
});
