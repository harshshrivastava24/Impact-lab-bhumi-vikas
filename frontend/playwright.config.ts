import { defineConfig } from '@playwright/test';

/**
 * Layout, print and network checks at the counter resolution (1366 x 768).
 * Uses the locally installed Microsoft Edge, so no browser download is needed.
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  fullyParallel: false,
  reporter: [['list']],
  use: {
    baseURL: 'http://127.0.0.1:5173',
    channel: 'msedge',
    viewport: { width: 1366, height: 768 },
    locale: 'en-IN',
  },
  webServer: {
    command: 'npm run dev:mock -- --host 127.0.0.1',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
