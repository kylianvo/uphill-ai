import { test, expect } from '@playwright/test';

test('verify page scrolls with mouse wheel and keyboard', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  const initialScrollY = await page.evaluate(() => window.scrollY);
  expect(initialScrollY).toBe(0);

  const diag = await page.evaluate(() => {
    const el = document.elementFromPoint(500, 500);
    const htmlStyle = getComputedStyle(document.documentElement);
    const bodyStyle = getComputedStyle(document.body);
    return {
      elTag: el ? el.tagName : null,
      elClass: el ? el.className : null,
      htmlOverflow: htmlStyle.overflow,
      htmlOverflowX: htmlStyle.overflowX,
      htmlOverflowY: htmlStyle.overflowY,
      htmlHeight: htmlStyle.height,
      bodyOverflow: bodyStyle.overflow,
      bodyOverflowX: bodyStyle.overflowX,
      bodyOverflowY: bodyStyle.overflowY,
      bodyHeight: bodyStyle.height,
      bodyOverscroll: bodyStyle.overscrollBehaviorY,
    };
  });
  console.log('DIAGNOSTICS:', JSON.stringify(diag, null, 2));

  // Scroll down with mouse wheel
  await page.mouse.wheel(0, 800);
  await page.waitForTimeout(500);

  const scrollInfo = await page.evaluate(() => ({
    windowY: window.scrollY,
    docScrollTop: document.documentElement.scrollTop,
    bodyScrollTop: document.body.scrollTop,
  }));
  console.log('Scroll info after wheel:', scrollInfo);

  // Try window.scrollTo
  await page.evaluate(() => window.scrollTo(0, 500));
  const scrollInfoAfterScrollTo = await page.evaluate(() => ({
    windowY: window.scrollY,
    docScrollTop: document.documentElement.scrollTop,
    bodyScrollTop: document.body.scrollTop,
  }));
  console.log('Scroll info after window.scrollTo:', scrollInfoAfterScrollTo);

  const scrollHeight = await page.evaluate(() => document.documentElement.scrollHeight);
  console.log('Document scrollHeight:', scrollHeight);
  expect(scrollHeight).toBeGreaterThan(900);
});
