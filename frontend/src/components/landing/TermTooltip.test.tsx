import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TermTooltip } from "./TermTooltip";

describe("TermTooltip", () => {
  it("renders the trigger children and hides the definition initially", () => {
    render(<TermTooltip termKey="aet" lang="en">AeT</TermTooltip>);
    expect(screen.getByText("AeT")).toBeInTheDocument();
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("shows the English definition on click", () => {
    render(<TermTooltip termKey="aet" lang="en">AeT</TermTooltip>);
    fireEvent.click(screen.getByText("AeT"));
    expect(screen.getByRole("tooltip")).toHaveTextContent("shifts from mostly burning fat");
  });

  it("shows the Vietnamese definition when lang is vi", () => {
    render(<TermTooltip termKey="aet" lang="vi">AeT</TermTooltip>);
    fireEvent.click(screen.getByText("AeT"));
    expect(screen.getByRole("tooltip")).toHaveTextContent("chuyển từ đốt mỡ");
  });

  it("closes when clicking outside", () => {
    render(
      <div>
        <TermTooltip termKey="aet" lang="en">AeT</TermTooltip>
        <span data-testid="outside">outside</span>
      </div>
    );
    fireEvent.click(screen.getByText("AeT"));
    expect(screen.getByRole("tooltip")).toBeInTheDocument();
    fireEvent.mouseDown(screen.getByTestId("outside"));
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("renders only children for an unknown term key without crashing", () => {
    render(<TermTooltip termKey={"not_a_real_key" as never} lang="en">Mystery</TermTooltip>);
    expect(screen.getByText("Mystery")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
