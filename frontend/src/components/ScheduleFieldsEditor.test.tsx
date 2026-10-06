import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import { ScheduleFieldsEditor, ScheduleFieldsValue } from "./ScheduleFieldsEditor";
import { translations } from "../app/translations";

const t = (key: keyof typeof translations.en) => translations.en[key] || key;

const baseValue: ScheduleFieldsValue = {
  days_per_week: 4,
  long_run_day: "Saturday",
  preferred_days: ["Monday", "Wednesday", "Saturday"],
  has_gym_access: false,
  use_treadmill: false,
  training_environment: "flat",
  mountain_days: [],
  stair_access: false,
  treadmill_max_incline: 15,
  double_session_days: [],
};

describe("ScheduleFieldsEditor", () => {
  it("reports the new days-per-week value when a button is clicked", () => {
    const onChange = vi.fn();
    render(<ScheduleFieldsEditor lang="en" t={t} isMobile={false} value={baseValue} onChange={onChange} />);

    fireEvent.click(screen.getByText("6"));

    expect(onChange).toHaveBeenCalledWith({ days_per_week: 6 });
  });

  it("toggles a preferred day on and off", () => {
    const onChange = vi.fn();
    render(<ScheduleFieldsEditor lang="en" t={t} isMobile={false} value={baseValue} onChange={onChange} />);

    const preferredSection = screen.getByText(t("plan_preferred_days")).closest("div")!;
    fireEvent.click(within(preferredSection).getByText("Tue"));

    expect(onChange).toHaveBeenCalledWith({ preferred_days: ["Monday", "Wednesday", "Saturday", "Tuesday"] });
  });

  it("only renders double-session-day buttons for days already in preferred_days", () => {
    render(<ScheduleFieldsEditor lang="en" t={t} isMobile={false} value={baseValue} onChange={vi.fn()} />);

    // preferred_days is Mon/Wed/Sat -- Tuesday's double-session button must not render
    const doubleSessionSection = screen.getByText(t("plan_double_session_days")).closest("div")!;
    expect(within(doubleSessionSection).queryAllByText("Tue")).toHaveLength(0);
  });

  it("updates athlete_notes when typing into the notes textarea", () => {
    const onChange = vi.fn();
    render(<ScheduleFieldsEditor lang="en" t={t} isMobile={false} value={{ ...baseValue, athlete_notes: "" }} onChange={onChange} />);

    const textarea = screen.getByPlaceholderText(t("plan_athlete_notes_placeholder"));
    fireEvent.change(textarea, { target: { value: "Living in city on weekdays, mountain running on weekends." } });

    expect(onChange).toHaveBeenCalledWith({ athlete_notes: "Living in city on weekdays, mountain running on weekends." });
  });

  it("records hill/trail days in weekday order", () => {
    const onChange = vi.fn();
    render(<ScheduleFieldsEditor lang="en" t={t} isMobile={false} value={{ ...baseValue, mountain_days: ["Sunday"] }} onChange={onChange} />);

    const hillSection = screen.getByText(t("plan_mountain_days")).closest("div")!;
    fireEvent.click(within(hillSection).getByText("Sat"));

    expect(onChange).toHaveBeenCalledWith({ mountain_days: ["Saturday", "Sunday"] });
  });

  it("toggles stair access", () => {
    const onChange = vi.fn();
    render(<ScheduleFieldsEditor lang="en" t={t} isMobile={false} value={baseValue} onChange={onChange} />);

    fireEvent.click(screen.getByLabelText(t("plan_stair_access")));

    expect(onChange).toHaveBeenCalledWith({ stair_access: true });
  });

  it("shows the treadmill incline picker only with a treadmill", () => {
    const onChange = vi.fn();
    const { rerender } = render(<ScheduleFieldsEditor lang="en" t={t} isMobile={false} value={baseValue} onChange={onChange} />);
    expect(screen.queryByText(t("plan_treadmill_max_incline"))).toBeNull();

    rerender(<ScheduleFieldsEditor lang="en" t={t} isMobile={false} value={{ ...baseValue, use_treadmill: true }} onChange={onChange} />);
    fireEvent.click(screen.getByText("25%+"));

    expect(onChange).toHaveBeenCalledWith({ treadmill_max_incline: 25 });
  });
});
