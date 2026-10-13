import { test, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
const base = {
  claim_id: null,
  source: "vbm",
  discipline: "road",
  elevation_gain_m: null,
  is_dnf: false,
  bib: "42",
  selected: false,
  hidden: false,
  user_note: null,
  verified: false,
  verification_methods: [],
  rank_overall: null,
  total_overall: null,
};
for (const [width, lang] of [
  [1440, "en"],
  [390, "vi"],
] as const) {
  test(`confirmation and manual clear ${width} ${lang}`, async ({ page }) => {
    test.setTimeout(120000);
    await page.setViewportSize({ width, height: 900 });
    const t = (en: string, vi: string) => (lang === "en" ? en : vi);
    const user = {
      id: 901,
      name: "Preview Runner",
      email: "preview@example.test",
      onboarding_complete: true,
    };
    const results: Array<Record<string, unknown>> = [
      {
        ...base,
        id: 7,
        race_name: "Preview City Marathon",
        race_date: "2023-12-03",
        distance_km: 42.195,
        finish_time_sec: 13154,
      },
      {
        ...base,
        id: 8,
        race_name: "Preview Half Marathon",
        race_date: "2023-11-19",
        distance_km: 21.0975,
        finish_time_sec: 6244,
      },
    ];
    let failRefresh = false;
    const writes: Array<Record<string, unknown>> = [];
    await page.route("**/api/**", async (route) => {
      const request = route.request(),
        url = new URL(request.url());
      let body: unknown = {};
      if (url.pathname.includes("invites")) body = [];
      if (url.pathname === "/api/auth/me") body = user;
      if (url.pathname === "/api/coach/active-plan") body = { active: false };
      if (url.pathname === "/api/race-history") {
        if (failRefresh) {
          await route.fulfill({ status: 503, json: { detail: "Unavailable" } });
          return;
        }
        const pr = (id: number) => {
          const r = results.find((row) => row.id === id);
          return r?.selected
            ? {
                result_id: id,
                time_sec: r.finish_time_sec,
                date: r.race_date,
                stale: true,
              }
            : null;
        };
        body = {
          claims: [],
          results,
          summary: {
            trail_finishes: 0,
            trail_dnfs: 0,
            ultras: 0,
            longest_finish: null,
            road_prs: { "5k": null, "10k": null, hm: pr(8), fm: pr(7) },
            road_hm_pr: pr(8),
            road_fm_pr: pr(7),
          },
        };
      }
      if (
        url.pathname === "/api/race-history/results" &&
        request.method() === "POST"
      ) {
        const payload = request.postDataJSON();
        writes.push(payload);
        const row = {
          ...base,
          ...payload,
          id: 9,
          source: "manual",
          selected: true,
        };
        results.push(row);
        body = row;
      }
      if (
        url.pathname.match(/\/api\/race-history\/results\/\d+$/) &&
        request.method() === "PATCH"
      ) {
        const payload = request.postDataJSON();
        writes.push(payload);
        const row = results.find(
          (r) => r.id === Number(url.pathname.split("/").pop())
        )!;
        Object.assign(row, payload);
        body = row;
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
      name: t("Race history", "Lịch sử Race"),
      exact: true,
    });
    await panel
      .getByRole("button", {
        name: /Your races, all in one place|Các Race bạn đã tham gia/,
      })
      .click();
    const confirm = panel.getByRole("button", {
      name: t("This is my result", "Của tôi"),
      exact: true,
    });
    await expect(confirm).toHaveCount(2);
    const directory = path.resolve(
      "../docs/screenshots/race-history-results/web"
    );
    fs.mkdirSync(directory, { recursive: true });
    await panel.screenshot({
      path: path.join(directory, `pending-${lang}-${width}.png`),
    });
    await confirm.first().click();
    await expect(confirm).toHaveCount(1);
    await expect(
      panel.getByRole("region", { name: t("Road personal bests", "PR Road") })
    ).toContainText("3:39:14");
    failRefresh = true;
    await confirm.first().click();
    await expect(panel.getByRole("alert")).toContainText(
      t(
        "Saved, but refresh failed. Retry.",
        "Đã lưu. Tải lại dữ liệu thất bại. Thử lại."
      )
    );
    await panel.screenshot({
      path: path.join(directory, `refresh-error-${lang}-${width}.png`),
    });
    failRefresh = false;
    await panel.getByRole("button", { name: t("Retry", "Thử lại") }).click();
    await expect(confirm).toHaveCount(0);
    await panel.screenshot({
      path: path.join(directory, `confirmed-${lang}-${width}.png`),
    });
    await panel
      .locator("button[aria-expanded]")
      .filter({ hasText: t("Add result", "Thêm kết quả") })
      .click();
    await panel
      .getByLabel(t("Race name", "Tên Race"), { exact: true })
      .fill("My manual half marathon");
    await panel
      .getByLabel(t("Race date", "Ngày Race"), { exact: true })
      .fill("2024-06-01");
    await panel
      .getByRole("combobox", {
        name: t("Discipline", "Loại Race"),
        exact: true,
      })
      .selectOption("road");
    await panel
      .getByLabel(t("Distance (km)", "Cự ly (km)"), { exact: true })
      .fill("21.0975");
    await panel
      .getByLabel(t("Finish time", "Thời gian"), { exact: true })
      .fill("1:50:00");
    await panel
      .getByLabel(t("Elevation gain (m)", "D+ (m)"), { exact: true })
      .fill("0");
    await panel
      .getByLabel(t("Location", "Địa điểm"), { exact: true })
      .fill("Mountain Town");
    await panel
      .getByLabel(t("Race note", "Ghi chú Race"), { exact: true })
      .first()
      .fill("Patient pacing");
    await panel
      .getByRole("button", {
        name: t("Save result", "Lưu kết quả"),
        exact: true,
      })
      .click();
    const row = panel
      .locator("details")
      .filter({ hasText: "My manual half marathon" });
    await expect(row).toBeVisible();
    await row.locator("summary").click();
    await row
      .getByRole("button", {
        name: t("Edit result", "Sửa kết quả"),
        exact: true,
      })
      .click();
    await panel
      .getByLabel(t("Elevation gain (m)", "D+ (m)"), { exact: true })
      .fill("");
    await panel.getByLabel(t("Location", "Địa điểm"), { exact: true }).fill("");
    await panel
      .getByLabel(t("Race note", "Ghi chú Race"), { exact: true })
      .first()
      .fill("");
    await panel.screenshot({
      path: path.join(directory, `manual-edit-${lang}-${width}.png`),
    });
    await panel
      .getByRole("button", {
        name: t("Save changes", "Lưu thay đổi"),
        exact: true,
      })
      .click();
    await expect.poll(() => writes.at(-1)?.elevation_gain_m).toBeNull();
    expect(writes.at(-1)?.location).toBeNull();
    expect(writes.at(-1)?.user_note).toBeNull();
  });
}
