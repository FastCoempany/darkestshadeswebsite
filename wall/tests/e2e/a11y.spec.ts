import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { bayButton, clickQuiet, waitForState, wallLoaded } from './helpers';

// Accessibility (DRAWER-WALL.md, Testing): axe on the wall, the drawer view shut and open, the lifted frame and the
// photographs; the names and the live announcements; every target at least 44 px; 320 px (reflow, WCAG 1.4.10); the
// labels' contrast measured against the plate's pixels under each label (at least 4.5:1), portrait and landscape: the
// measure is the mean luminance of the pixels under the label rect (the rail colour the eye reads the text against);
// the 95th and 99th percentiles (the grain's bright flecks) are recorded with it and shown in the record.
const TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];

async function axeClean(page: Page, where: string): Promise<void> {
  const results = await new AxeBuilder({ page }).withTags(TAGS).analyze();
  expect(results.violations.map((v) => `${v.id}: ${v.help} (${v.nodes.map((n) => n.target.join(' ')).join('; ')})`), where).toEqual([]);
}

async function canLift(page: Page): Promise<boolean> {
  return page.evaluate(() => !!window.__wall?.store.bay('drawer_bay/f09')?.canLift);
}

test.describe('accessibility', () => {
  test('the view in every state is clean under axe, named, and announced', async ({ page, browserName, isMobile }) => {
    test.skip(browserName !== 'chromium' || !!isMobile, 'the live frame needs Chromium; one desktop pass');
    await page.goto('index.html');
    await wallLoaded(page);
    await axeClean(page, 'the wall');
    const live = page.locator('drawer-wall').locator('[role="status"]');
    await bayButton(page, 'drawer_bay/f09').click();
    await waitForState(page, ['shut']);
    await expect(live).toHaveText(/What Stevie Saw\. The drawer is shut\./);
    await expect(page.locator('drawer-view').getByRole('dialog', { name: 'What Stevie Saw' })).toBeVisible();
    await axeClean(page, 'the view, shut');
    await clickQuiet(page, 'Open the drawer');
    await waitForState(page, ['open']);
    await expect(live).toHaveText(/What Stevie Saw\. The drawer is open\./);
    await axeClean(page, 'the view, open');
    test.skip(!(await canLift(page)), 'no GLB or lifted still in the manifest');
    await clickQuiet(page, 'Lift them out');
    await waitForState(page, ['lifted'], 20000);
    await expect(live).toHaveText(/What Stevie Saw, lifted out\./);
    await expect(page.locator('drawer-view').locator('lifted-frame canvas')).toHaveAttribute('aria-label', /a view you can turn/);
    await axeClean(page, 'the view, lifted');
    await clickQuiet(page, 'See the photographs');
    await waitForState(page, ['photos']);
    await expect(page.locator('drawer-view').locator('photo-zoom .view')).toHaveAttribute('aria-label', 'See the photographs');
    await axeClean(page, 'the photographs');
    // the next photograph, by the arrow key on the photographs' view and by its angle button: both announced
    await page.keyboard.press('ArrowRight');
    await expect(live).toHaveText(/What Stevie Saw, photograph 2 of \d+: .+/);
    await page.locator('drawer-view').locator('photo-zoom button').first().click();
    await expect(live).toHaveText(/What Stevie Saw, photograph 1 of \d+: .+/);
    await clickQuiet(page, 'Back to the frame');
    await waitForState(page, ['lifted']);
    await clickQuiet(page, 'Put them back');
    await waitForState(page, ['open'], 20000);
    await expect(live).toHaveText(/What Stevie Saw, back in the drawer\./);
    await clickQuiet(page, 'Shut the drawer');
    await waitForState(page, ['shut']);
    await expect(live).toHaveText(/The drawer is shut\./);
  });

  test('every control is at least 44 px: the quiet buttons, the photographs\' bar, the pull-first knobs', async ({ page, browserName }) => {
    test.skip(browserName !== 'chromium', 'the live frame needs Chromium');
    await page.goto('index.html?open=F09');
    await wallLoaded(page);
    await waitForState(page, ['open'], 15000);
    const sizes = async (selector: string) => page.locator('drawer-view').locator(selector).evaluateAll((els) => els.map((el) => { const r = el.getBoundingClientRect(); return { text: (el.textContent ?? '').trim(), w: r.width, h: r.height }; }));
    const check = (list: Array<{ text: string; w: number; h: number }>, where: string) => {
      expect(list.length, where).toBeGreaterThan(0);
      for (const b of list) { expect(b.w, `${where}: ${b.text} is ${b.w} wide`).toBeGreaterThanOrEqual(44); expect(b.h, `${where}: ${b.text} is ${b.h} tall`).toBeGreaterThanOrEqual(44); }
    };
    check(await sizes('button.quiet'), 'open');
    test.skip(!(await canLift(page)), 'no GLB or lifted still in the manifest');
    await clickQuiet(page, 'Lift them out');
    await waitForState(page, ['lifted'], 20000);
    check(await sizes('button.quiet'), 'lifted');
    await clickQuiet(page, 'See the photographs');
    await waitForState(page, ['photos']);
    await clickQuiet(page, 'Closer');
    check(await sizes('photo-zoom button'), 'the photographs');
    // pull first: every knob's target
    await page.goto('index.html?mech=pull');
    await wallLoaded(page);
    const knobs = await page.locator('drawer-wall').locator('drawer-bay .knob').evaluateAll((els) => els.map((el) => { const r = el.getBoundingClientRect(); return { text: el.closest('drawer-bay')?.getAttribute('data-id') ?? '', w: r.width, h: r.height }; }));
    check(knobs, 'the knobs');
    expect(knobs).toHaveLength(8);
  });

  test('320 px: the wall and the view reflow with no horizontal scroll, the name and $100 on screen', async ({ page, browserName, isMobile }) => {
    test.skip(browserName !== 'chromium' || !!isMobile, 'a viewport test on desktop Chromium');
    await page.setViewportSize({ width: 320, height: 568 });
    await page.goto('index.html');
    await wallLoaded(page);
    const overflow = () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(await overflow()).toBeLessThanOrEqual(0);
    for (const id of ['drawer_bay/f01', 'drawer_bay/f02', 'drawer_bay/f09']) {
      const bay = page.locator('drawer-wall').locator(`drawer-bay[data-id="${id}"]`);
      await expect(bay.locator('.price')).toHaveText('$100');
      const box = (await bay.locator('.label').boundingBox())!;
      expect(box.x).toBeGreaterThanOrEqual(0);
      expect(box.x + box.width).toBeLessThanOrEqual(320);
    }
    await page.goto('index.html?open=F02');
    await wallLoaded(page);
    await waitForState(page, ['open'], 15000);
    expect(await overflow()).toBeLessThanOrEqual(0);
    const top = page.locator('drawer-view').locator('.top');
    await expect(top.locator('.micro')).toHaveText(/Holly Wore Them to Breakfast/i);
    await expect(top.locator('.price')).toHaveText('$100');
    const tb = (await top.boundingBox())!;
    expect(tb.x + tb.width).toBeLessThanOrEqual(320);
    for (const b of await page.locator('drawer-view').locator('button.quiet').all()) {
      const r = (await b.boundingBox())!;
      expect(r.x).toBeGreaterThanOrEqual(0);
      expect(r.x + r.width).toBeLessThanOrEqual(320);
      expect(r.y + r.height).toBeLessThanOrEqual(568);
    }
  });

  for (const [layout, w, h] of [['portrait', 390, 844], ['landscape', 1440, 900]] as const) {
    test(`the labels hold 4.5:1 against the plate's pixels under them (${layout})`, async ({ page, browserName, isMobile }) => {
      test.skip(browserName !== 'chromium' || !!isMobile, 'one measurement per layout, from desktop Chromium');
      await page.setViewportSize({ width: w, height: h });
      await page.goto('index.html');
      await wallLoaded(page);
      await expect(page.locator('drawer-wall').locator('.plate')).toHaveAttribute('data-layout', layout);
      await page.locator('drawer-wall').locator('.plate img').evaluate((img) => (img as HTMLImageElement).decode());
      const report = await page.evaluate(async (layout) => {
        const store = window.__wall!.store;
        const wall = document.querySelector('drawer-wall')!.shadowRoot!;
        const img = wall.querySelector('.plate img') as HTMLImageElement;
        const rectsEntry = store.assets.rects(layout, store.knobStyle)!;
        const rects = (await (await fetch(store.assets.url(store.assets.file(rectsEntry)!))).json()) as { drawers: Array<{ label: { x: number; y: number; w: number; h: number } }> };
        const c = document.createElement('canvas');
        c.width = img.naturalWidth; c.height = img.naturalHeight;
        const ctx = c.getContext('2d')!;
        ctx.drawImage(img, 0, 0);
        const lum = (r: number, g: number, b: number) => { const f = (v: number) => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
        const parse = (s: string): [number, number, number] => { s = s.trim(); const m = s.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/); if (m) return [+m[1]!, +m[2]!, +m[3]!]; const x = s.replace('#', ''); return [parseInt(x.slice(0, 2), 16), parseInt(x.slice(2, 4), 16), parseInt(x.slice(4, 6), 16)]; };
        const root = getComputedStyle(document.documentElement);
        const colours: Record<string, number> = {};
        for (const k of ['--color-text-primary', '--color-text-secondary', '--color-text-editorial']) colours[k] = lum(...parse(root.getPropertyValue(k)));
        const out: Array<{ drawer: number; mean: number; p95: number; p99: number; contrast: Record<string, [number, number, number]> }> = [];
        rects.drawers.forEach((d, i) => {
          const x = Math.round((d.label.x / 100) * c.width), y = Math.round((d.label.y / 100) * c.height), rw = Math.round((d.label.w / 100) * c.width), rh = Math.round((d.label.h / 100) * c.height);
          const data = ctx.getImageData(x, y, rw, rh).data;
          const ls: number[] = [];
          for (let p = 0; p < data.length; p += 4) ls.push(lum(data[p]!, data[p + 1]!, data[p + 2]!));
          ls.sort((a, b) => a - b);
          const mean = ls.reduce((a, b) => a + b, 0) / ls.length, p95 = ls[Math.floor(ls.length * 0.95)]!, p99 = ls[Math.floor(ls.length * 0.99)]!;
          const contrast: Record<string, [number, number, number]> = {};
          for (const [k, L] of Object.entries(colours)) contrast[k] = [(L + 0.05) / (mean + 0.05), (L + 0.05) / (p95 + 0.05), (L + 0.05) / (p99 + 0.05)];
          out.push({ drawer: i, mean, p95, p99, contrast });
        });
        return out;
      }, layout);
      const line = report.map((r) => `${r.drawer}: Y mean ${r.mean.toFixed(4)} p95 ${r.p95.toFixed(4)} p99 ${r.p99.toFixed(4)}; ` + Object.entries(r.contrast).map(([k, v]) => `${k.replace('--color-text-', '')} ${v[0].toFixed(2)}/${v[1].toFixed(2)}/${v[2].toFixed(2)}`).join(', ')).join(' | ');
      console.log(`label contrast (${layout}; mean/p95/p99): ${line}`);
      test.info().annotations.push({ type: 'contrast', description: line });
      expect(report).toHaveLength(8);
      for (const r of report) for (const [k, [atMean]] of Object.entries(r.contrast)) {
        expect(atMean, `${layout} drawer ${r.drawer}: ${k} against the rail's mean luminance`).toBeGreaterThanOrEqual(4.5);
      }
    });
  }
});
