import { test } from '@playwright/test';

test('capture homepage screenshots', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  // Scroll down to ensure all sections render cleanly
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 400) {
      window.scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 50));
    }
    window.scrollTo(0, 0);
  });
  await page.waitForTimeout(500);

  await page.screenshot({ path: 'test-results/homepage-desktop-top.png', fullPage: false });
  await page.screenshot({ path: 'test-results/homepage-desktop-full.png', fullPage: true });

  const methodology = page.locator('#methodology');
  await methodology.scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  await methodology.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/methodology-en.png' });

  // Switch to Vietnamese
  await page.getByRole('button', { name: /Switch to Vietnamese|VI/i }).first().click();
  await page.waitForTimeout(300);
  await page.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/homepage-vietnamese-top.png', fullPage: false });
  await page.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/homepage-vietnamese-full.png', fullPage: true });
  await methodology.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/methodology-vi.png' });

  // Mobile viewport test & screenshots
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(400);

  const mobileHowItWorks = page.locator('#how-it-works');
  await mobileHowItWorks.scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  await mobileHowItWorks.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/mobile-landing-howitworks.png' });

  const mobileCoach = page.locator('#coach');
  await mobileCoach.scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  await mobileCoach.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/mobile-landing-coach.png' });

  const mobileTools = page.locator('#tools');
  await mobileTools.scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  await mobileTools.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/mobile-landing-tools.png' });

  await page.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/mobile-landing-full.png', fullPage: true });
});
