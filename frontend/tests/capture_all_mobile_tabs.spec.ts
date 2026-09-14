import { test } from '@playwright/test';

test('capture all mobile tabs', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/app');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);

  // Tools tab (current default)
  await page.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/tab-tools-mobile.png' });

  // Chat tab
  const chatTab = page.locator('.mobile-bottom-nav-tab').filter({ hasText: /Coach/i }).first();
  if (await chatTab.isVisible()) {
    await chatTab.click();
    await page.waitForTimeout(600);
    await page.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/tab-chat-mobile.png' });
  }

  // Planner tab
  const plannerTab = page.locator('.mobile-bottom-nav-tab').filter({ hasText: /Planner|Lịch/i }).first();
  if (await plannerTab.isVisible()) {
    await plannerTab.click();
    await page.waitForTimeout(600);
    await page.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/tab-planner-mobile.png' });
  }

  // Knowledge tab
  const knowledgeTab = page.locator('.mobile-bottom-nav-tab').filter({ hasText: /Knowledge|Hub|Tri thức/i }).first();
  if (await knowledgeTab.isVisible()) {
    await knowledgeTab.click();
    await page.waitForTimeout(600);
    await page.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/tab-knowledge-mobile.png' });
  }

  // About tab
  const aboutTab = page.locator('.mobile-bottom-nav-tab').filter({ hasText: /About|Philosophy|Giới thiệu/i }).first();
  if (await aboutTab.isVisible()) {
    await aboutTab.click();
    await page.waitForTimeout(600);
    await page.screenshot({ path: '/Users/vietvo/.gemini/antigravity-ide/brain/fa573ad3-7356-4d49-b631-37a5bccd92a5/tab-about-mobile.png' });
  }
});
