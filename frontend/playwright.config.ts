import path from 'path';
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: path.resolve(__dirname, 'tests'),
  testMatch: /.*\.spec\.ts$/,
  // NOTE: '**/.claude/**' used to be in this list. Playwright's ignore glob
  // matches ANY ancestor path segment, and this repo is checked out under
  // .claude/worktrees/<name>/ in every agentic worktree session -- so that
  // entry silently excluded every single test file whenever run from a
  // worktree, with no error beyond a bare "No tests found". testDir already
  // scopes discovery to tests/, which has no .claude subdirectory to guard
  // against, so the entry was pure risk with no benefit.
  testIgnore: ['**/node_modules/**', '**/.next/**'],
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:8080',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    }
  ],
});
