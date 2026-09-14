import { test, expect } from "@playwright/test";
import path from "path";

test.use({
  deviceScaleFactor: 2,
  viewport: { width: 1200, height: 1600 },
});

test("capture tight high-dpi screenshots for homepage marketing", async ({ page }) => {
  await page.goto("/marketing-preview");
  await page.waitForLoadState("networkidle");

  // Wait for all cards to render
  await expect(page.locator("#step1-planner-card")).toBeVisible({ timeout: 10000 });
  await page.waitForTimeout(500);

  const publicScreenshotsDir = path.resolve(__dirname, "../public/screenshots");

  // 1. Hero Preview: Current Planner View (tight crop)
  await page.locator("#step1-planner-card").screenshot({
    path: path.join(publicScreenshotsDir, "current-planner-view.png"),
  });
  console.log("Captured current-planner-view.png");

  // 1B. Step 1: Tell Us Where You Are (Onboarding & Goal Calibration)
  await page.locator("#step1-onboarding-card").screenshot({
    path: path.join(publicScreenshotsDir, "tell-us-where-you-are.png"),
  });
  console.log("Captured tell-us-where-you-are.png");

  // 2. Step 2: Next Block Constraints Modal (tight crop)
  await page.locator("#step2-constraints-card").screenshot({
    path: path.join(publicScreenshotsDir, "next-block-modal-constraints.png"),
  });
  console.log("Captured next-block-modal-constraints.png");

  // 3. Step 3: Adapt Week Feeling Selector (tight crop)
  await page.locator("#step3-feeling-card").screenshot({
    path: path.join(publicScreenshotsDir, "adapt-week-feeling-selector.png"),
  });
  console.log("Captured adapt-week-feeling-selector.png");

  // 4. Step 4: Block Review Coach Feedback (tight crop)
  await page.locator("#step4-review-card").screenshot({
    path: path.join(publicScreenshotsDir, "block-review-coach-feedback.png"),
  });
  console.log("Captured block-review-coach-feedback.png");

  // 5. Coach Uphill Chat Exchange (dedicated moment)
  await page.locator("#coach-chat-exchange-card").screenshot({
    path: path.join(publicScreenshotsDir, "coach-uphill-chat-exchange.png"),
  });
  console.log("Captured coach-uphill-chat-exchange.png");

  // 6. Tool 1: Pace Strategy (tight crop)
  await page.locator("#tool-pace-card").screenshot({
    path: path.join(publicScreenshotsDir, "tool-pace-strategy.png"),
  });
  console.log("Captured tool-pace-strategy.png");

  // 7. Tool 2: Goal Determiner (tight crop)
  await page.locator("#tool-goal-card").screenshot({
    path: path.join(publicScreenshotsDir, "tool-goal-determiner.png"),
  });
  console.log("Captured tool-goal-determiner.png");

  // 8. Tool 3: Gear Finder (tight crop)
  await page.locator("#tool-gear-card").screenshot({
    path: path.join(publicScreenshotsDir, "tool-gear-finder.png"),
  });
  console.log("Captured tool-gear-finder.png");

  // 9. Tool 4: Nutrition Lab (tight crop)
  await page.locator("#tool-nutrition-card").screenshot({
    path: path.join(publicScreenshotsDir, "tool-nutrition-lab.png"),
  });
  console.log("Captured tool-nutrition-lab.png");
});
