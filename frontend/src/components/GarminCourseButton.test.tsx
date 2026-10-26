import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import GarminCourseButton from "./GarminCourseButton";

const file = new File(["<gpx/>"], "utmb.gpx", { type: "application/gpx+xml" });

function mockFetch(status: unknown, send?: { ok: boolean; body: unknown }) {
  const calls: { url: string; init?: RequestInit }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      if (url.endsWith("/api/integrations/status")) return { ok: true, json: async () => status };
      return { ok: send?.ok ?? false, json: async () => send?.body };
    })
  );
  return calls;
}

afterEach(() => vi.unstubAllGlobals());

describe("GarminCourseButton", () => {
  it("renders nothing unless Garmin is connected", async () => {
    const calls = mockFetch({ garmin: { enabled: true, connected: false } });
    const { container } = render(<GarminCourseButton file={file} name="UTMB" lang="en" />);
    await waitFor(() => expect(calls.length).toBe(1));
    expect(container).toBeEmptyDOMElement();
  });

  it("sends the GPX with the race name and reports the course", async () => {
    const calls = mockFetch({ garmin: { enabled: true, connected: true } }, { ok: true, body: { distance_km: 50.2 } });
    render(<GarminCourseButton file={file} name="UTMB 50K" lang="en" />);
    await userEvent.click(await screen.findByRole("button", { name: "Send course to Garmin" }));
    const send = calls.find((c) => c.url.endsWith("/api/integrations/garmin/course"))!;
    const form = send.init!.body as FormData;
    expect(form.get("name")).toBe("UTMB 50K");
    expect((form.get("file") as File).name).toBe("utmb.gpx");
    expect(await screen.findByText(/Sent a 50.2 km course to Garmin/)).toBeInTheDocument();
  });

  it("explains a missing course permission in Vietnamese", async () => {
    mockFetch(
      { garmin: { enabled: true, connected: true } },
      { ok: false, body: { detail: { code: "GARMIN_no_course_permission" } } }
    );
    render(<GarminCourseButton file={file} name="x" lang="vi" />);
    await userEvent.click(await screen.findByRole("button", { name: "Gửi course sang Garmin" }));
    expect(await screen.findByText(/bật quyền nhập course/)).toBeInTheDocument();
  });
});
