import { test } from '@playwright/test';

// The review screens (DRAWER-WALL.md, the phases' exit lists): both pages at 390 and 1440 wide, saved under
// test-results/screens/ as evidence. Not pixel-compared here (the states sheet's baselines start in D5).
const WIDTHS = [[390, 844], [1440, 900]] as const;
const PAGES = ['index.html', 'states.html'] as const;

test.describe('review screens', () => {
  test.skip(({ browserName, isMobile }) => browserName !== 'chromium' || !!isMobile, 'one set, from desktop Chromium');
  for (const path of PAGES) for (const [w, h] of WIDTHS) {
    test(`${path} at ${w}`, async ({ page }, info) => {
      await page.setViewportSize({ width: w, height: h });
      await page.goto(path);
      await page.evaluate(() => document.fonts.ready);
      await page.waitForTimeout(200);
      await page.screenshot({ path: info.outputPath(`${path.replace('.html', '')}-${w}.png`), fullPage: true });
    });
  }
});
