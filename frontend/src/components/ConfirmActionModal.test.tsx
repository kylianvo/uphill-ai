/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ConfirmActionModal from "./ConfirmActionModal";

describe("ConfirmActionModal", () => {
  it("does not render when isOpen is false", () => {
    const { container } = render(
      <ConfirmActionModal
        isOpen={false}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        title="Test Title"
        message="Test message body"
      />
    );
    expect(screen.queryByText("Test Title")).toBeNull();
    expect(container.firstChild).toBeNull();
  });

  it("renders title, message, and buttons when isOpen is true", () => {
    render(
      <ConfirmActionModal
        isOpen={true}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        title="Generate New Block"
        message="Are you sure you want to generate Block 2?"
        confirmLabel="Generate"
        cancelLabel="Back"
      />
    );

    expect(screen.getByText("Generate New Block")).toBeDefined();
    expect(screen.getByText("Are you sure you want to generate Block 2?")).toBeDefined();
    expect(screen.getByText("Generate")).toBeDefined();
    expect(screen.getByText("Back")).toBeDefined();
  });

  it("calls onConfirm when confirm button is clicked", () => {
    const onConfirm = vi.fn();
    render(
      <ConfirmActionModal
        isOpen={true}
        onClose={vi.fn()}
        onConfirm={onConfirm}
        title="Confirm Plan"
        message="Confirm creating this plan"
        confirmLabel="Create Plan"
      />
    );

    const btn = screen.getByText("Create Plan");
    fireEvent.click(btn);
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when cancel or close button is clicked", () => {
    const onClose = vi.fn();
    render(
      <ConfirmActionModal
        isOpen={true}
        onClose={onClose}
        onConfirm={vi.fn()}
        title="Confirm Plan"
        message="Confirm creating this plan"
        cancelLabel="Nevermind"
      />
    );

    const cancelBtn = screen.getByText("Nevermind");
    fireEvent.click(cancelBtn);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose on Escape key", () => {
    const onClose = vi.fn();
    render(
      <ConfirmActionModal
        isOpen={true}
        onClose={onClose}
        onConfirm={vi.fn()}
        title="Confirm Plan"
        message="Confirm creating this plan"
      />
    );

    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
