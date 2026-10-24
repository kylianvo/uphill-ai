import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import GarminConnection from "./GarminConnection";

describe("GarminConnection", () => {
  it("only connects after the athlete consents to AI coaching on Garmin data", async () => {
    const onConnect = vi.fn();
    render(
      <GarminConnection
        lang="en"
        garmin={{ enabled: true, connected: false }}
        loading={false}
        onConnect={onConnect}
        onDisconnect={vi.fn()}
      />
    );
    const connect = screen.getByRole("button", { name: "Connect" });
    expect(connect).toBeDisabled();

    await userEvent.click(screen.getByRole("checkbox"));
    await userEvent.click(connect);
    expect(onConnect).toHaveBeenCalledOnce();
  });

  it("offers disconnect, which withdraws consent, once connected", async () => {
    const onDisconnect = vi.fn();
    render(
      <GarminConnection
        lang="en"
        garmin={{ enabled: true, connected: true, last_sync_at: null }}
        loading={false}
        onConnect={vi.fn()}
        onDisconnect={onDisconnect}
      />
    );
    expect(screen.getByText("Connected. Data arrives after your next watch sync.")).toBeInTheDocument();
    expect(screen.queryByRole("checkbox")).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: "Disconnect" }));
    expect(onDisconnect).toHaveBeenCalledOnce();
  });
});
