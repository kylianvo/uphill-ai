import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import ResultFeedback from "./ResultFeedback";

describe("ResultFeedback", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders nothing without a token (cached or unscored result)", () => {
    const { container } = render(<ResultFeedback token={null} lang="en" />);
    expect(container.firstChild).toBeNull();
  });

  it("posts the signed token with the vote and marks it pressed", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{}", { status: 200 }));
    render(<ResultFeedback token="tok" lang="en" />);

    fireEvent.click(screen.getByRole("button", { name: "Helpful" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toContain("/api/feedback/result");
    expect(JSON.parse(String((init as RequestInit).body))).toEqual({ token: "tok", value: 1 });
    expect(screen.getByRole("button", { name: "Helpful" }).getAttribute("aria-pressed")).toBe("true");
  });

  it("reverts the vote when the server rejects it", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{}", { status: 400 }));
    render(<ResultFeedback token="tok" lang="vi" />);

    fireEvent.click(screen.getByRole("button", { name: "Chưa hữu ích" }));

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Chưa hữu ích" }).getAttribute("aria-pressed")).toBe("false")
    );
  });
});
