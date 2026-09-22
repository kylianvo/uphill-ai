import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { parseMarkdown } from "./markdown";

describe("parseMarkdown citation pill rendering", () => {
  it("converts raw hex hashes into clean superscript citation pills", () => {
    const text = "Muscular endurance requires high local fatigue [7c9d28178ee9].";
    const citations = [
      {
        ref: "7c9d28178ee9",
        book: "Training for the Uphill Athlete",
        chapter: "Chapter 7: Muscular Endurance",
        section: "Section Three: Strength Training for the Uphill Athlete",
        title: "Difference Between Muscular Endurance and Conventional Strength Training",
      },
    ];

    const handleClick = vi.fn();
    const { container } = render(
      <div>
        {parseMarkdown(text, { citations, onCitationClick: handleClick })}
      </div>
    );

    // Should NOT render raw hex hash
    expect(container.textContent).not.toContain("7c9d28178ee9");

    // Should render [1] button
    const pill = screen.getByRole("button", { name: /Citation/i });
    expect(pill).toBeDefined();
    expect(pill.textContent).toBe("[1]");
    expect(pill.getAttribute("title")).toContain("Training for the Uphill Athlete — Chapter 7: Muscular Endurance");

    // Clicking should invoke callback
    fireEvent.click(pill);
    expect(handleClick).toHaveBeenCalledTimes(1);
    expect(handleClick).toHaveBeenCalledWith(citations[0]);
  });

  it("handles numeric markers like [1] directly", () => {
    const text = "Rest 48 hours after ME workouts [1].";
    const citations = [
      {
        ref: "abc12345",
        citation_label: "Training for the Uphill Athlete — Chapter 7: Muscular Endurance",
      },
    ];

    const { container } = render(
      <div>
        {parseMarkdown(text, { citations })}
      </div>
    );

    const pill = screen.getByRole("button", { name: /Citation/i });
    expect(pill).toBeDefined();
    expect(pill.textContent).toBe("[1]");
    expect(pill.getAttribute("title")).toBe("Training for the Uphill Athlete — Chapter 7: Muscular Endurance");
  });
});
