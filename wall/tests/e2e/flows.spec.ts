import { test, expect } from '@playwright/test';
import { bayButton, bayCenter, clickQuiet, stageCenter, touchDrag, touchDragXY, touchPinch, touchTap, viewState, waitForState, wallLoaded } from './helpers';

// The end-to-end flows (DRAWER-WALL.md, Testing): every drawer shows its name and $100; tap first: open, pull,
// settle both ways, lift, turn, pinch, photographs, put back, shut, close with focus back on the drawer; pull
// first: a pull on the knob opens and keeps pulling, a swipe on the face scrolls; tap first: a vertical swipe on a
// drawer scrolls and opens nothing; keyboard only; reduced motion; WebGL disabled (tier 1); ?open=; no JavaScript
// (tier 0); the records panel changes one drawer and no other.
const FRAMES = [['drawer_bay/f01', '01', 'Lou Went Underground'], ['drawer_bay/f02', '02', 'Holly Wore Them to Breakfast'], ['drawer_bay/f03', '03', 'Roy Forgot the Clear Ones'], ['drawer_bay/f04', '04', 'K Was Never Here'], ['drawer_bay/f05', '05', 'Jackie Gave Them Nothing'], ['drawer_bay/f06', '06', 'What Anna Thought'], ['drawer_bay/f08', '08', 'What Arnie Hid'], ['drawer_bay/f09', '09', 'What Stevie Saw']] as const;

test('every drawer shows its look number, its name and $100, and is a button named for it', async ({ page }) => {
  await page.goto('index.html');
  await wallLoaded(page);
  for (const [id, look, name] of FRAMES) {
    const bay = page.locator('drawer-wall').locator(`drawer-bay[data-id="${id}"]`);
    await expect(bay.locator('.look')).toHaveText(look);
    await expect(bay.locator('.name')).toHaveText(name.toUpperCase().length ? new RegExp(name, 'i') : name);
    await expect(bay.locator('.price')).toHaveText('$100');
    await expect(bayButton(page, id)).toHaveAttribute('aria-label', `${name}, $100. Open the drawer.`);
  }
});

test.describe('tap first', () => {
  test('open, pull, settle both ways, shut, close with focus back on the drawer', async ({ page, browserName, isMobile }) => {
    test.skip(browserName !== 'chromium' || !isMobile, 'touch through CDP needs Chromium');
    await page.goto('index.html?debug=1');
    await wallLoaded(page);
    const cdp = await page.context().newCDPSession(page);
    const c = await bayCenter(page, 'drawer_bay/f09');
    await touchTap(cdp, page, c.x, c.y);
    expect(await waitForState(page, ['shut', 'entering'])).toBeTruthy();
    await waitForState(page, ['shut']);
    const s = await stageCenter(page);
    // a slow pull halfway and release: it settles shut (position under 0.5)
    await touchDrag(cdp, page, s.x, s.y - s.h * 0.3, s.y - s.h * 0.3 + s.h * 0.45 * 0.3, 14, 40);
    expect(await waitForState(page, ['shut', 'shutting'])).toBeTruthy();
    await waitForState(page, ['shut']);
    // a full pull: it settles open
    await touchDrag(cdp, page, s.x, s.y - s.h * 0.35, s.y - s.h * 0.35 + s.h * 0.45 * 1.1, 14, 40);
    await waitForState(page, ['open', 'opening']);
    await waitForState(page, ['open']);
    expect((await viewState(page))!.p).toBe(1);
    // a fast flick up shuts it (velocity wins)
    await touchDrag(cdp, page, s.x, s.y, s.y - 120, 4, 8);
    await waitForState(page, ['shut', 'shutting']);
    await waitForState(page, ['shut']);
    await clickQuiet(page, 'Open the drawer');
    await waitForState(page, ['open']);
    await clickQuiet(page, 'Shut the drawer');
    await waitForState(page, ['shut']);
    await clickQuiet(page, 'Close');
    await page.waitForFunction(() => !(document.querySelector('drawer-view') as HTMLElement & { open?: boolean })?.open);
    await expect(bayButton(page, 'drawer_bay/f09')).toBeFocused();
  });

  test('a vertical swipe on a drawer scrolls the wall and opens nothing', async ({ page, browserName, isMobile }) => {
    test.skip(browserName !== 'chromium' || !isMobile, 'touch through CDP needs Chromium');
    await page.setViewportSize({ width: 412, height: 520 });   // short enough that the wall must scroll
    await page.goto('index.html');
    await wallLoaded(page);
    const cdp = await page.context().newCDPSession(page);
    const c = await bayCenter(page, 'drawer_bay/f01');
    const before = await page.evaluate(() => scrollY);
    await touchDrag(cdp, page, c.x, c.y, c.y - 220, 10);
    await page.waitForTimeout(500);
    expect(await page.evaluate(() => scrollY)).toBeGreaterThan(before);
    expect(await viewState(page)).toBeNull();
  });
});

test.describe('pull first (?mech=pull)', () => {
  test('a pull on the knob opens and keeps pulling; a swipe on the face scrolls', async ({ page, browserName, isMobile }) => {
    test.skip(browserName !== 'chromium' || !isMobile, 'touch through CDP needs Chromium');
    await page.goto('index.html?mech=pull');
    await wallLoaded(page);
    const cdp = await page.context().newCDPSession(page);
    const knob = page.locator('drawer-wall').locator('drawer-bay[data-id="drawer_bay/f09"]').locator('.knob');
    const kb = (await knob.boundingBox())!;
    expect(kb.width).toBeGreaterThanOrEqual(44);
    expect(kb.height).toBeGreaterThanOrEqual(44);
    const kx = kb.x + kb.width / 2, ky = kb.y + kb.height / 2;
    await touchDrag(cdp, page, kx, ky, ky + 320, 16, 30);
    const st = await waitForState(page, ['pulling', 'opening', 'open', 'shutting', 'shut']);
    expect(['pulling', 'opening', 'open']).toContain(st);
    await waitForState(page, ['open']);
    await clickQuiet(page, 'Close');
    await page.waitForFunction(() => !(document.querySelector('drawer-view') as HTMLElement & { open?: boolean })?.open);
    // the face still scrolls (a viewport short enough that the wall must scroll)
    await page.setViewportSize({ width: 412, height: 520 });
    const c = await bayCenter(page, 'drawer_bay/f03');
    const before = await page.evaluate(() => scrollY);
    await touchDrag(cdp, page, c.x - 60, c.y, c.y - 220, 10);
    await page.waitForTimeout(400);
    expect(await page.evaluate(() => scrollY)).toBeGreaterThan(before);
  });
});

test.describe('the lift', () => {
  test('lift, turn, pinch, the photographs, put back', async ({ page, browserName, isMobile }) => {
    test.skip(browserName !== 'chromium', 'the live frame needs Chromium (WebKit headless has no reliable WebGL)');
    await page.goto('index.html?open=F09&debug=1');
    await wallLoaded(page);
    await waitForState(page, ['open'], 15000);
    const canLift = await page.evaluate(() => (window as unknown as { __wall: { store: { bay(id: string): { canLift: boolean } } } }).__wall.store.bay('drawer_bay/f09').canLift);
    test.skip(!canLift, 'no GLB or lifted still in the manifest yet (D4)');
    // the lift by the gesture: a tap on the frame in the open drawer (the tap-frame's region; the button is the keyboard's)
    const s0 = await stageCenter(page);
    if (isMobile) await touchTap(await page.context().newCDPSession(page), page, s0.x, s0.y - s0.h * 0.08);
    else await page.mouse.click(s0.x, s0.y - s0.h * 0.08);
    await waitForState(page, ['lifted'], 20000);
    const yaw0 = await page.evaluate(() => (document.querySelector('drawer-view') as unknown as { ctx: { yaw: number } }).ctx?.yaw ?? 0);
    await clickQuiet(page, 'Turn right');
    const yaw1 = await page.evaluate(() => (document.querySelector('drawer-view') as unknown as { ctx: { yaw: number } }).ctx?.yaw ?? 0);
    expect(yaw1).not.toBe(yaw0);
    if (isMobile) {
      const cdp = await page.context().newCDPSession(page);
      const s = await stageCenter(page);
      await touchDragXY(cdp, page, { x: s.x - 60, y: s.y }, { x: s.x + 60, y: s.y });
      const yaw2 = await page.evaluate(() => (document.querySelector('drawer-view') as unknown as { ctx: { yaw: number } }).ctx?.yaw ?? 0);
      expect(yaw2).not.toBe(yaw1);
      await touchPinch(cdp, page, s.x, s.y, 2.0);
      const zoom = await page.evaluate(() => (document.querySelector('drawer-view') as unknown as { ctx: { zoom: number } }).ctx?.zoom ?? 1);
      expect(zoom).toBeGreaterThan(1.3);
    }
    await clickQuiet(page, 'See the photographs');
    await waitForState(page, ['photos']);
    await expect(page.locator('drawer-view').locator('photo-zoom')).toBeVisible();
    await clickQuiet(page, 'Back to the frame');
    await waitForState(page, ['lifted']);
    await clickQuiet(page, 'Put them back');
    await waitForState(page, ['open'], 20000);
  });
});

test('keyboard only, end to end', async ({ page, isMobile }) => {
  test.skip(!!isMobile, 'a keyboard flow');
  await page.goto('index.html');
  await wallLoaded(page);
  await bayButton(page, 'drawer_bay/f01').focus();
  await page.keyboard.press('Enter');
  await waitForState(page, ['shut']);
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('ArrowDown');
  await waitForState(page, ['pulling', 'shutting', 'shut', 'opening', 'open']);
  for (let i = 0; i < 8; i++) await page.keyboard.press('PageDown');
  await waitForState(page, ['open', 'opening'], 6000);
  await waitForState(page, ['open']);
  await page.keyboard.press('Escape');
  await waitForState(page, ['shut', 'shutting']);
  await waitForState(page, ['shut']);
  await page.keyboard.press('Escape');
  await page.waitForFunction(() => !(document.querySelector('drawer-view') as HTMLElement & { open?: boolean })?.open);
  await expect(bayButton(page, 'drawer_bay/f01')).toBeFocused();
});

test('reduced motion: the drawer snaps, no spring', async ({ page, browserName }) => {
  test.skip(browserName === 'webkit', 'emulateMedia with reduced motion is checked in Chromium');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('index.html?open=F02&debug=1');
  await wallLoaded(page);
  await waitForState(page, ['open'], 15000);
  await clickQuiet(page, 'Shut the drawer');
  const t0 = Date.now();
  await waitForState(page, ['shut']);
  expect(Date.now() - t0).toBeLessThan(700);
});

test('WebGL disabled: tier 1, everything but the live frame', async ({ browser, browserName }) => {
  test.skip(browserName !== 'chromium', 'a Chromium flag');
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.addInitScript(() => { const orig = HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext = function (this: HTMLCanvasElement, type: string, ...rest: unknown[]) { if (type === 'webgl2' || type === 'webgl') return null; return (orig as (this: HTMLCanvasElement, t: string, ...r: unknown[]) => RenderingContext | null).call(this, type, ...rest); } as typeof orig; });
  await page.goto('index.html?open=F09');
  await wallLoaded(page);
  await expect(page.locator('drawer-wall')).toHaveAttribute('data-tier', '1');
  await waitForState(page, ['open'], 15000);
  await expect(page.locator('drawer-view').locator('button.quiet', { hasText: /turn left/i })).toHaveCount(0);
  await ctx.close();
});

test('?open= opens that drawer on its last frame, not lifted; an unknown value opens nothing', async ({ page }) => {
  await page.goto('index.html?open=what-arnie-hid');
  await wallLoaded(page);
  expect(await waitForState(page, ['open'], 15000)).toBe('open');
  await expect(page.locator('drawer-view')).toHaveAttribute('aria-label', /What Arnie Hid/);
  await page.goto('index.html?open=F07');
  await wallLoaded(page);
  await page.waitForTimeout(800);
  expect(await viewState(page)).toBeNull();
});

test('no JavaScript: the plate and a plain list of the eight drawers, each linking to its photograph', async ({ browser }) => {
  const ctx = await browser.newContext({ javaScriptEnabled: false });
  const page = await ctx.newPage();
  await page.goto('index.html');
  const items = page.locator('noscript ol li, .tier0 ol li');
  await expect(page.locator('.tier0 h1')).toHaveText('The frames');
  await expect(items).toHaveCount(8);
  for (const [, look, name] of FRAMES) await expect(page.locator('.tier0')).toContainText(look);
  await expect(page.locator('.tier0 a[href$="f09-a1.webp"]')).toContainText('What Stevie Saw');
  await expect(page.locator('.tier0')).toContainText('$100');
  await ctx.close();
});

test('the records panel changes one drawer and no other', async ({ page }) => {
  await page.goto('index.html?panel=1');
  await wallLoaded(page);
  const panel = page.locator('records-panel');
  await expect(panel.locator('h2')).toHaveText('Records (example data)');
  const f04 = page.locator('drawer-wall').locator('drawer-bay[data-id="drawer_bay/f04"]');
  await expect(f04.locator('button.face')).toHaveAttribute('data-light', 'lit');
  await panel.locator('fieldset[data-id="drawer_bay/f04"] select').nth(1).selectOption('sold_out');
  await expect(f04.locator('button.face')).toHaveAttribute('data-light', 'dark');
  await expect(f04.locator('.status')).toHaveText('Sold out');
  for (const [id] of FRAMES) if (id !== 'drawer_bay/f04') await expect(bayButton(page, id)).toHaveAttribute('data-light', 'lit');
  await panel.locator('fieldset[data-id="drawer_bay/f04"] select').nth(1).selectOption('locked');
  await expect(f04.locator('.name')).toHaveText('Not yet.');
  await expect(bayButton(page, 'drawer_bay/f04')).toBeDisabled();
  await panel.locator('fieldset[data-id="drawer_bay/f04"] select').nth(1).selectOption('hidden');
  await expect(f04.locator('button.face')).toHaveCount(0);
  await expect(f04.locator('.label')).toHaveCount(0);
});
