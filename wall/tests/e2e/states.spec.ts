import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// The states sheet (DRAWER-WALL.md, Testing): screenshots at 390 and 1440 against committed baselines, the live
// canvas masked in the pixel comparison, as is the records panel's build stamp (it changes with every commit); a separate test checks that the canvas drew; axe clean on the sheet.
// WALL_NO_PIXELS=1 (CI) skips the comparisons only. Baselines carry stand-in type (Urbanist, Mona Sans).
// The comparison is tight (threshold 0.1, at most 200 px): with pixelmatch's default 0.2 the frame on the suede and the
// lifted still over the dark drawer did not count as a difference, and `--update-snapshots` kept a baseline without them.
test.describe('the states sheet', () => {
  test.skip(({ browserName, isMobile }) => browserName !== 'chromium' || !!isMobile, 'the baselines are desktop Chromium at two widths');

  for (const [w, h] of [[390, 844], [1440, 900]] as const) {
    test(`matches its baseline at ${w}`, async ({ page }) => {
      await page.setViewportSize({ width: w, height: h });
      await page.goto('states.html');
      // the sheet says when every view is in its state (its sequences fetched, the lifted frames risen)
      await page.waitForFunction(() => !!window.__states?.ready, undefined, { timeout: 45000 });
      await page.evaluate(() => document.fonts.ready);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(500);
      await expect(page).toHaveScreenshot(`states-${w}.png`, { fullPage: true, mask: [...['lifted', 'turned', 'zoomed'].map((f) => page.locator(`drawer-view[data-fixture="${f}"] lifted-frame canvas`)), page.locator('records-panel .build')], threshold: 0.1, maxDiffPixels: 200, timeout: 90000 });   // two full captures must agree, and each takes about ten seconds with the live canvases on the page; a frame missing from a drawer (black on dark suede) must fail, so the colour threshold is tight and at most 200 px may differ
    });
  }

  test('the live canvas drew where the lifted frame is shown', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('states.html');
    await page.waitForFunction(() => !!window.__states?.ready, undefined, { timeout: 45000 });
    await page.waitForLoadState('networkidle');
    const result = await page.evaluate(() => {
      const views = [...document.querySelector('states-sheet')!.shadowRoot!.querySelectorAll('drawer-view')];
      return views.map((v) => {
        const lf = v.shadowRoot?.querySelector('lifted-frame') as (HTMLElement & { hasDrawn?: () => boolean; tier?: number }) | null;
        return { fixture: v.getAttribute('data-fixture'), hasLifted: !!lf, drew: lf?.hasDrawn?.() ?? null, tier: lf?.tier ?? null };
      });
    });
    const live = result.filter((r) => r.hasLifted && r.tier === 2);
    test.info().annotations.push({ type: 'lifted', description: JSON.stringify(result) });
    const store = await page.evaluate(() => ({ glb: !!window.__states?.store.assets.glb('F09'), still: !!window.__states?.store.assets.still('F09') }));
    if (store.glb) {
      // the lifted, turned, zoomed and photographs fixtures carry a live frame at tier 2 (the photographs sit over it; the
      // tier-1 fixture shows the still instead): four canvases, each drawn
      expect(live.map((r) => r.fixture).sort()).toEqual(['lifted', 'photos', 'turned', 'zoomed']);
      for (const r of live) expect(r.drew, `${r.fixture} drew`).toBe(true);
    } else test.info().annotations.push({ type: 'skipped', description: 'no GLB in the manifest yet: the live canvas cannot draw' });
  });

  test('is clean under axe', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('states.html');
    // every fixture in its state (the lifted frames risen, the photographs' bar shown) before the sheet is analysed
    await page.waitForFunction(() => !!window.__states?.ready, undefined, { timeout: 45000 });
    await page.waitForTimeout(500);
    const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
    expect(results.violations.map((v) => `${v.id}: ${v.help} (${v.nodes.map((n) => n.target.join(' ')).join('; ')})`)).toEqual([]);
  });
});
