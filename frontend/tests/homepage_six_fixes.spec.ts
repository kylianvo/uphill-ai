import { test, expect } from "@playwright/test";

test.describe("Homepage 6 Fixes Verification", () => {
  test("1. Watch-sync row truthfully shows only COROS as live and others as coming soon", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Check COROS has live indicator
    const syncSection = page.locator("#sync");
    const corosBadge = syncSection.getByRole("img", { name: "COROS", exact: true });
    await expect(corosBadge).toBeVisible();
    await expect(syncSection.getByText(/^Live$|^Đang hoạt động$/i)).toBeVisible();

    // Check others are labeled Coming Soon
    const comingSoonLabels = syncSection.getByText(/Coming soon|Sắp ra mắt/i);
    await expect(comingSoonLabels.first()).toBeVisible();
    const count = await comingSoonLabels.count();
    expect(count).toBeGreaterThanOrEqual(3); // Garmin, Strava, Apple Watch

    // Check the integration labels, scoped away from the comparison table
    for (const name of ["Garmin Connect", "Strava", "Apple Watch"]) {
      const el = syncSection.getByText(name, { exact: true });
      await expect(el).toBeVisible();
    }
  });

  test("2. Proof section is null when SHOW_PROOF_CONTENT is false", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // The text 'Real numbers are coming here' or 'Proof' heading must NOT exist
    await expect(page.getByText("Real numbers are coming here once we have them to show.")).not.toBeVisible();
    await expect(page.getByText("Dữ liệu race finisher và kết quả thực tế sẽ được cập nhật tại đây.")).not.toBeVisible();
    await expect(page.getByRole("heading", { name: /^Proof$|^Thành tích Vận Động Viên$/ })).not.toBeVisible();
  });

  test("3. Science links have dedicated anchors and match destinations on /science", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Redundant 3-card credibility block under hero must be removed
    await expect(page.getByText("Steve House & Scott Johnston Methodology")).not.toBeVisible();
    await expect(page.getByText("Phương pháp Steve House & Scott Johnston")).not.toBeVisible();
    await expect(page.getByText("100% Threshold Precision")).not.toBeVisible();
    await expect(page.getByText("Course-Specific Vert & Pacing")).not.toBeVisible();

    // Check that step links have anchors
    const stepLinks = page.locator("#how-it-works a[href^='/science#']");
    const stepLinkCount = await stepLinks.count();
    expect(stepLinkCount).toBe(4);

    const step1Href = await stepLinks.nth(0).getAttribute("href");
    expect(step1Href).toBe("/science#thresholds");

    const step2Href = await stepLinks.nth(1).getAttribute("href");
    expect(step2Href).toBe("/science#thresholds");

    const step3Href = await stepLinks.nth(2).getAttribute("href");
    expect(step3Href).toBe("/science#adaptation");

    const step4Href = await stepLinks.nth(3).getAttribute("href");
    expect(step4Href).toBe("/science#block-evaluation");

    // Check Coach Uphill link has anchor
    const coachLink = page.locator("#coach a[href='/science#coach-grounding']");
    await expect(coachLink).toBeVisible();

    // Check tool cards have anchors
    const toolAnchors = [
      "/science#pace-physics",
      "/science#goal-prediction",
      "/science#gear-grounding",
      "/science#nutrition-grounding",
    ];
    for (const anchor of toolAnchors) {
      const toolLink = page.locator(`#tools a[href='${anchor}']`);
      await expect(toolLink).toBeVisible();
    }

    // Navigate to /science and verify all target IDs exist
    await page.goto("/science");
    await page.waitForLoadState("networkidle");

    const targetIds = [
      "thresholds",
      "adaptation",
      "block-evaluation",
      "coach-grounding",
      "pace-physics",
      "goal-prediction",
      "gear-grounding",
      "nutrition-grounding",
    ];
    for (const id of targetIds) {
      const section = page.locator(`#${id}`);
      await expect(section).toBeVisible();
    }
  });

  test("4 & 5. Coach Uphill spotlight and 4 tool cards have valid images (no 404s)", async ({ page }) => {
    // Listen for image requests
    const imageResponses: { url: string; status: number }[] = [];
    page.on("response", (res) => {
      if (res.request().resourceType() === "image") {
        imageResponses.push({ url: res.url(), status: res.status() });
      }
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Coach Uphill section is visible with image
    const coachImg = page.locator("#coach img");
    await coachImg.scrollIntoViewIfNeeded();
    await expect(coachImg).toBeVisible();
    const coachSrc = await coachImg.getAttribute("src");
    expect(coachSrc).toContain("ios-coach-saturday.png");

    // 4 tool images are visible
    const toolImages = page.locator("#tools img");
    expect(await toolImages.count()).toBe(4);

    const expectedToolImgs = [
      "ios-pace-strategy.png",
      "ios-goal-determiner.png",
      "ios-gear-vault.png",
      "ios-nutrition-lab.png",
    ];
    for (let i = 0; i < 4; i++) {
      const src = await toolImages.nth(i).getAttribute("src");
      expect(src).toContain(expectedToolImgs[i]);
    }

    // Step 1 shows the native plan builder, distinct from the adapt-week screen
    const stepImgs = page.locator("#how-it-works img");
    const step1Src = await stepImgs.nth(0).getAttribute("src");
    const step3Src = await stepImgs.nth(2).getAttribute("src");
    expect(step1Src).toContain("ios-plan-builder.png");
    expect(step1Src).not.toBe(step3Src);

    // Scroll lazy screenshots into view and verify the selected WebP/PNG loads.
    const screenshots = page.locator("#coach img, #tools img, #how-it-works img");
    for (const screenshot of await screenshots.all()) {
      await screenshot.scrollIntoViewIfNeeded();
      await expect(screenshot).toBeVisible();
      await expect.poll(() => screenshot.evaluate((img: HTMLImageElement) =>
        img.complete && img.naturalWidth > 0 && img.currentSrc.includes("/landing/")
      )).toBe(true);
    }

    // Assert all loaded screenshot images returned 200
    for (const res of imageResponses) {
      if (res.url.includes("/landing/")) {
        expect(res.status).toBe(200);
      }
    }
  });

  test("6. Video background and smooth scroll behavior", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Video element exists
    const video = page.locator("video").first();
    await expect(video).toBeAttached();

    // Scrolling down functions properly
    const scrollYBefore = await page.evaluate(() => window.scrollY);
    await page.evaluate(() => window.scrollTo({ top: 1200, behavior: "instant" }));
    await page.waitForTimeout(300);
    const scrollYAfter = await page.evaluate(() => window.scrollY);
    expect(scrollYAfter).toBeGreaterThan(scrollYBefore);
  });
});
