import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProfileExplainer } from "./ProfileExplainer";

describe("ProfileExplainer", () => {
  it("renders the English heading and all 6 input chips", () => {
    render(<ProfileExplainer lang="en" />);
    expect(screen.getByText("Your Profile")).toBeInTheDocument();
    expect(screen.getByText("AeT / AnT thresholds")).toBeInTheDocument();
    expect(screen.getByText("Goal race terrain & elevation")).toBeInTheDocument();
  });

  it("renders the Vietnamese heading and chips", () => {
    render(<ProfileExplainer lang="vi" />);
    expect(screen.getByText("Hồ sơ của bạn")).toBeInTheDocument();
    expect(screen.getByText("Ngưỡng AeT / AnT")).toBeInTheDocument();
  });
});
