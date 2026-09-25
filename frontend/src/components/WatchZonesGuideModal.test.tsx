import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import WatchZonesGuideModal from "./WatchZonesGuideModal";

describe("WatchZonesGuideModal", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("does not render when isOpen is false", () => {
    const { container } = render(<WatchZonesGuideModal isOpen={false} onClose={vi.fn()} lang="en" />);
    expect(container.firstChild).toBeNull();
  });

  it("renders watch platforms and threshold explanations in English", () => {
    render(<WatchZonesGuideModal isOpen={true} onClose={vi.fn()} lang="en" />);
    expect(screen.getByText(/How to Find Your Heart Rate Zones & Thresholds/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Garmin" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "COROS" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Apple Watch" })).toBeInTheDocument();
    expect(screen.getByText(/Aerobic Threshold \(AeT\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Anaerobic Threshold \(AnT\)/i)).toBeInTheDocument();
  });

  it("renders watch platforms and threshold explanations in Vietnamese", () => {
    render(<WatchZonesGuideModal isOpen={true} onClose={vi.fn()} lang="vi" />);
    expect(screen.getByText(/Cách tìm Zone nhịp tim & Ngưỡng thể chất/i)).toBeInTheDocument();
    expect(screen.getByText(/Ngưỡng hiếu khí \(AeT\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Ngưỡng kỵ khí \(AnT\)/i)).toBeInTheDocument();
  });

  it("allows copying the prompt to clipboard and shows feedback", async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: writeTextMock,
      },
    });

    render(<WatchZonesGuideModal isOpen={true} onClose={vi.fn()} lang="en" />);
    const copyButton = screen.getByRole("button", { name: /Copy Prompt/i });
    fireEvent.click(copyButton);

    expect(writeTextMock).toHaveBeenCalled();
    await waitFor(() => {
      expect(screen.getByText(/Copied!/i)).toBeInTheDocument();
    });
  });
});
