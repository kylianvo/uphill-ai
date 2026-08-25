import path from 'path';
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: path.resolve(__dirname, 'tests'),
  testMatch: /.*\.spec\.ts$/,
  testIgnore: ['**/.claude/**', '**/node_modules/**', '**/.next/**'],
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://127.0.0.1:8080',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    }
  ],
});
