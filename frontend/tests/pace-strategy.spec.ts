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
  // number inputs keep rendering after a match (typed values override the KB)
  await page.locator('input[type="number"]').first().fill('70');

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

test('goal determiner: reference result produces A/B/C goals and hands off to pace strategy', async ({ page }) => {
  await page.goto('/');

  await page.getByRole('button', { name: 'Tools', exact: true }).click();
  await page.getByText('Find out what finish time').click();

  // target: VMM 70k from the KB
  await page.locator('[role="combobox"]').first().pressSequentially('vmm', { delay: 60 });
  const numberInputs = page.locator('input[type="number"]');
  await numberInputs.nth(0).fill('70'); // target distance
  await numberInputs.nth(2).fill('16'); // weeks until race

  // fitness: a manual 50k / 2500m in 7:30
  await numberInputs.nth(3).fill('50'); // reference distance
  await numberInputs.nth(4).fill('2500'); // reference gain
  await page.locator('input[placeholder="e.g. 7:30:00"]').fill('7:30:00');

  await page.getByRole('button', { name: /Estimate my goal/ }).click();

  await expect(page.getByText('Ambitious', { exact: true })).toBeVisible({ timeout: 15000 });
  await expect(page.getByText('Realistic', { exact: true })).toBeVisible();
  await expect(page.getByText('Safe', { exact: true })).toBeVisible();

  // hand the realistic goal into Pace Strategy: modal opens with a plan
  await page.getByRole('button', { name: 'Plan pacing' }).nth(1).click();
  await expect(page.getByRole('heading', { name: 'Pace Strategy', level: 2 })).toBeVisible();
  await expect(page.getByText('Moving:')).toBeVisible({ timeout: 20000 });
});

test('pace strategy: manual distance works without a race match', async ({ page }) => {
  await page.goto('/');

  await page.getByRole('button', { name: 'Tools', exact: true }).click();
  await page.getByText('Turn a target finish time').click();

  await page.locator('input[type="number"]').nth(0).fill('21');
  await page.locator('input[type="number"]').nth(1).fill('1000');

  await expect(page.getByText('Moving:')).toBeVisible({ timeout: 20000 });
  const rows = page.locator('table tbody tr');
  await expect(rows.last()).toContainText('21');
});
