import { test, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
const result = {
  id: 7,
  claim_id: null,
  source: "manual",
  race_name: "Mountain Trail — the long ridge route across the national park",
  race_date: "2024-06-01",
  discipline: "trail",
  distance_km: 50,
  elevation_gain_m: 2200,
  finish_time_sec: 22000,
  is_dnf: false,
  bib: "42",
  selected: true,
  hidden: false,
  user_note: "Steady climbs. Patient pacing.",
  verified: false,
  verification_methods: [],
  rank_overall: 30,
  total_overall: 100,
};
const course = {
  id: 10,
  race_name: "Mountain Trail",
  distance_label: "50 km",
  distance_km: 50,
  elevation_gain_m: 2400,
  location: "Mountain Town",
  terrain: ["Technical singletrack"],
  key_climbs: ["Summit climb"],
  climate: { notes: "Cool mornings; exposed ridges." },
  runner_reviews: ["Save energy for the final descent."],
  source_label: "Organizer",
  source_urls: ["https://example.org/course", "javascript:alert(1)"],
  verified_at: "2026-10-13",
  edition_year: 2026,
  edition_status: "different",
};
for (const width of [1440, 390])
  for (const lang of ["en", "vi"] as const) {
    test(`race detail states ${width} ${lang}`, async ({ page }) => {
      test.setTimeout(120000);
      await page.setViewportSize({ width, height: 900 });
      let state = "matched";
      const choices: string[] = [];
      const user = {
        id: 901,
        name: "Preview Runner",
        email: "preview@example.test",
        onboarding_complete: true,
      };
      await page.route("**/api/**", async (route) => {
        const url = new URL(route.request().url());
        let body: unknown = {};
        if (url.pathname.includes("invites")) body = [];
        if (url.pathname === "/api/auth/me") body = user;
        else if (url.pathname === "/api/coach/active-plan")
          body = { active: false };
        else if (url.pathname === "/api/race-history")
          body = {
            claims: [],
            results: [result],
            summary: {
              trail_finishes: 1,
              trail_dnfs: 0,
              ultras: 1,
              longest_finish: result,
              road_prs: {},
              road_hm_pr: null,
              road_fm_pr: null,
            },
          };
        else if (url.pathname.endsWith("/7/detail")) {
          if (state === "error") {
            await route.fulfill({
              status: 503,
              json: { detail: "Review unavailable" },
            });
            return;
          }
          if (url.searchParams.has("course_id"))
            choices.push(url.searchParams.get("course_id")!);
          body = {
            result:
              state === "dnf"
                ? {
                    ...result,
                    is_dnf: true,
                    finish_time_sec: null,
                    total_overall: null,
                  }
                : result,
            performance: { overall_top_pct: state === "dnf" ? null : 30 },
            previous_finish: null,
            historical_field: null,
            course_context: {
              status: state === "error" ? "missing" : state,
              course:
                state === "matched" || url.searchParams.has("course_id")
                  ? course
                  : null,
              candidates:
                state === "ambiguous"
                  ? [
                      {
                        id: 10,
                        race_name: "Mountain Trail North",
                        distance_label: "50 km",
                      },
                      {
                        id: 11,
                        race_name: "Mountain Trail South",
                        distance_label: "50 km",
                      },
                    ]
                  : [],
              message: null,
            },
          };
        }
        await route.fulfill({ json: body });
      });
      await page.addInitScript(
        ({ user, lang }) => {
          localStorage.setItem("uphill_session_token", "preview");
          localStorage.setItem("uphill_user", JSON.stringify(user));
          localStorage.setItem("uphill_lang", lang);
        },
        { user, lang }
      );
      await page.goto("/app?ui=v2&tab=me");
      const panel = page.getByRole("region", {
        name: lang === "en" ? "Race history" : "Lịch sử Race",
        exact: true,
      });
      await panel
        .getByRole("button", {
          name: /Your races, all in one place|Các Race bạn đã tham gia/,
        })
        .click();
      await expect(panel.getByText(result.race_name, { exact: true })).toBeVisible();
      fs.mkdirSync(path.resolve("../docs/screenshots/race-history-review/web"), { recursive: true });
      await panel.screenshot({ path: path.resolve(`../docs/screenshots/race-history-review/web/history-${lang}-${width}.png`) });
      await panel
        .locator("summary")
        .filter({ hasText: result.race_name })
        .click();
      const opener = panel.getByRole("button", {
        name: lang === "en" ? "View details" : "Xem chi tiết",
      });
      const directory = path.resolve(
        "../docs/screenshots/race-history-review/web"
      );
      fs.mkdirSync(directory, { recursive: true });
      for (state of ["matched", "ambiguous", "missing", "dnf", "error"]) {
        await opener.click();
        const dialog = page.getByRole("dialog");
        await expect(dialog).toBeVisible();
        await expect(
          dialog.getByText(
            lang === "en" ? "Loading review…" : "Đang tải thông tin…"
          )
        ).not.toBeVisible();
        await expect(
          dialog.getByRole("heading", { name: result.race_name })
        ).toBeVisible();
        if (state === "matched")
          await expect(
            dialog.getByText(/Course profile: 2026|Thông tin đường đua: 2026/)
          ).toBeVisible();
        if (state === "dnf") {
          await expect(dialog.getByText("DNF", { exact: true })).toBeVisible();
          await expect(dialog.getByText(/Top .*%/)).toHaveCount(0);
        }
        if (state === "error") {
          await expect(dialog.getByRole("alert")).toBeVisible();
        }
        await dialog.screenshot({
          path: path.join(directory, `${state}-${lang}-${width}.png`),
        });
        if (state === "matched") {
          await page.screenshot({ path: path.join(directory, `viewport-${lang}-${width}.png`) });
          await dialog.getByText("Cool mornings; exposed ridges.").scrollIntoViewIfNeeded();
          await dialog.getByRole("link", { name: /Course source|Nguồn đường đua/ }).scrollIntoViewIfNeeded();
          await page.screenshot({ path: path.join(directory, `context-${lang}-${width}.png`) });
        }
        if (state === "ambiguous") {
          await dialog
            .getByRole("button", { name: "Mountain Trail North · 50 km" })
            .click();
          await expect(
            dialog.getByText(/Course profile: 2026|Thông tin đường đua: 2026/)
          ).toBeVisible();
          expect(choices).toContain("10");
        }
        if (state === "error") {
          state = "missing";
          await dialog
            .getByRole("button", { name: lang === "en" ? "Retry" : "Thử lại" })
            .click();
          await expect(
            dialog.getByText(
              lang === "en"
                ? "No course context available"
                : "Chưa có thông tin đường đua"
            )
          ).toBeVisible();
        }
        await page.keyboard.press("Escape");
        await expect(dialog).not.toBeVisible();
        await expect(opener).toBeFocused();
      }
    });
  }
