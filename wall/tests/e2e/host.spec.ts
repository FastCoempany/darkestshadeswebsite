import { test, expect } from '@playwright/test';
import { bayButton, waitForState, wallLoaded } from './helpers';

// The phone link is a published Artifact (DRAWER-WALL.md, On a phone; O18): the host wraps the page, stripped of its own
// document skeleton, in a skeleton of its own, with a system font on body. This serves the built page that way (the
// skeleton as read back from the published artifact in D7) and checks that the wall still loads, lays out at 390 px, and
// keeps its type: the stand-in text face on the labels and the controls, not the host's system font (D7's review found the
// first set rendering in the system font because the wall's typography sat on :root alone).
const SKELETON = '<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}html{scroll-padding-top:env(safe-area-inset-top,0px)}body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#fff;color:#000}img{max-width:100%}[hidden]:not([hidden=until-found i]){display:none!important}</style></head><body>\n';

/** The built page as the phone set strips it: the head's lines but the charset, viewport and stylesheet link, then the body. */
function stripped(html: string, css: string): string {
  const head = html.match(/<head>([\s\S]*?)<\/head>/)![1]!;
  const body = html.match(/<body>([\s\S]*?)<\/body>/)![1]!;
  const keep = head.split('\n').map((l) => l.trim()).filter((l) => l && !/^<meta charset|^<meta name="viewport"|<link rel="stylesheet"/.test(l));
  // the stylesheet inlined at the page's root: its font URLs, relative to assets/, are pointed there (as the set builder does)
  return [...keep, '<style>', css.replace(/url\((['"]?)\.\//g, 'url($1./assets/'), '</style>', body.trim()].join('\n');
}

test.describe('the page inside the host\'s skeleton', () => {
  test('loads, lays out at 390 px and keeps the wall\'s type', async ({ page, browserName, isMobile }) => {
    test.skip(browserName !== 'chromium' || !!isMobile, 'one pass from desktop Chromium at a phone viewport');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.route('**/index.html', async (route) => {
      const res = await route.fetch();
      const html = await res.text();
      const cssPath = html.match(/<link rel="stylesheet"[^>]*href="\.\/(assets\/[^"]+\.css)"/)?.[1];
      const css = cssPath ? await (await route.fetch({ url: new URL(cssPath, route.request().url()).toString() })).text() : '';
      await route.fulfill({ status: 200, contentType: 'text/html', body: SKELETON + stripped(html, css) + '</body></html>' });
    });
    await page.goto('index.html');
    await wallLoaded(page);
    await page.evaluate(() => document.fonts.ready);
    const layout = await page.evaluate(() => ({ compatMode: document.compatMode, innerWidth, viewport: !!document.querySelector('meta[name=viewport]'), bg: getComputedStyle(document.body).backgroundColor }));
    expect(layout.compatMode).toBe('CSS1Compat');
    expect(layout.innerWidth).toBe(390);
    expect(layout.bg).toBe('rgb(0, 0, 0)');   // the wall's scene, not the host's white
    const type = await page.evaluate(() => {
      const bay = document.querySelector('drawer-wall')!.shadowRoot!.querySelector('drawer-bay')!.shadowRoot!;
      const of = (el: Element | null) => (el ? getComputedStyle(el) : null);
      const look = of(bay.querySelector('.look')), name = of(bay.querySelector('.name'));
      return { lookFamily: look?.fontFamily ?? '', nameFamily: name?.fontFamily ?? '', bodyFamily: getComputedStyle(document.body).fontFamily, urbanist: document.fonts.check('300 16px "Urbanist Variable"') };
    });
    // the text stack (Stolzl, its stand-in Urbanist) on the body and the labels, never the host's system stack
    expect(type.bodyFamily).toMatch(/^Stolzl/);
    expect(type.lookFamily).toMatch(/^Stolzl/);
    expect(type.nameFamily).toMatch(/^Stolzl/);
    expect(type.urbanist).toBe(true);
    await bayButton(page, 'drawer_bay/f09').click();
    await waitForState(page, ['shut']);
    const quiet = await page.locator('drawer-view').locator('button.quiet').first().evaluate((el) => getComputedStyle(el).fontFamily);
    expect(quiet).toMatch(/^Stolzl/);
  });
});
