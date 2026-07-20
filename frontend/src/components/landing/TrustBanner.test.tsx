import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TrustBanner } from "./TrustBanner";

describe("TrustBanner", () => {
  it("shows the English trust message", () => {
    render(<TrustBanner lang="en" />);
    expect(screen.getByText(/No hallucinated advice/)).toBeInTheDocument();
  });

  it("shows the Vietnamese trust message", () => {
    render(<TrustBanner lang="vi" />);
    expect(screen.getByText(/Không có lời khuyên bịa đặt/)).toBeInTheDocument();
  });
});
