// frontend/src/components/landing/renderWithTerms.test.tsx
import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { renderWithTerms } from "./renderWithTerms";

describe("renderWithTerms", () => {
  it("returns the plain text unchanged when there are no markers", () => {
    const nodes = renderWithTerms("Just plain text.", "en");
    render(<>{nodes}</>);
    expect(screen.getByText("Just plain text.")).toBeInTheDocument();
  });

  it("renders a single marker as a TermTooltip trigger surrounded by the rest of the text", () => {
    const nodes = renderWithTerms("Anchored on your {{term:aet}}AeT{{/term}} threshold.", "en");
    render(<p>{nodes}</p>);
    expect(screen.getByText("Anchored on your", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("AeT")).toBeInTheDocument();
    expect(screen.getByText("threshold.", { exact: false })).toBeInTheDocument();
  });

  it("renders multiple markers in the same string", () => {
    const nodes = renderWithTerms("{{term:aet}}AeT{{/term}} and {{term:ant}}AnT{{/term}} both matter.", "en");
    render(<p>{nodes}</p>);
    expect(screen.getByText("AeT")).toBeInTheDocument();
    expect(screen.getByText("AnT")).toBeInTheDocument();
  });
});
