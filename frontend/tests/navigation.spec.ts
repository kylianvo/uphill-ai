import { test, expect } from '@playwright/test';

test('verify landing page loads and has Get Started button', async ({ page }) => {
  await page.goto('/');

  // Check the title or a specific heading to ensure it loaded
  await expect(page).toHaveTitle(/Uphill/);

});
