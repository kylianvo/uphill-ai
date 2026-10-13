import { render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi, beforeEach } from "vitest";
import RaceDetailDialog from "./RaceDetailDialog";
import type { RaceResult } from "../lib/raceHistory";
const result: RaceResult = {
  id: 7,
  claim_id: null,
  source: "vbm",
  race_name: "City Marathon",
  race_date: "2024-06-01",
  discipline: "road",
  distance_km: 42.195,
  elevation_gain_m: null,
  finish_time_sec: null,
  is_dnf: true,
  bib: null,
  selected: false,
  hidden: false,
  user_note: null,
  verified: false,
  verification_methods: [],
  rank_overall: 30,
  total_overall: null,
  result_url: "javascript:alert(1)",
};
beforeEach(() => {
  HTMLDialogElement.prototype.showModal = vi.fn();
  HTMLDialogElement.prototype.close = vi.fn();
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          result,
          performance: { overall_top_pct: null },
          previous_finish: { delta_sec: -846, race_date: "2023-01-01" },
          course_context: {
            status: "missing",
            course: null,
            candidates: [],
            message: null,
          },
          historical_field: null,
        }),
      })
  );
});
it("keeps recorded DNF visible with missing context and readonly controls", async () => {
  render(
    <RaceDetailDialog
      result={result}
      athleteId={3}
      lang="en"
      onClose={vi.fn()}
      onChanged={vi.fn()}
    />
  );
  await waitFor(() =>
    expect(screen.getByText("No course context available")).toBeInTheDocument()
  );
  expect(screen.getByText("City Marathon")).toBeInTheDocument();
  expect(screen.queryByText(/faster/)).not.toBeInTheDocument();
  expect(screen.queryByText(/Top .*%/)).not.toBeInTheDocument();
  expect(screen.queryByRole("link")).not.toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: "This is my result" })
  ).not.toBeInTheDocument();
});
it("ignores a late response after a newer result is opened", async () => {
  let resolveFirst!: (value: unknown) => void;
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveFirst = resolve;
          })
      )
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          result: { ...result, id: 8, race_name: "New race" },
          performance: {},
          previous_finish: null,
          course_context: {
            status: "missing",
            course: null,
            candidates: [],
            message: null,
          },
          historical_field: null,
        }),
      })
  );
  const view = render(
    <RaceDetailDialog
      result={result}
      lang="en"
      onClose={vi.fn()}
      onChanged={vi.fn()}
    />
  );
  view.rerender(
    <RaceDetailDialog
      result={{ ...result, id: 8, race_name: "New race" }}
      lang="en"
      onClose={vi.fn()}
      onChanged={vi.fn()}
    />
  );
  await waitFor(() =>
    expect(screen.getByText("No course context available")).toBeInTheDocument()
  );
  resolveFirst({
    ok: true,
    json: async () => ({
      result,
      performance: {},
      course_context: {
        status: "missing",
        course: null,
        candidates: [],
        message: null,
      },
    }),
  });
  await waitFor(() => expect(screen.getByText("New race")).toBeInTheDocument());
  expect(screen.queryByText("City Marathon")).not.toBeInTheDocument();
});
