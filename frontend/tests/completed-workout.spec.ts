import { test, expect, Page } from '@playwright/test';

// Deterministic API fixtures: no watch account, AI call, or persistent DB row needed.
async function openPlan(page: Page, lang: 'en' | 'vi', suggested = false) {
  const user = { id: 901, name: 'E2E Runner', email: 'e2e@example.test', onboarding_complete: true };
  const plan = { id: 901, race_name: 'E2E Trail 50K', race_date: '2026-11-22', start_date: '2026-09-28', total_weeks: 2, course_distance_km: 50, course_elevation_gain_m: 2400, goal_type: 'finish', plan_status: 'active' };
  const workouts = [
    { id: 901, plan_id: 901, week_number: 1, day_of_week: 'Monday', title: 'Easy Run', type: 'easy_run', phase: 'Base', duration_minutes: 45, distance_km: 7, target_zone: 'Zone 2', is_completed: suggested ? 0 : 1 },
    { id: 902, plan_id: 901, week_number: 1, day_of_week: 'Tuesday', title: 'Hill Repeat', type: 'hill_repeat', phase: 'Base', duration_minutes: 60, distance_km: 8, target_zone: 'Zone 3', is_completed: 0 },
  ];
  await page.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname;
    let body: unknown;
    if (path === '/api/auth/me') body = user;
    else if (path === '/api/health') body = { status: 'healthy' };
    else if (path === '/api/coach/active-plan') body = { active: true, plan, workouts };
    else if (path === '/api/coach/recent-plans') body = { plans: [plan] };
    else if (path === '/api/coach/workouts') body = { workouts };
    else if (path.includes('/block-completion/')) body = { blocks: [{ block_number: 1, unlocked: true, weeks: [1, 2], completion_pct: 50 }], max_generated_week: 2 };
    else if (path === '/api/integrations/matching') body = { activities: [{ activity_id: 901, workout_id: 901, workout_title: 'Easy Run', source_provider: 'coros', device_model: 'COROS PACE 3', activity_type: 'run', distance_km: 7.3, duration_seconds: 2820, avg_hr: 139, elevation_gain_m: 125, start_time: '2026-09-28T06:00:00Z', match_method: suggested ? 'suggest' : 'auto', match_confidence: 0.98 }] };
    await route.fulfill(body === undefined ? { status: 404, json: { detail: "Not part of this fixture" } } : { json: body });
  });
  await page.addInitScript(({ user, lang }) => {
    localStorage.setItem('uphill_session_token', 'e2e-fixture');
    localStorage.setItem('uphill_user', JSON.stringify(user));
    localStorage.setItem('uphill_lang', lang);
  }, { user, lang });
  await page.goto('/app');
  await page.getByRole('button', { name: 'Scheduler', exact: true }).filter({ visible: true }).click();
  return page.locator('details').filter({ has: page.locator('summary').filter({ hasText: 'COROS PACE 3' }) });
}

for (const width of [1440, 390]) {
  for (const lang of ['en', 'vi'] as const) {
    test(`completed COROS stays compact and expands accessibly (${lang}, ${width}px)`, async ({ page }) => {
      await page.setViewportSize({ width, height: 900 });
      const card = await openPlan(page, lang);
      await expect(card).toBeVisible();
      await expect(card).not.toHaveAttribute('open');
      const summary = card.locator('summary');
      for (const metric of ['7.3 km', '47:00', '139 bpm']) await expect(summary).toContainText(metric);
      await expect(summary).toContainText('Data provided by COROS');
      const compactHeight = (await card.boundingBox())!.height;
      expect(compactHeight).toBeLessThan(150);
      const unlink = card.getByRole('button', { name: lang === 'vi' ? 'Gỡ liên kết bài tập' : 'Unlink workout', exact: true });
      await expect(unlink).toBeHidden();
      await summary.focus();
      await page.keyboard.press('Enter');
      await expect(card).toHaveAttribute('open', '');
      await expect(unlink).toBeVisible();
      expect((await card.boundingBox())!.height).toBeGreaterThan(compactHeight);
      await summary.click();
      await expect(card).not.toHaveAttribute('open');
      await expect(page.getByText('Hill Repeat', { exact: true }).first()).toBeVisible();
    });
  }
}

test('suggested watch match keeps confirmation visible', async ({ page }) => {
  const card = await openPlan(page, 'en', true);
  await expect(card).toHaveAttribute('open', '');
  await expect(card.getByRole('button', { name: 'Confirm workout match', exact: true })).toBeVisible();
});
