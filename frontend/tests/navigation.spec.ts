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

  test('navigating to /app on web does NOT show Home tab', async ({ page }) => {
    await page.goto('/app');
    await page.waitForLoadState('networkidle');

    // On web, no "Home" or "Trang chủ" tab should exist in any navigation
    await expect(page.locator('.top-nav-tab', { hasText: /^(Home|Trang chủ)$/ })).toHaveCount(0);
    await expect(page.locator('.mobile-bottom-nav-tab', { hasText: /^(Home|Trang chủ)$/ })).toHaveCount(0);
    await expect(page.locator('.sidebar-nav-item', { hasText: /^(Home|Trang chủ)$/ })).toHaveCount(0);
  });

  test('on native platform: / redirects to /app, shows Home tab and Glassmorphism hero', async ({ page }) => {
    // Mock native Capacitor platform before loading
    await page.addInitScript(() => {
      try {
        window.localStorage.setItem('CAPACITOR_NATIVE_OVERRIDE', 'true');
      } catch (e) {}
    });

    await page.goto('/');
    await expect(page).toHaveURL(/\/app/);

    // App shell loads on native with Home tab
    const homeTab = page.locator('.mobile-bottom-nav-tab, .top-nav-tab').filter({ hasText: /^(Home|Trang chủ)$/ });
    await expect(homeTab.first()).toBeVisible();

    // HomeTab with Glassmorphism is active
    const heroHeader = page.locator('.hero-header-group');
    await expect(heroHeader).toBeVisible();

    // Verify glassmorphism style (backdrop-filter)
    const backdropFilter = await heroHeader.evaluate((el) => window.getComputedStyle(el).backdropFilter);
    expect(backdropFilter).toContain('blur');

    // Feature cards with glassmorphism are visible
    const cards = page.locator('.card');
    await expect(cards.first()).toBeVisible();
  });

  test('on native mobile device: displays Home tab on bottom nav with glassmorphism', async ({ page }) => {
    await page.setViewportSize({ width: 393, height: 852 });
    await page.addInitScript(() => {
      try {
        window.localStorage.setItem('CAPACITOR_NATIVE_OVERRIDE', 'true');
      } catch (e) {}
    });

    await page.goto('/');
    await expect(page).toHaveURL(/\/app/);

    const bottomHomeTab = page.locator('.mobile-bottom-nav-tab').filter({ hasText: /^(Home|Trang chủ)$/ });
    await expect(bottomHomeTab).toBeVisible();

    const heroHeader = page.locator('.hero-header-group');
    await expect(heroHeader).toBeVisible();
  });
});

test.describe('Shell v2 tab model (?ui=v2)', () => {
  const signIn = async (page: import('@playwright/test').Page, isCoach: boolean) => {
    const user = { id: 902, name: 'E2E Runner', email: 'e2e@example.test', onboarding_complete: true, is_coach: isCoach };
    await page.route('**/api/**', async route => {
      const path = new URL(route.request().url()).pathname;
      let body: unknown;
      if (path === '/api/auth/me') body = user;
      else if (path === '/api/health') body = { status: 'healthy' };
      else if (path === '/api/coach/active-plan') body = { active: false };
      else if (path === '/api/coach/recent-plans') body = { plans: [] };
      await route.fulfill(body === undefined ? { status: 404, json: { detail: 'Not part of this fixture' } } : { json: body });
    });
    await page.addInitScript((u) => {
      localStorage.setItem('uphill_session_token', 'e2e-fixture');
      localStorage.setItem('uphill_user', JSON.stringify(u));
    }, user);
  };
  const navButton = (page: import('@playwright/test').Page, name: string) =>
    page.locator('.top-nav-tab').filter({ hasText: new RegExp(`^${name}$`) });

  test('signed-in user lands on Plan and sees Plan/Coach/Me only', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await signIn(page, false);
    await page.goto('/app?ui=v2');
    await expect(navButton(page, 'Plan')).toHaveAttribute('aria-current', 'page');
    await expect(navButton(page, 'Coach')).toBeVisible();
    await expect(navButton(page, 'Me')).toBeVisible();
    await expect(navButton(page, 'Athletes')).toHaveCount(0);
    await expect(page).toHaveURL(/tab=plan/);
    await expect(page).toHaveURL(/ui=v2/);
  });

  test('coaches see Athletes', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await signIn(page, true);
    await page.goto('/app?ui=v2');
    await expect(navButton(page, 'Athletes')).toBeVisible();
  });

  test('?tab=me deep-links and Back to Me returns from Gear Finder', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await signIn(page, false);
    await page.goto('/app?ui=v2&tab=me');
    await expect(navButton(page, 'Me')).toHaveAttribute('aria-current', 'page');
    await page.getByRole('button', { name: 'Gear Finder' }).click();
    await expect(navButton(page, 'Me')).toHaveAttribute('aria-current', 'page');
    await page.getByRole('button', { name: /Back to Me/ }).click();
    await expect(page.getByRole('heading', { name: 'Me', exact: true })).toBeVisible();
    await expect(page).toHaveURL(/tab=me/);
  });
});
