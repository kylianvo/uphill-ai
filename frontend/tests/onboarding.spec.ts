import { test, expect } from "./fixtures/auth";

/**
 * Regression test for the plan_start_date onboarding bug: POST
 * /api/auth/onboarding used to silently ignore a user-submitted
 * plan_start_date and always hardcode start_date = date.today() (see
 * backend/main.py's OnboardingRequest + complete_onboarding, fixed
 * alongside backend/tests/integration/test_onboarding_endpoint.py's
 * equivalent backend-only regression test).
 *
 * This drives the actual OnboardingWizard UI end to end -- the original bug
 * lived entirely in backend logic, so this proves the whole pipeline (UI ->
 * API -> DB) still round-trips the user's chosen date correctly, not just
 * the backend in isolation.
 *
 * We do NOT wait for the background Gemini workout generation to finish
 * (30-60s, and CI runs with a fake GEMINI_API_KEY so it would fail) -- the
 * plans row is committed synchronously before that async job starts, so we
 * verify start_date via a direct API call right after submitting.
 */

const CHOSEN_START_DATE = "2026-08-23"; // deliberately far from "today" so a regression is unmistakable

test("onboarding wizard sends the chosen Plan Start Date, not today", async ({ page, freshUserEmail }) => {
  void freshUserEmail; // fixture already logged in and waited for the wizard to open

  // Step 1: Date of Birth
  await page.getByRole("textbox").fill("1995-06-15");
  await page.getByRole("button", { name: "Next →" }).click();

  // Step 2: Goal -- "Start Running" takes the shortest path to the Schedule
  // step, which is where Plan Start Date lives (rendered for every goal type).
  await page.getByRole("button", { name: "Start Running" }).click();
  await page.getByRole("button", { name: "Next →" }).click();

  // Step 3: Fitness (all fields optional) -- clicking Next with nothing
  // filled shows a "fitness data incomplete" confirmation popup.
  await page.getByRole("button", { name: "Next →" }).click();
  await page.getByRole("button", { name: "Got it, continue →" }).click();

  // Step 4: Schedule -- set Plan Start Date. Native date inputs need an
  // ISO (YYYY-MM-DD) value regardless of display locale.
  const startDateInput = page.locator('input[type="date"]');
  await startDateInput.fill(CHOSEN_START_DATE);
  await expect(startDateInput).toHaveValue(CHOSEN_START_DATE);
  await page.getByRole("button", { name: "Next →" }).click();

  // Step 5: Double Session Days (optional) -- skip straight to review.
  await page.getByRole("button", { name: "Review →" }).click();

  // Step 6: Review -- the summary should already display the chosen date.
  await expect(page.getByText(CHOSEN_START_DATE)).toBeVisible();

  const [onboardingResponse] = await Promise.all([
    page.waitForResponse((resp) => resp.url().includes("/api/auth/onboarding") && resp.request().method() === "POST"),
    page.getByRole("button", { name: "🚀 Generate My Training Plan" }).click(),
  ]);
  expect(onboardingResponse.ok()).toBeTruthy();

  // Verify the persisted plan directly via the API -- fast and deterministic,
  // unlike waiting for the (possibly Gemini-key-less, in CI) background job.
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const activePlanResponse = await page.evaluate(async (baseUrl) => {
    const token = localStorage.getItem("uphill_session_token");
    const resp = await fetch(`${baseUrl}/api/coach/active-plan`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return resp.json();
  }, apiBaseUrl);

  expect(activePlanResponse.active).toBe(true);
  expect(activePlanResponse.plan.start_date).toBe(CHOSEN_START_DATE);

  const today = new Date().toISOString().split("T")[0];
  expect(activePlanResponse.plan.start_date).not.toBe(today);
});
