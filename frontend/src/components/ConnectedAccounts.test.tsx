import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ConnectedAccounts from "./ConnectedAccounts";

// useDeviceConnection is Task 7's hook, reviewed and shipped separately. Each
// test below replaces it with a small stateful fake so we control exactly
// what `status`/`loading`/`error` the component sees, without re-testing the
// hook's own fetch plumbing (that lives in useDeviceConnection.test.ts).
const mockUseDeviceConnection = vi.fn();
vi.mock("../hooks/useDeviceConnection", () => ({
  useDeviceConnection: (...args: unknown[]) => mockUseDeviceConnection(...args),
}));

// ConnectedAccounts reads `lang` from AppContext, the same source
// ProfileSettingsModal.tsx uses (`const { lang } = ctx`) -- not a prop, per
// the existing pattern already used by other standalone components such as
// PendingInviteBanner.tsx. Default to "en"; individual tests override it.
const mockUseAppContext = vi.fn();
vi.mock("../contexts/AppContext", () => ({
  useAppContext: (...args: unknown[]) => mockUseAppContext(...args),
}));

function baseHook(overrides: Record<string, unknown> = {}) {
  return {
    status: null,
    loading: false,
    error: "",
    refreshStatus: vi.fn(),
    connectCoros: vi.fn(async () => ""),
    disconnectCoros: vi.fn(async () => {}),
    syncNow: vi.fn(async () => null),
    ...overrides,
  };
}

describe("ConnectedAccounts", () => {
  const originalLocation = window.location;

  beforeEach(() => {
    mockUseDeviceConnection.mockReset();
    mockUseAppContext.mockReset();
    mockUseAppContext.mockReturnValue({ lang: "en" });
    // @ts-expect-error -- jsdom's location is not directly assignable
    delete window.location;
    // @ts-expect-error -- minimal stand-in so we can observe navigation attempts
    window.location = { href: "http://localhost/settings" };
  });

  afterEach(() => {
    window.location = originalLocation;
  });

  it("shows the disconnected state with a Connect action", () => {
    mockUseDeviceConnection.mockReturnValue(
      baseHook({ status: { coros: { connected: false } } })
    );
    render(<ConnectedAccounts />);
    expect(screen.getByText("Not connected")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Connect" })).toBeInTheDocument();
  });

  it("shows the connected state with COROS attribution", () => {
    mockUseDeviceConnection.mockReturnValue(
      baseHook({
        status: { coros: { connected: true, last_sync_at: "2026-09-01T00:00:00Z" } },
      })
    );
    render(<ConnectedAccounts />);
    expect(screen.getByText(/Last synced/)).toBeInTheDocument();
    expect(screen.getByText(/Data provided by COROS/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sync now" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Disconnect" })).toBeInTheDocument();
  });

  it("renders a placeholder shape (not a blank or wrong-state row) while the first status check is in flight", () => {
    mockUseDeviceConnection.mockReturnValue(baseHook({ status: null, loading: true }));
    render(<ConnectedAccounts />);
    expect(screen.getByText("Checking connection...")).toBeInTheDocument();
    // Must not prematurely claim either connection state before the fetch resolves.
    expect(screen.queryByText("Not connected")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Connect" })).not.toBeInTheDocument();
  });

  it("does not navigate and surfaces the error when connectCoros fails", async () => {
    const user = userEvent.setup();
    // Mirrors the real hook's confirmed hazard: connectCoros() does not
    // throw, it records the failure in `error` and resolves to "".
    let error = "";
    const connectCoros = vi.fn(async () => {
      error = "COROS connection is unavailable.";
      rerenderHook();
      return "";
    });
    const rerenderHook = () =>
      mockUseDeviceConnection.mockReturnValue(
        baseHook({ status: { coros: { connected: false } }, error, connectCoros })
      );
    rerenderHook();

    const { rerender } = render(<ConnectedAccounts />);
    await user.click(screen.getByRole("button", { name: "Connect" }));
    rerender(<ConnectedAccounts />);

    await waitFor(() => {
      expect(screen.getByText("COROS connection is unavailable.")).toBeInTheDocument();
    });
    // The bug this guards against: `window.location.href = await connectCoros()`
    // with no check navigates to "" (i.e. reloads the current page) and the
    // error above is never seen.
    expect(window.location.href).toBe("http://localhost/settings");
  });

  it("renders Vietnamese copy, not English, when lang is vi", () => {
    mockUseAppContext.mockReturnValue({ lang: "vi" });
    mockUseDeviceConnection.mockReturnValue(
      baseHook({ status: { coros: { connected: false } } })
    );
    render(<ConnectedAccounts />);
    expect(screen.getByText("Chưa kết nối")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Kết nối" })).toBeInTheDocument();
    expect(screen.queryByText("Not connected")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Connect" })).not.toBeInTheDocument();
  });

  it("translates a known hook error message to Vietnamese when lang is vi", () => {
    mockUseAppContext.mockReturnValue({ lang: "vi" });
    mockUseDeviceConnection.mockReturnValue(
      baseHook({
        status: { coros: { connected: false } },
        error: "COROS connection is unavailable.",
      })
    );
    render(<ConnectedAccounts />);
    expect(
      screen.getByText("Không thể kết nối COROS lúc này. Vui lòng thử lại sau.")
    ).toBeInTheDocument();
    expect(screen.queryByText("COROS connection is unavailable.")).not.toBeInTheDocument();
  });
});
