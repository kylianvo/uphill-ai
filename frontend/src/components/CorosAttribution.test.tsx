import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import CorosAttribution from "./CorosAttribution";

describe("CorosAttribution", () => {
  it("names COROS as the data source", () => {
    render(<CorosAttribution deviceModel="COROS APEX Pro" />);
    expect(screen.getByText(/COROS/)).toBeInTheDocument();
  });

  it("names the specific device model, which the API agreement requires", () => {
    render(<CorosAttribution deviceModel="COROS APEX Pro" />);
    expect(screen.getByText(/COROS APEX Pro/)).toBeInTheDocument();
  });

  it("still attributes COROS when the device model is unknown", () => {
    // device_model is null when queryDevices returned an unrecognised shape.
    render(<CorosAttribution deviceModel={null} />);
    expect(screen.getByText(/Data provided by COROS/)).toBeInTheDocument();
  });

  it("renders nothing when the data did not come from COROS", () => {
    const { container } = render(<CorosAttribution deviceModel={null} provider="manual" />);
    expect(container).toBeEmptyDOMElement();
  });
});
