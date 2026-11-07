import { defineConfig, devices } from '@playwright/test';

// Three projects (DRAWER-WALL.md, Testing): Chromium as a Pixel with touch, WebKit as an iPhone (everything but the
// live 3D), and desktop Chromium. The suites run against the built wall served by `vite preview`, as a phone would get
// it. Screenshot baselines sit next to the specs. `WALL_NO_PIXELS=1` (CI) skips the pixel comparisons only.
export default defineConfig({
  testDir: 'tests/e2e',
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  timeout: 60_000,
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.002, animations: 'disabled', caret: 'hide' } },
  // CI has no committed-baseline fonts or GPU: WALL_NO_PIXELS=1 skips the toHaveScreenshot comparisons and nothing else
  ignoreSnapshots: !!process.env.WALL_NO_PIXELS,
  snapshotPathTemplate: '{testDir}/{testFileDir}/__screenshots__/{testFileName}/{projectName}/{arg}{ext}',
  outputDir: 'test-results',
  use: {
    baseURL: 'http://127.0.0.1:4173/',
    trace: 'off',
    video: 'off',
    screenshot: 'off',
  },
  webServer: {
    command: 'npm run preview',
    url: 'http://127.0.0.1:4173/',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
  projects: [
    { name: 'wall-pixel', use: { ...devices['Pixel 7'], browserName: 'chromium' } },
    { name: 'wall-iphone', use: { ...devices['iPhone 14'], browserName: 'webkit' } },
    { name: 'wall-desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
  ],
});
