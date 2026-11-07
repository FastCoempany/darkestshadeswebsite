import type { Page, CDPSession } from '@playwright/test';

// Touch through CDP (DRAWER-WALL.md, Testing): Playwright's touchscreen only taps, so drags and pinches go through
// Input.dispatchTouchEvent (D0's S4 showed a drag arrives as pointermoves and a pan-y swipe scrolls).
export async function touchDrag(cdp: CDPSession, page: Page, x: number, y0: number, y1: number, steps = 12, msPerStep = 16): Promise<void> {
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y: y0 }] });
  for (let i = 1; i <= steps; i++) {
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x, y: y0 + ((y1 - y0) * i) / steps }] });
    await page.waitForTimeout(msPerStep);
  }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
}

export async function touchDragXY(cdp: CDPSession, page: Page, from: { x: number; y: number }, to: { x: number; y: number }, steps = 12): Promise<void> {
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: from.x, y: from.y }] });
  for (let i = 1; i <= steps; i++) {
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: from.x + ((to.x - from.x) * i) / steps, y: from.y + ((to.y - from.y) * i) / steps }] });
    await page.waitForTimeout(16);
  }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
}

/** A two-finger pinch about (cx, cy): the fingers move apart (scale > 1) or together. */
export async function touchPinch(cdp: CDPSession, page: Page, cx: number, cy: number, scale: number, steps = 10): Promise<void> {
  const d0 = 60, d1 = d0 * scale;
  const pts = (d: number) => [{ x: cx - d / 2, y: cy }, { x: cx + d / 2, y: cy }];
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: pts(d0) });
  for (let i = 1; i <= steps; i++) {
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: pts(d0 + ((d1 - d0) * i) / steps) });
    await page.waitForTimeout(16);
  }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
}

export async function touchTap(cdp: CDPSession, page: Page, x: number, y: number): Promise<void> {
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] });
  await page.waitForTimeout(40);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
}

/** The wall's state as the page exposes it. */
export async function viewState(page: Page): Promise<{ state: string; p: number } | null> {
  return page.evaluate(() => {
    const v = document.querySelector('drawer-view') as (HTMLElement & { state?: string; position?: number }) | null;
    return v ? { state: v.state ?? '', p: v.position ?? 0 } : null;
  });
}

export async function waitForState(page: Page, states: string[], timeout = 8000): Promise<string> {
  await page.waitForFunction((wanted) => {
    const v = document.querySelector('drawer-view') as (HTMLElement & { state?: string }) | null;
    return !!v && wanted.includes(v.state ?? '');
  }, states, { timeout });
  return (await viewState(page))!.state;
}

/** A drawer's face button on the wall (inside two shadow roots). */
export function bayButton(page: Page, id: string) {
  return page.locator('drawer-wall').locator(`drawer-bay[data-id="${id}"]`).locator('button.face');
}

export async function bayCenter(page: Page, id: string): Promise<{ x: number; y: number }> {
  const box = await bayButton(page, id).boundingBox();
  if (!box) throw new Error(`no box for ${id}`);
  return { x: box.x + box.width / 2, y: box.y + box.height / 2 };
}

export async function stageCenter(page: Page): Promise<{ x: number; y: number; w: number; h: number }> {
  const box = await page.locator('drawer-view').locator('.stage').boundingBox();
  if (!box) throw new Error('no stage');
  return { x: box.x + box.width / 2, y: box.y + box.height / 2, w: box.width, h: box.height };
}

export async function clickQuiet(page: Page, text: string): Promise<void> {
  await page.locator('drawer-view').locator('button.quiet', { hasText: new RegExp(`^${text}$`, 'i') }).first().click();
}

export async function wallLoaded(page: Page): Promise<void> {
  await page.waitForFunction(() => !!window.__wall?.store && document.querySelector('drawer-wall')?.shadowRoot?.querySelector('drawer-bay'));
  await page.evaluate(() => document.fonts.ready);
}

