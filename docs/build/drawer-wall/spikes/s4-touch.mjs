// S4: a CDP touch drag in headless Chromium (Playwright). A vertical drag on a touch-action:none pad must
// arrive as pointermove events with the finger's path; the same drag on a touch-action:pan-y box must scroll.
import { chromium, devices } from 'playwright';
const html = `<!doctype html><meta name=viewport content="width=device-width"><style>
body{margin:0;height:3000px;background:#000;color:#fff;font:14px sans-serif}
#pad{position:fixed;left:40px;top:120px;width:300px;height:300px;background:#222;touch-action:none}
#pan{position:absolute;left:40px;top:500px;width:300px;height:300px;background:#444;touch-action:pan-y}
</style><div id=pad></div><div id=pan></div><script>
window.ev=[];for(const t of ['pointerdown','pointermove','pointerup','pointercancel','touchstart','touchmove','touchend'])
 for(const el of [pad,pan]) el.addEventListener(t,e=>{window.ev.push({t,id:el.id,x:e.clientX??(e.touches[0]&&e.touches[0].clientX),y:e.clientY??(e.touches[0]&&e.touches[0].clientY)})},{passive:true});
</script>`;
const browser = await chromium.launch();
const ctx = await browser.newContext({ ...devices['Pixel 7'] });
const page = await ctx.newPage();
await page.setContent(html);
const cdp = await ctx.newCDPSession(page);
async function drag(x, y0, y1, steps) {
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y: y0 }] });
  for (let i = 1; i <= steps; i++) {
    const y = y0 + (y1 - y0) * i / steps;
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x, y }] });
    await page.waitForTimeout(16);
  }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
}
await drag(190, 160, 360, 12);               // on the pad: touch-action none
const padEv = await page.evaluate(() => { const e = window.ev.slice(); window.ev.length = 0; return e; });
const moves = padEv.filter(e => e.t === 'pointermove' && e.id === 'pad');
const scrollBefore = await page.evaluate(() => scrollY);
await drag(190, 700, 300, 12);               // on the pan-y box: a swipe up should scroll the page down
await page.waitForTimeout(300);
const scrollAfter = await page.evaluate(() => scrollY);
const panEv = await page.evaluate(() => window.ev.slice());
const panMoves = panEv.filter(e => e.t === 'pointermove' && e.id === 'pan').length;
console.log(JSON.stringify({
  pad: { pointerdown: padEv.filter(e=>e.t==='pointerdown').length, pointermove: moves.length, pointerup: padEv.filter(e=>e.t==='pointerup').length,
         firstY: moves[0]?.y, lastY: moves[moves.length-1]?.y, touchmove: padEv.filter(e=>e.t==='touchmove').length },
  panY: { scrollBefore, scrollAfter, scrolled: scrollAfter > scrollBefore, pointermoveOnPan: panMoves, pointercancel: panEv.filter(e=>e.t==='pointercancel').length }
}, null, 1));
await browser.close();
