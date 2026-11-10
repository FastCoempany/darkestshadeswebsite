import { test, expect } from '@playwright/test';
import { bayButton, bayCenter, clickQuiet, focused, stageCenter, tabTo, touchDrag, touchDragXY, touchEnd, touchMoveTo, touchPinch, touchStart, touchTap, viewState, waitForState, wallLoaded } from './helpers';

// The end-to-end flows (DRAWER-WALL.md, Testing): every drawer shows its name and no price (#47); tap first: open, pull,
// settle both ways, lift, turn, pinch, photographs, put back, shut, close with focus back on the drawer; pull
// first: a pull on the knob opens and keeps pulling, a swipe on the face scrolls; tap first: a vertical swipe on a
// drawer scrolls and opens nothing; keyboard only (the pull, and the lift, the photographs and the way back through
// the quiet buttons, Tab reaching the controls inside nested shadow roots); reduced motion; WebGL disabled (tier 1:
// the lifted still); ?open=; no JavaScript (tier 0); the records panel changes one drawer and no other.
const FRAMES = [['drawer_bay/f01', '01', 'Lou Went Underground'], ['drawer_bay/f02', '02', 'Holly Wore Them to Breakfast'], ['drawer_bay/f03', '03', 'Roy Forgot the Clear Ones'], ['drawer_bay/f04', '04', 'K Was Never Here'], ['drawer_bay/f05', '05', 'Jackie Gave Them Nothing'], ['drawer_bay/f06', '06', 'What Anna Thought'], ['drawer_bay/f08', '08', 'What Arnie Hid'], ['drawer_bay/f09', '09', 'What Stevie Saw']] as const;

test('every drawer shows its look number and its name, no price, and is a button named for it', async ({ page }) => {
  await page.goto('index.html');
  await wallLoaded(page);
  for (const [id, look, name] of FRAMES) {
    const bay = page.locator('drawer-wall').locator(`drawer-bay[data-id="${id}"]`);
    await expect(bay.locator('.look')).toHaveText(look);
    await expect(bay.locator('.name')).toHaveText(name.toUpperCase().length ? new RegExp(name, 'i') : name);
    await expect(bay.locator('.price')).toHaveCount(0);
    expect(await bay.evaluate((el) => el.shadowRoot!.textContent ?? '')).not.toMatch(/\$|100/);   // no price anywhere in the drawer (#47)
    await expect(bayButton(page, id)).toHaveAttribute('aria-label', `${name}. Open the drawer.`);
  }
});

test.describe('tap first', () => {
  test('open, pull, settle both ways, shut, close with focus back on the drawer', async ({ page, browserName, isMobile }) => {
    test.skip(browserName !== 'chromium' || !isMobile, 'touch through CDP, on the Pixel project (Chromium with a mobile viewport)');
    await page.goto('index.html?debug=1');
    await wallLoaded(page);
    const cdp = await page.context().newCDPSession(page);
    const c = await bayCenter(page, 'drawer_bay/f09');
    await touchTap(cdp, page, c.x, c.y, 2);   // a real finger moves a pixel or two
    expect(await waitForState(page, ['shut', 'entering'])).toBeTruthy();
    await waitForState(page, ['shut']);
    const s = await stageCenter(page);
    const vh = page.viewportSize()!.height;   // a full pull is 45% of the view's height (DRAWER-WALL.md, Interaction constants)
    // a slow pull to 30% of a full pull and release: it settles shut (position under 0.5)
    await touchDrag(cdp, page, s.x, s.y - s.h * 0.3, s.y - s.h * 0.3 + vh * 0.45 * 0.3, 14, 40);
    expect(await waitForState(page, ['shut', 'shutting'])).toBeTruthy();
    await waitForState(page, ['shut']);
    // a full pull, held: at 45% of the stage's height the drawer is not yet open (the stage is 4:5 of the width, a part
    // of the view), at 45% of the view's height it is; let go and it settles open
    const y0 = s.y - s.h * 0.35;
    await touchStart(cdp, s.x, y0);
    await touchMoveTo(cdp, page, s.x, y0, y0 + s.h * 0.45, 10, 30);
    expect((await viewState(page))!.p).toBeGreaterThan(0.3);
    expect((await viewState(page))!.p).toBeLessThan(0.9);
    await touchMoveTo(cdp, page, s.x, y0 + s.h * 0.45, y0 + vh * 0.45 * 1.05, 6, 30);
    expect((await viewState(page))!.p).toBeGreaterThanOrEqual(0.98);
    await touchEnd(cdp);
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
    test.skip(browserName !== 'chromium' || !isMobile, 'touch through CDP, on the Pixel project (Chromium with a mobile viewport)');
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
    test.skip(browserName !== 'chromium' || !isMobile, 'touch through CDP, on the Pixel project (Chromium with a mobile viewport)');
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
    // the lift by the gesture: a tap on the frame in the open drawer (the stage's frame region; the quiet button is the
    // keyboard's), with the pixel or two of movement a real finger makes (inside the 8 px tap slop)
    const s0 = await stageCenter(page);
    if (isMobile) await touchTap(await page.context().newCDPSession(page), page, s0.x, s0.y - s0.h * 0.08, 2);
    else { await page.mouse.move(s0.x, s0.y - s0.h * 0.08); await page.mouse.down(); await page.mouse.move(s0.x + 2, s0.y - s0.h * 0.08 + 1); await page.mouse.up(); }
    await waitForState(page, ['lifted'], 20000);
    // the live frame is shown, at the inspect pose, over the empty drawer (the base sequence's last frame, faded in)
    const lifted = page.locator('drawer-view').locator('lifted-frame');
    await expect(lifted.locator('canvas.live')).toHaveCSS('opacity', '1');
    expect(await lifted.evaluate((el) => (el as unknown as { liftProgress: number }).liftProgress)).toBe(1);
    await expect(page.locator('drawer-view').locator('picture.empty')).toHaveClass(/\bin\b/);
    await expect(page.locator('drawer-view').locator('picture.empty')).toHaveCSS('opacity', '1');
    const yaw0 = await page.evaluate(() => (document.querySelector('drawer-view') as unknown as { ctx: { yaw: number } }).ctx?.yaw ?? 0);
    await clickQuiet(page, 'Turn right');
    const yaw1 = await page.evaluate(() => (document.querySelector('drawer-view') as unknown as { ctx: { yaw: number } }).ctx?.yaw ?? 0);
    expect(yaw1).not.toBe(yaw0);
    const pitch0 = await page.evaluate(() => (document.querySelector('drawer-view') as unknown as { ctx: { pitch: number } }).ctx?.pitch ?? 0);
    await clickQuiet(page, 'Tilt up');
    const pitch1 = await page.evaluate(() => (document.querySelector('drawer-view') as unknown as { ctx: { pitch: number } }).ctx?.pitch ?? 0);
    expect(pitch1).not.toBe(pitch0);
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
    // the pan buttons appear once the photograph is larger than the view, and move it
    const zoom = page.locator('drawer-view').locator('photo-zoom');
    await expect(zoom.locator('button', { hasText: /^Up$/ })).toHaveCount(0);
    await clickQuiet(page, 'Closer');
    await expect(zoom.locator('button', { hasText: /^Up$/ })).toHaveCount(1);
    // which way it can move depends on the viewport (a landscape photograph in a portrait view overhangs sideways only), so
    // both axes are pressed and the photograph must have moved
    const pan0 = await zoom.evaluate((el) => JSON.stringify((el as unknown as { pan: { x: number; y: number } }).pan));
    await clickQuiet(page, 'Down');
    await clickQuiet(page, 'Right');
    expect(await zoom.evaluate((el) => JSON.stringify((el as unknown as { pan: { x: number; y: number } }).pan))).not.toBe(pan0);
    await clickQuiet(page, 'Back to the frame');
    await waitForState(page, ['lifted']);
    await clickQuiet(page, 'Put them back');
    await waitForState(page, ['open'], 20000);
    // the empty drawer has faded out again: the rendered frame is back in the drawer
    await expect(page.locator('drawer-view').locator('picture.empty')).not.toHaveClass(/\bin\b/);
    await expect(page.locator('drawer-view').locator('lifted-frame')).toHaveCount(0);
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
  expect((await viewState(page))!.p).toBeGreaterThan(0);   // each ArrowDown pulls the drawer 12% of the way (it lets go 320 ms after the last key)
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

test('keyboard only: the lift, the photographs and the way back through the quiet buttons; Tab reaches the controls inside nested shadow roots', async ({ page, isMobile, browserName }) => {
  test.skip(!!isMobile, 'a keyboard flow');
  test.skip(browserName !== 'chromium', 'the live frame needs Chromium (WebKit headless has no reliable WebGL)');
  await page.goto('index.html?open=F09');
  await wallLoaded(page);
  await waitForState(page, ['open'], 15000);
  const canLift = await page.evaluate(() => (window as unknown as { __wall: { store: { bay(id: string): { canLift: boolean } } } }).__wall.store.bay('drawer_bay/f09').canLift);
  test.skip(!canLift, 'no GLB or lifted still in the manifest yet (D4)');
  // from the stage, Tab reaches the quiet buttons in order; Enter on "Lift them out" lifts
  await tabTo(page, 'Shut the drawer', 3);
  await tabTo(page, 'Lift them out', 1);
  await page.keyboard.press('Enter');
  await waitForState(page, ['lifted'], 20000);
  // the Tab cycle in the lifted view: the live frame's canvas (inside <lifted-frame>'s shadow root), the quiet buttons,
  // and round again to the canvas
  const cycle: string[] = [];
  for (let i = 0; i < 12; i++) { await page.keyboard.press('Tab'); const f = (await focused(page))!; cycle.push(f.tag === 'CANVAS' ? 'CANVAS' : f.text); if (i > 0 && cycle[i] === 'CANVAS') break; }
  expect(cycle).toEqual(['CANVAS', 'Turn left', 'Turn right', 'Tilt up', 'Tilt down', 'Closer', 'Further', 'Reset', 'See the photographs', 'Put them back', 'CANVAS']);
  // the arrow keys turn and tilt the frame, + and - bring it closer and further, 0 resets: the pose from the machine
  const pose = () => page.evaluate(() => { const c = (document.querySelector('drawer-view') as unknown as { ctx: { yaw: number; pitch: number; zoom: number } }).ctx; return { yaw: c.yaw, pitch: c.pitch, zoom: c.zoom }; });
  const p0 = await pose();
  await page.keyboard.press('ArrowRight');
  expect((await pose()).yaw).toBeGreaterThan(p0.yaw);
  await page.keyboard.press('ArrowUp');
  expect((await pose()).pitch).not.toBe(p0.pitch);
  await page.keyboard.press('+');
  expect((await pose()).zoom).toBeGreaterThan(1);
  await page.keyboard.press('0');
  expect(await pose()).toEqual(p0);
  await page.keyboard.press('Shift+Tab');
  expect((await focused(page))?.text).toBe('Put them back');
  // the photographs by keyboard: focus starts on their view; Tab reaches every button of the bar (inside <photo-zoom>'s
  // shadow root), wraps to the view and comes back
  await tabTo(page, 'See the photographs', 12, true);
  await page.keyboard.press('Enter');
  await waitForState(page, ['photos']);
  expect((await focused(page))?.cls).toBe('view');
  const firstAngle = await page.locator('drawer-view').locator('photo-zoom button').first().textContent();
  await page.keyboard.press('Tab');
  expect((await focused(page))?.text).toBe(firstAngle?.trim());
  await tabTo(page, 'Back to the frame', 12);
  await page.keyboard.press('Tab');
  expect((await focused(page))?.cls).toBe('view');
  await page.keyboard.press('Shift+Tab');
  expect((await focused(page))?.text).toBe('Back to the frame');
  await page.keyboard.press('Enter');
  await waitForState(page, ['lifted']);
  await tabTo(page, 'Put them back', 12);
  await page.keyboard.press('Enter');
  await waitForState(page, ['open'], 20000);
  await page.keyboard.press('Escape');
  await waitForState(page, ['shut'], 6000);
  await page.keyboard.press('Escape');
  await page.waitForFunction(() => !(document.querySelector('drawer-view') as HTMLElement & { open?: boolean })?.open);
  await expect(bayButton(page, 'drawer_bay/f09')).toBeFocused();
});

test('without photographs in the zoom index, the view offers none', async ({ page, browserName }) => {
  test.skip(browserName !== 'chromium', 'the lift needs Chromium');
  await page.route('**/zoom/index.json', (route) => route.fulfill({ json: { frames: {} } }));
  await page.goto('index.html?open=F09');
  await wallLoaded(page);
  await waitForState(page, ['open'], 15000);
  const canLift = await page.evaluate(() => !!window.__wall?.store.bay('drawer_bay/f09')?.canLift);
  test.skip(!canLift, 'no GLB or lifted still in the manifest yet (D4)');
  await clickQuiet(page, 'Lift them out');
  await waitForState(page, ['lifted'], 20000);
  await expect(page.locator('drawer-view').locator('button.quiet', { hasText: /put them back/i })).toHaveCount(1);
  await expect(page.locator('drawer-view').locator('button.quiet', { hasText: /see the photographs/i })).toHaveCount(0);
});

test('on the iPhone: a tap opens, the quiet buttons pull and shut, the lift shows what the tier allows, close returns focus', async ({ page, browserName, isMobile, hasTouch }) => {
  test.skip(browserName !== 'webkit' || !isMobile || !hasTouch, 'WebKit as a phone: touch through its own touchscreen (taps only; drags are the Pixel project\'s through CDP)');
  await page.goto('index.html');
  await wallLoaded(page);
  const c = await bayCenter(page, 'drawer_bay/f09');
  await page.touchscreen.tap(c.x, c.y);
  await waitForState(page, ['shut', 'entering']);
  await waitForState(page, ['shut']);
  await expect(page.locator('drawer-view').getByRole('dialog', { name: /What Stevie Saw/ })).toBeVisible();
  await clickQuiet(page, 'Open the drawer');
  await waitForState(page, ['open']);
  expect((await viewState(page))!.p).toBe(1);
  const canLift = await page.evaluate(() => !!window.__wall?.store.bay('drawer_bay/f09')?.canLift);
  if (canLift) {
    await clickQuiet(page, 'Lift them out');
    await waitForState(page, ['lifted'], 30000);
    const tier = await page.evaluate(() => window.__wall?.tier);
    test.info().annotations.push({ type: 'tier', description: `WebKit lifted at tier ${tier}` });
    const lifted = page.locator('drawer-view').locator('lifted-frame');
    if (tier === 2) await expect(lifted.locator('canvas.live')).toHaveCSS('opacity', '1');
    else await expect(lifted.locator('img.still')).toHaveCSS('opacity', '1');
    await clickQuiet(page, 'Put them back');
    await waitForState(page, ['open'], 30000);
  }
  await clickQuiet(page, 'Shut the drawer');
  await waitForState(page, ['shut']);
  await clickQuiet(page, 'Close');
  await page.waitForFunction(() => !(document.querySelector('drawer-view') as HTMLElement & { open?: boolean })?.open);
  await expect(bayButton(page, 'drawer_bay/f09')).toBeFocused();
});

test('reduced motion: the drawer snaps, no spring', async ({ page, browserName }) => {
  test.skip(browserName === 'webkit', 'a choice: emulateMedia with reduced motion is checked on the Chromium projects');
  // the wall's event log, mirrored to the console under ?debug=1: the draws between the state changes count the motion
  const events: Array<{ type: string; data: Record<string, unknown> | null }> = [];
  const pending: Promise<void>[] = [];
  page.on('console', (m) => { const a = m.args(); if (a.length >= 2) pending.push(Promise.all(a.map((x) => x.jsonValue().catch(() => null))).then((v) => { if (v[0] === '[wall]') events.push({ type: String(v[1]), data: (v[2] as Record<string, unknown> | null) ?? null }); })); });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('index.html?open=F02&debug=1');
  await wallLoaded(page);
  expect(await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches)).toBe(true);
  await waitForState(page, ['open'], 15000);
  await clickQuiet(page, 'Shut the drawer');
  const t0 = Date.now();
  await waitForState(page, ['shut']);
  // the spring takes about 690 ms to settle (SETTLE_SPRING 180/26); the snap is one draw
  expect(Date.now() - t0).toBeLessThan(250);
  await page.waitForTimeout(100);
  await Promise.all(pending);
  const from = events.findIndex((e) => e.type === 'view.state' && e.data?.from === 'open' && e.data?.to === 'shutting');
  const to = events.findIndex((e, i) => i > from && e.type === 'view.state' && e.data?.to === 'shut');
  expect(from).toBeGreaterThan(-1);
  expect(to).toBeGreaterThan(from);
  expect(events.slice(from + 1, to).filter((e) => e.type === 'view.draw')).toHaveLength(1);
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
  // the lift at tier 1: the lifted still fades in over the empty drawer; no turning (its buttons are tier 2's), the
  // photographs still offered
  await clickQuiet(page, 'Lift them out');
  await waitForState(page, ['lifted'], 20000);
  const still = page.locator('drawer-view').locator('lifted-frame img.still');
  await expect(still).toBeVisible();
  await expect(still).toHaveCSS('opacity', '1');
  expect(await still.evaluate((img) => (img as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);
  await expect(page.locator('drawer-view').locator('lifted-frame canvas.live')).toHaveCSS('opacity', '0');
  await expect(page.locator('drawer-view').locator('picture.empty')).toHaveCSS('opacity', '1');
  await expect(page.locator('drawer-view').locator('button.quiet', { hasText: /turn left/i })).toHaveCount(0);
  await expect(page.locator('drawer-view').locator('button.quiet', { hasText: /tilt up/i })).toHaveCount(0);
  await expect(page.locator('drawer-view').locator('button.quiet', { hasText: /see the photographs/i })).toHaveCount(1);
  await expect(page.locator('drawer-view').locator('button.quiet', { hasText: /put them back/i })).toHaveCount(1);
  await ctx.close();
});

test('?open= opens that drawer on its last frame, not lifted; an unknown value opens nothing', async ({ page }) => {
  await page.goto('index.html?open=what-arnie-hid');
  await wallLoaded(page);
  expect(await waitForState(page, ['open'], 15000)).toBe('open');
  // the view's dialog (its .view, role="dialog") is named for the frame; the host element carries no label
  await expect(page.locator('drawer-view').getByRole('dialog', { name: /What Arnie Hid/ })).toBeVisible();
  await page.goto('index.html?open=F07');
  await wallLoaded(page);
  await page.waitForTimeout(800);
  expect(await viewState(page)).toBeNull();
});

test('the switches from the hash, as the phone link passes them: #open-f09, #panel-debug, #pull', async ({ page }) => {
  // an Artifact's link passes a plain #name to the page and no query string (D7); the query forms are the other tests'
  await page.goto('index.html#open-f09');
  await wallLoaded(page);
  expect(await waitForState(page, ['open'], 15000)).toBe('open');
  await expect(page.locator('drawer-view').getByRole('dialog', { name: /What Stevie Saw/ })).toBeVisible();
  await page.goto('index.html#panel-debug');
  await page.reload();
  await wallLoaded(page);
  await expect(page.locator('records-panel h2')).toHaveText('Records (example data)');
  await expect(page.locator('button.debug-copy')).toHaveText('Copy the event log');
  await expect(page.locator('drawer-view')).toHaveCount(0);
  await page.goto('index.html#pull');
  await page.reload();
  await wallLoaded(page);
  expect(await page.evaluate(() => window.__wall?.store.mechanic)).toBe('pull');
  await expect(page.locator('drawer-wall').locator('drawer-bay .knob')).toHaveCount(8);
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
  expect(await page.locator('.tier0').textContent()).not.toMatch(/\$|100/);   // no price in the no-JavaScript list either (#47)
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
  await expect(bayButton(page, 'drawer_bay/f04')).toHaveAttribute('aria-label', `${FRAMES.find((f) => f[0] === 'drawer_bay/f04')![2]}. Sold out. Open the drawer.`);   // the sold-out name, no price (#47)
  for (const [id] of FRAMES) if (id !== 'drawer_bay/f04') await expect(bayButton(page, id)).toHaveAttribute('data-light', 'lit');
  await panel.locator('fieldset[data-id="drawer_bay/f04"] select').nth(1).selectOption('locked');
  await expect(f04.locator('.name')).toHaveText('Not yet.');
  await expect(bayButton(page, 'drawer_bay/f04')).toHaveAttribute('aria-label', 'Not yet.');   // the locked name, no price (#47)
  await expect(bayButton(page, 'drawer_bay/f04')).toBeDisabled();
  await panel.locator('fieldset[data-id="drawer_bay/f04"] select').nth(1).selectOption('hidden');
  await expect(f04.locator('button.face')).toHaveCount(0);
  await expect(f04.locator('.label')).toHaveCount(0);
});
