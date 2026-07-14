import { test, expect } from '@playwright/test';

// Pace Strategy modal happy path: pick a KB race, get a section-by-section plan.
// Needs the full local stack (frontend at 8080, backend at 8000 with the
// race_courses KB loaded), same as the other e2e specs.

test('pace strategy: race pick produces a segment plan', async ({ page }) => {
  await page.goto('/');

  await page.getByRole('button', { name: 'Tools', exact: true }).click();
  await page.getByText('Turn a target finish time').click();

  // Pick a race from the KB and give the matcher a distance
  await page.locator('[role="combobox"]').pressSequentially('vmm', { delay: 60 });
  await page.locator('input[placeholder="e.g. 70"]').fill('70');

  // Plan renders: headline chips, chart, table
  await expect(page.getByText('Moving:')).toBeVisible({ timeout: 20000 });
  await expect(page.getByText(/kcal/)).toBeVisible();
  await expect(page.locator('table tbody tr').first()).toContainText('Start');

  // Finish-time slider is seeded within bounds
  const slider = page.locator('input[type="range"]').first();
  const value = Number(await slider.inputValue());
  expect(value).toBeGreaterThan(0);

  // Benchmarks strip appears for VMM 70k (curated 2025 results)
  await expect(page.getByText(/finishers/)).toBeVisible({ timeout: 10000 });
});

test('pace strategy: manual distance works without a race match', async ({ page }) => {
  await page.goto('/');

  await page.getByRole('button', { name: 'Tools', exact: true }).click();
  await page.getByText('Turn a target finish time').click();

  await page.locator('input[placeholder="e.g. 70"]').fill('21');
  await page.locator('input[placeholder="e.g. 4000"]').fill('1000');

  await expect(page.getByText('Moving:')).toBeVisible({ timeout: 20000 });
  const rows = page.locator('table tbody tr');
  await expect(rows.last()).toContainText('21');
});
