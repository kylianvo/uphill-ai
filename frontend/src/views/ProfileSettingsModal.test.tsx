/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ProfileSettingsModal from "./ProfileSettingsModal";

const mockSetUser = vi.fn();
const mockSetProfileSettingsOpen = vi.fn();
const mockFetchPaceZones = vi.fn();
const mockTriggerHaptic = vi.fn();

const mockUser = { id: 1, name: "Test Athlete", email: "athlete@uphill.ai", pace_zone_model: "5_zone" as const };

vi.mock("../contexts/AppContext", () => ({
  useAppContext: () => ({
    lang: "en",
    user: mockUser,
    setUser: mockSetUser,
    profileSettingsOpen: true,
    setProfileSettingsOpen: mockSetProfileSettingsOpen,
    profileForm: {
      age: "30",
      gender: "male",
      height_cm: "175",
      weight_kg: "70",
      max_hr: "185",
      resting_hr: "50",
      aet_hr: "140",
      ant_hr: "168",
      zone2_pace_min: "5:30",
      zone2_pace_max: "5:00",
      gemini_api_key: "",
    },
    setProfileForm: vi.fn(),
    activePlan: null,
    setActivePlan: vi.fn(),
    workouts: [],
    setWorkouts: vi.fn(),
    setSources: vi.fn(),
    setAuthModalOpen: vi.fn(),
    setOnboardingOpen: vi.fn(),
    handleLogout: vi.fn(),
  }),
}));

vi.mock("../hooks/usePaceZones", () => ({
  usePaceZones: () => ({
    zones: null,
    loading: false,
    fetchPaceZones: mockFetchPaceZones,
    syncFitness: vi.fn(),
  }),
}));

vi.mock("../utils/native", () => ({
  triggerHaptic: () => mockTriggerHaptic(),
}));

vi.mock("../components/ConnectedAccounts", () => ({
  default: () => <div data-testid="connected-accounts-stub" />,
}));

describe("ProfileSettingsModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem("uphill_session_token", "test-token");
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 1, name: "Test Athlete", aet_hr: 140 }),
    }) as any;
  });

  it("shows success alert and triggers haptic feedback when profile is saved successfully", async () => {
    render(<ProfileSettingsModal />);

    const saveButton = screen.getByRole("button", { name: /Save Settings/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      const alerts = screen.getAllByTestId("profile-save-success-alert");
      expect(alerts.length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/Physiology profile updated successfully!/i)[0]).toBeInTheDocument();
    });
    expect(mockTriggerHaptic).toHaveBeenCalled();
  });
});
