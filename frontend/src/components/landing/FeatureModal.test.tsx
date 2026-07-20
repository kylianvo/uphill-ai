import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FeatureModal } from "./FeatureModal";
import { LANDING_FEATURES } from "../../data/landingFeatures";

const scheduler = LANDING_FEATURES.find((f) => f.id === "scheduler")!;

describe("FeatureModal", () => {
  it("renders the tagline, overview, and every how-it-works bullet for the given language", () => {
    render(<FeatureModal feature={scheduler} lang="en" onClose={() => {}} />);
    expect(screen.getByText(scheduler.en.tagline)).toBeInTheDocument();
    expect(screen.getByText(scheduler.en.overview)).toBeInTheDocument();
    expect(screen.getByText("AeT")).toBeInTheDocument();
    expect(screen.getByText("AnT")).toBeInTheDocument();
  });

  it("renders the Vietnamese copy when lang is vi", () => {
    render(<FeatureModal feature={scheduler} lang="vi" onClose={() => {}} />);
    expect(screen.getByText(scheduler.vi.tagline)).toBeInTheDocument();
  });

  it("renders every personalized chip", () => {
    render(<FeatureModal feature={scheduler} lang="en" onClose={() => {}} />);
    for (const chip of scheduler.en.personalizedChips) {
      expect(screen.getByText(chip)).toBeInTheDocument();
    }
  });

  it("calls onClose when the close button is clicked", () => {
    const onClose = vi.fn();
    render(<FeatureModal feature={scheduler} lang="en" onClose={onClose} />);
    fireEvent.click(screen.getByLabelText("Close"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
