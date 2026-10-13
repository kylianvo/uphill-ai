import React from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RaceHistoryPanel from "./RaceHistoryPanel";
const pending = { id: 7, claim_id: 1, source: "vbm", discipline: "road", race_name: "City Marathon", race_date: "2023-12-03", distance_km: 42.195, elevation_gain_m: null, finish_time_sec: 13154, is_dnf: false, bib: "42", selected: false, hidden: false, verified: false, verification_methods: [], user_note: null, rank_overall: 30, total_overall: 100 };
function history(selected = false) {
  const fm = selected ? { result_id: 7, time_sec: 13154, date: "2023-12-03", stale: true } : null;
  return { claims: [], results: [{ ...pending, selected }], summary: { trail_finishes: 0, trail_dnfs: 0, ultras: 0, longest_finish: null, road_hm_pr: null, road_fm_pr: fm, road_prs: { "5k": null, "10k": null, hm: null, fm } } };
}
beforeEach(() => { localStorage.setItem("uphill_session_token", "test"); });
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
it("confirms a pending result and refreshes road PBs", async () => {
  let selected = false;
  vi.stubGlobal("fetch", vi.fn(async (_url: string, init?: RequestInit) => {
    if (init?.method === "PATCH") { expect(JSON.parse(String(init.body))).toEqual({ selected: true }); selected = true; }
    return new Response(JSON.stringify(history(selected)), { status: 200 });
  }));
  render(<RaceHistoryPanel lang="en" initiallyOpen />);
  await userEvent.click(await screen.findByRole("button", { name: "This is my result" }, { timeout: 10000 }));
  expect(await screen.findByRole("heading", { name: "Road personal bests" })).toBeInTheDocument();
  await waitFor(() => expect(screen.queryByRole("button", { name: "This is my result" })).not.toBeInTheDocument());
  expect(screen.getAllByText("3:39:14").length).toBeGreaterThan(0);
}, 15000);
it("distinguishes a successful write from a failed following refresh", async () => {
  let wrote = false;
  vi.stubGlobal("fetch", vi.fn(async (_url: string, init?: RequestInit) => {
    if (init?.method === "PATCH") { wrote = true; return new Response(JSON.stringify({ ...pending, selected: true })); }
    return wrote ? new Response(JSON.stringify({ detail: "Unavailable" }), { status: 503 }) : new Response(JSON.stringify(history()));
  }));
  render(<RaceHistoryPanel lang="en" initiallyOpen />);
  await userEvent.click(await screen.findByRole("button", { name: "This is my result" }, { timeout: 10000 }));
  expect(await screen.findByText("Saved, but refresh failed. Retry.")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
});
it("keeps coached athlete race history read-only", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(history(true)))));
  render(<RaceHistoryPanel lang="en" initiallyOpen athleteId={3} />);
  await screen.findByText("City Marathon");
  expect(screen.queryByRole("button", { name: "Not my result" })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument();
});
