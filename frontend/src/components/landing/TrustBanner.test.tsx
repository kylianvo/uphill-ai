import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TrustBanner } from "./TrustBanner";

describe("TrustBanner", () => {
  it("shows the English trust message", () => {
    render(<TrustBanner lang="en" />);
    expect(screen.getByText(/Training for the Uphill Athlete/)).toBeInTheDocument();
  });

  it("shows the Vietnamese trust message", () => {
    render(<TrustBanner lang="vi" />);
    expect(screen.getByText(/Nguyên tắc tập luyện dựa trên/)).toBeInTheDocument();
  });
});
