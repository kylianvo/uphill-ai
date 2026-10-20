import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import WeekBrief from "./WeekBrief";

const chips = [
  { kind: "time" as const, delta: -25 },
  { kind: "long" as const, from: 105, to: 115 },
  { kind: "removed" as const, type: "Easy", count: 1 },
];
const brief = { why: "Week 1 was 33% complete, so this week holds.", benefits: ["Long Run: durability"], watch: "Keep Sunday easy." };

describe("WeekBrief", () => {
  it("renders nothing without chips or a brief", () => {
    const { container } = render(<WeekBrief chips={[]} brief={null} lang="en" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the change chips and the coach's reasons in English", () => {
    render(<WeekBrief chips={chips} brief={brief} lang="en" />);
    expect(screen.getByText("−25 min")).toBeInTheDocument();
    expect(screen.getByText("Long Run 105 → 115 min")).toBeInTheDocument();
    expect(screen.getByText("−1 Easy")).toBeInTheDocument();
    expect(screen.getByText(/Why this week/)).toBeInTheDocument();
    expect(screen.getByText(/this week holds/)).toBeInTheDocument();
    expect(screen.getByText("Long Run: durability")).toBeInTheDocument();
    expect(screen.getByText(/Keep Sunday easy/)).toBeInTheDocument();
  });

  it("uses Vietnamese labels and units", () => {
    render(<WeekBrief chips={chips} brief={brief} lang="vi" />);
    expect(screen.getByText("−25 phút")).toBeInTheDocument();
    expect(screen.getByText("Long Run 105 → 115 phút")).toBeInTheDocument();
    expect(screen.getByText(/Lý do tuần này/)).toBeInTheDocument();
    expect(screen.getByText("So với tuần trước")).toBeInTheDocument();
  });

  it("shows only the chips when no brief was written", () => {
    render(<WeekBrief chips={chips} lang="en" />);
    expect(screen.getByText("−25 min")).toBeInTheDocument();
    expect(screen.queryByText(/Why this week/)).not.toBeInTheDocument();
  });
});
