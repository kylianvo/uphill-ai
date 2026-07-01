import { test, expect } from "@playwright/test";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function uniqueEmail(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@uphill.ai`;
}

test.describe("Auth forms", () => {
  test("registering through the UI creates a session and opens onboarding", async ({ page }) => {
    const email = uniqueEmail("e2e-register");

    await page.goto("/");
    await page.getByRole("button", { name: "Sign In" }).click();
    await page.getByRole("button", { name: "Create Account" }).click();

    await page.getByPlaceholder("Alex Runner").fill("Ada Athlete");
    await page.getByPlaceholder("you@example.com").fill(email);
    await page.getByPlaceholder("Min 8 characters").fill("correcthorse");
    await page.getByPlaceholder("Repeat password").fill("correcthorse");

    await page.getByRole("button", { name: "Create Account" }).last().click();

    // Registration should close the auth modal and open onboarding for a fresh user.
    // (waitForResponse only guarantees the HTTP response arrived, not that the app's
    // async response.json() -> localStorage.setItem -> setOnboardingOpen chain has run
    // yet, so assert on the resulting UI state rather than racing the response event.)
    await expect(page.getByText(/Step 1 of/)).toBeVisible();

    const token = await page.evaluate(() => localStorage.getItem("uphill_session_token"));
    expect(token).toBeTruthy();
  });

  test("logging in with the wrong password shows an error and does not store a session", async ({ page }) => {
    const email = uniqueEmail("e2e-login-fail");
    // Create the account directly via the API so this test is only exercising the login form.
    await page.request.post(`${API_BASE_URL}/api/auth/register`, {
      data: { name: "Login Tester", email, password: "correcthorse" },
    });

    await page.goto("/");
    await page.getByRole("button", { name: "Sign In" }).click();
    await page.getByPlaceholder("you@example.com").fill(email);
    await page.getByPlaceholder("Your password").fill("wrong-password");
    await page.getByRole("button", { name: "Sign In" }).last().click();

    await expect(page.getByText(/invalid email or password/i)).toBeVisible();
    const token = await page.evaluate(() => localStorage.getItem("uphill_session_token"));
    expect(token).toBeNull();
  });

  test("logging in with correct credentials stores a session", async ({ page }) => {
    const email = uniqueEmail("e2e-login-ok");
    await page.request.post(`${API_BASE_URL}/api/auth/register`, {
      data: { name: "Login Tester", email, password: "correcthorse" },
    });

    await page.goto("/");
    await page.getByRole("button", { name: "Sign In" }).click();
    await page.getByPlaceholder("you@example.com").fill(email);
    await page.getByPlaceholder("Your password").fill("correcthorse");
    await page.getByRole("button", { name: "Sign In" }).last().click();

    // Same reasoning as the register test: wait for the resulting UI state (modal
    // closes on success) rather than racing the raw HTTP response event.
    await expect(page.getByPlaceholder("you@example.com")).toBeHidden();

    const token = await page.evaluate(() => localStorage.getItem("uphill_session_token"));
    expect(token).toBeTruthy();
  });
});
