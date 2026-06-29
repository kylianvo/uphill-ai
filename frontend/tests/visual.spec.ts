import { test, expect } from '@playwright/test';

test('landing page visual regression', async ({ page }) => {
  // Navigate to the frontend
  await page.goto('/');

  // Wait for the page to load completely and animations to settle
  await page.waitForLoadState('networkidle');

  // Take a baseline screenshot of the full page
  await expect(page).toHaveScreenshot('landing-page.png', {
    fullPage: true,
    maxDiffPixels: 100, // Allow small anti-aliasing differences
  });
});
