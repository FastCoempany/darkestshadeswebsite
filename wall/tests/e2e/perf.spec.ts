import { test, expect, type Page } from '@playwright/test';
import { bayCenter, clickQuiet, stageCenter, touchDrag, touchDragXY, touchTap, waitForState, wallLoaded } from './helpers';

// Performance (DRAWER-WALL.md, Budgets; Testing): three.js absent from the initial bundle and fetched only once a drawer
// is open (the prefetch at idle); input to the next frame on open, pull and turn under 200 ms; at most 5 decoded frames
// held through a pull (the debug log); the frame rate while pulling and turning, measured from the animation-frame gaps
// at the machine's own speed (asserted: never under 30 fps) and at 4x CPU throttling (recorded: the budget's 30 fps
// at 4x is a Chromium trace on a GPU-composited machine; this VM composites in software and shares four CPUs, so its 4x
// figure varies by run and is written to the record, not asserted). The bundle's gzipped sizes are checks/bundle.mjs's.

/** The wall's event log, mirrored to the console under ?debug=1, collected as it arrives. */
function collectLog(page: Page) {
  const events: Array<{ type: string; data: Record<string, unknown> | null }> = [];
  const pending: Promise<void>[] = [];
  page.on('console', (m) => { const a = m.args(); if (a.length >= 2) pending.push(Promise.all(a.map((x) => x.jsonValue().catch(() => null))).then((v) => { if (v[0] === '[wall]') events.push({ type: String(v[1]), data: (v[2] as Record<string, unknown> | null) ?? null }); })); });
  return { events, settle: async () => { await page.waitForTimeout(100); await Promise.all(pending); } };
}

test.describe('performance', () => {
  test('three.js is absent from the initial bundle and arrives only once a drawer is open', async ({ page, browserName }) => {
    test.skip(browserName !== 'chromium', 'the prefetch runs at tier 2 (Chromium here)');
    const scripts: string[] = [];
    page.on('request', (r) => { if (r.resourceType() === 'script' || /\.js(\?|$)/.test(r.url())) scripts.push(r.url().split('/').pop() ?? r.url()); });
    await page.goto('index.html');
    await wallLoaded(page);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);
    const initial = [...scripts];
    test.info().annotations.push({ type: 'initial scripts', description: initial.join(', ') });
    expect(initial.filter((s) => /^three-/.test(s) || /^lifted-/.test(s) || /^drawer-view-/.test(s)), 'nothing of the view or three.js before the first open').toEqual([]);
    expect(initial.length).toBeGreaterThan(0);
    // open a drawer: the view's modules load, then the three.js chunk at idle (the prefetch), before any lift
    const c = await bayCenter(page, 'drawer_bay/f09');
    await page.mouse.click(c.x, c.y);
    await waitForState(page, ['shut']);
    await expect.poll(() => scripts.some((s) => /^three-/.test(s)), { timeout: 10000, message: 'the three.js chunk prefetched at idle after the open' }).toBe(true);
    expect(scripts.some((s) => /^drawer-view-/.test(s))).toBe(true);
  });

  test('a pull holds at most 5 decoded frames', async ({ page, browserName, isMobile }) => {
    test.skip(browserName !== 'chromium' || !isMobile, 'touch through CDP, on the Pixel project');
    const log = collectLog(page);
    await page.goto('index.html?open=F09&debug=1');
    await wallLoaded(page);
    await waitForState(page, ['open'], 15000);
    const cdp = await page.context().newCDPSession(page);
    const s = await stageCenter(page);
    const vh = page.viewportSize()!.height;
    // shut it by a slow full pull up, open it by a slow full pull down, then once more each way
    for (let i = 0; i < 2; i++) {
      await touchDrag(cdp, page, s.x, s.y + s.h * 0.3, s.y + s.h * 0.3 - vh * 0.45 * 1.05, 30, 24);
      await waitForState(page, ['shut'], 6000);
      await touchDrag(cdp, page, s.x, s.y - s.h * 0.3, s.y - s.h * 0.3 + vh * 0.45 * 1.05, 30, 24);
      await waitForState(page, ['open'], 6000);
    }
    await log.settle();
    // held is read at two moments: after each draw (seek() has just closed what lies outside the window, so this reading
    // cannot exceed 5 by construction) and when each decode lands (the peak: a frame one past the window may still be held)
    const draws = log.events.filter((e) => e.type === 'view.draw');
    const decodes = log.events.filter((e) => e.type === 'sequence.decoded');
    const held = draws.map((e) => Number(e.data?.held ?? 0));
    const peak = decodes.map((e) => Number(e.data?.held ?? 0));
    console.log(`decoded frames: ${draws.length} draws, held at most ${Math.max(...held)} after a draw; ${decodes.length} decodes, held at most ${Math.max(...peak)} as a decode landed`);
    test.info().annotations.push({ type: 'decoded frames', description: `${draws.length} draws, held at most ${Math.max(...held)}; ${decodes.length} decodes, peak ${Math.max(...peak)}` });
    expect(draws.length).toBeGreaterThan(40);
    expect(decodes.length).toBeGreaterThan(20);
    expect(Math.max(...held)).toBeLessThanOrEqual(5);
    expect(Math.max(...peak), 'the decode-time peak').toBeLessThanOrEqual(5);
  });

  test('input to the frame after the next (past the paint): open, pull and turn under 200 ms', async ({ page, browserName, isMobile }) => {
    test.skip(browserName !== 'chromium' || !isMobile, 'touch through CDP, on the Pixel project');
    await page.goto('index.html');
    await wallLoaded(page);
    // every pointer event's time to the next frame, sorted by what the wall was doing when it arrived
    await page.evaluate(() => {
      const lat: Record<string, number[]> = { open: [], pull: [], turn: [] };
      (window as unknown as { __lat: typeof lat }).__lat = lat;
      const kind = () => { const v = document.querySelector('drawer-view') as (HTMLElement & { state?: string; open?: boolean }) | null; if (!v?.open) return 'open'; if (v.state === 'pulling') return 'pull'; if (v.state === 'lifted') return 'turn'; return null; };
      // to the start of the frame after the next: the next frame's start is before its paint, so the one after it is past the
      // presentation of the response (the proxy for INP the lab can read; a real INP is to the paint itself)
      for (const type of ['pointerdown', 'pointermove', 'pointerup']) document.addEventListener(type, (e) => { const k = kind(); if (!k) return; const t = e.timeStamp; requestAnimationFrame(() => requestAnimationFrame((ts2) => { lat[k]!.push(ts2 - t); })); }, true);
    });
    const cdp = await page.context().newCDPSession(page);
    const c = await bayCenter(page, 'drawer_bay/f09');
    await touchTap(cdp, page, c.x, c.y, 2);
    await waitForState(page, ['shut']);
    const s = await stageCenter(page);
    const vh = page.viewportSize()!.height;
    await touchDrag(cdp, page, s.x, s.y - s.h * 0.3, s.y - s.h * 0.3 + vh * 0.45 * 1.05, 24, 24);
    await waitForState(page, ['open'], 6000);
    const canLift = await page.evaluate(() => !!window.__wall?.store.bay('drawer_bay/f09')?.canLift);
    if (canLift) {
      await clickQuiet(page, 'Lift them out');
      await waitForState(page, ['lifted'], 20000);
      const s2 = await stageCenter(page);
      await touchDragXY(cdp, page, { x: s2.x - 80, y: s2.y }, { x: s2.x + 80, y: s2.y }, 20);
    }
    const lat = await page.evaluate(() => (window as unknown as { __lat: Record<string, number[]> }).__lat);
    const stats = (xs: number[]) => { const a = [...xs].sort((p, q) => p - q); return a.length ? { n: a.length, median: a[Math.floor(a.length / 2)]!, max: a[a.length - 1]! } : { n: 0, median: 0, max: 0 }; };
    const report = { open: stats(lat.open!), pull: stats(lat.pull!), turn: stats(lat.turn!) };
    console.log(`input to paint (ms): ${Object.entries(report).map(([k, v]) => `${k} n ${v.n}, median ${v.median.toFixed(1)}, max ${v.max.toFixed(1)}`).join('; ')}`);
    test.info().annotations.push({ type: 'input to paint (ms)', description: JSON.stringify(report) });
    expect(report.open.n).toBeGreaterThan(0);
    expect(report.pull.n).toBeGreaterThan(10);
    if (canLift) expect(report.turn.n).toBeGreaterThan(10);
    for (const [k, v] of Object.entries(report)) if (v.n) expect(v.max, `${k}: input to the frame after the next`).toBeLessThanOrEqual(200);
  });

  test('frame rate while pulling and turning: never under 30 fps at the machine\'s speed; the 4x CPU figure recorded', async ({ page, browserName, isMobile }) => {
    test.skip(browserName !== 'chromium' || !isMobile, 'touch through CDP, on the Pixel project');
    await page.goto('index.html?open=F09&debug=1');
    await wallLoaded(page);
    await waitForState(page, ['open'], 15000);
    const cdp = await page.context().newCDPSession(page);
    // the animation-frame gaps say whether the main thread kept up; the canvas draws (view.draw in the log) say how often the
    // picture advanced, which in the lab is bounded by the CDP drag's own pace (about 28 moves a second), not by the wall
    const log = collectLog(page);
    const sample = async (run: () => Promise<void>) => {
      await page.evaluate(() => { const w = window as unknown as { __frames: number[]; __stop: boolean }; w.__frames = []; w.__stop = false; const loop = (ts: number) => { w.__frames.push(ts); if (!w.__stop) requestAnimationFrame(loop); }; requestAnimationFrame(loop); });
      const drawsBefore = log.events.filter((e) => e.type === 'view.draw').length;
      const t0 = Date.now();
      await run();
      const seconds = (Date.now() - t0) / 1000;
      await log.settle();
      const draws = log.events.filter((e) => e.type === 'view.draw').length - drawsBefore;
      const r = await page.evaluate(() => { const w = window as unknown as { __frames: number[]; __stop: boolean }; w.__stop = true; const f = w.__frames; const gaps = f.slice(1).map((t, i) => t - f[i]!); gaps.sort((a, b) => a - b); return { frames: f.length, median: gaps[Math.floor(gaps.length / 2)] ?? 0, p95: gaps[Math.floor(gaps.length * 0.95)] ?? 0, max: gaps[gaps.length - 1] ?? 0 }; });
      return { ...r, draws, drawsPerSecond: draws / seconds };
    };
    const s = await stageCenter(page);
    const vh = page.viewportSize()!.height;
    const fps = (gap: number) => (gap ? Math.round(1000 / gap) : 0);
    // the canvas draws are the pull's (the turn renders through three.js, which the log does not count)
    const fmt = (r: { frames: number; median: number; p95: number; max: number; draws: number; drawsPerSecond: number }) => `${r.frames} frames, median ${fps(r.median)} fps, p95 ${fps(r.p95)} fps, slowest ${fps(r.max)} fps (${r.max.toFixed(1)} ms)` + (r.draws ? `; ${r.draws} canvas draws (${r.drawsPerSecond.toFixed(1)}/s, the drag's own pace)` : '');
    const canLift = await page.evaluate(() => !!window.__wall?.store.bay('drawer_bay/f09')?.canLift);
    // "never under 30 fps": no animation-frame gap longer than two 60 Hz periods (one skipped frame at most, 34.4 ms with
    // 1 ms for timer jitter: a single skipped frame measures 33.4 ms, not 33.33) and the median gap at the refresh itself
    // (no more than 17 ms), so a run slow throughout cannot pass on its own median
    const FLOOR_MS = 2 * (1000 / 60) + 1, MEDIAN_MS = 17;
    const results: Record<string, { pull: ReturnType<typeof fmt>; turn: ReturnType<typeof fmt>; pullMax: number; turnMax: number; pullMedian: number; turnMedian: number }> = {};
    // the same pull and turn at the machine's own speed and at 4x CPU throttling: both recorded, the floor asserted at 1x
    for (const rate of [1, 4]) {
      await cdp.send('Emulation.setCPUThrottlingRate', { rate });
      const pull = await sample(async () => {
        await touchDrag(cdp, page, s.x, s.y + s.h * 0.3, s.y + s.h * 0.3 - vh * 0.45 * 1.05, 40, 16);
        await waitForState(page, ['shut'], 8000);
        await touchDrag(cdp, page, s.x, s.y - s.h * 0.3, s.y - s.h * 0.3 + vh * 0.45 * 1.05, 40, 16);
        await waitForState(page, ['open'], 8000);
      });
      let turn = { frames: 0, median: 0, p95: 0, max: 0, draws: 0, drawsPerSecond: 0 };
      if (canLift) {
        await clickQuiet(page, 'Lift them out');
        await waitForState(page, ['lifted'], 30000);
        const s2 = await stageCenter(page);
        turn = await sample(async () => { await touchDragXY(cdp, page, { x: s2.x - 90, y: s2.y - 20 }, { x: s2.x + 90, y: s2.y + 20 }, 40); await page.waitForTimeout(300); });
        await clickQuiet(page, 'Put them back');
        await waitForState(page, ['open'], 30000);
      }
      results[`${rate}x`] = { pull: fmt(pull), turn: fmt(turn), pullMax: pull.max, turnMax: turn.max, pullMedian: pull.median, turnMedian: turn.median };
      expect(pull.frames).toBeGreaterThan(30);
      if (canLift) expect(turn.frames).toBeGreaterThan(20);
    }
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: 1 });
    const line = Object.entries(results).map(([k, v]) => `${k}: pull ${v.pull}; turn ${v.turn}`).join(' | ');
    console.log(`frame rate: ${line}`);
    test.info().annotations.push({ type: 'frame rate', description: line });
    expect(results['1x']!.pullMedian, 'the median frame while pulling, at the refresh').toBeLessThanOrEqual(MEDIAN_MS);
    expect(results['1x']!.pullMax, 'the slowest frame while pulling: at most one skipped frame').toBeLessThanOrEqual(FLOOR_MS);
    if (canLift) {
      expect(results['1x']!.turnMedian, 'the median frame while turning, at the refresh').toBeLessThanOrEqual(MEDIAN_MS);
      expect(results['1x']!.turnMax, 'the slowest frame while turning: at most one skipped frame').toBeLessThanOrEqual(FLOOR_MS);
    }
  });
});
