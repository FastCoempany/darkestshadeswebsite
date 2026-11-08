import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// D1: both pages load, carry noindex, sit on the scene color, and are clean under axe. Screenshots of both at the
// project's viewport go to test-results/ as evidence (pixel baselines start in D5). WALL_NO_PIXELS=1 skips the pixel
// comparisons only, nothing else.
const PAGES = [['index.html', 'the wall'], ['states.html', 'the states sheet']] as const;

for (const [path, name] of PAGES) {
  test(`${name} loads`, async ({ page }, info) => {
    const errors: string[] = [];
    page.on('pageerror', (e) => errors.push(e.message));
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    const res = await page.goto(path);
    expect(res?.ok()).toBe(true);
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', /noindex/);
    const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
    expect(bg).toBe('rgb(0, 0, 0)');
    await page.waitForTimeout(300);
    await page.screenshot({ path: info.outputPath(`${path.replace('.html', '')}-${info.project.name}.png`), fullPage: path === 'index.html' });   // the sheet is long: its full view is the states spec's
    expect(errors, 'no page or console errors').toEqual([]);
  });

  test(`${name} is clean under axe`, async ({ page }) => {
    await page.goto(path);
    const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
    expect(results.violations.map((v) => `${v.id}: ${v.help} (${v.nodes.length})`)).toEqual([]);
  });
}
