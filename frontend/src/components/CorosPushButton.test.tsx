import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CorosPushButton from "./CorosPushButton";

const fetchPushStatus = vi.fn();
const pushToCoros = vi.fn();
vi.mock("../lib/corosPush", async (orig) => {
  const actual = (await orig()) as Record<string, unknown>;
  return { ...actual, fetchPushStatus: () => fetchPushStatus(), pushToCoros: (l: string) => pushToCoros(l) };
});

beforeEach(() => {
  fetchPushStatus.mockReset();
  pushToCoros.mockReset();
});

describe("CorosPushButton", () => {
  it("renders nothing when COROS is not connected", async () => {
    fetchPushStatus.mockResolvedValue({ connected: false });
    const { container } = render(<CorosPushButton lang="en" refreshKey={1} />);
    await waitFor(() => expect(fetchPushStatus).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the button with the COROS mark and the out-of-date nudge", async () => {
    fetchPushStatus.mockResolvedValue({ connected: true, last_pushed_at: "2027-04-07T08:00:00+00:00", out_of_date: true });
    render(<CorosPushButton lang="en" refreshKey={1} />);
    expect(await screen.findByRole("button", { name: /send to coros/i })).toBeInTheDocument();
    expect(screen.getByAltText("COROS")).toBeInTheDocument();
    expect(screen.getByText("Changes not on your watch yet")).toBeInTheDocument();
  });

  it("sends, then shows the result summary and refreshes status", async () => {
    fetchPushStatus.mockResolvedValue({ connected: true, last_pushed_at: null, out_of_date: false });
    pushToCoros.mockResolvedValue({
      kind: "ok", status: "sent", last_pushed_at: "2027-04-07T08:00:00+00:00",
      summary: { days_sent: 26, workouts_sent: 11, left_in_uphill: 3, locked_days: 1, invalid: 0, window_end: "2027-05-02" },
    });
    render(<CorosPushButton lang="en" refreshKey={1} />);
    await userEvent.click(await screen.findByRole("button", { name: /send to coros/i }));
    expect(pushToCoros).toHaveBeenCalledWith("en");
    expect(await screen.findByText(/Sent 11 workouts to COROS/)).toBeInTheDocument();
    expect(screen.getByText(/3 strength session/)).toBeInTheDocument();
    expect(screen.getByText(/already completed/)).toBeInTheDocument();
    await waitFor(() => expect(fetchPushStatus).toHaveBeenCalledTimes(2));
  });

  it("shows a translated error and the reconnect link when disconnected", async () => {
    fetchPushStatus.mockResolvedValue({ connected: true, last_pushed_at: null });
    pushToCoros.mockResolvedValue({ kind: "error", code: "COROS_not_connected", params: {} });
    render(<CorosPushButton lang="vi" refreshKey={1} />);
    await userEvent.click(await screen.findByRole("button", { name: /gửi sang coros/i }));
    expect(await screen.findByText(/Chưa kết nối COROS/)).toBeInTheDocument();
    expect(screen.getByText("Kết nối lại COROS")).toBeInTheDocument();
  });

  it("opens the reconnect flow when onReconnect is given", async () => {
    fetchPushStatus.mockResolvedValue({ connected: true });
    pushToCoros.mockResolvedValue({ kind: "error", code: "COROS_not_connected", params: {} });
    const onReconnect = vi.fn();
    render(<CorosPushButton lang="en" refreshKey={1} onReconnect={onReconnect} />);
    await userEvent.click(await screen.findByRole("button", { name: /send to coros/i }));
    await userEvent.click(await screen.findByRole("button", { name: "Reconnect COROS" }));
    expect(onReconnect).toHaveBeenCalled();
  });

  it("fills the daily limit into the message", async () => {
    fetchPushStatus.mockResolvedValue({ connected: true });
    pushToCoros.mockResolvedValue({ kind: "error", code: "PUSH_limit", params: { limit: 10 } });
    render(<CorosPushButton lang="en" refreshKey={1} />);
    await userEvent.click(await screen.findByRole("button", { name: /send to coros/i }));
    expect(await screen.findByText(/sent to COROS 10 times today/)).toBeInTheDocument();
  });

  it("disables the button while sending", async () => {
    fetchPushStatus.mockResolvedValue({ connected: true });
    let resolve: (v: unknown) => void = () => {};
    pushToCoros.mockReturnValue(new Promise((r) => (resolve = r)));
    render(<CorosPushButton lang="en" refreshKey={1} />);
    await userEvent.click(await screen.findByRole("button", { name: /send to coros/i }));
    expect(screen.getByRole("button", { name: /sending/i })).toBeDisabled();
    resolve({ kind: "error", code: "COROS_unavailable", params: {} });
  });

  it("refetches status when refreshKey changes", async () => {
    fetchPushStatus.mockResolvedValue({ connected: true });
    const { rerender } = render(<CorosPushButton lang="en" refreshKey={1} />);
    await waitFor(() => expect(fetchPushStatus).toHaveBeenCalledTimes(1));
    rerender(<CorosPushButton lang="en" refreshKey={2} />);
    await waitFor(() => expect(fetchPushStatus).toHaveBeenCalledTimes(2));
  });

  const summary = {
    mode: "plan", days_sent: 4, workouts_sent: 3, left_in_uphill: 0, locked_days: 0, invalid: 0,
    stale: 0, window_end: "2027-07-04", plan_start: "2027-04-07",
  };

  it("says when a far race opens for sending, with a readable date", async () => {
    fetchPushStatus.mockResolvedValue({ connected: true });
    pushToCoros.mockResolvedValue({ kind: "error", code: "RACE_too_far", params: { opens_on: "2027-05-31" } });
    render(<CorosPushButton lang="en" refreshKey={1} />);
    await userEvent.click(await screen.findByRole("button", { name: /send to coros/i }));
    expect(await screen.findByText(/Send to COROS opens on 31 May/)).toBeInTheDocument();
  });

  it("explains a race that is too close, in Vietnamese", async () => {
    fetchPushStatus.mockResolvedValue({ connected: true });
    pushToCoros.mockResolvedValue({ kind: "error", code: "RACE_too_close", params: { weeks: 3 } });
    render(<CorosPushButton lang="vi" refreshKey={1} />);
    await userEvent.click(await screen.findByRole("button", { name: /gửi sang coros/i }));
    expect(await screen.findByText(/chỉ còn 3 tuần/)).toBeInTheDocument();
  });

  it("mentions a COROS plan that starts later than today", async () => {
    fetchPushStatus.mockResolvedValue({ connected: true });
    pushToCoros.mockResolvedValue({
      kind: "ok", status: "sent", last_pushed_at: null, summary: { ...summary, plan_start: "2099-04-19" },
    });
    render(<CorosPushButton lang="en" refreshKey={1} />);
    await userEvent.click(await screen.findByRole("button", { name: /send to coros/i }));
    expect(await screen.findByText(/Your COROS plan starts on 19 Apr/)).toBeInTheDocument();
  });

  it("tells the athlete to delete stale standalone workouts in the COROS app", async () => {
    fetchPushStatus.mockResolvedValue({ connected: true });
    pushToCoros.mockResolvedValue({
      kind: "ok", status: "sent", last_pushed_at: null,
      summary: { ...summary, mode: "standalone", plan_start: null, stale: 2 },
    });
    render(<CorosPushButton lang="en" refreshKey={1} />);
    await userEvent.click(await screen.findByRole("button", { name: /send to coros/i }));
    expect(await screen.findByText(/2 workouts that changed in Uphill are still on COROS/)).toBeInTheDocument();
    expect(screen.queryByText(/Your COROS plan starts/)).not.toBeInTheDocument();
  });
});
