/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import MeView from "./MeView";

const handleTabSwitch = vi.fn();
const setLang = vi.fn();
const handleLogout = vi.fn();
const setProfileSettingsOpen = vi.fn();
let ctx: any;

vi.mock("../contexts/AppContext", () => ({ useAppContext: () => ctx }));
vi.mock("../hooks/usePaceZones", () => ({
  usePaceZones: () => ({
    zones: { zone2_pace: "6:00", zone4_pace: "5:00", threshold_pace: "4:50", zone5_pace: "4:20" },
    fetchPaceZones: vi.fn(),
  }),
}));
vi.mock("../components/ConnectedAccounts", () => ({ default: () => <div>connected-accounts</div> }));
vi.mock("../components/RaceHistoryPanel", () => ({ default: () => <div>race-history-panel</div> }));

beforeEach(() => {
  vi.clearAllMocks();
  ctx = { handleTabSwitch, setLang, handleLogout, setProfileSettingsOpen, lang: "en", user: { name: "Ana" }, activePlan: { id: 1 } };
});

describe("MeView", () => {
  it("renders sections with a plan", () => {
    render(<MeView isMobile />);
    expect(screen.getByText("Ana")).toBeTruthy();
    expect(screen.getByText("6:00 /km")).toBeTruthy();
    expect(screen.getByText("4:50 /km")).toBeTruthy();
    expect(screen.getByText("4:20 /km")).toBeTruthy();
    expect(screen.getByText("connected-accounts")).toBeTruthy();
    expect(screen.getByText("race-history-panel")).toBeTruthy();
    fireEvent.click(screen.getByText("Edit profile"));
    expect(setProfileSettingsOpen).toHaveBeenCalledWith(true);
  });

  it("shows empty paces state without a plan", () => {
    ctx.activePlan = null;
    render(<MeView isMobile />);
    expect(screen.getByText("Paces appear once you have a plan.")).toBeTruthy();
    expect(screen.getByText("connected-accounts")).toBeTruthy();
  });

  it("More rows navigate and act", () => {
    render(<MeView isMobile />);
    fireEvent.click(screen.getByText("Gear Finder"));
    expect(handleTabSwitch).toHaveBeenCalledWith("tools");
    fireEvent.click(screen.getByText("Knowledge Hub"));
    expect(handleTabSwitch).toHaveBeenCalledWith("knowledge");
    fireEvent.click(screen.getByText("About Uphill"));
    expect(handleTabSwitch).toHaveBeenCalledWith("about");
    fireEvent.click(screen.getByText("Language"));
    expect(setLang).toHaveBeenCalledWith("vi");
    fireEvent.click(screen.getByText("Sign out"));
    expect(handleLogout).toHaveBeenCalled();
  });
});
