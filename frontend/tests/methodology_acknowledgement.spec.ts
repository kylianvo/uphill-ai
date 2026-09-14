import { test, expect } from "@playwright/test";

test.describe("Methodology & Acknowledgement Section Verification", () => {
  test("Methodology section, 3D floating book image, Amazon link, and author tributes render correctly", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // 1. Methodology section is present
    const methodologySec = page.locator("#methodology");
    await expect(methodologySec).toBeVisible();

    // 2. Book mockup image is loaded
    const bookImg = methodologySec.locator('img[src="/training-for-the-uphill-athlete.png"]');
    await expect(bookImg).toBeVisible();
    await expect(bookImg).toHaveClass(/book-mockup-floating/);

    const isLoaded = await bookImg.evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth > 0);
    expect(isLoaded).toBe(true);

    // 3. Amazon link is present, pointing to the exact URL
    const amazonLink = methodologySec.locator('a[href="https://www.amazon.com.au/Training-Uphill-Athlete-Mountain-Mountaineers/dp/1938340841"]');
    await expect(amazonLink.first()).toBeVisible();
    await expect(amazonLink.first()).toHaveAttribute("target", "_blank");

    // 4. Scott Johnston tribute card (mentions Tom Evans & Ruth Croft)
    await expect(methodologySec.getByRole("heading", { name: "Scott Johnston" })).toBeVisible();
    await expect(methodologySec.getByText(/COACH OF UTMB 2025 CHAMPIONS/i).first()).toBeVisible();
    await expect(methodologySec.getByText(/Tom Evans/i).first()).toBeVisible();
    await expect(methodologySec.getByText(/Ruth Croft/i).first()).toBeVisible();

    // 5. Kilian Jornet tribute card
    await expect(methodologySec.getByRole("heading", { name: "Kilian Jornet" })).toBeVisible();
    await expect(methodologySec.getByText(/GOAT OF TRAIL RUNNING/i)).toBeVisible();
    await expect(methodologySec.getByText(/4x UTMB Champion/i)).toBeVisible();

    // 6. Steve House tribute card
    await expect(methodologySec.getByRole("heading", { name: "Steve House" })).toBeVisible();
    await expect(methodologySec.getByText(/WORLD-CLASS ALPINIST/i)).toBeVisible();
    await expect(methodologySec.getByText(/Piolet d'Or Recipient/i)).toBeVisible();

    // 7. Verified book quote is present
    await expect(methodologySec.getByText(/You will never maximize your endurance without first maximizing your basic aerobic capacity/i)).toBeVisible();
    await expect(methodologySec.getByText(/mere window dressing/i)).toBeVisible();

    // 8. No emojis in the section text
    const textContent = await methodologySec.innerText();
    expect(textContent).not.toContain("⏱️");
    expect(textContent).not.toContain("👑");
    expect(textContent).not.toContain("🧗");
    expect(textContent).not.toContain("🏔️");

    // 9. Merged unified master card and 3 interactive author cards
    const masterCard = methodologySec.locator(".methodology-unified-card");
    await expect(masterCard).toBeVisible();
    const authorCards = methodologySec.locator(".card-interactive-lift");
    await expect(authorCards).toHaveCount(3);

    // 10. Dalat Ultra Trail block is placed in 'How it works' (Step 2), NOT in Hero
    const heroSection = page.locator("section").first();
    await expect(heroSection.locator('img[src="/screenshots/current-planner-view.png"]')).toHaveCount(0);

    const howItWorksSection = page.locator("#how-it-works");
    const dutImageInHowItWorks = howItWorksSection.locator('img[src="/screenshots/current-planner-view.png"]');
    await expect(dutImageInHowItWorks).toBeVisible();

    // 11. Bilingual toggle: Switch to Vietnamese and check acknowledgement translations
    const viBtn = page.getByRole("button", { name: /Switch to Vietnamese/i });
    await expect(viBtn).toBeVisible();
    await viBtn.click();

    await expect(methodologySec.getByText(/Xây Dựng Từ Khoa Học Của Những Huyền Thoại Chạy Núi/i)).toBeVisible();
    await expect(methodologySec.getByText(/HLV CÁC NHÀ VÔ ĐỊCH UTMB 2025/i).first()).toBeVisible();
    await expect(methodologySec.getByText(/Tom Evans/i).first()).toBeVisible();
    await expect(methodologySec.getByText(/Ruth Croft/i).first()).toBeVisible();
    await expect(methodologySec.getByText(/TƯỢNG ĐÀI CHẠY TRAIL/i)).toBeVisible();
    await expect(methodologySec.getByText(/NHÀ LEO NÚI ĐỈNH CAO/i)).toBeVisible();
    await expect(methodologySec.getByText(/dung tích hiếu khí cơ bản/i)).toBeVisible();
    await expect(methodologySec.getByText(/Xem trên Amazon/i)).toBeVisible();

    // Switch back to English
    const enBtn = page.getByRole("button", { name: /Switch to English/i });
    await expect(enBtn).toBeVisible();
    await enBtn.click();

    await expect(methodologySec.getByText(/Built on the Science of Mountain Endurance Legends/i)).toBeVisible();
  });
});
