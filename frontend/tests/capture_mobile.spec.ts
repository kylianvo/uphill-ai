import { test } from '@playwright/test';

test('capture mobile viewports', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });

  // 1. Landing page on mobile
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/mobile-landing-top.png', fullPage: false });
  await page.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/mobile-landing-full.png', fullPage: true });

  const methodology = page.locator('#methodology');
  if (await methodology.isVisible()) {
    await methodology.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    await methodology.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/mobile-landing-methodology.png' });
  }

  // 2. Web App (/app) on mobile - Tools Tab
  await page.goto('/app');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);

  // Close auth modal if open
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);

  // Click on Tools tab if visible in bottom nav
  const toolsTab = page.locator('.mobile-bottom-nav-tab:has-text("Tools"), .mobile-bottom-nav-tab:has-text("Công cụ")').first();
  if (await toolsTab.isVisible()) {
    await toolsTab.click();
    await page.waitForTimeout(400);
  }

  await page.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/mobile-app-tools.png', fullPage: false });

  // Check About tab
  const aboutTab = page.locator('.mobile-bottom-nav-tab:has-text("About"), .mobile-bottom-nav-tab:has-text("Giới thiệu")').first();
  if (await aboutTab.isVisible()) {
    await aboutTab.click();
    await page.waitForTimeout(400);
    await page.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/mobile-app-about.png', fullPage: false });
  }

  // Check Knowledge tab
  const knowledgeTab = page.locator('.mobile-bottom-nav-tab:has-text("Knowledge"), .mobile-bottom-nav-tab:has-text("Kiến thức")').first();
  if (await knowledgeTab.isVisible()) {
    await knowledgeTab.click();
    await page.waitForTimeout(400);
    await page.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/mobile-app-knowledge.png', fullPage: false });
  }
});
