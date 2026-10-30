import {defineConfig} from '@playwright/test';

/**
 * Playwright: screenshots, axe and behaviour against the review build (production settings, drafts
 * allowed) and the static Storybook. Visual tests run here, at 1x, with no hosted service (RUN.md).
 */
const APP = 'http://localhost:3000';
const STORYBOOK = 'http://localhost:6006';

export default defineConfig({
  testDir: 'tests/e2e',
  timeout: 90_000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: process.env.CI ? [['list'], ['html', {open: 'never'}]] : [['list']],
  snapshotPathTemplate: '{testDir}/__screenshots__/{projectName}/{testFilePath}/{arg}{ext}',
  expect: {
    toHaveScreenshot: {maxDiffPixelRatio: 0.002, animations: 'disabled', scale: 'css'},
  },
  use: {
    deviceScaleFactor: 1,
    colorScheme: 'dark',
    locale: 'en-US',
    timezoneId: 'America/Chicago',
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'app-390',
      testIgnore: /storybook/,
      use: {baseURL: APP, viewport: {width: 390, height: 844}, isMobile: true, hasTouch: true},
    },
    {
      name: 'app-1440',
      testIgnore: /storybook/,
      use: {baseURL: APP, viewport: {width: 1440, height: 900}},
    },
    {
      name: 'storybook',
      testMatch: /storybook/,
      use: {baseURL: STORYBOOK, viewport: {width: 1440, height: 900}},
    },
    // The review sets: `DS_CAPTURE=wire npx playwright test --project=capture` (docs/wireframes/) or `DS_CAPTURE=ui` (docs/ui/).
    ...(process.env.DS_CAPTURE
      ? [
          {
            name: 'capture',
            testDir: 'tests/capture',
            use: {baseURL: APP},
          },
        ]
      : []),
  ],
  webServer: [
    {
      command: 'npm run preview:review -- --port 3000',
      url: `${APP}/`,
      reuseExistingServer: !process.env.CI,
      timeout: 300_000,
      stdout: 'ignore',
      stderr: 'pipe',
    },
    {
      command: 'node checks/serve-storybook.mjs',
      url: `${STORYBOOK}/iframe.html`,
      reuseExistingServer: !process.env.CI,
      timeout: 300_000,
      stdout: 'ignore',
      stderr: 'pipe',
    },
  ],
});
