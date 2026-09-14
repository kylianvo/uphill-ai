import { test, expect } from '@playwright/test';

test.describe('Navigation and landing page split', () => {
  test('verify landing page loads, has title and CTA linking to /app', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveTitle(/Uphill/);

    const ctaButton = page.getByRole('link', { name: /Start Training Plan|Bắt đầu giáo án|Bắt đầu plan|Get Started/i }).first();
    await expect(ctaButton).toBeVisible();
    await expect(ctaButton).toHaveAttribute('href', '/app');
  });

  test('landing page / renders with no .mobile-bottom-nav-tabs or app navigation present', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Neither the mobile bottom nav nor the app shell top nav tabs should exist on the marketing route
    await expect(page.locator('.mobile-bottom-nav-tabs')).toHaveCount(0);
    await expect(page.locator('.phone-bottom-tab-bar')).toHaveCount(0);
    await expect(page.locator('.top-nav-tabs')).toHaveCount(0);
    await expect(page.locator('.laptop-sidebar')).toHaveCount(0);
  });

  test('every <img> in the 4-step section returns 200 (no 404s)', async ({ page, request }) => {
    const failedImageUrls: string[] = [];
    page.on('response', (response) => {
      const url = response.url();
      if (
        (url.includes('/screenshots/') || response.request().resourceType() === 'image') &&
        response.status() >= 400
      ) {
        failedImageUrls.push(`${url} (status ${response.status()})`);
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Find the 4-step section by its unique h2 heading
    const stepsSection = page.locator('section').filter({
      has: page.locator('h2', { hasText: /How it works|Quy trình 4 bước/i }),
    });
    await expect(stepsSection).toBeVisible();

    // Verify all <img> elements rendered within the 4-step section return 200
    const images = stepsSection.locator('img');
    const imageCount = await images.count();
    expect(imageCount).toBeGreaterThan(0);

    for (let i = 0; i < imageCount; i++) {
      const img = images.nth(i);
      const src = await img.getAttribute('src');
      expect(src).toBeTruthy();
      if (src) {
        const res = await request.get(src);
        expect(res.status(), `Image ${src} must return 200 OK`).toBe(200);
      }
    }

    expect(failedImageUrls).toEqual([]);
  });

  test('navigating to /app loads the app shell', async ({ page }) => {
    await page.goto('/app');
    await page.waitForLoadState('networkidle');

    // On /app, the app header/navigation should be present
    await expect(page.locator('.top-nav-logo, .phone-header, .laptop-sidebar-logo').first()).toBeVisible();
  });
});
