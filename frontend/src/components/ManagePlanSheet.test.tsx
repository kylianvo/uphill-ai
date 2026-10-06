/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import BottomSheet from "./BottomSheet";
import ManagePlanSheet from "./ManagePlanSheet";

function Harness() {
  const [open, setOpen] = React.useState(false);
  return (
    <>
      <button onClick={() => setOpen(true)}>trigger</button>
      <BottomSheet isOpen={open} onClose={() => setOpen(false)} title="Sheet">
        <button>inside</button>
      </BottomSheet>
    </>
  );
}

describe("BottomSheet", () => {
  it("moves focus in, closes on Esc, returns focus", () => {
    render(<Harness />);
    const trigger = screen.getByText("trigger");
    trigger.focus();
    fireEvent.click(trigger);
    expect(screen.getByRole("dialog", { name: "Sheet" })).toBeTruthy();
    expect(document.activeElement).toBe(screen.getByLabelText("Close"));
    expect(document.body.style.overflow).toBe("hidden");
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(trigger);
    expect(document.body.style.overflow).toBe("");
  });
  it("closes on backdrop click", () => {
    render(<Harness />);
    fireEvent.click(screen.getByText("trigger"));
    fireEvent.click(screen.getByTestId("bottom-sheet-backdrop"));
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});

const base = (o: any = {}) => ({
  isOpen: true, onClose: vi.fn(), onSync: vi.fn(), syncing: false, syncNotice: null,
  showExportOptions: false, onExport: vi.fn(), recentPlans: [{ id: 7, race_name: "UTMB" }],
  activePlanId: 1, formatPlanName: (p: any) => p.race_name, onSelectPlan: vi.fn(),
  onPlanSettings: vi.fn(), onNewPlan: vi.fn(), ...o,
});

describe("ManagePlanSheet", () => {
  it("each row calls its handler", () => {
    const p = base();
    render(<ManagePlanSheet {...p} />);
    fireEvent.click(screen.getByText("Sync watch"));
    fireEvent.click(screen.getByText("Export calendar"));
    fireEvent.click(screen.getByText("Plan settings"));
    fireEvent.click(screen.getByText("Load a recent plan"));
    fireEvent.click(screen.getByText("UTMB"));
    expect(p.onSync).toHaveBeenCalled();
    expect(p.onExport).toHaveBeenCalled();
    expect(p.onPlanSettings).toHaveBeenCalled();
    expect(p.onSelectPlan).toHaveBeenCalledWith(7);
  });
  it("new plan asks for confirmation", () => {
    const p = base();
    render(<ManagePlanSheet {...p} />);
    fireEvent.click(screen.getByText("Start a new plan"));
    expect(p.onNewPlan).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("Confirm"));
    expect(p.onNewPlan).toHaveBeenCalled();
  });
  it("shows sync notice as status", () => {
    render(<ManagePlanSheet {...base({ syncNotice: { kind: "info", text: "done" } })} />);
    expect(screen.getByRole("status").textContent).toBe("done");
  });
  it("Esc with the confirm open closes only the confirm", () => {
    const p = base();
    render(<ManagePlanSheet {...p} />);
    fireEvent.click(screen.getByText("Start a new plan"));
    expect(screen.getByText("Start a new plan?")).toBeTruthy();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByText("Start a new plan?")).toBeNull();
    expect(screen.getByRole("dialog", { name: "Manage plan" })).toBeTruthy();
    expect(p.onClose).not.toHaveBeenCalled();
  });
  it("Tab is not trapped back into the sheet while the confirm is open", () => {
    render(<ManagePlanSheet {...base()} />);
    fireEvent.click(screen.getByText("Start a new plan"));
    const confirm = screen.getByText("Confirm");
    confirm.focus();
    const notPrevented = fireEvent.keyDown(confirm, { key: "Tab" });
    expect(notPrevented).toBe(true);
    expect(document.activeElement).toBe(confirm);
  });
});
