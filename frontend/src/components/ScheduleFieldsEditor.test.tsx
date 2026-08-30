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

    fireEvent.click(screen.getByText("Tue"));

    expect(onChange).toHaveBeenCalledWith({ preferred_days: ["Monday", "Wednesday", "Saturday", "Tuesday"] });
  });

  it("only renders double-session-day buttons for days already in preferred_days", () => {
    render(<ScheduleFieldsEditor lang="en" t={t} isMobile={false} value={baseValue} onChange={vi.fn()} />);

    // preferred_days is Mon/Wed/Sat -- Tuesday's double-session button must not render
    const doubleSessionSection = screen.getByText(t("plan_double_session_days")).closest("div")!;
    expect(within(doubleSessionSection).queryAllByText("Tue")).toHaveLength(0);
  });
});
