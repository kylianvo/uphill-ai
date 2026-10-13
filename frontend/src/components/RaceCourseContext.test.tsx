import { render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import RaceCourseContext from "./RaceCourseContext";
it("labels another edition and rejects unsafe source links", () => {
  render(
    <RaceCourseContext
      lang="en"
      resultYear={2024}
      onChooseCourse={vi.fn()}
      onRetry={vi.fn()}
      context={{
        status: "matched",
        candidates: [],
        message: null,
        course: {
          id: 10,
          race_name: "Mountain Trail",
          distance_label: "50 km",
          distance_km: 50,
          elevation_gain_m: 2200,
          location: null,
          terrain: [],
          key_climbs: [],
          climate: { notes: "Cool mornings" },
          runner_reviews: [],
          source_label: "Organizer",
          source_urls: ["javascript:alert(1)"],
          verified_at: null,
          edition_year: 2026,
          edition_status: "different",
        },
      }}
    />
  );
  expect(screen.getByText(/Course profile: 2026/)).toBeInTheDocument();
  expect(screen.getByText("Typical conditions")).toBeInTheDocument();
  expect(screen.queryByRole("link")).not.toBeInTheDocument();
});
