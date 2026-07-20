import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FeatureGrid } from "./FeatureGrid";
import { LANDING_FEATURES } from "../../data/landingFeatures";

describe("FeatureGrid", () => {
  it("renders one card per feature with its tagline", () => {
    render(<FeatureGrid lang="en" isMobile={false} />);
    for (const feature of LANDING_FEATURES) {
      expect(screen.getByText(feature.en.tagline)).toBeInTheDocument();
    }
  });

  it("opens the matching modal when a card is clicked, and closes it on close", () => {
    render(<FeatureGrid lang="en" isMobile={false} />);
    const nutrition = LANDING_FEATURES.find((f) => f.id === "nutrition")!;

    expect(screen.queryByText(nutrition.en.overview)).not.toBeInTheDocument();

    fireEvent.click(screen.getByText(nutrition.en.tagline));
    expect(screen.getByText(nutrition.en.overview)).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("Close"));
    expect(screen.queryByText(nutrition.en.overview)).not.toBeInTheDocument();
  });
});
