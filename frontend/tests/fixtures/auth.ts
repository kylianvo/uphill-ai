import { test as base, expect, Page } from "@playwright/test";

/**
 * Logs in via the same postMessage channel the real Google/Facebook OAuth
 * popups use (see frontend/src/app/page.tsx's `window.addEventListener('message', ...)`
 * handler, which calls handleMockLogin). This is deliberately NOT a raw
 * localStorage injection: handleMockLogin is what sets onboardingOpen=true
 * for a fresh (onboarding_complete=false) user -- localStorage injection
 * alone restores the session but never opens onboarding, since that only
 * happens as a side effect of the login handlers themselves.
 *
 * mock-login is only registered when ENVIRONMENT != production on the
 * backend (see backend/main.py's `if not _is_prod` guard), so this fixture
 * only works against non-production backends -- exactly the ones these
 * tests run against.
 */
export async function loginAsFreshUser(page: Page, emailPrefix = "e2e"): Promise<string> {
  const email = `${emailPrefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@uphill.ai`;
  await page.goto("/");
  await page.evaluate((userEmail) => {
    window.postMessage({ provider: "mock", email: userEmail }, "*");
  }, email);
  // Wait until the onboarding wizard has actually opened before returning,
  // so callers don't race the async mock-login fetch + state update.
  await page.getByText(/Step 1 of/).waitFor();
  return email;
}

export const test = base.extend<{ freshUserEmail: string }>({
  // Navigates to the app and logs in as a brand-new user via the mock-login
  // postMessage flow, which also auto-opens the onboarding wizard (since
  // onboarding_complete is false for a never-seen-before email).
  freshUserEmail: async ({ page }, use) => {
    const email = await loginAsFreshUser(page);
    await use(email);
  },
});

export { expect };
